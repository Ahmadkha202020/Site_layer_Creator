import sys
import os
import csv
import json
import base64
import math
import subprocess
import zipfile
import webbrowser
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.sax.saxutils import escape

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QListWidget,
    QFileDialog, QMessageBox, QFrame, QComboBox, QRadioButton,
    QButtonGroup, QStackedWidget, QDialog, QScrollArea, QCheckBox,
    QColorDialog, QSpinBox, QTabWidget, QGroupBox
)
from PyQt6.QtGui import QPixmap, QAction, QColor
from PyQt6.QtCore import Qt, QUrl
import simplekml

# Optional embedded browser engine for the 2D Map Popup
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

HISTORY_FILE = "site_history.json"
BAND_SETTINGS_FILE = "band_sector_settings.json"

LOGO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAIcElEQVR"
    "4nO1Zj5OWVRn90HJ0ph8zTY39WF32vc85z/0+LTQysESwEiXkV1D+QCQIMCjKEDHEEAgVoTSUVEgdKAQr+2"
    "mUWRbN2P/VnHefS+++fbv7QSs2E3dmh112vvc999znnnOeZzudC+vCurCmZA0NDV1mZh/qdrvD7u4AZuScZw"
    "L49MjIyHVmdq2Z9fT7qqre3+l0pnXe6TV37tx3kfygmSWByzlfTfITAlvAm9lsd/8MgDlmNtfdbwLwBQA3aq"
    "PDw8OXvhPYL+l2u5g+ffqNOef57r6Y5FJ3X25mK1JKiwUypXR9zvl6kjcE4HkkP29mN5O8FcAX42tGr9e75"
    "LwgHx4e/nBKSUAW5JwXCjiAL7n7l3POd5K8G8A9Zra2qqo12pzAi32Sn9PG3P0WfR7AwrJ5M1uUUrri7cR+"
    "0fDwcA72FpjZbROBJ7nO3b9O8hsppfUCG+zPL+yb2SKSS+IZK0h+heR1eteUg49LOS54M7s7pXSPu68FsN7"
    "MavAAvkXyOwDu1wYL+3qGj57OMjNbrucAuMPM7tJJ6X5NGfper3dNk/mU0pKc8xjwYr4N3t0L+K1m9iCAh3"
    "QqYt7dxf7SBvu3A2ie4vwpOYmRkZHLpRa9Xs9SSvVXt9u9SgqTUrpFjJWyGQD8wyQf0c/B+DKxr9IJ9leSX"
    "AVgtcgg+dn/WtsBfKyqqivdfTqAqqoqaENFNrvd7rVVVS3QC0vNN8GTrMEDqMG7+26Sj+pfM1upjYj9KJ3"
    "C/hqSXwOwQRJ9rvgv6vV6UpwrZD4kR8R+zpkAuimlq9z944CuSSl9UlovIIOAB/C4me0HsC+A3unuhf2vB"
    "vvrANyr78/JK+SWZjZU2BcT0n6SubCviy3TcvdPFdOSumgTpWwEPuc8BjzJ/SR/4O5PAfiRTi3YX91kv6F"
    "i884W/8Xu/tHCvkpH7EdEqNmX44p9Oa6kD8CsOIUbpCICQfJ7wfweM3s0pTQGvJkdBHDI3X9MckthX3dJ7"
    "JPcBOCbUZbvHRi9mb1P7Pd6vStVOmJfpVPYj9KZEaVTsy/X1aVrOK42cTvJnQIf5aKy+SEAgX9a4AE8S/I"
    "wgJ+o5KJ0NpDcGDK8meR9ImbgDZTab19csd/OO2J/vLwTprVE5dQET7KAf07g3f0Fki+RPJZS2hVKVrPv"
    "7t/WndL/DRQAlUnEfvviiv0+F1fszxov78i0wnFlfJvc/cmJwAP4GckTuisNE7xPJgjggZzzRybdgGpNF1"
    "egVRYCknOuXTOcs44EAl0ubpTOnGbeUchr5x3VuOq/CR7AS2Z2zN0L+JMAfqGTCva3hKJtE55JN6B4LKPS"
    "8YeiLArDWZFzvsPdpderpBbxvUDOCfZvaqfNRt4pz5Bk7gEwLniSr5L8tTYq8GKf5Hfl2pNuIC7s/GCuBi"
    "+rD/ArU0o1+IZS6Kg3pJSWttNmyTuRNsfknchGLzbK5qS7N8H/FsBrAI5LigFs13sGKaF5Ai/mAnx5aQ3"
    "e3ceAbxnXxqqqlgX7C/ukzTrviAg5LkafcbAP878j+RrJPwD4E4Dfk3xGpzBICS1QQ5JzXtaw+fqFbeb"
    "7uW7knU3R4Czuk3fuauWddfocyePjgP8zyb8AeBPAXyfdgC5sk/nCVgHfL6w1IwOAXarxcF+ZUp1a+6TN"
    "4rj1M+N5T8cGavAkm+D/bmaTbyBqvw1+rZqSVljb0gbv7jX4iAy1caWUtuuyl+f1yzskN0rzQzYfNLMjJ"
    "E81wZP8h7ufmnQDisi6sM3uSiwJfOMlAv9AMyYLPMnvy3XdXeAPAHhSWScMbPMEeWeTft+UzZzz9rgfJ9"
    "xdpXTazE4OcgJzyouiBOqXhCv+B3jlHZWNmdXgg/kz4HX5Ii48T3JvtJrNvLOxQUzdubl7kc2HSp4CsFsl"
    "OMgduLqqqtXS64gDs4thyahiiiAl2dwET/KxJniSZ8Cb2fPurqzzIskj7r6jmTbx77zTLEvJpgRhZ4Ogmy"
    "fdgIZT0m+FtWbaLHlHkaHknTAxnZQu7z4zOxBxoS94Mzsaui9tf05Mi30zq/NOeMO2YH9Hg33dq4OKMZNu"
    "QIFJoa2VNmf1SZvNvLMwNrIr6vZM2ShlhuMeDcc93tD9X8YGd5TSbDVBYn+3uz/h7icHnuYpjU40XSuOG2"
    "mz5J3SpK+PzH+4gCdZmH+5n2lh1KhOhFk9pkQafcQ+AHLrN7WxzqBr5syZ79YGSqPSSpv98s5tzbwT851N"
    "algmA89R0zrVNC13L7ov6XyL5GmR2jmbFZ3YuGlznOna8laTvko1rTIB8EoBD+A3JMeAJ/lGW/cBvAXgn2"
    "pHO2e7NFhKKc0sF7fF/oTTtVbeqU3L3ZUqD6nuBV5BjeQpaXwL/OkGeH1/uNfrvadzLpvRurBf2sRycQe"
    "YrpW8s6bZJkaP+0j0wS+r/gG8HuDfiA29ql7B3R8fVHnGXerI+rSJddqcbLoWDcyZvNNuExGNyjiyuVfkd"
    "KZgTYs+uF+bqLpfEzq+LbomyeGGVtqsHbdfm8g+sqlIos1P5ZD3YplaUzZV91ES9weDMrMy+3lCchhTBq"
    "lRO++cYR+jjluzH0FQvrB79uzZl3WmeE2LmWh9cWOYu1VpMyLFngC9PyYPz0Tvq+jwVLSRAiv3rT/no4D"
    "lGVIpqv3R0J2qN/8="
)

# Default Band, Sector & Border Customization Settings
DEFAULT_BAND_SECTOR_SETTINGS = {
    "border": {
        "enabled": True,
        "color": "#ffffff"
    },
    "bands": {
        "Band 700": {
            "enabled": True,
            "length": 140.0,
            "width": 60.0,
            "transparency": 50,
            "color": "#00e5ff"
        },
        "Band 1800": {
            "enabled": True,
            "length": 170.0,
            "width": 60.0,
            "transparency": 50,
            "color": "#ffeb3b"
        },
        "Band 2600": {
            "enabled": True,
            "length": 100.0,
            "width": 60.0,
            "transparency": 50,
            "color": "#ff5252"
        },
        "C-Band": {
            "enabled": True,
            "length": 300.0,
            "width": 60.0,
            "transparency": 50,
            "color": "#000000"
        }
    },
    "sectors": {
        "S1": {
            "use_custom": False,
            "length": 120.0,
            "width": 60.0,
            "transparency": 50,
            "color": "#00e5ff"
        },
        "S2": {
            "use_custom": False,
            "length": 120.0,
            "width": 60.0,
            "transparency": 50,
            "color": "#ffeb3b"
        },
        "S3": {
            "use_custom": False,
            "length": 120.0,
            "width": 60.0,
            "transparency": 50,
            "color": "#ff5252"
        },
        "S4": {
            "use_custom": False,
            "length": 120.0,
            "width": 60.0,
            "transparency": 50,
            "color": "#69f0ae"
        }
    }
}

# Simple Template Columns
SIMPLE_TEMPLATE_COLS = ["site name", "lat", "long", "az-a", "az-b", "az-c", "az-d"]

# Grouped & Clear Customized Template Attributes
# Format: (Group Title, [ (column_key, display_label, default_checked, is_mandatory), ... ])
GROUPED_CUSTOM_ATTRIBUTES = [
    ("1. Mandatory & General Site Info", [
        ("site name", "Site Name (Mandatory)", True, True),
        ("lat", "Latitude (Mandatory)", True, True),
        ("long", "Longitude (Mandatory)", True, True),
        ("option", "Option Name", True, False),
        ("band", "Band (700 / 1800 / 2600 / C-Band)", True, False),
        ("site type", "Site Type (Macro / Micro / IBS / Rooftop / Greenfield)", True, False),
        ("line length", "Sector / Line Length (m)", True, False),
        ("sector width", "Sector Beamwidth (°)", True, False),
        ("general comment", "General Comment (Site Level)", True, False),
    ]),
    ("2. Sector Azimuths (S1 - S4)", [
        ("az-a", "Sector 1 Azimuth (az-a)", True, False),
        ("az-b", "Sector 2 Azimuth (az-b)", True, False),
        ("az-c", "Sector 3 Azimuth (az-c)", True, False),
        ("az-d", "Sector 4 Azimuth (az-d)", True, False),
    ]),
    ("3. Antenna Height per Sector (S1 - S4)", [
        ("antenna height s1", "Antenna Height S1 (m)", True, False),
        ("antenna height s2", "Antenna Height S2 (m)", True, False),
        ("antenna height s3", "Antenna Height S3 (m)", True, False),
        ("antenna height s4", "Antenna Height S4 (m)", False, False),
    ]),
    ("4. RS Power per Sector (S1 - S4)", [
        ("rs power s1", "RS Power S1 (dBm)", True, False),
        ("rs power s2", "RS Power S2 (dBm)", True, False),
        ("rs power s3", "RS Power S3 (dBm)", True, False),
        ("rs power s4", "RS Power S4 (dBm)", False, False),
    ]),
    ("5. PCI & MOD (S1 - S4)", [
        ("pci s1", "PCI S1", True, False),
        ("pci s2", "PCI S2", True, False),
        ("pci s3", "PCI S3", True, False),
        ("pci s4", "PCI S4", False, False),
        ("mod s1", "MOD S1 (MOD3 / MOD6 / MOD30)", True, False),
        ("mod s2", "MOD S2 (MOD3 / MOD6 / MOD30)", True, False),
        ("mod s3", "MOD S3 (MOD3 / MOD6 / MOD30)", True, False),
        ("mod s4", "MOD S4 (MOD3 / MOD6 / MOD30)", False, False),
    ]),
    ("6. Sector Comments & Extra RF Parameters", [
        ("comment s1", "Comment for Sector 1", False, False),
        ("comment s2", "Comment for Sector 2", False, False),
        ("comment s3", "Comment for Sector 3", False, False),
        ("comment s4", "Comment for Sector 4", False, False),
        ("mechanical tilt", "Mechanical Tilt (°)", False, False),
        ("electrical tilt", "Electrical Tilt (°)", False, False),
        ("technology", "Technology (2G / 3G / 4G / 5G)", False, False),
        ("cell id", "Cell ID", False, False),
    ])
]


