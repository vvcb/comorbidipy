#!/usr/bin/env python

"""Tests for `comorbidipy` package."""


import random
import unittest
from itertools import cycle

import pandas as pd

from comorbidipy import comorbidity, mapping

def generate_synthetic_icd10_data(
    score: str = "charlson",
    icd: str = "icd10",
    variant: str = "shmi",
    weighting: str = None,  # for compatibility
):

    mapping_key = f"{score}_{icd}_{variant}"
    patients = []

    num_of_patients = max(map(len, mapping.mapping[mapping_key].values()))
    codes = [cycle(random.sample(v, len(v))) for v in mapping.mapping[mapping_key].values()]

    for n in range(num_of_patients):

        age = random.randint(0, 100)

        for c in codes:

            patients.append({"id": n, "age": age, "code": next(c)})

    df = pd.DataFrame.from_records(patients)
    return df


class TestComorbidipy(unittest.TestCase):
    """Tests for `comorbidipy` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.test_args = [
            {
                "args": {
                    "icd": "icd10",
                    "score": "charlson",
                    "variant": "shmi",
                    "weighting": "shmi",
                },
                "max_ccs": 110,
            },
            {
                "args": {
                    "icd": "icd10",
                    "score": "charlson",
                    "variant": "quan",
                    "weighting": "charlson",
                },
                "max_ccs": 29,
            },
            {
                "args": {
                    "icd": "icd10",
                    "score": "charlson",
                    "variant": "quan",
                    "weighting": "quan",cd str
                },
                "max_ccs": 22,
            },
        ]
        self.number_of_runs = 20

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass


    def test_comorbidity_calculator(self):

        for x in self.test_args:

            kwargs = x["args"]
            max_ccs = x["max_ccs"]

            for i in range(self.number_of_runs):

                df = generate_synthetic_icd10_data(**kwargs)
                ccs = comorbidity(df, **kwargs)

                self.assertTrue(all(ccs["comorbidity_score"] == max_ccs))


if __name__ == "__main__":
    unittest.main()
