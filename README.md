# comorbidiPy

<p align="center">

<a href="https://pypi.python.org/pypi/comorbidipy" target="_blank">
    <img src="https://img.shields.io/pypi/v/comorbidipy.svg" alt="PyPi Version">
</a>
<a href="https://pypi.python.org/pypi/comorbidipy" target="_blank">
    <img src="https://github.com/vvcb/comorbidipy/actions/workflows/publish-to-pypi.yaml/badge.svg" alt="Build Status">
</a>
<a href="https://comorbidipy.readthedocs.io/en/latest/?version=latest" target="_blank">
    <img src="https://readthedocs.org/projects/comorbidipy/badge/?version=latest" alt="Documentation Status">
</a>
</p>

Python package to calculate comorbidity scores and other clinical risk scores.

The `comorbidity` function of this library is effectively a rewrite of the excellent R library `comorbidity` (<https://github.com/ellessenne/comorbidity/>) by Alessandro Gasparini (<https://www.ellessenne.xyz/>).

Comorbidipy also includes additional clinical risk calculators listed below.

## Feature List

- Charlson Comorbidity Score
- Elixhauser Comorbidity Index
- Hospital Frailty Risk Score
- Disability and Sensory Impairments

## Variants of Charlson and Elixhauser Scores

The `comorbidity` function allows calculation of Charlson and Elixhauser score using ICD9 or ICD10 codes and the following variations.

### Charlson Comorbidity Score

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

### Elixhauser Comorbidity Index

- Mapping:
  - Quan

- Weights:
  - van Walraven
  - Swiss

## License and Documentation

- Free software: MIT license
- Documentation: <https://comorbidipy.readthedocs.io>. (TODO)

## Credits

- __Cookiecutter__ <https://github.com/audreyr/cookiecutter>
- __R library `comorbidity`__ <https://github.com/ellessenne/comorbidity/>