def decode_base64_safely(b64_input):
    """Safely cleans and pads a Base64 string to prevent binascii.Error."""
    if not b64_input:
        return b""
    b64_str = "".join(b64_input.split()).rstrip("=")
    if len(b64_str) % 4 == 1:
        b64_str = b64_str[:-1]
    missing_padding = len(b64_str) % 4
    if missing_padding:
        b64_str += "=" * (4 - missing_padding)
    return base64.b64decode(b64_str)


def hex_and_transparency_to_kml_color(hex_color, transparency_pct):
    """
    Converts standard #RRGGBB hex and transparency percentage (0=opaque, 100=invisible)
    into KML's aabbggrr hex format.
    """
    hex_clean = hex_color.lstrip("#")
    if len(hex_clean) != 6:
        hex_clean = "ffffff"
    r = hex_clean[0:2]
    g = hex_clean[2:4]
    b = hex_clean[4:6]
    opacity_pct = max(0, min(100, 100 - int(transparency_pct)))
    alpha = int(round((opacity_pct / 100.0) * 255))
    return f"{alpha:02x}{b}{g}{r}"


def get_excel_col_letter(col_idx):
    result = ""
    while col_idx >= 0:
        result = chr(65 + (col_idx % 26)) + result
        col_idx = (col_idx // 26) - 1
    return result


# --- Standalone Native XLSX Writer & Reader ---
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


# --- Popup Dialog for Band, Sector & Border Customization ---
class BandSectorCustomizationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_win = parent
        self.setWindowTitle("Customize Bands, Sectors & Border")
        self.resize(760, 620)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        lbl_header = QLabel("Customize Layers by Band (700, 1800, 2600, C-Band), Sectors (S1-S4) & Border")
        lbl_header.setStyleSheet("font-size: 15px; font-weight: bold; color: #a9d3a5;")
        main_layout.addWidget(lbl_header)

        # --- Sector Border On/Off & Color Section ---
        border_frame = QFrame()
        border_frame.setObjectName("RadioGroupFrame")
        border_layout = QHBoxLayout(border_frame)
        border_layout.setContentsMargins(14, 10, 14, 10)

        lbl_border_title = QLabel("Sector Border (Outline):")
        lbl_border_title.setStyleSheet("font-weight: bold; color: #4da3ff;")
        border_layout.addWidget(lbl_border_title)

        self.chk_border_enabled = QCheckBox("Turn Border ON")
        self.chk_border_enabled.setChecked(True)
        border_layout.addWidget(self.chk_border_enabled)

        border_layout.addSpacing(20)
        lbl_b_col = QLabel("Border Color:")
        border_layout.addWidget(lbl_b_col)

        self.btn_border_color = QPushButton("#FFFFFF")
        self.btn_border_color.setFixedWidth(120)
        self.border_color_hex = "#ffffff"
        self.btn_border_color.clicked.connect(self.pick_border_color)
        border_layout.addWidget(self.btn_border_color)

        border_layout.addStretch(1)
        main_layout.addWidget(border_frame)

        # --- Tabs for Bands & Per-Sector ---
        self.tabs = QTabWidget()
        self.band_widgets = {}
        self.sector_widgets = {}

        # Tab 1: Bands Configuration
        band_tab = QWidget()
        band_layout = QVBoxLayout(band_tab)

        lbl_band_info = QLabel(
            "Configure each Band layer below. Checked bands can be generated simultaneously as multi-band layers "
            "or matched automatically from the 'band' column in Multi-Sites Mode."
        )
        lbl_band_info.setWordWrap(True)
        lbl_band_info.setStyleSheet("font-size: 12px; color: #cccccc;")
        band_layout.addWidget(lbl_band_info)

        band_grid = QGridLayout()
        band_grid.setSpacing(10)

        headers = ["Enable Band Layer", "Sector Length (m)", "Beamwidth (°)", "Transparency (%)", "Layer Color Palette"]
        for c_idx, h_text in enumerate(headers):
            lbl = QLabel(h_text)
            lbl.setStyleSheet("font-weight: bold; color: #4da3ff;")
            band_grid.addWidget(lbl, 0, c_idx)

        band_names = ["Band 700", "Band 1800", "Band 2600", "C-Band"]
        for r_idx, b_name in enumerate(band_names, start=1):
            chk = QCheckBox(b_name)
            inp_len = QLineEdit()
            inp_wid = QLineEdit()
            spin_trans = QSpinBox()
            spin_trans.setRange(0, 100)
            spin_trans.setSuffix("%")

            btn_color = QPushButton("Pick Color")
            btn_color.setFixedWidth(120)

            self.band_widgets[b_name] = {
                "enabled": chk,
                "length": inp_len,
                "width": inp_wid,
                "transparency": spin_trans,
                "color_btn": btn_color,
                "color_hex": "#000000"
            }

            btn_color.clicked.connect(lambda checked, bn=b_name: self.pick_band_color(bn))

            band_grid.addWidget(chk, r_idx, 0)
            band_grid.addWidget(inp_len, r_idx, 1)
            band_grid.addWidget(inp_wid, r_idx, 2)
            band_grid.addWidget(spin_trans, r_idx, 3)
            band_grid.addWidget(btn_color, r_idx, 4)

        band_layout.addLayout(band_grid)
        band_layout.addStretch(1)
        self.tabs.addTab(band_tab, "Band Layers (700 / 1800 / 2600 / C-Band)")

        # Tab 2: Individual Sector Overrides (S1 - S4)
        sector_tab = QWidget()
        sector_layout = QVBoxLayout(sector_tab)

        lbl_sec_info = QLabel(
            "Optional: Enable custom per-sector overrides if you want individual sectors (S1 to S4) "
            "to use custom length, beamwidth, transparency, or color when not using Band presets."
        )
        lbl_sec_info.setWordWrap(True)
        lbl_sec_info.setStyleSheet("font-size: 12px; color: #cccccc;")
        sector_layout.addWidget(lbl_sec_info)

        sec_grid = QGridLayout()
        sec_grid.setSpacing(10)

        sec_headers = ["Custom Sector", "Sector Length (m)", "Beamwidth (°)", "Transparency (%)", "Sector Color Palette"]
        for c_idx, h_text in enumerate(sec_headers):
            lbl = QLabel(h_text)
            lbl.setStyleSheet("font-weight: bold; color: #4da3ff;")
            sec_grid.addWidget(lbl, 0, c_idx)

        for r_idx, s_name in enumerate(["S1", "S2", "S3", "S4"], start=1):
            chk = QCheckBox(f"Customize {s_name}")
            inp_len = QLineEdit()
            inp_wid = QLineEdit()
            spin_trans = QSpinBox()
            spin_trans.setRange(0, 100)
            spin_trans.setSuffix("%")

            btn_color = QPushButton("Pick Color")
            btn_color.setFixedWidth(120)

            self.sector_widgets[s_name] = {
                "use_custom": chk,
                "length": inp_len,
                "width": inp_wid,
                "transparency": spin_trans,
                "color_btn": btn_color,
                "color_hex": "#00e5ff"
            }

            btn_color.clicked.connect(lambda checked, sn=s_name: self.pick_sector_color(sn))

            sec_grid.addWidget(chk, r_idx, 0)
            sec_grid.addWidget(inp_len, r_idx, 1)
            sec_grid.addWidget(inp_wid, r_idx, 2)
            sec_grid.addWidget(spin_trans, r_idx, 3)
            sec_grid.addWidget(btn_color, r_idx, 4)

        sector_layout.addLayout(sec_grid)
        sector_layout.addStretch(1)
        self.tabs.addTab(sector_tab, "Per-Sector Settings (S1 - S4)")

        main_layout.addWidget(self.tabs, 1)

        btn_row = QHBoxLayout()
        btn_reset = QPushButton("Reset to Defaults")
        btn_reset.setObjectName("RemoveBtn")
        btn_reset.clicked.connect(self.reset_to_defaults)

        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("CreateOpenBtn")
        btn_save.clicked.connect(self.save_and_close)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("BrowseBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_reset)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        main_layout.addLayout(btn_row)

    def update_color_button_style(self, btn, hex_color):
        c = QColor(hex_color)
        brightness = (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000
        text_col = "#000000" if brightness > 128 else "#ffffff"
        btn.setText(hex_color.upper())
        btn.setStyleSheet(
            f"background-color: {hex_color}; color: {text_col}; "
            f"font-weight: bold; border: 1px solid #ffffff; border-radius: 4px; padding: 6px;"
        )

    def pick_border_color(self):
        color = QColorDialog.getColor(QColor(self.border_color_hex), self, "Pick Sector Border Color")
        if color.isValid():
            self.border_color_hex = color.name()
            self.update_color_button_style(self.btn_border_color, self.border_color_hex)

    def pick_band_color(self, band_name):
        current_hex = self.band_widgets[band_name]["color_hex"]
        color = QColorDialog.getColor(QColor(current_hex), self, f"Pick Color for {band_name}")
        if color.isValid():
            hex_val = color.name()
            self.band_widgets[band_name]["color_hex"] = hex_val
            self.update_color_button_style(self.band_widgets[band_name]["color_btn"], hex_val)

    def pick_sector_color(self, sec_name):
        current_hex = self.sector_widgets[sec_name]["color_hex"]
        color = QColorDialog.getColor(QColor(current_hex), self, f"Pick Color for {sec_name}")
        if color.isValid():
            hex_val = color.name()
            self.sector_widgets[sec_name]["color_hex"] = hex_val
            self.update_color_button_style(self.sector_widgets[sec_name]["color_btn"], hex_val)

    def load_settings_into_ui(self, settings_data):
        border_cfg = settings_data.get("border", DEFAULT_BAND_SECTOR_SETTINGS["border"])
        self.chk_border_enabled.setChecked(bool(border_cfg.get("enabled", True)))
        self.border_color_hex = border_cfg.get("color", "#ffffff")
        self.update_color_button_style(self.btn_border_color, self.border_color_hex)

        bands_cfg = settings_data.get("bands", DEFAULT_BAND_SECTOR_SETTINGS["bands"])
        for b_name, w in self.band_widgets.items():
            b_data = bands_cfg.get(b_name, DEFAULT_BAND_SECTOR_SETTINGS["bands"][b_name])
            w["enabled"].setChecked(bool(b_data.get("enabled", True)))
            w["length"].setText(str(b_data.get("length", 140.0)))
            w["width"].setText(str(b_data.get("width", 60.0)))
            w["transparency"].setValue(int(b_data.get("transparency", 50)))
            hex_col = b_data.get("color", "#000000")
            w["color_hex"] = hex_col
            self.update_color_button_style(w["color_btn"], hex_col)

        sectors_cfg = settings_data.get("sectors", DEFAULT_BAND_SECTOR_SETTINGS["sectors"])
        for s_name, w in self.sector_widgets.items():
            s_data = sectors_cfg.get(s_name, DEFAULT_BAND_SECTOR_SETTINGS["sectors"][s_name])
            w["use_custom"].setChecked(bool(s_data.get("use_custom", False)))
            w["length"].setText(str(s_data.get("length", 120.0)))
            w["width"].setText(str(s_data.get("width", 60.0)))
            w["transparency"].setValue(int(s_data.get("transparency", 50)))
            hex_col = s_data.get("color", "#00e5ff")
            w["color_hex"] = hex_col
            self.update_color_button_style(w["color_btn"], hex_col)

    def reset_to_defaults(self):
        self.load_settings_into_ui(json.loads(json.dumps(DEFAULT_BAND_SECTOR_SETTINGS)))

    def save_and_close(self):
        try:
            new_settings = {
                "border": {
                    "enabled": self.chk_border_enabled.isChecked(),
                    "color": self.border_color_hex
                },
                "bands": {},
                "sectors": {}
            }
            for b_name, w in self.band_widgets.items():
                new_settings["bands"][b_name] = {
                    "enabled": w["enabled"].isChecked(),
                    "length": float(w["length"].text().strip() or 140.0),
                    "width": float(w["width"].text().strip() or 60.0),
                    "transparency": int(w["transparency"].value()),
                    "color": w["color_hex"]
                }

            for s_name, w in self.sector_widgets.items():
                new_settings["sectors"][s_name] = {
                    "use_custom": w["use_custom"].isChecked(),
                    "length": float(w["length"].text().strip() or 120.0),
                    "width": float(w["width"].text().strip() or 60.0),
                    "transparency": int(w["transparency"].value()),
                    "color": w["color_hex"]
                }

            self.parent_win.band_sector_settings = new_settings
            self.parent_win.save_band_sector_settings()
            self.parent_win.sync_band_checkboxes_from_settings()
            self.accept()
        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Please enter valid numeric values for Length and Beamwidth.")


# --- Clear & Categorized Popup Dialog for Customized Template Export ---
class CustomTemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_win = parent
        self.setWindowTitle("Customized Export Template - Select Parameters")
        self.resize(680, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        lbl_title = QLabel("Select Columns to Include in Your Custom Template:")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #a9d3a5;")
        layout.addWidget(lbl_title)

        lbl_hint = QLabel(
            "Parameters are organized into clear groups below. Check the items you want to export. "
            "When you import the filled sheet later, the program automatically maps S1-S4 parameters "
            "(Antenna Height, RS Power, PCI, MOD, Sector Comment) directly to each sector's popup table!"
        )
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("font-size: 12px; color: #cccccc;")
        layout.addWidget(lbl_hint)

        # Global Quick-Action Buttons
        sel_row = QHBoxLayout()
        btn_sel_all = QPushButton("☑ Check All Parameters")
        btn_sel_all.setObjectName("SaveBtn")
        btn_sel_all.clicked.connect(self.select_all)

        btn_reset_def = QPushButton("↺ Reset to Recommended")
        btn_reset_def.setObjectName("BrowseBtn")
        btn_reset_def.clicked.connect(self.reset_recommended)

        btn_uncheck_opt = QPushButton("☐ Uncheck All Optional")
        btn_uncheck_opt.setObjectName("BrowseBtn")
        btn_uncheck_opt.clicked.connect(self.uncheck_all_optional)

        sel_row.addWidget(btn_sel_all)
        sel_row.addWidget(btn_reset_def)
        sel_row.addWidget(btn_uncheck_opt)
        sel_row.addStretch(1)
        layout.addLayout(sel_row)

        # Scrollable Categorized Groups (2-Column Grid inside each GroupBox for clean reading)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(14)

        self.checkboxes = {}
        self.ordered_keys = []

        for group_title, items in GROUPED_CUSTOM_ATTRIBUTES:
            group_box = QGroupBox(group_title)
            group_box.setStyleSheet(
                "QGroupBox { font-weight: bold; color: #4da3ff; border: 1px solid #484848; "
                "border-radius: 6px; margin-top: 8px; padding-top: 12px; } "
                "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"
            )
            grid = QGridLayout(group_box)
            grid.setSpacing(8)

            for idx, (col_key, label_text, default_checked, is_mandatory) in enumerate(items):
                cb = QCheckBox(f"{label_text}  [{col_key}]")
                cb.setChecked(default_checked)
                if is_mandatory:
                    cb.setEnabled(False)
                self.checkboxes[col_key] = (cb, default_checked, is_mandatory)
                self.ordered_keys.append(col_key)
                row_idx = idx // 2
                col_idx = idx % 2
                grid.addWidget(cb, row_idx, col_idx)

            scroll_layout.addWidget(group_box)

        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        btn_exp_csv = QPushButton("Export Custom CSV")
        btn_exp_csv.setObjectName("ImportBtn")
        btn_exp_csv.clicked.connect(lambda: self.export_custom(is_excel=False))

        btn_exp_xls = QPushButton("Export Custom Excel (.xlsx)")
        btn_exp_xls.setObjectName("CreateOpenBtn")
        btn_exp_xls.clicked.connect(lambda: self.export_custom(is_excel=True))

        btn_close = QPushButton("Cancel")
        btn_close.setObjectName("BrowseBtn")
        btn_close.clicked.connect(self.reject)

        btn_row.addWidget(btn_exp_csv, 1)
        btn_row.addWidget(btn_exp_xls, 1)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def select_all(self):
        for cb, _, _ in self.checkboxes.values():
            cb.setChecked(True)

    def reset_recommended(self):
        for cb, default_checked, is_mandatory in self.checkboxes.values():
            cb.setChecked(True if is_mandatory else default_checked)

    def uncheck_all_optional(self):
        for cb, _, is_mandatory in self.checkboxes.values():
            cb.setChecked(True if is_mandatory else False)

    def get_selected_columns(self):
        return [k for k in self.ordered_keys if self.checkboxes[k][0].isChecked()]

    def export_custom(self, is_excel=False):
        selected_cols = self.get_selected_columns()
        if not selected_cols:
            QMessageBox.warning(self, "Warning", "Please select at least the mandatory columns.")
            return

        if is_excel:
            self.parent_win.save_template_file(selected_cols, default_name="custom_site_template.xlsx", is_excel=True)
        else:
            self.parent_win.save_template_file(selected_cols, default_name="custom_site_template.csv", is_excel=False)
        self.accept()


# --- Popup Dialog for 2D Open-Source Map Viewer (Maximizable & Default Satellite) ---
class MapViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("2D Open-Source Map Viewer")
        self.resize(1000, 700)
        self.setMinimumSize(650, 450)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.temp_map_file = os.path.join(tempfile.gettempdir(), "gis_layer_creator_2d_map.html")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            profile = self.web_view.page().profile()
            profile.setHttpUserAgent("GISLayerCreator/1.0 (mailto:ahmadkha202020@gmail.com)")
            layout.addWidget(self.web_view, 1)
        else:
            info_lbl = QLabel(
                "<h3>2D Interactive Open-Source Map Opened in Browser</h3>"
                "<p>The 2D map view has been generated and launched in your default web browser.</p>"
                "<p style='color:#a9d3a5;'><i>Tip: To view the interactive map directly inside this popup window "
                "without opening a browser, run:</i><br><code>pip install PyQt6-WebEngine</code></p>"
            )
            info_lbl.setWordWrap(True)
            info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(info_lbl, 1)

        btn_row = QHBoxLayout()
        btn_open_browser = QPushButton("Open Map in External Browser")
        btn_open_browser.setObjectName("SaveBtn")
        btn_open_browser.clicked.connect(self.open_in_external_browser)

        btn_close = QPushButton("Close Map")
        btn_close.setObjectName("BrowseBtn")
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(btn_open_browser)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def open_in_external_browser(self):
        if os.path.exists(self.temp_map_file):
            webbrowser.open(QUrl.fromLocalFile(self.temp_map_file).toString())

    def render_sites_on_map(self, sites_payload):
        payload_json = json.dumps(sites_payload)

        html_code = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="referrer" content="origin" />
    <title>GIS Layer Creator - 2D Map View</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        html, body, #map {{
            height: 100%;
            width: 100%;
            margin: 0;
            padding: 0;
            background: #1e1e1e;
            font-family: Arial, sans-serif;
        }}
        .site-tooltip {{
            background: rgba(0, 0, 0, 0.8);
            color: #ffffff;
            border: 1px solid #a9d3a5;
            border-radius: 4px;
            padding: 2px 6px;
            font-weight: bold;
            font-size: 12px;
        }}
        .popup-table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 6px;
            font-size: 12px;
        }}
        .popup-table td {{
            border: 1px solid #ccc;
            padding: 3px 6px;
        }}
        .popup-table td.key {{
            font-weight: bold;
            background-color: #f2f2f2;
            color: #111;
        }}
        .popup-table td.val {{
            color: #111;
        }}
    </style>
