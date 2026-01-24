"""Tests for Hospital Frailty Risk Score (HFRS) calculator."""

import polars as pl
import pytest
from conftest import generate_hfrs_data

from comorbidipy import hfrs


class TestHFRSInputValidation:
    """Tests for input validation."""

    def test_missing_id_column_raises_error(self):
        """Should raise KeyError when id column is missing."""
        df = pl.DataFrame({"code": ["F00", "G81"]})
        with pytest.raises(KeyError, match="must be present"):
            hfrs(df, id_col="id", code_col="code")

    def test_missing_code_column_raises_error(self):
        """Should raise KeyError when code column is missing."""
        df = pl.DataFrame({"id": ["1", "2"]})
        with pytest.raises(KeyError, match="must be present"):
            hfrs(df, id_col="id", code_col="code")

    def test_empty_dataframe_returns_empty_result(self):
        """Should handle empty DataFrame gracefully."""
        df = pl.DataFrame(
            {
                "id": pl.Series([], dtype=pl.Utf8),
                "code": pl.Series([], dtype=pl.Utf8),
            }
        )
        result = hfrs(df)
        assert result.height == 0

    def test_custom_column_names(self):
        """Should work with custom column names."""
        df = pl.DataFrame(
            {
                "patient_id": ["1", "2"],
                "icd_code": ["F00", "G81"],
            }
        )
        result = hfrs(df, id_col="patient_id", code_col="icd_code")
        assert result.height == 2
        assert "patient_id" in result.columns
        assert "hfrs" in result.columns


class TestHFRSCalculation:
    """Tests for HFRS score calculation."""

    def test_basic_hfrs_calculation(self):
        """Test basic HFRS calculation."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "2", "3"],
                "code": ["F00", "G81", "R54", "A00"],
            }
        )
        result = hfrs(df)

        assert result.height == 3
        assert "id" in result.columns
        assert "hfrs" in result.columns

        # Patient 1 has F00 and G81 (both are HFRS codes)
        p1 = result.filter(pl.col("id") == "1")
        assert p1["hfrs"][0] > 0

        # Patient 3 has A00 which is not an HFRS code
        p3 = result.filter(pl.col("id") == "3")
        assert p3["hfrs"][0] == 0

    def test_hfrs_code_prefix_matching(self):
        """Test that codes are matched by first 3 characters."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["F00.1", "F001"],  # Both should match F00
            }
        )
        result = hfrs(df)

        # Both should have the same HFRS score for F00
        p1 = result.filter(pl.col("id") == "1")
        p2 = result.filter(pl.col("id") == "2")
        assert p1["hfrs"][0] == p2["hfrs"][0]
        assert p1["hfrs"][0] > 0

    def test_hfrs_case_insensitive(self):
        """Test that code matching is case-insensitive."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["f00", "F00"],
            }
        )
        result = hfrs(df)

        p1 = result.filter(pl.col("id") == "1")
        p2 = result.filter(pl.col("id") == "2")
        assert p1["hfrs"][0] == p2["hfrs"][0]

    def test_hfrs_whitespace_handling(self):
        """Test that leading/trailing whitespace is handled."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": [" F00", "F00 "],
            }
        )
        result = hfrs(df)

        p1 = result.filter(pl.col("id") == "1")
        p2 = result.filter(pl.col("id") == "2")
        assert p1["hfrs"][0] == p2["hfrs"][0]
        assert p1["hfrs"][0] > 0

    def test_hfrs_duplicate_codes_counted_once(self):
        """Test that duplicate codes for same patient are counted once."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1"],
                "code": ["F00", "F00", "F00"],
            }
        )
        result = hfrs(df)

        # Should only count F00 once
        single_code_df = pl.DataFrame(
            {
                "id": ["2"],
                "code": ["F00"],
            }
        )
        single_result = hfrs(single_code_df)

        assert result["hfrs"][0] == single_result["hfrs"][0]

    def test_hfrs_multiple_codes_summed(self):
        """Test that multiple different codes are summed."""
        df = pl.DataFrame(
            {
                "id": ["1", "1"],
                "code": ["F00", "G81"],
            }
        )
        result = hfrs(df)

        # Get individual scores
        f00_df = pl.DataFrame({"id": ["f"], "code": ["F00"]})
        g81_df = pl.DataFrame({"id": ["g"], "code": ["G81"]})
        f00_score = hfrs(f00_df)["hfrs"][0]
        g81_score = hfrs(g81_df)["hfrs"][0]

        # Combined score should be sum of individual scores
        assert result["hfrs"][0] == f00_score + g81_score

    def test_hfrs_patients_without_frailty_codes_get_zero(self):
        """Test that patients without frailty codes get score of 0."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "2"],
                "code": ["A00", "A01", "F00"],
            }
        )
        result = hfrs(df)

        p1 = result.filter(pl.col("id") == "1")
        p2 = result.filter(pl.col("id") == "2")

        assert p1["hfrs"][0] == 0
        assert p2["hfrs"][0] > 0


class TestHFRSSyntheticData:
    """Tests using synthetic data."""

    def test_hfrs_with_synthetic_data(self):
        """Test HFRS calculation with synthetic data."""
        df = generate_hfrs_data(n_patients=100, seed=42)
        result = hfrs(df)

        assert result.height == 100
        assert "hfrs" in result.columns
        assert result["hfrs"].null_count() == 0

    def test_hfrs_all_patients_returned(self):
        """Test that all unique patients are in result."""
        df = generate_hfrs_data(n_patients=500, seed=42)
        n_unique_patients = df["id"].n_unique()

        result = hfrs(df)
        assert result.height == n_unique_patients


class TestHFRSLazyFrame:
    """Tests for LazyFrame input support."""

    def test_hfrs_with_lazyframe(self):
        """Test HFRS calculation with LazyFrame input."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["F00", "G81"],
            }
        )
        lazy_df = df.lazy()

        result = hfrs(lazy_df)

        assert isinstance(result, pl.DataFrame)
        assert result.height == 2


class TestHFRSNullHandling:
    """Tests for null value handling."""

    def test_null_ids_excluded(self):
        """Test that rows with null IDs are excluded."""
        df = pl.DataFrame(
            {
                "id": ["1", None, "2"],
                "code": ["F00", "G81", "R54"],
            }
        )
        result = hfrs(df)

        assert result.height == 2
        assert None not in result["id"].to_list()

    def test_null_codes_excluded(self):
        """Test that rows with null codes are excluded."""
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["F00", None, "R54"],
            }
        )
        result = hfrs(df)

        # Patient 2 only has null code, so only patients 1 and 3 are returned
        assert result.height == 2
        assert "2" not in result["id"].to_list()
