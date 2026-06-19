import os
import subprocess
import tempfile
from pathlib import Path

from lxml import etree

from .config import CLASSPATH, SVRL_NS


def validate_single_xsd(
        xmlfile: Path,
        schema_path: Path,
        schema_name: str,
        verbose: bool = False) -> dict:
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


def validate_single_sch(
        xmlfile: Path,
        schema_path: Path,
        schema_name: str,
        verbose: bool = False) -> dict:
    """Valideer één XML-bestand tegen een Schematron (gecompileerd naar XSLT).

    Schrijft het SVRL-rapport naar een UNIEK temp-bestand per aanroep, zodat
    parallel draaiende validaties elkaars rapport niet overschrijven.
    """
    svrl_fd, svrl_name = tempfile.mkstemp(suffix=".svrl.xml")
    os.close(svrl_fd)
    svrl_temp = Path(svrl_name)
    try:
        cmd = [
            "java",
            "-cp", CLASSPATH,
            "net.sf.saxon.Transform",
            f"-s:{xmlfile}",
            f"-xsl:{schema_path}",
            f"-o:{svrl_temp}"
        ]

        if verbose:
            print("-Running Java command:")
            print("   " + " ".join(cmd))

        subprocess.run(cmd, check=True)

        tree = etree.parse(str(svrl_temp))
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
    finally:
        svrl_temp.unlink(missing_ok=True)
