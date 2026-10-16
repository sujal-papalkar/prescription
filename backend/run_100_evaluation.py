"""
Comprehensive 100-Question Automated Clinical RAG Evaluation Pipeline
Covers:
- Table-based answers (exact tabular prescriptions, matra, sahpaan, aushadh kal)
- Exact clinical dosage (matra: 1-0-0, 2-0-2, 2-2-2, 1-0-1, 1-1-1, 1/2-0-0, 1 cap, 2 drops, etc.)
- Severity tiers (Mild, Moderate, Severe; HRCT 0-8 / 9-15 / >15; SpO2 >94 / 90-94 / <90; GFR stages 1-5)
- Comorbidities (Diabetes, Cardiac/HTN/CABG, Hepatic, GI, Renal, Psychiatric, Cancer, Pregnancy, Lactation)
- Cross-Document Retrieval (Synthesizing Respiratory PDF and Diabetes DOCX)
- Verified page number auditing against source documents
- 5 Core Metrics: Retrieval Accuracy, Answer Correctness, Completeness, Faithfulness, Document Relevance
"""

import os
import sys
import json
import time
import re
from typing import List, Dict, Any

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from core.database import HybridSearchEngine
from core.pipeline import ClinicalRAGPipeline

RESP_DOC = "Respiratory_Viral_Infection_Management_prorocol_FINAL_version_converted_1_25_Respiratory Viral Infection Management prorocol_FINAL version-converted-1-25.pdf"
DM_DOC = "DM_RR_DM RR.docx"

