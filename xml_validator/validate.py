# xml_validator/validate.py
import re
import subprocess
from lxml import etree
from tqdm import tqdm
from .config import SVRL_TEMP, SVRL_NS
from .utils import write_csv_log


def get_xml(path_xmls, filetype='.*mets\\.xml'):
    from pathlib import Path
    path = Path(path_xmls)
    if not path.exists():
        return []
    return [p for p in path.rglob("*.xml") if re.search(filetype, p.name, flags=re.IGNORECASE)]


def validate_xmls(files, schema_path, batch_name, csv_log_filename, verbose=False):
    validation_errors = {}
    rows = []
    try:
        with open(schema_path, "rb") as f:
            xsd = etree.XMLSchema(etree.parse(f))
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
                tqdm.write(f"⚠️ Error validating {xmlfile.name}: {e}")
            rows.append({"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "XSD", "status": "error", "details": str(e)})
            validation_errors[xmlfile.name] = ['error', str(e)]

    write_csv_log(rows, csv_log_filename)
    return rows


def validate_with_sch(files, schema_path, batch_name, csv_log_filename, verbose=False):
    rows = []
    for xmlfile in tqdm(files):
        if verbose:
            tqdm.write(f"Validating (Schematron): {xmlfile.name}")
        try:
            subprocess.run(["saxon", f"-s:{xmlfile}", f"-xsl:{schema_path}", f"-o:{SVRL_TEMP}"], check=True)
        except Exception as e:
            rows.append({"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "Schematron", "status": "error", "details": f"Saxon failed: {e}"})
            continue

        try:
            tree = etree.parse(SVRL_TEMP)
            failed = tree.xpath("//svrl:failed-assert", namespaces=SVRL_NS)
            if failed:
                details = "; ".join(f"{fa.attrib.get('location', 'unknown')}: {fa.findtext('svrl:text', namespaces=SVRL_NS)}" for fa in failed)
                rows.append({"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "Schematron", "status": "invalid", "details": details})
            else:
                rows.append({"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "Schematron", "status": "valid", "details": ""})
        except Exception as e:
            rows.append({"batch": batch_name, "file": xmlfile.resolve(), "validation_type": "Schematron", "status": "error", "details": f"SVRL parse failed: {e}"})

    write_csv_log(rows, csv_log_filename)
    return rows
