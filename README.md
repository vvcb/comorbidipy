comorbidiPy
===========

[![PyPi](https://img.shields.io/pypi/v/comorbidipy)](https://pypi.python.org/pypi/comorbidipy)
[![Build](https://github.com/vvcb/comorbidipy/actions/workflows/publish-to-pypi.yaml/badge.svg)](https://pypi.org/project/comorbidipy/)
[![Build](https://github.com/vvcb/comorbidipy/actions/workflows/publish-to-test-pypi.yaml/badge.svg)](https://test.pypi.org/project/comorbidipy)
[![Docs](https://readthedocs.org/projects/comorbidipy/badge/?version=latest)](https://comorbidipy.readthedocs.io/en/latest/?version=latest)

Python package to calculate comorbidity scores and other clinical risk scores.

The `comorbidity` function of this library is effectively a rewrite of the excellent R library `comorbidity` (<https://github.com/ellessenne/comorbidity/>) by Alessandro Gasparini (<https://www.ellessenne.xyz/>).

Comorbidipy also includes additional clinical risk calculators listed below.

Installation
------------

```bash
pip install comorbidipy
```

Quick Start
-----------

### Command Line Interface

Comorbidipy provides a CLI for processing files in CSV or Parquet format.

#### Calculate Charlson Comorbidity Score

```bash
# Using ICD-10 codes with default settings (Quan mapping and weighting)
comorbidipy comorbidity input.csv output.csv

# Specify ICD version, mapping, and weighting variants
comorbidipy comorbidity input.csv output.csv --icd icd9 --variant swedish --weighting charlson

# Calculate Elixhauser score with age adjustment
comorbidipy comorbidity input.csv output.csv --score elixhauser --age age_column
```

#### Calculate Hospital Frailty Risk Score

```bash
# For patients ≥75 years old
comorbidipy hfrs input.csv output.csv
```

#### Identify Disabilities and Sensory Impairments

```bash
comorbidipy disability input.csv output.csv
```

### Python API

```python
import polars as pl
from comorbidipy import comorbidity, hfrs, disability
from comorbidipy import ICDVersion, ScoreType, MappingVariant, WeightingVariant

# Load your data
df = pl.read_csv("patient_data.csv")

# Calculate Charlson score
result = comorbidity(
    df,
    id="patient_id",
    code="icd_code",
    age="age",
    score=ScoreType.CHARLSON,
    icd=ICDVersion.ICD10,
    variant=MappingVariant.QUAN,
    weighting=WeightingVariant.QUAN
)

# Calculate HFRS
hfrs_result = hfrs(df, id="patient_id", code="icd_code")

# Identify disabilities
disability_result = disability(df, id="patient_id", code="icd_code")
```

Input Data Format
-----------------

Your input data should have at least two columns:
- An ID column (default: "id") - patient or episode identifier
- A code column (default: "code") - ICD-9 or ICD-10 diagnosis codes

Example:
```
id,code
1,I50.9
1,I21.9
2,E11.9
```

Feature List
------------

- Charlson Comorbidity Score
- Elixhauser Comorbidity Index
- Hospital Frailty Risk Score
- Disability and Sensory Impairments

Variants of Charlson and Elixhauser Scores
------------------------------------------

The `comorbidity` function allows calculation of Charlson and Elixhauser score using ICD9 or ICD10 codes and the following variations.

Variations of Charlson Comorbidity Score
----------------------------------------

- Mapping:
  - Quan version
  - Swedish version
  - Australian version
  - UK version (from Summary Hospital-Level Mortality Indicator - SHMI)

- Weights:
  - Charlson
  - Quan
  - SHMI
  - Modified SHMI

Elixhauser Comorbidity Index
----------------------------

- Mapping:
  - Quan

- Weights:
  - van Walraven
  - Swiss

License and Documentation
-------------------------

- Free software: MIT license
- Documentation: <https://comorbidipy.readthedocs.io>. (TODO)

Credits
-------

- __Cookiecutter__ <https://github.com/audreyr/cookiecutter>
- __R library `comorbidity`__ <https://github.com/ellessenne/comorbidity/>