QUESTIONS_100 = [
    # =========================================================================
    # PART 1: RESPIRATORY VIRAL INFECTION MANAGEMENT PROTOCOL (45 QUESTIONS: R01 - R45)
    # =========================================================================
    # --- Category: Prophylaxis by Age Bracket (Page 6) ---
    {
        "id": "R01",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What is the prophylactic Rasayana regimen for patients older than 60 years with respiratory comorbidities (Pranvah Srotas Vyadhi) according to the guidelines?",
        "expected_pages": [6],
        "verified_target": "Page 6: Age >60 yrs (Respiratory Co-morbidities): Rasvir 1-0-0 (Honey/Warm Water, Rasayan kal - Early morning on empty stomach), Pranvir 2-0-2 (Warm water, Vyanodaan kal - twice a day after food), Rasaka Rasayana 1-0-1 (Honey/Warm Water, Rasayan kal and Nisha kal - Early morning on empty stomach and at bedtime). Duration: 90 days."
    },
    {
        "id": "R02",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic medicines and dosages are prescribed for adults aged 16 to 59 years with Pranvah Srotas comorbidities?",
        "expected_pages": [6],
        "verified_target": "Page 6: Age 16-59 yrs: Rasvir 1-0-0 (Honey/Warm Water, Rasayan kal), Pranvir 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 1-0-1 (Honey/Warm Water, Rasayan kal and Nisha kal). Duration: 90 days."
    },
    {
        "id": "R03",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "For children aged 3 to 15 years with respiratory comorbidities, what prophylactic formulations, doses, and timing are recommended?",
        "expected_pages": [6],
        "verified_target": "Page 6: Age 3-15 yrs: Rasvir 1-0-0 (Honey/Warm Water, Rasayan kal), Pranvir 1-1-1 (Warm water, Three times a day, after food), Rasaka Rasayana 0-0-1 (Honey/Warm Water, Nisha kal - at bedtime)."
    },
    {
        "id": "R04",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What is the prophylactic prescription for young children aged 1 to 3 years with respiratory comorbidities?",
        "expected_pages": [6],
        "verified_target": "Page 6: Age 1-3 yrs: Rasvir 1/2-0-0 (Honey/Warm Water, Rasayan kal), Rasaka Rasayana 0-0-1 (Honey/Warm Water, Nisha kal), Respin (200 mg) 1-0-1 (Warm water, Vyanodaan kal)."
    },
    {
        "id": "R05",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic regimen is recommended for infants below 1 year of age with respiratory comorbidities?",
        "expected_pages": [6],
        "verified_target": "Page 6: Below 1 yr: Rasvir 1/2-0-0 (Honey/Warm Water, Rasayan kal), Respin (100 mg) 1-0-1 (Warm Water, Vyanodaan kal), Yashada 1-0-1 (Honey/Warm Water, Nisha kal), SBP (Suvarn Bindu Prashan) Rasayana weekly once."
    },
    {
        "id": "R06",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What is the administration schedule for Suvarn Bindu Prashan (SBP) Rasayana in pediatric prophylaxis during an outbreak?",
        "expected_pages": [6, 7],
        "verified_target": "Page 6 & 7: SBP (Suvarn Bindu Prashan) Rasayana: Weekly once till pandemic/outbreak is ongoing, later as per SBP dates."
    },
    # --- Category: General & Cancer Prophylaxis (Page 7) ---
    {
        "id": "R07",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic protocol is specified for general adults (15+ years) without known comorbidities?",
        "expected_pages": [7],
        "verified_target": "Page 7: General Patients 15+ Yrs without known comorbidities: Pranvir 2-0-2 (Warm water, Vyanodaan kal - twice a day after food), Rasaka Rasayana 1-0-0 (Honey/Warm Water, Rasayan kal - Early morning on empty stomach). Duration: 90 days."
    },
    {
        "id": "R08",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic medicines are recommended for general children aged 3 to 15 years without known comorbidities?",
        "expected_pages": [7],
        "verified_target": "Page 7: General Patients 3-15 yrs: Pranvir 1-0-1 (Warm water, Vyanodaan kal), Rasaka Rasayana 0-0-1 (Honey/Warm Water, Nisha kal at bedtime)."
    },
    {
        "id": "R09",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic regimen applies to general toddlers aged 1 to 3 years without known comorbidities?",
        "expected_pages": [7],
        "verified_target": "Page 7: 1 to 3 age group: Rasvir 1/2-0-1/2 (Honey/Warm Water, Rasayan kal and Nisha kal), Respin (200 mg) 1-0-1 (Warm water, Vyanodaan kal), Yashada 0-0-1 (Honey/Warm Water, Nisha kal)."
    },
    {
        "id": "R10",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic guidelines are given for general infants below 1 year without comorbidities?",
        "expected_pages": [7],
        "verified_target": "Page 7: Below 1 yr: Rasvir 1/2-0-0 (Honey/Warm Water, Rasayan kal), Respin (100 mg) 1-0-1 (Warm water, Vyanodaan kal), Yashada 0-0-1 (Honey/Warm Water, Nisha kal), SBP Rasayana weekly till outbreak situation."
    },
    {
        "id": "R11",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic guidelines are specified for cancer patients who are on chemotherapy, radiotherapy, immunotherapy, or corticosteroid therapy?",
        "expected_pages": [7],
        "verified_target": "Page 7: Cancer Patients on Chemo/Radiotherapy/Immunocompromised: Rasvir 1-0-1 (Honey/Warm Water, Rasayan kal and Nisha kal), Pranvir 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 0-0-1 (Honey/Warm Water, Nisha kal), Heeraka Rasayana 1-0-0 (Honey/Warm Water, Rasayan kal), Mahalakshmi Vilas Ras 0-0-1 (Honey/Warm Water, Nisha kal)."
    },
    # --- Category: Comorbidity-Specific Rasayana Prophylaxis (Page 8-9) ---
    {
        "id": "R12",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic Rasayana protocol is recommended for chronic diabetic patients (Udakvah Srotas Vyadhi) to prevent respiratory viral infections?",
        "expected_pages": [8],
        "verified_target": "Page 8: Udakvah Srotas Vyadhi (Chronic Diabetic Patients): Rasvir 1-0-0 (Honey/warm water, Rasayan kal), Pranvir 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 0-0-1 (Honey/warm water, Nisha kal), Meha 1-0-0 (Honey/warm water, Rasayan kal)."
    },
    {
        "id": "R13",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "For cardiac patients (Rasvah Srotas Vyadhi) with hypertension (rasabhinodanvruddhi), which specific prophylactic medicines are added?",
        "expected_pages": [8],
        "verified_target": "Page 8: Rasvah Srotas Vyadhi: Rasvir 1-0-0, Pranvir 2-0-2, Rasaka Rasayana 0-0-1. If rasabhinodanvruddhi (HTN): add Sutendra Rasayana 1-0-0 (Honey/warm water, Rasayan kal)."
    },
    {
        "id": "R14",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "For cardiac patients with known Hrudrog, IHD, or prior CABG/angioplasty, which formulations are recommended in the prophylaxis guidelines?",
        "expected_pages": [8],
        "verified_target": "Page 8: If known case of Hrudrog/Hrudayshastrakriya (IHD/Angioplasty/CABG): Arpisa Rasayan 1-0-0 (Honey/warm water, Rasayan kal) and Heeraka 1-0-0 (Honey/warm water, Rasayan kal)."
    },
    {
        "id": "R15",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What is the prophylactic Rasayana regimen for patients with hepatic insufficiency (Raktavah Srotas Vyadhi)?",
        "expected_pages": [8],
        "verified_target": "Page 8: Raktavah Srotas Vyadhi (Hepatic insufficiency): Rasvir 1-0-0, Pranvir 2-0-2, Rasaka Rasayana 1-0-0 (Rasayan kal), Sutendra Rasayan 0-0-1 (Honey/warm water, Nisha kal)."
    },
    {
        "id": "R16",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic medicines are prescribed for patients with chronic gastrointestinal illnesses (Annavah Srotas Vyadhi)?",
        "expected_pages": [8],
        "verified_target": "Page 8: Annavah srotas Vyadhi (Chronic Gastrointestinal illnesses): Pranvir 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 1-0-0 (Honey/warm water, Rasayan kal), Sutendra 1-0-0 (Honey/warm water, Rasayan kal)."
    },
    {
        "id": "R17",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic medicines are recommended for patients with renal and urinary disorders including chronic renal failure (Mootravah Srotas Vyadhi)?",
        "expected_pages": [8, 9],
        "verified_target": "Page 8-9: Mootravah srotas Vyadhi (Renal and Urinary disorders including Chronic Renal Failure): Pranvir 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 1-0-0 (Honey/warm water, Rasayan kal), Heerak Rasayan 1-0-0 (Honey/warm water, Rasayan kal)."
    },
    {
        "id": "R18",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What prophylactic regimen is outlined for patients with concomitant psychiatric illnesses (Manovah Srotas Vyadhi)?",
        "expected_pages": [9],
        "verified_target": "Page 9: Manovah Srotas Vyadhi (Concomitant Psychiatric illness): Pranvir 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 1-0-0 (Honey/warm water, Rasayan kal), Pravi Rasayana 1-0-0 (Honey/warm water, Rasayan kal)."
    },
    # --- Category: Nitya Rasayan Sevan Prophylaxis (Page 10-11) ---
    {
        "id": "R19",
        "category": "Prophylaxis",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "For patients with mild asthma or COPD on occasional seasonal inhalers, what Nitya Rasayan formulation and vehicle are indicated?",
        "expected_pages": [10],
        "verified_target": "Page 10: Mild Pranvah srotas Vyadhi (Asthma / COPD on occasional/seasonal inhalers): Mahalaxmi Vilas 1-0-0, Sahpaan: Honey or Honey + ardrak rasa 2ml, Aushadh kal: Rasayan kal (Early morning on empty stomach)."
    },
    {
        "id": "R20",
        "category": "Dosage",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "For asthma or COPD patients dependent on regular inhalers, what Nitya Rasayan medicine is prescribed?",
        "expected_pages": [10],
        "verified_target": "Page 10: Pranvah srotas Vyadhi (If on regular inhalers): Pranvallabh Rasayan 1-0-0, Sahpaan: Honey/warm water, Timing: Rasayan kal (Early morning on empty stomach)."
    },
    {
        "id": "R21",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "Which Nitya Rasayan formulation is recommended for patients with a past history of malignancy?",
        "expected_pages": [10],
        "verified_target": "Page 10: Granthi / Arbud (Malignancies) - Past history of malignancy: Sinurbhushan Rasayan 1-0-0 (Honey/warm water, Rasayan kal)."
    },
    {
        "id": "R22",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "Which Nitya Rasayan formulation is advised for patients with active malignancy currently under treatment?",
        "expected_pages": [10],
        "verified_target": "Page 10: Malignancies - Active / under Treatment: Arpisa Rasayan 1-0-0 (Honey/warm water, Rasayan kal)."
    },
    {
        "id": "R23",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "For severe cardiac patients who have undergone PTCA or CABG, what Nitya Rasayan is recommended?",
        "expected_pages": [10, 11],
        "verified_target": "Page 10-11: Severe Rasavah srotas vyadhi (Post PTCA / CABG): Pranvallabh Rasayan 1-0-0 (Honey/warm water, Rasayan kal - early morning on empty stomach)."
    },
    {
        "id": "R24",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What Nitya Rasayan formulation is recommended for patients with chronic uncontrolled diabetes (Prameh)?",
        "expected_pages": [11],
        "verified_target": "Page 11: Patients with Prameh (Chronic uncontrolled Diabetes): Meha Rasayana 1-0-0 (Honey/warm water, Rasayan kal - Early morning on empty stomach)."
    },
    {
        "id": "R25",
        "category": "Table-Based",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What Nitya Rasayan formulation and vehicle are indicated during pregnancy?",
        "expected_pages": [11],
        "verified_target": "Page 11: Pregnancy: Heerak Rasayana 1-0-0, Sahpaan: Honey, Timing: Rasayan kal (Early morning on empty stomach)."
    },
    {
        "id": "R26",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What Nitya Rasayan formulation is specified for immunocompromised patients with HIV?",
        "expected_pages": [11],
        "verified_target": "Page 11: Immunocompromised patients e.g., HIV: Arpisa Rasayan 1-0-0, Sahpaan: Honey, Timing: Rasayan kal (Early morning on empty stomach)."
    },
    {
        "id": "R27",
        "category": "Table-Based",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "For independent rare cases of renal insufficiency (Mootravah Srotas), what Nitya Rasayan medicine is listed?",
        "expected_pages": [11],
        "verified_target": "Page 11: Mootravah srotas Vyadhi (Renal insufficiency) - Independent - Rare: Somakalpa 1-0-0, Sahpaan: Honey, Timing: Rasayan kal (Early morning on empty stomach)."
    },
    {
        "id": "R28",
        "category": "Table-Based",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What Nitya Rasayan medicine and vehicle are designated for patients with liver or blood disorders (Raktavah Srotas)?",
        "expected_pages": [11],
        "verified_target": "Page 11: Raktavah Srotas vyadhi (Liver/blood disorder): Dasma Rasayana 1-0-0, Sahpaan: Lemon Juice, Timing: Rasayan kal (Early morning on empty stomach)."
    },
    # --- Category: Therapeutic Guidelines & Severity Stratification (Page 13-21) ---
    {
        "id": "R29",
        "category": "Table-Based",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What are the basic therapeutic guidelines to reduce disease severity in infected patients above 15 years?",
        "expected_pages": [13],
        "verified_target": "Page 13: Above 15 yr: Somtajvir 1-0-0 (Honey/warm water, Rasayan kal), Pranvir 2-2-2 (Warm water, Three times a day after food), Rasaka Rasayana 1-0-1 compulsory (Honey/warm water, Rasayan kal and Nisha kal). Duration: usually 15 days."
    },
    {
        "id": "R30",
        "category": "Table-Based",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What are the basic therapeutic guidelines for children aged 3 to 15 years with acute respiratory infection?",
        "expected_pages": [13],
        "verified_target": "Page 13: 3-15 yrs: Pranvir 1-1-1 (Warm water, Three times a day after food), Rasaka Rasayana 1-0-1 (Honey/warm water, Rasayan kal and Nisha kal), Mahalakshmi Vilas Ras 1-0-1 (Honey/warm water, Rasayan kal and Nisha kal), Bal Rasayana 1-0-0 (Honey/warm water, Rasayan kal)."
    },
    {
        "id": "R31",
        "category": "Table-Based",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What therapeutic medicines and doses are recommended for lactating women with respiratory viral infection?",
        "expected_pages": [13],
        "verified_target": "Page 13: Lactating women: Somtajvir 1-0-1 (Honey/warm water, Rasayan kal and Nisha kal), Pranvir 2-2-2 (Warm water, Three times a day after food), Rasaka Rasayana 1-0-1 (Honey/warm water, Rasayan kal and Nisha kal)."
    },
    {
        "id": "R32",
        "category": "Severity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "A diabetic patient has respiratory viral infection with HRCT score 6 and SpO2 96% (Mild Tier). What exact therapeutic table applies?",
        "expected_pages": [14],
        "verified_target": "Page 14: Udakvah srotas vyadhi (Diabetes Mellitus) - MILD (0 to 8, SpO2 >94): Somtajvir 1-0-0 (Honey/Warm water, Rasayan kal), Pranvir 2-2-2 (Warm water, Three times a day after food), Rasaka Rasayana 1-0-1 (Honey/Warm water, Rasayan kal and Nisha kal), Meha Rasayan 1-0-0 (Honey/Warm water, Rasayan kal)."
    },
    {
        "id": "R33",
        "category": "Severity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "A diabetic patient has respiratory viral infection with HRCT score 12 and SpO2 92% (Moderate Tier). What is the prescribed regimen?",
        "expected_pages": [14],
        "verified_target": "Page 14: Udakvah srotas vyadhi (Diabetes Mellitus) - MODERATE (9 to 15, SpO2 90 to 94): Somtajvir 1-0-1 (Honey/Warm water, Rasayan kal and Nisha kal), Pranvir 2-2-2 (Warm water, Three times a day after food), Rasaka Rasayana 1-0-1 (Honey/Warm water, Rasayan kal and Nisha kal), Meha Rasayan 1-0-0 (Honey/Warm water, Rasayan kal)."
    },
    {
        "id": "R34",
        "category": "Severity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "A diabetic patient has severe respiratory infection with HRCT score 18 and SpO2 87%. Which additional formulation is added in the severe tier?",
        "expected_pages": [14],
        "verified_target": "Page 14: Udakvah srotas vyadhi - SEVERE (>15, SpO2 below 90): Somtajvir 1-1-1 (Rasayan kal and Vyanodaan kal), Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Meha Rasayan 1-0-0, Pranvallabha Rasayan 1-0-0 (Honey/Warm water, Rasayan kal)."
    },
    {
        "id": "R35",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What therapeutic formulations are prescribed for a cardiac patient with moderate respiratory viral infection (HRCT 9-15, SpO2 90-94%)?",
        "expected_pages": [15],
        "verified_target": "Page 15: Rasavah srotas vyadhi (Heart Diseases, HTN) - MODERATE (9 to 15, SpO2 90 to 94): Somtajvir 1-0-1, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Sutendra Rasayana 0-0-1 (Nisha kal), Arpisa Rasayan 1-0-0 (Rasayan kal), Heeraka Rasayana 1-0-0 (Rasayan kal)."
    },
    {
        "id": "R36",
        "category": "Severity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What is the therapeutic protocol for a pediatric patient (below 15 years) with moderate respiratory viral infection (HRCT 11, SpO2 92%)?",
        "expected_pages": [16],
        "verified_target": "Page 16: Pranvah Srotas vyadhi (Below 15 Years) - MODERATE (9 to 15, SpO2 90 to 94): Somtajvir 1-0-1, Pranvir 1-1-1, Rasaka Rasayana 1-0-1, Bal Rasayan 1-0-1, Mahalakshmi Vilas 0-0-1, Sindurbhushan Rasayan 1/2-0-1/2."
    },
    {
        "id": "R37",
        "category": "Severity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What is the therapeutic regimen for an adult above 15 years with severe respiratory viral infection (HRCT >15, SpO2 <90%) without other comorbidities?",
        "expected_pages": [17],
        "verified_target": "Page 17: Pranvah Srotas vyadhi (Above 15 Years) - SEVERE (>15, SpO2 <90): Somtajvir 1-1-1 (Rasayan kal & Vyanodaan kal), Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Sindhurbhushan Rasayan 1-0-0, Mahalakshmi Vilas 0-0-1, Pranvallabha Rasayan 1-0-0."
    },
    {
        "id": "R38",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What therapeutic regimen applies to a patient with renal disease (Mootravah Srotas) and moderate respiratory infection (HRCT 9-15, SpO2 90-94%)?",
        "expected_pages": [20],
        "verified_target": "Page 20: Mootravah Srotas vyadhi (Chronic/Acute renal failure) - MODERATE (9 to 15, SpO2 90 to 94): Somtajvir 1-0-1, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Heeraka Rasayana 1-0-0, Somkalpa 1-0-0, Mahalakshmi Vilas 0-0-1."
    },
    {
        "id": "R39",
        "category": "Comorbidity",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What is the recommended prescription for a patient with psychiatric illness (Manovah Srotas) and severe respiratory viral infection (HRCT >15, SpO2 <90%)?",
        "expected_pages": [21],
        "verified_target": "Page 21: Manovah Srotas vyadhi - SEVERE (>15, SpO2 <90): Somtajvir 1-1-1, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Mahalakshmi Vilas 0-0-1, Pravi Rasayana 1-1-1, Pranvallabha Rasayan 1-0-0."
    },
    # --- Category: Specific Symptom & Complication Management (Page 22-23) ---
    {
        "id": "R40",
        "category": "Symptom-Management",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What medicine, dosage, and vehicle are specified for persistent fever lasting more than 5 days (Santat Jwar) and weakness?",
        "expected_pages": [22],
        "verified_target": "Page 22: Santat Jwar (Persistent fever or more than 5 days) and weakness: Mahalakshmi Vilas 1-1-1, Sahpaan: Honey + Ginger juice, Timing: Rasayan kal and Vyanodaan kal (Early morning on empty stomach and after lunch and dinner)."
    },
    {
        "id": "R41",
        "category": "Symptom-Management",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What formulation, dose, and frequency are indicated for acute skin rash (Shitapitta) occurring during respiratory viral infection?",
        "expected_pages": [22],
        "verified_target": "Page 22: Shitapitta (Skin rash): Kanchan Rasayana 2-2-2 with honey/warm water, Timing: Three times a day after food."
    },
    {
        "id": "R42",
        "category": "Symptom-Management",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What therapies are prescribed for complete dry mouth and xerostomia (Mukhshushkata) during respiratory viral infection?",
        "expected_pages": [22],
        "verified_target": "Page 22: Mukhshushkata (Xerostomia / complete dry mouth): 1) Jyeshta Ghrita - Oral application Once/twice a day; 2) OHC oil 10ml to 20ml - Gandushkal."
    },
    {
        "id": "R43",
        "category": "Symptom-Management",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What is the recommended post-viral protocol to prevent thrombosis (Rasa-raktagat saamata and raktagranthi)?",
        "expected_pages": [22],
        "verified_target": "Page 22: Help to prevent Rasa-raktagat saamata and raktagranthi (Thrombosis): Continue Pranvir and Rasak for 90 days."
    },
    {
        "id": "R44",
        "category": "Symptom-Management",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What Nasya drops and dosages are recommended to prevent post-viral secondary infections like mucormycosis?",
        "expected_pages": [22],
        "verified_target": "Page 22: Help to prevent Upadrav (other infections e.g. mucormycosis): If Vatadhikya: Shamani Tail nasya 2 Drops (Pratimarsha nasya kal); If Kaphadhikya/Pittadhikya: Jyeshtha ghrita nasya 3 Drops (Pratimarsha nasya kal)."
    },
    # --- Category: Investigation Protocol (Page 24) ---
    {
        "id": "R45",
        "category": "Investigation",
        "doc": RESP_DOC,
        "disease_target": "Respiratory Viral Infection Management prorocol FINAL version converted 1 25",
        "question": "What investigation battery and follow-up monitoring intervals are mandated for Moderate respiratory cases (SpO2 90-94%, RR >= 24/min)?",
        "expected_pages": [24],
        "verified_target": "Page 24: Moderate State Investigations: CBC, RFT, LFT, RBS, ECG, ABG, ESR, CRP, S. FERRITIN, D-DIMER/LDH. *If QTc prolongation in ECG then daily S. Electrolytes ionic Calcium and Magnesium. *HRCT chest. *Follow up CRP, D-dimer and Sr. Ferritin every 48-72 hrs if available. *CBC with DLC, absolute lymphocyte count KFT/LFT daily."
    },

    # =========================================================================
    # PART 2: DIABETES MELLITUS GUIDELINE (DM RR DOCX) (45 QUESTIONS: D01 - D45)
    # =========================================================================
    # --- Category: Primary Prevention (Table 1, Pg 6) ---
    {
        "id": "D01",
        "category": "Dosage",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the recommended medication, dosage, and timing for an overweight person with BMI >= 25 at risk of developing diabetes?",
        "expected_pages": ["Table 1 (Pg 6)", "Pg 6", 6],
        "verified_target": "Table 1 (Pg 6): Over wt. (At-Risk BMI >= 25): Obecon 2-2-2 with Warm water, Timing: Vyanodaan kal (three times a day after food)."
    },
    {
        "id": "D02",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What primary prevention medicine is advised for individuals with a family history of diabetes mellitus?",
        "expected_pages": ["Table 1 (Pg 6)", "Pg 6", 6],
        "verified_target": "Table 1 (Pg 6): Family History Of DM: Sannidha Rasayan 2-0-2 with Warm water, Timing: Vyanodaan kal (twice a day after food)."
    },
    {
        "id": "D03",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What 3-tier stepped primary prevention protocol is recommended for Gestational Diabetes Mellitus based on severity?",
        "expected_pages": ["Table 1 (Pg 6)", "Pg 6", 6],
        "verified_target": "Table 1 (Pg 6): Gestational DM (Advice 1 or 1+2 or 1+2+3 as per severity): 1. Zincare 2-0-2 (Warm water, Vyanodaan kal); 2. Rasaka Rasayana 1-0-1 (Honey/warm water, Rasayan kal and Nisha kal); 3. Meha Rasayan 1-0-0 (Honey/warm water, Rasayan Kal)."
    },
    {
        "id": "D04",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "For a pre-diabetic individual with depression, what formulation and bedtime dose are specified?",
        "expected_pages": ["Table 1 (Pg 6)", "Pg 6", 6],
        "verified_target": "Table 1 (Pg 6): Depression: Tejonidhi Rasayan 0-0-1 with Honey, Timing: Nisha kal (At bedtime)."
    },
    {
        "id": "D05",
        "category": "Dosage",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "If an at-risk pre-diabetic patient experiences fatigue (Daurbalya-Alasya) with Vaat dushti, what adjuvant is prescribed?",
        "expected_pages": ["Table 1 (Pg 6)", "Pg 6", 6],
        "verified_target": "Table 1 (Pg 6): Daurbalya-Alasya (Fatigue) - If Vaat dushti: Deepan churna 0-1-1 with Cow ghee, Timing: Praan kal (along with Sannidha Rasayan 1-0-1)."
    },
    {
        "id": "D06",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "If an at-risk pre-diabetic patient has fatigue with Pitta and Kapha dushti, what formulation is given?",
        "expected_pages": ["Table 1 (Pg 6)", "Pg 6", 6],
        "verified_target": "Table 1 (Pg 6): Daurbalya-Alasya (Fatigue) - If Pitta and Kapha dushti: Ruchir 0-1-1 with Cow ghee, Timing: Praan kal."
    },
    {
        "id": "D07",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What primary prevention medicine is prescribed for excessive hunger / polyphagia (Laulya) in pre-diabetic individuals?",
        "expected_pages": ["Table 1 (Pg 6)", "Pg 6", 6],
        "verified_target": "Table 1 (Pg 6): Laulya (Polyphagia): Asinorm 2-0-2 with Warm water, Timing: Vyanodaan kal (twice a day after food)."
    },
    # --- Category: Symptom Management (Table 2, Pg 4) ---
    {
        "id": "D08",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the recommended Ayurvedic treatment for diabetic patients with loss of appetite, weakness, and unexplained weight loss (Shosh, Agnimandya, arochak, daurbalya)?",
        "expected_pages": ["Table 2 (Pg 4)", "Table 3 (Pg 4–8)", "Pg 4", "Pg 5"],
        "verified_target": "Table 2: Shosh Agnimandya, arochak, daurbalya etc.: Rasaka Rasayana 0-0-1 (Honey/warm water, Nisha kal), Ruchir 0-1-1 (Cow ghee, Pran kal); If chronic samprapti, add Zincare 2-0-2 (Warm water, Vyanodaan kal)."
    },
    {
        "id": "D09",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What formulations are prescribed for an unhealed diabetic ulcer / wound (Vidradhi, dushtavrana) in Table 2?",
        "expected_pages": ["Table 2 (Pg 4)", "Pg 4"],
        "verified_target": "Table 2: Vidradhi, dushtavrana (Unhealed Wound): Dasma Rasayan 1-0-0 (Lemon juice, Rasayan Kal), Pravalpanchamrut + kaamdudha + sootshekhar + ashwagandha + aarogyavardhini 1-0-1 (125 mg each with Warm water, Vyanodaan kal), Meh Rasayana 0-0-1 (Warm water, Nisha kal)."
    },
    {
        "id": "D10",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What medications are listed in Table 2 for tingling and numbness in limbs (Kampa) in diabetic patients?",
        "expected_pages": ["Table 2 (Pg 4)", "Pg 4"],
        "verified_target": "Table 2: Kampa (Tingling/Numbness in Limbs): Rasaka Rasayana 1-0-1 (Honey/warm water, Rasayan kal and Nisha kal), Kanchanar guggul + Tapyadi loh + ashwagandha 1-0-1 (125 mg each with Warm water, Vyanodaan kal)."
    },
    {
        "id": "D11",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the treatment for blurred vision (Aavil drushti) under Table 2 symptom management?",
        "expected_pages": ["Table 2 (Pg 4)", "Pg 4"],
        "verified_target": "Table 2: Aavil drushti (Blurred Vision): Sutendra Rasayana 1-0-0 SOS 1-0-1 (Honey, Rasayan kal), Rasaka Rasayana 0-0-1 (Honey/warm water, Nisha kal)."
    },
    {
        "id": "D12",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What medication and dosage are advised in Table 2 if a diabetic patient's lipid profile is abnormal?",
        "expected_pages": ["Table 2 (Pg 4)", "Pg 4"],
        "verified_target": "Table 2: Lipid profile - If abnormal: Ayulip 2-0-2 with Warm water, Timing: Vyanodaan kal (twice a day after food)."
    },
    {
        "id": "D13",
        "category": "Dosage",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What medication and dosage are indicated if HbA1c is abnormal in Table 2 routine screening?",
        "expected_pages": ["Table 2 (Pg 4)", "Pg 4"],
        "verified_target": "Table 2: HBA1C - If abnormal: Zincare 2-0-2 with Warm water, Timing: Vyanodaan kal (twice a day after food)."
    },
    # --- Category: Comprehensive Prameh Management (Table 3, Pg 4-8) ---
    {
        "id": "D14",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What medicines and dosages are prescribed for excessive thirst (Trushna / Polydipsia) in diagnosed diabetes under Table 3?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 5)", "Pg 4", "Pg 5"],
        "verified_target": "Table 3: Trushna (Polydipsia): Zincare 2-0-2 (Warm water, Vyanodaan kal - twice a day after food), Kansya Rasayan 0-0-1 (Honey/warm water, Nisha kal - At bedtime)."
    },
    {
        "id": "D15",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the comprehensive protocol for impaired taste (Aruchi) in diabetes, including chewing formulations?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 5)", "Pg 4", "Pg 5"],
        "verified_target": "Table 3: Aruchi (Impaired Taste): Zincare 2-0-2 (Warm water, Vyanodaan kal), Ruchir 0-1-1 (Cow ghee, Pran kal), Zinzi chips for chewing 3-4 times a day, Sannidha Rasayan 2-0-2 (Warm water, Vyanodaan kal)."
    },
    {
        "id": "D16",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What regimen is recommended for excessive bodily discharges, hyperhidrosis, and Acanthosis nigricans (Malaadhikya, Swed bahulya)?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 5)", "Pg 5"],
        "verified_target": "Table 3: Malaadhikya Swed bahulya (Hyperhidrosis, Acanthosis nigricans): Zincare 2-0-2, Sannidha Rasayan 2-0-2, Meha Rasayan 1-0-0 (Honey/warm water, Rasayan Kal), Aarevat Kalpa 0-0-1 or 0-0-2 (Warm water, Nisha Kal)."
    },
    {
        "id": "D17",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What comprehensive medicines are prescribed for polyphagia / excessive hunger (Laulya) in diagnosed diabetes?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 5)", "Pg 5"],
        "verified_target": "Table 3: Laulya (Polyphagia): Zincare 2-0-2, Livayog 1-0-1 (Warm water, Vyanodaan kal), Meha Rasayan 1-0-0 (Honey/warm water, Rasayan Kal), Kansya Rasayan 0-0-1 (Honey/warm water, Nisha Kal)."
    },
    {
        "id": "D18",
        "category": "Dosage",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What specific dose of Kanchanar Guggul and adjuvant formulations are prescribed for unhealed diabetic ulcers (Dushtavrana) in Table 3?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 6)", "Pg 6"],
        "verified_target": "Table 3: Unhealed wound (Vidradhi, Dushtavrana): Zincare 2-0-2, Kanchanar Guggul 250mg 2-0-2 (Warm water, Vyanodaan kal), Meha Rasayan 0-0-1 (Nisha Kal), Dasma 1-0-0 (Lemon juice, Rasayan Kal), Sannidha Rasayan 2-0-2."
    },
    {
        "id": "D19",
        "category": "Dosage",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the dosage and regimen for polyuria / frequent cloudy urination (Prabhoot Aavil Mutrata) in Table 3?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 6)", "Pg 6"],
        "verified_target": "Table 3: Prabhoot Aavil Mutrata (Polyuria): Zincare 1-0-1 (Warm water, Vyanodaan kal), Meha Rasayan 0-0-1 (Honey/warm water, Nisha Kal), Sannidha Rasayan 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 1-0-1 (Rasayan kal and Nisha kal)."
    },
    {
        "id": "D20",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What formulations are given for sweet-smelling, cloudy urine (Madhur-Shukla Mutrataa) in Table 3?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 6)", "Pg 6"],
        "verified_target": "Table 3: Madhur-Shukla Mutrataa: Zincare 1-0-1, Meha Rasayan 0-0-1, Sannidha Rasayan 2-0-2, Rasaka Rasayana 1-0-1."
    },
    {
        "id": "D21",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the treatment for foul breath and body odor (Visra Gandhata) in diabetic patients?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 6)", "Table 3 (Pg 7)", "Pg 6", "Pg 7"],
        "verified_target": "Table 3: Visra Gandhata (Foul smell of breath and body): Zincare 2-0-2, Meha Rasayan 0-0-1, Asinorm 1-0-1, Zinzi chips for chewing 3-4 times a day."
    },
    {
        "id": "D22",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the regimen for insomnia (Anidra) in diabetes, including topical / external therapy?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 7)", "Pg 7"],
        "verified_target": "Table 3: Anidra (Poor sleep/Insomnia): Zincare 2-0-2, Meha Rasayan 0-0-1, Tejonidhi 0-0-2 (Honey, Nisha Kal), Yashtighrut shiropichu 0-0-1 (Nisha Kal at bedtime)."
    },
    {
        "id": "D23",
        "category": "Dosage",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the prescription and timing for cystitis / bladder pain (Basti Shool) in diabetes?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 7)", "Pg 7"],
        "verified_target": "Table 3: Basti Shool (Cystitis): Zincare 2-0-2, Chandraprabha+Shankhavati+Gokshur+Praval each 125mg 1-0-1 (Warm water, Apaan kal - before food), Rasaka Rasayana 1-0-1, Asinorm 2-0-2, Ayukshar 5gm per 1litre drinking water."
    },
    {
        "id": "D24",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What medicines are prescribed for diabetic urinary incontinence (Basti Bheda)?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 7)", "Pg 7"],
        "verified_target": "Table 3: Basti Bheda (Urinary incontinence): Zincare 2-0-2, Chandraprabha+Gokshuradi guggul+jatamansi each 125mg 1-0-1 (Warm water, Apaan kal), Rasaka Rasayana 1-0-1, Asinorm 2-0-2."
    },
    {
        "id": "D25",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What protocol adaptation is specified for Type 1 Diabetes (Beej doshaj prameh)?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 7)", "Pg 7"],
        "verified_target": "Table 3: Beej doshaj prameh (For Type 1): Add Heerak Rasayan 1 at Rasayan Kal (early morning on empty stomach), rest same as type 2."
    },
    {
        "id": "D26",
        "category": "Severity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What critical warning signs must physicians monitor continuously in diabetic patients according to Table 3?",
        "expected_pages": ["Table 3 (Pg 4–8)", "Table 3 (Pg 8)", "Pg 8"],
        "verified_target": "Table 3 Warning Signs: Aayasen Shwas (Dyspnoea on exertion), Bhaarvruddhi/Bhaar kshay (Weight gain/loss), Bhrama, Hrullas, daurbalya (Electrolyte imbalance, fluid overload), Rasaabhinodanvruddhi (High BP), and E-GFR less than 60."
    },
    # --- Category: Secondary Prevention & Complication Onset (Table 4 & 5, Pg 10-11) ---
    {
        "id": "D27",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What formulations are used to prevent diabetic syncopal attacks and metabolic episodes (Murchha) in Table 4?",
        "expected_pages": ["Table 4 (Pg 10)", "Pg 10"],
        "verified_target": "Table 4: Murchha: Meha Rasayan 1-0-0 (Rasayan Kal), Rasaka Rasayana 0-0-1 (Nisha kal), Aarevat Kalpa 0-0-1 (Nisha kal), Aarogyavardhini + praval + chandraprabha + meshshringi 0-1-1 (Warm water, Vyanodaan kal)."
    },
    {
        "id": "D28",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What secondary prevention regimen is specified for erectile dysfunction (Punstvopghaat) in Table 4?",
        "expected_pages": ["Table 4 (Pg 10)", "Pg 10"],
        "verified_target": "Table 4: Punstvopghaat (Erectile dysfunction): Sindurbhushan Rasayan 1-0-0 (Honey/warm water, Rasayan Kal), Chandraprabha + bhasma + ashwagandha + praval bhasma 125mg each + jasad bhasma 30mg + vanga 10mg 0-1-1."
    },
    {
        "id": "D29",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What prophylactic regimen is prescribed for patients with a tendency for recurrent non-healing wounds (Vidradhi) in Table 4?",
        "expected_pages": ["Table 4 (Pg 10)", "Pg 10"],
        "verified_target": "Table 4: Vidradhi (recurrent non healing wound): Meha Rasayan 1-0-0 (Honey/warm water, Rasayan Kal), Zincare 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 0-0-1 (Honey/warm water, Nisha kal)."
    },
    {
        "id": "D30",
        "category": "Comorbidity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the prevention regimen for a patient at risk of diabetic gangrene (Putimansa) according to Table 5?",
        "expected_pages": ["Table 5 (Pg 10–11)", "Table 5 (Pg 10)", "Pg 10"],
        "verified_target": "Table 5: Putimansa (Gangrene) RISKY PATIENT: Meha Rasayan 1-0-0 (Honey/warm water, Rasayan Kal), Zincare 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 0-0-1 (Honey/warm water, Nisha kal)."
    },
    {
        "id": "D31",
        "category": "Comorbidity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What formulations are given to prevent cardiovascular complications (Hrudgraha / Hrudrog) in diabetic patients in Table 5?",
        "expected_pages": ["Table 5 (Pg 10–11)", "Table 5 (Pg 10)", "Pg 10"],
        "verified_target": "Table 5: Hrudgraha /Hrudrog (Cardiovascular complications): Arpisa Rasayan 1-0-0 (Honey/warm water, Rasayan Kal), Zincare 2-0-2 (Warm water, Vyanodaan kal), Meha Rasayan 0-0-1 (Honey/warm water, Nisha kal)."
    },
    {
        "id": "D32",
        "category": "Comorbidity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What regimen is recommended for preventing dementia and cognitive decline in chronic diabetic patients in Table 5?",
        "expected_pages": ["Table 5 (Pg 10–11)", "Table 5 (Pg 10)", "Pg 10"],
        "verified_target": "Table 5: Dementia/Alzheimer's: Tejonidhi Rasayan 2-0-2 (Honey/warm water, Rasayan kal and Nisha kal), Zincare 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 0-0-1 (Honey/warm water, Nisha kal)."
    },
    {
        "id": "D33",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What medicines and dosages are prescribed for recurrent skin infections in diabetic patients in Table 5?",
        "expected_pages": ["Table 5 (Pg 10–11)", "Table 5 (Pg 10)", "Pg 10"],
        "verified_target": "Table 5: Skin infections: Kanchan Rasayan 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 1-0-1 (Honey/warm water, Rasayan kal and Nisha kal)."
    },
    {
        "id": "D34",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What medicines are prescribed for idiopathic diabetic diarrhea (Vidbheda / Atisaar) in Table 5?",
        "expected_pages": ["Table 5 (Pg 10–11)", "Table 5 (Pg 10)", "Table 5 (Pg 11)", "Pg 10", "Pg 11"],
        "verified_target": "Table 5: Idiopathic diarrhoea (Vidbheda/ Atisaar): Rasaka Rasayana 1-0-1 (Honey/warm water, Rasayan kal and Nisha kal), Amaneel 2-0-2 (Warm water, Vyanodaan kal)."
    },
    # --- Category: Diabetic Nephropathy & Hypertension (Table 6, 7, 8, Pg 12-15) ---
    {
        "id": "D35",
        "category": "Comorbidity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "For a diabetic patient with known hypertension (Rasaabhinodan-vruddhi), what blood pressure formulations and doses are prescribed in Table 6?",
        "expected_pages": ["Table 6 (Pg 12)", "Pg 12"],
        "verified_target": "Table 6: Rasaabhinodan-vruddhi (K/C/O Hypertension): Sutendra Rasayana 1-0-0 or 1-0-1 with Honey, Normoten 1-0-1 or 2-0-2 (Vyanodaan kal)."
    },
    {
        "id": "D36",
        "category": "Severity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the complete Ayurvedic regimen for Diabetic Nephropathy Stage 1 (GFR >= 90%, creatinine around 2)?",
        "expected_pages": ["Table 6 (Pg 12)", "Pg 12"],
        "verified_target": "Table 6: Stage 1 (GFR >= 90%, creatinine ~2): Zincare 2-0-2 (Warm water, Vyanodaan kal), Sannidha Rasayan 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 1-0-1 (Honey/warm water, Rasayan kal and Nisha kal), Lavan (replace table salt in cooking)."
    },
    {
        "id": "D37",
        "category": "Severity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the complete Ayurvedic prescription for Diabetic Nephropathy Stage 2 (GFR 60–89%, creatinine 2 to 4)?",
        "expected_pages": ["Table 6 (Pg 12)", "Pg 12"],
        "verified_target": "Table 6: Stage 2 (GFR 60-89%, creatinine 2-4): Zincare 2-2-2 (Warm water, Three times a day after food), Sannidha Rasayan 2-0-2 (Warm water, Vyanodaan kal), Rasaka Rasayana 1-0-1 (Honey/warm water), Urokine 1-0-1 (Warm water, Vyanodaan kal), Lavan, Ayukshar 5gm per 1litre drinking water."
    },
    {
        "id": "D38",
        "category": "Severity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the complete management protocol for Diabetic Nephropathy Stage 3 (GFR 30–59%, creatinine 4 to 6)?",
        "expected_pages": ["Table 7 (Pg 12–13)", "Table 7 (Pg 12)", "Table 7 (Pg 13)", "Pg 12", "Pg 13"],
        "verified_target": "Table 7: Stage 3 (GFR 30-59%, creatinine 4-6): Zincare 2-2-2 (Three times a day), Sannidha Rasayan 2-0-2, Rasaka Rasayana 1-0-1, Urokine 2-2-2 (Vyanodaan kal), Meha Rasayan 1-0-0 (Rasayan Kal), Lavan, Ayukshar 5gm/1L drinking water, Aarevat 0-0-1 if constipated."
    },
    {
        "id": "D39",
        "category": "Severity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What formulations and timing changes occur in Diabetic Nephropathy Stage 4 (GFR 15–29%, creatinine 6 to 8)?",
        "expected_pages": ["Table 7 (Pg 12–13)", "Table 7 (Pg 13)", "Pg 13"],
        "verified_target": "Table 7: Stage 4 (GFR 15-29%, creatinine 6-8): Zincare 2-2-2, Sannidha Rasayan 2-0-2, Urokine 2-2-2, Meha Rasayan shifts to 0-0-1 (Nisha kal), Heerak Rasayan 1-0-0 added (Honey/warm water, Rasayan Kal), Aarevat Kalpa 0-0-1 or 0-0-2 (even if bowels clear), Lavan, Ayukshar 5gm/1L."
    },
    {
        "id": "D40",
        "category": "Severity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the full protocol for Diabetic Nephropathy Stage 5 / Kidney Failure (GFR < 15%, creatinine > 8)?",
        "expected_pages": ["Table 8 (Pg 13–15)", "Table 8 (Pg 13)", "Table 8 (Pg 14)", "Pg 13", "Pg 14"],
        "verified_target": "Table 8: Stage 5 (GFR < 15%, creatinine > 8): Zincare 2-2-2, Sannidha Rasayan 2-0-2, Urokine 2-2-2, Meha Rasayan 0-0-1, Heerak Rasayan 1-0-0 (Rasayan Kal), Aarevat Kalpa 0-0-1 or 2, Lavan, Ayukshar 5gm/1L."
    },
    {
        "id": "D41",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What formulations are prescribed for peripheral edema and swollen legs (Shoth) in diabetic dialysis patients?",
        "expected_pages": ["Table 8 (Pg 13–15)", "Table 8 (Pg 14)", "Pg 14"],
        "verified_target": "Table 8: Shoth (Swollen ankles, feet, legs, hands on dialysis): Urokine 2-0-2 or 2-2-2 (Warm water), Punarnavasav 3-3-3 tsf with Water, Timing: Vyanodaan kal (three times a day after food)."
    },
    {
        "id": "D42",
        "category": "Symptom-Management",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What medications are prescribed for heavy proteinuria / frothy urine (Shukla mutrataa) in diabetic nephropathy?",
        "expected_pages": ["Table 8 (Pg 13–15)", "Table 8 (Pg 14)", "Pg 14"],
        "verified_target": "Table 8: Shukla mutrataa (Protein in urine, frothy urine): Urokine 2-0-2 or 2-2-2, Zincare 2-0-2 (Warm water), Kansya rasayan 1-0-0 (Rasayan Kal), Meha Rasayan 0-0-1 (Nisha kal)."
    },
    # --- Category: Acute Ketones, Retinopathy, Neuropathy, Gangrene (Table 9-13, Pg 15-21) ---
    {
        "id": "D43",
        "category": "Table-Based",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What is the emergency Ayurvedic guideline for Pramehaj Moorcha with ketones in urine routine (DKA signs)?",
        "expected_pages": ["Table 9 (Pg 15–16)", "Table 9 (Pg 15)", "Pg 15"],
        "verified_target": "Table 9: Pramehaj Moorcha (Ketones in urine): Heerak Rasayan 1-0-0 (Rasayan Kal), Meha Rasayan 0-0-1 (Nisha kal), Zincare 2-0-2 or 2-2-2, Urokine 2-2-2, Ayukshar 5gm/1L, Lavan, Aarevat Kalpa 0-0-2, Asinorm 2-2-2."
    },
    {
        "id": "D44",
        "category": "Severity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What formulations are prescribed for early-stage diabetic retinopathy with blurred vision and floaters?",
        "expected_pages": ["Table 10 (Pg 16–17)", "Table 10 (Pg 16)", "Pg 16"],
        "verified_target": "Table 10: Diabetic Retinopathy Early Stage (Blurred vision, floaters, risk of hemorrhage): Sunetra Rasayan 1-0-1 (Honey + cow ghee, Vyanodaan kal), Rasaka Rasayana 1-0-1 (Honey/warm water); Nitya sevanarth: Heerak Rasayan 1-0-0, Meha Rasayan 0-0-1."
    },
    {
        "id": "D45",
        "category": "Severity",
        "doc": DM_DOC,
        "disease_target": "DM RR",
        "question": "What formulations are given for late-stage diabetic retinopathy with dark spots in vision and active bleeding?",
        "expected_pages": ["Table 10 (Pg 16–17)", "Table 10 (Pg 16)", "Table 10 (Pg 17)", "Pg 16", "Pg 17"],
        "verified_target": "Table 10: Diabetic Retinopathy Late Stage (Dark spots, active bleeding vitreous-retinal/maculopathy): Niketa Rasayan 1-0-1 (Honey/warm water, Vyanodaan kal) and Netraj Rasayan 1-0-1 (Honey/warm water, Vyanodaan kal)."
    },

    # =========================================================================
    # PART 3: CROSS-DOCUMENT RETRIEVAL & MULTI-MORBIDITY (10 QUESTIONS: C01 - C10)
    # =========================================================================
    {
        "id": "C01",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "A patient with acute respiratory viral infection also has chronic Type 2 diabetes. What does the respiratory protocol advise on Page 8/14, and what primary diabetes management is outlined in the diabetes guideline?",
        "expected_pages": [8, 14, "Table 1 (Pg 3–4)", "Table 3 (Pg 4–8)"],
        "verified_target": "Cross-Document Synthesis: Respiratory guideline (Page 8 & 14) prescribes Rasvir 1-0-0 / Somtajvir 1-0-0/1-0-1, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, and Meha Rasayan 1-0-0. Diabetes guideline (Table 1 & 3) outlines core glycemic management with Zincare 2-0-2, Meha Rasayan 1-0-0, and Sannidha Rasayan 2-0-2."
    },
    {
        "id": "C02",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "A patient has respiratory viral infection and severe diabetic nephropathy with GFR under 30. How do the renal guidelines in the respiratory protocol compare with Diabetic Nephropathy Stage 4/5 in the diabetes protocol?",
        "expected_pages": [8, 20, "Table 7 (Pg 12–13)", "Table 8 (Pg 13–15)"],
        "verified_target": "Cross-Document Synthesis: Respiratory guideline (Page 8 & 20) prescribes Pranvir 2-2-2, Rasaka Rasayana 1-0-1, and Heeraka Rasayana 1-0-0. Diabetic Nephropathy Stage 4/5 (Table 7 & 8) prescribes Zincare 2-2-2, Sannidha Rasayan 2-0-2, Urokine 2-2-2, Heerak Rasayan 1-0-0, Meha Rasayan 0-0-1, and Ayukshar 5gm/1L."
    },
    {
        "id": "C03",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "What is the dosage, vehicle, and clinical timing of Meha Rasayana across both the respiratory guidelines and the diabetes guidelines?",
        "expected_pages": [8, 11, 14, "Table 1 (Pg 3–4)", "Table 3 (Pg 4–8)", "Table 7 (Pg 12–13)"],
        "verified_target": "Cross-Document Synthesis: In respiratory guidelines (Pages 8, 11, 14), Meha Rasayana is dosed at 1-0-0 with Honey/warm water at Rasayan kal (early morning on empty stomach). In the diabetes guideline (Tables 1, 3, 7), it is 1-0-0 at Rasayan kal for prophylaxis/mild stages, and shifts to 0-0-1 at Nisha kal (bedtime) in advanced nephropathy / acute complications."
    },
    {
        "id": "C04",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "How is dry mouth / xerostomia addressed in the respiratory guidelines versus polydipsia / thirst in the diabetes guidelines?",
        "expected_pages": [22, "Table 1 (Pg 3–4)", "Table 3 (Pg 4–8)"],
        "verified_target": "Cross-Document Synthesis: Respiratory guideline (Page 22) uses Jyeshta Ghrita oral application and OHC oil (10-20ml) gandush. Diabetes guideline (Table 1 & 3) treats Trushna/thirst with Sannidha Rasayan 1-0-1, Zincare 2-0-2, Kansya Rasayan 0-0-1, and Ayukshar alkaline water."
    },
    {
        "id": "C05",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "Compare the recommendations for constipation (Malavrodh / Malbadhhata) between the respiratory symptom protocol and the diabetes complication protocols.",
        "expected_pages": [22, "Table 3 (Pg 4–8)", "Table 5 (Pg 10–11)", "Table 13 (Pg 20–21)"],
        "verified_target": "Cross-Document Synthesis: Respiratory guideline (Page 22) prescribes Aarewat Kalpa sos 0-0-1 or 2 with warm water at Nisha kal. Diabetes guideline (Tables 3, 5, 7, 11, 13) similarly prescribes Aarevat Kalpa 0-0-1 or 0-0-2 at bedtime with warm water, often paired with Meha Rasayan or Zincare."
    },
    {
        "id": "C06",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "A diabetic patient with severe diabetic neuropathy (numbness, burning pain) contracts a respiratory viral infection. What guidance from both documents addresses both conditions?",
        "expected_pages": [14, "Table 11 (Pg 17–19)"],
        "verified_target": "Cross-Document Synthesis: Respiratory infection managed via Page 14 protocol (Somtajvir, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Meha Rasayan 1-0-0). Diabetic neuropathy managed via Table 11: Heerak Rasayan 1-0-0, Meha Rasayan 0-0-1, Siraatone 2-0-2 or 2-2-2, and Abhyangini Tail for padabhyanga."
    },
    {
        "id": "C07",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "What is the clinical role and administration of Sutendra Rasayana in respiratory viral infection with hypertension versus diabetes with hypertension?",
        "expected_pages": [8, 10, 15, 22, "Table 1 (Pg 3–4)", "Table 6 (Pg 12)"],
        "verified_target": "Cross-Document Synthesis: In respiratory guidelines (Pages 8, 10, 15, 22), Sutendra Rasayana is given 1-0-0 for prophylaxis or 1-1-1 Muhurmuhur for acute blood pressure spikes. In diabetes guidelines (Tables 1 & 6), it is given 1-0-0 or 1-0-1 with honey at Rasayan kal / Nisha kal alongside Normoten."
    },
    {
        "id": "C08",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "A diabetic patient has an infected diabetic foot ulcer / gangrene (Putimansa) and develops respiratory symptoms. What treatments from both documents apply?",
        "expected_pages": [14, "Table 5 (Pg 10–11)", "Table 12 (Pg 19–20)"],
        "verified_target": "Cross-Document Synthesis: Respiratory management from Page 14 (Somtajvir, Pranvir, Rasaka Rasayana, Meha Rasayan). Diabetic gangrene from Table 5 & 12: Zincare 2-0-2, Siraatone 2-0-2/2-2-2, Heeraka Rasayan 1-0-0, Meha Rasayan 0-0-1, Dhruti oil local application, and Somtajvir 1-0-1 for wet gangrene (Sravi)."
    },
    {
        "id": "C09",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "Compare the indications for Heerak / Heeraka Rasayana across both the respiratory guidelines and the diabetes guidelines.",
        "expected_pages": [7, 8, 11, 15, 20, "Table 3 (Pg 4–8)", "Table 7 (Pg 12–13)", "Table 8 (Pg 13–15)", "Table 9 (Pg 15–16)", "Table 10 (Pg 16–17)", "Table 11 (Pg 17–19)"],
        "verified_target": "Cross-Document Synthesis: In respiratory guidelines, Heeraka Rasayana is used for cancer prophylaxis (Pg 7), renal failure (Pg 8, 20), severe cardiac disease (Pg 15), and pregnancy (Pg 11). In diabetes guidelines, it is indicated for Type 1 DM (Table 3), advanced nephropathy Stages 4-5 (Tables 7-8), DKA (Table 9), retinopathy (Table 10), and neuropathy (Table 11)."
    },
    {
        "id": "C10",
        "category": "Cross-Document",
        "doc": "Both Documents (Respiratory PDF + Diabetes DOCX)",
        "disease_target": "Cross-Document",
        "question": "A patient presents with fever, cough, SpO2 92% (moderate respiratory viral infection) and has poorly controlled diabetes with polyuria and HbA1c 10%. How should the attending physician synthesize guidance from both documents?",
        "expected_pages": [14, 24, "Table 2 (Pg 4)", "Table 3 (Pg 4–8)"],
        "verified_target": "Cross-Document Synthesis: For moderate respiratory infection: Somtajvir 1-0-1, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Meha Rasayan 1-0-0, plus Moderate Investigation battery (HRCT, CRP, Ferritin, D-dimer). For uncontrolled diabetes with polyuria & high HbA1c: Zincare 2-0-2 (Table 2 & 3), Sannidha Rasayan 2-0-2, and lifestyle/dietary guidance."
    }
]

