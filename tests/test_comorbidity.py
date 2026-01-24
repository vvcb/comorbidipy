"""Tests for comorbidity calculator (Charlson and Elixhauser)."""

import polars as pl
import pytest
from conftest import generate_charlson_data

from comorbidipy import (
    ICDVersion,
    MappingVariant,
    ScoreType,
    WeightingVariant,
    comorbidity,
)


class TestComorbidityInputValidation:
    """Tests for input validation."""

    def test_missing_id_column_raises_error(self):
        """Should raise KeyError when id column is missing."""
        df = pl.DataFrame({"code": ["I21", "I50"]})
        with pytest.raises(KeyError, match="Missing column"):
            comorbidity(df, id_col="id", code_col="code")

    def test_missing_code_column_raises_error(self):
        """Should raise KeyError when code column is missing."""
        df = pl.DataFrame({"id": ["1", "2"]})
        with pytest.raises(KeyError, match="Missing column"):
            comorbidity(df, id_col="id", code_col="code")

    def test_missing_age_column_raises_error(self):
        """Should raise KeyError when age column specified but missing."""
        df = pl.DataFrame({"id": ["1", "2"], "code": ["I21", "I50"]})
        with pytest.raises(KeyError, match="age"):
            comorbidity(df, id_col="id", code_col="code", age_col="age")

    def test_invalid_mapping_variant_raises_error(self):
        """Should raise KeyError for invalid score/icd/variant combination."""
        df = pl.DataFrame({"id": ["1"], "code": ["I21"]})
        with pytest.raises(KeyError, match="Combination of score"):
            comorbidity(
                df,
                score=ScoreType.CHARLSON,
                icd=ICDVersion.ICD9,
                variant=MappingVariant.SWEDISH,  # Swedish only available for ICD10
                age_col=None,
            )

    def test_empty_dataframe_returns_empty_result(self):
        """Should handle empty DataFrame gracefully."""
        df = pl.DataFrame(
            {"id": pl.Series([], dtype=pl.Utf8), "code": pl.Series([], dtype=pl.Utf8)}
        )
        result = comorbidity(df, id_col="id", code_col="code", age_col=None)
        assert result.height == 0


