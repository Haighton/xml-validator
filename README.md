# XML Validator

Validate folders of XML files using an XSD schema or Schematron.  
Schematron files are compiled under the hood to XSLT 3.0 using [SchXslt2](https://codeberg.org/dmaus/schxslt2) and executed with [Saxon HE](https://www.saxonica.com/download/).

Designed for batch validation of digitized metadata such as METS or ALTO files.

---

## Features

- Validate XML files using:
    - **XSD** (`.xsd`)
    - **Schematron** (`.sch` → automatically compiled to XSLT3)
    - Precompiled **Schematron XSLT** (`.xsl`, `.xslt`)
- Recursive validation of XML files across multiple folders
- CSV logging of results (batch name, file, type, status, errors)
- Usable as both Python module and CLI
- Optional `--verbose` flag for progress and debug output
- Self-contained: downloads SchXslt2 + Saxon HE locally

---

## Installation

Clone this repo and install locally:

```bash
git clone https://github.com/Haighton/xml-validator.git
cd xml-validator
pip install .
```

---

## First-time setup

Before first use, download dependencies (SchXslt2 + Saxon HE):

```bash
python scripts/download_dependencies.py
```

This will create:

```
xml_validator/schxslt/transpile.xsl
xml_validator/lib/Saxon-HE-12.5.jar
```

---

## Usage

### CLI

```bash
validate-xml ".*mets\.xml" path/to/schema.xsd path/to/batch1 [path/to/batch2 ...] \
  --output path/to/logfolder --verbose
```

### Examples

Validate with XSD:

```bash
validate-xml ".*mets\.xml" schemas/mets_schema.xsd batches/MMKB49_000000004_1_01
```

Validate with Schematron (`.sch`):

```bash
validate-xml ".*alto\.xml" schemas/alto_rules.sch batches/MMKB49_000000006_1_01
```

No need to transpile `.sch` yourself — the tool does it automatically with SchXslt2.

---

## Output

A CSV file `validation_log_<timestamp>.csv` will be written to the folder specified via `--output` (default: current folder).

### Columns

- `batch`: name of the folder the XML came from
- `file`: full path to the validated XML file
- `validation_type`: `XSD` or `Schematron`
- `status`: `valid`, `invalid`, or `error`
- `details`: validation errors or parse failures

---

## Requirements

- Python 3.8+
- `lxml`
- `tqdm`
- Java 11+ (to run bundled Saxon HE jar)

Dependencies:

- [Saxon HE](https://www.saxonica.com/download/) (downloaded automatically to `xml_validator/lib/`)
- [SchXslt2](https://codeberg.org/dmaus/schxslt2) (downloaded automatically to `xml_validator/schxslt/`)

---

## Author

Developed by T.Haighton for KB Digitalisering as a validation backup for KB BKT batches of digitized materials.
