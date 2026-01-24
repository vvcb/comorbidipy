# Changelog

## 0.7.0 (2026-01-24)

### Breaking Changes

- **Python 3.13+ required** - Dropped support for older Python versions
- **Polars replaces pandas** - All DataFrame operations now use Polars for improved performance
- **API changes** - Function signatures updated (e.g., `id_col` → `id`, `code_col` → `code`)

### New Features

- **Full CLI with Typer** - New command-line interface with commands: `charlson`, `elixhauser`, `hfrs`, `disability`, `info`
- **Multiple file format support** - CLI supports CSV, Parquet, JSON, NDJSON, and Avro formats
- **LazyFrame support** - All calculators accept both `pl.DataFrame` and `pl.LazyFrame` for memory-efficient processing
- **Logging** - Added structured logging throughout the library
- **Type hints** - Full type annotations with `py.typed` marker for IDE support

### Performance Improvements

- **Native Polars expressions** - Replaced slow `map_elements` calls with native string operations
- **Optimized code matching** - HFRS uses pre-computed frozenset for O(1) lookups
- **Large dataset support** - Tested with 100,000+ patient datasets

### Code Quality

- **64 comprehensive tests** - Full test coverage with synthetic data generators
- **Ruff formatting and linting** - Consistent code style
- **MyPy type checking** - Static type verification

### Documentation

- **MkDocs documentation** - Complete documentation with Material theme
- **Calculator guides** - Detailed pages for Charlson, Elixhauser, HFRS, and Disability calculators
- **API reference** - Full Python API documentation
- **CLI reference** - Command-line usage examples

### CI/CD

- **GitHub Actions for tests** - Automated testing on PRs and pushes to main
- **GitHub Actions for docs** - Automatic documentation deployment to GitHub Pages

### Bug Fixes

- Fixed broken imports in calculator modules
- Fixed `assign_zero` logic not applying correctly
- Replaced deprecated `map_dict` with `replace_strict`
- Fixed Polars expression syntax (`pl.max()` → `.max()`)

## 0.4.4 (2022-06-11)

- Additional function to identify disabilities
- Rewritten comorbidity function
- Additional modified weights for SHMI variant of Charlson Score
- CI/CD pipeline to publish to PyPi

## 0.3.0 (2022-02-11)

- Add SHMI variant of Charlson Comorbidity Score. Based on SHMI Specification Version 1.35 2020-09-24 (<https://files.digital.nhs.uk/B8/F8D021/SHMI%20specification%20v1.35.pdf>)

## 0.2.1 (2021-01-02)

- Rewritten HFRS calculator that is 5x faster than previous version.

## 0.2.0 (2021-12-31)

- Add function for calculating Hospital Frailty Risk Score (<https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(18)30668-8/>)

## 0.1.0 (2021-12-20)

- First release.
