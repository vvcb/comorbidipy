"""Tests for the CLI."""

import tempfile
from pathlib import Path

import polars as pl
from conftest import generate_charlson_data, generate_hfrs_data
from typer.testing import CliRunner

from comorbidipy.cli import app

runner = CliRunner()


class TestCLIBasic:
    """Basic CLI tests."""

    def test_version_flag(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "comorbidipy version" in result.stdout

    def test_help_flag(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "comorbidipy" in result.stdout.lower()

    def test_info_command(self):
        """Test info command."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "Charlson" in result.stdout
        assert "Elixhauser" in result.stdout


class TestCharlsonCLI:
    """Tests for charlson CLI command."""

    def test_charlson_csv_to_csv(self):
        """Test charlson command with CSV input and output."""
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
                    "--id-col",
                    "id",
                    "--code-col",
                    "code",
                    "--age-col",
                    "age",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

            output_df = pl.read_csv(output_path)
            assert output_df.height == 10
            assert "comorbidity_score" in output_df.columns

    def test_charlson_csv_to_parquet(self):
        """Test charlson command with CSV input and Parquet output."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.parquet"

            df.write_csv(input_path)

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

            output_df = pl.read_parquet(output_path)
            assert output_df.height == 10

    def test_charlson_with_mapping_option(self):
        """Test charlson command with mapping option."""
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
                    "swedish",
                ],
            )

            assert result.exit_code == 0

    def test_charlson_missing_input_file(self):
        """Test charlson command with missing input file."""
        result = runner.invoke(
            app,
            [
                "charlson",
                "nonexistent.csv",
                "output.csv",
            ],
        )

        assert result.exit_code == 1


class TestElixhauserCLI:
    """Tests for elixhauser CLI command."""

    def test_elixhauser_basic(self):
        """Test elixhauser command."""
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
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()


class TestHFRSCLI:
    """Tests for hfrs CLI command."""

    def test_hfrs_basic(self):
        """Test hfrs command."""
        df = generate_hfrs_data(n_patients=10, seed=42)

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

            assert result.exit_code == 0
            assert output_path.exists()

            output_df = pl.read_csv(output_path)
            assert "hfrs" in output_df.columns


class TestDisabilityCLI:
    """Tests for disability CLI command."""

    def test_disability_basic(self):
        """Test disability command."""
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["F70", "H54", "A00"],
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
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()


class TestCLIFileFormats:
    """Tests for different file format support."""

    def test_parquet_input(self):
        """Test reading Parquet input."""
        df = generate_charlson_data(n_patients=10, seed=42)

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
                ],
            )

            assert result.exit_code == 0

    def test_json_output(self):
        """Test writing JSON output."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.json"

            df.write_csv(input_path)

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


class TestCLIVerbosity:
    """Tests for verbosity options."""

    def test_verbose_flag(self):
        """Test --verbose flag."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "--verbose",
                    "charlson",
                    str(input_path),
                    str(output_path),
                ],
            )

            assert result.exit_code == 0

    def test_quiet_flag(self):
        """Test --quiet flag."""
        df = generate_charlson_data(n_patients=10, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            df.write_csv(input_path)

            result = runner.invoke(
                app,
                [
                    "--quiet",
                    "charlson",
                    str(input_path),
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
