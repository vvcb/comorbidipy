"""Synthetic test data generators for comorbidipy tests."""

import random

import polars as pl

# Sample ICD-10 codes for each Charlson comorbidity
CHARLSON_ICD10_CODES: dict[str, list[str]] = {
    "ami": ["I21", "I210", "I211", "I219", "I22", "I220", "I252"],
    "chf": [
        "I099",
        "I110",
        "I130",
        "I132",
        "I255",
        "I420",
        "I425",
        "I426",
        "I427",
        "I428",
        "I429",
        "I43",
        "I50",
        "P290",
    ],
    "pvd": [
        "I70",
        "I700",
        "I701",
        "I702",
        "I71",
        "I731",
        "I738",
        "I739",
        "I771",
        "I790",
        "I792",
        "K551",
        "K558",
        "K559",
        "Z958",
        "Z959",
    ],
    "cevd": [
        "G45",
        "G450",
        "G451",
        "G452",
        "G46",
        "H340",
        "I60",
        "I61",
        "I62",
        "I63",
        "I64",
        "I65",
        "I66",
        "I67",
        "I68",
        "I69",
    ],
    "dementia": ["F00", "F01", "F02", "F03", "F051", "G30", "G310", "G311"],
    "copd": [
        "I278",
        "I279",
        "J40",
        "J41",
        "J42",
        "J43",
        "J44",
        "J45",
        "J46",
        "J47",
        "J60",
        "J61",
        "J62",
        "J63",
        "J64",
        "J65",
        "J66",
        "J67",
        "J684",
        "J701",
        "J703",
    ],
    "rheumd": ["M05", "M06", "M315", "M32", "M33", "M34", "M351", "M353", "M360"],
    "pud": ["K25", "K26", "K27", "K28"],
    "mld": [
        "B18",
        "K700",
        "K701",
        "K702",
        "K703",
        "K709",
        "K713",
        "K714",
        "K715",
        "K717",
        "K73",
        "K74",
        "K760",
        "K762",
        "K763",
        "K764",
        "K768",
        "K769",
        "Z944",
    ],
    "diab": [
        "E100",
        "E101",
        "E106",
        "E108",
        "E109",
        "E110",
        "E111",
        "E116",
        "E118",
        "E119",
        "E120",
        "E121",
        "E126",
        "E128",
        "E129",
        "E130",
        "E131",
        "E136",
        "E138",
        "E139",
        "E140",
        "E141",
        "E146",
        "E148",
        "E149",
    ],
    "diabwc": [
        "E102",
        "E103",
        "E104",
        "E105",
        "E107",
        "E112",
        "E113",
        "E114",
        "E115",
        "E117",
        "E122",
        "E123",
        "E124",
        "E125",
        "E127",
        "E132",
        "E133",
        "E134",
        "E135",
        "E137",
        "E142",
        "E143",
        "E144",
        "E145",
        "E147",
    ],
    "hp": [
        "G041",
        "G114",
        "G801",
        "G802",
        "G81",
        "G82",
        "G830",
        "G831",
        "G832",
        "G833",
        "G834",
        "G839",
    ],
    "rend": [
        "I120",
        "I131",
        "N032",
        "N033",
        "N034",
        "N035",
        "N036",
        "N037",
        "N052",
        "N053",
        "N054",
        "N055",
        "N056",
        "N057",
        "N18",
        "N19",
        "N250",
        "Z490",
        "Z491",
        "Z492",
        "Z940",
        "Z992",
    ],
    "canc": [
        "C00",
        "C01",
        "C02",
        "C03",
        "C04",
        "C05",
        "C06",
        "C07",
        "C08",
        "C09",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21",
        "C22",
        "C23",
        "C24",
        "C25",
        "C26",
        "C30",
        "C31",
        "C32",
        "C33",
        "C34",
        "C37",
        "C38",
        "C39",
        "C40",
        "C41",
        "C43",
        "C45",
        "C46",
        "C47",
        "C48",
        "C49",
        "C50",
        "C51",
        "C52",
        "C53",
        "C54",
        "C55",
        "C56",
        "C57",
        "C58",
        "C60",
        "C61",
        "C62",
        "C63",
        "C64",
        "C65",
        "C66",
        "C67",
        "C68",
        "C69",
        "C70",
        "C71",
        "C72",
        "C73",
        "C74",
        "C75",
        "C76",
        "C81",
        "C82",
        "C83",
        "C84",
        "C85",
        "C88",
        "C90",
        "C91",
        "C92",
        "C93",
        "C94",
        "C95",
        "C96",
        "C97",
    ],
    "msld": [
        "I850",
        "I859",
        "I864",
        "I982",
        "K704",
        "K711",
        "K721",
        "K729",
        "K765",
        "K766",
        "K767",
    ],
    "metacanc": ["C77", "C78", "C79", "C80"],
    "aids": ["B20", "B21", "B22", "B24"],
}

