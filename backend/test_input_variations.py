"""
Comprehensive Clinical Input Variation Evaluation Suite.
Tests diverse real-world variations:
- Exact numerical values instead of ranges (e.g. HRCT 10, SpO2 93%, HRCT 5, SpO2 96%, HRCT 17, SpO2 88%)
- Clinical synonyms instead of technical Sanskrit terminology
- Colloquial doctor/patient phrasing
- Complication and comorbidity bridging
- Strict negative controls (allopathic drugs)
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(PARENT_DIR, ".env"))
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("variation_evaluator")

from core.database import HybridSearchEngine
from core.pipeline import ClinicalRAGPipeline

db = HybridSearchEngine()
pipeline = ClinicalRAGPipeline(db_engine=db)

VARIATION_TEST_CASES = [
    {
        "id": "VAR-01",
        "category": "Numeric Value instead of Range (Moderate Cardiac)",
        "query": "What are the recommended medicines and matra for a patient with respiratory viral infection having cardiac ailments or hypertension (Rasavah srotas vyadhi) with moderate HRCT score 10 and SpO2 93%?",
        "expected_page": 15,
        "expected_medicines": ["Somtajvir", "Pranvir", "Rasaka Rasayana", "Sutendra", "Arpisa", "Heeraka"],
        "is_negative": False
    },
    {
        "id": "VAR-02",
        "category": "Numeric Value + Colleague Phrasing (Mild Diabetic)",
        "query": "Prescription for an adult with respiratory infection and high blood sugar comorbidity, his CT scan score is 5 and O2 saturation is 96%.",
        "expected_page": 14,
        "expected_medicines": ["Somtajvir", "Pranvir", "Rasaka Rasayana", "Meha Rasayan"],
        "is_negative": False
    },
    {
        "id": "VAR-03",
        "category": "Numeric Value + Severity Phrasing (Severe Cardiac)",
        "query": "What are the urgent Ayurvedic medicines for a severe viral respiratory patient with heart disease having HRCT 17 and SpO2 88%?",
        "expected_page": 15,
        "expected_medicines": ["Somtajvir", "Pranvir", "Rasaka Rasayana", "Mahalakshmi Vilas"],
        "is_negative": False
    },
    {
        "id": "VAR-04",
        "category": "Colloquial Symptom Phrasing (Persistent Fever & Weakness)",
        "query": "What medicine and anupana should be given to a patient suffering from persistent fever for 6 days accompanied by intense weakness and fatigue?",
        "expected_page": 22,
        "expected_medicines": ["Mahalakshmi Vilas"],
        "is_negative": False
    },
    {
        "id": "VAR-05",
        "category": "Clinical Complication Synonym (Tachycardia / Fast Pulse)",
        "query": "If a patient develops tachycardia (fast pulse rate) or sudden rise in BP during viral respiratory illness, which formulation is indicated?",
        "expected_page": 22,
        "expected_medicines": ["Pranvallabh"],
        "is_negative": False
    },
    {
        "id": "VAR-06",
        "category": "Oncology Prophylaxis Synonym (Chemotherapy / Radiotherapy)",
        "query": "Immunity booster formulations for a cancer patient currently taking radiation or chemotherapy to prevent viral respiratory infection.",
        "expected_page": 7,
        "expected_medicines": ["Rasvir", "Pranvir", "Rasaka Rasayana"],
        "is_negative": False
    },
    {
        "id": "VAR-07",
        "category": "DOCX Symptom Translation (Appetite Loss & Weight Loss)",
        "query": "According to DM RR protocol, what should be prescribed for extreme emaciation, loss of appetite, indigestion and severe weakness in diabetic patients?",
        "expected_page": 2,
        "expected_medicines": ["Rasaka Rasayana"],
        "is_negative": False
    },
    {
        "id": "VAR-08",
        "category": "Strict Negative Control (Allopathic Medications)",
        "query": "What is the prescribed dosage of Dexamethasone 6mg and Favipiravir 800mg in the respiratory guideline?",
        "expected_page": None,
        "expected_medicines": [],
        "is_negative": True
    }
]

def run_variation_evaluation():
    print("=" * 80)
    print("STARTING CLINICAL INPUT VARIATION EVALUATION SUITE")
    print(f"Total Test Cases: {len(VARIATION_TEST_CASES)}")
    print("=" * 80)

    results = []
    total_med_recall = 0.0
    page_matches = 0
    neg_control_passed = 0
    total_non_neg = sum(1 for tc in VARIATION_TEST_CASES if not tc["is_negative"])

    for idx, tc in enumerate(VARIATION_TEST_CASES):
        print(f"\n--- Running [{tc['id']}] {tc['category']} ---")
        print(f"Query: {tc['query']}")

        t0 = time.time()
        res = pipeline.answer_question(query=tc["query"])
        elapsed = time.time() - t0

        answer = res.get("answer", "")
        found_in_pdf = res.get("found_in_pdf", False)
        source_chunks = res.get("source_chunks", [])
        retrieved_pages = [c.get("metadata", {}).get("page") for c in source_chunks if c.get("metadata", {}).get("page")]

        # Negative control check
        if tc["is_negative"]:
            passed_neg = (not found_in_pdf) or ("not mentioned in the pdf" in answer.lower())
            if passed_neg:
                neg_control_passed += 1
            med_recall = 1.0 if passed_neg else 0.0
            page_match = True
            print(f"Negative Control Passed: {passed_neg} (Answer: '{answer[:60]}...')")
        else:
            # Medicine Recall Calculation
            expected_meds = tc["expected_medicines"]
            found_meds = [m for m in expected_meds if m.lower() in answer.lower()]
            med_recall = len(found_meds) / len(expected_meds) if expected_meds else 1.0
            total_med_recall += med_recall

            # Page Match
            page_match = (tc["expected_page"] in retrieved_pages) if retrieved_pages else False
            if page_match:
                page_matches += 1

            print(f"Medicines Found: {found_meds}/{expected_meds} ({med_recall*100:.1f}%)")
            print(f"Target Page: {tc['expected_page']} | Retrieved Pages: {retrieved_pages} | Page Match: {page_match}")

        results.append({
            "id": tc["id"],
            "category": tc["category"],
            "query": tc["query"],
            "expected_page": tc["expected_page"],
            "retrieved_pages": retrieved_pages,
            "page_match": page_match,
            "expected_medicines": tc["expected_medicines"],
            "medicine_recall": med_recall,
            "answer_preview": answer[:250],
            "elapsed_sec": round(elapsed, 2)
        })

    avg_med_recall = (total_med_recall / total_non_neg) * 100.0 if total_non_neg else 100.0
    page_acc = (page_matches / total_non_neg) * 100.0 if total_non_neg else 100.0
    anti_hallucination = (neg_control_passed / 1.0) * 100.0

    print("\n" + "=" * 80)
    print("VARIATION EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Average Medicine Recall: {avg_med_recall:.1f}%")
    print(f"Source Page Attribution Accuracy: {page_acc:.1f}%")
    print(f"Anti-Hallucination Compliance: {anti_hallucination:.1f}%")

    # Generate Markdown Report
    report_lines = [
        "# Clinical Input Variation Benchmark Report",
        "",
        "## Summary Metrics",
        f"- **Prescription Medicine Recall**: **{avg_med_recall:.1f}%**",
        f"- **Source Page Attribution Accuracy**: **{page_acc:.1f}%**",
        f"- **Anti-Hallucination Compliance**: **{anti_hallucination:.1f}%**",
        "",
        "## Detailed Test Cases Breakdown",
        ""
    ]

    for r in results:
        report_lines.extend([
            f"### [{r['id']}] {r['category']}",
            f"- **User Query**: *\"{r['query']}\"*",
            f"- **Target Page**: `{r['expected_page']}` | **Retrieved Pages**: `{r['retrieved_pages']}` | **Page Match**: `{'PASSED' if r['page_match'] else 'FAILED'}`",
            f"- **Medicine Recall**: `{r['medicine_recall']*100:.1f}%`",
            f"- **Answer Excerpt**:\n```markdown\n{r['answer_preview']}...\n```",
            ""
        ])

    report_md = "\n".join(report_lines)
    out_path = os.path.join(BASE_DIR, "input_variation_benchmark_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"\n[SUCCESS] Saved variation benchmark report to: {out_path}")

if __name__ == "__main__":
    run_variation_evaluation()
