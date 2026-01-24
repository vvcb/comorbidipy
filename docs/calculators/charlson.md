# Charlson Comorbidity Index

The Charlson Comorbidity Index (CCI) is a method of categorizing comorbidities of patients based on ICD diagnosis codes. Each comorbidity category has an associated weight based on the adjusted risk of mortality or resource use.

## Overview

The original Charlson index was developed in 1987 and has been updated several times with different mapping schemes for ICD-9 and ICD-10 codes.

## Supported Mappings

| Mapping | ICD-9 | ICD-10 | Description |
|---------|-------|--------|-------------|
| `quan` | ✅ | ✅ | Quan et al. (2005) - Most widely used |
| `swedish` | ❌ | ✅ | Swedish National Patient Register |
| `australian` | ❌ | ✅ | Australian IHW adaptation |
| `shmi` | ❌ | ✅ | UK Summary Hospital-level Mortality Indicator |

## Weighting Schemes

| Weighting | Description |
|-----------|-------------|
| `charlson` | Original 1987 weights (1-6 scale) |
| `quan` | Quan et al. updated weights |
| `shmi` | UK SHMI weights |
| `shmi_modified` | Modified SHMI weights |

## Comorbidity Categories

The Charlson index identifies 17 comorbidity categories:

| Abbreviation | Condition | Original Weight |
|--------------|-----------|-----------------|
| `ami` | Acute myocardial infarction | 1 |
| `chf` | Congestive heart failure | 1 |
| `pvd` | Peripheral vascular disease | 1 |
| `cevd` | Cerebrovascular disease | 1 |
| `dementia` | Dementia | 1 |
| `copd` | Chronic obstructive pulmonary disease | 1 |
| `rheumd` | Rheumatoid disease | 1 |
| `pud` | Peptic ulcer disease | 1 |
| `mld` | Mild liver disease | 1 |
| `diab` | Diabetes without complications | 1 |
| `diabwc` | Diabetes with complications | 2 |
| `hp` | Hemiplegia or paraplegia | 2 |
| `rend` | Renal disease | 2 |
| `canc` | Cancer (any malignancy) | 2 |
| `msld` | Moderate or severe liver disease | 3 |
| `metacanc` | Metastatic solid tumor | 6 |
| `aids` | AIDS/HIV | 6 |

## Usage

### Python API

```python
import polars as pl
from comorbidipy import comorbidity, ScoreType, MappingVariant, WeightingVariant

df = pl.DataFrame({
    "id": ["P001", "P001", "P002"],
    "code": ["I21", "E112", "I50"],
    "age": [65, 65, 72],
})

# Basic calculation
result = comorbidity(
    df,
    id="id",
    code="code",
    score=ScoreType.CHARLSON,
    age=None,
)

# With age adjustment
result = comorbidity(
    df,
    id="id",
    code="code",
    age="age",
    score=ScoreType.CHARLSON,
    weighting=WeightingVariant.CHARLSON,
)

# Using Swedish mapping
result = comorbidity(
    df,
    id="id",
    code="code",
    score=ScoreType.CHARLSON,
    variant=MappingVariant.SWEDISH,
    age=None,
)
```

### CLI

```bash
# Basic Charlson calculation
comorbidipy charlson input.csv output.csv

# With specific mapping and weights
comorbidipy charlson input.csv output.parquet \
    --mapping quan \
    --weights charlson \
    --age-col age

# Using Swedish mapping
comorbidipy charlson input.csv output.csv --mapping swedish
```

## Age Adjustment

When age is provided with the original Charlson weights, the score includes an age component:

- Age 40-49: +1 point
- Age 50-59: +2 points
- Age 60-69: +3 points
- Age 70+: +4 points

The output includes:
- `comorbidity_score`: Base score without age adjustment
- `age_adj_comorbidity_score`: Score with age adjustment
- `survival_10yr`: Estimated 10-year survival probability

## Assign Zero Logic

By default (`assign0=True`), when a more severe form of a condition is present, the less severe form is set to 0:

- `mld` (mild liver disease) → 0 if `msld` (moderate/severe) present
- `diab` (diabetes) → 0 if `diabwc` (diabetes with complications) present
- `canc` (cancer) → 0 if `metacanc` (metastatic cancer) present

To keep both forms:

```python
result = comorbidity(df, assign0=False, age=None)
```

## Output

The output DataFrame includes:
- Patient ID column
- Binary columns (0/1) for each of the 17 comorbidity categories
- `comorbidity_score`: Weighted sum of comorbidities
- `age_adj_comorbidity_score`: (if age provided with Charlson weights)
- `survival_10yr`: (if age provided with Charlson weights)

## References

1. Charlson ME, et al. A new method of classifying prognostic comorbidity in longitudinal studies. J Chronic Dis. 1987;40(5):373-383.
2. Quan H, et al. Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data. Med Care. 2005;43(11):1130-1139.
