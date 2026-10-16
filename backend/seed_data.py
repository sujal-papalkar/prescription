"""
Seed Clinical Guidelines Generator
Creates realistic Ayurvedic Clinical Guideline PDFs with complex tabular matrices
and structured prose sections to validate the end-to-end ingestion and RAG pipeline.
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


SAMPLE_GUIDELINES = {
    "Respiratory Viral Infections": {
        "title": "Clinical Practice Guideline: Ayurvedic Management of Acute Respiratory Infections (Kasa & Shwasa)",
        "tables": [
            {
                "caption": "Table 1: Age-Stratified Prescription Matrix for Acute Vata-Kaphaja Kasa",
                "headers": ["Age Bracket", "Severity State", "Formulation (Aushadha)", "Matra (Dosage)", "Sahpaan (Vehicle)", "Aushadh Kal (Timing)"],
                "rows": [
                    ["Pediatric (3-12 yrs)", "Mild Catarrh", "Sitopaladi Churna", "1 gram twice daily", "Madhu (Honey)", "Pragbhakta (Before meals)"],
                    ["Pediatric (3-12 yrs)", "Moderate Cough with Phlegm", "Talishadi Churna", "1.5 grams twice daily", "Warm Water with Honey", "Vyan Kale (After meals)"],
                    ["Adult (18-60 yrs)", "Acute Productive Kasa", "Tribhuvankirti Rasa", "125 mg twice daily", "Ardraka Swarasa (Ginger Juice)", "Adhobhakta (After meals)"],
                    ["Adult (18-60 yrs)", "Severe Spasmodic Cough", "Shwas Kuthar Rasa", "125 mg thrice daily", "Warm Water with Pippali", "Nishi (Bedtime) & Post-meals"],
                    ["Adult (18-60 yrs)", "Bronchospasm with Dyspnea", "Kantakaryavaleha", "10 grams twice daily", "Luke warm water", "Pratahkal & Sandhyakal"],
                    ["Geriatric (>60 yrs)", "Chronic Kaphaja Shwasa", "Agastya Haritaki Rasayana", "6 grams twice daily", "Warm Godugdha (Cow Milk)", "Pragbhakta (Morning on empty stomach)"]
                ]
            }
        ],
        "prose": """
# Clinical Practice Guideline: Acute Respiratory Infections

## 1. Disease Definition & Nidana (Etiology)
Kasa and Shwasa represent acute and chronic inflammatory disorders of the Pranavaha Srotas. The primary causative factors include exposure to dust (Dhuma), cold wind (Vata), suppression of natural urges (Vega Dharana), and intake of Sheeta and Ruksha Ahara.

## 2. Pathophysiology (Samprapti)
Vata dosha, specifically Prana Vata, becomes obstructed by aggravated Kapha dosha in the chest (Uras). The retrograde movement of Vata produces the sound resembling broken bronze (Kamsya Patra), manifesting as coughing paroxysms, thoracic pain, and laboured respiration.

## 3. Clinical Warning Flags & Red Flags
- SpO2 below 93% on room air mandates immediate hospital admission.
- High fever exceeding 102°F persisting over 72 hours requires screening for secondary bacterial bronchopneumonia.
- Hemoptysis (Urakshata) contraindicates heating formulations such as Shwas Kuthar Rasa and requires immediate Pitta-Shamana hemostatic therapy.

## 4. Dietary Regimen (Pathya & Apathya)
### Pathya (Beneficial)
- Warm water (Ushnodaka) for drinking.
- Old Shali rice, Kulattha (horsegram soup), and Yava (barley).
- Spices: Ardraka (fresh ginger), Maricha (black pepper), and Lasuna (garlic).

