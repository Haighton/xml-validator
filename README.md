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
- Recursive or non-recursive validation (`--recursive`)
- CSV logging of results (batch, file, type, status, errors)
- Logs are rotated automatically and stored in `./output/logs/`
- Usable as both Python module and CLI
- Configurable via `config.yaml` (all CLI options can be set in advance)
- **Profiles**: reusable setups defined in `config.yaml`
- Parallel validation across batches with automatic worker detection
- Optional `--verbose` flag for detailed output
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
xml_validator/lib.xmlresolver-5.2.2.jar
```

---

## Usage

### CLI

Example usage:

```bash
validate-xml -f ".*_mets\.xml$" -s schemas/mets_schema.xsd -b batches/Kranten -o ./output -v
```

### Examples

Validate with XSD:

```bash
validate-xml -f ".*_mets\.xml$" -s schemas/mets_schema.xsd -b batches/MMKB49_000000004_1_01
```

Validate with Schematron (`.sch`):

```bash
validate-xml -f ".*alto\.xml" -s schemas/alto_rules.sch -b batches/MMKB49_000000006_1_01
```

Use recursive search:

```bash
validate-xml -r -f ".*_mets\.xml$" -s schemas/mets_schema.xsd -b batches/Kranten
```

---

## Config file

All CLI options can also be set in a `config.yaml` file.  
Here’s an example:

```yaml
# Default configuration for xml-validator

# Pattern for XML files (regex or glob style)
file_pattern: ".*_mets\\.xml$"

# Path to schema (XSD, Schematron .sch, or compiled XSLT .xsl/.xslt)
schema: "schemas/mets_schema.xsd"

# One or more batch directories to validate
batches:
  - "batches/Kranten"
  - "batches/Tijdschriften"

# Output folder for CSV logs
output: "./output"

# Verbose logging (true/false)
verbose: false

# Parallel worker configuration
jobs: null        # null = auto detect (cores-1, capped at 8)

# Search recursively for XML files inside batches
recursive: false

# Logging configuration
log_size: 5242880   # 5 MB max logfile size
log_backups: 5      # number of rotated log files to keep

# Predefined profiles for common use cases
profiles:
  mets:
    pattern: ".*_mets\\.xml$"
    schema: "schemas/mets_schema.xsd"
  alto:
    pattern: ".*alto\\.xml"
    schema: "schemas/alto_rules.sch"
  mods:
    pattern: ".*mods\\.xml"
    schema: "schemas/mods_schema.xsd"
```

You can check the effective merged configuration with:

```bash
validate-xml --print-config
```

---

## Profiles

List available profiles:

```bash
validate-xml --list-profiles
```

Use a profile:

```bash
validate-xml --profile mets -b batches/Kranten
```

---

## Output

- CSV files are written to `./output/validation_log_<timestamp>.csv`
- Logs are written to `./output/logs/validation.log` (with rotation)

### CSV columns
 
- `file`: full path to the validated XML file  
- `schema`: name of the schema used for validation
- `validation_type`: `XSD` or `Schematron`  
- `status`: `valid`, `invalid`, `error`, or `skipped`  
- `details`: validation errors or parse failures  

---

## CLI Options

| Flag / Option       | Description                                                                 | Default              |
|---------------------|-----------------------------------------------------------------------------|----------------------|
| `-c, --config`      | Path to YAML config file                                                    | `config.yaml`        |
| `-f, --file-pattern`| Glob/regex pattern for XML file matching                                    | required / config    |
| `-s, --schema`      | Path to XSD, Schematron (.sch), or compiled XSLT                            | required / config    |
| `-b, --batches`     | One or more batch directories to validate                                   | required / config    |
| `-o, --output`      | Output directory for CSV logs                                               | `./output`           |
| `-r, --recursive`   | Search for XML files recursively in batch directories                      | `false`              |
| `-v, --verbose`     | Enable verbose output                                                       | `false`              |
| `-j, --jobs`        | Number of parallel workers (`null` = auto detect)                           | auto (cores-1/capped)|
| `--profile`         | Use a predefined profile from config.yaml                                   | —                    |
| `--list-profiles`   | List available profiles from config.yaml                                    | —                    |
| `--print-config`    | Print the merged configuration (config.yaml + CLI overrides) and exit       | —                    |
| `--version`         | Print program version and exit                                              | —                    |

---

## Requirements

- Python 3.8+  
- `lxml`  
- `tqdm`  
- `PyYAML`  
- Java 11+ (to run bundled Saxon HE jar)  

Dependencies (downloaded automatically via `scripts/download_dependencies.py`):  
- [Saxon HE](https://www.saxonica.com/download/)  
- [SchXslt2](https://codeberg.org/dmaus/schxslt2)
- [xmlresolver](https://xmlresolver.org/?utm_source=chatgpt.com)  

---

## Author

Developed by T.Haighton for KB Digitalisering as a validation backup for KB BKT batches of digitized materials.
