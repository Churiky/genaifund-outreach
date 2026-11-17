import html
import os
import re
import zipfile

def create_docx(markdown_path: str, docx_path: str):
    with open(markdown_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # XML components
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:color w:val="1F2937"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:line="276" w:lineRule="auto" w:after="160"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>"""

    # Parse markdown into OpenXML elements
    lines = md_text.splitlines()
    body_xml_parts = []

    def escape(t):
        return html.escape(t).replace("&apos;", "'")

    def format_inline_runs(text):
        """Converts bold and normal text to w:r elements."""
        tokens = re.split(r"(\*\*.*?\*\*)", text)
        runs_xml = []
        for token in tokens:
            if not token:
                continue
            if token.startswith("**") and token.endswith("**") and len(token) >= 4:
                inner = escape(token[2:-2])
                runs_xml.append(f'<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{inner}</w:t></w:r>')
            else:
                inner = escape(token)
                runs_xml.append(f'<w:r><w:t xml:space="preserve">{inner}</w:t></w:r>')
        return "".join(runs_xml)

    i = 0
    in_table = False
    table_rows = []

    while i < len(lines):
        line = lines[i].strip()

        # Handle table
        if line.startswith("|") and line.endswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            if not re.match(r"^\|(\s*[-:]+\s*\|)+$", line):  # Skip separator row like |---|---|
                cells = [c.strip() for c in line.strip("|").split("|")]
                table_rows.append(cells)
            i += 1
            continue
        elif in_table:
            # End of table, render it
            in_table = False
            t_xml = ['<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>'
                     '<w:top w:val="single" w:sz="6" w:space="0" w:color="D1D5DB"/>'
                     '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="D1D5DB"/>'
                     '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>'
                     '<w:insideV w:val="none"/>'
                     '</w:tblBorders></w:tblPr>']
            for row_idx, r in enumerate(table_rows):
                t_xml.append('<w:tr>')
                is_header = (row_idx == 0)
                for cell in r:
                    shd = '<w:shd w:val="clear" w:color="auto" w:fill="F3F4F6"/>' if is_header else ''
                    tc_pr = f'<w:tcPr>{shd}<w:tcMar><w:top w:w="120" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/><w:left w:w="140" w:type="dxa"/><w:right w:w="140" w:type="dxa"/></w:tcMar></w:tcPr>'
                    b_tag = '<w:b/>' if is_header else ''
                    runs = format_inline_runs(cell)
                    t_xml.append(f'<w:tc>{tc_pr}<w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>{runs}</w:p></w:tc>')
                t_xml.append('</w:tr>')
            t_xml.append('</w:tbl>')
            body_xml_parts.append("".join(t_xml))

        if not line:
            i += 1
            continue

        if line == "---":
            # Horizontal rule
            body_xml_parts.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="12" w:space="8" w:color="E5E7EB"/></w:pBdr><w:spacing w:after="240"/></w:pPr></w:p>')
            i += 1
            continue

        if line.startswith("# "):
            title_text = escape(line[2:].strip())
            body_xml_parts.append(
                f'<w:p><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>'
                f'<w:r><w:rPr><w:b/><w:sz w:val="34"/><w:color w:val="111827"/></w:rPr><w:t>{title_text}</w:t></w:r></w:p>'
            )
            i += 1
            continue

        if line.startswith("## "):
            h2_text = escape(line[3:].strip())
            body_xml_parts.append(
                f'<w:p><w:pPr><w:spacing w:before="200" w:after="100"/></w:pPr>'
                f'<w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="1E40AF"/></w:rPr><w:t>{h2_text}</w:t></w:r></w:p>'
            )
            i += 1
            continue

        if line.startswith("### "):
            h3_text = escape(line[4:].strip())
            body_xml_parts.append(
                f'<w:p><w:pPr><w:spacing w:before="180" w:after="80"/></w:pPr>'
                f'<w:r><w:rPr><w:b/><w:sz w:val="24"/><w:color w:val="1F2937"/></w:rPr><w:t>{h3_text}</w:t></w:r></w:p>'
            )
            i += 1
            continue

        if line.startswith("* ") or line.startswith("- "):
            bullet_text = line[2:].strip()
            runs = format_inline_runs(bullet_text)
            body_xml_parts.append(
                f'<w:p><w:pPr><w:ind w:left="400" w:hanging="200"/><w:spacing w:after="80" w:line="260" w:lineRule="auto"/></w:pPr>'
                f'<w:r><w:t xml:space="preserve">•  </w:t></w:r>{runs}</w:p>'
            )
            i += 1
            continue

        # Normal paragraph
        runs = format_inline_runs(line)
        body_xml_parts.append(f'<w:p><w:pPr><w:spacing w:after="140" w:line="276" w:lineRule="auto"/></w:pPr>{runs}</w:p>')
        i += 1

    # End document body with standard 1-inch margins
    body_content = "".join(body_xml_parts)
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body_content}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", root_rels)
        docx.writestr("word/_rels/document.xml.rels", doc_rels)
        docx.writestr("word/styles.xml", styles_xml)
        docx.writestr("word/document.xml", document_xml)

    print(f"Successfully generated: {docx_path}")

if __name__ == "__main__":
    create_docx("D:\\PV\\WRITEUP.md", "D:\\PV\\GenAI_Fund_FDE_WriteUp.docx")
