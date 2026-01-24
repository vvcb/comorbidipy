"""Disability and sensory impairments identifier from ICD codes."""

import logging

import polars as pl

from ..codemaps.mapping import impairments

logger = logging.getLogger(__name__)

# Pre-compute reverse mapping at module load for performance
_IMPAIRMENT_PREFIXES: dict[str, tuple[str, ...]] = {
    k: tuple(v) for k, v in impairments.items()
}


def disability(
    df: pl.DataFrame | pl.LazyFrame,
    id_col: str = "id",
    code_col: str = "code",
) -> pl.DataFrame:
    """Identify disabilities and sensory impairments from ICD-10 codes.

    Args:
        df: DataFrame with patient IDs and ICD-10 codes.
        id_col: Name of column containing patient identifiers.
        code_col: Name of column containing ICD-10 codes.

    Returns:
        DataFrame with patient IDs and binary columns for each impairment type.

    Raises:
        KeyError: If required columns are missing from the input DataFrame.

    Example:
        >>> import polars as pl
        >>> from comorbidipy import disability
        >>> df = pl.DataFrame({
        ...     "id": [1, 1, 2],
        ...     "code": ["F70", "H54", "F71"]
        ... })
        >>> disability(df)
    """
    # Handle LazyFrame input - collect to DataFrame with streaming for large data
    working_df: pl.DataFrame = (
        df.collect(engine="streaming") if isinstance(df, pl.LazyFrame) else df
    )

    if id_col not in working_df.columns or code_col not in working_df.columns:
        raise KeyError(f"Columns '{id_col}' and '{code_col}' must be present.")

    logger.debug(f"Processing {working_df.height} rows for disability identification")

    working_df = working_df.drop_nulls(subset=[id_col, code_col])
    dfid = working_df.select(id_col).unique()

    # Get unique codes and build reverse mapping
    icd_codes = working_df.get_column(code_col).unique().to_list()

    reverse_mapping = {
        code: impairment
        for code in icd_codes
        for impairment, prefixes in _IMPAIRMENT_PREFIXES.items()
        if code.startswith(prefixes)
    }

    # Keep only codes that are in mapping
    working_df = working_df.with_columns(
        pl.col(code_col)
        .replace_strict(reverse_mapping, default=None)
        .alias("mapped_code")
    )

    working_df = working_df.filter(pl.col("mapped_code").is_not_null()).unique(
        subset=[id_col, "mapped_code"]
    )

    # Create pivot table using native Polars pivot
    if working_df.height == 0:
        # No matches found - return dfid with all impairment columns as 0
        result = dfid.clone()
        for imp in impairments:
            result = result.with_columns(pl.lit(0).alias(imp))
        return result

    working_df = working_df.with_columns(tmp=pl.lit(1))

    # Group by id and pivot to get one column per impairment
    pivot_expr = []
    unique_impairments = working_df.get_column("mapped_code").unique().to_list()

    for c in unique_impairments:
        pivot_expr.append(
            pl.when(pl.col("mapped_code") == c)
            .then(pl.col("tmp"))
            .otherwise(0)
            .max()
            .alias(c)
        )

    working_df = working_df.group_by(id_col).agg(pivot_expr)

    # Merge back into original list of IDs, fill missing with 0
    result = dfid.join(working_df, on=id_col, how="left").fill_null(0)

    # Add missing impairment columns (if any impairment type not present in data)
    for imp in impairments:
        if imp not in result.columns:
            result = result.with_columns(pl.lit(0).alias(imp))

    logger.debug(
        f"Disability identification complete. Output: {result.height} patients"
    )

    return result
