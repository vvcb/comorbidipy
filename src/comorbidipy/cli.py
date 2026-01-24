"""Comorbidipy CLI - Calculate clinical comorbidity scores from ICD codes."""

import logging
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from comorbidipy import __version__
from comorbidipy.calculators.comorbidity import (
    ICDVersion,
    MappingVariant,
    ScoreType,
    WeightingVariant,
    comorbidity,
)
from comorbidipy.calculators.hfrs import hfrs
from comorbidipy.calculators.learning_disability import disability

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("comorbidipy")


class OutputFormat(StrEnum):
    """Supported output file formats."""

    CSV = "csv"
    PARQUET = "parquet"
    JSON = "json"


def _detect_format(path: Path) -> str:
    """Detect file format from extension."""
    suffix = path.suffix.lower()
    format_map = {
        ".csv": "csv",
        ".parquet": "parquet",
        ".pq": "parquet",
        ".json": "json",
        ".ndjson": "ndjson",
        ".avro": "avro",
    }
    return format_map.get(suffix, "csv")


def _read_file(
    path: Path,
    format: str | None = None,
    streaming: bool = False,
) -> pl.DataFrame | pl.LazyFrame:
    """Read input file in various formats.

    Args:
        path: Path to input file.
        format: File format. Auto-detected from extension if not provided.
        streaming: If True, return LazyFrame for memory-efficient processing.

    Returns:
        DataFrame or LazyFrame depending on streaming parameter.
    """
    fmt = format or _detect_format(path)
    logger.info(f"Reading {fmt.upper()} file: {path}")

    if fmt == "csv":
        if streaming:
            return pl.scan_csv(path)
        return pl.read_csv(path)
    elif fmt == "parquet":
        if streaming:
            return pl.scan_parquet(path)
        return pl.read_parquet(path)
    elif fmt == "json":
        return pl.read_json(path)
    elif fmt == "ndjson":
        if streaming:
            return pl.scan_ndjson(path)
        return pl.read_ndjson(path)
    elif fmt == "avro":
        return pl.read_avro(path)
    else:
        raise ValueError(f"Unsupported input format: {fmt}")


def _write_file(
    df: pl.DataFrame,
    path: Path,
    format: str | None = None,
) -> None:
    """Write output file in various formats.

    Args:
        df: DataFrame to write.
        path: Output file path.
        format: File format. Auto-detected from extension if not provided.
    """
    fmt = format or _detect_format(path)
    logger.info(f"Writing {fmt.upper()} file: {path}")

    if fmt == "csv":
        df.write_csv(path)
    elif fmt == "parquet":
        df.write_parquet(path)
    elif fmt == "json":
        df.write_json(path)
    elif fmt == "ndjson":
        df.write_ndjson(path)
    elif fmt == "avro":
        df.write_avro(path)
    else:
        raise ValueError(f"Unsupported output format: {fmt}")

    logger.info(f"Successfully wrote {df.height} rows to {path}")


# Create typer app
app = typer.Typer(
    name="comorbidipy",
    help="Calculate clinical comorbidity scores from ICD codes.",
    add_completion=False,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"comorbidipy version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output."),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress all output except errors."),
    ] = False,
) -> None:
    """Comorbidipy - Calculate clinical comorbidity scores from ICD codes."""
    if quiet:
        logger.setLevel(logging.ERROR)
    elif verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