### Apathya (Strictly Prohibited)
- Cold refrigerated drinks, curd (Dadhi), and heavy sweets.
- Day-time sleep (Divaaswapna) which severely aggravates Kapha dosha.
- Direct exposure to air conditioning drafts.
"""
    },
    "Prameh / Diabetes Mellitus": {
        "title": "Clinical Practice Guideline: Management of Prameha (Type 2 Diabetes Mellitus)",
        "tables": [
            {
                "caption": "Table 2: Clinical Prescription Matrix for Kaphaja and Medoroga-associated Prameha",
                "headers": ["Clinical Stage", "Fasting Glucose Bracket", "Primary Medicine", "Matra (Dosage)", "Sahpaan (Vehicle)", "Aushadh Kal (Timing)"],
                "rows": [
                    ["Impaired Fasting (Prediabetes)", "100-125 mg/dL", "Nisha Amalaki Churna", "3 grams twice daily", "Luke warm water", "Pratah (Empty stomach)"],
                    ["Uncomplicated Established", "126-180 mg/dL", "Chandraprabha Vati", "500 mg twice daily", "Shilajit Kwatha / Warm water", "Adhobhakta (After meals)"],
                    ["Established with Dyslipidemia", "140-200 mg/dL", "Phalatrikadi Kwatha", "30 ml with equal water", "Honey (one teaspoon)", "Pragbhakta (Before meals)"],
                    ["Chronic with Neuropathy", ">200 mg/dL or long duration", "Vasant Kusumakar Rasa", "125 mg once daily", "Godugdha (Cow milk)", "Pratahkal (Morning)"],
                    ["Prameha with Microalbuminuria", "Any with proteinuria", "Gokshuradi Guggulu", "500 mg thrice daily", "Pashanbhed Kwatha", "Vyan Kale (After meals)"]
                ]
            }
        ],
        "prose": """
# Clinical Practice Guideline: Management of Prameha

## 1. Overview & Classification
Prameha is characterized by frequent, turbid micturition (Prabhoota Aavil Mootrata). It is classified into 20 sub-varieties, with 10 Kaphaja, 6 Pittaja, and 4 Vataja variants. Untreated Kaphaja and Pittaja stages eventually transition into irreversible Vataja Prameha (Madhumeha).

## 2. Diagnostic & Laboratory Criteria
- Fasting Blood Sugar (FBS) >= 126 mg/dL or HbA1c >= 6.5%.
- Assessment of Dushya: Meda (adipose tissue), Mamsa (muscle tissue), and Kleda (body fluid accumulation).

## 3. Clinical Warning Flags
- Patients presenting with diabetic foot ulcers or severe peripheral neuropathy require integrated wound care.
- Caution is advised when administering hypoglycemic herbal formulations concurrently with Metformin or Sulfonylureas to prevent sudden hypoglycemia.
- In patients with estimated GFR < 30 mL/min, Herbo-mineral preparations (Rasaushadhis) containing metallic bhasmas must be strictly monitored or substituted with aqueous decoctions.

## 4. Pathya & Apathya Protocol
### Pathya
- Yava (barley), Mudga (green gram), and Tikta Shaka (bitter vegetables like Karela/bitter gourd, Methi/fenugreek).
- Regular brisk physical exercise (Vyayama) to deplete Meda and Kleda.
### Apathya
- Sugar, jaggery, milk products, daytime sleep, and sedentary habits (Asya Sukham, Swapna Sukham).
"""
    },
    "Amavata / Rheumatoid Arthritis": {
        "title": "Clinical Practice Guideline: Diagnosis and Integrative Management of Amavata",
        "tables": [
            {
                "caption": "Table 3: Prescription Matrix for Inflammatory Arthritis according to Phase",
                "headers": ["Disease Phase", "Inflammatory Severity", "Selected Formulation", "Matra (Dosage)", "Sahpaan (Vehicle)", "Aushadh Kal (Timing)"],
                "rows": [
                    ["Acute / Sama Stage", "High ESR/CRP, severe joint heat", "Simhanada Guggulu", "500 mg twice daily", "Ushnodaka (Boiled warm water)", "Adhobhakta (After food)"],
                    ["Acute / Sama Stage", "Severe morning stiffness (>1 hr)", "Rasnadi Kwatha", "20 ml with equal water", "Pippali Churna (1 pinch)", "Pratah & Sandhya (Empty stomach)"],
                    ["Chronic / Nirama Stage", "Joint crepitus and deformity", "Yogaraj Guggulu", "500 mg thrice daily", "Warm water with Dashamoola", "Adhobhakta (After meals)"],
                    ["Localized Severe Pain", "Effusion in knee/wrist", "Balu Sweda (Sand bag)", "Dry fomentation 20 mins", "External procedure", "Twice daily"],
                    ["Systemic Ama Infiltration", "Loss of appetite & sluggishness", "Vaishwanara Churna", "3 grams twice daily", "Warm Takra (Buttermilk)", "Pragbhakta (Before food)"]
                ]
            }
        ],
        "prose": """