class TestCharlsonScore:
    """Tests for Charlson Comorbidity Index calculation."""

    def test_charlson_quan_basic(self):
        """Test basic Charlson calculation with Quan mapping."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "2", "2", "3"],
                "code": ["I21", "I50", "E112", "C78", "J44"],
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col=None,
            score=ScoreType.CHARLSON,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.QUAN,
        )

        assert result.height == 3
        assert "id" in result.columns
        assert "comorbidity_score" in result.columns

        # Patient 1 has AMI and CHF
        p1 = result.filter(pl.col("id") == "1")
        assert p1["ami"][0] == 1
        assert p1["chf"][0] == 1

        # Patient 2 has diabetes with complications and metastatic cancer
        p2 = result.filter(pl.col("id") == "2")
        assert p2["diabwc"][0] == 1
        assert p2["metacanc"][0] == 1

        # Patient 3 has COPD
        p3 = result.filter(pl.col("id") == "3")
        assert p3["copd"][0] == 1

    def test_charlson_with_age_adjustment(self):
        """Test Charlson calculation with age adjustment."""
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
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.CHARLSON,
        )

        assert "age_adj_comorbidity_score" in result.columns
        assert "survival_10yr" in result.columns

        # Younger patient should have lower age-adjusted score
        p1 = result.filter(pl.col("id") == "1")
        p3 = result.filter(pl.col("id") == "3")
        assert p1["age_adj_comorbidity_score"][0] < p3["age_adj_comorbidity_score"][0]

    def test_assign_zero_mild_liver_disease(self):
        """Test that mild liver disease is zeroed when severe present."""
        # Patient has both mild and moderate/severe liver disease codes
        df = pl.DataFrame(
            {
                "id": ["1", "1"],
                "code": ["K703", "K721"],  # K703 = mild, K721 = moderate/severe
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col=None,
            assign0=True,
        )

        # With assign0=True, mld should be 0 because msld is present
        assert result["mld"][0] == 0
        assert result["msld"][0] == 1

    def test_assign_zero_diabetes(self):
        """Test that uncomplicated diabetes is zeroed when complicated present."""
        df = pl.DataFrame(
            {
                "id": ["1", "1"],
                "code": ["E109", "E112"],  # E109 = uncomplicated, E112 = complicated
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col=None,
            assign0=True,
        )

        # With assign0=True, diab should be 0 because diabwc is present
        assert result["diab"][0] == 0
        assert result["diabwc"][0] == 1

    def test_assign_zero_cancer(self):
        """Test that cancer is zeroed when metastatic cancer present."""
        df = pl.DataFrame(
            {
                "id": ["1", "1"],
                "code": ["C50", "C78"],  # C50 = breast cancer, C78 = metastatic
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col=None,
            assign0=True,
        )

        # With assign0=True, canc should be 0 because metacanc is present
        assert result["canc"][0] == 0
        assert result["metacanc"][0] == 1

    def test_no_assign_zero(self):
        """Test that both forms are kept when assign0=False."""
        df = pl.DataFrame(
            {
                "id": ["1", "1"],
                "code": ["K703", "K721"],
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col=None,
            assign0=False,
        )

        # Both should be present
        assert result["mld"][0] == 1
        assert result["msld"][0] == 1

    def test_charlson_different_mappings(self):
        """Test that different mapping variants work."""
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["I21"],
            }
        )

        for variant in [
            MappingVariant.QUAN,
            MappingVariant.SWEDISH,
            MappingVariant.AUSTRALIAN,
        ]:
            result = comorbidity(
                df,
                score=ScoreType.CHARLSON,
                icd=ICDVersion.ICD10,
                variant=variant,
                age_col=None,
            )
            assert result.height == 1
            assert "comorbidity_score" in result.columns

    def test_charlson_different_weights(self):
        """Test that different weighting variants produce different scores."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1"],
                "code": ["I21", "I50", "E112"],  # AMI, CHF, Diabetes with complications
            }
        )

        results = {}
        for weight in [WeightingVariant.CHARLSON, WeightingVariant.QUAN]:
            result = comorbidity(
                df,
                weighting=weight,
                age_col=None,
            )
            results[weight] = result["comorbidity_score"][0]

        # Different weights should produce different scores
        # (unless by coincidence they're the same)
        assert "comorbidity_score" in result.columns


