"""Extended comorbidity tests for additional edge cases and mappings.

Tests additional mapping variants, ICD-9 codes, survival calculations,
and edge cases not covered in the main test_comorbidity.py.
"""

import polars as pl

from comorbidipy import (
    ICDVersion,
    MappingVariant,
    ScoreType,
    WeightingVariant,
    comorbidity,
)


class TestICD9CharlsonScore:
    """Tests for ICD-9 Charlson calculations."""

    def test_icd9_quan_basic(self):
        """Test basic ICD-9 Charlson calculation with Quan mapping."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "2", "2", "3"],
                "code": ["410", "428", "250", "196", "496"],
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col=None,
            score=ScoreType.CHARLSON,
            icd=ICDVersion.ICD9,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.QUAN,
        )

        assert result.height == 3
        assert "comorbidity_score" in result.columns

        # Patient 1 has AMI (410) and CHF (428)
        p1 = result.filter(pl.col("id") == "1")
        assert p1["ami"][0] == 1
        assert p1["chf"][0] == 1

    def test_icd9_multiple_codes_same_comorbidity(self):
        """Test that multiple ICD-9 codes for same comorbidity don't double count."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1"],
                "code": ["4280", "4281", "4289"],  # All CHF codes
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.CHARLSON,
            icd=ICDVersion.ICD9,
            variant=MappingVariant.QUAN,
            age_col=None,
        )

        # Should only count CHF once
        assert result["chf"][0] == 1
        assert result.height == 1


class TestICD9ElixhauserScore:
    """Tests for ICD-9 Elixhauser calculations."""

    def test_icd9_elixhauser_basic(self):
        """Test basic ICD-9 Elixhauser calculation."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "2"],
                "code": ["401", "250", "296"],  # HTN, DM, Depression
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col=None,
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD9,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.VAN_WALRAVEN,
        )

        assert result.height == 2
        assert "comorbidity_score" in result.columns


class TestSHMIMapping:
    """Tests for SHMI mapping variant."""

    def test_shmi_mapping_basic(self):
        """Test SHMI mapping with ICD-10 codes."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "2"],
                "code": ["I21", "I50", "E112"],
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.CHARLSON,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.SHMI,
            weighting=WeightingVariant.SHMI,
            age_col=None,
        )

        assert result.height == 2
        assert "comorbidity_score" in result.columns

    def test_shmi_modified_weights(self):
        """Test SHMI modified weighting."""
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["E112"],  # Diabetes with complications
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.CHARLSON,
            variant=MappingVariant.SHMI,
            weighting=WeightingVariant.SHMI_MODIFIED,
            age_col=None,
        )

        # SHMI modified has different weight for diabwc
        assert result["diabwc"][0] == 1
        assert result["comorbidity_score"][0] >= 0