</head>
<body>
<div id="map"></div>
<script>
    const sites = {payload_json};

    const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
    }});

    const esriStreet = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
    }});

    const map = L.map('map', {{
        center: [30.0444, 31.2357],
        zoom: 13,
        layers: [esriSatellite]
    }});

    const baseMaps = {{
        "Satellite Imagery (Esri)": esriSatellite,
        "Esri Street Map": esriStreet
    }};
    L.control.layers(baseMaps).addTo(map);

    const featureGroup = L.featureGroup().addTo(map);
    const fallbackColors = ['#00e5ff', '#ffeb3b', '#ff5252', '#69f0ae'];

    function buildExtraHtml(extraObj) {{
        if (!extraObj || Object.keys(extraObj).length === 0) return "";
        let rows = "";
        for (const [k, v] of Object.entries(extraObj)) {{
            rows += `<tr><td class="key">${{k}}</td><td class="val">${{v}}</td></tr>`;
        }}
        return `<table class="popup-table">${{rows}}</table>`;
    }}

    sites.forEach(site => {{
        const titleLabel = site.option_name ? (site.site_name + " - " + site.option_name) : site.site_name;
        const siteExtraHtml = buildExtraHtml(site.extra_data);

        if (site.layer_mode === 'sector' || site.layer_mode === 'both') {{
            site.polygons.forEach((poly, idx) => {{
                const color = poly.color || fallbackColors[idx % fallbackColors.length];
                const fillOp = (poly.opacity !== undefined) ? poly.opacity : 0.5;
                const hasBorder = (poly.border_enabled !== undefined) ? poly.border_enabled : true;
                const borderCol = poly.border_color || '#ffffff';
                const polyExtraHtml = buildExtraHtml(poly.sector_extra || site.extra_data);

                const p = L.polygon(poly.coords, {{
                    stroke: hasBorder,
                    color: borderCol,
                    weight: hasBorder ? 2 : 0,
                    fillColor: color,
                    fillOpacity: fillOp
                }}).addTo(featureGroup);
                p.bindPopup(`<b>${{titleLabel}}</b><br>${{poly.name}}<br>Length: ${{poly.length}}m | Width: ${{poly.width}}&deg;${{polyExtraHtml}}`);
            }});
        }}

        if (site.layer_mode === 'lines') {{
            site.lines.forEach((lin, idx) => {{
                const color = lin.color || '#00e5ff';
                const linExtraHtml = buildExtraHtml(lin.sector_extra || site.extra_data);
                const l = L.polyline(lin.coords, {{
                    color: color,
                    weight: 4
                }}).addTo(featureGroup);
                l.bindPopup(`<b>${{titleLabel}}</b><br>${{lin.name}}<br>Length: ${{lin.length}}m${{linExtraHtml}}`);
            }});
        }}

        if (site.layer_mode === 'pin' || site.layer_mode === 'both' || site.layer_mode === 'lines') {{
            const m = L.marker([site.lat, site.lon]).addTo(featureGroup);
            m.bindPopup(`<b>${{titleLabel}}</b><br>Lat, Long: ${{site.lat}}, ${{site.lon}}${{siteExtraHtml}}`);
            m.bindTooltip(titleLabel, {{
                permanent: true,
                direction: 'top',
                offset: [0, -12],
                className: 'site-tooltip'
            }});
        }}
    }});

    if (featureGroup.getLayers().length > 0) {{
        map.fitBounds(featureGroup.getBounds(), {{ padding: [45, 45], maxZoom: 17 }});
    }}
