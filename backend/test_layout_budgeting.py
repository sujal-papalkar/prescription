import docx

doc = docx.Document("data/uploads/DM_RR_DM RR.docx")
body = doc._body._element

current_page = 1
lines_on_page = 0
MAX_LINES_PER_PAGE = 30  # Standard Word page text lines
ROWS_PER_TABLE_PAGE = 18

table_pages = []

# Section markers that begin a new page in Word
PAGE_HEADINGS = [
    "AYURVED RASAYANI",
    "DEAR VAIDYAS",
    "DISCLAIMER",
    "PROPHYLACTIC GUIDELINES",
    "THEREPEUTIC GUIDELINES",
    "TREATMENT GUIDELINES FOR THE MANAGEMENT OF PRAMEH UPADRAV"
]

consecutive_empty = 0

for child in body:
    tag = child.tag.split("}")[-1]
    if tag == "p":
        txt = "".join(child.itertext()).strip()
        if not txt:
            consecutive_empty += 1
            continue
        
        has_break = bool(child.xpath('.//*[local-name()="lastRenderedPageBreak" or (local-name()="br" and @*[local-name()="type"]="page")]'))
        has_pb_before = bool(child.xpath('.//*[local-name()="pageBreakBefore"]'))
        
        # Check major section banners
        txt_upper = txt.upper()
        is_page_heading = any(h in txt_upper for h in PAGE_HEADINGS)
        
        if has_break or has_pb_before or (is_page_heading and lines_on_page > 0):
            current_page += 1
            lines_on_page = 0
            
        p_lines = max(1, len(txt) // 80 + 1)
        lines_on_page += p_lines
        if lines_on_page >= MAX_LINES_PER_PAGE:
            current_page += (lines_on_page // MAX_LINES_PER_PAGE)
            lines_on_page = lines_on_page % MAX_LINES_PER_PAGE
        consecutive_empty = 0
                
    elif tag == "tbl":
        rows = child.xpath("./w:tr")
        num_rows = len(rows)
        
        # In this document, each table is a major standalone clinical guideline block starting on a fresh page
        if lines_on_page > 4:
            current_page += 1
            lines_on_page = 0
            
        start_pg = current_page
        added_pages = max(0, (num_rows - 1) // ROWS_PER_TABLE_PAGE)
        end_pg = start_pg + added_pages
        table_pages.append((len(table_pages) + 1, start_pg, end_pg, num_rows))
        current_page = end_pg + 1
        lines_on_page = 0
        consecutive_empty = 0

print("\n--- SIMULATED WORD PRINT LAYOUT (EXACT 25-PAGE CALIBRATION) ---")
for t_num, sp, ep, nr in table_pages:
    page_str = f"Page {sp}" if sp == ep else f"Page {sp}–{ep}"
    print(f"Table {t_num:02d} (Rows: {nr:<2}) -> {page_str}")
print(f"Total Document Pages: {current_page - 1}\n")
