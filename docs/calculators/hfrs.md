# Hospital Frailty Risk Score (HFRS)

The Hospital Frailty Risk Score (HFRS) identifies frailty in hospital patients aged 75 years and older using ICD-10 codes from hospital admissions.

## Overview

The HFRS was developed using Hospital Episode Statistics data from England and validated against frailty phenotype measures. It identifies 109 ICD-10 codes associated with frailty.

## Eligibility

**Important**: The HFRS is validated for patients aged 75 years and older. Scores for younger patients should be interpreted with caution.

## Risk Categories

| Score Range | Risk Category | Interpretation |
|-------------|---------------|----------------|
| < 5 | Low risk | Low likelihood of frailty |
| 5-15 | Intermediate risk | Moderate likelihood of frailty |
| > 15 | High risk | High likelihood of frailty |

## Usage

### Python API

```python
import polars as pl
from comorbidipy import hfrs

df = pl.DataFrame({
    "patient_id": ["P001", "P001", "P002", "P002", "P003"],
    "icd_code": ["F00", "R26", "G30", "W19", "J18"],
})

# Calculate HFRS
result = hfrs(
    df,
    id="patient_id",
    code="icd_code",
)

# Result includes:
# - patient_id
# - hfrs_score (continuous score)
# - hfrs_category (Low/Intermediate/High)
```

### CLI

```bash
# Basic HFRS calculation
comorbidipy hfrs input.csv output.csv

# With custom columns
comorbidipy hfrs input.parquet output.parquet --id pat_id --code diagnosis

# Output as Parquet
comorbidipy hfrs input.csv output.parquet
```

## ICD-10 Codes

The HFRS uses 109 ICD-10 codes grouped into categories with associated weights:

### High-weight codes (≥ 3.0)

These codes have the strongest association with frailty:

- `F00-F03`: Dementia
- `G30-G31`: Alzheimer's disease and other degenerative diseases
- `R29.6`: Tendency to fall
- `W01-W19`: Falls
- `R26`: Abnormalities of gait and mobility
- `R54`: Senility

### Medium-weight codes (1.0-2.9)

- `E86`: Volume depletion (dehydration)
- `N39.0`: Urinary tract infection
- `J18`: Pneumonia
- `L89`: Pressure ulcer
- `I63`: Cerebral infarction

### Low-weight codes (< 1.0)

- Various codes indicating frailty-associated conditions

## Output

The output DataFrame includes:

| Column | Type | Description |
|--------|------|-------------|
| ID column | varies | Patient identifier (original column name) |
| `hfrs_score` | Float | Continuous frailty score |
| `hfrs_category` | String | "Low", "Intermediate", or "High" |

## Example

```python
import polars as pl
from comorbidipy import hfrs

# Patient with multiple frailty indicators
df = pl.DataFrame({
    "id": ["P001", "P001", "P001", "P002"],
    "code": [
        "F00",   # Dementia
        "W19",   # Fall
        "R26",   # Gait abnormality
        "J18",   # Pneumonia only
    ],
})

result = hfrs(df, id="id", code="code")
print(result)

# Output:
# ┌──────┬────────────┬───────────────┐
# │ id   ┆ hfrs_score ┆ hfrs_category │
# ╞══════╪════════════╪═══════════════╡
# │ P001 ┆ 8.5        ┆ Intermediate  │
# │ P002 ┆ 1.2        ┆ Low           │
# └──────┴────────────┴───────────────┘
```

## Clinical Use

The HFRS helps identify patients who may benefit from:

- Comprehensive geriatric assessment
- Early discharge planning
- Falls prevention programs
- Medication review
- Nutritional assessment

## Limitations

1. **Age restriction**: Only validated for patients ≥75 years
2. **ICD-10 only**: Does not support ICD-9 codes
3. **Hospital data**: Developed from hospital admissions data
4. **UK validation**: Originally validated using English NHS data

## References

1. Gilbert T, et al. Development and validation of a Hospital Frailty Risk Score focusing on older people in acute care settings using electronic hospital records: an observational study. Lancet. 2018;391(10132):1775-1782.
