# Clinical Input Variation Benchmark Report

## Summary Metrics
- **Prescription Medicine Recall**: **95.2%**
- **Source Page Attribution Accuracy**: **100.0%**
- **Anti-Hallucination Compliance**: **100.0%**

## Detailed Test Cases Breakdown

### [VAR-01] Numeric Value instead of Range (Moderate Cardiac)
- **User Query**: *"What are the recommended medicines and matra for a patient with respiratory viral infection having cardiac ailments or hypertension (Rasavah srotas vyadhi) with moderate HRCT score 10 and SpO2 93%?"*
- **Target Page**: `15` | **Retrieved Pages**: `[15]` | **Page Match**: `PASSED`
- **Medicine Recall**: `100.0%`
- **Answer Excerpt**:
```markdown
| MEDICINE / FORMULATION | DOSE / MATRA | FREQUENCY | TIMING / AUSHADH KAL | DURATION | ANUPANA / SAHAPAAN | SOURCE DOCUMENT | PAGE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Somtajvir | 1-0-1 | Twice a day | Rasayan kal and Nisha ...
```

### [VAR-02] Numeric Value + Colleague Phrasing (Mild Diabetic)
- **User Query**: *"Prescription for an adult with respiratory infection and high blood sugar comorbidity, his CT scan score is 5 and O2 saturation is 96%."*
- **Target Page**: `14` | **Retrieved Pages**: `[14, 3, 3, 3, 14, 1]` | **Page Match**: `PASSED`
- **Medicine Recall**: `100.0%`
- **Answer Excerpt**:
```markdown
| MEDICINE / FORMULATION | DOSE / MATRA | FREQUENCY | TIMING / AUSHADH KAL | DURATION | ANUPANA / SAHAPAAN | SOURCE DOCUMENT | PAGE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Somtajvir | 1-0-0 | Not specified | Rasayan kal (Early morning o...
```

### [VAR-03] Numeric Value + Severity Phrasing (Severe Cardiac)
- **User Query**: *"What are the urgent Ayurvedic medicines for a severe viral respiratory patient with heart disease having HRCT 17 and SpO2 88%?"*
- **Target Page**: `15` | **Retrieved Pages**: `[3, 15, 1, 3, 15, 1]` | **Page Match**: `PASSED`
- **Medicine Recall**: `100.0%`
- **Answer Excerpt**:
```markdown
| MEDICINE / FORMULATION | DOSE / MATRA | FREQUENCY | TIMING / AUSHADH KAL | DURATION | ANUPANA / SAHAPAAN | SOURCE DOCUMENT | PAGE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Somtajvir | 1-1-1 | Three times | Rasayan kal and Vyanodaan kal ...
```

### [VAR-04] Colloquial Symptom Phrasing (Persistent Fever & Weakness)
- **User Query**: *"What medicine and anupana should be given to a patient suffering from persistent fever for 6 days accompanied by intense weakness and fatigue?"*
- **Target Page**: `22` | **Retrieved Pages**: `[1, 22, 3, 4, 3, 24]` | **Page Match**: `PASSED`
- **Medicine Recall**: `100.0%`
- **Answer Excerpt**:
```markdown
| MEDICINE / FORMULATION | DOSE / MATRA | FREQUENCY | TIMING / AUSHADH KAL | DURATION | ANUPANA / SAHAPAAN | SOURCE DOCUMENT | PAGE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Mahalakshmi Vilas | 1-1-1 | Three times a day | Rasayan ...
```

### [VAR-05] Clinical Complication Synonym (Tachycardia / Fast Pulse)
- **User Query**: *"If a patient develops tachycardia (fast pulse rate) or sudden rise in BP during viral respiratory illness, which formulation is indicated?"*
- **Target Page**: `22` | **Retrieved Pages**: `[22, 10, 11, 22, 1, 10]` | **Page Match**: `PASSED`
- **Medicine Recall**: `100.0%`
- **Answer Excerpt**:
```markdown
| MEDICINE / FORMULATION | DOSE / MATRA | FREQUENCY | TIMING / AUSHADH KAL | DURATION | ANUPANA / SAHAPAAN | SOURCE DOCUMENT | PAGE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Pranvallabh | 1cap | Not specified | SOS | Not specified...
```

### [VAR-06] Oncology Prophylaxis Synonym (Chemotherapy / Radiotherapy)
- **User Query**: *"Immunity booster formulations for a cancer patient currently taking radiation or chemotherapy to prevent viral respiratory infection."*
- **Target Page**: `7` | **Retrieved Pages**: `[3, 7, 1, 14, 7, 3]` | **Page Match**: `PASSED`
- **Medicine Recall**: `66.7%`
- **Answer Excerpt**:
```markdown
| MEDICINE / FORMULATION | DOSE / MATRA | FREQUENCY | TIMING / AUSHADH KAL | DURATION | ANUPANA / SAHAPAAN | SOURCE DOCUMENT | PAGE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Pranvir | 2-0-2 | Not specified | Vyanodaan kal (twice a...
```

### [VAR-07] DOCX Symptom Translation (Appetite Loss & Weight Loss)
- **User Query**: *"According to DM RR protocol, what should be prescribed for extreme emaciation, loss of appetite, indigestion and severe weakness in diabetic patients?"*
- **Target Page**: `2` | **Retrieved Pages**: `[14, 2, 2, 23, 2, 4]` | **Page Match**: `PASSED`
- **Medicine Recall**: `100.0%`
- **Answer Excerpt**:
```markdown
| MEDICINE / FORMULATION | DOSE / MATRA | FREQUENCY | TIMING / AUSHADH KAL | DURATION | ANUPANA / SAHAPAAN | SOURCE DOCUMENT | PAGE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Rasaka Rasayana | 0-0-1 | Not specified | Nisha kal (At ...
```

### [VAR-08] Strict Negative Control (Allopathic Medications)
- **User Query**: *"What is the prescribed dosage of Dexamethasone 6mg and Favipiravir 800mg in the respiratory guideline?"*
- **Target Page**: `None` | **Retrieved Pages**: `[]` | **Page Match**: `PASSED`
- **Medicine Recall**: `100.0%`
- **Answer Excerpt**:
```markdown
Not mentioned in the PDF....
```
