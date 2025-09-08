# XML Validator

Een command-line tool om XML-bestanden te valideren met **XSD** en/of **Schematron**.

## Features

- Valideer één of meerdere batches met XML-bestanden.
- Ondersteuning voor **XSD**, **Schematron (.sch)** en **XSLT-based Schematron**.
- **Parallel verwerking** van batches (automatisch aantal workers).
- **Profiles** in `config.yaml` voor veelgebruikte validatie-sets.
- **Meerdere schema’s per pattern** (bijv. een METS-bestand zowel XSD- als Schematron-validatie).
- **Logging** naar bestand én console.
- CSV-resultaten met status per bestand en schema.

---

## Installatie

1. Clone de repo:

```bash
git clone https://github.com/KB/xml-validator.git
cd xml-validator
```

2. Maak een virtualenv (optioneel) en installeer dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows

pip install -e .
```

## 📦 Java Dependencies

Voor Schematron-validatie gebruikt `xml-validator` externe Java-libraries:

- **SchXslt2** → transpiler van `.sch` naar `.xsl`
- **Saxon HE** → XSLT 3.0 processor
- **xmlresolver** → resolver voor Saxon ≥ 12

Om dit te installeren, run je na het clonen:

```bash
python scripts/download_dependencies.py
```

Dit script doet het volgende:

1. Download SchXslt2 en extraheert transpile.xsl naar de juiste plek.
2. Download Saxon HE JAR naar lib/.
3. (Indien nodig) download xmlresolver JAR voor Saxon ≥ 12.
4. Print de volledige classpath zodat je kunt controleren of alles goed staat.

Na afloop zie je een overzicht:

```
✅ Dependencies are up to date
Classpath: lib/Saxon-HE-12.5.jar:lib/xmlresolver-6.0.5.jar
```

> Dit hoef je slechts één keer te doen na het clonen of als je `config.py` een nieuwe versie van de dependencies specificeert.

---

## Configuratie

De standaardconfiguratie staat in `config.yaml`:

```yaml
# Output folder voor CSV logs
output: "./output"

# Logging configuratie
log_path: "./logs"      # map voor logbestanden
log_size: 5242880       # max 5 MB per logfile
log_backups: 5          # aantal rotated logs bewaren
```

### Voorbeeld profiel met meerdere schema’s per pattern

```yaml
profiles:
  tk4-kranten:
    validations:
      - pattern: ".*_mets\\.xml$"
        schemas:
          - "schemas/kbdg_mets_kranten_SIP.xsd"
          - "schemas/mets_gesegmenteerd.sch"
      - pattern: ".*_alto\\.xml$"
        schemas:
          - "schemas/kbdg_alto.xsd"
          - "schemas/alto.sch"
      - pattern: ".*_pakbon\\.xml$"
        schemas:
          - "schemas/kbdg_pakbon.xsd"
          - "schemas/pakbon.sch"
```

---

## Gebruik

### Profielen tonen
```bash
python -m xml_validator --list-profiles
```

### Config controleren
```bash
python -m xml_validator --profile tk4-kranten --print-config
```

### Batches valideren
```bash
python -m xml_validator --profile tk4-kranten
```

### Meerdere schema’s via CLI

Het is ook mogelijk om meerdere schema’s direct mee te geven via de `--schema` (`-s`) optie.
Hiermee hoef je geen profiel in `config.yaml` te definiëren.

Voorbeeld: een METS-bestand zowel met XSD als Schematron valideren:

```bash
python -m xml_validator \
  -f ".*_mets\.xml$" \
  -s schemas/mets_schema.xsd schemas/mets_rules.sch \
  -b batches/Kranten
```

Dit voert twee validaties uit op elk `*_mets.xml` bestand:

1. XSD-validatie met mets_schema.xsd
2. Schematron-validatie met mets_rules.sch

De resultaten komen in de CSV-log als twee aparte regels per bestand.

Resultaten worden gelogd naar:
- **CSV** in `output/validation_log_<timestamp>.csv`
- **Logfile** in `logs/validation.log` (met rotatie)

---

## ⚡ CLI Opties

| Optie | Beschrijving | Default |
|-------|--------------|---------|
| `-h, --help` | Toon helptekst | – |
| `-c CONFIG, --config CONFIG` | Pad naar `config.yaml` | `config.yaml` |
| `-f FILE_PATTERN, --file-pattern FILE_PATTERN` | Regex om bestanden te matchen | `.*\.xml$` |
| `-s SCHEMA, --schema SCHEMA` | Pad naar XSD, Schematron (.sch) of XSLT | – |
| `-b BATCHES [BATCHES ...], --batches BATCHES [BATCHES ...]` | Eén of meer batchmappen met XML-bestanden | – |
| `-o OUTPUT, --output OUTPUT` | Map voor CSV-resultaten | `output` |
| `-v, --verbose` | Meer logging (debugniveau) | `false` |
| `-j JOBS, --jobs JOBS` | Aantal parallelle workers | auto (cores, capped op 8) |
| `-r, --recursive` | Zoek XML-bestanden recursief in batchmappen | `false` |
| `--profile PROFILE` | Gebruik een profiel uit `config.yaml` | – |
| `--list-profiles` | Toon alle beschikbare profielen en stop | – |
| `--print-config` | Print effectieve configuratie en stop | – |
| `--version` | Toon huidige versie | – |

---

## 📊 CSV Output

CSV bevat deze kolommen:

- `file` → pad naar XML bestand  
- `schema` → gebruikt schema  
- `validation_type` → XSD / Schematron  
- `status` → valid / invalid / error / skipped  
- `details` → foutmelding of extra info  

---


## Ontwikkeld door

Thomas Haighton thomas.haighton@kb.nl – Koninklijke Bibliotheek - Digitalisering, 09-2025
