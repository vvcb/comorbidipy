# comorbidipy

[![PyPI](https://img.shields.io/pypi/v/comorbidipy)](https://pypi.python.org/pypi/comorbidipy)
[![Tests](https://github.com/vvcb/comorbidipy/actions/workflows/tests.yml/badge.svg)](https://github.com/vvcb/comorbidipy/actions/workflows/tests.yml)
[![Docs](https://github.com/vvcb/comorbidipy/actions/workflows/docs.yml/badge.svg)](https://vvcb.github.io/comorbidipy)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A high-performance Python package for calculating comorbidity scores and clinical risk scores from ICD codes.

Built with [Polars](https://pola.rs/) for blazing-fast processing of large datasets.

## Features

- **Charlson Comorbidity Index** – Multiple mapping variants (Quan, Swedish, Australian, SHMI) and weighting schemes
- **Elixhauser Comorbidity Index** – Quan mapping with van Walraven or Swiss weights
- **Hospital Frailty Risk Score (HFRS)** – For patients ≥75 years
- **Disability & Sensory Impairments** – Learning disabilities, visual and hearing impairments

## Installation

```bash
pip install comorbidipy
```

Requires Python 3.13+.

## Quick Start

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

# Calculate Hospital Frailty Risk Score
frailty = hfrs(df, id="id", code="code")

# Identify disabilities
disabilities = disability(df, id="id", code="code")
```

### Command Line Interface

```bash
# Charlson score
comorbidipy charlson input.csv output.csv --age-col age

# Elixhauser score
comorbidipy elixhauser input.parquet output.parquet --weights vanwalraven

# Hospital Frailty Risk Score
comorbidipy hfrs input.csv output.csv

# Disability identification
comorbidipy disability input.csv output.csv

# Show available options
comorbidipy info
```

Supported file formats: CSV, Parquet, JSON, NDJSON, Avro.

## Charlson Variants

| Mapping | ICD-9 | ICD-10 | Description |
|---------|-------|--------|-------------|
| `quan` | ✅ | ✅ | Quan et al. (2005) |
| `swedish` | ❌ | ✅ | Swedish National Patient Register |
| `australian` | ❌ | ✅ | Australian IHW adaptation |
| `shmi` | ❌ | ✅ | UK SHMI specification |

| Weighting | Description |
|-----------|-------------|
| `charlson` | Original 1987 weights |
| `quan` | Quan et al. updated weights |
| `shmi` | UK SHMI weights |
| `shmi_modified` | Modified SHMI weights |

## Documentation

Full documentation: [https://vvcb.github.io/comorbidipy](https://vvcb.github.io/comorbidipy)

## License

MIT License – see [LICENSE](LICENSE) for details.

## Credits

- Inspired by the R library [`comorbidity`](https://github.com/ellessenne/comorbidity/) by Alessandro Gasparini
- Built with [Polars](https://pola.rs/) and [Typer](https://typer.tiangolo.com/)
