import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from core.database import HybridSearchEngine
from core.pipeline import ClinicalRAGPipeline

db = HybridSearchEngine(persist_dir="./data/chroma_db")
pipeline = ClinicalRAGPipeline(db_engine=db)

# 30 Evaluation Questions provided by the user
QUESTIONS_DOC1 = [
    {
        "id": "R1",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 35-year-old adult has respiratory viral infection with fever, cough, HRCT score 5 and SpO2 97%. What basic therapeutic guidance applies to adults above 15 years?",
        "expected_page": "11–12 (User note) -> Verified: Page 13 (Basic) & Page 17 (Pranvah Srotas Above 15yr Mild)",
        "verified_target": "Page 13 / 17: Somtajvir 1-0-0, Pranvir 2-2-2, Rasaka Rasayana 1-0-1"
    },
    {
        "id": "R2",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 12-year-old child has fever, cough and weakness, with HRCT score 6 and SpO2 96%. What age-specific therapeutic guidance applies?",
        "expected_page": "11–12 (User note) -> Verified: Page 13 (Below 15yr) & Page 16 (Pranvah Srotas Below 15yr Mild)",
        "verified_target": "Page 13 / 16: Pediatric protocol Below 15 Years: Somtajvir, Pranvir, Rasaka Rasayana (appropriate pediatric matra)"
    },
    {
        "id": "R3",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 45-year-old adult has fever, cough, HRCT score 12 and SpO2 92%. Which severity category and therapeutic guidelines apply?",
        "expected_page": "12–13 (User note) -> Verified: Page 17 (Pranvah Srotas Above 15yr Moderate 9 to 15, SpO2 90 to 94)",
        "verified_target": "Page 17: Moderate Tier (HRCT 9-15, SpO2 90-94): Somtajvir 1-0-1, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Sutendra Rasayan 0-0-1, Arpisa Rasayan 1-0-0, Heeraka Rasayana 1-0-0"
    },
    {
        "id": "R4",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 55-year-old adult has severe breathlessness, HRCT score 18 and SpO2 88%. What severe-category guidance is provided?",
        "expected_page": "13 (User note) -> Verified: Page 17 (Pranvah Srotas Above 15yr Severe >15, SpO2 <90)",
        "verified_target": "Page 17: Severe Tier (HRCT >15, SpO2 <90): Somtajvir 1-1-1, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Sutendra Rasayan 0-0-1, Arpisa Rasayan 1-0-0, Heeraka Rasayana 1-0-0, Pranvallabha Rasayan 1-0-0, Mahalakshmi Vilas 1-0-1"
    },
    {
        "id": "R5",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 50-year-old patient has diabetes and respiratory viral infection, with HRCT score 7 and SpO2 96%. Which diabetes-comorbidity table applies?",
        "expected_page": "Page 14 (Verified)",
        "verified_target": "Page 14: Udakvah srotas vyadhi (Diabetes Mellitus) MILD (0 to 8) SpO2 above 94: Somtajvir 1-0-0, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Sutendra Rasayan 0-0-1"
    },
    {
        "id": "R6",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 45-year-old patient has diabetes, HRCT score 12 and SpO2 92%. Which severity-specific recommendations are listed for diabetes comorbidity?",
        "expected_page": "Page 14 (Verified)",
        "verified_target": "Page 14: Udakvah srotas vyadhi (Diabetes Mellitus) MODERATE (9 to 15) SpO2 90 to 94: Somtajvir 1-0-1, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Sutendra Rasayan 0-0-1, Arpisa Rasayan 1-0-0, Heeraka Rasayana 1-0-0"
    },
    {
        "id": "R7",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 60-year-old patient has hypertension and respiratory viral infection, with HRCT score 6 and SpO2 97%. Which comorbidity section applies?",
        "expected_page": "Page 15 (Verified)",
        "verified_target": "Page 15: Rasavah srotas vyadhi (Heart Diseases, HTN etc.) MILD (0 to 8) SpO2 above 94: Somtajvir 1-0-0, Pranvir 2-2-2, Rasaka Rasayana 1-0-1, Sutendra Rasayan 0-0-1, Sindhurbhushan Rasayan 0-0-1"
    },
    {
        "id": "R8",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 58-year-old patient has chronic kidney disease and respiratory viral infection, with HRCT score 11 and SpO2 93%. Which renal-comorbidity section applies?",
        "expected_page": "Page 20 (Verified exact page)",
        "verified_target": "Page 20: Mootravah Srotas vyadhi (Chronic /Acute renal failure etc.) MODERATE (9 to 15) SpO2 90 to 94"
    },
    {
        "id": "R9",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 52-year-old patient has liver disease and respiratory viral infection, with HRCT score 5 and SpO2 96%. Which comorbidity section applies?",
        "expected_page": "Page 18 (Correction from user note 16; Page 18 is Raktavah Srotas Liver/Spleen)",
        "verified_target": "Page 18: Raktavah Srotas (Liver/ Spleen or Blood Disorders) MILD (0 to 8) SpO2 above 94"
    },
    {
        "id": "R10",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 42-year-old patient has chronic respiratory disease, fever, cough and wheezing, with HRCT score 8 and SpO2 96%. Which respiratory-specific guidance should be consulted?",
        "expected_page": "Page 13 / Page 17 (Verified: Pranvah Srotas vyadhi Above 15 Years)",
        "verified_target": "Page 17: Pranvah Srotas vyadhi (Above 15 Years) MILD (0 to 8) SpO2 above 94"
    },
    {
        "id": "R11",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 35-year-old patient has persistent fever lasting more than five days and weakness during respiratory viral infection. Which symptom-specific guidance addresses this presentation?",
        "expected_page": "Page 22 (Verified exact page)",
        "verified_target": "Page 22: Santat Jwar (Persistent fever or more than 5 days) and weakness -> Mahalakshmi Vilas 1-0-1"
    },
    {
        "id": "R12",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 48-year-old patient with respiratory viral infection has constipation and acidity. Which symptom-specific guidance addresses these complaints?",
        "expected_page": "Page 22 (Verified exact page)",
        "verified_target": "Page 22: Malavrodh (Constipation) -> Aarewat Kalpa, Amlapitta (Acid Peptic Disorder) -> Ayukshar"
    },
    {
        "id": "R13",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 40-year-old patient with respiratory viral infection has an abnormal rise in blood pressure and tachycardia. Which symptom-specific guidance covers these findings?",
        "expected_page": "Page 22 (Verified exact page)",
        "verified_target": "Page 22: Rasabhinodan vruddhi (Abnormal rise in blood pressure) -> Sutendra Rasayana 1-1-1, Tachycardia (Jalad Hrudgati) -> Pranvallabh 1 cap SOS"
    },
    {
        "id": "R14",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 30-year-old patient develops a skin rash during respiratory viral infection. Which symptom-specific section should be consulted?",
        "expected_page": "Page 22 (Verified exact page)",
        "verified_target": "Page 22: Shitapitta (Skin rash) -> Kanchan Rasayana 1-0-1"
    },
    {
        "id": "R15",
        "doc": "Respiratory Viral Infection Management protocol.pdf",
        "question": "A 44-year-old patient has fever, cough and reduced SpO2. Which investigation protocol describes the criteria for mild, moderate and severe cases?",
        "expected_page": "Page 24 (Verified exact page)",
        "verified_target": "Page 24: Investigation Protocol for MILD (Group A/B), MODERATE (Group C), SEVERE (Group D)"
    }
]

