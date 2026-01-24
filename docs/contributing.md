# Contributing

Thank you for your interest in contributing to comorbidipy!

## Development Setup

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/comorbidipy.git
cd comorbidipy
```

2. Create a virtual environment and install dependencies:

```bash
uv sync
```

3. Verify the installation:

```bash
uv run pytest
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=comorbidipy

# Run specific test file
uv run pytest tests/test_comorbidity.py

# Run tests matching a pattern
uv run pytest -k "charlson"
```

### Code Formatting

We use `ruff` for formatting and linting:

```bash
# Format code
uv run ruff format

# Check for linting issues
uv run ruff check

# Fix auto-fixable issues
uv run ruff check --fix
```

### Type Checking

```bash
uv run mypy src/comorbidipy
```

### Building Documentation

```bash
# Serve documentation locally
uv run mkdocs serve

# Build documentation
uv run mkdocs build
```

## Code Style

### Python Guidelines

- Follow PEP 8 with 88-character line length
- Use type annotations for all function signatures
- Write docstrings following PEP 257 with Args/Returns sections
- Use modern type hints (`list[str]` not `List[str]`)

### Example Function

```python
def calculate_score(
    df: pl.DataFrame,
    id_col: str = "id",
    value_col: str = "value",
) -> pl.DataFrame:
    """
    Calculate a score from input data.

    Args:
        df: Input DataFrame with patient data.
        id_col: Name of the column containing patient identifiers.
        value_col: Name of the column containing values.

    Returns:
        DataFrame with patient IDs and calculated scores.

    Raises:
        KeyError: If required columns are missing.
    """
    if id_col not in df.columns:
        raise KeyError(f"Column '{id_col}' not found in DataFrame")

    return df.group_by(id_col).agg(
        pl.col(value_col).sum().alias("score")
    )
```

### Polars Guidelines

- Use native Polars expressions instead of `map_elements`
- Prefer `LazyFrame` operations where possible
- Use `replace_strict` for dictionary mappings with `default=None`

## Adding a New Calculator

1. **Create the module** in `src/comorbidipy/calculators/`:

```python
# src/comorbidipy/calculators/new_calculator.py
import polars as pl
import logging

logger = logging.getLogger(__name__)

def new_calculator(
    df: pl.DataFrame | pl.LazyFrame,
    id: str = "id",
    code: str = "code",
) -> pl.DataFrame:
    """Calculate new score."""
    logger.info("Calculating new score")
    # Implementation here
    return result
```

2. **Add ICD mappings** (if needed) to `src/comorbidipy/codemaps/mapping.py`

3. **Add weights** (if needed) to `src/comorbidipy/codemaps/weights.py`

4. **Export from package** in `src/comorbidipy/__init__.py`:

```python
from comorbidipy.calculators.new_calculator import new_calculator

__all__ = [
    # ... existing exports
    "new_calculator",
]
```

5. **Add CLI command** in `src/comorbidipy/cli.py`:

```python
@app.command()
def new_cmd(
    input_file: Path,
    output_file: Path,
    id: str = "id",
    code: str = "code",
    verbose: bool = False,
) -> None:
    """Calculate new score."""
    # Implementation
```

6. **Write tests** in `tests/test_new_calculator.py`:

```python
import pytest
import polars as pl
from comorbidipy import new_calculator

def test_new_calculator_basic():
    df = pl.DataFrame({
        "id": ["P001", "P002"],
        "code": ["A00", "B00"],
    })
    result = new_calculator(df)
    assert "score" in result.columns
```

7. **Add documentation** in `docs/calculators/new_calculator.md`

## Testing Guidelines

### Test Structure

- One test file per module: `test_<module>.py`
- Use descriptive test names: `test_charlson_with_age_adjustment`
- Test edge cases: empty input, missing columns, duplicate IDs

### Synthetic Data

Use the fixtures in `tests/conftest.py`:

```python
def test_with_synthetic_data(generate_charlson_data):
    df = generate_charlson_data(n_patients=100, codes_per_patient=5)
    result = comorbidity(df, age=None)
    assert len(result) == 100
```

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/new-calculator`
3. **Make your changes** with tests and documentation
4. **Run checks**:
   ```bash
   uv run ruff format
   uv run ruff check
   uv run pytest
   ```
5. **Commit** with clear messages
6. **Push** and create a pull request

## Reporting Issues

When reporting bugs, please include:

- Python version
- comorbidipy version
- Minimal reproducible example
- Full error traceback

## Questions?

Open an issue for:

- Feature requests
- Documentation improvements
- General questions

Thank you for contributing! 🎉
