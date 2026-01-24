"""Tests for ICD codes that map to multiple comorbidities."""

import polars as pl

from comorbidipy import (
    ICDVersion,
    MappingVariant,
    ScoreType,
    WeightingVariant,
    comorbidity,
)


class TestMultipleComorbidityMapping:
    """Tests for codes that map to multiple comorbidities.

    These tests verify that ICD codes which should map to multiple
    comorbidities are correctly handled. The issue was that dictionary-based
    reverse mapping only allowed one comorbidity per code.
    """

    def test_elixhauser_icd10_quan_i426_maps_to_chf_and_alcohol(self):
        """I426 (alcoholic cardiomyopathy) should map to both CHF and alcohol."""
        df = pl.DataFrame({"id": [1], "code": ["I426"]})

        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.SWISS,
        )

        # I426 should map to both CHF and alcohol
        assert result["chf"][0] == 1, "I426 should map to CHF"
        assert result["alcohol"][0] == 1, "I426 should map to alcohol"

    def test_elixhauser_icd10_quan_f315_maps_to_psycho_and_depre(self):
        """F315 should map to both psychosis and depression."""
        df = pl.DataFrame({"id": [1], "code": ["F315"]})

        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.SWISS,
        )

        # F315 should map to both psychosis and depression
        assert result["psycho"][0] == 1, "F315 should map to psychosis"
        assert result["depre"][0] == 1, "F315 should map to depression"

    def test_elixhauser_icd10_quan_i2782_maps_to_pcd_and_cpd(self):
        """I2782 should map to both PCD and CPD."""
        df = pl.DataFrame({"id": [1], "code": ["I2782"]})

        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.SWISS,
        )

        # I2782 should map to both PCD and CPD
        assert result["pcd"][0] == 1, "I2782 should map to PCD"
        assert result["cpd"][0] == 1, "I2782 should map to CPD"

    def test_original_issue_example(self):
        """Test the exact example from the GitHub issue.

        Reproduces the bug where codes mapping to multiple comorbidities
        only mapped to one.
        """
        df = pl.DataFrame({"id": [1, 1, 1], "code": ["I2782", "I426", "F315"]})

        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.SWISS,
        )

        # All six comorbidities should be present
        assert result["pcd"][0] == 1, "PCD should be 1"
        assert result["cpd"][0] == 1, "CPD should be 1"
        assert result["psycho"][0] == 1, "psycho should be 1"
        assert result["depre"][0] == 1, "depre should be 1"
        assert result["alcohol"][0] == 1, "alcohol should be 1"
        assert result["chf"][0] == 1, "CHF should be 1"

        # Check the score calculation
        # Swiss weights: alcohol=-3, chf=13, cpd=3, depre=-3, pcd=6, psycho=-4
        expected_score = -3 + 13 + 3 + (-3) + 6 + (-4)
        assert result["comorbidity_score"][0] == expected_score, (
            f"Score should be {expected_score}"
        )

    def test_charlson_icd9_quan_40403_maps_to_chf_and_rend(self):
        """ICD9 code 40403 should map to both CHF and renal disease."""
        df = pl.DataFrame({"id": [1], "code": ["40403"]})

        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            score=ScoreType.CHARLSON,
            icd=ICDVersion.ICD9,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.QUAN,
        )

        # 40403 should map to both CHF and renal disease
        assert result["chf"][0] == 1, "40403 should map to CHF"
        assert result["rend"][0] == 1, "40403 should map to renal disease"

    def test_elixhauser_icd9_quan_40403_maps_to_chf_and_rf(self):
        """ICD9 code 40403 in Elixhauser should map to CHF and renal failure."""
        df = pl.DataFrame({"id": [1], "code": ["40403"]})

        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD9,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.VAN_WALRAVEN,
        )

        # 40403 should map to both CHF and renal failure
        assert result["chf"][0] == 1, "40403 should map to CHF"
        assert result["rf"][0] == 1, "40403 should map to renal failure"

    def test_elixhauser_icd9_quan_4255_maps_to_chf_and_alcohol(self):
        """ICD9 code 4255 (alcoholic cardiomyopathy) maps to CHF and alcohol."""
        df = pl.DataFrame({"id": [1], "code": ["4255"]})

        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD9,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.VAN_WALRAVEN,
        )

        # 4255 should map to both CHF and alcohol
        assert result["chf"][0] == 1, "4255 should map to CHF"
        assert result["alcohol"][0] == 1, "4255 should map to alcohol"

    def test_multiple_patients_with_overlapping_codes(self):
        """Test multiple patients where some have codes mapping to multiple comorbidities."""  # noqa: E501
        df = pl.DataFrame(
            {
                "id": [1, 1, 2, 2, 3],
                "code": ["I426", "I50", "F315", "J44", "I21"],
            }
        )

        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.SWISS,
        )

        # Patient 1: I426 (CHF+alcohol) and I50 (CHF only) -> CHF=1, alcohol=1
        p1 = result.filter(pl.col("id") == 1)
        assert p1["chf"][0] == 1
        assert p1["alcohol"][0] == 1

        # Patient 2: F315 (psycho+depre) and J44 (CPD) -> psycho=1, depre=1, cpd=1
        p2 = result.filter(pl.col("id") == 2)
        assert p2["psycho"][0] == 1
        assert p2["depre"][0] == 1
        assert p2["cpd"][0] == 1

        # Patient 3: I21 (AMI only) -> no multiple mappings
        p3 = result.filter(pl.col("id") == 3)
        # AMI is not in Elixhauser, so no comorbidities should be flagged
        assert p3["comorbidity_score"][0] == 0

    def test_duplicate_codes_for_same_patient(self):
        """Test that duplicate codes don't double-count comorbidities."""
        df = pl.DataFrame(
            {
                "id": [1, 1, 1],
                "code": ["I426", "I426", "I426"],  # Same code three times
            }
        )

        result = comorbidity(
            df,
            id_col="id",
            code_col="code",
            score=ScoreType.ELIXHAUSER,
            icd=ICDVersion.ICD10,
            variant=MappingVariant.QUAN,
            weighting=WeightingVariant.SWISS,
        )

        # Even with three instances of I426, patient should have CHF=1 and alcohol=1
        # (not 3 for each)
        assert result["chf"][0] == 1
        assert result["alcohol"][0] == 1
