# src/xml_validator/cli.py
import argparse
import logging
import os
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import yaml
from tqdm import tqdm
from xml_validator.config import SVRL_TEMP
from xml_validator.schematron import compile_schematron
from xml_validator.utils import load_config, setup_logging
from xml_validator.validate import validate_single_sch, validate_single_xsd

from . import __version__


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate XML files using XSD or Schematron."
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to config.yaml (default: config.yaml)",
        default="config.yaml"
    )
    parser.add_argument(
        "-f", "--file-pattern",
        help="Regex pattern to match XML files (default: .*\\.xml$).")
    parser.add_argument(
        "-s", "--schema",
        help="Path to XSD, Schematron (.sch), or XSLT file."
    )
    parser.add_argument(
        "-b", "--batches",
        nargs="+",
        help="One or more batch directories.")
    parser.add_argument(
        "-o", "--output",
        help="Output directory for CSV log.",
        default="output"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging.")
    parser.add_argument(
        "-j", "--jobs",
        type=int,
        help="Number of parallel workers.")
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Search for XML files recursively in batch directories."
    )
    parser.add_argument(
        "--profile",
        help="Use a predefined profile from config.yaml"
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles from config.yaml")
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print merged configuration and exit.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}")
    return parser.parse_args()


def merge_config_and_args(args) -> dict:
    config = load_config(args.config)

    if args.list_profiles:
        profiles = config.get("profiles", {})
        if not profiles:
            print("No profiles defined in config.yaml")
        else:
            print("Available profiles:")
            for name, prof in profiles.items():
                if "validations" in prof:
                    print(f"  {name}:")
                    for v in prof["validations"]:
                        schemas = v.get("schemas", [])
                        if not schemas and "schema" in v:
                            schemas = [v["schema"]]
                        print(f"    - pattern={v.get('pattern')}  schemas={schemas}")
                else:
                    print(f"  {name}: pattern={prof.get('pattern')} schema={prof.get('schema')}")
        sys.exit(0)

    validations = []

    if args.profile:
        profiles = config.get("profiles", {})
        if args.profile not in profiles:
            print(f"Profile '{args.profile}' not found in config.yaml")
            sys.exit(2)

        selected = profiles[args.profile]
        if "validations" in selected:
            for v in selected["validations"]:
                pattern = v["pattern"]
                schemas = v.get("schemas", [])
                if not schemas and "schema" in v:
                    schemas = [v["schema"]]
                for schema in schemas:
                    validations.append({"pattern": pattern, "schema": schema})
        else:
            validations = [{
                "pattern": selected.get("pattern"),
                "schema": selected.get("schema"),
            }]
    else:
        # fallback naar losse args
        if not args.schema and not config.get("schema"):
            print("No schema defined (use --schema or a profile).")
            sys.exit(2)
        validations = [{
            "pattern": args.file_pattern or config.get("file_pattern") or r".*\.xml$",
            "schema": args.schema or config.get("schema"),
        }]

    return {
        "validations": validations,
        "batches": args.batches or config.get("batches", []),
        "output": Path(args.output or config.get("output", "output")),
        "verbose": args.verbose or config.get("verbose", False),
        "jobs": args.jobs if args.jobs is not None else config.get("jobs"),
        "recursive": args.recursive or config.get("recursive", False),
        "log_size": config.get("log_size", 5 * 1024 * 1024),
        "log_backups": config.get("log_backups", 5),
    }


def determine_workers(
        num_batches: int,
        requested: int | None) -> tuple[int, str]:
    if requested:
        return max(1, requested), f"user-specified ({requested})"

    cores = os.cpu_count() or 2
    if num_batches <= 2:
        return max(2, cores), f"auto: small batch count → all {cores} cores"
    if num_batches <= cores:
        return max(2, min(num_batches, cores - 1)), f"auto: ≤ cores → {min(num_batches, cores - 1)} workers"
    return min(8, cores), f"auto: many batches → capped at {min(8, cores)} workers"


