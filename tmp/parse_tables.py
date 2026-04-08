import zipfile
import xml.etree.ElementTree as ET
import json

def get_text(node, namespaces):
    texts = []
    for t in node.findall('.//w:t', namespaces):
        if t.text:
            texts.append(t.text)
    return ''.join(texts).strip()

def parse_docx_tables(docx_path):
    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    tables_data = []
    
    with zipfile.ZipFile(docx_path) as docx:
        xml_content = docx.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        
        tables = tree.findall('.//w:tbl', namespaces)
        for tbl in tables:
            rows_data = []
            for tr in tbl.findall('.//w:tr', namespaces):
                row = []
                for tc in tr.findall('.//w:tc', namespaces):
                    row.append(get_text(tc, namespaces))
                rows_data.append(row)
            tables_data.append(rows_data)
            
    return tables_data

tables = parse_docx_tables(r'/tmp/一）单项指标评分表.docx')
with open('tables_debug.json', 'w', encoding='utf-8') as f:
    json.dump(tables, f, ensure_ascii=False, indent=2)
print(f"Extracted {len(tables)} tables")
