import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from lxml import etree
import subprocess
from pathlib import Path
from tqdm import tqdm
from .config import SVRL_TEMP, SVRL_NS
from .utils import write_csv_log


def determine_workers(num_files: int) -> int:
    cores = os.cpu_count() or 2
    if num_files <= 2:
        return max(2, cores)
    if num_files <= cores:
        return max(2, min(num_files, cores - 1))
    return min(8, cores)


def validate_single_xsd(xmlfile, schema_path, batch_name, verbose=False):
    try:
        with open(schema_path, "rb") as f:
            xsd = etree.XMLSchema(etree.parse(f))
<<<<<<< HEAD
        doc = etree.parse(xmlfile)
        valid = xsd.validate(doc)
        if valid:
            return {"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "XSD",
                    "status": "valid", "details": ""}
        else:
            details = "; ".join(f"Line {e.line}: {e.message} (domain: {e.domain_name})"
                                for e in xsd.error_log)
            return {"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "XSD",
                    "status": "invalid", "details": details}
    except Exception as e:
        return {"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "XSD",
                "status": "error", "details": str(e)}
=======
    except OSError:
        raise FileNotFoundError(f'{schema_path} could not be loaded.')

    for xmlfile in tqdm(files):
        if verbose:
            tqdm.write(f"Validating (XSD): {xmlfile.name}")
        try:
            doc = etree.parse(xmlfile)
            valid = xsd.validate(doc)
            state = 'valid' if valid else 'invalid'
            error_log = xsd.error_log if not valid else None

            validation_errors[xmlfile.name] = [state, error_log]

            if valid:
                rows.append({"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "XSD", "status": "valid", "details": ""})
            else:
                details = "; ".join(f"Line {e.line}: {e.message} (domain: {e.domain_name})" for e in error_log)
                rows.append({"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "XSD", "status": "invalid", "details": details})
        except Exception as e:
            if verbose:
                tqdm.write(f"Error validating {xmlfile.name}: {e}")
            rows.append({"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "XSD", "status": "error", "details": str(e)})
            validation_errors[xmlfile.name] = ['error', str(e)]

    write_csv_log(rows, csv_log_filename)
    return rows
>>>>>>> 92ae569 (WIP: lokale aanpassingen)


def validate_single_sch(xmlfile, schema_path, batch_name, verbose=False):
    try:
        subprocess.run(["java", "-jar", str(schema_path.parent / "lib" / "Saxon-HE-12.5.jar"),
                        f"-s:{xmlfile}", f"-xsl:{schema_path}", f"-o:{SVRL_TEMP}"],
                       check=True)
        tree = etree.parse(SVRL_TEMP)
        failed = tree.xpath("//svrl:failed-assert", namespaces=SVRL_NS)
        if failed:
            details = "; ".join(f"{fa.attrib.get('location', 'unknown')}: "
                                f"{fa.findtext('svrl:text', namespaces=SVRL_NS)}"
                                for fa in failed)
            return {"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "Schematron",
                    "status": "invalid", "details": details}
        else:
            return {"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "Schematron",
                    "status": "valid", "details": ""}
    except Exception as e:
        return {"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "Schematron",
                "status": "error", "details": f"Saxon failed: {e}"}


def parallel_validate(files, schema_path, batch_name, csv_log_filename, verbose=False, progress=None):
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
                    validate_single_xsd, xmlfile, schema_path, batch_name, verbose))
            else:
                futures.append(executor.submit(
                    validate_single_sch, xmlfile, schema_path, batch_name, verbose))

        for f in as_completed(futures):
            rows.append(f.result())
            if prog and task is not None:
                prog.update(task, advance=1)

    write_csv_log(rows, csv_log_filename)
    return rows
