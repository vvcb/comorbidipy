"""Hospital Frailty Risk Score (HFRS) calculator."""

import logging

import polars as pl

from ..codemaps.mapping import hfrs_mapping

logger = logging.getLogger(__name__)

# Pre-compute set of valid HFRS codes for fast lookup
_HFRS_CODES = frozenset(hfrs_mapping.keys())


def hfrs(
    df: pl.DataFrame | pl.LazyFrame,
    id_col: str = "id",
    code_col: str = "code",
) -> pl.DataFrame:
    """Calculate Hospital Frailty Risk Score.

    This is only applicable to patients who are 75 years or older.
    Reference: https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(18)30668-8

    Args:
        df: DataFrame with patient IDs and ICD-10 codes.
        id_col: Name of column containing patient identifiers.
        code_col: Name of column containing ICD-10 codes.

    Returns:
        DataFrame with patient IDs and HFRS scores.

    Raises:
        KeyError: If required columns are missing from the input DataFrame.

    Example:
        >>> import polars as pl
        >>> from comorbidipy import hfrs
        >>> df = pl.DataFrame({
        ...     "id": [1, 1, 2],
        ...     "code": ["F00", "G81", "F00"]
        ... })
        >>> hfrs(df)
    """
    # Handle LazyFrame input - collect to DataFrame with streaming for large data
    working_df: pl.DataFrame = (
        df.collect(engine="streaming") if isinstance(df, pl.LazyFrame) else df
    )

    if id_col not in working_df.columns or code_col not in working_df.columns:
        raise KeyError(f"Columns '{id_col}' and '{code_col}' must be present.")

    logger.debug(f"Processing {working_df.height} rows for HFRS calculation")

    # Keep only required columns and drop missing/duplicates
    working_df = working_df.select(id_col, code_col).drop_nulls().unique()

    # Store unique IDs for later join
    dfid = working_df.select(id_col).unique()

    # Extract first 3 characters, strip whitespace, and uppercase using native Polars
    # This replaces the slow map_elements call
    working_df = working_df.with_columns(
        pl.col(code_col)
        .str.strip_chars()
        .str.slice(0, 3)
        .str.to_uppercase()
        .alias("mapped_code")
    )

    # Filter to only codes that exist in HFRS mapping
    working_df = working_df.filter(pl.col("mapped_code").is_in(_HFRS_CODES)).unique()

    # Replace with HFRS weights and sum by ID
    working_df = working_df.with_columns(
        pl.col("mapped_code").replace_strict(hfrs_mapping).alias("hfrs")
    )

    working_df = working_df.group_by(id_col).agg(pl.sum("hfrs"))

    # Merge back into original list of IDs, fill missing with 0
    result = dfid.join(working_df, on=id_col, how="left").fill_null(0)

    logger.debug(f"HFRS calculation complete. Output: {result.height} patients")

    return result
