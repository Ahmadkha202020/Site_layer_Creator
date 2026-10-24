import sys
import os
import csv
import json
import subprocess
from datetime import datetime
from xml.sax.saxutils import escape

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QListWidget,
    QFileDialog, QMessageBox, QFrame, QComboBox, QRadioButton,
    QButtonGroup, QStackedWidget, QCheckBox
)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt
import simplekml

from config import HISTORY_FILE, BAND_SETTINGS_FILE, LOGO_B64, SIMPLE_TEMPLATE_COLS, DEFAULT_BAND_SECTOR_SETTINGS
from geometry import decode_base64_safely, hex_and_transparency_to_kml_color, calculate_destination
from file_handlers import write_simple_xlsx, read_simple_xlsx
from dialogs import BandSectorCustomizationDialog, CustomTemplateDialog, MapViewerDialog, HistoryPopupDialog, HowToUseDialog


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
        flags = Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint
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

        settings_menu = menu_bar.addMenu("Settings")
        customize_bands_action = QAction("Customize Bands, Sectors & Border...", self)
        customize_bands_action.triggered.connect(self.open_band_sector_dialog)
        settings_menu.addAction(customize_bands_action)

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

        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        header_layout.setContentsMargins(10, 0, 0, 5)

        self.logo_lbl = QLabel()
        try:
            logo_bytes = decode_base64_safely(LOGO_B64)
            pixmap = QPixmap()
            pixmap.loadFromData(logo_bytes)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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

        shared_grid = QGridLayout()
        shared_grid.setSpacing(10)
        shared_grid.setColumnStretch(1, 1)

        lbl_output = QLabel("Output Folder")
        lbl_output.setFixedWidth(150)
        self.input_output = QLineEdit()
        default_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        self.input_output.setText(default_desktop if os.path.exists(default_desktop) else "")

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

        mode_tabs_layout = QHBoxLayout()
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

        for i, text in enumerate(["", "S1", "S2", "S3", "S4"]):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold;")
            form_layout.addWidget(lbl, 3, i)

        form_layout.addWidget(QLabel("Azimuth °"), 4, 0)
        self.az_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setPlaceholderText(f"S{i+1} Az")
            self.az_inputs.append(inp)
            form_layout.addWidget(inp, 4, i + 1)

        layout.addLayout(form_layout)

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

        grid.addWidget(QLabel("1. Simple Template"), 0, 0)
        btn_template_csv = QPushButton("Simple CSV Template")
        btn_template_csv.setObjectName("ImportBtn")
        btn_template_csv.clicked.connect(self.export_simple_template_csv)
        btn_template_xls = QPushButton("Simple Excel Template")
        btn_template_xls.setObjectName("SaveBtn")
        btn_template_xls.clicked.connect(self.export_simple_template_excel)

        grid.addWidget(btn_template_csv, 0, 1)
        grid.addWidget(btn_template_xls, 0, 2, 1, 2)

        grid.addWidget(QLabel("   Custom Template"), 1, 0)
        btn_custom_tmpl = QPushButton("Customized Export Template (Checklist)...")
        btn_custom_tmpl.setObjectName("ViewMapBtn")
        btn_custom_tmpl.clicked.connect(self.open_custom_template_dialog)
        grid.addWidget(btn_custom_tmpl, 1, 1, 1, 3)

        grid.addWidget(QLabel("2. Select Filled File"), 2, 0)
        self.input_csv_path = QLineEdit()
        self.input_csv_path.setPlaceholderText("Browse and select your filled file...")
        btn_browse_csv = QPushButton("Browse File")
        btn_browse_csv.setObjectName("BrowseBtn")
        btn_browse_csv.clicked.connect(self.browse_csv_file)
        grid.addWidget(self.input_csv_path, 2, 1, 1, 2)
        grid.addWidget(btn_browse_csv, 2, 3)

        grid.addWidget(QLabel("Default Length (m)"), 3, 0)
        self.input_multi_length = QLineEdit("120")
        grid.addWidget(self.input_multi_length, 3, 1)
        lbl_multi_wid = QLabel("Default Width °")
        lbl_multi_wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(lbl_multi_wid, 3, 2)
        self.input_multi_width = QLineEdit("60")
        grid.addWidget(self.input_multi_width, 3, 3)

        grid.addWidget(QLabel("Output File Name"), 4, 0)
        self.input_multi_outname = QLineEdit("imported_multi_sites.kml")
        grid.addWidget(self.input_multi_outname, 4, 1, 1, 3)
        layout.addLayout(grid)

        multi_band_frame = QFrame()
        multi_band_frame.setObjectName("RadioGroupFrame")
        mb_layout = QHBoxLayout(multi_band_frame)
        mb_layout.setContentsMargins(15, 8, 15, 8)
        self.chk_multi_use_bands = QCheckBox("Apply Customized Band Layers to Imported Sites")
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
        if self.rb_one_pin.isChecked(): return "pin"
        if self.rb_one_sector.isChecked(): return "sector"
        if self.rb_one_lines.isChecked(): return "lines"
        return "both"

    def get_multi_site_layer_mode(self):
        if self.rb_multi_pin.isChecked(): return "pin"
        if self.rb_multi_sector.isChecked(): return "sector"
        if self.rb_multi_lines.isChecked(): return "lines"
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
                QMainWindow, QWidget, QDialog { background-color: #2b2b2b; color: #ffffff; font-family: Arial, sans-serif; font-size: 14px; }
                QTabWidget::pane { border: 1px solid #444; background: #232323; }
                QTabBar::tab { background: #3c3f41; color: #ccc; padding: 8px 14px; border: 1px solid #555; }
                QTabBar::tab:selected { background: #005a9e; color: #fff; font-weight: bold; }
                QMenuBar { background-color: #1e1e1e; color: #ffffff; border-bottom: 1px solid #3c3f41; }
                QMenuBar::item:selected { background-color: #3c3f41; }
                QMenu { background-color: #2b2b2b; color: #ffffff; border: 1px solid #555; }
                QMenu::item:selected { background-color: #005a9e; }
                QFrame#ModeBox { background-color: #232323; border: 1px solid #3c3f41; border-radius: 6px; }
                QFrame#RadioGroupFrame { background-color: #323232; border: 1px solid #484848; border-radius: 5px; }
                QLineEdit, QComboBox, QSpinBox { background-color: #3c3f41; border: 1px solid #555; border-radius: 4px; padding: 6px; color: white; }
                QLineEdit:disabled { background-color: #262626; color: #666; border: 1px solid #3a3a3a; }
                QListWidget { background-color: #3c3f41; border: 1px solid #555; border-radius: 4px; outline: none; }
                QListWidget::item { padding: 10px; border-bottom: 1px solid #4a4d4f; }
                QListWidget::item:selected { background-color: #008000; color: white; font-weight: bold; }
                QPushButton#ModeTabBtn { background-color: #3c3f41; color: #bbbbbb; border: 1px solid #555; border-radius: 5px; padding: 11px; font-weight: bold; font-size: 14px; }
                QPushButton#ModeTabBtn:checked { background-color: #005a9e; color: #ffffff; border: 1px solid #4da3ff; }
                QPushButton#CreateOnlyBtn { background-color: #2e7d32; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 12px; }
                QPushButton#CreateOpenBtn { background-color: #008000; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 12px; }
                QPushButton#ViewMapBtn { background-color: #6a1b9a; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 11px; }
                QPushButton#SaveBtn { background-color: #005a9e; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 11px; }
                QPushButton#ImportBtn { background-color: #d83b01; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 10px; }
                QPushButton#BrowseBtn { background-color: #555555; color: white; border: none; border-radius: 4px; padding: 6px 12px; }
                QPushButton#RemoveBtn { background-color: #9e6a00; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 9px; }
                QRadioButton, QCheckBox { spacing: 8px; font-weight: bold; }
            """
        else:
            return """
                QMainWindow, QWidget, QDialog { background-color: #f4f6f8; color: #1e293b; font-family: Arial, sans-serif; font-size: 14px; }
                QMenuBar { background-color: #e2e8f0; color: #1e293b; border-bottom: 1px solid #cbd5e1; }
                QFrame#ModeBox { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; }
                QFrame#RadioGroupFrame { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 5px; }
                QLineEdit, QComboBox, QSpinBox { background-color: #ffffff; border: 1px solid #94a3b8; border-radius: 4px; padding: 6px; color: #1e293b; }
                QPushButton#ModeTabBtn { background-color: #e2e8f0; color: #475569; border: 1px solid #cbd5e1; border-radius: 5px; padding: 11px; font-weight: bold; }
                QPushButton#ModeTabBtn:checked { background-color: #0284c7; color: #ffffff; border: 1px solid #0369a1; }
                QPushButton#CreateOnlyBtn { background-color: #2e7d32; color: white; font-weight: bold; border-radius: 4px; padding: 12px; }
                QPushButton#CreateOpenBtn { background-color: #15803d; color: white; font-weight: bold; border-radius: 4px; padding: 12px; }
                QPushButton#ViewMapBtn { background-color: #7b1fa2; color: white; font-weight: bold; border-radius: 4px; padding: 11px; }
                QPushButton#SaveBtn { background-color: #0284c7; color: white; font-weight: bold; border-radius: 4px; padding: 11px; }
                QPushButton#ImportBtn { background-color: #ea580c; color: white; font-weight: bold; border-radius: 4px; padding: 10px; }
                QPushButton#BrowseBtn { background-color: #64748b; color: white; border-radius: 4px; padding: 6px 12px; }
                QPushButton#RemoveBtn { background-color: #b45309; color: white; font-weight: bold; border-radius: 4px; padding: 9px; }
                QRadioButton, QCheckBox { spacing: 8px; font-weight: bold; }
            """

    def browse_output_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder: self.input_output.setText(folder)

    def browse_csv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Template File", "", "Template Files (*.csv *.xlsx);;All Files (*)")
        if file_path: self.input_csv_path.setText(file_path)

    def save_template_file(self, columns_list, default_name, is_excel=False):
        if is_excel:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel Template", default_name, "Excel Files (*.xlsx)")
            if not file_path: return
            try:
                if not file_path.lower().endswith(".xlsx"): file_path += ".xlsx"
                write_simple_xlsx(file_path, [columns_list])
                QMessageBox.information(self, "Success", f"Excel Template exported successfully with {len(columns_list)} columns!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))
        else:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV Template", default_name, "CSV Files (*.csv)")
            if not file_path: return
            try:
                if not file_path.lower().endswith(".csv"): file_path += ".csv"
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
        QMessageBox.information(self, "About App", "<h3>GIS Layer Creator</h3><p>Developed by: Ahmad</p>")

    def show_support_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Support")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText("<h3>Technical Support</h3><p>Email: ahmadkha202020@gmail.com</p><p>WhatsApp: +201021785230</p>")
        msg.exec()

    def show_history_popup(self):
        self.populate_history_list()
        self.history_dialog.show()
        self.history_dialog.raise_()
        self.history_dialog.activateWindow()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
            except Exception: return {}
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
        if not site_name or site_name not in self.history_data: return
        self.switch_mode(0)
        data = self.history_data[site_name]
        self.input_name.setText(data.get("site_name", ""))
        self.input_option.setText(data.get("option_name", ""))
        self.input_coords.setText(data.get("coords", ""))
        self.input_length.setText(data.get("length", "120") or "120")
        self.input_width.setText(data.get("width", "60") or "60")
        layer_mode = data.get("layer_mode", "both")
        if layer_mode == "pin": self.rb_one_pin.setChecked(True)
        elif layer_mode == "sector": self.rb_one_sector.setChecked(True)
        elif layer_mode == "lines": self.rb_one_lines.setChecked(True)
        else: self.rb_one_both.setChecked(True)
        sectors = data.get("sectors", [])
        for i in range(4):
            if i < len(sectors): self.az_inputs[i].setText(sectors[i].get("azimuth", ""))
            else: self.az_inputs[i].clear()

    def remove_selected_history(self):
        current_item = self.history_dialog.list_widget.currentItem()
        if not current_item: return
        site_name = current_item.text()
        if QMessageBox.question(self.history_dialog, 'Confirm', f"Remove '{site_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if site_name in self.history_data:
                del self.history_data[site_name]
                self.save_history()
                self.populate_history_list()

    def clear_history(self):
        if QMessageBox.question(self, 'Confirm', 'Clear all history?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.history_data = {}
            self.save_history()
            self.populate_history_list()

    def export_history_data(self):
        if not self.history_data: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export History", "history.csv", "CSV Files (*.csv)")
        if not file_path: return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["site name", "option", "lat", "long", "az-a", "az-b", "az-c", "az-d", "line length"])
                for site_key, data in self.history_data.items():
                    coords = data.get("coords", "").split(",")
                    lat_str = coords[0].strip() if len(coords) > 0 else ""
                    lon_str = coords[1].strip() if len(coords) > 1 else ""
                    sectors = data.get("sectors", [])
                    az_list = [sectors[i].get("azimuth", "") if i < len(sectors) else "" for i in range(4)]
                    writer.writerow([data.get("site_name", site_key), data.get("option_name", ""), lat_str, lon_str, az_list[0], az_list[1], az_list[2], az_list[3], data.get("length", "120")])
            QMessageBox.information(self, "Success", f"History exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def add_site_to_history(self, site_name, option_name, coord_text, length, width, layer_mode, sectors_data, extra_data=None):
        self.history_data[site_name] = {
            "site_name": site_name, "option_name": option_name, "coords": coord_text,
            "length": str(length), "width": str(width), "layer_mode": layer_mode,
            "sectors": sectors_data, "extra_data": extra_data or {}
        }

    def save_to_history(self, show_message=True):
        try:
            site_name = self.input_name.text().strip() or "Site"
            option_name = self.input_option.text().strip()
            coord_text = self.input_coords.text().strip()
            if not coord_text: raise ValueError("Coordinates are empty.")
            lat_str, lon_str = coord_text.split(',')
            float(lat_str.strip()); float(lon_str.strip())
            length_val = self.input_length.text().strip() or "120"
            width_val = self.input_width.text().strip() or "60"
            layer_mode = self.get_one_site_layer_mode()
            sectors_data = [{"azimuth": self.az_inputs[i].text().strip()} for i in range(4)]
            self.add_site_to_history(site_name, option_name, coord_text, length_val, width_val, layer_mode, sectors_data)
            self.save_history()
            self.populate_history_list()
            if show_message: QMessageBox.information(self, "Saved", f"Site '{site_name}' saved.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def match_band_name(self, raw_band_str):
        if not raw_band_str: return None
        s = str(raw_band_str).strip().lower()
        if "700" in s: return "Band 700"
        if "1800" in s: return "Band 1800"
        if "2600" in s: return "Band 2600"
        if "c-band" in s or "cband" in s or "3500" in s or s == "c": return "C-Band"
        return None

    def get_active_bands_for_site(self, use_bands_flag, specific_band_str=None):
        bands_cfg = self.band_sector_settings.get("bands", DEFAULT_BAND_SECTOR_SETTINGS["bands"])
        matched = self.match_band_name(specific_band_str)
        if matched and matched in bands_cfg:
            b = bands_cfg[matched]
            return [{"band_name": matched, "length": float(b["length"]), "width": float(b["width"]), "transparency": int(b["transparency"]), "color": b["color"]}]
        if use_bands_flag:
            active_list = []
            for b_name in ["Band 700", "Band 1800", "Band 2600", "C-Band"]:
                b = bands_cfg.get(b_name, {})
                if b.get("enabled", False):
                    active_list.append({"band_name": b_name, "length": float(b.get("length", 140.0)), "width": float(b.get("width", 60.0)), "transparency": int(b.get("transparency", 50)), "color": b.get("color", "#00e5ff")})
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
            return float(sec_cfg.get("length", default_length)), float(sec_cfg.get("width", default_width)), int(sec_cfg.get("transparency", 50)), sec_cfg.get("color", "#00e5ff"), s_key
        fallback_colors = ["#00e5ff", "#ffeb3b", "#ff5252", "#69f0ae"]
        return default_length, default_width, 50, fallback_colors[sector_idx % len(fallback_colors)], s_key

    def filter_extra_data_for_sector(self, extra_data, sector_idx=None):
        if not extra_data: return {}
        if sector_idx is None: return extra_data
        target_s = f"s{sector_idx + 1}"
        other_sectors = {f"s{j}" for j in range(1, 5) if j != (sector_idx + 1)}
        filtered = {}
        for k, v in extra_data.items():
            k_low = k.strip().lower()
            tokens = k_low.replace("_", " ").replace("-", " ").split()
            if any(os_tok in tokens for os_tok in other_sectors): continue
            filtered[k] = v
        return filtered

    def build_kml_description_html(self, site_name, option_name, lat, lon, length, sector_width, band_name="", extra_data=None, sector_idx=None):
        rows_html = f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Site Name</td><td style='padding:4px;'>{escape(str(site_name))}</td></tr><tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Coordinates</td><td style='padding:4px;'>{lat}, {lon}</td></tr>"
        if option_name: rows_html += f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Option</td><td style='padding:4px;'>{escape(str(option_name))}</td></tr>"
        if band_name: rows_html += f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Band Layer</td><td style='padding:4px;'>{escape(str(band_name))}</td></tr>"
        if sector_idx is not None: rows_html += f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Sector</td><td style='padding:4px;'>S{sector_idx + 1}</td></tr>"
        rows_html += f"<tr><td style='font-weight:bold; background:#f0f0f0; padding:4px;'>Length / Width</td><td style='padding:4px;'>{length}m / {sector_width}°</td></tr>"
        for k, v in self.filter_extra_data_for_sector(extra_data, sector_idx).items():
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
                    if not az_text or az_text in ["-", " "]: continue
                    try: azimuth = float(az_text)
                    except ValueError: continue

                    s_len, s_wid, s_trans, s_col, s_prefix = self.get_sector_parameters(i, length, sector_width, b_cfg)
                    desc_html = self.build_kml_description_html(site_name, option_name, lat, lon, s_len, s_wid, b_label, extra_data, sector_idx=i)
                    pol = target_fol.newpolygon(name=f"{s_prefix} Az:{azimuth:g}")
                    pol.description = desc_html
                    start_bearing = azimuth - (s_wid / 2.0)
                    arc_coords = []
                    steps = max(int(s_wid / 5) + 1, 2)
                    bearing_step = s_wid / (steps - 1)
                    for step in range(steps):
                        dest_lat, dest_lon = calculate_destination(lat, lon, start_bearing + (step * bearing_step), s_len)
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
                    if not az_text or az_text in ["-", " "]: continue
                    try: azimuth = float(az_text)
                    except ValueError: continue
                    s_len, s_wid, s_trans, s_col, s_prefix = self.get_sector_parameters(i, length, sector_width, b_cfg)
                    desc_html = self.build_kml_description_html(site_name, option_name, lat, lon, s_len, s_wid, b_label, extra_data, sector_idx=i)
                    end_lat, end_lon = calculate_destination(lat, lon, azimuth, s_len)
                    lin = target_fol.newlinestring(name=f"{s_prefix} Az:{azimuth:g}")
                    lin.description = desc_html
                    lin.coords = [(lon, lat, height), (end_lon, end_lat, height)]
                    lin.style.linestyle.color = hex_and_transparency_to_kml_color(s_col, 0)
                    lin.style.linestyle.width = 3

        if layer_mode in ("pin", "both", "lines"):
            point_label = f"{site_name} - {option_name}" if option_name else site_name
            pnt = fol.newpoint(name=point_label)
            pnt.description = self.build_kml_description_html(site_name, option_name, lat, lon, length, sector_width, "", extra_data, sector_idx=None)
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
                if not az_text or az_text in ["-", " "]: continue
                try: azimuth = float(az_text)
                except ValueError: continue

                s_len, s_wid, s_trans, s_col, s_prefix = self.get_sector_parameters(i, length, sector_width, b_cfg)
                opacity_float = max(0.05, min(1.0, (100 - s_trans) / 100.0))
                sector_extra = self.filter_extra_data_for_sector(extra_data, sector_idx=i)

                if layer_mode in ("sector", "both"):
                    start_bearing = azimuth - (s_wid / 2.0)
                    steps = max(int(s_wid / 5) + 1, 2)
                    bearing_step = s_wid / (steps - 1)
                    poly_coords = [[lat, lon]]
                    for step in range(steps):
                        dest_lat, dest_lon = calculate_destination(lat, lon, start_bearing + (step * bearing_step), s_len)
                        poly_coords.append([dest_lat, dest_lon])
                    poly_coords.append([lat, lon])
                    polygons.append({
                        "name": f"{s_prefix} (Azimuth: {azimuth:g}°)", "coords": poly_coords,
                        "color": s_col, "opacity": opacity_float, "border_enabled": border_enabled,
                        "border_color": border_hex, "length": s_len, "width": s_wid, "sector_extra": sector_extra
                    })
                if layer_mode == "lines":
                    end_lat, end_lon = calculate_destination(lat, lon, azimuth, s_len)
                    lines.append({
                        "name": f"{s_prefix} (Azimuth: {azimuth:g}°)", "coords": [[lat, lon], [end_lat, end_lon]],
                        "color": s_col, "length": s_len, "sector_extra": sector_extra
                    })

        return {
            "site_name": site_name, "option_name": option_name, "lat": lat, "lon": lon,
            "length": length, "sector_width": sector_width, "layer_mode": layer_mode,
            "polygons": polygons, "lines": lines, "extra_data": extra_data or {}
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
                ge_paths = [r"C:\Program Files\Google\Google Earth Pro\client\googleearth.exe", r"C:\Program Files (x86)\Google\Google Earth Pro\client\googleearth.exe"]
                for gpath in ge_paths:
                    if os.path.exists(gpath):
                        subprocess.Popen([gpath, abs_path]); return
                os.startfile(abs_path)
            elif viewer == "QGIS":
                qgis_paths = [r"C:\Program Files\QGIS 3.34.0\bin\qgis-bin.exe", r"C:\Program Files\QGIS 3.28.0\bin\qgis-bin.exe"]
                for qpath in qgis_paths:
                    if os.path.exists(qpath):
                        subprocess.Popen([qpath, abs_path]); return
                os.startfile(abs_path)
            elif viewer == "ArcGIS Earth":
                arc_paths = [r"C:\Program Files\ArcGIS\ArcGIS Earth\bin\ArcGISEarth.exe", r"C:\Program Files (x86)\ArcGIS\ArcGIS Earth\bin\ArcGISEarth.exe"]
                for apath in arc_paths:
                    if os.path.exists(apath):
                        subprocess.Popen([apath, abs_path]); return
                os.startfile(abs_path)
        except Exception as e:
            QMessageBox.warning(self, "Viewer Launch Warning", f"Saved KML, but could not launch {viewer}:\n{str(e)}")

    def create_single_kml(self, open_file=False):
        try:
            self.save_to_history(show_message=False)
            site_name = self.input_name.text().strip() or "Site"
            option_name = self.input_option.text().strip()
            lat_str, lon_str = self.input_coords.text().split(',')
            lat = float(lat_str.strip()); lon = float(lon_str.strip())
            length = float(self.input_length.text().strip() or 120.0)
            sector_width = float(self.input_width.text().strip() or 60.0)
            layer_mode = self.get_one_site_layer_mode()
            use_bands = self.chk_use_band_layers.isChecked()

            kml = simplekml.Kml()
            fol = kml.newfolder(name=f"{site_name} {option_name}".strip())
            azims = [inp.text().strip() for inp in self.az_inputs]
            self.generate_site_kml(fol, site_name, option_name, lat, lon, 0.0, length, azims, layer_mode, sector_width, None, use_bands)
            output_filename = self.get_output_filepath(f"{site_name}_design.kml")
            kml.save(output_filename)
            if open_file: self.open_kml_file(output_filename)
            QMessageBox.information(self, "Success", f"Layer saved to:\n'{output_filename}'")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def view_single_site_in_map(self):
        try:
            self.save_to_history(show_message=False)
            site_name = self.input_name.text().strip() or "Site"
            option_name = self.input_option.text().strip()
            lat_str, lon_str = self.input_coords.text().split(',')
            lat = float(lat_str.strip()); lon = float(lon_str.strip())
            length = float(self.input_length.text().strip() or 120.0)
            sector_width = float(self.input_width.text().strip() or 60.0)
            layer_mode = self.get_one_site_layer_mode()
            use_bands = self.chk_use_band_layers.isChecked()
            azims = [inp.text().strip() for inp in self.az_inputs]

            site_feature = self.build_site_map_feature(site_name, option_name, lat, lon, length, azims, layer_mode, sector_width, None, use_bands)
            self.map_viewer_dialog.render_sites_on_map([site_feature])
        except Exception as e:
            QMessageBox.critical(self, "Map View Error", str(e))

    def parse_multi_sites_file(self):
        file_path = self.input_csv_path.text().strip()
        if not file_path or not os.path.exists(file_path):
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Template File", "", "Template Files (*.csv *.xlsx);;All Files (*)")
            if not file_path: return None
            self.input_csv_path.setText(file_path)

        layer_mode = self.get_multi_site_layer_mode()
        default_length = float(self.input_multi_length.text().strip() or 120.0)
        default_width = float(self.input_multi_width.text().strip() or 60.0)

        def clean_cell(value):
            if value is None: return ""
            val = str(value).strip()
            return "" if val in ["-", ""] else val

        def norm_key(k):
            return str(k).strip().lower().replace(" ", "").replace("_", "")

        raw_rows = []
        if file_path.lower().endswith(".xlsx"):
            xlsx_rows = read_simple_xlsx(file_path)
            if not xlsx_rows: raise ValueError("Excel file is empty.")
            raw_headers = [str(h).strip() for h in xlsx_rows[0]]
            for r in xlsx_rows[1:]:
                row_dict = {}
                for i, h in enumerate(raw_headers):
                    if h: row_dict[h] = r[i] if i < len(r) else ""
                raw_rows.append(row_dict)
        else:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames: raise ValueError("CSV file has no headers.")
                for row in reader: raw_rows.append(row)

        if not raw_rows: raise ValueError("No data rows found.")
        sample_keys = list(raw_rows[0].keys())
        norm_to_orig = {norm_key(k): k for k in sample_keys}

        has_site = any(k in norm_to_orig for k in ('sitename', 'site', 'sitename/option', 'name'))
        has_lat = any(k in norm_to_orig for k in ('lat', 'latitude'))
        has_lon = any(k in norm_to_orig for k in ('long', 'lon', 'longitude'))
        if not (has_site and has_lat and has_lon):
            raise ValueError("Missing mandatory columns: 'site name', 'lat', 'long'.")

        standard_norm_keys = {
            'sitename', 'site', 'sitename/option', 'name', 'option', 'opt', 'lat', 'latitude', 'long', 'lon', 'longitude',
            'aza', 'az-a', 's1', 'sector1', 'azb', 'az-b', 's2', 'sector2', 'azc', 'az-c', 's3', 'sector3',
            'azd', 'az-d', 's4', 'sector4', 'linelength', 'length', 'sectorlength', 'sectorwidth', 'width', 'beamwidth'
        }

        def get_val(row_obj, possible_norm_keys, default_val=""):
            for pk in possible_norm_keys:
                if pk in norm_to_orig: return clean_cell(row_obj.get(norm_to_orig[pk], ""))
            return default_val

        parsed_sites = []
        for row in raw_rows:
            site_name = get_val(row, ['sitename', 'site', 'sitename/option', 'name'], 'Unnamed')
            option = get_val(row, ['option', 'opt'], '')
            lat_str = get_val(row, ['lat', 'latitude'], '')
            lon_str = get_val(row, ['long', 'lon', 'longitude'], '')
            if not lat_str or not lon_str: continue

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
                if norm_key(orig_col) not in standard_norm_keys:
                    val = clean_cell(row.get(orig_col, ""))
                    if val: extra_data[orig_col] = val

            parsed_sites.append({
                "site_name": site_name, "option": option, "lat": float(lat_str), "lon": float(lon_str),
                "length": length, "sector_width": sector_width, "layer_mode": layer_mode,
                "azims": azims, "extra_data": extra_data
            })
        return parsed_sites

    def create_multi_sites_kml(self, open_file=False):
        try:
            parsed_sites = self.parse_multi_sites_file()
            if not parsed_sites: return
            use_bands = self.chk_multi_use_bands.isChecked()
            kml = simplekml.Kml()
            for s in parsed_sites:
                coord_text = f"{s['lat']}, {s['lon']}"
                sectors_data = [{"azimuth": az} for az in s["azims"]]
                self.add_site_to_history(s["site_name"], s["option"], coord_text, s["length"], s["sector_width"], s["layer_mode"], sectors_data, s["extra_data"])
                fol = kml.newfolder(name=f"{s['site_name']} {s['option']}".strip())
                self.generate_site_kml(fol, s["site_name"], s["option"], s["lat"], s["lon"], 0.0, s["length"], s["azims"], s["layer_mode"], s["sector_width"], s["extra_data"], use_bands=use_bands)

            self.save_history()
            self.populate_history_list()
            out_name = self.input_multi_outname.text().strip() or "imported_multi_sites.kml"
            if not out_name.lower().endswith(".kml"): out_name += ".kml"
            output_filename = self.get_output_filepath(out_name)
            kml.save(output_filename)
            if open_file: self.open_kml_file(output_filename)
            QMessageBox.information(self, "Success", f"Imported {len(parsed_sites)} sites & created:\n'{output_filename}'")
        except Exception as e:
            QMessageBox.critical(self, "Multi-Site Import Error", str(e))

    def view_multi_sites_in_map(self):
        try:
            parsed_sites = self.parse_multi_sites_file()
            if not parsed_sites: return
            use_bands = self.chk_multi_use_bands.isChecked()
            map_features = []
            for s in parsed_sites:
                coord_text = f"{s['lat']}, {s['lon']}"
                sectors_data = [{"azimuth": az} for az in s["azims"]]
                self.add_site_to_history(s["site_name"], s["option"], coord_text, s["length"], s["sector_width"], s["layer_mode"], sectors_data, s["extra_data"])
                feat = self.build_site_map_feature(s["site_name"], s["option"], s["lat"], s["lon"], s["length"], s["azims"], s["layer_mode"], s["sector_width"], s["extra_data"], use_bands=use_bands)
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