# Getting Started

This guide will help you get started with comorbidipy for calculating clinical comorbidity scores from ICD codes.

## Installation

### From PyPI

```bash
pip install comorbidipy
```

### From source

```bash
git clone https://github.com/vvcb/comorbidipy.git
cd comorbidipy
pip install -e .
```

## Basic Usage

### Preparing Your Data

comorbidipy expects a DataFrame with at least two columns:

- **id**: Patient or episode identifier
- **code**: ICD-9 or ICD-10 diagnosis codes

```python
import polars as pl

# Example data format
df = pl.DataFrame({
    "id": ["P001", "P001", "P001", "P002", "P002"],
    "code": ["I21", "E112", "I50", "J44", "K703"],
    "age": [65, 65, 65, 72, 72],  # Optional for age-adjusted scores
})
```

### Calculating Charlson Comorbidity Index

```python
from comorbidipy import comorbidity, ScoreType, MappingVariant, WeightingVariant

result = comorbidity(
    df,
    id="id",
    code="code",
    age="age",  # Optional - enables age-adjusted score
    score=ScoreType.CHARLSON,
    variant=MappingVariant.QUAN,
    weighting=WeightingVariant.CHARLSON,
)

print(result)
```

### Calculating Elixhauser Comorbidity Index

```python
result = comorbidity(
    df,
    id="id",
    code="code",
    score=ScoreType.ELIXHAUSER,
    weighting=WeightingVariant.VAN_WALRAVEN,
    age=None,  # Elixhauser doesn't use age adjustment
)
```

### Calculating Hospital Frailty Risk Score

```python
from comorbidipy import hfrs

# HFRS only requires id and code
result = hfrs(df, id_col="id", code_col="code")
```

### Identifying Disabilities

```python
from comorbidipy import disability

result = disability(df, id_col="id", code_col="code")
```

## Command Line Interface

comorbidipy provides a full-featured CLI for processing files directly:

```bash
# View help
comorbidipy --help

# Calculate Charlson score
comorbidipy charlson input.csv output.parquet

# With options
comorbidipy charlson input.csv output.csv \
    --id-col patient_id \
    --code-col diagnosis_code \
    --age-col patient_age \
    --mapping quan \
    --weights charlson

# Calculate HFRS
comorbidipy hfrs-cmd input.parquet output.parquet

# Show available options
comorbidipy info
```

## Supported File Formats

| Format | Read | Write | Streaming |
|--------|------|-------|-----------|
| CSV | ✅ | ✅ | ✅ |
| Parquet | ✅ | ✅ | ✅ |
| JSON | ✅ | ✅ | ❌ |
| NDJSON | ✅ | ✅ | ✅ |
| Avro | ✅ | ✅ | ❌ |

## Performance Tips

### Processing Large Files

For files that don't fit in memory, use streaming mode:

```bash
comorbidipy charlson large_input.parquet output.parquet --streaming
```

### Use Parquet Format

Parquet files are significantly faster to read/write than CSV:

```python
# Read Parquet
df = pl.read_parquet("data.parquet")

# Or use CLI
comorbidipy charlson input.parquet output.parquet
```

### LazyFrame for Deferred Computation

```python
# Use LazyFrame for memory efficiency
lazy_df = pl.scan_parquet("large_file.parquet")
result = comorbidity(lazy_df, id="id", code="code", age=None)
```

## Next Steps

- [Charlson Comorbidity Index](calculators/charlson.md) - Detailed documentation
- [CLI Reference](cli.md) - Full command-line options
- [API Reference](api.md) - Python API documentation