# Sample ICD-10 codes for HFRS
HFRS_ICD10_CODES: list[str] = [
    "F00",
    "F01",
    "F02",
    "F03",
    "F05",
    "G30",
    "G31",
    "G81",
    "G82",
    "I63",
    "I69",
    "J69",
    "J96",
    "K59",
    "K92",
    "L89",
    "N17",
    "N18",
    "N19",
    "N39",
    "R26",
    "R29",
    "R31",
    "R32",
    "R39",
    "R40",
    "R41",
    "R44",
    "R45",
    "R54",
    "S00",
    "S01",
    "S06",
    "S09",
    "S22",
    "S32",
    "S42",
    "S52",
    "S72",
    "W00",
    "W01",
    "W06",
    "W10",
    "W18",
    "W19",
    "X59",
    "Y30",
    "Z22",
    "Z50",
    "Z74",
    "Z75",
    "Z87",
    "Z91",
    "Z93",
    "Z99",
]

# Sample ICD-10 codes for disabilities and impairments
IMPAIRMENT_ICD10_CODES: dict[str, list[str]] = {
    "ld_asd": ["F70", "F71", "F72", "F73", "F78", "F79"],
    "impaired_vision": [
        "H54",
        "H540",
        "H541",
        "H542",
        "H543",
        "H544",
        "H545",
        "H546",
        "H547",
    ],
    "impaired_hearing": [
        "H90",
        "H900",
        "H903",
        "H906",
        "H91",
        "H910",
        "H911",
        "H912",
        "H913",
        "H918",
        "H919",
    ],
    "frail": ["R54", "R53"],
}


def generate_patient_ids(n: int, prefix: str = "P") -> list[str]:
    """Generate unique patient IDs.

    Args:
        n: Number of patient IDs to generate.
        prefix: Prefix for patient IDs.

    Returns:
        List of unique patient ID strings.
    """
    return [f"{prefix}{i:06d}" for i in range(1, n + 1)]


def generate_charlson_data(
    n_patients: int = 1000,
    codes_per_patient: tuple[int, int] = (1, 10),
    comorbidity_prevalence: float = 0.3,
    seed: int | None = None,
) -> pl.DataFrame:
    """Generate synthetic data for Charlson comorbidity testing.

    Args:
        n_patients: Number of unique patients.
        codes_per_patient: Range of (min, max) codes per patient.
        comorbidity_prevalence: Probability that a code is a comorbidity code.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with 'id', 'code', and 'age' columns.
    """
    if seed is not None:
        random.seed(seed)

    patient_ids = generate_patient_ids(n_patients)
    all_comorbidity_codes = [
        code for codes in CHARLSON_ICD10_CODES.values() for code in codes
    ]

    records = []
    for patient_id in patient_ids:
        n_codes = random.randint(*codes_per_patient)
        age = random.randint(18, 95)

        for _ in range(n_codes):
            if random.random() < comorbidity_prevalence:
                # Pick a comorbidity code
                code = random.choice(all_comorbidity_codes)
            else:
                # Generate a random non-comorbidity ICD-10 code
                letter = random.choice("ABCDEFGHJKLMNOPQRSTUVWXYZ")
                num = random.randint(0, 99)
                code = f"{letter}{num:02d}"

            records.append({"id": patient_id, "code": code, "age": age})

    return pl.DataFrame(records)


