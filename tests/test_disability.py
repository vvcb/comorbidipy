"""Tests for disability and sensory impairments identifier."""

import polars as pl
import pytest
from conftest import generate_disability_data

from comorbidipy import disability


class TestDisabilityInputValidation:
    """Tests for input validation."""

    def test_missing_id_column_raises_error(self):
        """Should raise KeyError when id column is missing."""
        df = pl.DataFrame({"code": ["F70", "H54"]})
        with pytest.raises(KeyError, match="must be present"):
            disability(df, id_col="id", code_col="code")

    def test_missing_code_column_raises_error(self):
        """Should raise KeyError when code column is missing."""
        df = pl.DataFrame({"id": ["1", "2"]})
        with pytest.raises(KeyError, match="must be present"):
            disability(df, id_col="id", code_col="code")

    def test_empty_dataframe_returns_result_with_columns(self):
        """Should handle empty DataFrame gracefully."""
        df = pl.DataFrame(
            {
                "id": pl.Series([], dtype=pl.Utf8),
                "code": pl.Series([], dtype=pl.Utf8),
            }
        )
        result = disability(df)
        assert result.height == 0

    def test_custom_column_names(self):
        """Should work with custom column names."""
        df = pl.DataFrame(
            {
                "patient_id": ["1", "2"],
                "icd_code": ["F70", "H54"],
            }
        )
        result = disability(df, id_col="patient_id", code_col="icd_code")
        assert result.height == 2
        assert "patient_id" in result.columns


class TestDisabilityCalculation:
    """Tests for disability identification."""

    def test_learning_disability_identification(self):
        """Test identification of learning disability codes."""
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["F70", "F71", "A00"],
            }
        )
        result = disability(df)

        assert result.height == 3

        # Patients 1 and 2 have learning disability codes
        p1 = result.filter(pl.col("id") == "1")
        p2 = result.filter(pl.col("id") == "2")
        p3 = result.filter(pl.col("id") == "3")

        assert p1["ld_asd"][0] == 1
        assert p2["ld_asd"][0] == 1
        assert p3["ld_asd"][0] == 0

    def test_visual_impairment_identification(self):
        """Test identification of visual impairment codes."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["H54", "H540"],
            }
        )
        result = disability(df)

        # Both should have visual impairment
        assert result["impaired_vision"].sum() == 2

    def test_hearing_impairment_identification(self):
        """Test identification of hearing impairment codes."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["H90", "H91"],
            }
        )
        result = disability(df)

        # Both should have hearing impairment
        assert result["impaired_hearing"].sum() == 2

    def test_multiple_impairments_per_patient(self):
        """Test patient with multiple impairment types."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1"],
                "code": ["F70", "H54", "H90"],
            }
        )
        result = disability(df)

        assert result.height == 1
        assert result["ld_asd"][0] == 1
        assert result["impaired_vision"][0] == 1
        assert result["impaired_hearing"][0] == 1

    def test_duplicate_codes_counted_once(self):
        """Test that duplicate codes for same patient are counted once."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1"],
                "code": ["F70", "F70", "F70"],
            }
        )
        result = disability(df)

        assert result.height == 1
        assert result["ld_asd"][0] == 1

    def test_patients_without_impairments_get_zero(self):
        """Test that patients without impairment codes get 0."""
        df = pl.DataFrame(
            {
                "id": ["1", "1"],
                "code": ["A00", "B00"],
            }
        )
        result = disability(df)

        # Check that all impairment columns are 0
        for col in result.columns:
            if col != "id":
                assert result[col][0] == 0


class TestDisabilitySyntheticData:
    """Tests using synthetic data."""

    def test_disability_with_synthetic_data(self):
        """Test disability identification with synthetic data."""
        df = generate_disability_data(n_patients=100, seed=42)
        result = disability(df)

        assert result.height == 100
        assert "id" in result.columns

    def test_disability_all_patients_returned(self):
        """Test that all unique patients are in result."""
        df = generate_disability_data(n_patients=500, seed=42)
        n_unique_patients = df["id"].n_unique()

        result = disability(df)
        assert result.height == n_unique_patients


class TestDisabilityLazyFrame:
    """Tests for LazyFrame input support."""

    def test_disability_with_lazyframe(self):
        """Test disability identification with LazyFrame input."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["F70", "H54"],
            }
        )
        lazy_df = df.lazy()

        result = disability(lazy_df)

        assert isinstance(result, pl.DataFrame)
        assert result.height == 2


class TestDisabilityNullHandling:
    """Tests for null value handling."""

    def test_null_ids_excluded(self):
        """Test that rows with null IDs are excluded."""
        df = pl.DataFrame(
            {
                "id": ["1", None, "2"],
                "code": ["F70", "H54", "H90"],
            }
        )
        result = disability(df)

        # Only valid patients should be returned
        assert None not in result["id"].to_list()

    def test_null_codes_excluded(self):
        """Test that rows with null codes are excluded."""
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["F70", None, "H54"],
            }
        )
        result = disability(df)

        # Patient 2 only has null code, so only patients 1 and 3 are returned
        assert result.height == 2
        assert "2" not in result["id"].to_list()
