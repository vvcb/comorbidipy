"""Command-line interface for comorbidipy."""

from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from .calculators.comorbidity import (
    ICDVersion,
    MappingVariant,
    ScoreType,
    WeightingVariant,
    comorbidity,
)
from .calculators.hfrs import hfrs
from .calculators.learning_disability import disability

app = typer.Typer(
    help="Calculate comorbidity scores and clinical risk scores from ICD codes.",
    no_args_is_help=True,
)


def _read_file(input_path: Path, format: str | None = None) -> pl.DataFrame:
    """Read input file, auto-detecting format if not specified."""
    if format is None:
        # Auto-detect from extension
        ext = input_path.suffix.lower()
        if ext == ".csv":
            return pl.read_csv(input_path)
        elif ext == ".parquet":
            return pl.read_parquet(input_path)
        else:
            raise ValueError(
                f"Cannot auto-detect format for {input_path}. "
                "Please specify --format explicitly."
            )
    elif format.lower() == "csv":
        return pl.read_csv(input_path)
    elif format.lower() == "parquet":
        return pl.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported input format: {format}")


def _write_file(
    df: pl.DataFrame, output_path: Path, format: str | None = None
) -> None:
    """Write output file, auto-detecting format if not specified."""
    if format is None:
        # Auto-detect from extension
        ext = output_path.suffix.lower()
        if ext == ".csv":
            df.write_csv(output_path)
        elif ext == ".parquet":
            df.write_parquet(output_path)
        else:
            raise ValueError(
                f"Cannot auto-detect format for {output_path}. "
                "Please specify --output-format explicitly."
            )
    elif format.lower() == "csv":
        df.write_csv(output_path)
    elif format.lower() == "parquet":
        df.write_parquet(output_path)
    else:
        raise ValueError(f"Unsupported output format: {format}")


@app.command()
def charlson(
    input_file: Annotated[
        Path, typer.Argument(help="Input file (CSV or Parquet)", exists=True)
    ],
    output_file: Annotated[Path, typer.Argument(help="Output file path")],
    id_col: Annotated[str, typer.Option(help="Column name for patient ID")] = "id",
    code_col: Annotated[str, typer.Option(help="Column name for ICD codes")] = "code",
    age_col: Annotated[
        str | None, typer.Option(help="Column name for age (optional)")
    ] = "age",
    icd_version: Annotated[
        ICDVersion, typer.Option(help="ICD version")
    ] = ICDVersion.ICD10,
    mapping_variant: Annotated[
        MappingVariant, typer.Option(help="Mapping variant")
    ] = MappingVariant.QUAN,
    weighting: Annotated[
        WeightingVariant, typer.Option(help="Weighting scheme")
    ] = WeightingVariant.QUAN,
    assign_zero: Annotated[
        bool,
        typer.Option(
            help="Set less severe comorbidity to 0 if more severe form is present"
        ),
    ] = True,
    input_format: Annotated[
        str | None, typer.Option(help="Input format (csv/parquet)")
    ] = None,
    output_format: Annotated[
        str | None, typer.Option(help="Output format (csv/parquet)")
    ] = None,
) -> None:
    """Calculate Charlson Comorbidity Score from ICD codes."""
    df = _read_file(input_file, input_format)

    result = comorbidity(
        df=df,
        id=id_col,
        code=code_col,
        age=age_col if age_col else None,
        score=ScoreType.CHARLSON,
        icd=icd_version,
        variant=mapping_variant,
        weighting=weighting,
        assign0=assign_zero,
    )

    _write_file(result, output_file, output_format)
    typer.echo(f"Charlson scores calculated and saved to {output_file}")


@app.command()
def elixhauser(
    input_file: Annotated[
        Path, typer.Argument(help="Input file (CSV or Parquet)", exists=True)
    ],
    output_file: Annotated[Path, typer.Argument(help="Output file path")],
    id_col: Annotated[str, typer.Option(help="Column name for patient ID")] = "id",
    code_col: Annotated[str, typer.Option(help="Column name for ICD codes")] = "code",
    icd_version: Annotated[
        ICDVersion, typer.Option(help="ICD version")
    ] = ICDVersion.ICD10,
    mapping_variant: Annotated[
        MappingVariant, typer.Option(help="Mapping variant")
    ] = MappingVariant.QUAN,
    weighting: Annotated[
        WeightingVariant, typer.Option(help="Weighting scheme")
    ] = WeightingVariant.VAN_WALRAVEN,
    assign_zero: Annotated[
        bool,
        typer.Option(
            help="Set less severe comorbidity to 0 if more severe form is present"
        ),
    ] = True,
    input_format: Annotated[
        str | None, typer.Option(help="Input format (csv/parquet)")
    ] = None,
    output_format: Annotated[
        str | None, typer.Option(help="Output format (csv/parquet)")
    ] = None,
) -> None:
    """Calculate Elixhauser Comorbidity Index from ICD codes."""
    df = _read_file(input_file, input_format)

    result = comorbidity(
        df=df,
        id=id_col,
        code=code_col,
        age=None,
        score=ScoreType.ELIXHAUSER,
        icd=icd_version,
        variant=mapping_variant,
        weighting=weighting,
        assign0=assign_zero,
    )

    _write_file(result, output_file, output_format)
    typer.echo(f"Elixhauser scores calculated and saved to {output_file}")


@app.command()
def hfrs_cmd(
    input_file: Annotated[
        Path, typer.Argument(help="Input file (CSV or Parquet)", exists=True)
    ],
    output_file: Annotated[Path, typer.Argument(help="Output file path")],
    id_col: Annotated[str, typer.Option(help="Column name for patient ID")] = "id",
    code_col: Annotated[str, typer.Option(help="Column name for ICD codes")] = "code",
    input_format: Annotated[
        str | None, typer.Option(help="Input format (csv/parquet)")
    ] = None,
    output_format: Annotated[
        str | None, typer.Option(help="Output format (csv/parquet)")
    ] = None,
) -> None:
    """Calculate Hospital Frailty Risk Score (for patients ≥75 years)."""
    df = _read_file(input_file, input_format)

    result = hfrs(df=df, id=id_col, code=code_col)

    _write_file(result, output_file, output_format)
    typer.echo(f"HFRS scores calculated and saved to {output_file}")


@app.command()
def disability_cmd(
    input_file: Annotated[
        Path, typer.Argument(help="Input file (CSV or Parquet)", exists=True)
    ],
    output_file: Annotated[Path, typer.Argument(help="Output file path")],
    id_col: Annotated[str, typer.Option(help="Column name for patient ID")] = "id",
    code_col: Annotated[str, typer.Option(help="Column name for ICD codes")] = "code",
    input_format: Annotated[
        str | None, typer.Option(help="Input format (csv/parquet)")
    ] = None,
    output_format: Annotated[
        str | None, typer.Option(help="Output format (csv/parquet)")
    ] = None,
) -> None:
    """Identify disabilities and sensory impairments from ICD-10 codes."""
    df = _read_file(input_file, input_format)

    result = disability(df=df, id=id_col, code=code_col)

    _write_file(result, output_file, output_format)
    typer.echo(f"Disability indicators calculated and saved to {output_file}")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
