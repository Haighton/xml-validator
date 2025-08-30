import subprocess
import tempfile
from pathlib import Path
from .config import SAXON_JAR, SCHXSLT_TRANSPILER


def compile_schematron(sch_file: Path) -> Path:
    """
    Compile a .sch Schematron file into an XSLT3 validator using SchXslt2.
    Returns path to the compiled XSL file (temp file).
    """
    if not SCHXSLT_TRANSPILER.exists():
        raise FileNotFoundError(f"SchXslt2 transpiler not found: {SCHXSLT_TRANSPILER}")
    if not SAXON_JAR.exists():
        raise FileNotFoundError(f"Saxon JAR not found: {SAXON_JAR}")

    compiled_xsl = Path(tempfile.mkstemp(suffix=".xsl")[1])

    cmd = [
        "java", "-jar", str(SAXON_JAR),
        f"-s:{sch_file}",
        f"-xsl:{SCHXSLT_TRANSPILER}",
        f"-o:{compiled_xsl}"
    ]
    subprocess.run(cmd, check=True)
    return compiled_xsl
