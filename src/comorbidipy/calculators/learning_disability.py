import polars as pl

from ..mapping import impairments


def disability(df: pl.DataFrame, id: str = "id", code: str = "code") -> pl.DataFrame:
    """Identify disabilities and sensory impairments from ICD10 codes

    Args:
        df (pl.DataFrame): Polars dataframe containing at least id and code columns
        id (str, optional): Name of column containing patient identifier. Defaults to
            "id".
        code (str, optional): Name of column containing ICD10 codes. Defaults to
            "code".

    Raises:
        KeyError: Error is raised if id or code columns are not present in dataframe.

    Returns:
        Polars DataFrame: Polars DataFrame with id and various
            disabilities/impairments columns coded as 0 or 1.
    """

    if id not in df.columns or code not in df.columns:
        raise KeyError(f"Missing column(s). Ensure column(s) {id}, {code} are present.")

    df = df.drop_nulls(subset=[id, code])

    dfid = df.select(id).unique()

    icd = df.get_column(code).unique().to_list()

    reverse_mapping = {
        i: k for i in icd for k, v in impairments.items() if i.startswith(tuple(v))
    }

    # Keep only codes that are in mapping
    df = df.with_columns(
        pl.col(code).map_dict(reverse_mapping, default=None).alias("mapped_code"),
    )

    df = df.filter(pl.col("mapped_code").is_not_null()).unique(
        subset=[id, "mapped_code"],
    )

    # Create pivot table: one row per ID, one column per impairment
    df = df.with_columns(tmp=pl.lit(1))

    # Group by id and pivot to get one column per impairment
    pivot_expr = []
    unique_impairments = df.get_column("mapped_code").unique().to_list()

    for c in unique_impairments:
        pivot_expr.append(
            pl.max(
                pl.when(pl.col("mapped_code") == c).then(pl.col("tmp")).otherwise(0),
            ).alias(c),
        )

    df = df.group_by(id).agg(pivot_expr)

    # Merge back into original list of ids. Fill missing values with 0.
    df = dfid.join(df, on=id, how="left").fill_null(0)

    return df
