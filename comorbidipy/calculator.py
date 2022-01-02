"""Main module."""
import warnings
from functools import lru_cache
import pandas as pd
from pandas.core.common import SettingWithCopyWarning

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

import math
from .mapping import mapping, hfrs_mapping
from .weights import weights
from .assignzero import assignzero
from .colnames import get_colnames


def _calculate_weights(
    dfp: pd.DataFrame, param_score: str, assign0: bool, weighting: str
):

    # Create a copy of the supplied dataframe first
    df = dfp.copy()

    # if assign0 is True, set the less severe of the comorbidities to 0
    if assign0:
        df = assignzero(df, param_score)

    # Get the weights into a dataframe
    w = weights[param_score][weighting]
    w = pd.Series(w)

    colname = f"{weighting}_wt_{param_score}"
    dfp[colname] = df.multiply(w).sum(axis=1)

    return dfp


def _age_adjust(dfp: pd.DataFrame, age: str, param_score: str):

    colnames = dfp.filter(regex=param_score).columns
    age_score = dfp[age].subtract(40).floordiv(10).apply(lambda x: min(max(0, x), 4))
    for c in colnames:
        dfp["age_adj_" + c] = dfp[c] + age_score

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
    if age:
        if age not in df.columns:
            raise KeyError(f"Column age was assigned {age} but not found")

    param_score = f"{score}_{icd}_{variant}"

    if param_score not in mapping.keys():
        raise KeyError("Combination of score, icd and variant not found in mappings.")

    df = df.dropna(subset=[id, code])

    dfid = df[[id, age]].drop_duplicates()

    icd = df[code].unique()

    reverse_mapping = {
        i: k
        for i in icd
        for k, v in mapping[param_score].items()
        if i.startswith(tuple(v))
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
    dfp = df.pivot(index=id, columns=code, values="tmp").fillna(0)

    # If a particular comorbidity does not occur at all in the dataset,
    # create a column with 0 values in it
    colnames = get_colnames(score)
    for c in colnames:
        if c not in dfp:
            dfp[c] = 0

    dfp = _calculate_weights(dfp, param_score, assign0, weighting)

    if age:
        dfp = dfid.merge(dfp, on=id, how="left").fillna(0)
        dfp = _age_adjust(dfp, age, param_score)

    if score == "charlson":
        dfp[f"survival_10yr"] = dfp[
            f"age_adj_{weighting}_wt_charlson_icd10_quan"
        ].apply(lambda x: 0.983 ** math.exp(0.9 * x))

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

    dfid = df[[id]].drop_duplicates()

    df = df[[id, code]].dropna().drop_duplicates()
    df[code] = df[code].apply(_mapper)

    # Drop missing and duplicates. This should leave only codes in hfrs_mapping
    df = df.dropna().drop_duplicates()

    df["hfrs"] = df.icd10.replace(hfrs_mapping)
    df = df.groupby(id)["hfrs"].sum().reset_index()

    # Merge back into original list of ids. Fill missing values with 0.
    df = dfid.merge(df, on=id, how="left").fillna(0)

    return df
