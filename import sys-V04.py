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
    QButtonGroup, QStackedWidget, QDialog, QScrollArea
)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt, QUrl
import simplekml

# Optional embedded browser engine for the 2D Map Popup
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

HISTORY_FILE = "site_history.json"

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
    "C/hqSXwOwQRJ9rvgv6vV6UpwrZD4kR8R+zpkAuimlq9z94wCuSSl9UlovIIOAB/C4me0HsC+A3unuhf2vB"
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
    "lGVIpqv3R0J2qN/f"
)


# --- Standalone Native XLSX Writer & Reader (Zero 3rd-party dependencies) ---
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
            col_letter = chr(65 + c_idx)
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
            row_vals = []
            for c_el in row_el.findall('m:c', ns):
                c_type = c_el.get('t')
                if c_type == 's':
                    v_el = c_el.find('m:v', ns)
                    idx = int(v_el.text) if v_el is not None and v_el.text else 0
                    val = shared_strings[idx] if idx < len(shared_strings) else ""
                elif c_type == 'inlineStr':
                    t_el = c_el.find('.//m:t', ns)
                    val = t_el.text if t_el is not None and t_el.text else ""
                else:
                    v_el = c_el.find('m:v', ns)
                    val = v_el.text if v_el is not None and v_el.text else ""
                row_vals.append(val)
            rows_data.append(row_vals)
        return rows_data


# --- Popup Dialog for 2D Open-Source Map Viewer (Fixed 403 Tile Block) ---
class MapViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("2D Open-Source Map Viewer")
        self.setFixedSize(920, 660)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.temp_map_file = os.path.join(tempfile.gettempdir(), "gis_layer_creator_2d_map.html")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()
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
    </style>
