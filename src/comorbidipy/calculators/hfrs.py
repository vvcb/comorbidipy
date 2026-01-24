from functools import lru_cache

import polars as pl

from ..codemaps.mapping import hfrs_mapping


@lru_cache(maxsize=65536)
def _mapper(x: str):
    try:
        x = x.lstrip()[0:3].upper()
        return x if x in hfrs_mapping else None
    except Exception as e:
        print(f"Error in mapping: {e}")
        return None


def hfrs(df: pl.DataFrame, id: str = "id", code: str = "code"):
    """Calculate Hospital Frailty Risk Score

    This is only applicable to patients who are 75 years or older.

    https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(18)30668-8

    Args:
        df (pl.DataFrame): DataFrame with 2 columns named `id` and `code`
        id (str, optional): Name of column to use as `id`. Defaults to "id".
        code (str, optional): Name of column to use as `code`. Defaults to "code".

    Return:
        pl.DataFrame: DataFrame with `id` and `hfrs` values.
    """

    if id not in df.columns or code not in df.columns:
        raise KeyError(f"Missing column(s). Ensure column(s) {id}, {code} are present.")

    # Keep only id, code columns and drop missing and duplicates first
    df = df.select(id, code).drop_nulls().unique()

    dfid = df.select(id).unique()

    # Apply mapper function to code column
    df = df.with_columns(
        pl.col(code).map_elements(_mapper, return_dtype=pl.Utf8).alias("mapped_code"),
    )

    # Drop nulls and duplicates
    df = df.filter(pl.col("mapped_code").is_not_null()).unique()

    # Replace with HFRS mappings and sum by ID
    df = df.with_columns(
        pl.col("mapped_code")
        .replace_strict(hfrs_mapping, default=0.0, return_dtype=pl.Float64)
        .alias("hfrs"),
    )

    df = df.group_by(id).agg(
        pl.sum("hfrs"),
    )

    # Merge back into original list of ids. Fill missing values with 0.
    df = dfid.join(df, on=id, how="left").fill_null(0)

    return df