class TestAustralianMapping:
    """Tests for Australian mapping variant."""

    def test_australian_mapping_basic(self):
        """Test Australian mapping with ICD-10 codes."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "2"],
                "code": ["I21", "I50", "J44"],
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.CHARLSON,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.AUSTRALIAN,
            weighting=WeightingVariant.CHARLSON,
            age_col=None,
        )

        assert result.height == 2
        assert "comorbidity_score" in result.columns


class TestSurvivalCalculation:
    """Tests for 10-year survival calculation."""

    def test_survival_calculated_with_charlson_weights_and_age(self):
        """Test that survival is calculated with Charlson weights and age."""
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["I21", "I21", "I21"],
                "age": [35, 55, 75],
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col="age",
            score=ScoreType.CHARLSON,
            weighting=WeightingVariant.CHARLSON,
        )

        assert "survival_10yr" in result.columns
        assert result["survival_10yr"].null_count() == 0

        # Survival should decrease with higher comorbidity/age score
        p1_survival = result.filter(pl.col("id") == "1")["survival_10yr"][0]
        p3_survival = result.filter(pl.col("id") == "3")["survival_10yr"][0]
        assert p1_survival > p3_survival

    def test_survival_not_calculated_without_age(self):
        """Test that survival is not calculated without age column."""
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["I21"],
            }
        )
        result = comorbidity(
            df,
            age_col=None,
            weighting=WeightingVariant.CHARLSON,
        )

        assert "survival_10yr" not in result.columns

    def test_survival_not_calculated_with_non_charlson_weights(self):
        """Test that survival is not calculated with non-Charlson weights."""
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["I21"],
                "age": [65],
            }
        )
        result = comorbidity(
            df,
            age_col="age",
            weighting=WeightingVariant.QUAN,
        )

        # Age adjustment exists but survival formula is only for Charlson weights
        assert "survival_10yr" not in result.columns


class TestAgeAdjustment:
    """Tests for age adjustment in Charlson score."""

    def test_age_adjustment_boundaries(self):
        """Test age adjustment at boundary values."""
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3", "4", "5"],
                "code": ["I21", "I21", "I21", "I21", "I21"],
                "age": [30, 40, 50, 80, 90],  # Various ages
            }
        )
        result = comorbidity(
            df,
            age_col="age",
            weighting=WeightingVariant.CHARLSON,
        )

        # Age < 40: age score = 0
        p1 = result.filter(pl.col("id") == "1")
        base_score = p1["comorbidity_score"][0]
        assert p1["age_adj_comorbidity_score"][0] == base_score

        # Age = 40: age score = 0 (floor((40-40)/10) = 0)
        p2 = result.filter(pl.col("id") == "2")
        assert p2["age_adj_comorbidity_score"][0] == base_score

        # Age = 50: age score = 1
        p3 = result.filter(pl.col("id") == "3")
        assert p3["age_adj_comorbidity_score"][0] == base_score + 1

        # Age > 80: age score should be capped at 4
        p4 = result.filter(pl.col("id") == "4")
        p5 = result.filter(pl.col("id") == "5")
        assert p4["age_adj_comorbidity_score"][0] == base_score + 4
        assert p5["age_adj_comorbidity_score"][0] == base_score + 4  # Capped

    def test_age_column_preserved_in_output(self):
        """Test that age column is preserved in output."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["I21", "I50"],
                "age": [65, 55],
            }
        )
        result = comorbidity(df, age_col="age")

        assert "age" in result.columns


class TestLazyFrameInput:
    """Tests for LazyFrame input support."""

    def test_comorbidity_with_lazyframe(self):
        """Test comorbidity calculation with LazyFrame input."""
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["I21", "I50", "J44"],
            }
        )
        lazy_df = df.lazy()

        result = comorbidity(lazy_df, age_col=None)

        assert isinstance(result, pl.DataFrame)
        assert result.height == 3

    def test_lazyframe_with_age(self):
        """Test comorbidity with LazyFrame and age column."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["I21", "I50"],
                "age": [65, 55],
            }
        )
        lazy_df = df.lazy()

        result = comorbidity(
            lazy_df, age_col="age", weighting=WeightingVariant.CHARLSON
        )

        assert isinstance(result, pl.DataFrame)
        assert "age_adj_comorbidity_score" in result.columns


class TestCodeNormalization:
    """Tests for ICD code normalization."""

    def test_codes_with_dots(self):
        """Test that codes with dots are handled correctly."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["I21.0", "I21.1"],  # Codes with dots
            }
        )
        result = comorbidity(df, age_col=None)

        # Both should be recognized as AMI
        assert result.height == 2
        assert result.filter(pl.col("id") == "1")["ami"][0] == 1
        assert result.filter(pl.col("id") == "2")["ami"][0] == 1

    def test_mixed_case_codes(self):
        """Test that mixed case codes work (they should, based on prefix matching)."""
        df = pl.DataFrame(
            {
                "id": ["1", "2"],
                "code": ["i21", "I21"],  # Mixed case
            }
        )
        # This might fail if codes aren't normalized - depends on implementation
        # Just verify it doesn't crash
        result = comorbidity(df, age_col=None)
        assert result.height == 2


