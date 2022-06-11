# Usage

comorbidiPy is simple to use.

## Charlson and Elixhauser scores

```python
import pandas as pd
from comorbidipy import comorbidity

df = pd.read_csv("../data/test_data.csv")
df.head()
```

Output:

```python
     code    id   age
0    M4809   0    56
1    Z530    0    56
2    E039    1    40
3    M4807   1    40
4    M4786   2    75
```

Then call the `comorbidity` function as below.

```python
df_out = comorbidity(df,  
                     id="id",
                     code="code",
                     age="age",
                     score="charlson",
                     icd="icd10",
                     variant="shmi",
                     weighting="shmi",
                     assign0=True)
df_out.head()
```

This should result in an output similar to below.

|  id |  age |  aids |  ami  |  canc |  ...  |  pvd  |  rend |rheumd |  comorbidity_score  |  age_adj_comorbidity_score|
|----:|-----:|------:|------:|------:|:-----:|------:|------:|------:|--------------------:|--------------------------:|
|  0  |  56  |  0.0  |  0.0  |  0.0  |  ...  |  0.0  |  0.0  |  0.0  |  15.0               |  16.0                     |
|  1  |  35  |  0.0  |  0.0  |  0.0  |  ...  |  0.0  |  0.0  |  0.0  |  0.0                |  0.0                      |
|  2  |  51  |  0.0  |  0.0  |  0.0  |  ...  |  0.0  |  0.0  |  0.0  |  0.0                |  1.0                      |
|  3  |  51  |  0.0  |  0.0  |  1.0  |  ...  |  0.0  |  0.0  |  0.0  |  14.0               |  15.0                     |
|  4  |  69  |  0.0  |  0.0  |  0.0  |  ...  |  0.0  |  0.0  |  0.0  |  18.0               |  20.0                     |

The parameters used to call `comorbidity` are returned in the `attrs` attribute of the returned Pandas DataFrame.

```python
df.attrs()

{'score': 'charlson',
 'icd': 'icd10',
 'variant': 'shmi',
 'weighting': 'shmi_modified',
 'assign0': True}
```

### Column Labels and Descriptions

The descriptions for the column names in the returned data frame can be obtained easily.

```python
from comorbidipy import get_colnames

get_colnames('charlson')

# returns the following
{'aids': 'AIDS or HIV',
 'ami': 'acute myocardial infarction',
 'canc': 'cancer any malignancy',
 'cevd': 'cerebrovascular disease',
 'chf': 'congestive heart failure',
 'copd': 'chronic obstructive pulmonary disease',
 'dementia': 'dementia',
 'diab': 'diabetes without complications',
 'diabwc': 'diabetes with complications',
 'hp': 'hemiplegia or paraplegia',
 'metacanc': 'metastatic solid tumour',
 'mld': 'mild liver disease',
 'msld': 'moderate or severe liver disease',
 'pud': 'peptic ulcer disease',
 'pvd': 'peripheral vascular disease',
 'rend': 'renal disease',
 'rheumd': 'rheumatoid disease'}

 get_colnames('elixhauser')

 # returns the following
 {'aids': ' AIDS/HIV',
 'alcohol': ' alcohol abuse',
 'blane': ' blood loss anaemia',
 'carit': ' cardiac arrhythmias',
 'chf': ' congestive heart failure',
 'coag': ' coagulopathy',
 'cpd': ' chronic pulmonary disease',
 'dane': ' deficiency anaemia',
 'depre': ' depression',
 'diabc': ' diabetes complicated',
 'diabunc': ' diabetes uncomplicated',
 'drug': ' drug abuse',
 'fed': ' fluid and electrolyte disorders',
 'hypc': ' hypertension complicated',
 'hypothy': ' hypothyroidism',
 'hypunc': ' hypertension uncomplicated',
 'ld': ' liver disease',
 'lymph': ' lymphoma',
 'metacanc': ' metastatic cancer',
 'obes': ' obesity',
 'ond': ' other neurological disorders',
 'para': ' paralysis',
 'pcd': ' pulmonary circulation disorders',
 'psycho': ' psychoses',
 'pud': ' peptic ulcer disease excluding bleeding',
 'pvd': ' peripheral vascular disorders',
 'rf': ' renal failure',
 'rheumd': ' rheumatoid arthritis/collaged vascular disease',
 'solidtum': ' solid tumour without metastasis',
 'valv': ' valvular disease',
 'wloss': ' weight loss'}
```
