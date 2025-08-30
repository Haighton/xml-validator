from pathlib import Path
from collections import Counter
from datetime import datetime
import argparse
import sys
import logging
import argcomplete
from logging.handlers import RotatingFileHandler

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table

from xml_validator.validate import validate_xmls, validate_with_sch, get_xml, parallel_validate
from xml_validator.schematron import compile_schematron
from xml_validator.config import SVRL_TEMP

console = Console()

# ---------------- Logging ---------------- #
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_path = log_dir / "xml_validator.log"

logger = logging.getLogger("xml-validator")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def load_profiles(profile_file="profiles.yaml"):
    """Load validation profiles from YAML file if present."""
    path = Path(profile_file)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    parser = argparse.ArgumentParser(
        description="Validate XML files using XSD or Schematron.")
    parser.add_argument(
        "--pattern", help="Regex pattern for XML filenames (e.g. '.*mets\\.xml')")
    parser.add_argument(
        "--schema", help="Path to schema file (.xsd, .sch, .xsl)")
    parser.add_argument(
        "--profile", help="Profile name from profiles.yaml").completer = lambda **_: list(load_profiles().keys())
    parser.add_argument("--list-profiles", action="store_true",
                        help="List available profiles from profiles.yaml")
    parser.add_argument("--batches", nargs="+",
                        help="One or more batch folders")
    parser.add_argument("--output", default=".",
                        help="Output folder for CSV logs")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    # Enable argcomplete (bash/zsh autocompletion)
    argcomplete.autocomplete(parser)

    args = parser.parse_args()

    # Load profiles
    profiles = load_profiles()

    if args.list_profiles:
        if not profiles:
            console.print(
                "[yellow]⚠ No profiles found (profiles.yaml missing or empty)[/yellow]")
            sys.exit(0)
        console.print("[bold]Available profiles:[/bold]")
        for name, prof in profiles.items():
            console.print(f"  [cyan]{name}[/cyan] → pattern: {prof.get('pattern')} | schema: {prof.get('schema')}")
        sys.exit(0)

    if args.profile:
        if args.profile not in profiles:
            console.print(f"[red]❌ Profile '{args.profile}' not found in profiles.yaml[/red]")
            sys.exit(2)
        prof = profiles[args.profile]
        pattern = prof.get("pattern")
        schema_path = Path(prof.get("schema"))
    else:
        if not args.pattern or not args.schema:
            console.print(
                "[red]❌ Either --profile OR both --pattern and --schema must be provided[/red]")
            sys.exit(2)
        pattern = args.pattern
        schema_path = Path(args.schema)

    if not schema_path.exists():
        console.print(f"[red]❌ Schema not found: {schema_path}[/red]")
        sys.exit(2)

    if not args.batches:
        console.print("[red]❌ No batch folders provided[/red]")
        sys.exit(2)

    output = Path(args.output)
    output.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_csv = output / f"validation_log_{timestamp}.csv"

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        console.print("[yellow]Verbose logging enabled[/yellow]")

    all_rows = []
    for i, batch in enumerate(args.batches, start=1):
        batch_path = Path(batch)
        console.print(f"[cyan][{i}/{len(args.batches)}] Validating batch:[/cyan] {batch_path.name}")

        xml_files = get_xml(batch_path, pattern)
        if not xml_files:
            console.print(f"[yellow]⚠ No matching files in {batch_path}. Skipping.[/yellow]")
            continue

        # --- Use automatic parallelism with Rich progress ---
        with Progress(
            SpinnerColumn(),
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"Validating {len(xml_files)} files", total=len(xml_files))

            if schema_path.suffix.lower() in {".xsd", ".xsl", ".xslt"}:
                rows = parallel_validate(xml_files, schema_path, batch_path.name, log_csv,
                                         verbose=args.verbose, progress=(progress, task))
            elif schema_path.suffix.lower() == ".sch":
                compiled = compile_schematron(schema_path)
                rows = parallel_validate(xml_files, compiled, batch_path.name, log_csv,
                                         verbose=args.verbose, progress=(progress, task))
                compiled.unlink(missing_ok=True)
                if SVRL_TEMP.exists():
                    SVRL_TEMP.unlink()
            else:
                console.print(f"[red]❌ Unsupported schema type: {schema_path.suffix}[/red]")
                continue

        all_rows.extend(rows)

    # Summary
    summary = Counter(row["status"] for row in all_rows)

    table = Table(title="Validation Summary", show_lines=True)
    table.add_column("Status", justify="center", style="bold")
    table.add_column("Count", justify="right")

    for status in ["valid", "invalid", "error"]:
        if status in summary:
            color = "green" if status == "valid" else "red" if status == "invalid" else "yellow"
            table.add_row(f"[{color}]{status}[/{color}]", str(summary[status]))

    console.print(table)
    console.print(f"[bold]CSV log written to:[/bold] {log_csv.resolve()}")

    # Exit codes
    if any(r["status"] == "error" for r in all_rows):
        sys.exit(2)  # fatal error
    elif any(r["status"] == "invalid" for r in all_rows):
        sys.exit(1)  # invalid XMLs
    else:
        sys.exit(0)  # all valid
