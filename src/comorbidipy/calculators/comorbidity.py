"""Charlson and Elixhauser comorbidity score calculators."""

import logging
from enum import StrEnum
from typing import Annotated

import polars as pl

from comorbidipy.codemaps.mapping import mapping

from ..codemaps.weights import weights

logger = logging.getLogger(__name__)


class ICDVersion(StrEnum):
    """ICD version enum."""

    ICD9 = "icd9"
    ICD10 = "icd10"


class ScoreType(StrEnum):
    """Score type enum."""

    CHARLSON = "charlson"
    ELIXHAUSER = "elixhauser"


class MappingVariant(StrEnum):
    """Mapping variant enum."""

    QUAN = "quan"
    SWEDISH = "swedish"
    AUSTRALIAN = "australian"
    SHMI = "shmi"


class WeightingVariant(StrEnum):
    """Weighting variant enum."""

    QUAN = "quan"
    CHARLSON = "charlson"
    SHMI = "shmi"
    SHMI_MODIFIED = "shmi_modified"
    VAN_WALRAVEN = "van_walraven"
    SWISS = "swiss"


T_assign_zero = Annotated[
    bool,
    "Should the less severe form of a comorbidity be set to 0 if the more severe form is present.",  # noqa: E501
    "Default: True",
]


colnames = {
    "charlson": {
        "aids": "AIDS or HIV",
        "ami": "acute myocardial infarction",
        "canc": "cancer any malignancy",
        "cevd": "cerebrovascular disease",
        "chf": "congestive heart failure",
        "copd": "chronic obstructive pulmonary disease",
        "dementia": "dementia",
        "diab": "diabetes without complications",
        "diabwc": "diabetes with complications",
        "hp": "hemiplegia or paraplegia",
        "metacanc": "metastatic solid tumour",
        "mld": "mild liver disease",
        "msld": "moderate or severe liver disease",
        "pud": "peptic ulcer disease",
        "pvd": "peripheral vascular disease",
        "rend": "renal disease",
        "rheumd": "rheumatoid disease",
    },
    "elixhauser": {
        "aids": " AIDS/HIV",
        "alcohol": " alcohol abuse",
        "blane": " blood loss anaemia",
        "carit": " cardiac arrhythmias",
        "chf": " congestive heart failure",
        "coag": " coagulopathy",
        "cpd": " chronic pulmonary disease",
        "dane": " deficiency anaemia",
        "depre": " depression",
        "diabc": " diabetes complicated",
        "diabunc": " diabetes uncomplicated",
        "drug": " drug abuse",
        "fed": " fluid and electrolyte disorders",
        "hypc": " hypertension complicated",
        "hypothy": " hypothyroidism",
        "hypunc": " hypertension uncomplicated",
        "ld": " liver disease",
        "lymph": " lymphoma",
        "metacanc": " metastatic cancer",
        "obes": " obesity",
        "ond": " other neurological disorders",
        "para": " paralysis",
        "pcd": " pulmonary circulation disorders",
        "psycho": " psychoses",
        "pud": " peptic ulcer disease excluding bleeding",
        "pvd": " peripheral vascular disorders",
        "rf": " renal failure",
        "rheumd": " rheumatoid arthritis/collaged vascular disease",
        "solidtum": " solid tumour without metastasis",
        "valv": " valvular disease",
        "wloss": " weight loss",
    },
}


def _assignzero(df: pl.DataFrame, score: str) -> pl.DataFrame:
    if "charlson" in score:
        # "Mild liver disease" (`mld`) and "Moderate/severe liver disease" (`msld`)
        df = df.with_columns(
            mld=pl.when(pl.col("msld") == 0).then(pl.col("mld")).otherwise(0),
        )

        # "Diabetes" (`diab`) and "Diabetes with complications" (`diabwc`)
        df = df.with_columns(
            diab=pl.when(pl.col("diabwc") == 0).then(pl.col("diab")).otherwise(0),
        )

        # "Cancer" (`canc`) and "Metastatic solid tumour" (`metacanc`)
        df = df.with_columns(
            canc=pl.when(pl.col("metacanc") == 0).then(pl.col("canc")).otherwise(0),
        )

    elif "elixhauser" in score:
        # "Hypertension, uncomplicated" (`hypunc`) and "Hypertension, complicated" (`hypc`)  # noqa: E501
        df = df.with_columns(
            hypunc=pl.when(pl.col("hypc") == 0).then(pl.col("hypunc")).otherwise(0),
        )

        # "Diabetes, uncomplicated" (`diabunc`) and "Diabetes, complicated" (`diabc`)
        df = df.with_columns(
            diabunc=pl.when(pl.col("diabc") == 0).then(pl.col("diabunc")).otherwise(0),
        )

        # "Solid tumour" (`solidtum`) and "Metastatic cancer" (`metacanc`)
        df = df.with_columns(
            solidtum=pl.when(pl.col("metacanc") == 0)
            .then(pl.col("solidtum"))
            .otherwise(0),
        )

    return df


