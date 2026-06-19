import os
from pathlib import Path

# Namespace used in SVRL reports.
# (Het SVRL-rapport zelf gaat per validatie naar een uniek temp-bestand,
#  zie validate_single_sch, om races bij parallel draaien te voorkomen.)
SVRL_NS = {"svrl": "http://purl.oclc.org/dsdl/svrl"}

# ---------------- Dependency settings ---------------- #

BASE_DIR = Path(__file__).resolve().parent
LIB_DIR = BASE_DIR / "lib"

# Saxon HE (XSLT 3.0 processor)
SAXON_VERSION = "12.5"

# SchXslt2 transpiler (Schematron -> XSLT3)
SCHXSLT_VERSION = "1.4.4"
SCHXSLT_TRANSPILER = BASE_DIR / "schxslt" / "transpile.xsl"

# xmlresolver (needed for Saxon >= 12)
XMLRESOLVER_VERSION = "5.2.2"

# Build classpath: all jars inside lib/
# (Saxon + xmlresolver jars are put here by download_dependencies.py)
CLASSPATH = os.pathsep.join(str(jar.resolve()) for jar in LIB_DIR.glob("*.jar"))
