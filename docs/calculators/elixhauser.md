# Elixhauser Comorbidity Index

The Elixhauser Comorbidity Index identifies 31 comorbidity categories that affect hospital outcomes, resource utilization, and mortality.

## Overview

The Elixhauser index was developed in 1998 as a more comprehensive alternative to the Charlson index, capturing a broader range of comorbid conditions.

## Supported Mappings

| Mapping | ICD-9 | ICD-10 | Description |
|---------|-------|--------|-------------|
| `quan` | ✅ | ✅ | Quan et al. enhanced ICD coding |

## Weighting Schemes

| Weighting | Description |
|-----------|-------------|
| `vanwalraven` | van Walraven et al. (2009) - mortality prediction |
| `swiss` | Swiss adaptation for mortality prediction |

## Comorbidity Categories

The Elixhauser index identifies 31 comorbidity categories:

| Abbreviation | Condition |
|--------------|-----------|
| `chf` | Congestive heart failure |
| `carit` | Cardiac arrhythmias |
| `valv` | Valvular disease |
| `pcd` | Pulmonary circulation disorders |
| `pvd` | Peripheral vascular disorders |
| `hypunc` | Hypertension, uncomplicated |
| `hypc` | Hypertension, complicated |
| `para` | Paralysis |
| `ond` | Other neurological disorders |
| `cpd` | Chronic pulmonary disease |
| `diabunc` | Diabetes, uncomplicated |
| `diabc` | Diabetes, complicated |
| `hypothy` | Hypothyroidism |
| `rf` | Renal failure |
| `ld` | Liver disease |
| `pud` | Peptic ulcer disease (excluding bleeding) |
| `aids` | AIDS/HIV |
| `lymph` | Lymphoma |
| `metacanc` | Metastatic cancer |
| `solidtum` | Solid tumor without metastasis |
| `rheumd` | Rheumatoid arthritis/collagen vascular |
| `coag` | Coagulopathy |
| `obes` | Obesity |
| `wloss` | Weight loss |
| `fed` | Fluid and electrolyte disorders |
| `blane` | Blood loss anemia |
| `dane` | Deficiency anemia |
| `alcohol` | Alcohol abuse |
| `drug` | Drug abuse |
| `psycho` | Psychoses |
| `depre` | Depression |

## Usage

### Python API

```python
import polars as pl
from comorbidipy import comorbidity, ScoreType, WeightingVariant

df = pl.DataFrame({
    "patient_id": ["P001", "P001", "P002", "P002"],
    "icd_code": ["I50", "E11", "F32", "J44"],
})

# Basic Elixhauser calculation
result = comorbidity(
    df,
    id="patient_id",
    code="icd_code",
    score=ScoreType.ELIXHAUSER,
    age=None,
)

# With van Walraven weights
result = comorbidity(
    df,
    id="patient_id",
    code="icd_code",
    score=ScoreType.ELIXHAUSER,
    weighting=WeightingVariant.VAN_WALRAVEN,
    age=None,
)

# With Swiss weights
result = comorbidity(
    df,
    id="patient_id",
    code="icd_code",
    score=ScoreType.ELIXHAUSER,
    weighting=WeightingVariant.SWISS,
    age=None,
)
```

### CLI

```bash
# Basic Elixhauser calculation
comorbidipy elixhauser input.csv output.csv

# With van Walraven weights
comorbidipy elixhauser input.parquet output.parquet --weights vanwalraven

# With Swiss weights
comorbidipy elixhauser input.csv output.csv --weights swiss
```

## Assign Zero Logic

By default (`assign0=True`), when a more severe or complicated form of a condition is present, the uncomplicated form is set to 0:

- `hypunc` (uncomplicated hypertension) → 0 if `hypc` (complicated) present
- `diabunc` (uncomplicated diabetes) → 0 if `diabc` (complicated) present
- `solidtum` (solid tumor) → 0 if `metacanc` (metastatic) present

To keep both forms:

```python
result = comorbidity(df, assign0=False, age=None)
```

## Output

The output DataFrame includes:
- Patient ID column
- Binary columns (0/1) for each of the 31 comorbidity categories
- `comorbidity_score`: Weighted sum of comorbidities

## van Walraven Weights

The van Walraven weighting scheme assigns the following weights to predict in-hospital mortality:

| Condition | Weight |
|-----------|--------|
| Congestive heart failure | 7 |
| Cardiac arrhythmias | 5 |
| Valvular disease | -1 |
| Pulmonary circulation disorders | 4 |
| Peripheral vascular disorders | 2 |
| Hypertension, uncomplicated | 0 |
| Hypertension, complicated | 0 |
| Paralysis | 7 |
| Other neurological disorders | 6 |
| Chronic pulmonary disease | 3 |
| Diabetes, uncomplicated | 0 |
| Diabetes, complicated | 0 |
| Hypothyroidism | 0 |
| Renal failure | 5 |
| Liver disease | 11 |
| Peptic ulcer disease | 0 |
| AIDS/HIV | 0 |
| Lymphoma | 9 |
| Metastatic cancer | 12 |
| Solid tumor | 4 |
| Rheumatoid arthritis | 0 |
| Coagulopathy | 3 |
| Obesity | -4 |
| Weight loss | 6 |
| Fluid and electrolyte disorders | 5 |
| Blood loss anemia | -2 |
| Deficiency anemia | -2 |
| Alcohol abuse | 0 |
| Drug abuse | -7 |
| Psychoses | 0 |
| Depression | -3 |

Note that some weights are negative, reflecting protective associations in the original study.

## References

1. Elixhauser A, et al. Comorbidity measures for use with administrative data. Med Care. 1998;36(1):8-27.
2. van Walraven C, et al. A modification of the Elixhauser comorbidity measures into a point system for hospital death using administrative data. Med Care. 2009;47(6):626-633.
