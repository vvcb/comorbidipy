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
                
class TestSpecifics(unittest.TestCase):

    def test_combinations(self):

        """
        Create an example with a known value.
        
        B20 = 2
        E120 = 3
        E117 = -1
        N18 = 10

        The score of 3 from E120 (Diabetes) should be superseded by the -1 from Diabetes with Complications (E117).

        Result should be 11 (2-1+10)

        """

        df = pd.DataFrame({'id': [1,1,1,1], 
                           'age':[60,60,60,60],
                           'code': ['B20','E120','E117','N18']})

        ccs = comorbidity(df, icd="icd10", score="charlson", variant="shmi", weighting="shmi")

        score = ccs["comorbidity_score"][0]

        self.assertTrue(score == 11)

        """
        Create another example with a known value.
        
        K721, K767 = 18
        K74, K702 = 8
        J60 = 4
        C18 = 8

        The score of 8 from K74 and K702 (Mild Liver Disease) should be superseded by the 18 from Moderate or Severe Liver Disease (K721, K767).

        Result should be 30 (18+4+8)

        """

        df = pd.DataFrame({'id': [1,1,1,1,1,1], 
                    'age':[60,60,60,60,60,60],
                    'code': ['K721','K767','K74','K702','J60','C18']})

        ccs = comorbidity(df, icd="icd10", score="charlson", variant="shmi", weighting="shmi")

        score = ccs["comorbidity_score"][0]

        self.assertTrue(score == 30)

        """
        Create a final example with a known value.
        
        C25 = 8
        C79 = 14
        K27 = 9
        G820 = 1
        M32 = 4

        The score of 8 from C25 (Cancer) should be superseded by the 14 from metastatic solid tumour (C79).

        Result should be 28 (14+9+1+4)

        """

        df = pd.DataFrame({'id': [1,1,1,1,1], 
                    'age':[60,60,60,60,60],
                    'code': ['C25','C79','K27','G820','M32']})

        ccs = comorbidity(df, icd="icd10", score="charlson", variant="shmi", weighting="shmi")

        score = ccs["comorbidity_score"][0]

        self.assertTrue(score == 28)


if __name__ == "__main__":
    unittest.main()
