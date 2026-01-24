# Disability and Sensory Impairments

This calculator identifies learning disabilities (intellectual disabilities) and sensory impairments from ICD-10 diagnosis codes.

## Overview

The disability identifier detects three categories of impairments:

1. **Learning Disability / Autism Spectrum Disorder (ASD)**
2. **Visual Impairment**
3. **Hearing Impairment**

## Supported Codes

### Learning Disability / ASD

ICD-10 codes starting with:

| Prefix | Description |
|--------|-------------|
| `F70` | Mild intellectual disabilities |
| `F71` | Moderate intellectual disabilities |
| `F72` | Severe intellectual disabilities |
| `F73` | Profound intellectual disabilities |
| `F78` | Other intellectual disabilities |
| `F79` | Unspecified intellectual disabilities |
| `F84` | Pervasive developmental disorders (including autism) |

### Visual Impairment

ICD-10 codes starting with:

| Prefix | Description |
|--------|-------------|
| `H54` | Blindness and low vision |

### Hearing Impairment

ICD-10 codes starting with:

| Prefix | Description |
|--------|-------------|
| `H90` | Conductive and sensorineural hearing loss |
| `H91` | Other and unspecified hearing loss |

## Usage

### Python API

```python
import polars as pl
from comorbidipy import disability

df = pl.DataFrame({
    "patient_id": ["P001", "P001", "P002", "P003"],
    "icd_code": ["F70", "H54", "H90", "J18"],
})

# Identify impairments
result = disability(
    df,
    id="patient_id",
    code="icd_code",
)

# Result includes binary columns for each impairment type
```

### CLI

```bash
# Basic disability identification
comorbidipy disability input.csv output.csv

# With custom columns
comorbidipy disability input.parquet output.parquet --id pat_id --code diagnosis

# Output as Parquet
comorbidipy disability input.csv output.parquet
```

## Output

The output DataFrame includes:

| Column | Type | Description |
|--------|------|-------------|
| ID column | varies | Patient identifier (original column name) |
| `ld_asd` | Int (0/1) | Learning disability or ASD present |
| `impaired_vision` | Int (0/1) | Visual impairment present |
| `impaired_hearing` | Int (0/1) | Hearing impairment present |

## Example

```python
import polars as pl
from comorbidipy import disability

df = pl.DataFrame({
    "id": [
        "P001", "P001",  # LD + vision
        "P002",          # Hearing only
        "P003",          # No impairments
    ],
    "code": [
        "F70", "H541",   # Mild LD + low vision
        "H900",          # Conductive hearing loss
        "J18",           # Pneumonia (not an impairment)
    ],
})

result = disability(df, id="id", code="code")
print(result)

# Output:
# ┌──────┬────────┬─────────────────┬──────────────────┐
# │ id   ┆ ld_asd ┆ impaired_vision ┆ impaired_hearing │
# ╞══════╪════════╪═════════════════╪══════════════════╡
# │ P001 ┆ 1      ┆ 1               ┆ 0                │
# │ P002 ┆ 0      ┆ 0               ┆ 1                │
# │ P003 ┆ 0      ┆ 0               ┆ 0                │
# └──────┴────────┴─────────────────┴──────────────────┘
```

## Use Cases

This calculator is useful for:

- **Epidemiological studies**: Identifying cohorts with specific impairments
- **Healthcare planning**: Understanding patient populations
- **Reasonable adjustments**: Flagging patients who may need communication support
- **Quality metrics**: Stratifying outcomes by disability status

## Notes

1. **ICD-10 only**: This calculator only supports ICD-10 codes
2. **Prefix matching**: Codes are matched by their first 3 characters
3. **Binary output**: Each patient gets a 0 or 1 for each impairment type
4. **Multiple impairments**: A patient can have multiple impairments flagged

## Clinical Considerations

When using these flags:

- **Learning disability**: May indicate need for easy-read materials, longer appointments, or carer involvement
- **Visual impairment**: Consider large print, audio information, or assistance with navigation
- **Hearing impairment**: Consider sign language interpreters, written communication, or hearing loops
