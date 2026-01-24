__version__ = "0.6.0"

# Import calculators for public API
from .calculators.comorbidity import (
    ICDVersion,
    MappingVariant,
    ScoreType,
    WeightingVariant,
    comorbidity,
)
from .calculators.hfrs import hfrs
from .calculators.learning_disability import disability

__all__ = [
    "__version__",
    # Main comorbidity calculator
    "comorbidity",
    # Specialized calculators
    "hfrs",
    "disability",
    # Enums for comorbidity function
    "ICDVersion",
    "ScoreType",
    "MappingVariant",
    "WeightingVariant",
]