# Clinical Practice Guideline: Management of Amavata

## 1. Etiopathology of Amavata
Amavata occurs when impaired Mandagni leads to the formation of Ama (undigested toxic metabolite). Vitiated Vata carries Ama into the Shleshma Sthana (synovial joints), causing acute swelling, intense pain (Vrishchika Damshavat - like a scorpion sting), and functional stiffness.

## 2. Core Treatment Principles (Chikitsa Sutra)
Langhana (fasting/light diet), Swedana (dry sudation without oil), Tikta-Katu Deepana (digestive fire stimulants), Virechana (therapeutic purgation), and Basti (enema).

## 3. Strict Clinical Warnings
- Snehana (oil massage) is strictly CONTRAINDICATED in the Sama stage, as oil massage will aggravate inflammation and worsen pain.
- Monitor liver and kidney functions during intensive Guggulu administration.
"""
    }
}


def generate_guideline_markdown(disease_name: str) -> str:
    """Generates the Markdown representation of the sample guideline with tables and prose."""
    data = SAMPLE_GUIDELINES.get(disease_name)
    if not data:
        raise ValueError(f"Unknown sample guideline disease: {disease_name}")

    parts = [f"# {data['title']}\n"]

    for table in data["tables"]:
        parts.append(f"### {table['caption']}\n")
        # Format markdown table
        headers = table["headers"]
        header_row = "| " + " | ".join(headers) + " |"
        sep_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        parts.append(header_row)
        parts.append(sep_row)
        for r in table["rows"]:
            parts.append("| " + " | ".join(r) + " |")
        parts.append("\n")

    parts.append(data["prose"])
    return "\n".join(parts)


def create_sample_pdf(file_path: str, disease_name: str):
    """
    Creates a formatted PDF document with tables and prose on disk using reportlab / fpdf or pypdf.
    If third-party PDF generators are not available, writes a clean guideline file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    md_content = generate_guideline_markdown(disease_name)

    # Simple plain text or basic PDF creation
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        data = SAMPLE_GUIDELINES[disease_name]
        story.append(Paragraph(data["title"], styles['Title']))
        story.append(Spacer(1, 14))

        for table in data["tables"]:
            story.append(Paragraph(table['caption'], styles['Heading2']))
            story.append(Spacer(1, 8))
            table_matrix = [table["headers"]] + table["rows"]
            t = Table(table_matrix)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#166534')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(t)
            story.append(Spacer(1, 14))

        for line in data["prose"].splitlines():
            if line.startswith("# "):
                story.append(Paragraph(line[2:], styles['Heading1']))
            elif line.startswith("## "):
                story.append(Paragraph(line[3:], styles['Heading2']))
            elif line.startswith("### "):
                story.append(Paragraph(line[4:], styles['Heading3']))
            elif line.strip():
                story.append(Paragraph(line, styles['Normal']))
            story.append(Spacer(1, 4))

        doc.build(story)
        logger.info(f"ReportLab built sample PDF at: {file_path}")
        return file_path
    except Exception as e:
        logger.info(f"ReportLab not available ({e}), writing guideline markdown document directly.")
        # Write .md or text file
        md_path = file_path.replace(".pdf", ".md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        return md_path
