#!/usr/bin/env python3
"""
Download dependencies for xml-validator:
- SchXslt2 (Schematron transpiler)
- Saxon HE (XSLT 3.0 processor)

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
    print(f"Downloading {url} -> {out_path}")
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
        print(f"Extracted transpile.xsl -> {target}")

    schxslt_zip.unlink()

    # --- Saxon ---
    saxon_url = (
        f"https://repo1.maven.org/maven2/net/sf/saxon/Saxon-HE/"
        f"{config.SAXON_VERSION}/Saxon-HE-{config.SAXON_VERSION}.jar"
    )
    if config.SAXON_JAR.exists():
        print(f"ℹ️ Saxon already exists: {config.SAXON_JAR}")
    else:
        download_file(saxon_url, config.SAXON_JAR)

    print("\n✅ Dependencies are up to date.")
    print(f"   SchXslt2 -> {config.SCHXSLT_TRANSPILER}")
    print(f"   Saxon    -> {config.SAXON_JAR}")


if __name__ == "__main__":
    main()
