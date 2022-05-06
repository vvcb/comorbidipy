"""Main module."""
import warnings
from functools import lru_cache
import pandas as pd
from pandas.core.common import SettingWithCopyWarning

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

import math
from .mapping import mapping, hfrs_mapping, impairments
from .weights import weights
from .assignzero import assignzero
from .colnames import get_colnames


def _calculate_weighted_score(
    dfp: pd.DataFrame, param_score: str, assign0: bool, weighting: str
):

    # Create a copy of the supplied dataframe first
    df = dfp.copy()

    # if assign0 is True, set the less severe of the comorbidities to 0
    # this does not change the values in the actual columns but only affects the weighting
    # e.g the final dataset will still have true for both diabetes and diabetes with complications
    # but only diabetes with complications will be used for calculating the final score.
    if assign0:
        df = assignzero(df, param_score)

    # Get the weights into a pandas series
    w = weights[param_score][weighting]
    w = pd.Series(w)

    dfp["comorbidity_score"] = df.multiply(w).sum(axis=1)
    # if sum of weights is less than zero, set it zero (this only applies to UK SHMI)
    dfp["comorbidity_score"] = dfp["comorbidity_score"].where(
        dfp["comorbidity_score"] >= 0, 0
    )
    return dfp


def _age_adjust(dfp: pd.DataFrame, age: str):

    age_score = dfp[age].subtract(40).floordiv(10).apply(lambda x: min(max(0, x), 4))
    dfp["age_adj_comorbidity_score"] = dfp["comorbidity_score"] + age_score

    return dfp


def comorbidity(
    df: pd.DataFrame,
    id: str = "id",
    code: str = "code",
    age: str = "age",
    score: str = "charlson",
    icd: str = "icd10",
    variant: str = "quan",
    weighting: str = "quan",
    assign0: bool = True,
):

    # check the dataframe contains the required columns

    if id not in df.columns or code not in df.columns:
        raise KeyError(f"Missing column(s). Ensure column(s) {id}, {code} are present.")

    df = df.dropna(subset=[id, code])

    if age:
        if age not in df.columns:
            raise KeyError(f"Column age was assigned {age} but not found")
        dfid = df[[id, age]].drop_duplicates(subset=['id'])
    else:
        dfid = df[[id]].drop_duplicates()

    score_icd_variant = f"{score}_{icd}_{variant}"

    if score_icd_variant not in mapping.keys():
        raise KeyError(
            "Combination of score, icd and variant not found in mappings.\n"
            f"Allowed score_icd_variant combinations are {list(mapping)}"
        )

    reverse_mapping = {
        i: k
        for i in df[code].unique()
        for k, v in mapping[score_icd_variant].items()
        if i.startswith(tuple(v))
    }

    # Keep only codes that are in mapping
    df[code] = df[code].where(df[code].isin(reverse_mapping), other=None)

    df = df.dropna(subset=[code]).drop_duplicates(subset=[id, code])

    # Replace codes with mapping
    df[code] = df[code].replace(reverse_mapping)
    # The following is needed as multiple codes may map to same comorbidity
    # If there are duplicates, pivot will fail
    df = df.drop_duplicates(subset=[id, code])

    # Pivot
    df["tmp"] = 1
    dfp = df.pivot(index=id, columns=code, values="tmp").fillna(0)

    # If a particular comorbidity does not occur at all in the dataset,
    # create a column and assign 0
    colnames = get_colnames(score)
    for c in colnames:
        if c not in dfp.columns:
            dfp[c] = 0

    # Calculate weighted score
    dfp = _calculate_weighted_score(dfp, score_icd_variant, assign0, weighting)

    # Merge back into dfid, adjusting for age and calculating survival if needed
    if age:
        dfp = dfid.merge(dfp, on=id, how="left").fillna(0)
        dfp = _age_adjust(dfp, age)

        if score == "charlson" and weighting == "charlson":
            dfp[f"survival_10yr"] = dfp[f"age_adj_comorbidity_score"].apply(
                lambda x: 0.983 ** math.exp(0.9 * x)
            )
    else:
        dfp = dfid.merge(dfp, on=id, how="left").fillna(0)

    # Add metadata to dataframe before returning.
    # Helps when calling this function with different parameters and
    # outputs are all called 'comorbidity_score'!
    dfp.attrs = {
        "score": score,
        "icd": icd,
        "variant": variant,
        "weighting": weighting,
        "assign0": assign0,
    }

    return dfp


def hfrs(df: pd.DataFrame, id: str = "id", code: str = "code"):
    """Calculate Hospital Frailty Risk Score

    This is only applicable to patients who are 75 years or older.

    https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(18)30668-8

    Args:
        df (pd.DataFrame): Dataframe with 2 columns named `id` and `code`
        id (str, optional): Name of column to use as `id`. Defaults to "id".
        code (str, optional): Name of column to use as `code`. Defaults to "code".

    Return:
        pd.DataFrame: Dataframe with `id` and `hfrs` values.
    """

    @lru_cache(maxsize=65536)
    def _mapper(x: str):
        try:
            x = x.lstrip()[0:3].upper()
            return x if x in hfrs_mapping else None
        except:
            return None

    if id not in df.columns or code not in df.columns:
        raise KeyError(f"Missing column(s). Ensure column(s) {id}, {code} are present.")

    # Keep only id, code columns and drop missing and duplicates first
    df = df[[id, code]].dropna().drop_duplicates()

    dfid = df[[id]].drop_duplicates()

    df[code] = df[code].apply(_mapper)

    # Drop missing and duplicates. This should leave only codes in hfrs_mapping
    df = df.dropna().drop_duplicates()

    df["hfrs"] = df[code].replace(hfrs_mapping)
    df = df.groupby(id)["hfrs"].sum().reset_index()

    # Merge back into original list of ids. Fill missing values with 0.
    df = dfid.merge(df, on=id, how="left").fillna(0)

    return df


def disability(df: pd.DataFrame, id: str = "id", code: str = "code") -> pd.DataFrame:
    """Identify disabilities and sensory impairments from ICD10 codes

    Args:
        df (pd.DataFrame): Pandas dataframe containing at least id and code columns
        id (str, optional): Name of column containing patient identifier. Defaults to "id".
        code (str, optional): Name of column containing ICD10 codes. Defaults to "code".

    Raises:
        KeyError: Error is raised if id or code columns are not present in dataframe.

    Returns:
        Pandas DataFrame: Pandas DataFrame with id and various disabilities/impairments columns coded as 0 or 1.
    """

    if id not in df.columns or code not in df.columns:
        raise KeyError(f"Missing column(s). Ensure column(s) {id}, {code} are present.")

    df = df.dropna(subset=[id, code])

    dfid = df[[id]].drop_duplicates()

    icd = df[code].unique()

    reverse_mapping = {
        i: k for i in icd for k, v in impairments.items() if i.startswith(tuple(v))
    }

    # Keep only codes that are in mapping
    df[code] = df[code].where(df[code].isin(reverse_mapping.keys()), other=None)

    df = df.dropna(subset=[code]).drop_duplicates(subset=[id, code])

    # Replace codes with mapping
    df[code] = df[code].replace(reverse_mapping)
    # not sure if this is needed but if there are duplicates,  pivot will fail
    df = df.drop_duplicates(subset=[id, code])
    df["tmp"] = 1

    # Pivot
    df = df.pivot(index=id, columns=code, values="tmp")

    # Merge back into original list of ids. Fill missing values with 0.
    df = dfid.merge(df, on=id, how="left").fillna(0)

    return df