@app.command()
def charlson(
    input_file: Annotated[
        Path,
        typer.Argument(help="Input file path (CSV, Parquet, JSON, or Avro)."),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(help="Output file path."),
    ],
    id_col: Annotated[
        str,
        typer.Option("--id-col", "-i", help="Column name for patient/episode ID."),
    ] = "id",
    code_col: Annotated[
        str,
        typer.Option("--code-col", "-c", help="Column name for ICD codes."),
    ] = "code",
    age_col: Annotated[
        str | None,
        typer.Option("--age-col", "-a", help="Column name for age (optional)."),
    ] = None,
    icd_version: Annotated[
        ICDVersion,
        typer.Option("--icd", help="ICD version: icd9 or icd10."),
    ] = ICDVersion.ICD10,
    mapping: Annotated[
        MappingVariant,
        typer.Option("--mapping", "-m", help="Mapping variant."),
    ] = MappingVariant.QUAN,
    weights: Annotated[
        WeightingVariant,
        typer.Option("--weights", "-w", help="Weighting variant."),
    ] = WeightingVariant.QUAN,
    assign_zero: Annotated[
        bool,
        typer.Option(
            "--assign-zero/--no-assign-zero",
            help="Zero less severe comorbidity if more severe present.",
        ),
    ] = True,
    input_format: Annotated[
        str | None,
        typer.Option(
            "--input-format", help="Input file format (auto-detected if not set)."
        ),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option(
            "--output-format", help="Output file format (auto-detected if not set)."
        ),
    ] = None,
    streaming: Annotated[
        bool,
        typer.Option("--streaming", help="Use streaming mode for large files."),
    ] = False,
) -> None:
    """Calculate Charlson Comorbidity Index.

    Mappings: quan, swedish, australian, shmi

    Weights: charlson, quan, shmi, shmi_modified

    Example:
        comorbidipy charlson input.csv output.parquet --mapping quan --weights charlson
    """
    try:
        df = _read_file(input_file, input_format, streaming)
        logger.info(
            f"Calculating Charlson score with {mapping} mapping and {weights} weights"
        )

        result = comorbidity(
            df,
            id=id_col,
            code=code_col,
            age=age_col,
            score=ScoreType.CHARLSON,
            icd=icd_version,
            variant=mapping,
            weighting=weights,
            assign0=assign_zero,
        )

        _write_file(result, output_file, output_format)
        typer.echo(
            f"✓ Charlson scores calculated for {result.height} patients → {output_file}"
        )

    except KeyError as e:
        logger.error(f"Column error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        logger.exception("Unexpected error")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def elixhauser(
    input_file: Annotated[
        Path,
        typer.Argument(help="Input file path (CSV, Parquet, JSON, or Avro)."),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(help="Output file path."),
    ],
    id_col: Annotated[
        str,
        typer.Option("--id-col", "-i", help="Column name for patient/episode ID."),
    ] = "id",
    code_col: Annotated[
        str,
        typer.Option("--code-col", "-c", help="Column name for ICD codes."),
    ] = "code",
    icd_version: Annotated[
        ICDVersion,
        typer.Option("--icd", help="ICD version: icd9 or icd10."),
    ] = ICDVersion.ICD10,
    weights: Annotated[
        WeightingVariant,
        typer.Option(
            "--weights", "-w", help="Weighting variant: van_walraven or swiss."
        ),
    ] = WeightingVariant.VAN_WALRAVEN,
    assign_zero: Annotated[
        bool,
        typer.Option(
            "--assign-zero/--no-assign-zero",
            help="Zero less severe comorbidity if more severe present.",
        ),
    ] = True,
    input_format: Annotated[
        str | None,
        typer.Option(
            "--input-format", help="Input file format (auto-detected if not set)."
        ),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option(
            "--output-format", help="Output file format (auto-detected if not set)."
        ),
    ] = None,
    streaming: Annotated[
        bool,
        typer.Option("--streaming", help="Use streaming mode for large files."),
    ] = False,
) -> None:
    """Calculate Elixhauser Comorbidity Index.

    Mappings: quan (only ICD-10 supported)

    Weights: van_walraven, swiss

    Example:
        comorbidipy elixhauser input.csv output.parquet --weights van_walraven
    """
    try:
        df = _read_file(input_file, input_format, streaming)
        logger.info(f"Calculating Elixhauser score with {weights} weights")

        result = comorbidity(
            df,
            id=id_col,
            code=code_col,
            age=None,
            score=ScoreType.ELIXHAUSER,
            icd=icd_version,
            variant=MappingVariant.QUAN,
            weighting=weights,
            assign0=assign_zero,
        )

        _write_file(result, output_file, output_format)
        typer.echo(f"✓ Elixhauser scores for {result.height} patients → {output_file}")

    except KeyError as e:
        logger.error(f"Column error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        logger.exception("Unexpected error")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def hfrs_cmd(
    input_file: Annotated[
        Path,
        typer.Argument(help="Input file path (CSV, Parquet, JSON, or Avro)."),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(help="Output file path."),
    ],
    id_col: Annotated[
        str,
        typer.Option("--id-col", "-i", help="Column name for patient/episode ID."),
    ] = "id",
    code_col: Annotated[
        str,
        typer.Option("--code-col", "-c", help="Column name for ICD codes."),
    ] = "code",
    input_format: Annotated[
        str | None,
        typer.Option(
            "--input-format", help="Input file format (auto-detected if not set)."
        ),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option(
            "--output-format", help="Output file format (auto-detected if not set)."
        ),
    ] = None,
    streaming: Annotated[
        bool,
        typer.Option("--streaming", help="Use streaming mode for large files."),
    ] = False,
) -> None:
    """Calculate Hospital Frailty Risk Score (HFRS).

    Only applicable to patients aged 75 years or older.
    Uses ICD-10 codes only.

    Reference: Gilbert et al. Lancet 2018

    Example:
        comorbidipy hfrs input.csv output.parquet
    """
    try:
        df = _read_file(input_file, input_format, streaming)
        logger.info("Calculating Hospital Frailty Risk Score")

        result = hfrs(df, id_col=id_col, code_col=code_col)

        _write_file(result, output_file, output_format)
        typer.echo(f"✓ HFRS calculated for {result.height} patients → {output_file}")

    except KeyError as e:
        logger.error(f"Column error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        logger.exception("Unexpected error")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def disability_cmd(
    input_file: Annotated[
        Path,
        typer.Argument(help="Input file path (CSV, Parquet, JSON, or Avro)."),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(help="Output file path."),
    ],
    id_col: Annotated[
        str,
        typer.Option("--id-col", "-i", help="Column name for patient/episode ID."),
    ] = "id",
    code_col: Annotated[
        str,
        typer.Option("--code-col", "-c", help="Column name for ICD codes."),
    ] = "code",
    input_format: Annotated[
        str | None,
        typer.Option(
            "--input-format", help="Input file format (auto-detected if not set)."
        ),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option(
            "--output-format", help="Output file format (auto-detected if not set)."
        ),
    ] = None,
    streaming: Annotated[
        bool,
        typer.Option("--streaming", help="Use streaming mode for large files."),
    ] = False,
) -> None:
    """Identify disabilities and sensory impairments.

    Identifies learning disabilities, visual impairments, hearing impairments,
    and other conditions from ICD-10 codes.

    Example:
        comorbidipy disability input.csv output.parquet
    """
    try:
        df = _read_file(input_file, input_format, streaming)
        logger.info("Identifying disabilities and sensory impairments")

        result = disability(df, id_col=id_col, code_col=code_col)

        _write_file(result, output_file, output_format)
        typer.echo(
            f"✓ Disabilities identified for {result.height} patients → {output_file}"
        )

    except KeyError as e:
        logger.error(f"Column error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        logger.exception("Unexpected error")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def info() -> None:
    """Show available mappings and weighting variants."""
    typer.echo("\n[bold]Comorbidipy - Available Options[/bold]\n")

    typer.echo("[bold cyan]Charlson Comorbidity Index[/bold cyan]")
    typer.echo("  Mappings: quan, swedish, australian, shmi")
    typer.echo("  Weights:  charlson, quan, shmi, shmi_modified")
    typer.echo("  ICD:      icd9, icd10\n")

    typer.echo("[bold cyan]Elixhauser Comorbidity Index[/bold cyan]")
    typer.echo("  Mappings: quan (ICD-10 only)")
    typer.echo("  Weights:  van_walraven, swiss\n")

    typer.echo("[bold cyan]Hospital Frailty Risk Score[/bold cyan]")
    typer.echo("  ICD-10 only, patients ≥75 years\n")

    typer.echo("[bold cyan]Disability & Sensory Impairments[/bold cyan]")
    typer.echo("  ICD-10 only\n")

    typer.echo("[bold]Supported file formats:[/bold] CSV, Parquet, JSON, NDJSON, Avro")


if __name__ == "__main__":
    app()
