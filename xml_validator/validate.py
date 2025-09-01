# src/xml_validator/validate.py
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from lxml import etree
from tqdm import tqdm

from .config import SVRL_TEMP, SVRL_NS, CLASSPATH
from .utils import write_csv_log


def determine_workers(num_files: int) -> int:
    cores = os.cpu_count() or 2
    if num_files <= 2:
        return max(2, cores)
    if num_files <= cores:
        return max(2, min(num_files, cores - 1))
    return min(8, cores)


def validate_single_xsd(xmlfile: Path, schema_path: Path, schema_name: str, verbose: bool = False) -> dict:
    """Valideer één XML-bestand tegen een XSD-schema."""
    try:
        with open(schema_path, "rb") as f:
            xsd = etree.XMLSchema(etree.parse(f))

        doc = etree.parse(xmlfile)
        valid = xsd.validate(doc)

        if valid:
            return {
                "file": xmlfile.resolve(),
                "schema": schema_name,
                "validation_type": "XSD",
                "status": "valid",
                "details": ""
            }
        else:
            details = "; ".join(
                f"Line {e.line}: {e.message} (domain: {e.domain_name})"
                for e in xsd.error_log
            )
            return {
                "file": xmlfile.resolve(),
                "schema": schema_name,
                "validation_type": "XSD",
                "status": "invalid",
                "details": details
            }
    except Exception as e:
        return {
            "file": xmlfile.resolve(),
            "schema": schema_name,
            "validation_type": "XSD",
            "status": "error",
            "details": str(e)
        }


def validate_single_sch(xmlfile: Path, schema_path: Path, schema_name: str, verbose: bool = False) -> dict:
    """Valideer één XML-bestand tegen een Schematron (gecompileerd naar XSLT)."""
    try:
        cmd = [
            "java",
            "-cp", CLASSPATH,
            "net.sf.saxon.Transform",
            f"-s:{xmlfile}",
            f"-xsl:{schema_path}",
            f"-o:{SVRL_TEMP}"
        ]

        if verbose:
            print("👉 Running Java command:")
            print("   " + " ".join(cmd))

        subprocess.run(cmd, check=True)

        tree = etree.parse(SVRL_TEMP)
        failed = tree.xpath("//svrl:failed-assert", namespaces=SVRL_NS)

        if failed:
            details = "; ".join(
                f"{fa.attrib.get('location', 'unknown')}: "
                f"{fa.findtext('svrl:text', namespaces=SVRL_NS)}"
                for fa in failed
            )
            return {
                "file": xmlfile.resolve(),
                "schema": schema_name,
                "validation_type": "Schematron",
                "status": "invalid",
                "details": details
            }
        else:
            return {
                "file": xmlfile.resolve(),
                "schema": schema_name,
                "validation_type": "Schematron",
                "status": "valid",
                "details": ""
            }
    except Exception as e:
        return {
            "file": xmlfile.resolve(),
            "schema": schema_name,
            "validation_type": "Schematron",
            "status": "error",
            "details": f"Saxon failed: {e}"
        }


def parallel_validate(files, schema_path: Path, schema_name: str, csv_log_filename: Path,
                      verbose: bool = False, progress=None):
    workers = determine_workers(len(files))
    if verbose:
        print(f"[parallel] Using {workers} workers for {len(files)} files")

    rows = []
    prog, task = progress if progress else (None, None)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = []
        for xmlfile in files:
            if schema_path.suffix.lower() == ".xsd":
                futures.append(executor.submit(
                    validate_single_xsd, xmlfile, schema_path, schema_name, verbose
                ))
            else:
                futures.append(executor.submit(
                    validate_single_sch, xmlfile, schema_path, schema_name, verbose
                ))

        for f in as_completed(futures):
            rows.append(f.result())
            if prog and task is not None:
                prog.update(task, advance=1)

    write_csv_log(rows, csv_log_filename)
    return rows
