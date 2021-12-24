import pandas as pd


def assignzero(df: pd.DataFrame, score: str):
    if "charlson" in score:
        # "Mild liver disease" (`mld`) and "Moderate/severe liver disease" (`msld`)
        # x[msld == 1, mld := 0]
        df.mld = df.mld.where(df.msld == 0, 0)

        # "Diabetes" (`diab`) and "Diabetes with complications" (`diabwc`)
        # x[diabwc == 1, diab := 0]
        df.diab = df.diab.where(df.diabwc == 0, 0)

        # "Cancer" (`canc`) and "Metastatic solid tumour" (`metacanc`)
        # x[metacanc == 1, canc := 0]
        df.canc = df.canc.where(df.metacanc == 0, 0)

    elif "elixhauser" in score:
        # "Hypertension, uncomplicated" (`hypunc`) and "Hypertension, complicated" (`hypc`)
        # x[hypc == 1, hypunc := 0]
        df.hypunc = df.hypunc.where(df.hypc == 0, 0)

        # "Diabetes, uncomplicated" (`diabunc`) and "Diabetes, complicated" (`diabc`)
        # x[diabc == 1, diabunc := 0]
        df.diabunc = df.diabunc.where(df.diabc == 0, 0)

        # "Solid tumour" (`solidtum`) and "Metastatic cancer" (`metacanc`)
        # x[metacanc == 1, solidtum := 0]
        df.solidtum = df.solidtum.where(df.metacanc == 0, 0)

    return df