def verify_page_numbers(expected_pages: List[Any], retrieved_pages: List[Any]) -> Dict[str, Any]:
    """
    Verifies whether retrieved page numbers match the actual pages containing supporting answers.
    Handles numeric pages (e.g. 6, 14, 22) and docx string labels (e.g. 'Table 1 (Pg 3-4)').
    """
    if not retrieved_pages:
        return {
            "match": False,
            "status": "MISMATCH",
            "reason": "No pages retrieved by RAG pipeline"
        }
    
    # Normalize expected pages to strings and integers
    exp_ints = set()
    exp_strs = []
    for ep in expected_pages:
        if isinstance(ep, int):
            exp_ints.add(ep)
        elif isinstance(ep, str):
            exp_strs.append(ep.lower())
            found_nums = [int(n) for n in re.findall(r"\b\d+\b", ep)]
            exp_ints.update(found_nums)

    # Normalize retrieved pages
    ret_ints = set()
    ret_strs = []
    for rp in retrieved_pages:
        if isinstance(rp, int):
            ret_ints.add(rp)
        elif isinstance(rp, str):
            ret_strs.append(rp.lower())
            found_nums = [int(n) for n in re.findall(r"\b\d+\b", rp)]
            ret_ints.update(found_nums)

    # 1. Exact match check
    int_overlap = exp_ints.intersection(ret_ints)
    str_match = False
    for es in exp_strs:
        for rs in ret_strs:
            if es in rs or rs in es:
                str_match = True
                break

    if int_overlap or str_match:
        matched_details = list(int_overlap) if int_overlap else [s for s in exp_strs if any(s in r for r in ret_strs)]
        return {
            "match": True,
            "status": "EXACT_MATCH",
            "matched_pages": matched_details,
            "reason": f"Direct match found: {matched_details}"
        }

    # 2. Partial / Adjacent match check (within +/- 1 page in document)
    adjacent = set()
    for ei in exp_ints:
        adjacent.update([ei - 1, ei + 1])
    adj_overlap = adjacent.intersection(ret_ints)
    if adj_overlap:
        return {
            "match": True,
            "status": "PARTIAL_MATCH",
            "matched_pages": list(adj_overlap),
            "reason": f"Adjacent page match (within 1 page): {list(adj_overlap)}"
        }

    return {
        "match": False,
        "status": "MISMATCH",
        "reason": f"Retrieved pages {retrieved_pages} do not contain expected pages {expected_pages}"
    }

