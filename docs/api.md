# API Reference

This page documents the public Python API for comorbidipy.

## Main Functions

### comorbidity

Calculate Charlson or Elixhauser comorbidity scores.

```python
def comorbidity(
    df: pl.DataFrame | pl.LazyFrame,
    id: str = "id",
    code: str = "code",
    score: ScoreType = ScoreType.CHARLSON,
    icd: ICDVersion = ICDVersion.ICD10,
    variant: MappingVariant = MappingVariant.QUAN,
    weighting: WeightingVariant = WeightingVariant.CHARLSON,
    assign0: bool = True,
    age: str | None = None,
) -> pl.DataFrame:
    """
    Calculate comorbidity scores from ICD diagnosis codes.

    Args:
        df: DataFrame with patient IDs and ICD codes.
        id: Name of the column containing patient identifiers.
        code: Name of the column containing ICD codes.
        score: Type of comorbidity score (CHARLSON or ELIXHAUSER).
        icd: Version of ICD codes (ICD9 or ICD10).
        variant: Mapping variant for ICD code classification.
        weighting: Weighting scheme for calculating the score.
        assign0: Whether to zero out less severe conditions when
            more severe forms are present.
        age: Name of the column containing patient age (optional).
            When provided with Charlson score and Charlson weights,
            enables age adjustment and survival calculation.

    Returns:
        DataFrame with patient IDs, binary comorbidity flags,
        and calculated scores.

    Raises:
        KeyError: If required columns are missing from the input DataFrame.
        ValueError: If invalid combination of score/mapping/weighting is used.
    """
```

**Example:**

```python
import polars as pl
from comorbidipy import comorbidity, ScoreType, MappingVariant

df = pl.DataFrame({
    "patient_id": ["P001", "P001", "P002"],
    "diagnosis": ["I21", "E112", "I50"],
    "patient_age": [65, 65, 72],
})

result = comorbidity(
    df,
    id="patient_id",
    code="diagnosis",
    score=ScoreType.CHARLSON,
    age="patient_age",
)
```

---

### hfrs

Calculate Hospital Frailty Risk Score.

```python
def hfrs(
    df: pl.DataFrame | pl.LazyFrame,
    id: str = "id",
    code: str = "code",
) -> pl.DataFrame:
    """
    Calculate Hospital Frailty Risk Score from ICD-10 codes.

    The HFRS identifies frailty in hospital patients using 109
    ICD-10 codes associated with frailty conditions.

    Args:
        df: DataFrame with patient IDs and ICD-10 codes.
        id: Name of the column containing patient identifiers.
        code: Name of the column containing ICD codes.

    Returns:
        DataFrame with columns:
        - Patient ID (original column name)
        - hfrs_score: Continuous frailty score
        - hfrs_category: "Low" (<5), "Intermediate" (5-15), or "High" (>15)

    Raises:
        KeyError: If required columns are missing from the input DataFrame.

    Note:
        The HFRS is validated for patients aged 75 years and older.
    """
```

**Example:**

```python
import polars as pl
from comorbidipy import hfrs

df = pl.DataFrame({
    "id": ["P001", "P001", "P002"],
    "code": ["F00", "R26", "J18"],
})

result = hfrs(df, id="id", code="code")
```

---

### disability

Identify learning disabilities and sensory impairments.

```python
def disability(
    df: pl.DataFrame | pl.LazyFrame,
    id: str = "id",
    code: str = "code",
) -> pl.DataFrame:
    """
    Identify learning disabilities and sensory impairments from ICD-10 codes.

    Detects:
    - Learning disability / Autism Spectrum Disorder (F70-F79, F84)
    - Visual impairment (H54)
    - Hearing impairment (H90-H91)

    Args:
        df: DataFrame with patient IDs and ICD-10 codes.
        id: Name of the column containing patient identifiers.
        code: Name of the column containing ICD codes.

    Returns:
        DataFrame with columns:
        - Patient ID (original column name)
        - ld_asd: 1 if learning disability/ASD present, 0 otherwise
        - impaired_vision: 1 if visual impairment present, 0 otherwise
        - impaired_hearing: 1 if hearing impairment present, 0 otherwise

    Raises:
        KeyError: If required columns are missing from the input DataFrame.
    """
```

**Example:**

```python
import polars as pl
from comorbidipy import disability

df = pl.DataFrame({
    "id": ["P001", "P002"],
    "code": ["F70", "H90"],
})

result = disability(df, id="id", code="code")
```

---

## Enumerations

### ScoreType

Type of comorbidity score to calculate.

```python
class ScoreType(StrEnum):
    CHARLSON = "charlson"
    ELIXHAUSER = "elixhauser"
```

### ICDVersion

Version of ICD codes.

```python
class ICDVersion(StrEnum):
    ICD9 = "icd9"
    ICD10 = "icd10"
```

### MappingVariant

Mapping variant for ICD code classification.

```python
class MappingVariant(StrEnum):
    QUAN = "quan"
    SWEDISH = "swedish"
    AUSTRALIAN = "australian"
    SHMI = "shmi"
```

**Compatibility:**

| Mapping | Charlson ICD-9 | Charlson ICD-10 | Elixhauser |
|---------|----------------|-----------------|------------|
| QUAN | ✅ | ✅ | ✅ |
| SWEDISH | ❌ | ✅ | ❌ |
| AUSTRALIAN | ❌ | ✅ | ❌ |
| SHMI | ❌ | ✅ | ❌ |

### WeightingVariant

Weighting scheme for score calculation.

```python
class WeightingVariant(StrEnum):
    CHARLSON = "charlson"
    QUAN = "quan"
    SHMI = "shmi"
    SHMI_MODIFIED = "shmi_modified"
    VAN_WALRAVEN = "vanwalraven"
    SWISS = "swiss"
```

**Compatibility:**

| Weighting | Charlson | Elixhauser |
|-----------|----------|------------|
| CHARLSON | ✅ | ❌ |
| QUAN | ✅ | ❌ |
| SHMI | ✅ | ❌ |
| SHMI_MODIFIED | ✅ | ❌ |
| VAN_WALRAVEN | ❌ | ✅ |
| SWISS | ❌ | ✅ |

---

## Type Hints

comorbidipy is fully typed. Import types for IDE support:

```python
from comorbidipy import (
    comorbidity,
    hfrs,
    disability,
    ScoreType,
    ICDVersion,
    MappingVariant,
    WeightingVariant,
)
```

---

## LazyFrame Support

All functions accept both `pl.DataFrame` and `pl.LazyFrame`:

```python
import polars as pl
from comorbidipy import comorbidity

# LazyFrame for memory-efficient processing
lf = pl.scan_parquet("large_file.parquet")
result = comorbidity(lf, id="id", code="code", age=None)
```

When a `LazyFrame` is passed, the function will:
1. Collect necessary data lazily
2. Return an eager `DataFrame` with results

---

## Error Handling

All functions raise clear exceptions:

```python
from comorbidipy import comorbidity
import polars as pl

df = pl.DataFrame({"wrong_col": ["P001"], "also_wrong": ["I21"]})

try:
    result = comorbidity(df, id="patient_id", code="code", age=None)
except KeyError as e:
    print(f"Missing column: {e}")
```
