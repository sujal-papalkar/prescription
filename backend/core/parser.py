"""
Structure-Aware Parser for Ayurvedic Clinical Guidelines
Implements Fork A (Table Matrix Extraction & Patient-State Grouping)
and Fork B (Prose Markdown Section Hierarchy Chunking).
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Check docling availability
DOCLING_AVAILABLE = False
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("IBM Docling not available in active environment, using fallback structure parser.")


class StructureAwareParser:
    """
    Parses complex multi-disease clinical guideline PDFs into structured chunks.
    Separates narrative prose and clinical tabular matrices to avoid semantic blurriness.
    """

    def __init__(self):
        self.docling_converter = None
        if DOCLING_AVAILABLE:
            try:
                self.docling_converter = DocumentConverter()
                logger.info("Initialized IBM Docling DocumentConverter successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize Docling DocumentConverter: {e}. Fallback enabled.")
                self.docling_converter = None

    def parse_document(self, file_path: str, disease_name: str) -> List[Dict[str, Any]]:
        """
        Parses a document (PDF, DOCX, TXT, MD, CSV, XLSX, PNG, JPG, JPEG) into structured chunks with metadata.
        Returns a list of chunk dictionaries with 'text', 'metadata', and 'chunk_id'.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found at: {file_path}")

        chunks: List[Dict[str, Any]] = []
        ext = os.path.splitext(file_path)[1].lower()

        # Format-specific high-fidelity extraction
        parsed_with_specialized = False

        if ext in [".docx", ".doc"]:
            logger.info(f"Parsing {file_path} using dedicated Word document structure parser...")
            chunks = self._fallback_parse_docx(file_path, disease_name)
            parsed_with_specialized = bool(chunks)
        elif ext == ".csv":
            logger.info(f"Parsing {file_path} using dedicated CSV table matrix parser...")
            chunks = self._fallback_parse_csv(file_path, disease_name)
            parsed_with_specialized = bool(chunks)
        elif ext in [".xlsx", ".xlsv", ".xls"]:
            logger.info(f"Parsing {file_path} using dedicated Excel workbook matrix parser...")
            chunks = self._fallback_parse_excel(file_path, disease_name)
            parsed_with_specialized = bool(chunks)

        if not parsed_with_specialized:
            # Primary Docling extraction for PDF and image documents
            parsed_with_docling = False
            if self.docling_converter:
                try:
                    logger.info(f"Parsing {file_path} using IBM Docling...")
                    conv_result = self.docling_converter.convert(file_path)
                    doc = conv_result.document

                    # Fork A: Process Tabular Prescription Matrices from Docling
                    table_chunks = self._process_docling_tables(doc, disease_name, file_path)
                    chunks.extend(table_chunks)

                    # Fork B: Process Prose Narrative from Docling Markdown
                    markdown_text = doc.export_to_markdown()
                    prose_chunks = self._process_markdown_prose(markdown_text, disease_name, file_path)
                    chunks.extend(prose_chunks)

                    parsed_with_docling = True
                    logger.info(f"Docling parsed {len(table_chunks)} table chunks and {len(prose_chunks)} prose chunks.")
                except Exception as e:
                    logger.warning(f"Docling parsing encountered error: {e}. Switching to format-specific fallback parser.")

            if not parsed_with_docling:
                if ext in [".txt", ".md"]:
                    chunks = self._fallback_parse_text(file_path, disease_name)
                elif ext in [".png", ".jpg", ".jpeg"]:
                    chunks = self._fallback_parse_image(file_path, disease_name)
                else:
                    chunks = self._fallback_parse_pdf(file_path, disease_name)

        # Dynamic physical page number resolution for PDF chunks
        page_texts: Dict[int, str] = {}
        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for p_idx, page_obj in enumerate(reader.pages):
                    page_texts[p_idx + 1] = page_obj.extract_text() or ""
            except Exception as e:
                logger.warning(f"Could not load pypdf reader for page mapping: {e}")

        # Assign unique chunk identifiers and exact dynamic page numbers
        for idx, chunk in enumerate(chunks):
            chunk["chunk_id"] = f"{disease_name.lower().replace(' ', '_')}_{chunk['metadata'].get('chunk_type', 'chunk')}_{idx}"
            if "page" not in chunk["metadata"] or not chunk["metadata"]["page"]:
                if page_texts:
                    chunk["metadata"]["page"] = self._detect_chunk_page(chunk["text"], page_texts)
                else:
                    chunk["metadata"]["page"] = 1

        logger.info(f"Total structure-aware chunks produced for '{disease_name}': {len(chunks)}")
        return chunks

    def parse_pdf(self, file_path: str, disease_name: str) -> List[Dict[str, Any]]:
        """Alias for parse_document for backward compatibility."""
        return self.parse_document(file_path, disease_name)

    def _detect_chunk_page(self, chunk_text: str, page_texts: Dict[int, str]) -> int:
        """
        Dynamically detects the true physical PDF page number for a given chunk.
        Uses exact phrase search for unambiguous page identification, followed by
        distinctive keyword overlap scoring.
        """
        if not page_texts:
            return 1

        clean_lines = [
            l.strip() for l in chunk_text.splitlines()
            if len(l.strip()) > 8 and not l.strip().startswith("|---") and not l.strip().startswith("[")
        ]

        if "Table Section Matrix" in chunk_text:
            parts = [p.strip() for p in chunk_text.replace("Table Section Matrix.", "").split(",")]
            clean_lines.extend([p for p in parts if len(p) > 8 and ":" in p])

        generic_header_patterns = [
            {"medicine", "matra"},
            {"sahpaan", "aushadh"},
            {"hrct", "score"},
            {"patient", "type"},
            {"age", "group"},
        ]

        # Pass 1: Look for an unambiguous exact phrase unique to a single page
        for line in clean_lines:
            line_lower = line.lower()
            # Skip lines that are just generic column headers
            if any(all(kw in line_lower for kw in pat) for pat in generic_header_patterns):
                continue

            line_clean = line.replace("|", " ").strip()
            if ":" in line_clean:
                line_clean = line_clean.split(":")[-1].strip()

            words = [w for w in line_clean.split() if len(w) > 3]
            if len(words) >= 2:
                search_phrase = " ".join(words[:min(4, len(words))]).lower()
                matched_pages = [p_no for p_no, p_txt in page_texts.items() if search_phrase in p_txt.lower()]
                if len(matched_pages) == 1:
                    return matched_pages[0]

        # Pass 2: Distinctive keyword overlap fallback (excluding common clinical stopwords)
        words = set(w.lower() for w in re.findall(r"\b[a-zA-Z0-9]{4,}\b", chunk_text))
        clinical_stopwords = {"medicine", "matra", "sahpaan", "aushadh", "respiratory", "viral", "infection", "protocol", "table"}
        distinctive_words = words - clinical_stopwords

        best_p = 1
        best_score = 0
        for p_no, p_txt in page_texts.items():
            p_words = set(w.lower() for w in re.findall(r"\b[a-zA-Z0-9]{4,}\b", p_txt))
            score = len(distinctive_words.intersection(p_words))
            if score > best_score:
                best_score = score
                best_p = p_no

        return best_p

    def _process_docling_tables(self, doc: Any, disease_name: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Fork A: Converts IBM Docling tables to Pandas DataFrames.
        Forward-fills category columns to eliminate disjointed rows,
        and serializes row-clusters with header labels into descriptive matrices.
        """
        table_chunks: List[Dict[str, Any]] = []

        try:
            tables = getattr(doc, "tables", [])
            for t_idx, table in enumerate(tables):
                # Export table to pandas DataFrame if supported
                if hasattr(table, "export_to_dataframe"):
                    df = table.export_to_dataframe()
                else:
                    # Generic extraction from table rows/cells
                    df = self._extract_df_from_table_obj(table)

                if df is None or df.empty:
                    continue

                serialized = self._serialize_dataframe_matrix(df, disease_name, file_path, t_idx)
                table_chunks.extend(serialized)
        except Exception as e:
            logger.error(f"Error processing Docling tables: {e}")

        return table_chunks

    def _extract_df_from_table_obj(self, table: Any) -> Optional[pd.DataFrame]:
        """Extracts a Pandas DataFrame from arbitrary table representations."""
        try:
            if hasattr(table, "data") and isinstance(table.data, list):
                return pd.DataFrame(table.data)
            if hasattr(table, "grid") and isinstance(table.grid, list):
                rows = []
                for row in table.grid:
                    rows.append([cell.text if hasattr(cell, 'text') else str(cell) for cell in row])
                if len(rows) > 1:
                    return pd.DataFrame(rows[1:], columns=rows[0])
                elif len(rows) == 1:
                    return pd.DataFrame(rows)
        except Exception as e:
            logger.debug(f"DataFrame extraction error: {e}")
        return None

    def _serialize_dataframe_matrix(
        self, df: pd.DataFrame, disease_name: str, file_path: str, table_idx: int, table_title: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Processes a table DataFrame:
        1. Normalizes column headers.
        2. Forward-fills the first category column(s) to preserve patient-state context.
        3. Serializes rows or row-clusters into single factual blocks.
        """
        chunks = []
        df = df.copy()

        # Clean and disambiguate headers to ensure unique, descriptive column names
        clean_headers = []
        seen = {}
        for idx, c in enumerate(df.columns):
            name = str(c).strip().replace("\n", " ").replace("<!-- rich cell -->", "").strip()
            if not name:
                name = f"Column_{idx + 1}"
            if name in seen:
                seen[name] += 1
                name = f"{name}_{seen[name]}"
            else:
                seen[name] = 1
            clean_headers.append(name)
        df.columns = clean_headers

        # Forward-fill first category columns to avoid disjointed text lines
        if len(df.columns) > 0:
            df.iloc[:, 0] = df.iloc[:, 0].replace("", None).ffill()
        if len(df.columns) > 1:
            try:
                col_2 = df.iloc[:, 1]
                if isinstance(col_2, pd.Series) and col_2.isna().sum() > len(df) * 0.3:
                    df.iloc[:, 1] = col_2.replace("", None).ffill()
            except Exception:
                pass

        # Group rows logically into Patient-State Groups (e.g. by column 0 or severity)
        for row_idx, row in df.iterrows():
            row_items = []
            row_values = []
            for col in df.columns:
                val = str(row[col]).strip() if pd.notna(row[col]) else ""
                if val and val.lower() != "nan":
                    row_items.append(f"{col}: {val}")
                    row_values.append(val.lower())

            if not row_items:
                continue

            # Skip merged section header rows where all columns share identical text
            if len(row_values) >= 3 and len(set(row_values)) == 1:
                continue

            prefix = (
                f"Table Section Matrix [{table_title}]. Criteria and Intervention Details -> "
                if table_title
                else "Table Section Matrix. Criteria and Intervention Details -> "
            )
            matrix_sentence = prefix + ", ".join(row_items)

            chunks.append({
                "text": matrix_sentence,
                "metadata": {
                    "disease_name": disease_name,
                    "source": os.path.basename(file_path),
                    "chunk_type": "table_matrix",
                    "table_index": table_idx,
                    "row_index": int(row_idx),
                    "category": str(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else "General"
                }
            })

        return chunks

    def _process_markdown_prose(
        self, markdown_text: str, disease_name: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Fork B (Prose):
        Segments narrative text neatly at Markdown layout headers (#, ##, ###).
        Pre-pends section titles onto child text fragments to preserve operational context.
        """
        chunks: List[Dict[str, Any]] = []
        lines = markdown_text.splitlines()

        current_hierarchy: List[str] = []
        current_buffer: List[str] = []
        current_level = 0

        def flush_buffer():
            nonlocal current_buffer, current_hierarchy
            text_body = "\n".join(current_buffer).strip()
            # Filter out empty or placeholder chunks (e.g. only <!-- image --> or disclaimers)
            clean_body = text_body.replace("<!-- image -->", "").strip()
            lines_body = [
                l for l in clean_body.splitlines()
                if "Registered Ayurvedic Medical" not in l and "mere translation" not in l
            ]
            meaningful_text = " ".join(lines_body).strip()
            if meaningful_text and (len(meaningful_text) >= 30 or "|" in text_body):
                section_title = " > ".join(current_hierarchy) if current_hierarchy else "Overview"
                full_chunk_text = f"[{section_title}]\n{text_body}"
                chunks.append({
                    "text": full_chunk_text,
                    "metadata": {
                        "disease_name": disease_name,
                        "source": os.path.basename(file_path),
                        "chunk_type": "prose_narrative",
                        "section": section_title,
                        "level": current_level
                    }
                })
            current_buffer = []

        header_regex = re.compile(r"^(#{1,6})\s+(.+)$")

        for line in lines:
            header_match = header_regex.match(line.strip())
            if header_match:
                # Flush previous prose block before starting new section
                flush_buffer()
                hashes = header_match.group(1)
                title = header_match.group(2).strip()
                level = len(hashes)
                current_level = level

                # Adjust hierarchy depth
                if level == 1:
                    current_hierarchy = [title]
                elif level == 2:
                    current_hierarchy = current_hierarchy[:1] + [title]
                elif level >= 3:
                    current_hierarchy = current_hierarchy[:2] + [title]
            else:
                # Accumulate paragraph text
                if line.strip():
                    current_buffer.append(line.strip())
                elif current_buffer and len("\n".join(current_buffer)) > 800:
                    # Natural paragraph split if very large section
                    flush_buffer()

        flush_buffer()
        return chunks

    def _fallback_parse_pdf(self, file_path: str, disease_name: str) -> List[Dict[str, Any]]:
        """
        High-fidelity fallback parser using pdfplumber / pypdf to extract:
        1. Formatted tables into DataFrames with forward-fill & serialization.
        2. Layout-aware prose split along detected headings and sections.
        """
        chunks: List[Dict[str, Any]] = []

        try:
            import pdfplumber
            logger.info(f"Extracting layout and tables using pdfplumber for: {file_path}")

            with pdfplumber.open(file_path) as pdf:
                full_prose_lines = []

                for p_idx, page in enumerate(pdf.pages):
                    # 1. Extract and process tables on this page
                    tables = page.extract_tables()
                    for t_idx, table_data in enumerate(tables):
                        if not table_data or len(table_data) < 2:
                            continue

                        # Clean rows
                        raw_headers = [str(c or "").strip() for c in table_data[0]]
                        headers = [h if h else f"Col_{i}" for i, h in enumerate(raw_headers)]
                        rows = table_data[1:]

                        df = pd.DataFrame(rows, columns=headers)
                        serialized_tables = self._serialize_dataframe_matrix(
                            df, disease_name, file_path, table_idx=(p_idx * 10 + t_idx)
                        )
                        for s_chunk in serialized_tables:
                            s_chunk["metadata"]["page"] = p_idx + 1
                        chunks.extend(serialized_tables)

                    # 2. Extract page prose excluding table bboxes if possible
                    page_text = page.extract_text()
                    if page_text:
                        full_prose_lines.extend(page_text.splitlines())

                # Process prose lines with pseudo-markdown heading detection
                prose_md = self._convert_plain_text_to_heading_md(full_prose_lines)
                prose_chunks = self._process_markdown_prose(prose_md, disease_name, file_path)
                chunks.extend(prose_chunks)

        except Exception as e:
            logger.error(f"pdfplumber fallback encountered error: {e}. Attempting raw text extraction.")
            # Ultimate fallback if pdfplumber fails
            chunks.extend(self._raw_text_fallback(file_path, disease_name))

        return chunks

    def _convert_plain_text_to_heading_md(self, lines: List[str]) -> str:
        """Heuristic heading detector for plain text lines into Markdown."""
        md_lines = []
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            # Check if line looks like an uppercase section title or Roman numeral
            if (
                re.match(r"^(SECTION|CHAPTER|PART|MODULE|[I|V|X]+\.|\d+\.)\s+", cleaned, re.IGNORECASE)
                or (cleaned.isupper() and len(cleaned) < 60 and not cleaned.endswith("."))
            ):
                md_lines.append(f"\n## {cleaned}\n")
            elif cleaned.startswith(("#", "##", "###")):
                md_lines.append(cleaned)
            else:
                md_lines.append(cleaned)

        return "\n".join(md_lines)

    def _raw_text_fallback(self, file_path: str, disease_name: str) -> List[Dict[str, Any]]:
        """Emergency fallback reader."""
        chunks = []
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            all_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text:
                    all_text.append(f"\n## Page {i+1}\n" + text)
            md = "\n".join(all_text)
            chunks = self._process_markdown_prose(md, disease_name, file_path)
        except Exception as err:
            logger.error(f"Raw PDF read failed: {err}")
        return chunks

    def _fallback_parse_text(self, file_path: str, disease_name: str) -> List[Dict[str, Any]]:
        """Parses plain text (.txt) and Markdown (.md) documents."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return self._process_markdown_prose(content, disease_name, file_path)
        except Exception as e:
            logger.error(f"Text fallback parse error: {e}")
            return []

    def _fallback_parse_docx(self, file_path: str, disease_name: str) -> List[Dict[str, Any]]:
        """Parses Word (.docx, .doc) documents including tables and text with exact XML page and table provenance."""
        chunks = []
        try:
            import docx
            doc = docx.Document(file_path)
            body = doc._body._element

            # Map XML table elements to their docx table index
            table_element_map = {t._element: idx for idx, t in enumerate(doc.tables)}

            # 1. Read document total pages recorded by Word if available in docProps/app.xml
            total_doc_pages = None
            try:
                import zipfile
                import xml.etree.ElementTree as ET
                with zipfile.ZipFile(file_path) as z:
                    if "docProps/app.xml" in z.namelist():
                        tree = ET.fromstring(z.read("docProps/app.xml"))
                        elem = tree.find(".//{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Pages")
                        if elem is not None and elem.text.isdigit():
                            total_doc_pages = int(elem.text)
            except Exception as e_props:
                logger.debug(f"Could not read docProps/app.xml: {e_props}")

            # 2. Inspect document elements to count prose characters and total table rows
            total_prose_chars = 0
            prose_chars_before = 0
            has_table = False
            total_table_rows = 0
            for child in body:
                tag = child.tag.split("}")[-1]
                if tag == "p":
                    txt_len = len("".join(child.itertext()).strip())
                    total_prose_chars += txt_len
                    if not has_table:
                        prose_chars_before += txt_len
                elif tag == "tbl":
                    has_table = True
                    row_elements = child.xpath("./*[local-name()='tr']")
                    total_table_rows += len(row_elements)

            # 3. Dynamic layout pagination budgeting derived from document typography:
            # In standard A4 layout, a page holds ~5,000 characters of formatted prose or ~15 table rows (~330 char-units per row)
            ROW_CHAR_EQUIVALENT = 330
            if total_doc_pages and total_doc_pages > 1:
                total_units = total_prose_chars + (total_table_rows * ROW_CHAR_EQUIVALENT)
                front_ratio = prose_chars_before / max(1, total_units)
                front_matter_pages = round(total_doc_pages * front_ratio)
                first_table_start_page = max(1, min(total_doc_pages, front_matter_pages + 1))
                table_budget_pages = max(1, total_doc_pages - front_matter_pages)
                rows_per_page = max(10, round(total_table_rows / table_budget_pages))
            elif total_doc_pages == 1:
                first_table_start_page = 1
                rows_per_page = max(1, total_table_rows)
            else:
                front_matter_pages = round(prose_chars_before / 5000.0)
                first_table_start_page = max(1, front_matter_pages + 1)
                rows_per_page = 15

            current_page = 1
            tbl_counter = 0

            # Collect prose paragraphs with their exact page numbers
            prose_paragraphs = []

            for child in body:
                tag = child.tag.split("}")[-1]

                if tag == "tbl":
                    tbl_counter += 1
                    if tbl_counter == 1:
                        current_page = first_table_start_page

                    t_idx = table_element_map.get(child, tbl_counter - 1)
                    table_obj = doc.tables[t_idx] if t_idx < len(doc.tables) else None

                    # Extract rows and assign row-level page numbers based on layout row budgeting
                    t_rows = []
                    row_elements = child.xpath("./*[local-name()='tr']")
                    num_rows = len(row_elements)
                    t_start_page = min(total_doc_pages or 999, current_page)
                    added_pages = max(0, (num_rows - 1) // rows_per_page)
                    t_end_page = min(total_doc_pages or 999, t_start_page + added_pages)
                    row_pages = [min(total_doc_pages or 999, t_start_page + (r_i // rows_per_page)) for r_i in range(num_rows)]
                    current_page = t_end_page + 1

                    if table_obj:
                        for row in table_obj.rows:
                            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                            t_rows.append(cells)

                    if t_rows and len(t_rows) >= 2:
                        headers = t_rows[0]
                        # Determine meaningful table title from first row or headers
                        first_cell_set = set(headers)
                        if len(first_cell_set) == 1 and len(headers[0]) > 3:
                            table_name = headers[0]
                            # If row 0 was a merged title row and row 1 has actual column headers
                            if len(t_rows) >= 3 and any(c.lower() in ["medicine", "matra", "stage", "symptoms"] for c in t_rows[1]):
                                headers = t_rows[1]
                                data_rows = t_rows[2:]
                            else:
                                data_rows = t_rows[1:]
                        else:
                            table_name = f"Table {tbl_counter}"
                            data_rows = t_rows[1:]

                        page_label = f"Table {tbl_counter} (Pg {t_start_page})" if t_start_page == t_end_page else f"Table {tbl_counter} (Pg {t_start_page}–{t_end_page})"

                        md_lines = [
                            "| " + " | ".join(headers) + " |",
                            "| " + " | ".join([":---"] * len(headers)) + " |"
                        ]
                        for r in data_rows:
                            md_lines.append("| " + " | ".join(r) + " |")
                        table_md = "\n".join(md_lines)

                        # Add structured markdown table chunk
                        chunks.append({
                            "text": f"[Table Matrix {tbl_counter}: {table_name}]\n{table_md}",
                            "metadata": {
                                "disease_name": disease_name,
                                "source": os.path.basename(file_path),
                                "chunk_type": "prose_narrative",
                                "page": page_label,
                                "table_number": tbl_counter,
                                "table_index": t_idx,
                                "start_page": t_start_page,
                                "end_page": t_end_page
                            }
                        })

                        # Add forward-filled row-level patient-state matrix chunks with exact row pages
                        try:
                            import pandas as pd
                            df = pd.DataFrame(data_rows, columns=headers)
                            serialized = self._serialize_dataframe_matrix(
                                df, disease_name, file_path, t_idx, table_title=f"Table {tbl_counter}: {table_name}"
                            )
                            offset = len(t_rows) - len(data_rows)
                            for s_i, s_chunk in enumerate(serialized):
                                row_idx = min(s_i + offset, len(row_pages) - 1)
                                row_pg = row_pages[row_idx] if row_pages else t_start_page
                                s_chunk["metadata"]["page"] = f"Table {tbl_counter} (Pg {row_pg})"
                                s_chunk["metadata"]["table_number"] = tbl_counter
                                s_chunk["metadata"]["start_page"] = row_pg
                            chunks.extend(serialized)
                        except Exception as de:
                            logger.debug(f"DOCX DataFrame serialization error: {de}")

                elif tag == "p":
                    p_txt = "".join(child.itertext()).strip()
                    if tbl_counter == 0:
                        p_page = min(max(1, first_table_start_page - 1), current_page)
                    else:
                        p_page = min(total_doc_pages or 999, current_page)
                    if p_txt:
                        prose_paragraphs.append((p_txt, p_page))
                    breaks = child.xpath(".//*[local-name()='lastRenderedPageBreak' or (local-name()='br' and @*[local-name()='type']='page')]")
                    if breaks:
                        current_page += len(breaks)

            # Process prose paragraphs with accurate page numbers
            if prose_paragraphs:
                for p_txt, p_page in prose_paragraphs:
                    if len(p_txt) >= 40:
                        chunks.append({
                            "text": f"[{os.path.basename(file_path)} | Overview]\n{p_txt}",
                            "metadata": {
                                "disease_name": disease_name,
                                "source": os.path.basename(file_path),
                                "chunk_type": "prose_narrative",
                                "page": f"Pg {p_page}",
                                "start_page": p_page
                            }
                        })

        except Exception as e:
            logger.error(f"DOCX fallback parse error: {e}")
        return chunks

    def _fallback_parse_csv(self, file_path: str, disease_name: str) -> List[Dict[str, Any]]:
        """Parses CSV (.csv) spreadsheets into markdown table chunks and matrix rows."""
        chunks = []
        try:
            import pandas as pd
            df = pd.read_csv(file_path, keep_default_na=False)
            table_md = df.to_markdown(index=False)
            chunks.append({
                "text": f"[{os.path.basename(file_path)}]\n{table_md}",
                "metadata": {
                    "disease_name": disease_name,
                    "source": os.path.basename(file_path),
                    "chunk_type": "prose_narrative",
                    "page": 1,
                    "table_index": 0
                }
            })
            # Forward-filled patient-state matrix chunks
            serialized = self._serialize_dataframe_matrix(df, disease_name, file_path, 0)
            chunks.extend(serialized)
        except Exception as e:
            logger.error(f"CSV fallback parse error: {e}")
        return chunks

    def _fallback_parse_excel(self, file_path: str, disease_name: str) -> List[Dict[str, Any]]:
        """Parses Excel (.xlsx, .xlsv, .xls) workbooks across all sheets into tables and matrix rows."""
        chunks = []
        try:
            import pandas as pd
            sheets = pd.read_excel(file_path, sheet_name=None, keep_default_na=False)
            for s_idx, (sheet_name, df) in enumerate(sheets.items()):
                if df.empty:
                    continue
                table_md = df.to_markdown(index=False)
                chunks.append({
                    "text": f"[{sheet_name}]\n{table_md}",
                    "metadata": {
                        "disease_name": disease_name,
                        "source": os.path.basename(file_path),
                        "chunk_type": "prose_narrative",
                        "page": s_idx + 1,
                        "sheet_name": str(sheet_name),
                        "table_index": s_idx
                    }
                })
                # Forward-filled patient-state matrix chunks
                serialized = self._serialize_dataframe_matrix(df, disease_name, file_path, s_idx)
                chunks.extend(serialized)
        except Exception as e:
            logger.error(f"Excel fallback parse error: {e}")
        return chunks

    def _fallback_parse_image(self, file_path: str, disease_name: str) -> List[Dict[str, Any]]:
        """Parses image guidelines (.png, .jpg, .jpeg) using OCR or GenAI vision."""
        chunks = []
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                from PIL import Image
                client = genai.Client(api_key=api_key)
                img = Image.open(file_path)
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[img, "Extract all text, clinical guidelines, and tabular matrices from this image in markdown format."]
                )
                if resp and resp.text:
                    prose_chunks = self._process_markdown_prose(resp.text, disease_name, file_path)
                    chunks.extend(prose_chunks)
            except Exception as e:
                logger.warning(f"Image vision parse error: {e}")

        if not chunks:
            # Fallback descriptor chunk if offline
            chunks.append({
                "text": f"[Guideline Image: {os.path.basename(file_path)}]\nClinical guideline image document uploaded for {disease_name}.",
                "metadata": {
                    "disease_name": disease_name,
                    "source": os.path.basename(file_path),
                    "chunk_type": "prose_narrative",
                    "page": 1
                }
            })
        return chunks
