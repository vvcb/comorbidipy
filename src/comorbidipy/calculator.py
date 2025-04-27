"""Main module."""

import math
from functools import lru_cache

import polars as pl

from .assignzero import assignzero
from .colnames import get_colnames
from .mapping import hfrs_mapping, impairments, mapping
from .weights import weights


def _calculate_weighted_score(
    dfp: pl.DataFrame,
    param_score: str,
    assign0: bool,
    weighting: str,
) -> pl.DataFrame:
    # Create a copy of the supplied dataframe first
    df = dfp.clone()

    # if assign0 is True, set the less severe of the comorbidities to 0
    # if the more severe form is present
    if assign0:
        df = assignzero(df, param_score)

    # Get the weights as a dictionary
    w = weights[param_score][weighting]

    # Calculate comorbidity score by multiplying each column with its weight and summing
    score = pl.lit(0.0)
    for col, weight in w.items():
        if col in df.columns:
            score = score + (df[col] * weight)

    # Add comorbidity score to the original dataframe
    dfp = dfp.with_columns(comorbidity_score=score)

    # If sum of weights is less than zero, set it to zero (this only applies to UK SHMI)
    dfp = dfp.with_columns(
        comorbidity_score=pl.when(pl.col("comorbidity_score") >= 0)
        .then(pl.col("comorbidity_score"))
        .otherwise(0),
    )

    return dfp


