import logging
logging.basicConfig(level=logging.DEBUG)

from core.database import HybridSearchEngine
from core.pipeline import ClinicalRAGPipeline

db = HybridSearchEngine(persist_dir='./data/chroma_db')
pipe = ClinicalRAGPipeline(db)

q = "A patient has respiratory viral infection and severe diabetic nephropathy with GFR under 30. How do the renal guidelines in the respiratory protocol compare with Diabetic Nephropathy Stage 4/5 in the diabetes protocol?"
res = pipe.answer_question(q, disease_name="Cross-Document")
print("RESULT:", res)
