"""Command-line interface for comorbidipy."""

from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from comorbidipy.calculators.comorbidity import (
    ICDVersion,
    MappingVariant,
    ScoreType,
    WeightingVariant,
)
from comorbidipy.calculators.comorbidity import (
    comorbidity as calc_comorbidity,
)
from comorbidipy.calculators.hfrs import hfrs as calc_hfrs
from comorbidipy.calculators.learning_disability import disability as calc_disability

app = typer.Typer(
    help="Calculate comorbidity scores and clinical risk scores from ICD codes",
    no_args_is_help=True,
)


def _read_file(
    input_file: Path,
) -> pl.DataFrame:
    """Read input file based on extension."""
    if not input_file.exists():
        typer.echo(f"Error: File {input_file} does not exist", err=True)
        raise typer.Exit(code=1)

    suffix = input_file.suffix.lower()

    try:
        if suffix == ".csv":
            return pl.read_csv(input_file)
        elif suffix == ".parquet":
            return pl.read_parquet(input_file)
        else:
            typer.echo(
                f"Error: Unsupported file format '{suffix}'. "
                "Supported formats: .csv, .parquet",
                err=True,
            )
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error reading file: {e}", err=True)
        raise typer.Exit(code=1) from e


def _write_file(df: pl.DataFrame, output_file: Path) -> None:
    """Write output file based on extension."""
    suffix = output_file.suffix.lower()

    try:
        if suffix == ".csv":
            df.write_csv(output_file)
        elif suffix == ".parquet":
            df.write_parquet(output_file)
        else:
            typer.echo(
                f"Error: Unsupported output format '{suffix}'. "
                "Supported formats: .csv, .parquet",
                err=True,
            )
            raise typer.Exit(code=1)
        typer.echo(f"Output written to {output_file}")
    except Exception as e:
        typer.echo(f"Error writing file: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def comorbidity(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Input file path (CSV or Parquet)",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(
            help="Output file path (CSV or Parquet)",
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    id_col: Annotated[
        str,
        typer.Option(
            "--id",
            help="Name of column containing patient identifiers",
        ),
    ] = "id",
    code_col: Annotated[
        str,
        typer.Option(
            "--code",
            help="Name of column containing ICD codes",
        ),
    ] = "code",
    age_col: Annotated[
        str | None,
        typer.Option(
            "--age",
            help="Name of column containing age (optional for Charlson age adjustment)",
        ),
    ] = None,
    score: Annotated[
        ScoreType,
        typer.Option(
            "--score",
            help="Type of comorbidity score to calculate",
            case_sensitive=False,
        ),
    ] = ScoreType.CHARLSON,
    icd_version: Annotated[
        ICDVersion,
        typer.Option(
            "--icd",
            help="Version of ICD codes",
            case_sensitive=False,
        ),
    ] = ICDVersion.ICD10,
    variant: Annotated[
        MappingVariant,
        typer.Option(
            "--variant",
            help="Mapping variant to use",
            case_sensitive=False,
        ),
    ] = MappingVariant.QUAN,
    weighting: Annotated[
        WeightingVariant,
        typer.Option(
            "--weighting",
            help="Weighting variant to use",
            case_sensitive=False,
        ),
    ] = WeightingVariant.QUAN,
    assign_zero: Annotated[
        bool,
        typer.Option(
            "--assign-zero/--no-assign-zero",
            help="Set less severe comorbidity to 0 if more severe form is present",
        ),
    ] = True,
) -> None:
    """Calculate Charlson or Elixhauser comorbidity scores from ICD codes."""
    typer.echo(f"Reading input from {input_file}...")
    df = _read_file(input_file)

    typer.echo(
        f"Calculating {score.value} score using {icd_version.value} "
        f"codes with {variant.value} mapping and {weighting.value} weighting..."
    )

    try:
        result = calc_comorbidity(
            df=df,
            id=id_col,
            code=code_col,
            age=age_col,
            score=score,
            icd=icd_version,
            variant=variant,
            weighting=weighting,
            assign0=assign_zero,
        )

        _write_file(result, output_file)
        typer.echo(
            f"Successfully calculated scores for {len(result)} unique patients/episodes"
        )

    except KeyError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error calculating comorbidity: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def hfrs(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Input file path (CSV or Parquet)",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(
            help="Output file path (CSV or Parquet)",
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    id_col: Annotated[
        str,
        typer.Option(
            "--id",
            help="Name of column containing patient identifiers",
        ),
    ] = "id",
    code_col: Annotated[
        str,
        typer.Option(
            "--code",
            help="Name of column containing ICD codes",
        ),
    ] = "code",
) -> None:
    """Calculate Hospital Frailty Risk Score (HFRS) for patients ≥75 years."""
    typer.echo(f"Reading input from {input_file}...")
    df = _read_file(input_file)

    typer.echo("Calculating Hospital Frailty Risk Score...")

    try:
        result = calc_hfrs(df=df, id=id_col, code=code_col)

        _write_file(result, output_file)
        typer.echo(
            f"Successfully calculated HFRS for {len(result)} unique patients/episodes"
        )

    except KeyError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error calculating HFRS: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def disability(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Input file path (CSV or Parquet)",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(
            help="Output file path (CSV or Parquet)",
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    id_col: Annotated[
        str,
        typer.Option(
            "--id",
            help="Name of column containing patient identifiers",
        ),
    ] = "id",
    code_col: Annotated[
        str,
        typer.Option(
            "--code",
            help="Name of column containing ICD10 codes",
        ),
    ] = "code",
) -> None:
    """Identify disabilities and sensory impairments from ICD10 codes."""
    typer.echo(f"Reading input from {input_file}...")
    df = _read_file(input_file)

    typer.echo("Identifying disabilities and sensory impairments...")

    try:
        result = calc_disability(df=df, id=id_col, code=code_col)

        _write_file(result, output_file)
        typer.echo(f"Successfully processed {len(result)} unique patients/episodes")

    except KeyError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error identifying disabilities: {e}", err=True)
        raise typer.Exit(code=1) from e


def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