def process_batch(batch_path: Path, schema_path: Path, file_pattern: str,
                  log_path: Path, verbose: bool, recursive: bool):
    import csv
    regex = re.compile(file_pattern or r".*\.xml$")
    files = batch_path.rglob("*") if recursive else batch_path.glob("*")
    xml_files = [f for f in files if regex.search(f.name)]

    schema_name = schema_path.name
    rows = []

    if not xml_files:
        msg = f"No matching files in {batch_path} for pattern '{file_pattern}'"
        rows.append({
            "file": "",
            "schema": schema_name,
            "validation_type": "N/A",
            "status": "skipped",
            "details": msg
        })
        logger = logging.getLogger("xml_validator")
        logger.warning(msg)
    else:
        if schema_path.suffix.lower() == ".xsd":
            rows = [validate_single_xsd(
                f, schema_path, schema_name, verbose) for f in xml_files]

        elif schema_path.suffix.lower() == ".sch":
            compiled = compile_schematron(schema_path, verbose=verbose)
            rows = [validate_single_sch(
                f, compiled, schema_name, verbose) for f in xml_files]
            compiled.unlink(missing_ok=True)
            if SVRL_TEMP.exists():
                SVRL_TEMP.unlink()

        elif schema_path.suffix.lower() in {".xsl", ".xslt"}:
            rows = [validate_single_sch(
                f, schema_path, schema_name, verbose) for f in xml_files]
            if SVRL_TEMP.exists():
                SVRL_TEMP.unlink()

        else:
            msg = f"Unsupported schema type: {schema_path.suffix}"
            rows.append({
                "file": "",
                "schema": schema_name,
                "validation_type": "N/A",
                "status": "error",
                "details": msg
            })
            logger = logging.getLogger("xml_validator")
            logger.error(msg)

    with log_path.open("a", encoding="utf-8", newline="") as csvfile:
        fieldnames = ["file", "schema", "validation_type", "status", "details"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        if log_path.stat().st_size == 0:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return rows


def main():
    args = parse_args()
    cfg = merge_config_and_args(args)

    if args.print_config:
        print("Effective configuration:\n")
        print(f"Batches: {cfg['batches']}")
        print(f"Output: {cfg['output']}")
        print(f"Verbose: {cfg['verbose']}")
        print(f"Jobs: {cfg['jobs']}")
        print(f"Recursive: {cfg['recursive']}")
        print(f"Log path: {cfg.get('log_path', './logs')}")
        print(f"Log size: {cfg['log_size']}")
        print(f"Log backups: {cfg['log_backups']}")
        print("\nValidations to run:")
        for i, val in enumerate(cfg["validations"], 1):
            print(f"  {i}. pattern={val['pattern']}  schema={val['schema']}")
        sys.exit(0)

    output = cfg["output"]
    output.mkdir(parents=True, exist_ok=True)

    # log_path uit config gebruiken
    log_dir = Path(cfg.get("log_path", "./logs"))
    logger = setup_logging(log_dir, cfg["log_size"], cfg["log_backups"])

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = output / f"validation_log_{timestamp}.csv"
    log_path.touch(exist_ok=True)

    total_tasks = len(cfg["batches"]) * len(cfg["validations"])
    workers, reason = determine_workers(len(cfg["batches"]), cfg["jobs"])
    logger.info(f"Using {workers} parallel workers for {total_tasks} tasks ({reason}).")

    all_rows = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for batch in cfg["batches"]:
            for val in cfg["validations"]:
                schema_path = Path(val["schema"])
                futures[executor.submit(
                    process_batch, Path(batch), schema_path, val["pattern"],
                    log_path, cfg["verbose"], cfg["recursive"]
                )] = (batch, schema_path.name)

        for i, future in enumerate(tqdm(as_completed(futures), total=len(futures), desc="Validating")):
            batch, schema_name = futures[future]
            try:
                rows = future.result()
                all_rows.extend(rows)
                logger.info(f"[{i+1}/{len(futures)}] Done: {Path(batch).name} ({schema_name})")
            except Exception as e:
                logger.error(f"[{i+1}/{len(futures)}] Error in {Path(batch).name} ({schema_name}): {e}")

    summary = Counter(row["status"] for row in all_rows)
    logger.info("\nSummary:")
    for k, v in summary.items():
        logger.info(f"  {k}: {v}")

    logger.info(f"\nCSV log written to: {log_path.resolve()}")
    sys.exit(1 if any(r["status"] in ("invalid", "error")
                      for r in all_rows) else 0)