def generate_hfrs_data(
    n_patients: int = 1000,
    codes_per_patient: tuple[int, int] = (1, 20),
    frailty_prevalence: float = 0.2,
    seed: int | None = None,
) -> pl.DataFrame:
    """Generate synthetic data for HFRS testing.

    Args:
        n_patients: Number of unique patients.
        codes_per_patient: Range of (min, max) codes per patient.
        frailty_prevalence: Probability that a code is a frailty-related code.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with 'id' and 'code' columns.
    """
    if seed is not None:
        random.seed(seed)

    patient_ids = generate_patient_ids(n_patients)

    records = []
    for patient_id in patient_ids:
        n_codes = random.randint(*codes_per_patient)

        for _ in range(n_codes):
            if random.random() < frailty_prevalence:
                code = random.choice(HFRS_ICD10_CODES)
            else:
                letter = random.choice("ABCDEFGHJKLMNOPQRSTUVWXYZ")
                num = random.randint(0, 99)
                code = f"{letter}{num:02d}"

            records.append({"id": patient_id, "code": code})

    return pl.DataFrame(records)


def generate_disability_data(
    n_patients: int = 1000,
    codes_per_patient: tuple[int, int] = (1, 5),
    disability_prevalence: float = 0.1,
    seed: int | None = None,
) -> pl.DataFrame:
    """Generate synthetic data for disability testing.

    Args:
        n_patients: Number of unique patients.
        codes_per_patient: Range of (min, max) codes per patient.
        disability_prevalence: Probability that a code is a disability code.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with 'id' and 'code' columns.
    """
    if seed is not None:
        random.seed(seed)

    patient_ids = generate_patient_ids(n_patients)
    all_disability_codes = [
        code for codes in IMPAIRMENT_ICD10_CODES.values() for code in codes
    ]

    records = []
    for patient_id in patient_ids:
        n_codes = random.randint(*codes_per_patient)

        for _ in range(n_codes):
            if random.random() < disability_prevalence:
                code = random.choice(all_disability_codes)
            else:
                letter = random.choice("ABCDEFGHJKLMNOPQRSTUVWXYZ")
                num = random.randint(0, 99)
                code = f"{letter}{num:02d}"

            records.append({"id": patient_id, "code": code})

    return pl.DataFrame(records)


def generate_large_dataset(
    n_patients: int = 100_000,
    codes_per_patient: tuple[int, int] = (5, 50),
    seed: int | None = 42,
) -> pl.DataFrame:
    """Generate a large dataset for performance testing.

    Args:
        n_patients: Number of unique patients.
        codes_per_patient: Range of codes per patient.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with 'id', 'code', and 'age' columns.
    """
    if seed is not None:
        random.seed(seed)

    all_codes = (
        [code for codes in CHARLSON_ICD10_CODES.values() for code in codes]
        + HFRS_ICD10_CODES
        + [code for codes in IMPAIRMENT_ICD10_CODES.values() for code in codes]
    )

    # Add random codes too
    random_codes = [
        f"{random.choice('ABCDEFGHJKLMNOPQRSTUVWXYZ')}{random.randint(0, 99):02d}"
        for _ in range(500)
    ]
    all_codes.extend(random_codes)

    patient_ids = generate_patient_ids(n_patients)

    records = []
    for patient_id in patient_ids:
        n_codes = random.randint(*codes_per_patient)
        age = random.randint(18, 95)

        for _ in range(n_codes):
            code = random.choice(all_codes)
            records.append({"id": patient_id, "code": code, "age": age})

    return pl.DataFrame(records)


# Known test cases with expected outputs
KNOWN_CHARLSON_CASES = [
    {
        "input": pl.DataFrame(
            {
                "id": ["1", "1", "1", "2", "2"],
                "code": ["I21", "E112", "C78", "I50", "J44"],
                "age": [65, 65, 65, 45, 45],
            }
        ),
        "expected_comorbidities": {
            "1": {"ami": 1, "diabwc": 1, "metacanc": 1},
            "2": {"chf": 1, "copd": 1},
        },
    },
]

KNOWN_HFRS_CASES = [
    {
        "input": pl.DataFrame(
            {
                "id": ["1", "1", "2"],
                "code": ["F00", "G81", "R54"],
            }
        ),
        # HFRS scores based on Gilbert et al. mapping
    },
]
