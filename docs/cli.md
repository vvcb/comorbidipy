# Command Line Interface

comorbidipy provides a powerful CLI for calculating comorbidity scores from data files.

## Installation

The CLI is automatically available after installing comorbidipy:

```bash
pip install comorbidipy
```

Two command aliases are available:

- `comorbidipy` - Full name
- `cmpy` - Short alias

## Quick Start

```bash
# Calculate Charlson score
comorbidipy charlson input.csv output.csv

# Calculate Elixhauser score
comorbidipy elixhauser input.parquet output.parquet

# Calculate HFRS
comorbidipy hfrs input.csv output.csv

# Identify disabilities
comorbidipy disability input.csv output.csv
```

## Global Options

All commands support these common options:

| Option | Default | Description |
|--------|---------|-------------|
| `--id` | `id` | Column name containing patient identifiers |
| `--code` | `code` | Column name containing ICD codes |
| `--verbose` / `-v` | False | Enable verbose logging |

## Commands

### charlson

Calculate Charlson Comorbidity Index.

```bash
comorbidipy charlson [OPTIONS] INPUT OUTPUT
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--mapping` | `quan` | Mapping variant: quan, swedish, australian, shmi |
| `--weights` | `charlson` | Weighting scheme: charlson, quan, shmi, shmi_modified |
| `--age-col` | None | Column name for age (enables age adjustment) |
| `--icd-version` | `10` | ICD version: 9 or 10 |
| `--no-assign0` | False | Don't zero out less severe conditions |

**Examples:**

```bash
# Basic Charlson with defaults
comorbidipy charlson data.csv results.csv

# Swedish mapping with age adjustment
comorbidipy charlson data.csv results.parquet \
    --mapping swedish \
    --age-col patient_age

# ICD-9 codes with Quan weights
comorbidipy charlson data.csv results.csv \
    --icd-version 9 \
    --weights quan
```

### elixhauser

Calculate Elixhauser Comorbidity Index.

```bash
comorbidipy elixhauser [OPTIONS] INPUT OUTPUT
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--weights` | `vanwalraven` | Weighting scheme: vanwalraven, swiss |
| `--icd-version` | `10` | ICD version: 9 or 10 |
| `--no-assign0` | False | Don't zero out less severe conditions |

**Examples:**

```bash
# Basic Elixhauser
comorbidipy elixhauser data.csv results.csv

# With Swiss weights
comorbidipy elixhauser data.parquet results.parquet --weights swiss
```

### hfrs

Calculate Hospital Frailty Risk Score.

```bash
comorbidipy hfrs [OPTIONS] INPUT OUTPUT
```

**Examples:**

```bash
# Basic HFRS
comorbidipy hfrs admissions.csv frailty.csv

# Custom column names
comorbidipy hfrs data.parquet results.parquet --id patient_id --code diagnosis
```

### disability

Identify learning disabilities and sensory impairments.

```bash
comorbidipy disability [OPTIONS] INPUT OUTPUT
```

**Examples:**

```bash
# Basic disability identification
comorbidipy disability data.csv results.csv

# From Parquet to Parquet
comorbidipy disability data.parquet results.parquet
```

### info

Display information about comorbidipy.

```bash
comorbidipy info
```

Shows version number and available calculators.

## Supported File Formats

The CLI automatically detects file format from the extension:

| Extension | Format | Read | Write |
|-----------|--------|------|-------|
| `.csv` | CSV | ✅ | ✅ |
| `.parquet` | Parquet | ✅ | ✅ |
| `.json` | JSON | ✅ | ✅ |
| `.ndjson` | Newline-delimited JSON | ✅ | ✅ |
| `.avro` | Avro | ✅ | ✅ |

**Note**: Avro support requires the `pyarrow` library.

## Large Files

For files that don't fit in memory, use Parquet format which supports lazy evaluation:

```bash
# Process large Parquet file efficiently
comorbidipy charlson large_data.parquet results.parquet
```

## Examples

### Complete Workflow

```bash
# 1. Check input file
head -5 input.csv
# id,code,age
# P001,I21,65
# P001,E112,65
# P002,I50,72

# 2. Calculate Charlson with age adjustment
comorbidipy charlson input.csv output.csv \
    --age-col age \
    --verbose

# 3. Check results
head -5 output.csv
```

### Pipeline Usage

```bash
# Chain with other tools
comorbidipy charlson input.csv /dev/stdout | \
    csvstat --mean comorbidity_score
```

### Batch Processing

```bash
# Process multiple files
for f in data/*.csv; do
    comorbidipy charlson "$f" "results/$(basename "$f")"
done
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid input, missing columns, etc.) |

## Error Messages

Common errors and solutions:

| Error | Solution |
|-------|----------|
| "Column 'id' not found" | Use `--id` to specify the correct column name |
| "Column 'code' not found" | Use `--code` to specify the correct column name |
| "Unsupported file format" | Use a supported extension (.csv, .parquet, etc.) |
| "File not found" | Check the input file path |

## Logging

Use `--verbose` or `-v` for detailed logging:

```bash
comorbidipy charlson input.csv output.csv --verbose

# Output:
# INFO: Reading input file: input.csv
# INFO: Found 1000 rows, 50 unique patients
# INFO: Calculating Charlson score with quan mapping
# INFO: Writing results to: output.csv
# INFO: Done!
```