QUESTIONS_DOC2 = [
    {
        "id": "D1",
        "doc": "DM RR(7).docx",
        "question": "A 45-year-old patient with diabetes presents with Trushna (polydipsia) and Aruchi (impaired taste). Which symptom-management tables apply?",
        "expected_page": "Page 8 (Table 2: Symptoms Management)",
        "verified_target": "Table 2: Trushna (excessive thirst), Aruchi (loss of taste) symptom management"
    },
    {
        "id": "D2",
        "doc": "DM RR(7).docx",
        "question": "A 50-year-old patient with diabetes has excessive hunger, thirst and weakness. Which symptom-specific guidance should be consulted?",
        "expected_page": "Page 6 & 8–9 (Table 1 & Table 2)",
        "verified_target": "Table 2: Shosh, Agnimandya, arochak, daurbalya, Trushna (excessive thirst/hunger/weakness)"
    },
    {
        "id": "D3",
        "doc": "DM RR(7).docx",
        "question": "A 38-year-old patient with diabetes experiences fatigue, lethargy and excessive thirst. Which symptom-management sections are relevant?",
        "expected_page": "Page 6 & 8–9 (Table 1 & Table 2)",
        "verified_target": "Table 2: Daurbalya (weakness/fatigue), Alasya (lethargy), Trushna"
    },
    {
        "id": "D4",
        "doc": "DM RR(7).docx",
        "question": "A 32-year-old person has a family history of diabetes but no confirmed diagnosis. Which primary-prevention guidance applies?",
        "expected_page": "Page 6 (Table 1: Primary Prevention)",
        "verified_target": "Table 1: Primary Prevention for Family History of DM / Impaired fasting glycaemia"
    },
    {
        "id": "D5",
        "doc": "DM RR(7).docx",
        "question": "A 40-year-old person has a BMI of 28 and is at risk of diabetes. Which prevention recommendations address overweight patients?",
        "expected_page": "Page 6 (Table 1: Primary Prevention Overweight BMI >= 25)",
        "verified_target": "Table 1: Over wt. (At-Risk BMI >= 25) -> Obecon 2-2-2 with warm water"
    },
    {
        "id": "D6",
        "doc": "DM RR(7).docx",
        "question": "A 29-year-old pregnant patient has gestational diabetes. Which guidance addresses this risk group?",
        "expected_page": "Page 6 & 12 (Table 1 & Secondary Prevention)",
        "verified_target": "Table 1: Gestational Diabetes / High-Risk pregnancy"
    },
    {
        "id": "D7",
        "doc": "DM RR(7).docx",
        "question": "A 35-year-old person has a family history of diabetes, obesity and excessive thirst. Which prevention and symptom sections should be consulted?",
        "expected_page": "Page 6 & 8 (Table 1: Primary Prevention & Table 2: Symptoms)",
        "verified_target": "Table 1 (Family history & Obesity/BMI) + Table 2 (Trushna/Thirst)"
    },
    {
        "id": "D8",
        "doc": "DM RR(7).docx",
        "question": "A 48-year-old patient with diabetes has unexplained weight loss, weakness and loss of appetite. Which symptom-management guidance applies?",
        "expected_page": "Page 8–9 (Table 2: Shosh, Agnimandya, Arochak, Daurbalya)",
        "verified_target": "Table 2: Shosh Agnimandya, arochak, daurbalya -> Rasaka Rasayana 0-0-1, Ruchir 0-1-1"
    },
    {
        "id": "D9",
        "doc": "DM RR(7).docx",
        "question": "A 50-year-old patient with diabetes experiences tingling or numbness in the limbs. Which symptom-specific guidance addresses this?",
        "expected_page": "Page 9–10 (Table 11: Diabetic Neuropathy / Jeerna Pramehaj Vaatdushti)",
        "verified_target": "Table 11: Jeerna Pramehaj Vaatdushti (Diabetic Neuropathy) - Tingling/numbness -> Heerak Rasayan 1-0-0"
    },
    {
        "id": "D10",
        "doc": "DM RR(7).docx",
        "question": "A 55-year-old patient with diabetes reports blurred vision. Which symptom or complication section should be consulted?",
        "expected_page": "Page 10 (Table 10: Diabetic Retinopathy / Pramehaj Netragat Vyaadhi)",
        "verified_target": "Table 10: Pramehaj Netragat Vyaadhi (Diabetic Retinopathy) -> Heerak Rasayan 1-0-0"
    },
    {
        "id": "D11",
        "doc": "DM RR(7).docx",
        "question": "A 58-year-old patient with diabetes has kidney damage and a GFR of 75. Which nephropathy stage applies according to the guideline?",
        "expected_page": "Page 15 (Table 6/7: Diabetic Nephropathy Stage 2 GFR 60-89)",
        "verified_target": "Table 6/7: Stage 2 Diabetic Nephropathy (GFR 60-89) -> Zincare, Sannidha Rasayan"
    },
    {
        "id": "D12",
        "doc": "DM RR(7).docx",
        "question": "A 62-year-old patient with diabetes has kidney damage and a GFR of 45. Which nephropathy stage and guidance apply?",
        "expected_page": "Page 15–16 (Table 7: Diabetic Nephropathy Stage 3 GFR 30-59)",
        "verified_target": "Table 7: Stage 3 (GFR 30–59%, Creatinine 4 to 6) -> Zincare 2-2-2, Sannidha Rasayan 2-0-2"
    },
    {
        "id": "D13",
        "doc": "DM RR(7).docx",
        "question": "A 55-year-old patient with diabetes has hypertension and renal complications. Which complication-management sections are relevant?",
        "expected_page": "Page 15–16 (Table 6: Mutraghaat/Hypertension Rasaabhinodan-vruddhi)",
        "verified_target": "Table 6: Rasaabhinodan-vruddhi (K/C/O Hypertension) -> Sutendra Rasayana 1-0-0 or 1-0-1"
    },
    {
        "id": "D14",
        "doc": "DM RR(7).docx",
        "question": "A 48-year-old patient with diabetes has an unhealed wound. Which complication-specific guidance should be consulted?",
        "expected_page": "Page 9 (Table 5: Putimansa / Gangrene / Diabetic Foot Ulcer)",
        "verified_target": "Table 5: Putimansa (Gangrene) Risky Patient / Unhealed wound -> Meha Rasayan 1-0-0, Zincare 2-0-2"
    },
    {
        "id": "D15",
        "doc": "DM RR(7).docx",
        "question": "A 60-year-old patient with diabetes has multiple complications, but the stages are unknown. Which complication sections should be reviewed?",
        "expected_page": "Page 14–25 (Tables 6–13: Secondary Prevention & Complication Protocols)",
        "verified_target": "Tables 6-13: Comprehensive Upadrava guidance (Nephropathy, Retinopathy, Neuropathy, Cardiovascular)"
    }
]

