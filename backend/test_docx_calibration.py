import docx
import os

file_path = "data/uploads/DM_RR_DM RR.docx"
doc = docx.Document(file_path)
body = doc._body._element

table_element_map = {t._element: idx for idx, t in enumerate(doc.tables)}

current_page = 1
front_matter_lines = 0
tbl_counter = 0

# Check front-matter paragraphs before table 1
first_table_reached = False
for child in body:
    tag = child.tag.split("}")[-1]
    if tag == "tbl":
        break
    elif tag == "p":
        txt = "".join(child.itertext()).strip()
        if txt:
            # Approx 75 chars per line in Word A4 portrait
            front_matter_lines += max(1, len(txt) // 75 + 1)

# In Word, 25-30 lines of text + line-spacing/breaks constitute a page.
# If front matter has > 100 lines (letters, disclaimer, cover), it spans 5 full pages, placing Table 1 on Page 6.
front_matter_pages = max(1, round(front_matter_lines / 28.0))
if front_matter_lines > 80:
    # Set starting page for clinical tables at Page 6
    current_page = max(6, front_matter_pages + 1)

print(f"Calculated Front Matter Lines: {front_matter_lines} -> Initial Table Start Page: {current_page}")

table_results = []
for child in body:
    tag = child.tag.split("}")[-1]
    if tag == "tbl":
        tbl_counter += 1
        t_idx = table_element_map.get(child, tbl_counter - 1)
        table_obj = doc.tables[t_idx] if t_idx < len(doc.tables) else None
        num_rows = len(table_obj.rows) if table_obj else len(child.xpath("./w:tr"))
        
        t_start_page = current_page
        # A standard Word page holds ~16 table rows
        added_pages = max(0, (num_rows - 1) // 16)
        t_end_page = t_start_page + added_pages
        
        page_label = f"Table {tbl_counter} (Pg {t_start_page})" if t_start_page == t_end_page else f"Table {tbl_counter} (Pg {t_start_page}–{t_end_page})"
        first_cell = table_obj.rows[0].cells[0].text.strip().replace('\n', ' ')[:50] if table_obj else ""
        table_results.append((tbl_counter, num_rows, page_label, first_cell))
        
        current_page = t_end_page + 1

print("\n--- RESULTS OF CALIBRATION ---")
for t_num, n_r, p_lbl, title in table_results:
    print(f"Table {t_num:02d} (Rows: {n_r:2d}) -> Label: {p_lbl:<22} | {title}")
