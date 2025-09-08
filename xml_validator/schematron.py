import subprocess
import tempfile
from pathlib import Path

from .config import CLASSPATH, SCHXSLT_TRANSPILER


def compile_schematron(sch_file: Path, verbose: bool = False) -> Path:
    """
    Compile a .sch Schematron file into an XSLT3 validator using SchXslt2.
    Returns path to the compiled XSL file (temp file).
    """
    if not SCHXSLT_TRANSPILER.exists():
        raise FileNotFoundError(f"SchXslt2 transpiler not found: {SCHXSLT_TRANSPILER}")

    compiled_xsl = Path(tempfile.mkstemp(suffix=".xsl")[1])

    cmd = [
        "java",
        "-cp", CLASSPATH,
        "net.sf.saxon.Transform",
        f"-s:{sch_file}",
        f"-xsl:{SCHXSLT_TRANSPILER}",
        f"-o:{compiled_xsl}"
    ]

    if verbose:
        print("-Running Java command:")
        print("   " + " ".join(cmd))

    subprocess.run(cmd, check=True)

    return compiled_xsl
