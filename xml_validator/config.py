from pathlib import Path

# Temporary output file for SVRL validation reports
SVRL_TEMP = Path("svrl_temp.xml")

# Namespace used in SVRL reports
SVRL_NS = {"svrl": "http://purl.oclc.org/dsdl/svrl"}

# ---------------- Dependency settings ---------------- #

BASE_DIR = Path(__file__).resolve().parent

# Saxon HE (XSLT 3.0 processor)
SAXON_VERSION = "12.5"
SAXON_JAR = BASE_DIR / "lib" / f"Saxon-HE-{SAXON_VERSION}.jar"

# SchXslt2 transpiler (Schematron -> XSLT3)
SCHXSLT_VERSION = "1.4.4"
SCHXSLT_TRANSPILER = BASE_DIR / "schxslt" / "transpile.xsl"