</head>
<body>
<div id="map"></div>
<script>
    const sites = {payload_json};

    // 1. CartoDB Voyager (OpenStreetMap Data - Zero 403 blocks)
    const osmCartoVoyager = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
        subdomains: 'abcd',
        maxZoom: 20,
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }});

    // 2. CartoDB Dark Matter (OpenStreetMap Dark 2D Map)
    const osmCartoDark = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
        subdomains: 'abcd',
        maxZoom: 20,
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }});

    // 3. Esri World Street Map
    const esriStreet = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
    }});

    // 4. Esri Satellite Imagery
    const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
    }});

    const map = L.map('map', {{
        center: [30.0444, 31.2357],
        zoom: 13,
        layers: [osmCartoVoyager]
    }});

    const baseMaps = {{
        "OpenStreetMap (2D Street)": osmCartoVoyager,
        "OpenStreetMap (Dark Mode)": osmCartoDark,
        "Esri Street Map": esriStreet,
        "Satellite Imagery (Esri)": esriSatellite
    }};
    L.control.layers(baseMaps).addTo(map);

    const featureGroup = L.featureGroup().addTo(map);
    const sectorColors = ['#00e5ff', '#ffeb3b', '#ff5252', '#69f0ae'];

    sites.forEach(site => {{
        const titleLabel = site.option_name ? (site.site_name + " - " + site.option_name) : site.site_name;

        // 1. Draw Sector Polygons
        if (site.layer_mode === 'sector' || site.layer_mode === 'both') {{
            site.polygons.forEach((poly, idx) => {{
                const color = sectorColors[idx % sectorColors.length];
                const p = L.polygon(poly.coords, {{
                    color: '#111111',
                    weight: 2,
                    fillColor: color,
                    fillOpacity: 0.55
                }}).addTo(featureGroup);
                p.bindPopup(`<b>${{titleLabel}}</b><br>${{poly.name}}<br>Length: ${{site.length}}m | Width: ${{site.sector_width}}&deg;`);
            }});
        }}

        // 2. Draw Sector Azimuth Lines
        if (site.layer_mode === 'lines') {{
            site.lines.forEach((lin, idx) => {{
                const l = L.polyline(lin.coords, {{
                    color: '#d83b01',
                    weight: 4
                }}).addTo(featureGroup);
                l.bindPopup(`<b>${{titleLabel}}</b><br>${{lin.name}}<br>Length: ${{site.length}}m`);
            }});
        }}

        // 3. Draw Site Pin Marker
        if (site.layer_mode === 'pin' || site.layer_mode === 'both' || site.layer_mode === 'lines') {{
            const m = L.marker([site.lat, site.lon]).addTo(featureGroup);
            m.bindPopup(`<b>${{titleLabel}}</b><br>Lat, Long: ${{site.lat}}, ${{site.lon}}`);
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
        self.setFixedSize(360, 480)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

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


# --- Popup Dialog for "How to Use?" User Guide ---
class HowToUseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Use - User Guide")
        self.setFixedSize(680, 580)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)

        guide_html = """
        <h2 style='color:#a9d3a5; margin-bottom:5px;'>GIS Layer Creator - User Guide</h2>
        <p>Welcome to <b>GIS Layer Creator</b>! This guide details how to operate every single feature and tool in the application:</p>

        <h3 style='color:#4da3ff;'>1. Global Settings (Header)</h3>
        <ul>
            <li><b>Output Folder:</b> Choose the folder where generated <code>.kml</code> files are saved (defaults to Desktop). Click <b>Browse</b> or change it via <b>File &rarr; Change Output Folder</b>.</li>
            <li><b>Open KML File With:</b> Select your preferred external GIS application (<b>Google Earth</b>, <b>QGIS</b>, or <b>ArcGIS Earth</b>).</li>
        </ul>

        <h3 style='color:#4da3ff;'>2. One Site Mode</h3>
        <ul>
            <li><b>Site Name / Option:</b> Enter the site identifier (e.g. <code>LCAIE10480</code>) and optional antenna/carrier label (e.g. <code>Opt1</code>).</li>
            <li><b>Latitude, Longitude:</b> Coordinates separated by a comma (e.g. <code>30.0444, 31.2357</code>).</li>
            <li><b>Sector Length (m):</b> Distance/radius of the sector in meters (default: <code>120m</code>).</li>
            <li><b>Sector Width (°):</b> Beamwidth angle in degrees (default: <code>60°</code>).</li>
            <li><b>Azimuths (S1 to S4):</b> True azimuth angles (0° to 360°) for sectors 1 through 4. Empty fields are skipped.</li>
            <li><b>Layer Output Type:</b>
                <ul>
                    <li><b>Pin Only:</b> Generates only the location placemark icon.</li>
                    <li><b>Sectorized Only:</b> Generates the sector pie-wedge polygons only.</li>
                    <li><b>Lines:</b> Draws straight directional radial lines along the given azimuths instead of polygons.</li>
                    <li><b>Both:</b> Generates both the site pin icon and the sector polygons.</li>
                </ul>
            </li>
            <li><b>Save Site to History:</b> Stores the site data into local history for future reuse.</li>
            <li><b>Create Layer / Create and Open Layer:</b> Saves the <code>.kml</code> layer to the output folder and optionally opens it in your chosen GIS viewer.</li>
            <li><b>View in Map:</b> Opens a built-in <b>2D Open-Source Map (OpenStreetMap / Satellite)</b> popup window and plots your site layers (Pins, Sectors, or Lines) directly without opening Google Earth!</li>
        </ul>

        <h3 style='color:#4da3ff;'>3. Multi Sites Mode (Batch Processing)</h3>
        <ul>
            <li><b>Export CSV / Excel Template:</b> Click to generate a clean template file pre-formatted with the required columns:
            <br><code>site name, option, lat, long, az-a, az-b, az-c, az-d, line length</code>.</li>
            <li><b>Select Filled File:</b> Browse and pick your prepared <code>.csv</code> or <code>.xlsx</code> file.</li>
            <li><b>Default Length / Width:</b> Fallback length and beamwidth used for any row where <code>line length</code> is left blank.</li>
            <li><b>Output File Name:</b> Specify the KML filename (e.g. <code>imported_multi_sites.kml</code>).</li>
            <li><b>Create / Create & Open Multi-Sites Layer:</b> Builds all sites into organized KML folders and automatically registers them into your History list.</li>
            <li><b>View in Map:</b> Plots all sites from your selected template file directly onto the 2D OpenStreetMap popup window!</li>
        </ul>

        <h3 style='color:#4da3ff;'>4. History Management</h3>
        <ul>
            <li><b>View History:</b> Access via <b>History &rarr; View History</b> in the top bar to open the popup list of all saved sites.</li>
            <li><b>Load Site:</b> Click any site name in the popup list to immediately load its parameters back into <i>One Site Mode</i>.</li>
            <li><b>Export History:</b> Exports all saved sites with a timestamped filename (<code>exported history YYYY-MM-DD_HH-MM-SS.csv</code> or <code>.xlsx</code>).</li>
            <li><b>Clear All History:</b> Resets the saved history list completely.</li>
        </ul>

        <h3 style='color:#4da3ff;'>5. View & Themes</h3>
        <ul>
            <li>Switch between <b>Dark Mode On</b> and <b>Dark Mode Off</b> via the <b>View</b> menu at any time.</li>
        </ul>

        <h3 style='color:#4da3ff;'>6. Help & Support</h3>
        <ul>
            <li><b>How to use?:</b> Opens this complete operational guide (updated with every new tool added).</li>
            <li><b>About App?:</b> View summary info and developer credits.</li>
            <li><b>Support:</b> Direct contact information via Email and WhatsApp.</li>
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

        # 1. Remove Maximize button & Make Always On Top
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(850, 750)

        self.dark_mode = True
        self.history_data = self.load_history()

        # Popup Dialogs
        self.history_dialog = HistoryPopupDialog(self)
        self.how_to_use_dialog = HowToUseDialog(self)
        self.map_viewer_dialog = MapViewerDialog(self)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.create_menu_bar()
        self.init_ui(central_widget)
        self.populate_history_list()
        self.apply_theme()

    # ==========================================
    # Top Menu Bar: File, History, View, Help
    # ==========================================
    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # 1. File Menu
        file_menu = menu_bar.addMenu("File")

        export_csv_action = QAction("Export Template CSV", self)
        export_csv_action.triggered.connect(self.export_template_csv)
        file_menu.addAction(export_csv_action)

        export_excel_action = QAction("Export Template Excel", self)
        export_excel_action.triggered.connect(self.export_template_excel)
        file_menu.addAction(export_excel_action)

        file_menu.addSeparator()

        change_output_action = QAction("Change Output Folder", self)
        change_output_action.triggered.connect(self.browse_output_directory)
        file_menu.addAction(change_output_action)

        # 2. History Menu
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

        # 3. View Menu
        view_menu = menu_bar.addMenu("View")

        dark_on_action = QAction("Dark Mode On", self)
        dark_on_action.triggered.connect(lambda: self.set_dark_mode(True))
        view_menu.addAction(dark_on_action)

        dark_off_action = QAction("Dark Mode Off", self)
        dark_off_action.triggered.connect(lambda: self.set_dark_mode(False))
        view_menu.addAction(dark_off_action)

        # 4. Help Menu
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

    # ==========================================
    # Main UI Layout
    # ==========================================
    def init_ui(self, central_widget):
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(14)

        # Header Logo + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        header_layout.setContentsMargins(10, 0, 0, 5)

        self.logo_lbl = QLabel()
        if LOGO_B64:
            b64_str = LOGO_B64.strip()
            missing_padding = len(b64_str) % 4
            if missing_padding:
                b64_str += '=' * (4 - missing_padding)

            logo_bytes = base64.b64decode(b64_str)
            pixmap = QPixmap()
            pixmap.loadFromData(logo_bytes)
            pixmap = pixmap.scaled(
                100, 100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_lbl.setPixmap(pixmap)
        header_layout.addWidget(self.logo_lbl)

        self.title_lbl = QLabel()
        self.title_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch(1)

        main_layout.addLayout(header_layout)

        # Shared Top Settings: Output Folder & Open With App
        shared_grid = QGridLayout()
        shared_grid.setSpacing(10)

        lbl_output = QLabel("Output Folder")
        lbl_output.setFixedWidth(150)
        self.input_output = QLineEdit()
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.input_output.setText(desktop_path)

        btn_browse_output = QPushButton("Browse")
        btn_browse_output.setObjectName("BrowseBtn")
        btn_browse_output.clicked.connect(self.browse_output_directory)

        shared_grid.addWidget(lbl_output, 0, 0)
        shared_grid.addWidget(self.input_output, 0, 1)
        shared_grid.addWidget(btn_browse_output, 0, 2)

        self.lbl_app_choice = QLabel("Open KML File With:")
        self.combo_app_choice = QComboBox()
        self.combo_app_choice.addItems(["Google Earth", "QGIS", "ArcGIS Earth"])

        shared_grid.addWidget(self.lbl_app_choice, 1, 0)
        shared_grid.addWidget(self.combo_app_choice, 1, 1, 1, 2)

        main_layout.addLayout(shared_grid)

        # Mode Switcher Buttons
        mode_tab_layout = QHBoxLayout()
        mode_tab_layout.setSpacing(10)

        self.btn_mode_one = QPushButton("ONE SITE MODE")
        self.btn_mode_one.setCheckable(True)
        self.btn_mode_one.setChecked(True)
        self.btn_mode_one.setObjectName("ModeTabBtn")
        self.btn_mode_one.clicked.connect(lambda: self.switch_mode(0))

        self.btn_mode_multi = QPushButton("MULTI SITES MODE (TEMPLATE)")
        self.btn_mode_multi.setCheckable(True)
        self.btn_mode_multi.setObjectName("ModeTabBtn")
        self.btn_mode_multi.clicked.connect(lambda: self.switch_mode(1))

        mode_tab_layout.addWidget(self.btn_mode_one, 1)
        mode_tab_layout.addWidget(self.btn_mode_multi, 1)
        main_layout.addLayout(mode_tab_layout)

        # Stacked Widget for Both Modes
        self.stacked_modes = QStackedWidget()
        self.page_one_site = self.build_one_site_page()
        self.page_multi_sites = self.build_multi_sites_page()

        self.stacked_modes.addWidget(self.page_one_site)
        self.stacked_modes.addWidget(self.page_multi_sites)

        main_layout.addWidget(self.stacked_modes, 1)

    # ==========================================
    # Page 1: One Site Mode
    # ==========================================
    def build_one_site_page(self):
        page = QFrame()
        page.setObjectName("ModeBox")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(2, 1)
        form_layout.setColumnStretch(3, 1)
        form_layout.setColumnStretch(4, 1)

        # Site Name & Option
        lbl_name = QLabel("Site Name / Option")
        lbl_name.setFixedWidth(150)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Site Name")

        self.input_option = QLineEdit()
        self.input_option.setPlaceholderText("Option")
        self.input_option.setFixedWidth(140)

        form_layout.addWidget(lbl_name, 0, 0)
        form_layout.addWidget(self.input_name, 0, 1, 1, 3)
        form_layout.addWidget(self.input_option, 0, 4)

        # Lat, Long
        lbl_coords = QLabel("Latitude, Longitude")
        self.input_coords = QLineEdit()
        self.input_coords.setPlaceholderText("Lat, Long (e.g. 30.0444, 31.2357)")

        form_layout.addWidget(lbl_coords, 1, 0)
        form_layout.addWidget(self.input_coords, 1, 1, 1, 4)

        # Sector Length (Default 120) & Sector Width (Default 60)
        self.lbl_length = QLabel("Sector Length (m)")
        self.input_length = QLineEdit("120")
        self.input_length.setPlaceholderText("120")

        self.lbl_width = QLabel("Sector Width °")
        self.lbl_width.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.input_width = QLineEdit("60")
        self.input_width.setPlaceholderText("60")

        form_layout.addWidget(self.lbl_length, 2, 0)
        form_layout.addWidget(self.input_length, 2, 1, 1, 2)
        form_layout.addWidget(self.lbl_width, 2, 3)
        form_layout.addWidget(self.input_width, 2, 4)

        # Sector Headers (S1, S2, S3, S4)
        headers = ["", "S1", "S2", "S3", "S4"]
        for i, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold;")
            form_layout.addWidget(lbl, 3, i)

        # Azimuth inputs
        self.lbl_azimuth = QLabel("Azimuth °")
        form_layout.addWidget(self.lbl_azimuth, 4, 0)

        self.az_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setPlaceholderText("-")
            inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.az_inputs.append(inp)
            form_layout.addWidget(inp, 4, i + 1)

        layout.addLayout(form_layout)

        # Layer Output Type Radio Group (Pin Only, Sectorized Only, Lines, Both)
        radio_frame = QFrame()
        radio_frame.setObjectName("RadioGroupFrame")
        radio_layout = QHBoxLayout(radio_frame)
        radio_layout.setContentsMargins(15, 10, 15, 10)

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

        # Action Buttons
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

    # ==========================================
    # Page 2: Multi Sites Mode
    # ==========================================
    def build_multi_sites_page(self):
        page = QFrame()
        page.setObjectName("ModeBox")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        # 1. Export Templates
        lbl_step1 = QLabel("1. Template File")
        lbl_step1.setFixedWidth(150)

        btn_template_csv = QPushButton("Export CSV Template")
        btn_template_csv.setObjectName("ImportBtn")
        btn_template_csv.clicked.connect(self.export_template_csv)

        btn_template_xls = QPushButton("Export Excel Template")
        btn_template_xls.setObjectName("SaveBtn")
        btn_template_xls.clicked.connect(self.export_template_excel)

        grid.addWidget(lbl_step1, 0, 0)
        grid.addWidget(btn_template_csv, 0, 1)
        grid.addWidget(btn_template_xls, 0, 2, 1, 2)

        # 2. Select Template File
        lbl_step2 = QLabel("2. Select Filled File")
        self.input_csv_path = QLineEdit()
        self.input_csv_path.setPlaceholderText("Browse and select your filled CSV or Excel (.xlsx) file...")
        btn_browse_csv = QPushButton("Browse File")
        btn_browse_csv.setObjectName("BrowseBtn")
        btn_browse_csv.clicked.connect(self.browse_csv_file)

        grid.addWidget(lbl_step2, 1, 0)
        grid.addWidget(self.input_csv_path, 1, 1, 1, 2)
        grid.addWidget(btn_browse_csv, 1, 3)

        # 3. Default Length & Width
        lbl_multi_len = QLabel("Default Length (m)")
        self.input_multi_length = QLineEdit("120")

        lbl_multi_wid = QLabel("Default Width °")
        lbl_multi_wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.input_multi_width = QLineEdit("60")

        grid.addWidget(lbl_multi_len, 2, 0)
        grid.addWidget(self.input_multi_length, 2, 1)
        grid.addWidget(lbl_multi_wid, 2, 2)
        grid.addWidget(self.input_multi_width, 2, 3)

        # 4. Output KML File Name
        lbl_out_name = QLabel("Output File Name")
        self.input_multi_outname = QLineEdit("imported_multi_sites.kml")

        grid.addWidget(lbl_out_name, 3, 0)
        grid.addWidget(self.input_multi_outname, 3, 1, 1, 3)

        layout.addLayout(grid)

        # Layer Output Type Radio Group for Multi Sites
        radio_frame = QFrame()
        radio_frame.setObjectName("RadioGroupFrame")
        radio_layout = QHBoxLayout(radio_frame)
        radio_layout.setContentsMargins(15, 10, 15, 10)

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

        # Action Buttons
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

    # ==========================================
    # Mode & Theme Helpers
    # ==========================================
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

        top_color = "#ffffff" if self.dark_mode else "#1e293b"
        bottom_color = "#a9d3a5" if self.dark_mode else "#2e7d32"
        accent_style = f"font-weight: bold; color: {bottom_color};"

        self.title_lbl.setText(
            f"<div style='font-size:32px; font-weight:bold; line-height:1.15;'>"
            f"<span style='color:{top_color};'>GIS LAYER</span><br>"
            f"<span style='color:{bottom_color};'>CREATOR</span>"
            f"</div>"
        )
        self.lbl_app_choice.setStyleSheet(accent_style)
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
                QFrame#ModeBox {
                    background-color: #252525;
                    border: 1px solid #3c3f41;
                    border-radius: 6px;
                }
                QFrame#RadioGroupFrame {
                    background-color: #323232;
                    border: 1px solid #444;
                    border-radius: 4px;
                }
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #3c3f41;
                }
                QMenu {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555;
                }
                QMenu::item:selected {
                    background-color: #005a9e;
                }
                QLineEdit, QComboBox {
                    background-color: #3c3f41;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 6px;
                    color: white;
                }
                QLineEdit:disabled {
                    background-color: #2b2b2b;
                    color: #666;
                    border: 1px solid #3c3f41;
                }
                QComboBox QAbstractItemView {
                    background-color: #2b2b2b;
                    color: white;
                    selection-background-color: #005a9e;
                }
                QLineEdit:focus {
                    border: 1px solid #77aa77;
                }
                QListWidget {
                    background-color: #3c3f41;
                    border: 1px solid #555;
                    border-radius: 4px;
                    outline: none;
                    color: white;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #4a4d4f;
                }
                QListWidget::item:hover {
                    background-color: #4a4d4f;
                }
                QListWidget::item:selected {
                    background-color: #008000;
                    color: white;
                    font-weight: bold;
                }
                QPushButton#ModeTabBtn {
                    background-color: #3c3f41;
                    color: #bbbbbb;
                    font-weight: bold;
                    font-size: 15px;
                    border: 1px solid #555;
                    border-radius: 6px;
                    padding: 12px;
                }
                QPushButton#ModeTabBtn:checked {
                    background-color: #005a9e;
                    color: #ffffff;
                    border: 1px solid #4da3ff;
                }
                QPushButton#ModeTabBtn:hover:!checked {
                    background-color: #4a4d4f;
                }
                QPushButton#CreateOnlyBtn {
                    background-color: #2e7d32;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#CreateOnlyBtn:hover {
                    background-color: #388e3c;
                }
                QPushButton#CreateOpenBtn {
                    background-color: #008000;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#CreateOpenBtn:hover {
                    background-color: #009900;
                }
                QPushButton#ViewMapBtn {
                    background-color: #6b21a8;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#ViewMapBtn:hover {
                    background-color: #7e22ce;
                }
                QPushButton#SaveBtn {
                    background-color: #005a9e;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 11px;
                }
                QPushButton#SaveBtn:hover {
                    background-color: #0078d4;
                }
                QPushButton#ImportBtn {
                    background-color: #d83b01;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 11px;
                }
                QPushButton#ImportBtn:hover {
                    background-color: #ea4a1f;
                }
                QPushButton#BrowseBtn {
                    background-color: #555555;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 14px;
                }
                QPushButton#BrowseBtn:hover {
                    background-color: #666666;
                }
                QPushButton#RemoveBtn {
                    background-color: #9e6a00;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 10px;
                }
                QPushButton#RemoveBtn:hover {
                    background-color: #c08000;
                }
                QRadioButton {
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
                QFrame#ModeBox {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                }
                QFrame#RadioGroupFrame {
                    background-color: #e2e8f0;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                }
                QMenuBar {
                    background-color: #e2e8f0;
                    color: #1e293b;
                }
                QMenuBar::item:selected {
                    background-color: #cbd5e1;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                }
                QMenu::item:selected {
                    background-color: #005a9e;
                    color: #ffffff;
                }
                QLineEdit, QComboBox {
                    background-color: #ffffff;
                    border: 1px solid #94a3b8;
                    border-radius: 4px;
                    padding: 6px;
                    color: #1e293b;
                }
                QLineEdit:disabled {
                    background-color: #e2e8f0;
                    color: #94a3b8;
                    border: 1px solid #cbd5e1;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #1e293b;
                    selection-background-color: #005a9e;
                    selection-color: #ffffff;
                }
                QLineEdit:focus {
                    border: 1px solid #2e7d32;
                }
                QListWidget {
                    background-color: #ffffff;
                    border: 1px solid #94a3b8;
                    border-radius: 4px;
                    outline: none;
                    color: #1e293b;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #e2e8f0;
                }
                QListWidget::item:hover {
                    background-color: #f1f5f9;
                }
                QListWidget::item:selected {
                    background-color: #2e7d32;
                    color: white;
                    font-weight: bold;
                }
                QPushButton#ModeTabBtn {
                    background-color: #e2e8f0;
                    color: #475569;
                    font-weight: bold;
                    font-size: 15px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 12px;
                }
                QPushButton#ModeTabBtn:checked {
                    background-color: #005a9e;
                    color: #ffffff;
                    border: 1px solid #004070;
                }
                QPushButton#ModeTabBtn:hover:!checked {
                    background-color: #cbd5e1;
                }
                QPushButton#CreateOnlyBtn {
                    background-color: #2e7d32;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#CreateOnlyBtn:hover {
                    background-color: #388e3c;
                }
                QPushButton#CreateOpenBtn {
                    background-color: #15803d;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#CreateOpenBtn:hover {
                    background-color: #16a34a;
                }
                QPushButton#ViewMapBtn {
                    background-color: #6b21a8;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 12px;
                }
                QPushButton#ViewMapBtn:hover {
                    background-color: #7e22ce;
                }
                QPushButton#SaveBtn {
                    background-color: #005a9e;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 11px;
                }
                QPushButton#SaveBtn:hover {
                    background-color: #0078d4;
                }
                QPushButton#ImportBtn {
                    background-color: #d83b01;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 11px;
                }
                QPushButton#ImportBtn:hover {
                    background-color: #ea4a1f;
                }
                QPushButton#BrowseBtn {
                    background-color: #64748b;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 14px;
                }
                QPushButton#BrowseBtn:hover {
                    background-color: #475569;
                }
                QPushButton#RemoveBtn {
                    background-color: #b45309;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 10px;
                }
                QPushButton#RemoveBtn:hover {
                    background-color: #d97706;
                }
                QRadioButton {
                    spacing: 8px;
                    font-weight: bold;
                }
            """

    # ==========================================
    # File & Help Dialog Actions
    # ==========================================
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

    def export_template_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV Template", "site_template.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["site name", "option", "lat", "long", "az-a", "az-b", "az-c", "az-d", "line length"])
            QMessageBox.information(self, "Success", "CSV Template exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def export_template_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel Template", "site_template.xlsx", "Excel Files (*.xlsx)")
        if not file_path:
            return
        try:
            if not file_path.lower().endswith(".xlsx"):
                file_path += ".xlsx"
            headers = [["site name", "option", "lat", "long", "az-a", "az-b", "az-c", "az-d", "line length"]]
            write_simple_xlsx(file_path, headers)
            QMessageBox.information(self, "Success", "Excel (.xlsx) Template exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def show_how_to_use_dialog(self):
        self.how_to_use_dialog.show()
        self.how_to_use_dialog.raise_()
        self.how_to_use_dialog.activateWindow()

    def show_about_dialog(self):
        about_text = (
            "<h3>GIS Layer Creator</h3>"
            "<p>A specialized telecom & GIS design tool built to quickly generate "
            "single-site and multi-site KML layers (Pins, Sector Polygons, and Azimuth Lines) "
            "for Google Earth, QGIS, ArcGIS Earth, and an integrated 2D OpenStreetMap viewer.</p>"
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

    # ==========================================
    # History Management & Export
    # ==========================================
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

    def add_site_to_history(self, site_name, option_name, coord_text, length, width, layer_mode, sectors_data):
        self.history_data[site_name] = {
            "site_name": site_name,
            "option_name": option_name,
            "coords": coord_text,
            "length": str(length),
            "width": str(width),
            "layer_mode": layer_mode,
            "sectors": sectors_data
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
            if show_message:
                QMessageBox.critical(self, "Save Error", str(e))
            else:
                raise e

    # ==========================================
    # KML & 2D Map Geometry Builders
    # ==========================================
    def calculate_destination(self, lat, lon, bearing, distance):
        R = 6371000
        lat1 = math.radians(lat)
        lon1 = math.radians(lon)
        bearing = math.radians(bearing)

        lat2 = math.asin(
            math.sin(lat1) * math.cos(distance / R) + 
            math.cos(lat1) * math.sin(distance / R) * math.cos(bearing)
        )
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(distance / R) * math.cos(lat1),
            math.cos(distance / R) - math.sin(lat1) * math.sin(lat2)
        )

        return math.degrees(lat2), math.degrees(lon2)

    def build_site_map_feature(self, site_name, option_name, lat, lon, length, azims, layer_mode, sector_width):
        polygons = []
        lines = []

        for i in range(4):
            az_text = str(azims[i]).strip() if i < len(azims) and azims[i] is not None else ""
            if not az_text or az_text in ["-", " "]:
                continue
            try:
                azimuth = float(az_text)
            except Exception:
                continue

            if layer_mode in ["sector", "both"]:
                start_bearing = azimuth - (sector_width / 2)
                steps = max(int(sector_width / 5) + 1, 2)
                bearing_step = sector_width / (steps - 1) if steps > 1 else 0

                ring = [[lat, lon]]
                for step in range(steps):
                    current_bearing = start_bearing + (step * bearing_step)
                    d_lat, d_lon = self.calculate_destination(lat, lon, current_bearing, length)
                    ring.append([d_lat, d_lon])
                ring.append([lat, lon])
                polygons.append({"name": f"S{i+1} Az:{azimuth}°", "coords": ring})

            elif layer_mode == "lines":
                end_lat, end_lon = self.calculate_destination(lat, lon, azimuth, length)
                lines.append({"name": f"S{i+1} Az:{azimuth}°", "coords": [[lat, lon], [end_lat, end_lon]]})

        return {
            "site_name": site_name,
            "option_name": option_name,
            "lat": lat,
            "lon": lon,
            "length": length,
            "sector_width": sector_width,
            "layer_mode": layer_mode,
            "polygons": polygons,
            "lines": lines
        }

    def generate_site_kml(self, fol, site_name, option_name, lat, lon, height, length, azims, layer_mode, sector_width):
        kml_outline_color = "ffffffff"

        if layer_mode in ["sector", "both"]:
            for i in range(4):
                az_text = str(azims[i]).strip() if i < len(azims) and azims[i] is not None else ""
                if not az_text or az_text in ["-", " "]:
                    continue

                try:
                    azimuth = float(az_text)
                except Exception:
                    continue

                pol = fol.newpolygon(name=f"S{i+1} Az:{azimuth}")
                start_bearing = azimuth - (sector_width / 2)

                arc_coords = []
                steps = max(int(sector_width / 5) + 1, 2)
                bearing_step = sector_width / (steps - 1) if steps > 1 else 0

                for step in range(steps):
                    current_bearing = start_bearing + (step * bearing_step)
                    dest_lat, dest_lon = self.calculate_destination(lat, lon, current_bearing, length)
                    arc_coords.append((dest_lon, dest_lat, height))

                pol.outerboundaryis = [(lon, lat, height)] + arc_coords + [(lon, lat, height)]
                pol.style.polystyle.color = "4Dffffff"
                pol.style.polystyle.fill = 1
                pol.style.polystyle.outline = 1
                pol.style.linestyle.color = kml_outline_color
                pol.style.linestyle.width = 3

        elif layer_mode == "lines":
            for i in range(4):
                az_text = str(azims[i]).strip() if i < len(azims) and azims[i] is not None else ""
                if not az_text or az_text in ["-", " "]:
                    continue

                try:
                    azimuth = float(az_text)
                except Exception:
                    continue

                end_lat, end_lon = self.calculate_destination(lat, lon, azimuth, length)
                lin = fol.newlinestring(name=f"S{i+1} Az:{azimuth}")
                lin.coords = [(lon, lat, height), (end_lon, end_lat, height)]
                lin.style.linestyle.color = kml_outline_color
                lin.style.linestyle.width = 3

        if layer_mode in ["pin", "both", "lines"]:
            point_label = f"{site_name} - {option_name}" if option_name else site_name
            pnt = fol.newpoint(name=point_label)
            pnt.coords = [(lon, lat, height)]
            pnt.style.iconstyle.scale = 1.0 
            pnt.style.labelstyle.scale = 1.0
            pnt.style.labelstyle.color = simplekml.Color.white

    def get_output_filepath(self, filename):
        if not filename.lower().endswith(".kml"):
            filename += ".kml"
        folder = self.input_output.text().strip()
        if folder and os.path.exists(folder):
            return os.path.abspath(os.path.join(folder, filename))
        return os.path.abspath(filename)

    def open_kml_file(self, file_path):
        app_choice = self.combo_app_choice.currentText()
        abs_path = os.path.abspath(file_path)

        try:
            if app_choice == "Google Earth":
                if sys.platform == 'win32':
                    ge_paths = [
                        r"C:\Program Files\Google\Google Earth Pro\client\googleearth.exe",
                        r"C:\Program Files (x86)\Google\Google Earth Pro\client\googleearth.exe",
                        os.path.expandvars(r"%LOCALAPPDATA%\Google\Google Earth Pro\client\googleearth.exe")
                    ]
                    opened = False
                    for gpath in ge_paths:
                        if os.path.exists(gpath):
                            subprocess.Popen([gpath, abs_path])
                            opened = True
                            break
                    if not opened:
                        os.startfile(abs_path)
                elif sys.platform == 'darwin':
                    os.system(f'open -a "Google Earth Pro" "{abs_path}"')
                else:
                    os.system(f'google-earth-pro "{abs_path}" &')

            elif app_choice == "QGIS":
                if sys.platform == 'win32':
                    qgis_paths = [
                        r"C:\Program Files\QGIS 3.34.0\bin\qgis-bin.exe",
                        r"C:\Program Files\QGIS 3.28.0\bin\qgis-bin.exe",
                        r"C:\Program Files\QGIS 3.22.0\bin\qgis-bin.exe"
                    ]
                    opened = False
                    for qpath in qgis_paths:
                        if os.path.exists(qpath):
                            subprocess.Popen([qpath, abs_path])
                            opened = True
                            break
                    if not opened:
                        try:
                            subprocess.Popen(['qgis', abs_path], shell=True)
                        except FileNotFoundError:
                            os.startfile(abs_path)
                elif sys.platform == 'darwin':
                    os.system(f'open -a "QGIS" "{abs_path}"')
                else:
                    subprocess.Popen(['qgis', abs_path])

            elif app_choice == "ArcGIS Earth":
                if sys.platform == 'win32':
                    arcgis_paths = [
                        r"C:\Program Files\ArcGIS\ArcGIS Earth\bin\ArcGISEarth.exe",
                        r"C:\Program Files (x86)\ArcGIS\ArcGIS Earth\bin\ArcGISEarth.exe",
                        r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe",
                        os.path.expandvars(r"%LOCALAPPDATA%\Programs\ArcGIS\ArcGIS Earth\bin\ArcGISEarth.exe")
                    ]
                    opened = False
                    for apath in arcgis_paths:
                        if os.path.exists(apath):
                            subprocess.Popen([apath, abs_path])
                            opened = True
                            break
                    if not opened:
                        try:
                            subprocess.Popen(['ArcGISEarth', abs_path])
                        except FileNotFoundError:
                            os.startfile(abs_path)
                elif sys.platform == 'darwin':
                    os.startfile(abs_path)
                else:
                    os.system(f'xdg-open "{abs_path}"')

        except Exception:
            QMessageBox.warning(
                self, 
                "Launch Warning", 
                f"Could not open the KML file automatically with {app_choice}.\n"
                f"Please make sure {app_choice} is installed or set a default .kml app in Windows.\n\n"
                f"File saved at:\n{abs_path}"
            )

    # ==========================================
    # Action Handlers: Create KML & View in 2D Map
    # ==========================================
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

            kml = simplekml.Kml()
            fol_name = f"{site_name} {option_name}".strip()
            fol = kml.newfolder(name=fol_name)

            azims = [inp.text().strip() for inp in self.az_inputs]

            self.generate_site_kml(
                fol, site_name, option_name, lat, lon, 0.0, 
                length, azims, layer_mode, sector_width
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
            azims = [inp.text().strip() for inp in self.az_inputs]

            site_feature = self.build_site_map_feature(
                site_name, option_name, lat, lon, length, azims, layer_mode, sector_width
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
        sector_width = float(self.input_multi_width.text().strip()) if self.input_multi_width.text().strip() else 60.0

        def clean_cell(value):
            if value is None:
                return ""
            val = str(value).strip()
            if val in ["-", ""]:
                return ""
            return val

        dict_rows = []
        if file_path.lower().endswith(".xlsx"):
            raw_rows = read_simple_xlsx(file_path)
            if not raw_rows:
                raise ValueError("The Excel file is empty.")
            headers = [str(h).strip().lower().replace(" ", "") for h in raw_rows[0]]
            for r in raw_rows[1:]:
                row_dict = {headers[i]: (r[i] if i < len(r) else "") for i in range(len(headers))}
                dict_rows.append(row_dict)
            fieldnames = headers
        else:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                fieldnames = [name.strip().lower().replace(" ", "") for name in (reader.fieldnames or [])]
                reader.fieldnames = fieldnames
                for r in reader:
                    dict_rows.append(r)

        required_cols = ['sitename', 'option', 'lat', 'long', 'az-a', 'az-b', 'az-c', 'az-d', 'linelength']
        for col in required_cols:
            if col not in fieldnames:
                if col == 'sitename' and 'sitename/option' in fieldnames:
                    continue
                raise ValueError(
                    f"Missing column: '{col}'.\n"
                    f"Expected: site name, option, lat, long, az-a, az-b, az-c, az-d, line length"
                )

        parsed_sites = []
        for row in dict_rows:
            site_name = clean_cell(row.get('sitename', row.get('sitename/option', 'Unnamed')))
            option = clean_cell(row.get('option', ''))

            lat_str = clean_cell(row.get('lat', ''))
            lon_str = clean_cell(row.get('long', ''))
            length_str = clean_cell(row.get('linelength', ''))

            if not lat_str or not lon_str:
                continue

            lat = float(lat_str)
            lon = float(lon_str)
            length = float(length_str) if length_str else default_length

            azims = [
                clean_cell(row.get('az-a')), 
                clean_cell(row.get('az-b')), 
                clean_cell(row.get('az-c')), 
                clean_cell(row.get('az-d'))
            ]

            parsed_sites.append({
                "site_name": site_name,
                "option": option,
                "lat": lat,
                "lon": lon,
                "length": length,
                "sector_width": sector_width,
                "layer_mode": layer_mode,
                "azims": azims
            })

        if not parsed_sites:
            raise ValueError("No valid data rows found in the template file.")

        return parsed_sites

    def create_multi_sites_kml(self, open_file=False):
        try:
            parsed_sites = self.parse_multi_sites_file()
            if parsed_sites is None:
                return

            kml = simplekml.Kml()
            for s in parsed_sites:
                coord_text = f"{s['lat']}, {s['lon']}"
                sectors_data = [{"azimuth": az} for az in s['azims']]
                self.add_site_to_history(
                    s['site_name'], s['option'], coord_text, s['length'],
                    s['sector_width'], s['layer_mode'], sectors_data
                )

                fol_name = f"{s['site_name']} {s['option']}".strip()
                fol = kml.newfolder(name=fol_name)
                self.generate_site_kml(
                    fol, s['site_name'], s['option'], s['lat'], s['lon'], 0.0,
                    s['length'], s['azims'], s['layer_mode'], s['sector_width']
                )

            self.save_history()
            self.populate_history_list()

            out_name = self.input_multi_outname.text().strip() or "imported_multi_sites.kml"
            output_filename = self.get_output_filepath(out_name)
            kml.save(output_filename)

            if open_file:
                self.open_kml_file(output_filename)

            QMessageBox.information(
                self, "Success", 
                f"Imported {len(parsed_sites)} sites to history & created:\n'{output_filename}'!"
            )

        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def view_multi_sites_in_map(self):
        try:
            parsed_sites = self.parse_multi_sites_file()
            if parsed_sites is None:
                return

            map_features = []
            for s in parsed_sites:
                coord_text = f"{s['lat']}, {s['lon']}"
                sectors_data = [{"azimuth": az} for az in s['azims']]
                self.add_site_to_history(
                    s['site_name'], s['option'], coord_text, s['length'],
                    s['sector_width'], s['layer_mode'], sectors_data
                )
                feat = self.build_site_map_feature(
                    s['site_name'], s['option'], s['lat'], s['lon'],
                    s['length'], s['azims'], s['layer_mode'], s['sector_width']
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
