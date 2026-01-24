"""Extended CLI tests for comorbidipy.

Tests additional CLI functionality including file formats, streaming,
error handling, and edge cases not covered in the main test_cli.py.
"""

import tempfile
from pathlib import Path

import polars as pl
from conftest import generate_charlson_data, generate_hfrs_data
from typer.testing import CliRunner

from comorbidipy.cli import app

runner = CliRunner()


class TestCLIFileFormats:
    """Tests for additional file format support."""

    def test_ndjson_input_output(self):
        """Test reading and writing NDJSON format."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.ndjson"
            output_path = Path(tmpdir) / "output.ndjson"

            df.write_ndjson(input_path)

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

            output_df = pl.read_ndjson(output_path)
            assert output_df.height == 10

    def test_ndjson_streaming_mode(self):
        """Test NDJSON format with streaming mode."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.ndjson"
            output_path = Path(tmpdir) / "output.csv"

            df.write_ndjson(input_path)

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                    "--streaming",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

    def test_avro_input_output(self):
        """Test reading and writing Avro format."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.avro"
            output_path = Path(tmpdir) / "output.avro"

            df.write_avro(input_path)

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

            output_df = pl.read_avro(output_path)
            assert output_df.height == 10


class TestCLIStreaming:
    """Tests for streaming mode."""

    def test_charlson_streaming_mode(self):
        """Test charlson command with streaming mode."""
        df = generate_charlson_data(n_patients=100, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                    "--streaming",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

            output_df = pl.read_csv(output_path)
            assert output_df.height == 100

    def test_elixhauser_streaming_mode(self):
        """Test elixhauser command with streaming mode."""
        df = generate_charlson_data(n_patients=100, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"

            df.write_parquet(input_path)

            result = runner.invoke(
                app,
                [
                    "elixhauser",
                    str(input_path),
                    str(output_path),
                    "--streaming",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

    def test_hfrs_streaming_mode(self):
        """Test HFRS command with streaming mode."""
        df = generate_hfrs_data(n_patients=50, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "hfrs-cmd",
                    str(input_path),
                    str(output_path),
                    "--streaming",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

    def test_disability_streaming_mode(self):
        """Test disability command with streaming mode."""
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["F70", "H54", "H90"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "disability-cmd",
                    str(input_path),
                    str(output_path),
                    "--streaming",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_unsupported_input_format(self):
        """Test error handling for unsupported input format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.xyz"
            output_path = Path(tmpdir) / "output.csv"

            # Create a dummy file with unsupported extension
            input_path.write_text("dummy content")

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                ],
            )

            # Should fail due to unsupported format
            assert result.exit_code == 1

    def test_elixhauser_missing_input_file(self):
        """Test elixhauser command with missing input file."""
        result = runner.invoke(
            app,
            [
                "elixhauser",
                "nonexistent.csv",
                "output.csv",
            ],
        )

        assert result.exit_code == 1

    def test_hfrs_missing_input_file(self):
        """Test HFRS command with missing input file."""
        result = runner.invoke(
            app,
            [
                "hfrs-cmd",
                "nonexistent.csv",
                "output.csv",
            ],
        )

        assert result.exit_code == 1

    def test_disability_missing_input_file(self):
        """Test disability command with missing input file."""
        result = runner.invoke(
            app,
            [
                "disability-cmd",
                "nonexistent.csv",
                "output.csv",
            ],
        )

        assert result.exit_code == 1

    def test_charlson_missing_columns(self):
        """Test charlson command with missing required columns."""
        df = pl.DataFrame({"wrong_col": ["value"]})

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                ],
            )

            assert result.exit_code == 1
            assert "Error" in result.output or "error" in result.output.lower()

    def test_elixhauser_missing_columns(self):
        """Test elixhauser command with missing required columns."""
        df = pl.DataFrame({"wrong_col": ["value"]})

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "elixhauser",
                    str(input_path),
                    str(output_path),
                ],
            )

            assert result.exit_code == 1

    def test_hfrs_missing_columns(self):
        """Test HFRS command with missing required columns."""
        df = pl.DataFrame({"wrong_col": ["value"]})

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "hfrs-cmd",
                    str(input_path),
                    str(output_path),
                ],
            )

            assert result.exit_code == 1

    def test_disability_missing_columns(self):
        """Test disability command with missing required columns."""
        df = pl.DataFrame({"wrong_col": ["value"]})

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "disability-cmd",
                    str(input_path),
                    str(output_path),
                ],
            )

            assert result.exit_code == 1


