import json
import time
import os
import sys

from run_100_evaluation import QUESTIONS_100, evaluate_single_response
from core.database import HybridSearchEngine
from core.pipeline import ClinicalRAGPipeline

db = HybridSearchEngine(persist_dir='./data/chroma_db')
pipe = ClinicalRAGPipeline(db)

# Load existing 100 questions report
with open('evaluation_100_questions_report.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# Re-evaluate C01 to C10
c_items = {q['id']: q for q in QUESTIONS_100 if q['id'].startswith('C')}
for i, r in enumerate(results):
    if r['id'] in c_items:
        q_item = c_items[r['id']]
        t0 = time.time()
        try:
            res = pipe.answer_question(q_item['question'], disease_name='Cross-Document')
            dur = round(time.time() - t0, 2)
            ev = evaluate_single_response(q_item, res, dur)
            results[i] = ev
            print(f"Updated {r['id']}: {ev['verdict']} | Pages: {ev['retrieved_pages']}")
        except Exception as e:
            print(f"Error on {r['id']}: {e}")

# Save updated JSON
with open('evaluation_100_questions_report.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Compute Aggregates
total_q = len(results)
passed_q = sum(1 for r in results if r['verdict'] == 'PASS')
exact_pages = sum(1 for r in results if r['page_match_status'] == 'EXACT_MATCH')
partial_pages = sum(1 for r in results if r['page_match_status'] == 'PARTIAL_MATCH')
page_match_rate = round((exact_pages + partial_pages) / total_q * 100, 1)

avg_retrieval = round(sum(r['metrics']['retrieval_accuracy'] for r in results) / total_q, 3)
avg_correctness = round(sum(r['metrics']['answer_correctness'] for r in results) / total_q, 3)
avg_completeness = round(sum(r['metrics']['completeness'] for r in results) / total_q, 3)
avg_faithfulness = round(sum(r['metrics']['faithfulness'] for r in results) / total_q, 3)
avg_relevance = round(sum(r['metrics']['document_relevance'] for r in results) / total_q, 3)
avg_duration = round(sum(r['duration_seconds'] for r in results) / total_q, 2)

report_txt_path = 'evaluation_results_100_questions.txt'
with open(report_txt_path, 'w', encoding='utf-8') as out:
    out.write('=' * 100 + '\n')
    out.write('CLINICAL RAG PIPELINE BENCHMARK EVALUATION REPORT (100 QUESTIONS)\n')
    out.write('Automated Evaluation: Verified Source Answers vs RAG Pipeline Output\n')
    out.write('=' * 100 + '\n\n')
    out.write('EXECUTIVE SUMMARY METRICS:\n')
    out.write(f'  Total Questions Evaluated       : {total_q}\n')
    out.write(f'  Overall Verdict                 : {passed_q} / {total_q} PASS ({round(passed_q/total_q*100, 1)}% Pass Rate)\n')
    out.write(f'  Page Number Verification Rate   : {page_match_rate}% ({exact_pages} Exact, {partial_pages} Partial)\n')
    out.write(f'  Average Retrieval Accuracy      : {round(avg_retrieval * 100, 1)}%\n')
    out.write(f'  Average Answer Correctness      : {round(avg_correctness * 100, 1)}%\n')
    out.write(f'  Average Completeness Score      : {round(avg_completeness * 100, 1)}%\n')
    out.write(f'  Average Faithfulness Score      : {round(avg_faithfulness * 100, 1)}%\n')
    out.write(f'  Average Document Relevance      : {round(avg_relevance * 100, 1)}%\n')
    out.write(f'  Average Pipeline Latency        : {avg_duration}s per question\n')
    out.write('=' * 100 + '\n\n')

    # Category Breakdown Table
    categories = sorted(list(set(r['category'] for r in results)))
    out.write('PER-CATEGORY BREAKDOWN:\n')
    out.write(f'{"Category":<22} | {"Count":<6} | {"Pass Rate":<10} | {"Page Match":<10} | {"Correctness":<12} | {"Faithfulness":<12}\n')
    out.write('-' * 85 + '\n')
    for cat in categories:
        cat_items = [r for r in results if r['category'] == cat]
        c_count = len(cat_items)
        c_pass = sum(1 for r in cat_items if r['verdict'] == 'PASS')
        c_page = sum(1 for r in cat_items if r['page_match_status'] in ('EXACT_MATCH', 'PARTIAL_MATCH'))
        c_corr = sum(r['metrics']['answer_correctness'] for r in cat_items) / c_count
        c_faith = sum(r['metrics']['faithfulness'] for r in cat_items) / c_count
        out.write(f'{cat:<22} | {c_count:<6} | {round(c_pass/c_count*100, 1):<9}% | {round(c_page/c_count*100, 1):<9}% | {round(c_corr*100, 1):<11}% | {round(c_faith*100, 1):<11}%\n')
    out.write('=' * 100 + '\n\n')

    # Detailed Question by Question Audit
    out.write('DETAILED QUESTION-BY-QUESTION EVALUATION RESULTS:\n')
    out.write('=' * 100 + '\n\n')

    for r in results:
        out.write('-' * 100 + '\n')
        out.write(f'QUESTION ID: {r["id"]} | CATEGORY: {r["category"]} | VERDICT: {r["verdict"]}\n')
        out.write('-' * 100 + '\n')
        out.write(f'QUESTION:\n  {r["question"]}\n\n')
        out.write(f'TARGET SOURCE DOCUMENT:\n  {r["target_document"]}\n\n')
        out.write('PAGE VERIFICATION AUDIT:\n')
        out.write(f'  - Expected Source Page(s) : {r["expected_pages"]}\n')
        out.write(f'  - Retrieved Page(s)       : {r["retrieved_pages"]}\n')
        out.write(f'  - Page Match Status       : {r["page_match_status"]} ({r["page_audit_reason"]})\n\n')
        out.write('EVALUATION METRICS:\n')
        m = r['metrics']
        out.write(f'  - Retrieval Accuracy : {round(m["retrieval_accuracy"]*100, 1)}%\n')
        out.write(f'  - Answer Correctness : {round(m["answer_correctness"]*100, 1)}%\n')
        out.write(f'  - Completeness       : {round(m["completeness"]*100, 1)}%\n')
        out.write(f'  - Faithfulness       : {round(m["faithfulness"]*100, 1)}%\n')
        out.write(f'  - Document Relevance : {round(m["document_relevance"]*100, 1)}%\n')
        out.write(f'  - Pipeline Latency   : {r["duration_seconds"]}s\n')
        out.write(f'  - Failure Diagnostic : {r["failure_reasons"]}\n\n')
        out.write('ACTUAL VERIFIED REFERENCE ANSWER (SOURCE DOCUMENT GROUND TRUTH):\n')
        out.write(f'  {r["verified_reference_answer"]}\n\n')
        out.write('RAG PIPELINE GENERATED ANSWER:\n')
        out.write(f'  {r["rag_answer"]}\n\n')

# Also copy to medical_rag_app root for user convenience
root_report = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'evaluation_results_100_questions.txt')
with open(root_report, 'w', encoding='utf-8') as f:
    with open(report_txt_path, 'r', encoding='utf-8') as src:
        f.write(src.read())

print(f"Report generation complete: {passed_q}/{total_q} PASS ({round(passed_q/total_q*100, 1)}%). Page Match: {page_match_rate}%.")