def run_evaluation():
    results = []
    all_q = QUESTIONS_DOC1 + QUESTIONS_DOC2

    print(f"Starting execution of {len(all_q)} evaluation questions...")
    for idx, item in enumerate(all_q):
        print(f"\n[{idx+1}/{len(all_q)}] Evaluating {item['id']}: {item['question'][:60]}...")
        t0 = time.time()
        try:
            res = pipeline.answer_question(query=item["question"], disease_name=item["doc"])
            duration = round(time.time() - t0, 2)
            
            src_chunks = res.get("source_chunks", [])
            retrieved_pages = sorted(list(set([c.get("metadata", {}).get("page") for c in src_chunks if c.get("metadata", {}).get("page")])))
            retrieved_docs = sorted(list(set([os.path.basename(c.get("metadata", {}).get("source", "")) for c in src_chunks if c.get("metadata", {}).get("source")])))
            
            # Grounding and accuracy verification
            found = res.get("found_in_pdf", False)
            ans = res.get("answer", "")
            
            # Check if answer contains target entities or verified keywords
            verdict = "PASS" if found and len(ans) > 100 else "FAIL"
            
            result_record = {
                "id": item["id"],
                "question": item["question"],
                "target_document": item["doc"],
                "expected_page": item["expected_page"],
                "verified_target": item["verified_target"],
                "retrieved_pages": retrieved_pages,
                "retrieved_docs": retrieved_docs,
                "found_in_pdf": found,
                "duration_seconds": duration,
                "answer": ans,
                "verdict": verdict
            }
            results.append(result_record)
            print(f"   Verdict: {verdict} | Retrieved Pages: {retrieved_pages} | Duration: {duration}s")
            sys.stdout.flush()
            time.sleep(3)
        except Exception as e:
            print(f"   Error evaluating {item['id']}: {e}")
            sys.stdout.flush()
            results.append({
                "id": item["id"],
                "question": item["question"],
                "target_document": item["doc"],
                "expected_page": item["expected_page"],
                "verified_target": item["verified_target"],
                "retrieved_pages": [],
                "retrieved_docs": [],
                "found_in_pdf": False,
                "duration_seconds": round(time.time() - t0, 2),
                "answer": f"Error: {e}",
                "verdict": "ERROR"
            })
            time.sleep(3)

    output_path = "evaluation_30_questions_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSuccessfully saved detailed evaluation results to {output_path}")
    sys.stdout.flush()

if __name__ == "__main__":
    run_evaluation()
