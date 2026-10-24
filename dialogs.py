import os
import json
import webbrowser
import tempfile
import csv
from datetime import datetime
from xml.sax.saxutils import escape

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QScrollArea, QFrame, QCheckBox, QGridLayout, 
    QTabWidget, QLineEdit, QSpinBox, QColorDialog, QGroupBox, QFileDialog, QMessageBox, QWidget
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QUrl

from config import GROUPED_CUSTOM_ATTRIBUTES, DEFAULT_BAND_SECTOR_SETTINGS

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


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

        self.tabs = QTabWidget()
        self.band_widgets = {}
        self.sector_widgets = {}

        band_tab = QWidget()
        band_layout = QVBoxLayout(band_tab)
        band_grid = QGridLayout()
        band_grid.setSpacing(10)

        headers = ["Enable Band Layer", "Sector Length (m)", "Beamwidth (°)", "Transparency (%)", "Layer Color Palette"]
        for c_idx, h_text in enumerate(headers):
            lbl = QLabel(h_text)
            lbl.setStyleSheet("font-weight: bold; color: #4da3ff;")
            band_grid.addWidget(lbl, 0, c_idx)

        for r_idx, b_name in enumerate(["Band 700", "Band 1800", "Band 2600", "C-Band"], start=1):
            chk = QCheckBox(b_name)
            inp_len = QLineEdit()
            inp_wid = QLineEdit()
            spin_trans = QSpinBox()
            spin_trans.setRange(0, 100)
            spin_trans.setSuffix("%")
            btn_color = QPushButton("Pick Color")
            btn_color.setFixedWidth(120)

            self.band_widgets[b_name] = {"enabled": chk, "length": inp_len, "width": inp_wid, "transparency": spin_trans, "color_btn": btn_color, "color_hex": "#000000"}
            btn_color.clicked.connect(lambda checked, bn=b_name: self.pick_band_color(bn))

            band_grid.addWidget(chk, r_idx, 0)
            band_grid.addWidget(inp_len, r_idx, 1)
            band_grid.addWidget(inp_wid, r_idx, 2)
            band_grid.addWidget(spin_trans, r_idx, 3)
            band_grid.addWidget(btn_color, r_idx, 4)

        band_layout.addLayout(band_grid)
        band_layout.addStretch(1)
        self.tabs.addTab(band_tab, "Band Layers")

        sector_tab = QWidget()
        sector_layout = QVBoxLayout(sector_tab)
        sec_grid = QGridLayout()
        sec_grid.setSpacing(10)

        for c_idx, h_text in enumerate(["Custom Sector", "Sector Length (m)", "Beamwidth (°)", "Transparency (%)", "Sector Color Palette"]):
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

            self.sector_widgets[s_name] = {"use_custom": chk, "length": inp_len, "width": inp_wid, "transparency": spin_trans, "color_btn": btn_color, "color_hex": "#00e5ff"}
            btn_color.clicked.connect(lambda checked, sn=s_name: self.pick_sector_color(sn))

            sec_grid.addWidget(chk, r_idx, 0)
            sec_grid.addWidget(inp_len, r_idx, 1)
            sec_grid.addWidget(inp_wid, r_idx, 2)
            sec_grid.addWidget(spin_trans, r_idx, 3)
            sec_grid.addWidget(btn_color, r_idx, 4)

        sector_layout.addLayout(sec_grid)
        sector_layout.addStretch(1)
        self.tabs.addTab(sector_tab, "Per-Sector Settings")

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
        btn.setStyleSheet(f"background-color: {hex_color}; color: {text_col}; font-weight: bold; border: 1px solid #ffffff; border-radius: 4px; padding: 6px;")

    def pick_border_color(self):
        color = QColorDialog.getColor(QColor(self.border_color_hex), self, "Pick Sector Border Color")
        if color.isValid():
            self.border_color_hex = color.name()
            self.update_color_button_style(self.btn_border_color, self.border_color_hex)

    def pick_band_color(self, band_name):
        color = QColorDialog.getColor(QColor(self.band_widgets[band_name]["color_hex"]), self, f"Pick Color for {band_name}")
        if color.isValid():
            self.band_widgets[band_name]["color_hex"] = color.name()
            self.update_color_button_style(self.band_widgets[band_name]["color_btn"], color.name())

    def pick_sector_color(self, sec_name):
        color = QColorDialog.getColor(QColor(self.sector_widgets[sec_name]["color_hex"]), self, f"Pick Color for {sec_name}")
        if color.isValid():
            self.sector_widgets[sec_name]["color_hex"] = color.name()
            self.update_color_button_style(self.sector_widgets[sec_name]["color_btn"], color.name())

    def load_settings_into_ui(self, settings_data):
        border_cfg = settings_data.get("border", DEFAULT_BAND_SECTOR_SETTINGS["border"])
        self.chk_border_enabled.setChecked(bool(border_cfg.get("enabled", True)))
        self.border_color_hex = border_cfg.get("color", "#ffffff")
        self.update_color_button_style(self.btn_border_color, self.border_color_hex)

        for b_name, w in self.band_widgets.items():
            b_data = settings_data.get("bands", {}).get(b_name, DEFAULT_BAND_SECTOR_SETTINGS["bands"][b_name])
            w["enabled"].setChecked(bool(b_data.get("enabled", True)))
            w["length"].setText(str(b_data.get("length", 140.0)))
            w["width"].setText(str(b_data.get("width", 60.0)))
            w["transparency"].setValue(int(b_data.get("transparency", 50)))
            w["color_hex"] = b_data.get("color", "#000000")
            self.update_color_button_style(w["color_btn"], w["color_hex"])

        for s_name, w in self.sector_widgets.items():
            s_data = settings_data.get("sectors", {}).get(s_name, DEFAULT_BAND_SECTOR_SETTINGS["sectors"][s_name])
            w["use_custom"].setChecked(bool(s_data.get("use_custom", False)))
            w["length"].setText(str(s_data.get("length", 120.0)))
            w["width"].setText(str(s_data.get("width", 60.0)))
            w["transparency"].setValue(int(s_data.get("transparency", 50)))
            w["color_hex"] = s_data.get("color", "#00e5ff")
            self.update_color_button_style(w["color_btn"], w["color_hex"])

    def reset_to_defaults(self):
        self.load_settings_into_ui(json.loads(json.dumps(DEFAULT_BAND_SECTOR_SETTINGS)))

    def save_and_close(self):
        try:
            new_settings = {
                "border": {"enabled": self.chk_border_enabled.isChecked(), "color": self.border_color_hex},
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(14)

        self.checkboxes = {}
        self.ordered_keys = []

        for group_title, items in GROUPED_CUSTOM_ATTRIBUTES:
            group_box = QGroupBox(group_title)
            group_box.setStyleSheet("QGroupBox { font-weight: bold; color: #4da3ff; border: 1px solid #484848; border-radius: 6px; margin-top: 8px; padding-top: 12px; }")
            grid = QGridLayout(group_box)
            grid.setSpacing(8)

            for idx, (col_key, label_text, default_checked, is_mandatory) in enumerate(items):
                cb = QCheckBox(f"{label_text}  [{col_key}]")
                cb.setChecked(default_checked)
                if is_mandatory:
                    cb.setEnabled(False)
                self.checkboxes[col_key] = (cb, default_checked, is_mandatory)
                self.ordered_keys.append(col_key)
                grid.addWidget(cb, idx // 2, idx % 2)

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


class MapViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("2D Open-Source Map Viewer")
        self.resize(1000, 700)
        self.setMinimumSize(650, 450)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)

        self.temp_map_file = os.path.join(tempfile.gettempdir(), "gis_layer_creator_2d_map.html")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            layout.addWidget(self.web_view, 1)
        else:
            info_lbl = QLabel("<h3>2D Interactive Open-Source Map Opened in Browser</h3>")
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
    <title>GIS Layer Creator - 2D Map View</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        html, body, #map {{ height: 100%; width: 100%; margin: 0; padding: 0; background: #1e1e1e; font-family: Arial, sans-serif; }}
        .site-tooltip {{ background: rgba(0, 0, 0, 0.8); color: #ffffff; border: 1px solid #a9d3a5; border-radius: 4px; padding: 2px 6px; font-weight: bold; font-size: 12px; }}
        .popup-table {{ border-collapse: collapse; width: 100%; margin-top: 6px; font-size: 12px; }}
        .popup-table td {{ border: 1px solid #ccc; padding: 3px 6px; }}
        .popup-table td.key {{ font-weight: bold; background-color: #f2f2f2; color: #111; }}
        .popup-table td.val {{ color: #111; }}
    </style>
</head>
<body>
<div id="map"></div>
<script>
    const sites = {payload_json};
    const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ maxZoom: 19, attribution: 'Tiles &copy; Esri' }});
    const esriStreet = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ maxZoom: 19, attribution: 'Tiles &copy; Esri' }});
    const map = L.map('map', {{ center: [30.0444, 31.2357], zoom: 13, layers: [esriSatellite] }});
    L.control.layers({{"Satellite Imagery (Esri)": esriSatellite, "Esri Street Map": esriStreet}}).addTo(map);
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
                const p = L.polygon(poly.coords, {{ stroke: hasBorder, color: borderCol, weight: hasBorder ? 2 : 0, fillColor: color, fillOpacity: fillOp }}).addTo(featureGroup);
                p.bindPopup(`<b>${{titleLabel}}</b><br>${{poly.name}}<br>Length: ${{poly.length}}m | Width: ${{poly.width}}&deg;${{polyExtraHtml}}`);
            }});
        }}
        if (site.layer_mode === 'lines') {{
            site.lines.forEach((lin, idx) => {{
                const color = lin.color || '#00e5ff';
                const l = L.polyline(lin.coords, {{ color: color, weight: 4 }}).addTo(featureGroup);
                l.bindPopup(`<b>${{titleLabel}}</b><br>${{lin.name}}<br>Length: ${{lin.length}}m`);
            }});
        }}
        if (site.layer_mode === 'pin' || site.layer_mode === 'both' || site.layer_mode === 'lines') {{
            const m = L.marker([site.lat, site.lon]).addTo(featureGroup);
            m.bindPopup(`<b>${{titleLabel}}</b><br>Lat, Long: ${{site.lat}}, ${{site.lon}} ${{siteExtraHtml}}`);
            m.bindTooltip(titleLabel, {{ permanent: true, direction: 'top', offset: [0, -12], className: 'site-tooltip' }});
        }}
    }});
    if (featureGroup.getLayers().length > 0) {{ map.fitBounds(featureGroup.getBounds(), {{ padding: [45, 45], maxZoom: 17 }}); }}
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


class HowToUseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Use - GIS Layer Creator")
        self.setFixedSize(720, 640)
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        guide_html = "<h2>GIS Layer Creator - User Guide</h2><p>Use the top menus, customize bands, sectors, borders, and templates easily.</p>"
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