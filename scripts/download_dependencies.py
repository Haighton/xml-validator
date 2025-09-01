#!/usr/bin/env python3
"""
Download dependencies for xml-validator:
- SchXslt2 (Schematron transpiler)
- Saxon HE (XSLT 3.0 processor)
- xmlresolver (required for Saxon >= 12)

Run this once after cloning the repo.
"""

import urllib.request
import zipfile
import shutil
import sys
from pathlib import Path

# Import config directly from package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from xml_validator import config  # noqa: E402


def download_file(url: str, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"⬇️  Downloading {url} -> {out_path}")
    urllib.request.urlretrieve(url, out_path)


def main():
    # --- SchXslt2 ---
    schxslt_zip = Path("schxslt2.zip")
    schxslt_url = (
        f"https://codeberg.org/SchXslt/schxslt2/releases/download/v{config.SCHXSLT_VERSION}/"
        f"schxslt2-{config.SCHXSLT_VERSION}.zip"
    )
    download_file(schxslt_url, schxslt_zip)

    with zipfile.ZipFile(schxslt_zip, "r") as zf:
        member = f"schxslt2-{config.SCHXSLT_VERSION}/transpile.xsl"
        target = config.SCHXSLT_TRANSPILER
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)
        print(f"✅ Extracted transpile.xsl -> {target}")

    schxslt_zip.unlink()

    # --- Saxon ---
    saxon_url = (
        f"https://repo1.maven.org/maven2/net/sf/saxon/Saxon-HE/"
        f"{config.SAXON_VERSION}/Saxon-HE-{config.SAXON_VERSION}.jar"
    )
    saxon_jar = config.LIB_DIR / f"Saxon-HE-{config.SAXON_VERSION}.jar"
    if saxon_jar.exists():
        print(f"ℹ️ Saxon already exists: {saxon_jar}")
    else:
        download_file(saxon_url, saxon_jar)
        print(f"✅ Downloaded Saxon -> {saxon_jar}")

    # --- xmlresolver (only for Saxon >= 12) ---
    major_version = int(config.SAXON_VERSION.split(".")[0])
    if major_version >= 12:
        xmlresolver_jar = config.LIB_DIR / f"xmlresolver-{config.XMLRESOLVER_VERSION}.jar"
        if xmlresolver_jar.exists():
            print(f"ℹ️ xmlresolver already exists: {xmlresolver_jar}")
        else:
            xmlresolver_url = (
                f"https://repo1.maven.org/maven2/org/xmlresolver/xmlresolver/"
                f"{config.XMLRESOLVER_VERSION}/xmlresolver-{config.XMLRESOLVER_VERSION}.jar"
            )
            download_file(xmlresolver_url, xmlresolver_jar)
            print(f"✅ Downloaded xmlresolver -> {xmlresolver_jar}")

    # --- Verify classpath ---
    print("\n🔍 Verifying JARs in lib/ ...")
    jars = list(config.LIB_DIR.glob("*.jar"))
    if not jars:
        print("❌ No JARs found in lib/. Something went wrong.")
        sys.exit(1)

    for j in jars:
        print(f"   - {j.name}")

    print("\n✅ Dependencies are up to date")
    print(f"Classpath: {config.CLASSPATH}")


if __name__ == "__main__":
    main()
