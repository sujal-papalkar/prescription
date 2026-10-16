from core.database import HybridSearchEngine
from core.pipeline import ClinicalRAGPipeline
from google.genai import types

db = HybridSearchEngine()
p = ClinicalRAGPipeline(db_engine=db)

q = "What are the recommended medicines and matra for a patient with respiratory viral infection having cardiac ailments or hypertension (Rasavah srotas vyadhi) with HRCT score 9 and SpO2 97?"

d = "Respiratory Viral Infection Management prorocol FINAL version converted 1 25"

chunks = db.hybrid_retrieve(q, disease_name=d, top_k=12)
print("Retrieved chunks:", len(chunks), "Contains 263:", any("263" in c["chunk_id"] for c in chunks))

context_str = "\n\n".join([
    f"[Excerpt {i+1} | Source: {c.get('metadata', {}).get('source', 'PDF')} | Page: {c.get('metadata', {}).get('page', 1)}]:\n{c['text']}"
    for i, c in enumerate(chunks)
])

prompt = f"""You are an objective Clinical Decision Support Assistant.
Answer the user's clinical question strictly using the provided excerpts from the uploaded document(s).

CRITICAL CLINICAL & DOCUMENT RULES:
1. Strict Grounding:
   - Base your answer ONLY on the provided document excerpts.
   - If the requested information is not mentioned or cannot be determined from the excerpts, respond EXACTLY: "Not mentioned in the PDF."
   - Do NOT guess, infer, extrapolate, or introduce outside medical information.

2. Objective Clinical Decision Support (Let the Attending Doctor Decide):
   - You are a clinical decision support tool; you do NOT make executive clinical choices for the physician or decide which option is "better".
   - When the patient's clinical presentation, test scores, or vitals match or cross MULTIPLE tiers/categories in the document (for example, imaging score corresponds to one tier while oxygen saturation/vitals corresponds to another tier):
     a) State the clinical observation objectively: explain which parameter corresponds to which guideline tier.
     b) Present the matching protocols for BOTH options clearly labeled:
        - Option 1: Protocol corresponding to the first parameter (e.g. Based on HRCT Score 9: Moderate Tier [9 to 15])
        - Option 2: Protocol corresponding to the second parameter (e.g. Based on SpO2 97%: Mild Tier [Above 94%])
     c) For each option, provide the exact medications, doses (matra), timings, and vehicles in a standard Markdown table.
     d) Explicitly state that the attending doctor/physician should determine which protocol is appropriate based on the patient's overall clinical presentation and assessment.

3. Standard Markdown Table Requirement:
   Format every protocol option using a clean Markdown table:
   | MEDICINE / FORMULATION | DOSE / MATRA | FREQUENCY | TIMING / AUSHADH KAL | DURATION | ANUPANA / SAHAPAAN | SOURCE DOCUMENT | PAGE |
   (If frequency or duration is not stated in the excerpt, write "Not specified").
   Always cite the exact SOURCE DOCUMENT and PAGE from the excerpt header.

USER QUESTION:
{q}

DOCUMENT EXCERPTS:
{context_str}
"""

res = p.genai_client.models.generate_content(
    model="gemini-flash-lite-latest",
    contents=prompt,
    config=types.GenerateContentConfig(temperature=0.0)
)
print("=== GENERATED CDSS OUTPUT ===\n", res.text)