</script>
</body>
</html>"""

        with open(self.temp_map_file, "w", encoding="utf-8") as f:
            f.write(html_code)

        if HAS_WEBENGINE:
            self.web_view.setUrl(QUrl.fromLocalFile(self.temp_map_file))
        else:
            self.open_in_external_browser()

        self.show()
        self.raise_()
        self.activateWindow()


# --- Popup Dialog for History List ---
class HistoryPopupDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_win = parent
        self.setWindowTitle("Saved Sites History")
        self.resize(380, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        lbl = QLabel("Click a site to load it into One Site Mode:")
        lbl.setStyleSheet("font-weight: bold; color: #77aa77;")
        layout.addWidget(lbl)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.parent_win.load_from_history)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        btn_remove = QPushButton("Remove Selected")
        btn_remove.setObjectName("RemoveBtn")
        btn_remove.clicked.connect(self.parent_win.remove_selected_history)

        btn_export = QPushButton("Export History")
        btn_export.setObjectName("SaveBtn")
        btn_export.clicked.connect(self.parent_win.export_history_data)

        btn_row.addWidget(btn_remove)
        btn_row.addWidget(btn_export)
        layout.addLayout(btn_row)


# --- Popup Dialog for "How to use?" Operational Guide ---
class HowToUseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Use - GIS Layer Creator")
        self.setFixedSize(720, 640)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        guide_html = """
        <h2 style='color:#a9d3a5; margin-top:0;'>GIS Layer Creator - Complete User Guide</h2>
        <p>Welcome to <b>GIS Layer Creator</b>. Below is the complete guide on how to use every feature:</p>

        <h3 style='color:#4da3ff;'>1. Customize Bands, Sectors & Sector Border</h3>
        <ul>
            <li><b>Sector Border On/Off & Color:</b> Turn the polygon border outline ON or OFF and pick any border color from the color palette.</li>
            <li><b>Band Layers (700 / 1800 / 2600 / C-Band):</b> Configure each band's Sector Length (defaults: 700=140m, 1800=170m, 2600=100m, C-Band=300m), Beamwidth (60°), Transparency (50%), and Color Palette (C-Band defaults to Black).</li>
            <li><b>Per-Sector Settings (S1 - S4):</b> Customize length, beamwidth, transparency, and color for each individual sector.</li>
        </ul>

        <h3 style='color:#4da3ff;'>2. Customized Export Template (Categorized Checklist)</h3>
        <ul>
            <li>Click <b>Customized Export Template (Checklist)...</b> to choose from clearly organized groups:
                <ul>
                    <li><b>Basic & Site Info:</b> Site Name, Lat, Long, Option, Band, Site Type, Length, Width, General Comment.</li>
                    <li><b>Sector Azimuths:</b> az-a, az-b, az-c, az-d.</li>
                    <li><b>Antenna Height (S1-S4):</b> antenna height s1, s2, s3, s4.</li>
                    <li><b>RS Power (S1-S4):</b> rs power s1, s2, s3, s4.</li>
                    <li><b>PCI & MOD (S1-S4):</b> pci s1..s4, mod s1..s4.</li>
                    <li><b>Sector Comments:</b> comment s1, s2, s3, s4.</li>
                </ul>
            </li>
            <li>When imported, each sector's specific data (e.g., S1 Height, S1 RS Power, S1 PCI, S1 MOD, S1 Comment) automatically appears in that sector's KML & 2D Map popup table!</li>
        </ul>

        <h3 style='color:#4da3ff;'>3. View Menu (Always on Top & Dark Mode)</h3>
        <ul>
            <li><b>Always on Top On / Off:</b> Toggle whether the main application window stays pinned above all other desktop windows.</li>
            <li><b>View History:</b> Opens the saved sites history popup window.</li>
            <li><b>Dark Mode On / Off:</b> Switch between Dark and Light themes at any time.</li>
        </ul>
        """

        lbl_content = QLabel(guide_html)
        lbl_content.setWordWrap(True)
        lbl_content.setTextFormat(Qt.TextFormat.RichText)
        content_layout.addWidget(lbl_content)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        btn_close = QPushButton("Close")
        btn_close.setObjectName("BrowseBtn")
        btn_close.clicked.connect(self.accept)
        main_layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)


# --- Main Application Window ---
class SiteLayerCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIS Layer Creator")
        self.always_on_top = True
        self.dark_mode = True

        self.apply_window_flags(initial=True)
        self.setFixedSize(880, 820)

        self.history_data = self.load_history()
        self.band_sector_settings = self.load_band_sector_settings()

        self.history_dialog = HistoryPopupDialog(self)
        self.how_to_use_dialog = HowToUseDialog(self)
        self.map_viewer_dialog = MapViewerDialog(self)
        self.custom_template_dialog = CustomTemplateDialog(self)
        self.band_sector_dialog = BandSectorCustomizationDialog(self)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.create_menu_bar()
        self.init_ui(central_widget)
        self.populate_history_list()
        self.sync_band_checkboxes_from_settings()
        self.apply_theme()

    def apply_window_flags(self, initial=False):
        flags = (
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        if not initial:
            self.show()
            self.raise_()
            self.activateWindow()

    def set_always_on_top(self, enabled):
        self.always_on_top = enabled
        if hasattr(self, "act_top_on") and hasattr(self, "act_top_off"):
            self.act_top_on.setChecked(enabled)
            self.act_top_off.setChecked(not enabled)
        self.apply_window_flags(initial=False)

    def load_band_sector_settings(self):
        if os.path.exists(BAND_SETTINGS_FILE):
            try:
                with open(BAND_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "bands" in data and "sectors" in data:
                        if "border" not in data:
                            data["border"] = json.loads(json.dumps(DEFAULT_BAND_SECTOR_SETTINGS["border"]))
                        return data
            except Exception:
                pass
        return json.loads(json.dumps(DEFAULT_BAND_SECTOR_SETTINGS))

    def save_band_sector_settings(self):
        try:
            with open(BAND_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.band_sector_settings, f, indent=4)
        except Exception:
            pass

    def open_band_sector_dialog(self):
        self.band_sector_dialog.load_settings_into_ui(self.band_sector_settings)
        self.band_sector_dialog.show()
        self.band_sector_dialog.raise_()
        self.band_sector_dialog.activateWindow()

    def sync_band_checkboxes_from_settings(self):
        bands_cfg = self.band_sector_settings.get("bands", {})
        for b_name, chk in self.one_site_band_checks.items():
            chk.blockSignals(True)
            chk.setChecked(bool(bands_cfg.get(b_name, {}).get("enabled", True)))
            chk.blockSignals(False)

    def on_quick_band_check_changed(self):
        for b_name, chk in self.one_site_band_checks.items():
            if b_name in self.band_sector_settings["bands"]:
                self.band_sector_settings["bands"][b_name]["enabled"] = chk.isChecked()
        self.save_band_sector_settings()

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # 1. File Menu
        file_menu = menu_bar.addMenu("File")

        export_simple_csv_action = QAction("Export Simple Template (CSV)", self)
        export_simple_csv_action.triggered.connect(self.export_simple_template_csv)
        file_menu.addAction(export_simple_csv_action)

        export_simple_xls_action = QAction("Export Simple Template (Excel)", self)
        export_simple_xls_action.triggered.connect(self.export_simple_template_excel)
        file_menu.addAction(export_simple_xls_action)

        export_custom_action = QAction("Customized Export Template...", self)
        export_custom_action.triggered.connect(self.open_custom_template_dialog)
        file_menu.addAction(export_custom_action)

        file_menu.addSeparator()

        change_output_action = QAction("Change Output Folder", self)
        change_output_action.triggered.connect(self.browse_output_directory)
        file_menu.addAction(change_output_action)

        # 2. Settings Menu
        settings_menu = menu_bar.addMenu("Settings")
        customize_bands_action = QAction("Customize Bands, Sectors & Border...", self)
        customize_bands_action.triggered.connect(self.open_band_sector_dialog)
        settings_menu.addAction(customize_bands_action)

        # 3. View Menu (Includes View History, Always on Top On/Off, Dark Mode On/Off)
        view_menu = menu_bar.addMenu("View")

        view_history_from_view = QAction("View History (Popup Window)", self)
        view_history_from_view.triggered.connect(self.show_history_popup)
        view_menu.addAction(view_history_from_view)

        view_menu.addSeparator()

        self.act_top_on = QAction("Always on Top On", self, checkable=True)
        self.act_top_on.setChecked(True)
        self.act_top_on.triggered.connect(lambda: self.set_always_on_top(True))
        view_menu.addAction(self.act_top_on)

        self.act_top_off = QAction("Always on Top Off", self, checkable=True)
        self.act_top_off.setChecked(False)
        self.act_top_off.triggered.connect(lambda: self.set_always_on_top(False))
        view_menu.addAction(self.act_top_off)

        view_menu.addSeparator()

        dark_on_action = QAction("Dark Mode On", self)
        dark_on_action.triggered.connect(lambda: self.set_dark_mode(True))
        view_menu.addAction(dark_on_action)

        dark_off_action = QAction("Dark Mode Off", self)
        dark_off_action.triggered.connect(lambda: self.set_dark_mode(False))
        view_menu.addAction(dark_off_action)

        # 4. History Menu
        history_menu = menu_bar.addMenu("History")

        view_history_action = QAction("View History", self)
        view_history_action.triggered.connect(self.show_history_popup)
        history_menu.addAction(view_history_action)

        export_history_action = QAction("Export History", self)
        export_history_action.triggered.connect(self.export_history_data)
        history_menu.addAction(export_history_action)

        history_menu.addSeparator()

        clear_history_action = QAction("Clear All History", self)
        clear_history_action.triggered.connect(self.clear_history)
        history_menu.addAction(clear_history_action)

        # 5. Help Menu
        help_menu = menu_bar.addMenu("Help")

        how_to_use_action = QAction("How to use?", self)
        how_to_use_action.triggered.connect(self.show_how_to_use_dialog)
        help_menu.addAction(how_to_use_action)

        help_menu.addSeparator()

        about_action = QAction("About App?", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        support_action = QAction("Support", self)
        support_action.triggered.connect(self.show_support_dialog)
        help_menu.addAction(support_action)

    def init_ui(self, central_widget):
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 16, 25, 16)
        main_layout.setSpacing(12)

        # Header: Logo + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        header_layout.setContentsMargins(10, 0, 0, 5)

        self.logo_lbl = QLabel()
        try:
            logo_bytes = decode_base64_safely(LOGO_B64)
            pixmap = QPixmap()
            pixmap.loadFromData(logo_bytes)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    90, 90,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_lbl.setPixmap(pixmap)
        except Exception:
            pass
        header_layout.addWidget(self.logo_lbl)

        self.title_lbl = QLabel()
        self.title_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch(1)

        btn_top_customize = QPushButton("⚙ Customize Bands, Sectors & Border")
        btn_top_customize.setObjectName("ViewMapBtn")
        btn_top_customize.clicked.connect(self.open_band_sector_dialog)
        header_layout.addWidget(btn_top_customize)

        main_layout.addLayout(header_layout)

        # Shared Top Settings: Output Folder + Open With
        shared_grid = QGridLayout()
        shared_grid.setSpacing(10)
        shared_grid.setColumnStretch(1, 1)

        lbl_output = QLabel("Output Folder")
        lbl_output.setFixedWidth(150)
        self.input_output = QLineEdit()
        default_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        self.input_output.setText(default_desktop if os.path.exists(default_desktop) else "")
        self.input_output.setPlaceholderText("Select folder to save KML file...")

        btn_browse_output = QPushButton("Browse")
        btn_browse_output.setObjectName("BrowseBtn")
        btn_browse_output.setFixedWidth(90)
        btn_browse_output.clicked.connect(self.browse_output_directory)

        shared_grid.addWidget(lbl_output, 0, 0)
        shared_grid.addWidget(self.input_output, 0, 1)
        shared_grid.addWidget(btn_browse_output, 0, 2)

        self.lbl_viewer = QLabel("Open KML File With:")
        self.combo_viewer = QComboBox()
        self.combo_viewer.addItems(["Google Earth", "QGIS", "ArcGIS Earth"])

        shared_grid.addWidget(self.lbl_viewer, 1, 0)
        shared_grid.addWidget(self.combo_viewer, 1, 1, 1, 2)

        main_layout.addLayout(shared_grid)

        # Mode Switcher Tabs
        mode_tabs_layout = QHBoxLayout()
        mode_tabs_layout.setSpacing(12)

        self.btn_mode_one = QPushButton("ONE SITE MODE")
        self.btn_mode_one.setCheckable(True)
        self.btn_mode_one.setChecked(True)
        self.btn_mode_one.setObjectName("ModeTabBtn")
        self.btn_mode_one.clicked.connect(lambda: self.switch_mode(0))

        self.btn_mode_multi = QPushButton("MULTI SITES MODE (CSV / EXCEL)")
        self.btn_mode_multi.setCheckable(True)
        self.btn_mode_multi.setObjectName("ModeTabBtn")
        self.btn_mode_multi.clicked.connect(lambda: self.switch_mode(1))

        mode_tabs_layout.addWidget(self.btn_mode_one)
        mode_tabs_layout.addWidget(self.btn_mode_multi)
        main_layout.addLayout(mode_tabs_layout)

        # Stacked Widget for the 2 Modes
        self.stacked_modes = QStackedWidget()
        self.page_one_site = self.build_one_site_page()
        self.page_multi_sites = self.build_multi_sites_page()

        self.stacked_modes.addWidget(self.page_one_site)
        self.stacked_modes.addWidget(self.page_multi_sites)

        main_layout.addWidget(self.stacked_modes, 1)

    def build_one_site_page(self):
        page = QFrame()
        page.setObjectName("ModeBox")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 16, 18, 16)

        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        for c in range(1, 5):
            form_layout.setColumnStretch(c, 1)

        lbl_name = QLabel("Site Name / Option")
        lbl_name.setFixedWidth(150)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Site Name")

        self.input_option = QLineEdit()
        self.input_option.setPlaceholderText("Option")

        form_layout.addWidget(lbl_name, 0, 0)
        form_layout.addWidget(self.input_name, 0, 1, 1, 3)
        form_layout.addWidget(self.input_option, 0, 4)

        lbl_coords = QLabel("Latitude, Longitude")
        self.input_coords = QLineEdit()
        self.input_coords.setPlaceholderText("e.g. 30.0444, 31.2357")

        form_layout.addWidget(lbl_coords, 1, 0)
        form_layout.addWidget(self.input_coords, 1, 1, 1, 4)

        lbl_length = QLabel("Default Length (m)")
        self.input_length = QLineEdit("120")

        self.lbl_width = QLabel("Default Width °")
        self.lbl_width.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.input_width = QLineEdit("60")

        form_layout.addWidget(lbl_length, 2, 0)
        form_layout.addWidget(self.input_length, 2, 1)
        form_layout.addWidget(self.lbl_width, 2, 3)
        form_layout.addWidget(self.input_width, 2, 4)

        headers = ["", "S1", "S2", "S3", "S4"]
        for i, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold;")
            form_layout.addWidget(lbl, 3, i)

        lbl_azimuth = QLabel("Azimuth °")
        form_layout.addWidget(lbl_azimuth, 4, 0)

        self.az_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setPlaceholderText(f"S{i+1} Az")
            self.az_inputs.append(inp)
            form_layout.addWidget(inp, 4, i + 1)

        layout.addLayout(form_layout)

        # Band Layer Selection Bar in One Site Mode
        band_frame = QFrame()
        band_frame.setObjectName("RadioGroupFrame")
        band_layout = QHBoxLayout(band_frame)
        band_layout.setContentsMargins(15, 8, 15, 8)

        self.chk_use_band_layers = QCheckBox("Generate Band Layers:")
        self.chk_use_band_layers.setChecked(True)
        self.chk_use_band_layers.setStyleSheet("color: #a9d3a5; font-weight: bold;")
        band_layout.addWidget(self.chk_use_band_layers)

        self.one_site_band_checks = {}
        for b_name in ["Band 700", "Band 1800", "Band 2600", "C-Band"]:
            cb = QCheckBox(b_name)
            cb.setChecked(True)
            cb.toggled.connect(self.on_quick_band_check_changed)
            self.one_site_band_checks[b_name] = cb
            band_layout.addWidget(cb)

        btn_cfg_bands = QPushButton("Settings / Border / Colors...")
        btn_cfg_bands.setObjectName("BrowseBtn")
        btn_cfg_bands.clicked.connect(self.open_band_sector_dialog)
        band_layout.addStretch(1)
        band_layout.addWidget(btn_cfg_bands)

        layout.addWidget(band_frame)

        # Layer Output Type Radio Group
        radio_frame = QFrame()
        radio_frame.setObjectName("RadioGroupFrame")
        radio_layout = QHBoxLayout(radio_frame)
        radio_layout.setContentsMargins(15, 8, 15, 8)

        self.lbl_one_type = QLabel("Layer Output Type:")
        radio_layout.addWidget(self.lbl_one_type)

        self.one_type_group = QButtonGroup(self)
        self.rb_one_pin = QRadioButton("Pin Only")
        self.rb_one_sector = QRadioButton("Sectorized Only")
        self.rb_one_lines = QRadioButton("Lines")
        self.rb_one_both = QRadioButton("Both")
        self.rb_one_both.setChecked(True)

        for rb in (self.rb_one_pin, self.rb_one_sector, self.rb_one_lines, self.rb_one_both):
            self.one_type_group.addButton(rb)
            rb.toggled.connect(self.toggle_one_site_fields)
            radio_layout.addWidget(rb)

        radio_layout.addStretch(1)
        layout.addWidget(radio_frame)
        layout.addStretch(1)

        btn_save = QPushButton("Save Site to History")
        btn_save.setObjectName("SaveBtn")
        btn_save.clicked.connect(lambda: self.save_to_history(show_message=True))
        layout.addWidget(btn_save)

        btn_row = QHBoxLayout()
        btn_create_only = QPushButton("Create Layer")
        btn_create_only.setObjectName("CreateOnlyBtn")
        btn_create_only.clicked.connect(lambda: self.create_single_kml(open_file=False))

        btn_create_open = QPushButton("Create and Open Layer")
        btn_create_open.setObjectName("CreateOpenBtn")
        btn_create_open.clicked.connect(lambda: self.create_single_kml(open_file=True))

        btn_view_map = QPushButton("View in Map")
        btn_view_map.setObjectName("ViewMapBtn")
        btn_view_map.clicked.connect(self.view_single_site_in_map)

        btn_row.addWidget(btn_create_only, 1)
        btn_row.addWidget(btn_create_open, 1)
        btn_row.addWidget(btn_view_map, 1)
        layout.addLayout(btn_row)

        return page

    def build_multi_sites_page(self):
        page = QFrame()
        page.setObjectName("ModeBox")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 16, 18, 16)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        lbl_step1 = QLabel("1. Simple Template")
        lbl_step1.setFixedWidth(150)

        btn_template_csv = QPushButton("Simple CSV Template")
        btn_template_csv.setObjectName("ImportBtn")
        btn_template_csv.clicked.connect(self.export_simple_template_csv)

        btn_template_xls = QPushButton("Simple Excel Template")
        btn_template_xls.setObjectName("SaveBtn")
        btn_template_xls.clicked.connect(self.export_simple_template_excel)

        grid.addWidget(lbl_step1, 0, 0)
        grid.addWidget(btn_template_csv, 0, 1)
        grid.addWidget(btn_template_xls, 0, 2, 1, 2)

        lbl_step_custom = QLabel("   Custom Template")
        btn_custom_tmpl = QPushButton("Customized Export Template (Categorized Checklist)...")
        btn_custom_tmpl.setObjectName("ViewMapBtn")
        btn_custom_tmpl.clicked.connect(self.open_custom_template_dialog)

        grid.addWidget(lbl_step_custom, 1, 0)
        grid.addWidget(btn_custom_tmpl, 1, 1, 1, 3)

        lbl_step2 = QLabel("2. Select Filled File")
        self.input_csv_path = QLineEdit()
        self.input_csv_path.setPlaceholderText("Browse and select your filled Simple or Customized (.csv / .xlsx) file...")
        btn_browse_csv = QPushButton("Browse File")
        btn_browse_csv.setObjectName("BrowseBtn")
        btn_browse_csv.clicked.connect(self.browse_csv_file)

        grid.addWidget(lbl_step2, 2, 0)
        grid.addWidget(self.input_csv_path, 2, 1, 1, 2)
        grid.addWidget(btn_browse_csv, 2, 3)

        lbl_multi_len = QLabel("Default Length (m)")
        self.input_multi_length = QLineEdit("120")

        lbl_multi_wid = QLabel("Default Width °")
        lbl_multi_wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.input_multi_width = QLineEdit("60")

        grid.addWidget(lbl_multi_len, 3, 0)
        grid.addWidget(self.input_multi_length, 3, 1)
        grid.addWidget(lbl_multi_wid, 3, 2)
        grid.addWidget(self.input_multi_width, 3, 3)

        lbl_out_name = QLabel("Output File Name")
        self.input_multi_outname = QLineEdit("imported_multi_sites.kml")

        grid.addWidget(lbl_out_name, 4, 0)
        grid.addWidget(self.input_multi_outname, 4, 1, 1, 3)

        layout.addLayout(grid)

        # Multi-Site Band Mode Option
        multi_band_frame = QFrame()
        multi_band_frame.setObjectName("RadioGroupFrame")
        mb_layout = QHBoxLayout(multi_band_frame)
        mb_layout.setContentsMargins(15, 8, 15, 8)

        self.chk_multi_use_bands = QCheckBox("Apply Customized Band Layers (700 / 1800 / 2600 / C-Band) to Imported Sites")
        self.chk_multi_use_bands.setChecked(True)
        mb_layout.addWidget(self.chk_multi_use_bands)

        btn_mb_cfg = QPushButton("Band & Border Settings...")
        btn_mb_cfg.setObjectName("BrowseBtn")
        btn_mb_cfg.clicked.connect(self.open_band_sector_dialog)
        mb_layout.addStretch(1)
        mb_layout.addWidget(btn_mb_cfg)

        layout.addWidget(multi_band_frame)

        radio_frame = QFrame()
        radio_frame.setObjectName("RadioGroupFrame")
        radio_layout = QHBoxLayout(radio_frame)
        radio_layout.setContentsMargins(15, 8, 15, 8)

        self.lbl_multi_type = QLabel("Layer Output Type:")
        radio_layout.addWidget(self.lbl_multi_type)

        self.multi_type_group = QButtonGroup(self)
        self.rb_multi_pin = QRadioButton("Pin Only")
        self.rb_multi_sector = QRadioButton("Sectorized Only")
        self.rb_multi_lines = QRadioButton("Lines")
        self.rb_multi_both = QRadioButton("Both")
        self.rb_multi_both.setChecked(True)

        for rb in (self.rb_multi_pin, self.rb_multi_sector, self.rb_multi_lines, self.rb_multi_both):
            self.multi_type_group.addButton(rb)
            radio_layout.addWidget(rb)

        radio_layout.addStretch(1)
        layout.addWidget(radio_frame)
        layout.addStretch(1)

        btn_row = QHBoxLayout()
        btn_multi_create = QPushButton("Create Multi-Sites Layer")
        btn_multi_create.setObjectName("CreateOnlyBtn")
        btn_multi_create.clicked.connect(lambda: self.create_multi_sites_kml(open_file=False))

        btn_multi_open = QPushButton("Create & Open Layer")
        btn_multi_open.setObjectName("CreateOpenBtn")
        btn_multi_open.clicked.connect(lambda: self.create_multi_sites_kml(open_file=True))

        btn_multi_map = QPushButton("View in Map")
        btn_multi_map.setObjectName("ViewMapBtn")
        btn_multi_map.clicked.connect(self.view_multi_sites_in_map)

        btn_row.addWidget(btn_multi_create, 1)
        btn_row.addWidget(btn_multi_open, 1)
        btn_row.addWidget(btn_multi_map, 1)
        layout.addLayout(btn_row)

        return page

    def switch_mode(self, index):
        self.stacked_modes.setCurrentIndex(index)
        self.btn_mode_one.setChecked(index == 0)
        self.btn_mode_multi.setChecked(index == 1)

    def get_one_site_layer_mode(self):
        if self.rb_one_pin.isChecked():
            return "pin"
        elif self.rb_one_sector.isChecked():
            return "sector"
        elif self.rb_one_lines.isChecked():
            return "lines"
        return "both"

    def get_multi_site_layer_mode(self):
        if self.rb_multi_pin.isChecked():
            return "pin"
        elif self.rb_multi_sector.isChecked():
            return "sector"
        elif self.rb_multi_lines.isChecked():
            return "lines"
        return "both"

    def toggle_one_site_fields(self):
        is_pin_only = self.rb_one_pin.isChecked()
        is_lines = self.rb_one_lines.isChecked()

        self.input_length.setEnabled(not is_pin_only)
        self.input_width.setEnabled(not is_pin_only and not is_lines)
        for inp in self.az_inputs:
            inp.setEnabled(not is_pin_only)

    def set_dark_mode(self, enabled):
        self.dark_mode = enabled
        self.apply_theme()

    def apply_theme(self):
        style = self.get_stylesheet(self.dark_mode)
        self.setStyleSheet(style)
        self.history_dialog.setStyleSheet(style)
        self.how_to_use_dialog.setStyleSheet(style)
        self.map_viewer_dialog.setStyleSheet(style)
        self.custom_template_dialog.setStyleSheet(style)
        self.band_sector_dialog.setStyleSheet(style)

        top_color = "#ffffff" if self.dark_mode else "#1e293b"
        bottom_color = "#a9d3a5" if self.dark_mode else "#2e7d32"
        accent_style = f"font-weight: bold; color: {bottom_color};"

        self.title_lbl.setText(
            f"<div style='font-size:32px; font-weight:bold; line-height:1.15;'>"
            f"<span style='color:{top_color};'>GIS LAYER</span><br>"
            f"<span style='color:{bottom_color};'>CREATOR</span>"
            f"</div>"
        )
        self.lbl_viewer.setStyleSheet(accent_style)
        self.lbl_one_type.setStyleSheet(accent_style)
        self.lbl_multi_type.setStyleSheet(accent_style)

    def get_stylesheet(self, dark=True):
        if dark:
            return """
                QMainWindow, QWidget, QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                }
                QTabWidget::pane {
                    border: 1px solid #444;
                    background: #232323;
                }
                QTabBar::tab {
                    background: #3c3f41;
                    color: #ccc;
                    padding: 8px 14px;
                    border: 1px solid #555;
                }
                QTabBar::tab:selected {
                    background: #005a9e;
                    color: #fff;
                    font-weight: bold;
                }
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border-bottom: 1px solid #3c3f41;
                }
                QMenuBar::item:selected { background-color: #3c3f41; }
                QMenu {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555;
                }
                QMenu::item:selected { background-color: #005a9e; }
                QFrame#ModeBox {
                    background-color: #232323;
                    border: 1px solid #3c3f41;
                    border-radius: 6px;
                }
                QFrame#RadioGroupFrame {
                    background-color: #323232;
                    border: 1px solid #484848;
                    border-radius: 5px;
                }
                QLineEdit, QComboBox, QSpinBox {
                    background-color: #3c3f41;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 6px;
                    color: white;
                }
                QLineEdit:disabled {
                    background-color: #262626;
                    color: #666;
                    border: 1px solid #3a3a3a;
                }
                QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #77aa77; }
                QListWidget {
                    background-color: #3c3f41;
                    border: 1px solid #555;
                    border-radius: 4px;
                    outline: none;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #4a4d4f;
                }
                QListWidget::item:hover { background-color: #4a4d4f; }
                QListWidget::item:selected {
                    background-color: #008000;
                    color: white;
                    font-weight: bold;
                }
                QPushButton#ModeTabBtn {
                    background-color: #3c3f41;
                    color: #bbbbbb;
                    border: 1px solid #555;
                    border-radius: 5px;
                    padding: 11px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton#ModeTabBtn:checked {
                    background-color: #005a9e;
                    color: #ffffff;
                    border: 1px solid #4da3ff;
                }
                QPushButton#CreateOnlyBtn {
                    background-color: #2e7d32;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#CreateOnlyBtn:hover { background-color: #388e3c; }
                QPushButton#CreateOpenBtn {
                    background-color: #008000;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#CreateOpenBtn:hover { background-color: #009900; }
                QPushButton#ViewMapBtn {
                    background-color: #6a1b9a;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 11px;
                }
                QPushButton#ViewMapBtn:hover { background-color: #8e24aa; }
                QPushButton#SaveBtn {
                    background-color: #005a9e;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 11px;
                }
                QPushButton#SaveBtn:hover { background-color: #0078d4; }
                QPushButton#ImportBtn {
                    background-color: #d83b01;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 10px;
                }
                QPushButton#ImportBtn:hover { background-color: #ea4a1f; }
                QPushButton#BrowseBtn {
                    background-color: #555555;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                QPushButton#BrowseBtn:hover { background-color: #666666; }
                QPushButton#RemoveBtn {
                    background-color: #9e6a00;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 9px;
                }
                QPushButton#RemoveBtn:hover { background-color: #c08000; }
                QRadioButton, QCheckBox {
                    spacing: 8px;
                    font-weight: bold;
                }
            """
        else:
            return """
                QMainWindow, QWidget, QDialog {
                    background-color: #f4f6f8;
                    color: #1e293b;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                }
                QMenuBar {
                    background-color: #e2e8f0;
                    color: #1e293b;
                    border-bottom: 1px solid #cbd5e1;
                }
                QMenuBar::item:selected { background-color: #cbd5e1; }
                QMenu {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                }
                QMenu::item:selected {
                    background-color: #0284c7;
                    color: #ffffff;
                }
                QFrame#ModeBox {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                }
                QFrame#RadioGroupFrame {
                    background-color: #f1f5f9;
                    border: 1px solid #cbd5e1;
                    border-radius: 5px;
                }
                QLineEdit, QComboBox, QSpinBox {
                    background-color: #ffffff;
                    border: 1px solid #94a3b8;
                    border-radius: 4px;
                    padding: 6px;
                    color: #1e293b;
                }
                QLineEdit:disabled {
                    background-color: #e2e8f0;
                    color: #94a3b8;
                }
                QListWidget {
                    background-color: #ffffff;
                    border: 1px solid #94a3b8;
                    border-radius: 4px;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #e2e8f0;
                }
                QListWidget::item:selected {
                    background-color: #16a34a;
                    color: white;
                    font-weight: bold;
                }
                QPushButton#ModeTabBtn {
                    background-color: #e2e8f0;
                    color: #475569;
                    border: 1px solid #cbd5e1;
                    border-radius: 5px;
                    padding: 11px;
                    font-weight: bold;
                }
                QPushButton#ModeTabBtn:checked {
                    background-color: #0284c7;
                    color: #ffffff;
                    border: 1px solid #0369a1;
                }
                QPushButton#CreateOnlyBtn {
                    background-color: #2e7d32;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#CreateOpenBtn {
                    background-color: #15803d;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#ViewMapBtn {
                    background-color: #7b1fa2;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 11px;
                }
                QPushButton#SaveBtn {
                    background-color: #0284c7;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 11px;
                }
                QPushButton#ImportBtn {
                    background-color: #ea580c;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 10px;
                }
                QPushButton#BrowseBtn {
                    background-color: #64748b;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                QPushButton#RemoveBtn {
                    background-color: #b45309;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 9px;
                }
                QRadioButton, QCheckBox {
                    spacing: 8px;
                    font-weight: bold;
                }
            """

    def browse_output_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.input_output.setText(folder)

    def browse_csv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Template File", "", "Template Files (*.csv *.xlsx);;CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )
        if file_path:
            self.input_csv_path.setText(file_path)

    def save_template_file(self, columns_list, default_name, is_excel=False):
        if is_excel:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel Template", default_name, "Excel Files (*.xlsx)")
            if not file_path:
                return
            try:
                if not file_path.lower().endswith(".xlsx"):
                    file_path += ".xlsx"
                write_simple_xlsx(file_path, [columns_list])
                QMessageBox.information(self, "Success", f"Excel Template exported successfully with {len(columns_list)} columns!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))
        else:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV Template", default_name, "CSV Files (*.csv)")
            if not file_path:
                return
            try:
                if not file_path.lower().endswith(".csv"):
                    file_path += ".csv"
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns_list)
                QMessageBox.information(self, "Success", f"CSV Template exported successfully with {len(columns_list)} columns!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def export_simple_template_csv(self):
        self.save_template_file(SIMPLE_TEMPLATE_COLS, "simple_site_template.csv", is_excel=False)

    def export_simple_template_excel(self):
        self.save_template_file(SIMPLE_TEMPLATE_COLS, "simple_site_template.xlsx", is_excel=True)

    def open_custom_template_dialog(self):
        self.custom_template_dialog.show()
        self.custom_template_dialog.raise_()
        self.custom_template_dialog.activateWindow()

    def show_how_to_use_dialog(self):
        self.how_to_use_dialog.show()
        self.how_to_use_dialog.raise_()
        self.how_to_use_dialog.activateWindow()

    def show_about_dialog(self):
        about_text = (
            "<h3>GIS Layer Creator</h3>"
            "<p>A specialized telecom & GIS design tool built to quickly generate "
            "single-site and multi-site KML layers (Pins, Sector Polygons, Multi-Band Layers, and Azimuth Lines) "
            "for Google Earth, QGIS, ArcGIS Earth, and an integrated 2D Satellite Map viewer.</p>"
            "<p><b>Developed by:</b> Ahmad</p>"
        )
        QMessageBox.information(self, "About App", about_text)

    def show_support_dialog(self):
        support_text = (
            "<h3>Technical Support & Contact</h3>"
            "<p>If you need any assistance or have feedback, feel free to reach out:</p>"
            "<p>📧 <b>Email:</b> <a href='mailto:ahmadkha202020@gmail.com'>ahmadkha202020@gmail.com</a></p>"
            "<p>💬 <b>WhatsApp:</b> +201021785230</p>"
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("Support")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(support_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def show_history_popup(self):
        self.populate_history_list()
        self.history_dialog.show()
        self.history_dialog.raise_()
        self.history_dialog.activateWindow()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_history(self):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history_data, f, ensure_ascii=False, indent=4)

    def populate_history_list(self):
        self.history_dialog.list_widget.clear()
        for site_name in self.history_data.keys():
            self.history_dialog.list_widget.addItem(site_name)

    def load_from_history(self, item):
        site_name = item.text()
        if not site_name or site_name not in self.history_data:
            return

        self.switch_mode(0)

        data = self.history_data[site_name]
        self.input_name.setText(data.get("site_name", ""))
        self.input_option.setText(data.get("option_name", ""))
        self.input_coords.setText(data.get("coords", ""))
        self.input_length.setText(data.get("length", "120") or "120")
        self.input_width.setText(data.get("width", "60") or "60")

        layer_mode = data.get("layer_mode", "both")
        if layer_mode == "pin":
            self.rb_one_pin.setChecked(True)
        elif layer_mode == "sector":
            self.rb_one_sector.setChecked(True)
        elif layer_mode == "lines":
            self.rb_one_lines.setChecked(True)
        else:
            self.rb_one_both.setChecked(True)

        sectors = data.get("sectors", [])
        for i in range(4):
            if i < len(sectors):
                self.az_inputs[i].setText(sectors[i].get("azimuth", ""))
            else:
                self.az_inputs[i].clear()

    def remove_selected_history(self):
        current_item = self.history_dialog.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self.history_dialog, "No Selection", "Please select a history item to remove.")
            return

        site_name = current_item.text()
        reply = QMessageBox.question(
            self.history_dialog, 'Confirm',
            f"Are you sure you want to remove '{site_name}' from history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if site_name in self.history_data:
                del self.history_data[site_name]
                self.save_history()
                self.populate_history_list()
                QMessageBox.information(self.history_dialog, "Success", f"'{site_name}' removed from history.")

    def clear_history(self):
        reply = QMessageBox.question(
            self, 'Confirm', 'Are you sure you want to clear all history?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_data = {}
            self.save_history()
            self.populate_history_list()
            QMessageBox.information(self, "Success", "History cleared successfully.")

    def export_history_data(self):
        if not self.history_data:
            QMessageBox.warning(self, "Empty History", "There are no saved sites in history to export.")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_filename = f"exported history {timestamp}.csv"
        default_dir = self.input_output.text().strip() or os.path.expanduser("~")
        initial_path = os.path.join(default_dir, default_filename)

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export History", initial_path, "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        try:
            rows = [["site name", "option", "lat", "long", "az-a", "az-b", "az-c", "az-d", "line length"]]
            for site_key, data in self.history_data.items():
                s_name = data.get("site_name", site_key)
                opt = data.get("option_name", "")
                coords = data.get("coords", "")
                lat_str, lon_str = "", ""
                if "," in coords:
                    parts = coords.split(",")
                    lat_str = parts[0].strip()
                    lon_str = parts[1].strip()

                sectors = data.get("sectors", [])
                az_list = []
                for i in range(4):
                    az_list.append(sectors[i].get("azimuth", "") if i < len(sectors) else "")

                length_str = data.get("length", "120")
                rows.append([s_name, opt, lat_str, lon_str, az_list[0], az_list[1], az_list[2], az_list[3], length_str])

            if file_path.lower().endswith(".xlsx") or "Excel" in selected_filter:
                if not file_path.lower().endswith(".xlsx"):
                    file_path += ".xlsx"
                write_simple_xlsx(file_path, rows)
            else:
                if not file_path.lower().endswith(".csv"):
                    file_path += ".csv"
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)

            QMessageBox.information(self, "Success", f"History exported successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def add_site_to_history(self, site_name, option_name, coord_text, length, width, layer_mode, sectors_data, extra_data=None):
        self.history_data[site_name] = {
            "site_name": site_name,
            "option_name": option_name,
            "coords": coord_text,
            "length": str(length),
            "width": str(width),
            "layer_mode": layer_mode,
            "sectors": sectors_data,
            "extra_data": extra_data or {}
        }

    def save_to_history(self, show_message=True):
        try:
            site_name = self.input_name.text().strip() or "Site"
            option_name = self.input_option.text().strip()
            coord_text = self.input_coords.text().strip()

            if not coord_text:
                raise ValueError("Coordinates are empty. Please enter Lat, Long.")

            try:
                lat_str, lon_str = coord_text.split(',')
                float(lat_str.strip())
                float(lon_str.strip())
            except Exception:
                raise ValueError("Coordinate format invalid. Use 'Lat, Long'.")

            length_val = self.input_length.text().strip() or "120"
            width_val = self.input_width.text().strip() or "60"
            layer_mode = self.get_one_site_layer_mode()
            sectors_data = [{"azimuth": self.az_inputs[i].text().strip()} for i in range(4)]

            self.add_site_to_history(
                site_name, option_name, coord_text,
                length_val, width_val, layer_mode, sectors_data
            )

            self.save_history()
            self.populate_history_list()

            if show_message:
                QMessageBox.information(self, "Saved", f"Site '{site_name}' saved to history successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def calculate_destination(self, lat, lon, bearing, distance):
        R = 6371000.0
        lat1 = math.radians(lat)
        lon1 = math.radians(lon)
        bearing_rad = math.radians(bearing)

        lat2 = math.asin(
            math.sin(lat1) * math.cos(distance / R) +
            math.cos(lat1) * math.sin(distance / R) * math.cos(bearing_rad)
        )
        lon2 = lon1 + math.atan2(
            math.sin(bearing_rad) * math.sin(distance / R) * math.cos(lat1),
            math.cos(distance / R) - math.sin(lat1) * math.sin(lat2)
        )
        return math.degrees(lat2), math.degrees(lon2)

    def match_band_name(self, raw_band_str):
        if not raw_band_str:
            return None
        s = str(raw_band_str).strip().lower()
        if "700" in s:
            return "Band 700"
        if "1800" in s:
            return "Band 1800"
        if "2600" in s:
            return "Band 2600"
        if "c-band" in s or "cband" in s or "3500" in s or s == "c":
            return "C-Band"
        return None

    def get_active_bands_for_site(self, use_bands_flag, specific_band_str=None):
        bands_cfg = self.band_sector_settings.get("bands", DEFAULT_BAND_SECTOR_SETTINGS["bands"])
        matched = self.match_band_name(specific_band_str)
        if matched and matched in bands_cfg:
            b = bands_cfg[matched]
            return [{
                "band_name": matched,
                "length": float(b["length"]),
                "width": float(b["width"]),
                "transparency": int(b["transparency"]),
                "color": b["color"]
            }]

        if use_bands_flag:
            active_list = []
            for b_name in ["Band 700", "Band 1800", "Band 2600", "C-Band"]:
                b = bands_cfg.get(b_name, {})
                if b.get("enabled", False):
                    active_list.append({
                        "band_name": b_name,
                        "length": float(b.get("length", 140.0)),
                        "width": float(b.get("width", 60.0)),
                        "transparency": int(b.get("transparency", 50)),
                        "color": b.get("color", "#00e5ff")
                    })
            active_list.sort(key=lambda x: x["length"], reverse=True)
            return active_list
        return []

    def get_sector_parameters(self, sector_idx, default_length, default_width, band_override=None):
        s_key = f"S{sector_idx + 1}"
        sec_cfg = self.band_sector_settings.get("sectors", {}).get(s_key, {})

        if band_override:
            length = band_override["length"]
            width = band_override["width"]
            trans = band_override["transparency"]
            color = band_override["color"]
            if sec_cfg.get("use_custom", False):
                length = float(sec_cfg.get("length", length))
                width = float(sec_cfg.get("width", width))
            return length, width, trans, color, f"{band_override['band_name']} - {s_key}"

        if sec_cfg.get("use_custom", False):
            return (
                float(sec_cfg.get("length", default_length)),
                float(sec_cfg.get("width", default_width)),
                int(sec_cfg.get("transparency", 50)),
                sec_cfg.get("color", "#00e5ff"),
                s_key
            )

        fallback_colors = ["#00e5ff", "#ffeb3b", "#ff5252", "#69f0ae"]
        return (
            default_length,
            default_width,
            50,
            fallback_colors[sector_idx % len(fallback_colors)],
            s_key
        )

    def filter_extra_data_for_sector(self, extra_data, sector_idx=None):
        """
        Filters extra_data so that when clicking Sector N (1..4), only Sector N's
        specific attributes (e.g., antenna height s1, rs power s1, pci s1, mod s1, comment s1)
        and general site attributes are displayed.
        """
        if not extra_data:
            return {}
        if sector_idx is None:
            return extra_data

        target_s = f"s{sector_idx + 1}"
        other_sectors = {f"s{j}" for j in range(1, 5) if j != (sector_idx + 1)}

        filtered = {}
        for k, v in extra_data.items():
            k_low = k.strip().lower()
            tokens = k_low.replace("_", " ").replace("-", " ").split()
            if any(os_tok in tokens for os_tok in other_sectors):
                continue
            filtered[k] = v
        return filtered

    def build_kml_description_html(self, site_name, option_name, lat, lon, length, sector_width, band_name="", extra_data=None, sector_idx=None):
        rows_html = f"""
        <tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Site Name</td><td style='padding:4px;'>{escape(str(site_name))}</td></tr>
        <tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Coordinates</td><td style='padding:4px;'>{lat}, {lon}</td></tr>
        """
        if option_name:
            rows_html += f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Option</td><td style='padding:4px;'>{escape(str(option_name))}</td></tr>"
        if band_name:
            rows_html += f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Band Layer</td><td style='padding:4px;'>{escape(str(band_name))}</td></tr>"
        if sector_idx is not None:
            rows_html += f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Sector</td><td style='padding:4px;'>S{sector_idx + 1}</td></tr>"
        rows_html += f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Length / Width</td><td style='padding:4px;'>{length}m / {sector_width}°</td></tr>"

        filtered_extra = self.filter_extra_data_for_sector(extra_data, sector_idx)
        for k, v in filtered_extra.items():
            rows_html += f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>{escape(str(k))}</td><td style='padding:4px;'>{escape(str(v))}</td></tr>"

        return f"<table border='1' style='border-collapse:collapse; font-family:Arial; font-size:12px;'>{rows_html}</table>"

    def generate_site_kml(self, fol, site_name, option_name, lat, lon, height, length, azims, layer_mode, sector_width, extra_data=None, use_bands=False):
        border_cfg = self.band_sector_settings.get("border", DEFAULT_BAND_SECTOR_SETTINGS["border"])
        border_enabled = bool(border_cfg.get("enabled", True))
        border_hex = border_cfg.get("color", "#ffffff")
        kml_outline_color = hex_and_transparency_to_kml_color(border_hex, 0)

        specific_band = None
        if extra_data:
            for k, v in extra_data.items():
                if k.strip().lower() in ("band", "frequency", "freq"):
                    specific_band = v
                    break

        active_bands = self.get_active_bands_for_site(use_bands, specific_band)
        band_targets = active_bands if active_bands else [None]

        for b_cfg in band_targets:
            target_fol = fol.newfolder(name=b_cfg["band_name"]) if b_cfg else fol
            b_label = b_cfg["band_name"] if b_cfg else ""

            if layer_mode in ("sector", "both"):
                for i in range(4):
                    az_text = str(azims[i]).strip() if i < len(azims) and azims[i] is not None else ""
                    if not az_text or az_text in ["-", " "]:
                        continue
                    try:
                        azimuth = float(az_text)
                    except ValueError:
                        continue

                    s_len, s_wid, s_trans, s_col, s_prefix = self.get_sector_parameters(i, length, sector_width, b_cfg)
                    desc_html = self.build_kml_description_html(
                        site_name, option_name, lat, lon, s_len, s_wid, b_label, extra_data, sector_idx=i
                    )

                    pol = target_fol.newpolygon(name=f"{s_prefix} Az:{azimuth:g}")
                    pol.description = desc_html
                    start_bearing = azimuth - (s_wid / 2.0)

                    arc_coords = []
                    steps = max(int(s_wid / 5) + 1, 2)
                    bearing_step = s_wid / (steps - 1)

                    for step in range(steps):
                        current_bearing = start_bearing + (step * bearing_step)
                        dest_lat, dest_lon = self.calculate_destination(lat, lon, current_bearing, s_len)
                        arc_coords.append((dest_lon, dest_lat, height))

                    pol.outerboundaryis = [(lon, lat, height)] + arc_coords + [(lon, lat, height)]
                    pol.style.polystyle.color = hex_and_transparency_to_kml_color(s_col, s_trans)
                    pol.style.polystyle.fill = 1
                    pol.style.polystyle.outline = 1 if border_enabled else 0
                    if border_enabled:
                        pol.style.linestyle.color = kml_outline_color
                        pol.style.linestyle.width = 2

            elif layer_mode == "lines":
                for i in range(4):
                    az_text = str(azims[i]).strip() if i < len(azims) and azims[i] is not None else ""
                    if not az_text or az_text in ["-", " "]:
                        continue
                    try:
                        azimuth = float(az_text)
                    except ValueError:
                        continue

                    s_len, s_wid, s_trans, s_col, s_prefix = self.get_sector_parameters(i, length, sector_width, b_cfg)
                    desc_html = self.build_kml_description_html(
                        site_name, option_name, lat, lon, s_len, s_wid, b_label, extra_data, sector_idx=i
                    )

                    end_lat, end_lon = self.calculate_destination(lat, lon, azimuth, s_len)
                    lin = target_fol.newlinestring(name=f"{s_prefix} Az:{azimuth:g}")
                    lin.description = desc_html
                    lin.coords = [(lon, lat, height), (end_lon, end_lat, height)]
                    lin.style.linestyle.color = hex_and_transparency_to_kml_color(s_col, 0)
                    lin.style.linestyle.width = 3

        if layer_mode in ("pin", "both", "lines"):
            point_label = f"{site_name} - {option_name}" if option_name else site_name
            desc_html = self.build_kml_description_html(
                site_name, option_name, lat, lon, length, sector_width, "", extra_data, sector_idx=None
            )
            pnt = fol.newpoint(name=point_label)
            pnt.description = desc_html
            pnt.coords = [(lon, lat, height)]
            pnt.style.iconstyle.scale = 1.0
            pnt.style.labelstyle.scale = 1.0
            pnt.style.labelstyle.color = simplekml.Color.white

    def build_site_map_feature(self, site_name, option_name, lat, lon, length, azims, layer_mode, sector_width, extra_data=None, use_bands=False):
        polygons = []
        lines = []

        border_cfg = self.band_sector_settings.get("border", DEFAULT_BAND_SECTOR_SETTINGS["border"])
        border_enabled = bool(border_cfg.get("enabled", True))
        border_hex = border_cfg.get("color", "#ffffff")

        specific_band = None
        if extra_data:
            for k, v in extra_data.items():
                if k.strip().lower() in ("band", "frequency", "freq"):
                    specific_band = v
                    break

        active_bands = self.get_active_bands_for_site(use_bands, specific_band)
        band_targets = active_bands if active_bands else [None]

        for b_cfg in band_targets:
            for i in range(4):
                az_text = str(azims[i]).strip() if i < len(azims) and azims[i] is not None else ""
                if not az_text or az_text in ["-", " "]:
                    continue
                try:
                    azimuth = float(az_text)
                except ValueError:
                    continue

                s_len, s_wid, s_trans, s_col, s_prefix = self.get_sector_parameters(i, length, sector_width, b_cfg)
                opacity_float = max(0.05, min(1.0, (100 - s_trans) / 100.0))
                sector_extra = self.filter_extra_data_for_sector(extra_data, sector_idx=i)

                if layer_mode in ("sector", "both"):
                    start_bearing = azimuth - (s_wid / 2.0)
                    steps = max(int(s_wid / 5) + 1, 2)
                    bearing_step = s_wid / (steps - 1)
                    poly_coords = [[lat, lon]]
                    for step in range(steps):
                        current_bearing = start_bearing + (step * bearing_step)
                        dest_lat, dest_lon = self.calculate_destination(lat, lon, current_bearing, s_len)
                        poly_coords.append([dest_lat, dest_lon])
                    poly_coords.append([lat, lon])
                    polygons.append({
                        "name": f"{s_prefix} (Azimuth: {azimuth:g}°)",
                        "coords": poly_coords,
                        "color": s_col,
                        "opacity": opacity_float,
                        "border_enabled": border_enabled,
                        "border_color": border_hex,
                        "length": s_len,
                        "width": s_wid,
                        "sector_extra": sector_extra
                    })

                if layer_mode == "lines":
                    end_lat, end_lon = self.calculate_destination(lat, lon, azimuth, s_len)
                    lines.append({
                        "name": f"{s_prefix} (Azimuth: {azimuth:g}°)",
                        "coords": [[lat, lon], [end_lat, end_lon]],
                        "color": s_col,
                        "length": s_len,
                        "sector_extra": sector_extra
                    })

        return {
            "site_name": site_name,
            "option_name": option_name,
            "lat": lat,
            "lon": lon,
            "length": length,
            "sector_width": sector_width,
            "layer_mode": layer_mode,
            "polygons": polygons,
            "lines": lines,
            "extra_data": extra_data or {}
        }

    def get_output_filepath(self, filename):
        folder = self.input_output.text().strip()
        if folder and os.path.exists(folder):
            return os.path.join(folder, filename)
        return os.path.abspath(filename)

    def open_kml_file(self, file_path):
        abs_path = os.path.abspath(file_path)
        viewer = self.combo_viewer.currentText()

        try:
            if viewer == "Google Earth":
                if sys.platform == "win32":
                    ge_paths = [
                        r"C:\Program Files\Google\Google Earth Pro\client\googleearth.exe",
                        r"C:\Program Files (x86)\Google\Google Earth Pro\client\googleearth.exe"
                    ]
                    for gpath in ge_paths:
                        if os.path.exists(gpath):
                            subprocess.Popen([gpath, abs_path])
                            return
                    os.startfile(abs_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", "-a", "Google Earth Pro", abs_path])
                else:
                    subprocess.Popen(["google-earth-pro", abs_path])

            elif viewer == "QGIS":
                if sys.platform == "win32":
                    qgis_paths = [
                        r"C:\Program Files\QGIS 3.34.0\bin\qgis-bin.exe",
                        r"C:\Program Files\QGIS 3.28.0\bin\qgis-bin.exe",
                        r"C:\Program Files\QGIS 3.22.0\bin\qgis-bin.exe"
                    ]
                    for qpath in qgis_paths:
                        if os.path.exists(qpath):
                            subprocess.Popen([qpath, abs_path])
                            return
                    os.startfile(abs_path)
                else:
                    subprocess.Popen(["qgis", abs_path])

            elif viewer == "ArcGIS Earth":
                if sys.platform == "win32":
                    arc_paths = [
                        r"C:\Program Files\ArcGIS\ArcGIS Earth\bin\ArcGISEarth.exe",
                        r"C:\Program Files (x86)\ArcGIS\ArcGIS Earth\bin\ArcGISEarth.exe",
                        r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe"
                    ]
                    for apath in arc_paths:
                        if os.path.exists(apath):
                            subprocess.Popen([apath, abs_path])
                            return
                    os.startfile(abs_path)
                else:
                    subprocess.Popen(["arcgis", abs_path])

        except Exception as e:
            QMessageBox.warning(self, "Viewer Launch Warning", f"Saved KML, but could not launch {viewer}:\n{str(e)}")

    def create_single_kml(self, open_file=False):
        try:
            self.save_to_history(show_message=False)

            site_name = self.input_name.text().strip() or "Site"
            option_name = self.input_option.text().strip()

            lat_str, lon_str = self.input_coords.text().split(',')
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())

            length = float(self.input_length.text().strip()) if self.input_length.text().strip() else 120.0
            sector_width = float(self.input_width.text().strip()) if self.input_width.text().strip() else 60.0
            layer_mode = self.get_one_site_layer_mode()
            use_bands = self.chk_use_band_layers.isChecked()

            kml = simplekml.Kml()
            fol_name = f"{site_name} {option_name}".strip()
            fol = kml.newfolder(name=fol_name)

            azims = [inp.text().strip() for inp in self.az_inputs]

            self.generate_site_kml(
                fol, site_name, option_name, lat, lon, 0.0,
                length, azims, layer_mode, sector_width,
                extra_data=None, use_bands=use_bands
            )

            output_filename = self.get_output_filepath(f"{site_name}_design.kml")
            kml.save(output_filename)

            if open_file:
                self.open_kml_file(output_filename)

            QMessageBox.information(self, "Success", f"Layer saved to:\n'{output_filename}'")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def view_single_site_in_map(self):
        try:
            self.save_to_history(show_message=False)

            site_name = self.input_name.text().strip() or "Site"
            option_name = self.input_option.text().strip()

            lat_str, lon_str = self.input_coords.text().split(',')
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())

            length = float(self.input_length.text().strip()) if self.input_length.text().strip() else 120.0
            sector_width = float(self.input_width.text().strip()) if self.input_width.text().strip() else 60.0
            layer_mode = self.get_one_site_layer_mode()
            use_bands = self.chk_use_band_layers.isChecked()
            azims = [inp.text().strip() for inp in self.az_inputs]

            site_feature = self.build_site_map_feature(
                site_name, option_name, lat, lon, length, azims,
                layer_mode, sector_width, extra_data=None, use_bands=use_bands
            )
            self.map_viewer_dialog.render_sites_on_map([site_feature])

        except Exception as e:
            QMessageBox.critical(self, "Map View Error", str(e))

    def parse_multi_sites_file(self):
        file_path = self.input_csv_path.text().strip()
        if not file_path or not os.path.exists(file_path):
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Template File", "", "Template Files (*.csv *.xlsx);;All Files (*)"
            )
            if not file_path:
                return None
            self.input_csv_path.setText(file_path)

        layer_mode = self.get_multi_site_layer_mode()
        default_length = float(self.input_multi_length.text().strip()) if self.input_multi_length.text().strip() else 120.0
        default_width = float(self.input_multi_width.text().strip()) if self.input_multi_width.text().strip() else 60.0

        def clean_cell(value):
            if value is None:
                return ""
            val = str(value).strip()
            if val in ["-", ""]:
                return ""
            return val

        def norm_key(k):
            return str(k).strip().lower().replace(" ", "").replace("_", "")

        raw_rows = []
        if file_path.lower().endswith(".xlsx"):
            xlsx_rows = read_simple_xlsx(file_path)
            if not xlsx_rows:
                raise ValueError("Excel file is empty.")
            raw_headers = [str(h).strip() for h in xlsx_rows[0]]
            for r in xlsx_rows[1:]:
                row_dict = {}
                for i, h in enumerate(raw_headers):
                    if h:
                        row_dict[h] = r[i] if i < len(r) else ""
                raw_rows.append(row_dict)
        else:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise ValueError("CSV file has no headers.")
                for row in reader:
                    raw_rows.append(row)

        if not raw_rows:
            raise ValueError("No data rows found in the selected file.")

        sample_keys = list(raw_rows[0].keys())
        norm_to_orig = {norm_key(k): k for k in sample_keys}

        has_site = any(k in norm_to_orig for k in ('sitename', 'site', 'sitename/option', 'name'))
        has_lat = any(k in norm_to_orig for k in ('lat', 'latitude'))
        has_lon = any(k in norm_to_orig for k in ('long', 'lon', 'longitude'))

        if not (has_site and has_lat and has_lon):
            raise ValueError("Missing mandatory columns! Template must include at least: 'site name', 'lat', 'long'.")

        standard_norm_keys = {
            'sitename', 'site', 'sitename/option', 'name',
            'option', 'opt',
            'lat', 'latitude',
            'long', 'lon', 'longitude',
            'aza', 'az-a', 's1', 'sector1',
            'azb', 'az-b', 's2', 'sector2',
            'azc', 'az-c', 's3', 'sector3',
            'azd', 'az-d', 's4', 'sector4',
            'linelength', 'length', 'sectorlength',
            'sectorwidth', 'width', 'beamwidth'
        }

        def get_val(row_obj, possible_norm_keys, default_val=""):
            for pk in possible_norm_keys:
                if pk in norm_to_orig:
                    return clean_cell(row_obj.get(norm_to_orig[pk], ""))
            return default_val

        parsed_sites = []
        for row in raw_rows:
            site_name = get_val(row, ['sitename', 'site', 'sitename/option', 'name'], 'Unnamed')
            option = get_val(row, ['option', 'opt'], '')
            lat_str = get_val(row, ['lat', 'latitude'], '')
            lon_str = get_val(row, ['long', 'lon', 'longitude'], '')

            if not lat_str or not lon_str:
                continue

            lat = float(lat_str)
            lon = float(lon_str)

            length_str = get_val(row, ['linelength', 'length', 'sectorlength'], '')
            length = float(length_str) if length_str else default_length

            width_str = get_val(row, ['sectorwidth', 'width', 'beamwidth'], '')
            sector_width = float(width_str) if width_str else default_width

            azims = [
                get_val(row, ['aza', 'az-a', 's1', 'sector1'], ''),
                get_val(row, ['azb', 'az-b', 's2', 'sector2'], ''),
                get_val(row, ['azc', 'az-c', 's3', 'sector3'], ''),
                get_val(row, ['azd', 'az-d', 's4', 'sector4'], '')
            ]

            extra_data = {}
            for orig_col in sample_keys:
                nk = norm_key(orig_col)
                if nk not in standard_norm_keys:
                    val = clean_cell(row.get(orig_col, ""))
                    if val:
                        extra_data[orig_col] = val

            parsed_sites.append({
                "site_name": site_name,
                "option": option,
                "lat": lat,
                "lon": lon,
                "length": length,
                "sector_width": sector_width,
                "layer_mode": layer_mode,
                "azims": azims,
                "extra_data": extra_data
            })

        if not parsed_sites:
            raise ValueError("No valid rows with Lat/Long found in the template file.")

        return parsed_sites

    def create_multi_sites_kml(self, open_file=False):
        try:
            parsed_sites = self.parse_multi_sites_file()
            if not parsed_sites:
                return

            use_bands = self.chk_multi_use_bands.isChecked()
            kml = simplekml.Kml()
            for s in parsed_sites:
                coord_text = f"{s['lat']}, {s['lon']}"
                sectors_data = [{"azimuth": az} for az in s["azims"]]
                self.add_site_to_history(
                    s["site_name"], s["option"], coord_text,
                    s["length"], s["sector_width"], s["layer_mode"],
                    sectors_data, s["extra_data"]
                )

                fol_name = f"{s['site_name']} {s['option']}".strip()
                fol = kml.newfolder(name=fol_name)
                self.generate_site_kml(
                    fol, s["site_name"], s["option"], s["lat"], s["lon"], 0.0,
                    s["length"], s["azims"], s["layer_mode"], s["sector_width"],
                    s["extra_data"], use_bands=use_bands
                )

            self.save_history()
            self.populate_history_list()

            out_name = self.input_multi_outname.text().strip() or "imported_multi_sites.kml"
            if not out_name.lower().endswith(".kml"):
                out_name += ".kml"

            output_filename = self.get_output_filepath(out_name)
            kml.save(output_filename)

            if open_file:
                self.open_kml_file(output_filename)

            QMessageBox.information(
                self, "Success",
                f"Imported {len(parsed_sites)} sites to history & created:\n'{output_filename}'"
            )

        except Exception as e:
            QMessageBox.critical(self, "Multi-Site Import Error", str(e))

    def view_multi_sites_in_map(self):
        try:
            parsed_sites = self.parse_multi_sites_file()
            if not parsed_sites:
                return

            use_bands = self.chk_multi_use_bands.isChecked()
            map_features = []
            for s in parsed_sites:
                coord_text = f"{s['lat']}, {s['lon']}"
                sectors_data = [{"azimuth": az} for az in s["azims"]]
                self.add_site_to_history(
                    s["site_name"], s["option"], coord_text,
                    s["length"], s["sector_width"], s["layer_mode"],
                    sectors_data, s["extra_data"]
                )

                feat = self.build_site_map_feature(
                    s["site_name"], s["option"], s["lat"], s["lon"],
                    s["length"], s["azims"], s["layer_mode"], s["sector_width"],
                    s["extra_data"], use_bands=use_bands
                )
                map_features.append(feat)

            self.save_history()
            self.populate_history_list()

            self.map_viewer_dialog.render_sites_on_map(map_features)

        except Exception as e:
            QMessageBox.critical(self, "Map View Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SiteLayerCreator()
    window.show()
    sys.exit(app.exec())
