import polars as pl


def assignzero(df: pl.DataFrame, score: str) -> pl.DataFrame:
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
