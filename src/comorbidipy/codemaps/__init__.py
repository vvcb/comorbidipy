"""ICD code mappings and weight definitions for comorbidity scores."""

from comorbidipy.codemaps.mapping import hfrs_mapping, impairments, mapping
from comorbidipy.codemaps.weights import weights

__all__ = [
    "mapping",
    "weights",
    "hfrs_mapping",
    "impairments",
]
