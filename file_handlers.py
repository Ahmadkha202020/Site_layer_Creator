import zipfile
import csv
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from geometry import get_excel_col_letter

def write_simple_xlsx(filepath, rows):
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Template" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )
    sheet_rows = []
    for r_idx, row in enumerate(rows, start=1):
        cells = []
        for c_idx, val in enumerate(row):
            col_letter = get_excel_col_letter(c_idx)
            val_str = escape(str(val if val is not None else ""))
            cells.append(f'<c r="{col_letter}{r_idx}" t="inlineStr"><is><t>{val_str}</t></is></c>')
        sheet_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')

    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        '</worksheet>'
    )
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('xl/workbook.xml', workbook)
        zf.writestr('xl/_rels/workbook.xml.rels', wb_rels)
        zf.writestr('xl/worksheets/sheet1.xml', sheet)


def read_simple_xlsx(filepath):
    with zipfile.ZipFile(filepath, 'r') as zf:
        shared_strings = []
        if 'xl/sharedStrings.xml' in zf.namelist():
            ss_xml = zf.read('xl/sharedStrings.xml')
            ss_root = ET.fromstring(ss_xml)
            for si in ss_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                texts = [t.text or '' for t in si.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')]
                shared_strings.append("".join(texts))

        sheet_xml = zf.read('xl/worksheets/sheet1.xml')
        root = ET.fromstring(sheet_xml)
        ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

        rows_data = []
        for row_el in root.findall('.//m:sheetData/m:row', ns):
            row_dict = {}
            max_col = 0
            for c in row_el.findall('m:c', ns):
                ref = c.attrib.get('r', '')
                col_letters = ''.join(ch for ch in ref if ch.isalpha())
                col_idx = 0
                for ch in col_letters:
                    col_idx = col_idx * 26 + (ord(ch.upper()) - 64)
                col_idx -= 1
                if col_idx > max_col:
                    max_col = col_idx

                cell_type = c.attrib.get('t', '')
                val = ""
                if cell_type == 's':
                    v_el = c.find('m:v', ns)
                    if v_el is not None and v_el.text is not None:
                        idx = int(v_el.text)
                        if 0 <= idx < len(shared_strings):
                            val = shared_strings[idx]
                elif cell_type == 'inlineStr':
                    t_el = c.find('.//m:t', ns)
                    if t_el is not None and t_el.text is not None:
                        val = t_el.text
                else:
                    v_el = c.find('m:v', ns)
                    if v_el is not None and v_el.text is not None:
                        val = v_el.text
                row_dict[col_idx] = val

            if row_dict:
                row_list = [row_dict.get(i, "") for i in range(max_col + 1)]
                rows_data.append(row_list)
        return rows_data