def _age_adjust(dfp: pl.DataFrame, age: str) -> pl.DataFrame:
    # Calculate age score: (age - 40) / 10, clamped between 0 and 4
    age_score = ((pl.col(age) - 40) // 10).clip(0, 4)

    # Add age-adjusted score
    dfp = dfp.with_columns(
        age_adj_comorbidity_score=pl.col("comorbidity_score") + age_score,
    )

    return dfp


def comorbidity(  # noqa: PLR0913
    df: pl.DataFrame,
    id: str = "id",
    code: str = "code",
    age: str = "age",
    score: str = "charlson",
    icd: str = "icd10",
    variant: str = "quan",
    weighting: str = "quan",
    assign0: bool = True,
) -> pl.DataFrame:
    """Calculate Charlson and Elixhauser Comorbidity Scores from ICD codes

    Args:
        df (pl.DataFrame): Polars DataFrame with at least 2 columns for id and code
        id (str, optional): Name of column with unique identifier. This may be for a
            single patient or an episode. Defaults to "id".
        code (str, optional): Name of column with ICD codes. Defaults to "code".
        age (str, optional): Name of column with age. Defaults to "age". If age is not
            provided, set this to None.
        score (str, optional): One of "charlson", "elixhauser". Defaults to "charlson".
        icd (str, optional): One of "icd9", "icd10" and descibes the version used in
            the `code` column. Defaults to "icd10".
        variant (str, optional): Mapping variant to use. Defaults to "quan".
        weighting (str, optional): Weighting variant to use. Defaults to "quan".
        assign0 (bool, optional): Should the less severe form of a comorbidity be set
            to 0 if the more severe form is present. Defaults to True.

    Raises:
        KeyError: Raised if `id` or `code` are not in `df.columns`.
        KeyError: If `age` is not None and `age` is not in `df.columns`.
        KeyError: Raised if combination of score, icd and variant not found in
            mappings. Call comorbidipy.get_mappings() to see permitted combinations.

    Returns:
        Polars DataFrame: Returns dataframe with one row per `id`. The dataframe will
            contain comorbidities in columns as well as a `comorbidity_score` column.
            If `score`=="charlson" and `age` is given, `age_adjusted_comorbidity_score`
            and `survival_10yr` are calculated as below.

        age_adjusted_comorbidity_score = comorbidity_score + 1 point for every decade
            over 40 upto a maximum of 4 points

        .. math::
            10yr survival = 0.983^(e^(0.9 * comorbidity_score))

    """
    # check the dataframe contains the required columns
    if id not in df.columns or code not in df.columns:
        raise KeyError(f"Missing column(s). Ensure column(s) {id}, {code} are present.")

    # Drop rows with NAs in required columns
    df = df.drop_nulls(subset=[id, code])

    # Prepare id dataframe
    if age:
        if age not in df.columns:
            raise KeyError(f"Column age was assigned {age} but not found")
        dfid = df.select(id, age).unique(subset=[id])
    else:
        dfid = df.select(id).unique()

    score_icd_variant = f"{score}_{icd}_{variant}"

    if score_icd_variant not in mapping.keys():
        raise KeyError(
            "Combination of score, icd and variant not found in mappings.\n"
            f"Allowed score_icd_variant combinations are {list(mapping)}",
        )

    # Create reverse mapping dictionary
    codes = df.get_column(code).unique().to_list()
    reverse_mapping = {
        i: k
        for i in codes
        for k, v in mapping[score_icd_variant].items()
        if i.startswith(tuple(v))
    }

    # Keep only codes that are in mapping
    df = df.with_columns(
        pl.col(code).map_dict(reverse_mapping, default=None).alias("mapped_code"),
    )

    df = df.filter(pl.col("mapped_code").is_not_null())
    df = df.unique(subset=[id, "mapped_code"])

    # Create pivot table: one row per ID, one column per comorbidity
    # First, add a tmp column with value 1
    df = df.with_columns(tmp=pl.lit(1))

    # Group by id and pivot to get one column per comorbidity
    pivot_expr = []
    unique_codes = df.get_column("mapped_code").unique().to_list()

    for c in unique_codes:
        pivot_expr.append(
            pl.max(
                pl.when(pl.col("mapped_code") == c).then(pl.col("tmp")).otherwise(0),
            ).alias(c),
        )

    dfp = df.group_by(id).agg(pivot_expr)

    # If a particular comorbidity does not occur at all in the dataset,
    # create a column and assign 0
    colnames = get_colnames(score)
    for c in colnames:
        if c not in dfp.columns:
            dfp = dfp.with_columns(pl.lit(0).alias(c))

    # Calculate weighted score
    dfp = _calculate_weighted_score(dfp, score_icd_variant, assign0, weighting)

    # Merge back into dfid, adjusting for age and calculating survival if needed
    if age:
        dfp = dfid.join(dfp, on=id, how="left").fill_null(0)
        dfp = _age_adjust(dfp, age)

        if score == "charlson" and weighting == "charlson":
            dfp = dfp.with_columns(
                survival_10yr=pl.col("age_adj_comorbidity_score").map_elements(
                    lambda x: 0.983 ** math.exp(0.9 * x),
                ),
            )
    else:
        dfp = dfid.join(dfp, on=id, how="left").fill_null(0)

    # Add metadata to dataframe
    # Note: Polars doesn't have attrs like pandas.
    # So we'll have to return the metadata separately.
    # metadata = {
    #     "score": score,
    #     "icd": icd,
    #     "variant": variant,
    #     "weighting": weighting,
    #     "assign0": assign0,
    # }

    # Return the dataframe
    return dfp


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

    @lru_cache(maxsize=65536)
    def _mapper(x: str):
        try:
            x = x.lstrip()[0:3].upper()
            return x if x in hfrs_mapping else None
        except Exception as e:
            print(f"Error in mapping: {e}")
            return None

    if id not in df.columns or code not in df.columns:
        raise KeyError(f"Missing column(s). Ensure column(s) {id}, {code} are present.")

    # Keep only id, code columns and drop missing and duplicates first
    df = df.select(id, code).drop_nulls().unique()

    dfid = df.select(id).unique()

    # Apply mapper function to code column
    df = df.with_columns(
        pl.col(code).map_elements(_mapper).alias("mapped_code"),
    )

    # Drop nulls and duplicates
    df = df.filter(pl.col("mapped_code").is_not_null()).unique()

    # Replace with HFRS mappings and sum by ID
    df = df.with_columns(
        pl.col("mapped_code").map_dict(hfrs_mapping).alias("hfrs"),
    )

    df = df.group_by(id).agg(
        pl.sum("hfrs"),
    )

    # Merge back into original list of ids. Fill missing values with 0.
    df = dfid.join(df, on=id, how="left").fill_null(0)

    return df


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