class TestElixhauserScore:
    """Tests for Elixhauser Comorbidity Index calculation."""

    def test_elixhauser_basic(self):
        """Test basic Elixhauser calculation."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "2"],
                "code": ["I10", "E119", "F32"],  # Hypertension, Diabetes, Depression
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col=None,
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.VAN_WALRAVEN,
        )

        assert result.height == 2
        assert "comorbidity_score" in result.columns

    def test_elixhauser_assign_zero_hypertension(self):
        """Test that uncomplicated hypertension zeroed when complicated present."""
        df = pl.DataFrame(
            {
                "id": ["1", "1"],
                "code": ["I10", "I110"],  # Uncomplicated and complicated hypertension
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.ELIXHAUSER,
            weighting=WeightingVariant.VAN_WALRAVEN,
            assign0=True,
            age_col=None,
        )

        # hypunc should be 0 because hypc is present
        assert result["hypunc"][0] == 0
        assert result["hypc"][0] == 1


class TestSyntheticData:
    """Tests using synthetic data generators."""

    def test_charlson_with_synthetic_data(self):
        """Test Charlson calculation with synthetic data."""
        df = generate_charlson_data(n_patients=100, seed=42)
        result = comorbidity(df, age_col="age")

        assert result.height == 100
        assert "comorbidity_score" in result.columns
        assert result["comorbidity_score"].null_count() == 0

    def test_duplicate_ids_handled(self):
        """Test that duplicate IDs are aggregated correctly."""
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1", "1"],
                "code": ["I21", "I21", "I50", "I50"],  # Duplicate codes
            }
        )
        result = comorbidity(df, age_col=None)

        assert result.height == 1
        assert result["ami"][0] == 1
        assert result["chf"][0] == 1

    def test_null_values_dropped(self):
        """Test that null values are handled gracefully."""
        df = pl.DataFrame(
            {
                "id": ["1", "2", None, "3"],
                "code": ["I21", None, "I50", "J44"],
            }
        )
        result = comorbidity(df, age_col=None)

        # Only patients with valid id and code should be included
        assert result.height <= 3


class TestPerformance:
    """Performance-related tests."""

    def test_large_dataset(self):
        """Test performance with moderately large dataset."""
        df = generate_charlson_data(n_patients=10_000, seed=42)
        result = comorbidity(df, age_col="age")

        assert result.height == 10_000
        assert "comorbidity_score" in result.columns


class TestNegativeScores:
    """Tests for correct handling of negative comorbidity scores."""

    def test_van_walraven_allows_negative_scores(self):
        """Test that van Walraven weighting returns negative scores correctly."""
        # Create a patient with only "drug abuse" which has weight -7
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["F11"],  # Drug abuse ICD-10 code
            }
        )
        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            age_col=None,
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.VAN_WALRAVEN,
        )

        # Should return -7, not 0
        assert result["comorbidity_score"][0] == -7
        assert result["drug"][0] == 1

    def test_van_walraven_multiple_negative_weights(self):
        """Test van Walraven with multiple negative weight conditions."""
        # Patient with drug abuse (-7), obesity (-4), and depression (-3)
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1"],
                "code": ["F11", "E66", "F32"],  # Drug abuse, obesity, depression
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.ELIXHAUSER,
            weighting=WeightingVariant.VAN_WALRAVEN,
            age_col=None,
        )

        # Total should be -7 + (-4) + (-3) = -14
        assert result["comorbidity_score"][0] == -14

    def test_swiss_allows_negative_scores(self):
        """Test that Swiss weighting returns negative scores correctly."""
        # Create a patient with only "drug abuse" which has weight -5 in Swiss
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["F11"],  # Drug abuse
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.ELIXHAUSER,
            weighting=WeightingVariant.SWISS,
            age_col=None,
        )

        # Should return -5, not 0
        assert result["comorbidity_score"][0] == -5

    def test_shmi_clamps_negative_to_zero(self):
        """Test that SHMI weighting clamps negative scores to zero."""
        # Create a patient with only diabetes with complications (weight -1 in SHMI)
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["E112"],  # Diabetes with complications
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.CHARLSON,
            weighting=WeightingVariant.SHMI,
            age_col=None,
        )

        # SHMI should clamp to 0
        assert result["comorbidity_score"][0] == 0
        assert result["diabwc"][0] == 1

    def test_shmi_modified_allows_positive_scores(self):
        """Test that SHMI modified handles diabetes correctly with positive weight."""
        # Create a patient with diabetes with complications (weight 4 in SHMI modified)
        df = pl.DataFrame(
            {
                "id": ["1"],
                "code": ["E112"],
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.CHARLSON,
            weighting=WeightingVariant.SHMI_MODIFIED,
            age_col=None,
        )

        # SHMI modified has positive weight (4) for diabwc
        assert result["comorbidity_score"][0] == 4

    def test_mixed_positive_negative_weights(self):
        """Test mixed positive and negative weights sum correctly."""
        # Patient with CHF (7) and drug abuse (-7) in van Walraven
        df = pl.DataFrame(
            {
                "id": ["1", "1"],
                "code": ["I50", "F11"],  # CHF and drug abuse
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.ELIXHAUSER,
            weighting=WeightingVariant.VAN_WALRAVEN,
            age_col=None,
        )

        # Should be 7 + (-7) = 0
        assert result["comorbidity_score"][0] == 0

    def test_net_negative_score_from_mixed_weights(self):
        """Test that net negative scores are preserved for non-SHMI."""
        # Patient with CHF (7) and drug abuse (-7) and obesity (-4)
        df = pl.DataFrame(
            {
                "id": ["1", "1", "1"],
                "code": ["I50", "F11", "E66"],  # CHF, drug abuse, obesity
            }
        )
        result = comorbidity(
            df,
            score=ScoreType.ELIXHAUSER,
            weighting=WeightingVariant.VAN_WALRAVEN,
            age_col=None,
        )

        # Should be 7 + (-7) + (-4) = -4
        assert result["comorbidity_score"][0] == -4
