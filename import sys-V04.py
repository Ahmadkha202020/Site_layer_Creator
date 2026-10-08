import sys
import os
import csv
import json
import base64
import math
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QPushButton, QListWidget, 
    QFileDialog, QMessageBox, QCheckBox, QFrame, QComboBox
)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt
import simplekml

HISTORY_FILE = "site_history.json"

LOGO_B64 = (
    "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"
    "lGVIpqv3R0J2qN/f"
)


class SiteLayerCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("One Site Design Layer")
        self.setGeometry(100, 100, 1150, 780)

        self.history_data = self.load_history()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.setStyleSheet(self.get_stylesheet())

        self.create_menu_bar()
        self.init_ui(central_widget)
        self.populate_history_list()

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # --- File Menu ---
        file_menu = menu_bar.addMenu("File")

        change_output_action = QAction("Change Output Folder", self)
        change_output_action.triggered.connect(self.browse_output_directory)
        file_menu.addAction(change_output_action)

        file_menu.addSeparator()

        export_action = QAction("Export Template (CSV)", self)
        export_action.triggered.connect(self.export_template)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        clear_history_action = QAction("Clear All History", self)
        clear_history_action.triggered.connect(self.clear_history)
        file_menu.addAction(clear_history_action)

        # --- Insert Menu ---
        insert_menu = menu_bar.addMenu("Insert")

        pins_only_action = QAction("Need Only Pins", self)
        pins_only_action.triggered.connect(self.set_pins_only_mode)
        insert_menu.addAction(pins_only_action)

        sectorized_only_action = QAction("Need Only Sectorized", self)
        sectorized_only_action.triggered.connect(self.set_sectorized_only_mode)
        insert_menu.addAction(sectorized_only_action)

    def init_ui(self, central_widget):
        main_h_layout = QHBoxLayout(central_widget)
        main_h_layout.setContentsMargins(20, 20, 20, 20)
        main_h_layout.setSpacing(20)

        # ==========================================
        # 1. Left Panel: History List
        # ==========================================
        left_panel = QVBoxLayout()

        lbl_history = QLabel("History")
        lbl_history.setStyleSheet("font-size: 16px; font-weight: bold; color: #77aa77;")
        left_panel.addWidget(lbl_history)

        self.list_history = QListWidget()
        self.list_history.itemClicked.connect(self.load_from_history)
        left_panel.addWidget(self.list_history)

        btn_remove_history = QPushButton("Remove Selected")
        btn_remove_history.setObjectName("RemoveBtn")
        btn_remove_history.clicked.connect(self.remove_selected_history)
        left_panel.addWidget(btn_remove_history)

        # ==========================================
        # 2. Right Panel: Input Form
        # ==========================================
        right_panel = QVBoxLayout()

        # Header Logo + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(25)
        header_layout.setContentsMargins(30, 10, 0, 20)

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
                140, 140,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_lbl.setPixmap(pixmap)
        header_layout.addWidget(self.logo_lbl)

        title = QLabel()
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setText(
            "<div style='font-size:36px; font-weight:bold; line-height:1.15;'>"
            "<span style='color:#ffffff;'>GIS LAYER</span><br>"
            "<span style='color:#a9d3a5;'>CREATOR</span>"
            "</div>"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        right_panel.addLayout(header_layout)

        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(2, 1)
        form_layout.setColumnStretch(3, 1)
        form_layout.setColumnStretch(4, 1)

        # Output Directory (Desktop Default)
        lbl_output = QLabel("Output Folder")
        self.input_output = QLineEdit()
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.input_output.setText(desktop_path)

        btn_browse_output = QPushButton("Browse")
        btn_browse_output.setObjectName("BrowseBtn")
        btn_browse_output.clicked.connect(self.browse_output_directory)

        form_layout.addWidget(lbl_output, 0, 0)
        form_layout.addWidget(self.input_output, 0, 1, 1, 3)
        form_layout.addWidget(btn_browse_output, 0, 4)

        # Site Name & Option
        lbl_name = QLabel("Site Name / Option")
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Site Name")

        self.input_option = QLineEdit()
        self.input_option.setPlaceholderText("Option")
        self.input_option.setFixedWidth(150)

        form_layout.addWidget(lbl_name, 1, 0)
        form_layout.addWidget(self.input_name, 1, 1, 1, 3)
        form_layout.addWidget(self.input_option, 1, 4)

        # Lat, Long
        lbl_coords = QLabel("Latitude, Longitude")
        self.input_coords = QLineEdit()
        self.input_coords.setPlaceholderText("Lat, Long")

        form_layout.addWidget(lbl_coords, 2, 0)
        form_layout.addWidget(self.input_coords, 2, 1, 1, 4)

        # Line Length & Sector Width
        lbl_length = QLabel("Line Length (m)")
        self.input_length = QLineEdit()

        self.lbl_width = QLabel("Sector Width °")
        self.input_width = QLineEdit()
        self.input_width.setPlaceholderText("60")
        self.input_width.setText("60")

        form_layout.addWidget(lbl_length, 3, 0)
        form_layout.addWidget(self.input_length, 3, 1)
        form_layout.addWidget(self.lbl_width, 3, 3)
        form_layout.addWidget(self.input_width, 3, 4)

        form_layout.addWidget(QLabel(""), 4, 0)

        # Sector Headers
        headers = ["", "S1", "S2", "S3", "S4"]
        for i, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold;")
            form_layout.addWidget(lbl, 5, i)

        # Azimuth inputs
        lbl_azimuth = QLabel("Azimuth °")
        form_layout.addWidget(lbl_azimuth, 6, 0)

        self.az_inputs = []
        for i in range(4):
            inp = QLineEdit()
            self.az_inputs.append(inp)
            form_layout.addWidget(inp, 6, i + 1)

        right_panel.addLayout(form_layout)

        # Checkbox
        self.chk_sectorization = QCheckBox("Use Sectorization")
        self.chk_sectorization.setChecked(True)
        self.chk_sectorization.stateChanged.connect(self.toggle_sector_width)
        right_panel.addWidget(self.chk_sectorization)

        # Viewer Dropdown
        app_select_layout = QHBoxLayout()
        lbl_app_choice = QLabel("Open KML File With:")
        lbl_app_choice.setStyleSheet("font-weight: bold; color: #a9d3a5;")

        self.combo_app_choice = QComboBox()
        self.combo_app_choice.addItems(["Google Earth", "QGIS", "ArcGIS Earth"])
        
        app_select_layout.addWidget(lbl_app_choice)
        app_select_layout.addWidget(self.combo_app_choice, 1)
        right_panel.addLayout(app_select_layout)

        # Control Buttons
        btn_layout_row1 = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.clicked.connect(self.save_to_history)
        btn_layout_row1.addWidget(self.btn_save, 1)

        self.btn_import = QPushButton("Import from CSV")
        self.btn_import.setObjectName("ImportBtn")
        self.btn_import.clicked.connect(self.import_multi_sites)
        btn_layout_row1.addWidget(self.btn_import, 1)

        right_panel.addLayout(btn_layout_row1)

        btn_layout_row2 = QHBoxLayout()
        self.btn_create_only = QPushButton("Create Layer")
        self.btn_create_only.setObjectName("CreateOnlyBtn")
        self.btn_create_only.clicked.connect(lambda: self.create_kml(open_file=False))

        self.btn_create_open = QPushButton("Create and Open Layer")
        self.btn_create_open.setObjectName("CreateOpenBtn")
        self.btn_create_open.clicked.connect(lambda: self.create_kml(open_file=True))

        btn_layout_row2.addWidget(self.btn_create_only, 1)
        btn_layout_row2.addWidget(self.btn_create_open, 1)

        right_panel.addLayout(btn_layout_row2)

        main_h_layout.addLayout(left_panel, 1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #555;")
        main_h_layout.addWidget(line)

        main_h_layout.addLayout(right_panel, 4)

        self.toggle_sector_width()

    def set_pins_only_mode(self):
        self.chk_sectorization.setChecked(False)
        for inp in self.az_inputs:
            inp.clear()
        QMessageBox.information(self, "Insert Mode", "Switched to 'Pins Only' mode.")

    def set_sectorized_only_mode(self):
        self.chk_sectorization.setChecked(True)
        QMessageBox.information(self, "Insert Mode", "Switched to 'Sectorized' mode.")

    def browse_output_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.input_output.setText(folder)

    def toggle_sector_width(self):
        is_checked = self.chk_sectorization.isChecked()
        self.input_width.setEnabled(is_checked)
        self.lbl_width.setEnabled(is_checked)
        if not is_checked:
            self.input_width.setStyleSheet("background-color: #2b2b2b; color: #777; border: 1px solid #444;")
        else:
            self.input_width.setStyleSheet("")

    def get_stylesheet(self):
        return """
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: Arial, sans-serif;
                font-size: 14px;
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
                padding: 5px;
                color: white;
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
            QPushButton#CreateOnlyBtn {
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
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
                font-size: 14px;
            }
            QPushButton#CreateOpenBtn:hover {
                background-color: #009900;
            }
            QPushButton#SaveBtn {
                background-color: #005a9e;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
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
                padding: 12px;
                font-size: 14px;
            }
            QPushButton#ImportBtn:hover {
                background-color: #ea4a1f;
            }
            QPushButton#BrowseBtn {
                background-color: #555555;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton#BrowseBtn:hover {
                background-color: #666666;
            }
            QPushButton#RemoveBtn {
                background-color: #9e6a00;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin-top: 5px;
            }
            QPushButton#RemoveBtn:hover {
                background-color: #c08000;
            }
            QCheckBox {
                spacing: 10px;
                margin-top: 5px;
                margin-bottom: 5px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 1px solid #777;
                border-radius: 3px;
                background: #3c3f41;
            }
            QCheckBox::indicator:checked {
                background: #ffffff;
            }
        """

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
        self.list_history.clear()
        for site_name in self.history_data.keys():
            self.list_history.addItem(site_name)

    def load_from_history(self, item):
        site_name = item.text()
        if not site_name or site_name not in self.history_data:
            return

        data = self.history_data[site_name]
        self.input_name.setText(data.get("site_name", ""))
        self.input_option.setText(data.get("option_name", ""))
        self.input_coords.setText(data.get("coords", ""))
        self.input_length.setText(data.get("length", ""))
        self.input_width.setText(data.get("width", "60"))
        self.chk_sectorization.setChecked(data.get("sectorization", True))

        sectors = data.get("sectors", [])
        for i in range(4):
            if i < len(sectors):
                self.az_inputs[i].setText(sectors[i].get("azimuth", ""))
            else:
                self.az_inputs[i].clear()

    def remove_selected_history(self):
        current_item = self.list_history.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a history item to remove.")
            return

        site_name = current_item.text()
        reply = QMessageBox.question(
            self, 'Confirm', 
            f"Are you sure you want to remove '{site_name}' from history?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if site_name in self.history_data:
                del self.history_data[site_name]
                self.save_history()
                self.populate_history_list()
                QMessageBox.information(self, "Success", f"'{site_name}' removed from history.")

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

    def add_site_to_history(self, site_name, option_name, coord_text, length, width, sectorization, sectors_data):
        self.history_data[site_name] = {
            "site_name": site_name,
            "option_name": option_name,
            "coords": coord_text,
            "length": str(length),
            "width": str(width),
            "sectorization": sectorization,
            "sectors": sectors_data
        }

    def save_to_history(self, show_message=True):
        try:
            site_name = self.input_name.text() or "Site"
            option_name = self.input_option.text()
            coord_text = self.input_coords.text()

            if not coord_text:
                raise ValueError("Coordinates are empty. Please enter Lat, Long.")

            try:
                lat_str, lon_str = coord_text.split(',')
                float(lat_str.strip())
                float(lon_str.strip())
            except Exception:
                raise ValueError("Coordinate format invalid. Use 'Lat, Long'.")

            sectors_data = [{"azimuth": self.az_inputs[i].text()} for i in range(4)]

            self.add_site_to_history(
                site_name, option_name, coord_text, 
                self.input_length.text(), self.input_width.text(), 
                self.chk_sectorization.isChecked(), sectors_data
            )

            self.save_history()
            self.populate_history_list()

            if show_message:
                QMessageBox.information(self, "Saved", f"Site '{site_name}' saved to history successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def export_template(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV Template", "site_template.csv", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["site name", "option", "lat", "long", "az-a", "az-b", "az-c", "az-d", "line length"])

            QMessageBox.information(self, "Success", "Template exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

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

    def generate_site_kml(self, fol, site_name, option_name, lat, lon, height, length, azims, is_sectorization, sector_width):
        kml_outline_color = "ffffffff"

        for i in range(4):
            az_text = str(azims[i]).strip() if i < len(azims) and azims[i] is not None else ""
            if not az_text or az_text in ["-", " "]:
                continue

            try:
                azimuth = float(az_text)
            except Exception:
                continue

            if is_sectorization:
                pol = fol.newpolygon(name=f"S{i+1} Az:{azimuth}")
                start_bearing = azimuth - (sector_width / 2)

                arc_coords = []
                steps = int(sector_width / 5) + 1 
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
            else:
                end_lat, end_lon = self.calculate_destination(lat, lon, azimuth, length)
                lin = fol.newlinestring(name=f"S{i+1} Az:{azimuth}")
                lin.coords = [(lon, lat, height), (end_lon, end_lat, height)]
                lin.style.linestyle.color = kml_outline_color
                lin.style.linestyle.width = 3

        pnt = fol.newpoint(name=f"{site_name} - {option_name}")
        pnt.coords = [(lon, lat, height)]
        pnt.style.iconstyle.scale = 1.0 
        pnt.style.labelstyle.scale = 1.0
        pnt.style.labelstyle.color = simplekml.Color.white

    def get_output_filepath(self, filename):
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
                        r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe"
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

        except Exception as e:
            QMessageBox.warning(self, "Launch Warning", f"Could not open file with {app_choice}: {str(e)}\nOpening with default app.")
            if sys.platform == 'win32':
                os.startfile(abs_path)

    def create_kml(self, open_file=False):
        try:
            self.save_to_history(show_message=False)

            site_name = self.input_name.text() or "Site"
            option_name = self.input_option.text()

            lat_str, lon_str = self.input_coords.text().split(',')
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())

            length = float(self.input_length.text()) if self.input_length.text() else 0.0
            sector_width = float(self.input_width.text()) if self.input_width.text() else 60.0
            is_sectorization = self.chk_sectorization.isChecked()

            kml = simplekml.Kml()
            fol = kml.newfolder(name=f"{site_name} {option_name}")

            azims = [inp.text() for inp in self.az_inputs]

            self.generate_site_kml(fol, site_name, option_name, lat, lon, 0.0, length, azims, is_sectorization, sector_width)

            output_filename = self.get_output_filepath(f"{site_name}_design.kml")
            kml.save(output_filename)

            if open_file:
                self.open_kml_file(output_filename)

            QMessageBox.information(self, "Success", f"Layer saved to '{output_filename}' successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def import_multi_sites(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if not file_path:
            return

        try:
            kml = simplekml.Kml()
            is_sectorization = self.chk_sectorization.isChecked()
            sector_width = float(self.input_width.text()) if self.input_width.text() else 60.0

            def clean_cell(value):
                if value is None:
                    return ""
                val = str(value).strip()
                if val in ["-", ""]:
                    return ""
                return val

            with open(file_path, 'r', encoding='utf-8-sig') as f: 
                reader = csv.DictReader(f)
                reader.fieldnames = [name.strip().lower().replace(" ", "") for name in reader.fieldnames]

                required_cols = ['sitename', 'option', 'lat', 'long', 'az-a', 'az-b', 'az-c', 'az-d', 'linelength']
                for col in required_cols:
                    if col not in reader.fieldnames:
                        if col == 'sitename' and 'sitename/option' in reader.fieldnames:
                            continue
                        raise ValueError(f"Missing column: '{col}'. Expected: site name, option, lat, long, az-a, az-b, az-c, az-d, line length")

                count = 0
                for row in reader:
                    site_name = clean_cell(row.get('sitename', row.get('sitename/option', 'Unnamed')))
                    option = clean_cell(row.get('option', ''))

                    lat_str = clean_cell(row.get('lat', '0'))
                    lon_str = clean_cell(row.get('long', '0'))
                    length_str = clean_cell(row.get('linelength', '0'))

                    if not lat_str or not lon_str or not length_str:
                        continue

                    lat = float(lat_str)
                    lon = float(lon_str)
                    length = float(length_str)
                    height = 0.0

                    azims = [
                        clean_cell(row.get('az-a')), 
                        clean_cell(row.get('az-b')), 
                        clean_cell(row.get('az-c')), 
                        clean_cell(row.get('az-d'))
                    ]

                    coord_text = f"{lat}, {lon}"
                    sectors_data = [{"azimuth": az} for az in azims]
                    self.add_site_to_history(site_name, option, coord_text, length, sector_width, is_sectorization, sectors_data)

                    fol = kml.newfolder(name=f"{site_name} {option}")
                    self.generate_site_kml(fol, site_name, option, lat, lon, height, length, azims, is_sectorization, sector_width)
                    count += 1

            if count == 0:
                raise ValueError("No valid data rows found in CSV.")

            self.save_history()
            self.populate_history_list()

            output_filename = self.get_output_filepath("imported_multi_sites.kml")
            kml.save(output_filename)

            self.open_kml_file(output_filename)

            QMessageBox.information(self, "Success", f"Imported {count} sites to history & created '{output_filename}'!")

        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SiteLayerCreator()
    window.show()
    sys.exit(app.exec())