def evaluate_single_response(item: Dict[str, Any], rag_result: Dict[str, Any], duration: float) -> Dict[str, Any]:
    """
    Evaluates retrieval accuracy, answer correctness, completeness, faithfulness, and document relevance.
    """
    src_chunks = rag_result.get("source_chunks", [])
    ans = rag_result.get("answer", "")
    found = rag_result.get("found_in_pdf", False)
    
    retrieved_pages = sorted(list(set([c.get("metadata", {}).get("page") for c in src_chunks if c.get("metadata", {}).get("page") is not None])), key=lambda x: str(x))
    retrieved_docs = sorted(list(set([os.path.basename(c.get("metadata", {}).get("source", "")) for c in src_chunks if c.get("metadata", {}).get("source")])))

    # 1. Page Number Verification
    page_audit = verify_page_numbers(item["expected_pages"], retrieved_pages)
    
    # 2. Document match check
    doc_target = item["doc"]
    if "Both" in doc_target:
        doc_matched = any("Respiratory" in d for d in retrieved_docs) and any("DM" in d for d in retrieved_docs)
        if not doc_matched:
            # Partial document match
            doc_matched = any("Respiratory" in d or "DM" in d for d in retrieved_docs)
    else:
        doc_matched = any(os.path.basename(doc_target).lower() in d.lower() or d.lower() in os.path.basename(doc_target).lower() for d in retrieved_docs)

    # 3. Retrieval Accuracy (0.0 to 1.0)
    # Combines document provenance and page accuracy
    doc_score = 1.0 if doc_matched else 0.0
    page_score = 1.0 if page_audit["status"] == "EXACT_MATCH" else (0.75 if page_audit["status"] == "PARTIAL_MATCH" else 0.25)
    retrieval_accuracy = round(0.4 * doc_score + 0.6 * page_score, 2)

    # 4. Answer Correctness & Completeness
    # Extract reference keywords and entities from verified target
    ref_text = item["verified_target"].lower()
    # Key formulations
    key_entities = [
        "pranvir", "rasvir", "rasaka", "somtajvir", "meha", "sutendra", "arpisa", "heerak", "heeraka",
        "mahalakshmi", "sindurbhushan", "pranvallabh", "bal rasayan", "respin", "yashada", "suvarn",
        "kanchan", "ayukshar", "aarewat", "aarevat", "zincare", "sannidha", "urokine", "obecon",
        "tejonidhi", "asinorm", "ruchir", "dasma", "livayog", "sunetra", "niketa", "netraj",
        "siraatone", "abhyangini", "pawanchintamani", "pawan chintamani", "indriyakalyanak",
        "panchamukta", "amaneel", "normoten", "lavan", "punarnavasav", "chandanasav"
    ]
    ref_entities = [e for e in key_entities if e in ref_text]
    ans_lower = ans.lower()
    
    matched_entities = [e for e in ref_entities if e in ans_lower]
    entity_score = len(matched_entities) / max(1, len(ref_entities))

    # Dosage format match (e.g. 1-0-0, 2-0-2, 2-2-2, 1-0-1, etc.)
    ref_dosages = re.findall(r"\b\d+-\d+-\d+\b", item["verified_target"])
    matched_dosages = [d for d in ref_dosages if d in ans]
    dosage_score = len(matched_dosages) / max(1, len(ref_dosages)) if ref_dosages else 1.0

    # Answer Correctness score
    answer_correctness = round(0.65 * entity_score + 0.35 * dosage_score, 2)
    if not found or "not mentioned" in ans_lower:
        answer_correctness = 0.0

    # 5. Completeness Score
    # Assesses coverage of formulation, dosage, timing/vehicle
    has_timing = any(t in ans_lower for t in ["rasayan kal", "nisha kal", "vyanodaan", "food", "empty stomach", "bedtime", "after meals"])
    has_vehicle = any(v in ans_lower for v in ["honey", "water", "ghee", "warm", "lemon"])
    completeness = round(0.5 * entity_score + 0.25 * (1.0 if has_timing else 0.0) + 0.25 * (1.0 if has_vehicle else 0.0), 2)

    # 6. Faithfulness Score
    # Check that medications mentioned in answer actually appear in retrieved chunks
    chunk_combined = " ".join([c["text"].lower() for c in src_chunks])
    answer_meds = [e for e in key_entities if e in ans_lower]
    grounded_meds = [m for m in answer_meds if m in chunk_combined]
    faithfulness = round(len(grounded_meds) / max(1, len(answer_meds)), 2) if answer_meds else 1.0

    # 7. Document Relevance Score
    # Measures question token presence in retrieved context
    q_tokens = set(re.findall(r"\w+", item["question"].lower())) - {"what", "is", "the", "for", "and", "in", "with", "according", "guidelines", "which", "are"}
    relevance_overlap = sum(1 for t in q_tokens if t in chunk_combined)
    document_relevance = round(min(1.0, relevance_overlap / max(1, len(q_tokens) * 0.4)), 2)

    # 8. Overall Pass / Fail Status
    pass_criteria = (
        retrieval_accuracy >= 0.55 and
        answer_correctness >= 0.50 and
        faithfulness >= 0.70 and
        len(ans) > 60
    )
    verdict = "PASS" if pass_criteria else "FAIL"

    # 9. Failure Reasons
    failure_reasons = []
    if page_audit["status"] == "MISMATCH":
        failure_reasons.append(f"Page Mismatch: Expected {item['expected_pages']}, Retrieved {retrieved_pages}")
    if not doc_matched:
        failure_reasons.append(f"Document Mismatch: Target {doc_target} not in retrieved {retrieved_docs}")
    if entity_score < 0.50:
        missing = [e for e in ref_entities if e not in ans_lower]
        failure_reasons.append(f"Missing Key Ayurvedic Formulations: {missing}")
    if dosage_score < 0.50 and ref_dosages:
        missing_d = [d for d in ref_dosages if d not in ans]
        failure_reasons.append(f"Missing Specific Dosage Formats: {missing_d}")
    if faithfulness < 0.75:
        failure_reasons.append(f"Low Faithfulness: Potential ungrounded entities in answer")
    if not found:
        failure_reasons.append("RAG pipeline returned 'Not mentioned in the PDF'")

    failure_reason_str = "; ".join(failure_reasons) if failure_reasons else "None (All criteria met)"

    return {
        "id": item["id"],
        "category": item["category"],
        "target_document": item["doc"],
        "question": item["question"],
        "expected_pages": item["expected_pages"],
        "retrieved_pages": retrieved_pages,
        "page_match_status": page_audit["status"],
        "page_audit_reason": page_audit["reason"],
        "retrieved_docs": retrieved_docs,
        "found_in_pdf": found,
        "duration_seconds": duration,
        "verified_reference_answer": item["verified_target"],
        "rag_answer": ans,
        "metrics": {
            "retrieval_accuracy": retrieval_accuracy,
            "answer_correctness": answer_correctness,
            "completeness": completeness,
            "faithfulness": faithfulness,
            "document_relevance": document_relevance
        },
        "verdict": verdict,
        "failure_reasons": failure_reason_str
    }

