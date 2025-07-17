# cli.py
from xml_validator.validate import validate_xmls, validate_with_sch, get_xml
from xml_validator.config import SVRL_TEMP
from pathlib import Path
from collections import Counter
from datetime import datetime
import argparse
import sys
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(description="Validate XML files using XSD or Schematron.")
    parser.add_argument("file_pattern")
    parser.add_argument("schema_path")
    parser.add_argument("batches", nargs="+")
    parser.add_argument("--output", default=".")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    output = Path(args.output)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = output / f"validation_log_{timestamp}.csv"

    schema_path = Path(args.schema_path)
    if not schema_path.exists():
        sys.exit(f"Schema not found: {schema_path}")

    all_rows = []
    for i, batch in enumerate(args.batches):
        batch_path = Path(batch)
        print(f"[{i+1}/{len(args.batches)}] {batch_path.name}")
        xml_files = get_xml(batch_path, args.file_pattern)
        if not xml_files:
            print(f"No matching files in {batch_path}. Skipping.")
            continue
        if schema_path.suffix.lower() == ".xsd":
            rows = validate_xmls(xml_files, schema_path, batch_path.name, log_path, verbose=args.verbose)
        elif schema_path.suffix.lower() in {".xsl", ".xslt"}:
            rows = validate_with_sch(xml_files, schema_path, batch_path.name, log_path, verbose=args.verbose)
            if SVRL_TEMP.exists():
                SVRL_TEMP.unlink()
        else:
            print(f"Unsupported schema type: {schema_path.suffix}")
            continue
        all_rows.extend(rows)

    summary = Counter(row["status"] for row in all_rows)
    print("\nSummary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"\nCSV log written to: {log_path.resolve()}")
    sys.exit(1 if any(r["status"] in ("invalid", "error") for r in all_rows) else 0)