def _calculate_weighted_score(
    dfp: pl.DataFrame,
    param_score: str,
    assign0: bool,
    weighting: str,
) -> pl.DataFrame:
    # if assign0 is True, set the less severe of the comorbidities to 0
    # if the more severe form is present
    if assign0:
        dfp = _assignzero(dfp, param_score)

    # Get the weights as a dictionary
    w = weights[param_score][weighting]

    # Calculate comorbidity score by multiplying each column with its weight and summing
    score = pl.lit(0.0)
    for col, weight in w.items():
        if col in dfp.columns:
            score = score + (dfp[col] * weight)

    # Add comorbidity score to the dataframe
    dfp = dfp.with_columns(comorbidity_score=score)

    # If sum of weights is less than zero, set it to zero (this only applies to UK SHMI)
    if weighting in [WeightingVariant.SHMI, WeightingVariant.SHMI_MODIFIED]:
        dfp = dfp.with_columns(
            comorbidity_score=pl.when(pl.col("comorbidity_score") >= 0)
            .then(pl.col("comorbidity_score"))
            .otherwise(0),
        )

    return dfp


def _add_age_weighting(dfp: pl.DataFrame, age: str) -> pl.DataFrame:
    # Calculate age score: (age - 40) / 10, clamped between 0 and 4
    age_score = ((pl.col(age) - 40) // 10).clip(0, 4)

    # Add age-adjusted score
    dfp = dfp.with_columns(
        age_adj_comorbidity_score=pl.col("comorbidity_score") + age_score,
    )

    return dfp


def comorbidity(  # noqa: PLR0913
    df: pl.DataFrame | pl.LazyFrame,
    id_col: str = "id",
    code_col: str = "code",
    age_col: str | None = None,
    score: ScoreType = ScoreType.CHARLSON,
    icd: ICDVersion = ICDVersion.ICD10,
    variant: MappingVariant = MappingVariant.QUAN,
    weighting: WeightingVariant = WeightingVariant.QUAN,
    assign0: T_assign_zero = True,
) -> pl.DataFrame:
    """Calculate Charlson and Elixhauser Comorbidity Scores from ICD codes.

    Args:
        df: Polars DataFrame with at least 2 columns for id and code.
        id_col: Name of column with unique identifier. This may be for a
            single patient or an episode. Defaults to "id".
        code_col: Name of column with ICD codes. Defaults to "code".
        age_col: Name of column with age. Defaults to None. If age is not
            provided, set this to None.
        score: One of "charlson", "elixhauser". Defaults to "charlson".
        icd: One of "icd9", "icd10" and describes the version used in
            the `code_col` column. Defaults to "icd10".
        variant: Mapping variant to use. Defaults to "quan".
        weighting: Weighting variant to use. Defaults to "quan".
        assign0: Should the less severe form of a comorbidity be set
            to 0 if the more severe form is present. Defaults to True.

    Raises:
        KeyError: Raised if `id_col` or `code_col` are not in `df.columns`.
        KeyError: If `age_col` is not None and `age_col` is not in `df.columns`.
        KeyError: Raised if combination of score, icd and variant not found in
            mappings. Call comorbidipy.get_mappings() to see permitted combinations.

    Returns:
        Polars DataFrame: Returns dataframe with one row per `id_col`. The dataframe
            will contain comorbidities in columns as well as a `comorbidity_score`
            column. If `score`=="charlson" and `age_col` is given,
            `age_adj_comorbidity_score` and `survival_10yr` are calculated as
            below.

        age_adj_comorbidity_score = comorbidity_score + 1 point for every decade
            over 40 upto a maximum of 4 points

        .. math::
            10yr survival = 0.983^(e^(0.9 * comorbidity_score))

    """
    # Handle LazyFrame input - collect to DataFrame with streaming for large data
    working_df: pl.DataFrame = (
        df.collect(engine="streaming") if isinstance(df, pl.LazyFrame) else df
    )

    # check the dataframe contains the required columns
    if id_col not in working_df.columns or code_col not in working_df.columns:
        raise KeyError(
            f"Missing column(s). Ensure column(s) {id_col}, {code_col} are present."
        )

    # Drop rows with NAs in required columns
    working_df = working_df.drop_nulls(subset=[id_col, code_col])

    # Prepare id dataframe
    if age_col:
        if age_col not in working_df.columns:
            raise KeyError(f"Column age was assigned {age_col} but not found")
        dfid = working_df.select(id_col, age_col).unique(subset=[id_col])
    else:
        dfid = working_df.select(id_col).unique()

    score_icd_variant = f"{score}_{icd}_{variant}"

    if score_icd_variant not in mapping.keys():
        raise KeyError(
            "Combination of score, icd and variant not found in mappings.\n"
            f"Allowed score_icd_variant combinations are {list(mapping)}",
        )

    # Create reverse mapping - each code can map to multiple comorbidities
    # Build a list of all (code, comorbidity) pairs
    codes = working_df.get_column(code_col).unique().to_list()
    code_to_comorbidities = []
    for icd_code in codes:
        for comorbidity_name, icd_patterns in mapping[score_icd_variant].items():
            if icd_code.startswith(tuple(icd_patterns)):
                code_to_comorbidities.append((icd_code, comorbidity_name))

    # Create a mapping dataframe
    if code_to_comorbidities:
        mapping_df = pl.DataFrame(
            code_to_comorbidities,
            schema=[code_col, "mapped_code"],
            orient="row",
        )
    else:
        # No codes matched - create empty mapping
        mapping_df = pl.DataFrame(schema={code_col: pl.Utf8, "mapped_code": pl.Utf8})

    # Join with mapping to get all code->comorbidity mappings
    # This will create multiple rows for codes that map to multiple comorbidities
    working_df = working_df.join(mapping_df, on=code_col, how="inner")

    # Remove duplicate (id, comorbidity) pairs - a patient should only get
    # credit once for each comorbidity even if they have multiple codes for it
    working_df = working_df.unique(subset=[id_col, "mapped_code"])

    # Create pivot table: one row per ID, one column per comorbidity
    # First, add a tmp column with value 1
    working_df = working_df.with_columns(tmp=pl.lit(1))

    # Group by id and pivot to get one column per comorbidity
    pivot_expr = []
    unique_codes = working_df.get_column("mapped_code").unique().to_list()

    for c in unique_codes:
        pivot_expr.append(
            pl.when(pl.col("mapped_code") == c)
            .then(pl.col("tmp"))
            .otherwise(0)
            .max()
            .alias(c),
        )

    dfp = working_df.group_by(id_col).agg(pivot_expr)

    # If a particular comorbidity does not occur at all in the dataset,
    # create a column and assign 0

    for c in colnames[score]:
        if c not in dfp.columns:
            dfp = dfp.with_columns(pl.lit(0).alias(c))

    # Calculate weighted score
    dfp = _calculate_weighted_score(dfp, score_icd_variant, assign0, weighting)

    # Merge back into dfid, adjusting for age and calculating survival if needed
    if score == "charlson" and weighting == "charlson" and age_col:
        dfp = dfid.join(dfp, on=id_col, how="left").fill_null(0)
        dfp = _add_age_weighting(dfp, age_col)
        # Calculate 10-year survival using native Polars expression
        # Formula: 0.983^(e^(0.9 * score))
        dfp = dfp.with_columns(
            survival_10yr=(0.983 ** (0.9 * pl.col("age_adj_comorbidity_score")).exp()),
        )
    else:
        dfp = dfid.join(dfp, on=id_col, how="left").fill_null(0)

    return dfp
