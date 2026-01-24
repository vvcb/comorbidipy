"""Comorbidipy: Calculate comorbidity scores and clinical risk scores."""

__version__ = "0.6.0"

from comorbidipy.calculators.comorbidity import (
    ICDVersion,
    MappingVariant,
    ScoreType,
    WeightingVariant,
    comorbidity,
)
from comorbidipy.calculators.hfrs import hfrs
from comorbidipy.calculators.learning_disability import disability

__all__ = [
    "comorbidity",
    "hfrs",
    "disability",
    "ICDVersion",
    "ScoreType",
    "MappingVariant",
    "WeightingVariant",
]
