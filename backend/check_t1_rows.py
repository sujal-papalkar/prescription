import docx

doc = docx.Document("data/uploads/DM_RR_DM RR.docx")
t1 = doc.tables[0]
print(f"Table 1 Total Rows: {len(t1.rows)}")
for idx, r in enumerate(t1.rows):
    cells = [c.text.strip().replace("\n", " ") for c in r.cells]
    has_break = any(
        c._tc.xpath('.//*[local-name()="lastRenderedPageBreak" or (local-name()="br" and @*[local-name()="type"]="page")]')
        for c in r.cells
    )
    print(f"Row {idx:02d} (PageBreak={has_break}): {cells[0][:32]} | {cells[1][:20]} | {cells[2][:8]} | {cells[3][:12]} | {cells[4][:25]}")