class TestCLICustomColumns:
    """Tests for custom column name support in CLI."""

    def test_charlson_custom_column_names(self):
        """Test charlson with custom column names."""
        df = pl.DataFrame(
            {
                "patient_id": ["1", "2", "3"],
                "icd_code": ["I21", "I50", "J44"],
                "patient_age": [65, 55, 45],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                    "--id-col",
                    "patient_id",
                    "--code-col",
                    "icd_code",
                    "--age-col",
                    "patient_age",
                ],
            )

            assert result.exit_code == 0
            output_df = pl.read_csv(output_path)
            assert "patient_id" in output_df.columns
            assert "comorbidity_score" in output_df.columns

    def test_elixhauser_custom_column_names(self):
        """Test elixhauser with custom column names."""
        df = pl.DataFrame(
            {
                "patient_id": ["1", "2", "3"],
                "icd_code": ["I10", "E119", "F32"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "elixhauser",
                    str(input_path),
                    str(output_path),
                    "--id-col",
                    "patient_id",
                    "--code-col",
                    "icd_code",
                ],
            )

            assert result.exit_code == 0
            output_df = pl.read_csv(output_path)
            assert "patient_id" in output_df.columns

    def test_hfrs_custom_column_names(self):
        """Test HFRS with custom column names."""
        df = pl.DataFrame(
            {
                "patient_id": ["1", "2"],
                "icd_code": ["F00", "G81"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "hfrs-cmd",
                    str(input_path),
                    str(output_path),
                    "--id-col",
                    "patient_id",
                    "--code-col",
                    "icd_code",
                ],
            )

            assert result.exit_code == 0
            output_df = pl.read_csv(output_path)
            assert "patient_id" in output_df.columns
            assert "hfrs_score" in output_df.columns

    def test_disability_custom_column_names(self):
        """Test disability with custom column names."""
        df = pl.DataFrame(
            {
                "patient_id": ["1", "2"],
                "icd_code": ["F70", "H54"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "disability-cmd",
                    str(input_path),
                    str(output_path),
                    "--id-col",
                    "patient_id",
                    "--code-col",
                    "icd_code",
                ],
            )

            assert result.exit_code == 0
            output_df = pl.read_csv(output_path)
            assert "patient_id" in output_df.columns


class TestCLIElixhauserOptions:
    """Tests for Elixhauser-specific CLI options."""

    def test_elixhauser_swiss_weights(self):
        """Test elixhauser with Swiss weights."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "elixhauser",
                    str(input_path),
                    str(output_path),
                    "--weights",
                    "swiss",
                ],
            )

            assert result.exit_code == 0

    def test_elixhauser_no_assign_zero(self):
        """Test elixhauser with assign-zero disabled."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "elixhauser",
                    str(input_path),
                    str(output_path),
                    "--no-assign-zero",
                ],
            )

            assert result.exit_code == 0

    def test_elixhauser_icd9(self):
        """Test elixhauser with ICD-9 codes."""
        # ICD-9 codes for Elixhauser - must be strings
        # Use parquet to preserve types instead of CSV which infers integers
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["4280", "40201", "4255"],
            },
            schema={"id": pl.Utf8, "code": pl.Utf8},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.csv"

            df.write_parquet(input_path)

            result = runner.invoke(
                app,
                [
                    "elixhauser",
                    str(input_path),
                    str(output_path),
                    "--icd",
                    "icd9",
                ],
            )

            assert result.exit_code == 0


class TestCLICharlsonOptions:
    """Tests for Charlson-specific CLI options."""

    def test_charlson_shmi_mapping(self):
        """Test charlson with SHMI mapping."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                    "--mapping",
                    "shmi",
                    "--weights",
                    "shmi",
                ],
            )

            assert result.exit_code == 0

    def test_charlson_australian_mapping(self):
        """Test charlson with Australian mapping."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                    "--mapping",
                    "australian",
                ],
            )

            assert result.exit_code == 0

    def test_charlson_icd9(self):
        """Test charlson with ICD-9 codes."""
        # Use parquet to preserve types instead of CSV which infers integers
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["410", "428", "496"],
                "age": [65, 55, 45],
            },
            schema={"id": pl.Utf8, "code": pl.Utf8, "age": pl.Int64},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.csv"

            df.write_parquet(input_path)

            result = runner.invoke(
                app,
                [
                    "charlson",
                    str(input_path),
                    str(output_path),
                    "--icd",
                    "icd9",
                ],
            )

            assert result.exit_code == 0
