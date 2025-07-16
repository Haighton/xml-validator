# XML Validator

Validate folders of XML files using an XSD schema or Schematron (compiled XSLT 2.0).

Designed for batch validation of digitized metadata such as METS or ALTO files.

## Features

- ✅ Validate XML files using XSD or compiled Schematron (XSLT)
- 📂 Support for recursive validation of XMLs across multiple folders
- 🧾 CSV logging of validation results (including batch name, file, type, status, and errors)
- 🐍 Usable as both Python module and CLI
- 🔍 Optional `--verbose` flag for progress and debug output

## Installation

Clone this repo and install locally:

```bash
git clone https://github.com/YOUR_USERNAME/xml_validator.git
cd xml_validator
pip install .
```

## Usage

Schematron files cannot be used directly for validation. You must first convert them to XSLT using a processor like [SchXslt](https://codeberg.org/SchXslt/schxslt2).


### CLI

```bash
validate-xml ".*mets\.xml" path/to/schema.xsd path/to/batch1 [path/to/batch2 ...] \
  --output path/to/logfolder --verbose
```

### Example

```bash
validate-xml ".*mets\.xml" schemas/mets_schema.xsd batches/MMKB49_000000004_1_01
```

### Output

A CSV file `validation_log_<timestamp>.csv` will be written to the folder specified via `--output` (default: current folder).

### Columns

- `batch`: name of the folder the XML came from
- `file`: full path to the validated XML file
- `validation_type`: `XSD` or `Schematron`
- `status`: `valid`, `invalid`, or `error`
- `details`: validation errors or parse failures


## Requirements

- Python 3.7+
- `lxml`
- `tqdm`
- External dependency: [Saxon HE](https://www.saxonica.com/download/java.xml) must be installed and available in your PATH for Schematron validation.


## Author

Developed by THA010 as a validation backup for KB BKT batches of digitized materials.
