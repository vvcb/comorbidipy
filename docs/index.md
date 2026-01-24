# comorbidipy

[![PyPI](https://img.shields.io/pypi/v/comorbidipy)](https://pypi.python.org/pypi/comorbidipy)
[![Build](https://github.com/vvcb/comorbidipy/actions/workflows/publish-to-pypi.yaml/badge.svg)](https://pypi.org/project/comorbidipy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**comorbidipy** is a Python package for calculating comorbidity scores and clinical risk scores from ICD codes. It is a modernized rewrite of the excellent R library [comorbidity](https://github.com/ellessenne/comorbidity/) with additional calculators.

## Features

- 🏥 **Charlson Comorbidity Index** – Multiple mapping variants (Quan, Swedish, Australian, SHMI) and weighting schemes
- 📊 **Elixhauser Comorbidity Index** – van Walraven and Swiss weights
- 👴 **Hospital Frailty Risk Score (HFRS)** – For patients ≥75 years
- ♿ **Disability & Sensory Impairments** – Learning disabilities, visual/hearing impairments

## Performance

Built with [Polars](https://pola.rs/) for exceptional performance:

- ⚡ Process millions of rows efficiently
- 🧠 Memory-efficient operations with lazy evaluation
- 📁 Support for CSV, Parquet, JSON, and Avro formats

## Quick Start

### Installation

```bash
pip install comorbidipy
```

### Python API

```python
import polars as pl
from comorbidipy import comorbidity, hfrs, disability

# Sample data
df = pl.DataFrame({
    "id": ["P001", "P001", "P002", "P002"],
    "code": ["I21", "E112", "I50", "J44"],
    "age": [65, 65, 72, 72],
})

# Calculate Charlson Comorbidity Index
result = comorbidity(df, id="id", code="code", age="age")
print(result)
```

### Command Line

```bash
# Calculate Charlson score
comorbidipy charlson input.csv output.parquet --mapping quan --weights charlson

# Calculate Elixhauser score
comorbidipy elixhauser input.csv output.csv --weights van_walraven

# Calculate HFRS
comorbidipy hfrs-cmd patients.parquet results.parquet

# Show available options
comorbidipy info
```

## Why comorbidipy?

| Feature | comorbidipy | Other packages |
|---------|-------------|----------------|
| DataFrame library | Polars (fast) | pandas (slower) |
| Large datasets | ✅ Streaming support | ❌ Memory-bound |
| CLI | ✅ Full-featured | ❌ Limited/None |
| Multiple formats | CSV, Parquet, JSON, Avro | CSV only |
| Type hints | ✅ Complete | Partial |

## License

MIT License - see [LICENSE](https://github.com/vvcb/comorbidipy/blob/main/LICENSE) for details.

## Credits

- [R comorbidity package](https://github.com/ellessenne/comorbidity/) by Alessandro Gasparini
- [Polars](https://pola.rs/) for high-performance DataFrames