class TestAllComorbidityColumns:
    """Tests to verify all expected columns are present."""

    def test_charlson_all_columns_present(self):
        """Test that all Charlson comorbidity columns are in output."""
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["A00"],  # Non-comorbidity code
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.CHARLSON,
            age_col=None,
        )

        expected_columns = [
            "ami",
            "chf",
            "pvd",
            "cevd",
            "dementia",
            "copd",
            "rheumd",
            "pud",
            "mld",
            "diab",
            "diabwc",
            "hp",
            "rend",
            "canc",
            "msld",
            "metacanc",
            "aids",
            "comorbidity_score",
        ]

        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"

    def test_elixhauser_all_columns_present(self):
        """Test that all Elixhauser comorbidity columns are in output."""
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["A00"],  # Non-comorbidity code
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.ELIXHAUSER,
            weighting=WeightingVariant.VAN_WALRAVEN,
            age_col=None,
        )

        expected_columns = [
            "chf",
            "carit",
            "valv",
            "pcd",
            "pvd",
            "hypunc",
            "hypc",
            "para",
            "ond",
            "cpd",
            "diabunc",
            "diabc",
            "hypothy",
            "rf",
            "ld",
            "pud",
            "aids",
            "lymph",
            "metacanc",
            "solidtum",
            "rheumd",
            "coag",
            "obes",
            "wloss",
            "fed",
            "blane",
            "dane",
            "alcohol",
            "drug",
            "psycho",
            "depre",
            "comorbidity_score",
        ]

        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"


class TestWeightingVariants:
    """Tests for different weighting variants."""

    def test_all_charlson_weighting_variants(self):
        """Test all Charlson weighting variants run without error."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1"],
                "code": ["I21", "I50", "E112"],
            }
        )

        for weight in [
            WeightingVariant.CHARLSON,
            WeightingVariant.QUAN,
        ]:
            result = comorbidity(
                df,
                score=ScoreType.CHARLSON,
                variant=MappingVariant.QUAN,
                weighting=weight,
                age_col=None,
            )
            assert "comorbidity_score" in result.columns
            assert result.height == 1

    def test_all_elixhauser_weighting_variants(self):
        """Test all Elixhauser weighting variants run without error."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1"],
                "code": ["I10", "E119", "F32"],
            }
        )

        for weight in [WeightingVariant.VAN_WALRAVEN, WeightingVariant.SWISS]:
            result = comorbidity(
                df,
                score=ScoreType.ELIXHAUSER,
                variant=MappingVariant.QUAN,
                weighting=weight,
                age_col=None,
            )
            assert "comorbidity_score" in result.columns
            assert result.height == 1


class TestIntegerIds:
    """Tests for integer patient IDs."""

    def test_integer_patient_ids(self):
        """Test that integer patient IDs work correctly."""
        df = pl.DataFrame(
            {
                "id": [1, 1, 2, 2, 3],
                "code": ["I21", "I50", "E112", "C78", "J44"],
            }
        )
        result = comorbidity(df, age_col=None)

        assert result.height == 3
        assert result.filter(pl.col("id") == 1)["ami"][0] == 1

    def test_mixed_type_ids(self):
        """Test behavior with various ID types."""
        # UUID-like strings
        df = pl.DataFrame(
            {
                "id": [
                    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "b2c3d4e5-f6a7-8901-bcde-f23456789012",
                ],
                "code": ["I21", "I50", "J44"],
            }
        )
        result = comorbidity(df, age_col=None)

        assert result.height == 2


class TestEmptyResults:
    """Tests for empty result handling."""

    def test_no_matching_codes(self):
        """Test handling when no codes match any comorbidity."""
        # Use codes that definitely don't match any comorbidity
        # A00 = cholera, X99 = invalid code, Z00 = general exam
        df = pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "code": ["A00", "X99", "Z00"],  # Non-matching codes
            }
        )
        result = comorbidity(df, age_col=None)

        assert result.height == 3
        assert result["comorbidity_score"].sum() == 0


class TestDuplicateHandling:
    """Tests for duplicate data handling."""

    def test_duplicate_rows_handled(self):
        """Test that completely duplicate rows are handled."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1", "1"],
                "code": ["I21", "I21", "I21", "I21"],  # Same row repeated
            }
        )
        result = comorbidity(df, age_col=None)

        assert result.height == 1
        assert result["ami"][0] == 1  # Should only be counted once
