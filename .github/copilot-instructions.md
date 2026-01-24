# Copilot Instructions

## Tone and Style
- Keep answers concise, factual, and engineering-focused.
- Use a collaborative tone and surface logical next steps when appropriate.
- Prefer Markdown lists for clarity; avoid unnecessary prose.

## Project Overview
comorbidipy is a Python package for calculating comorbidity scores and clinical risk scores from ICD codes. It is a rewrite of the R library `comorbidity` with additional calculators.

### Supported Calculators
- **Charlson Comorbidity Score** – mappings: Quan, Swedish, Australian, SHMI; weights: Charlson, Quan, SHMI, SHMI Modified
- **Elixhauser Comorbidity Index** – mappings: Quan; weights: van Walraven, Swiss
- **Hospital Frailty Risk Score (HFRS)** – for patients ≥75 years
- **Disability and Sensory Impairments**

## Repository Structure
- Calculator implementations live in [src/comorbidipy/calculators/](src/comorbidipy/calculators/); each module handles a specific score type.
- ICD code mappings and weight definitions are in [src/comorbidipy/codemaps/](src/comorbidipy/codemaps/); extend these when adding new mapping variants.
- CLI entry point is defined in [src/comorbidipy/cli.py](src/comorbidipy/cli.py) and registered as `comorbidipy` and `cmpy` in [pyproject.toml](pyproject.toml#L27).
- Public API exports should be added to [src/comorbidipy/__init__.py](src/comorbidipy/__init__.py).

## Coding Guidelines
- Target **Python ≥3.13**; maintain type annotations throughout.
- Use **Polars** for all DataFrame operations; avoid pandas unless interfacing with external code.
- Use **StrEnum** for categorical parameters (see `ICDVersion`, `ScoreType`, `MappingVariant`, `WeightingVariant` in [comorbidity.py](src/comorbidipy/calculators/comorbidity.py)).
- Prefer `@lru_cache` for expensive mapping lookups (see [hfrs.py](src/comorbidipy/calculators/hfrs.py)).
- Respect the link format `[path/file.py](path/file.py#L42)` when referencing repository files.

## Tooling and Quality
- Use `typer` for CLI commands; follow existing command structure. Typer docs: https://typer.tiangolo.com/
- Use `uv` for dependency management; prefer `uv run` over direct `python` calls.
- Format with `ruff format` and lint with `ruff check`; line length is **88 characters**.
- Run `pytest` from the repository root to execute tests.
- Use `mypy` for type checking on heavily typed modules.
- Documentation is built with `mkdocs` and `mkdocs-material`.

## Adding New Calculators
1. Create a new module in [src/comorbidipy/calculators/](src/comorbidipy/calculators/).
2. Add any required ICD mappings to [src/comorbidipy/codemaps/mapping.py](src/comorbidipy/codemaps/mapping.py).
3. Add weight definitions to [src/comorbidipy/codemaps/weights.py](src/comorbidipy/codemaps/weights.py) if applicable.
4. Export the calculator function from the package `__init__.py`.
5. Add corresponding CLI command in [src/comorbidipy/cli.py](src/comorbidipy/cli.py).
6. Write tests covering edge cases (empty input, missing columns, duplicate IDs).

## Safety and Compliance
- Decline policy-violating requests with "Sorry, I can't assist with that."
- Do not introduce proprietary clinical data or copyrighted mappings not already present.

## Collaboration
- When requirements are unclear, ask for clarification instead of guessing.
- Highlight breaking changes to public API or CLI so users can update their workflows.

---
description: 'Python coding conventions and guidelines'
applyTo: '**/*.py'
---

# Python Coding Conventions

## Python Instructions

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Provide docstrings following PEP 257 conventions with Args/Returns sections.
- Use modern type annotations (e.g., `list[str]`, `dict[str, int]`) instead of `typing` module equivalents.
- Break down complex functions into smaller, more manageable functions.

## General Instructions

- Always prioritize readability and clarity.
- For algorithm-related code, include explanations of the approach used.
- Write code with good maintainability practices, including comments on why certain design decisions were made.
- Handle edge cases and write clear exception handling with informative error messages.
- Use consistent naming conventions and follow language-specific best practices.
- Write concise, efficient, and idiomatic code that is also easily understandable.

## Code Style and Formatting

- Follow the **PEP 8** style guide for Python.
- Maintain proper indentation (use 4 spaces for each level of indentation).
- Line length is **88 characters** (ruff/Black default).
- Place function and class docstrings immediately after the `def` or `class` keyword.
- Use blank lines to separate functions, classes, and code blocks where appropriate.

## Edge Cases and Testing

- Always include test cases for critical paths of the application.
- Account for common edge cases: empty DataFrames, missing columns, invalid ICD codes, duplicate IDs.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.

## Example of Proper Documentation

```python
def comorbidity(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    score: ScoreType = ScoreType.CHARLSON,
    icd_version: ICDVersion = ICDVersion.ICD10,
) -> pl.DataFrame:
    """
    Calculate comorbidity scores from ICD diagnosis codes.

    Args:
        df: DataFrame with patient IDs and ICD codes.
        id_col: Name of the column containing patient identifiers.
        code_col: Name of the column containing ICD codes.
        score: Type of comorbidity score to calculate.
        icd_version: Version of ICD codes (ICD9 or ICD10).

    Returns:
        DataFrame with patient IDs and calculated comorbidity scores.

    Raises:
        KeyError: If required columns are missing from the input DataFrame.
    """
    ...
```