def run_evaluation():
    db = HybridSearchEngine(persist_dir="./data/chroma_db")
    pipeline = ClinicalRAGPipeline(db_engine=db)

    print("=" * 80)
    print("STARTING COMPREHENSIVE 100-QUESTION AUTOMATED RAG EVALUATION PIPELINE")
    print(f"Total Questions: {len(QUESTIONS_100)}")
    print(f"ChromaDB Chunk Count: {db.collection.count()}")
    print("=" * 80)
    sys.stdout.flush()

    results = []
    t_start_all = time.time()

    for idx, item in enumerate(QUESTIONS_100):
        q_num = idx + 1
        print(f"\n[{q_num:03d}/100] Evaluating Question {item['id']} ({item['category']})...")
        print(f"   Target Doc: {os.path.basename(item['doc'])}")
        print(f"   Query: {item['question'][:80]}...")
        sys.stdout.flush()

        t0 = time.time()
        try:
            # Query pipeline
            disease_param = item["disease_target"]
            res = pipeline.answer_question(query=item["question"], disease_name=disease_param)
            dur = round(time.time() - t0, 2)
            
            evaluated = evaluate_single_response(item, res, dur)
            results.append(evaluated)

            m = evaluated["metrics"]
            print(f"   Verdict: {evaluated['verdict']} | Page Status: {evaluated['page_match_status']}")
            print(f"   Retrieval: {m['retrieval_accuracy']} | Correctness: {m['answer_correctness']} | Completeness: {m['completeness']} | Faithfulness: {m['faithfulness']} | Relevance: {m['document_relevance']}")
            print(f"   Retrieved Pages: {evaluated['retrieved_pages']} vs Expected: {item['expected_pages']}")
            if evaluated["verdict"] == "FAIL":
                print(f"   Failure Reason: {evaluated['failure_reasons']}")
            sys.stdout.flush()

        except Exception as e:
            dur = round(time.time() - t0, 2)
            print(f"   Error executing {item['id']}: {e}")
            sys.stdout.flush()
            results.append({
                "id": item["id"],
                "category": item["category"],
                "target_document": item["doc"],
                "question": item["question"],
                "expected_pages": item["expected_pages"],
                "retrieved_pages": [],
                "page_match_status": "MISMATCH",
                "page_audit_reason": f"Execution error: {e}",
                "retrieved_docs": [],
                "found_in_pdf": False,
                "duration_seconds": dur,
                "verified_reference_answer": item["verified_target"],
                "rag_answer": f"Error during pipeline execution: {e}",
                "metrics": {
                    "retrieval_accuracy": 0.0,
                    "answer_correctness": 0.0,
                    "completeness": 0.0,
                    "faithfulness": 0.0,
                    "document_relevance": 0.0
                },
                "verdict": "ERROR",
                "failure_reasons": f"Execution Exception: {e}"
            })

        # Save intermediate snapshot every 10 questions
        if q_num % 10 == 0 or q_num == len(QUESTIONS_100):
            with open("evaluation_100_questions_report.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"   -> [Checkpoint Saved: {q_num}/100 questions]")
            sys.stdout.flush()

        # Polite rate-limiting sleep between Gemini API calls
        time.sleep(2.5)

    total_time = round(time.time() - t_start_all, 2)

    # Compute Aggregate Metrics
    total_q = len(results)
    passed_q = sum(1 for r in results if r["verdict"] == "PASS")
    exact_pages = sum(1 for r in results if r["page_match_status"] == "EXACT_MATCH")
    partial_pages = sum(1 for r in results if r["page_match_status"] == "PARTIAL_MATCH")
    page_match_rate = round((exact_pages + partial_pages) / total_q * 100, 1)

    avg_retrieval = round(sum(r["metrics"]["retrieval_accuracy"] for r in results) / total_q, 3)
    avg_correctness = round(sum(r["metrics"]["answer_correctness"] for r in results) / total_q, 3)
    avg_completeness = round(sum(r["metrics"]["completeness"] for r in results) / total_q, 3)
    avg_faithfulness = round(sum(r["metrics"]["faithfulness"] for r in results) / total_q, 3)
    avg_relevance = round(sum(r["metrics"]["document_relevance"] for r in results) / total_q, 3)
    avg_duration = round(sum(r["duration_seconds"] for r in results) / total_q, 2)

    # Write Final Structured JSON Report
    with open("evaluation_100_questions_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Generate Human-Readable Formatted Text Report
    report_txt_path = "evaluation_results_100_questions.txt"
    with open(report_txt_path, "w", encoding="utf-8") as out:
        out.write("=" * 100 + "\n")
        out.write("CLINICAL RAG PIPELINE BENCHMARK EVALUATION REPORT (100 QUESTIONS)\n")
        out.write("Automated Evaluation: Verified Source Answers vs RAG Pipeline Output\n")
        out.write("=" * 100 + "\n\n")
        out.write("EXECUTIVE SUMMARY METRICS:\n")
        out.write(f"  Total Questions Evaluated       : {total_q}\n")
        out.write(f"  Overall Verdict                 : {passed_q} / {total_q} PASS ({round(passed_q/total_q*100, 1)}% Pass Rate)\n")
        out.write(f"  Page Number Verification Rate   : {page_match_rate}% ({exact_pages} Exact, {partial_pages} Partial)\n")
        out.write(f"  Average Retrieval Accuracy      : {round(avg_retrieval * 100, 1)}%\n")
        out.write(f"  Average Answer Correctness      : {round(avg_correctness * 100, 1)}%\n")
        out.write(f"  Average Completeness Score      : {round(avg_completeness * 100, 1)}%\n")
        out.write(f"  Average Faithfulness Score      : {round(avg_faithfulness * 100, 1)}%\n")
        out.write(f"  Average Document Relevance      : {round(avg_relevance * 100, 1)}%\n")
        out.write(f"  Average Pipeline Latency        : {avg_duration}s per question\n")
        out.write(f"  Total Execution Duration        : {round(total_time/60, 2)} minutes\n")
        out.write("=" * 100 + "\n\n")

        # Category Breakdown Table
        categories = sorted(list(set(r["category"] for r in results)))
        out.write("PER-CATEGORY BREAKDOWN:\n")
        out.write(f"{'Category':<22} | {'Count':<6} | {'Pass Rate':<10} | {'Page Match':<10} | {'Correctness':<12} | {'Faithfulness':<12}\n")
        out.write("-" * 85 + "\n")
        for cat in categories:
            cat_items = [r for r in results if r["category"] == cat]
            c_count = len(cat_items)
            c_pass = sum(1 for r in cat_items if r["verdict"] == "PASS")
            c_page = sum(1 for r in cat_items if r["page_match_status"] in ("EXACT_MATCH", "PARTIAL_MATCH"))
            c_corr = sum(r["metrics"]["answer_correctness"] for r in cat_items) / c_count
            c_faith = sum(r["metrics"]["faithfulness"] for r in cat_items) / c_count
            out.write(f"{cat:<22} | {c_count:<6} | {round(c_pass/c_count*100, 1):<9}% | {round(c_page/c_count*100, 1):<9}% | {round(c_corr*100, 1):<11}% | {round(c_faith*100, 1):<11}%\n")
        out.write("=" * 100 + "\n\n")

        # Detailed Question by Question Audit
        out.write("DETAILED QUESTION-BY-QUESTION EVALUATION RESULTS:\n")
        out.write("=" * 100 + "\n\n")

        for r in results:
            out.write("-" * 100 + "\n")
            out.write(f"QUESTION ID: {r['id']} | CATEGORY: {r['category']} | VERDICT: {r['verdict']}\n")
            out.write("-" * 100 + "\n")
            out.write(f"QUESTION:\n  {r['question']}\n\n")
            out.write(f"TARGET SOURCE DOCUMENT:\n  {r['target_document']}\n\n")
            out.write("PAGE VERIFICATION AUDIT:\n")
            out.write(f"  - Expected Source Page(s) : {r['expected_pages']}\n")
            out.write(f"  - Retrieved Page(s)       : {r['retrieved_pages']}\n")
            out.write(f"  - Page Match Status       : {r['page_match_status']} ({r['page_audit_reason']})\n\n")
            out.write("EVALUATION METRICS:\n")
            m = r["metrics"]
            out.write(f"  - Retrieval Accuracy : {round(m['retrieval_accuracy']*100, 1)}%\n")
            out.write(f"  - Answer Correctness : {round(m['answer_correctness']*100, 1)}%\n")
            out.write(f"  - Completeness       : {round(m['completeness']*100, 1)}%\n")
            out.write(f"  - Faithfulness       : {round(m['faithfulness']*100, 1)}%\n")
            out.write(f"  - Document Relevance : {round(m['document_relevance']*100, 1)}%\n")
            out.write(f"  - Pipeline Latency   : {r['duration_seconds']}s\n")
            out.write(f"  - Failure Diagnostic : {r['failure_reasons']}\n\n")
            out.write("ACTUAL VERIFIED REFERENCE ANSWER (SOURCE DOCUMENT GROUND TRUTH):\n")
            out.write(f"  {r['verified_reference_answer']}\n\n")
            out.write("RAG PIPELINE GENERATED ANSWER:\n")
            out.write(f"  {r['rag_answer']}\n\n")

    print(f"\n========================================================")
    print(f"EVALUATION COMPLETE! Total Duration: {round(total_time/60, 2)} minutes.")
    print(f"Results saved to:")
    print(f"  - {os.path.abspath('evaluation_100_questions_report.json')}")
    print(f"  - {os.path.abspath(report_txt_path)}")
    print(f"========================================================\n")
    sys.stdout.flush()

if __name__ == "__main__":
    run_evaluation()
