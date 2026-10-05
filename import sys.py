import sys
import math
import json
import os
import csv
import simplekml
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QCheckBox, QGridLayout, 
                             QListWidget, QMessageBox, QFrame, QFileDialog)
from PyQt6.QtCore import Qt

HISTORY_FILE = "site_history.json"

class SiteLayerCreator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("one site design layer")
        self.setGeometry(100, 100, 1150, 750)
        self.setStyleSheet(self.get_stylesheet())
        
        self.history_data = self.load_history()
        
        self.init_ui()
        self.populate_history_list()

    def init_ui(self):
        main_h_layout = QHBoxLayout()
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

        btn_delete_history = QPushButton("Clear All History")
        btn_delete_history.setObjectName("DeleteBtn")
        btn_delete_history.clicked.connect(self.clear_history)
        left_panel.addWidget(btn_delete_history)

        # ==========================================
        # 2. Right Panel: Input Form
        # ==========================================
        right_panel = QVBoxLayout()

        title = QLabel("one site design layer")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("Title")
        right_panel.addWidget(title)

        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(2, 1)
        form_layout.setColumnStretch(3, 1)
        form_layout.setColumnStretch(4, 1)

        # --- Row 1: Site Name ---
        lbl_name = QLabel("Site Name / Option")
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Site Name")
        
        self.input_option = QLineEdit()
        self.input_option.setPlaceholderText("Option")
        self.input_option.setFixedWidth(150)

        form_layout.addWidget(lbl_name, 0, 0)
        form_layout.addWidget(self.input_name, 0, 1, 1, 3)
        form_layout.addWidget(self.input_option, 0, 4)

        # --- Row 2: Lat, Long ---
        lbl_coords = QLabel("Latitude, Longitude")
        self.input_coords = QLineEdit()
        self.input_coords.setPlaceholderText("Lat, Long")
        
        form_layout.addWidget(lbl_coords, 1, 0)
        form_layout.addWidget(self.input_coords, 1, 1, 1, 4)

        # --- Row 3: Line Length & Sector Width ---
        lbl_length = QLabel("Line Length (m)")
        self.input_length = QLineEdit()
        
        self.lbl_width = QLabel("Sector Width °")
        self.input_width = QLineEdit()
        self.input_width.setPlaceholderText("60") 
        self.input_width.setText("60")            
        
        form_layout.addWidget(lbl_length, 2, 0)
        form_layout.addWidget(self.input_length, 2, 1)
        form_layout.addWidget(self.lbl_width, 2, 3)
        form_layout.addWidget(self.input_width, 2, 4)

        # --- Spacer Row ---
        form_layout.addWidget(QLabel(""), 3, 0) 

        # --- Row 4: Sector Headers ---
        headers = ["", "S1", "S2", "S3", "S4"]
        for i, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold;")
            form_layout.addWidget(lbl, 4, i)

        # --- Row 5: Azimuth ---
        lbl_azimuth = QLabel("Azimuth °")
        form_layout.addWidget(lbl_azimuth, 5, 0)
        
        self.az_inputs = []
        for i in range(4):
            inp = QLineEdit()
            self.az_inputs.append(inp)
            form_layout.addWidget(inp, 5, i + 1)

        # --- Row 6: Color ---
        lbl_color = QLabel("Color (Outline)")
        form_layout.addWidget(lbl_color, 6, 0)
        
        self.color_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setText("white") 
            inp.setStyleSheet("background-color: white; color: black;") 
            self.color_inputs.append(inp)
            form_layout.addWidget(inp, 6, i + 1)

        right_panel.addLayout(form_layout)

        # --- Sectorization Checkbox ---
        self.chk_sectorization = QCheckBox("Use Sectorization")
        self.chk_sectorization.setChecked(True) 
        self.chk_sectorization.stateChanged.connect(self.toggle_sector_width) 
        right_panel.addWidget(self.chk_sectorization)

        # ==========================================
        # 3. Control Buttons Layout
        # ==========================================
        
        btn_layout_row1 = QHBoxLayout()
        
        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.clicked.connect(self.save_to_history)
        
        self.btn_template = QPushButton("Export Template (CSV)")
        self.btn_template.setObjectName("TemplateBtn")
        self.btn_template.clicked.connect(self.export_template)
        
        btn_layout_row1.addWidget(self.btn_save, 1)
        btn_layout_row1.addWidget(self.btn_template, 1)
        
        right_panel.addLayout(btn_layout_row1)

        btn_layout_row2 = QHBoxLayout()
        
        self.btn_import = QPushButton("Import from Item (CSV)")
        self.btn_import.setObjectName("ImportBtn")
        self.btn_import.clicked.connect(self.import_multi_sites)
        
        self.btn_create = QPushButton("Create and Open Layer")
        self.btn_create.setObjectName("CreateBtn")
        self.btn_create.clicked.connect(self.create_kml)
        
        btn_layout_row2.addWidget(self.btn_import, 1)
        btn_layout_row2.addWidget(self.btn_create, 1)
        
        right_panel.addLayout(btn_layout_row2)

        main_h_layout.addLayout(left_panel, 1)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #555;")
        main_h_layout.addWidget(line)
        
        main_h_layout.addLayout(right_panel, 4)

        self.setLayout(main_h_layout)
        self.toggle_sector_width()

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
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QLabel#Title {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QLineEdit {
                background-color: #3c3f41;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                color: white;
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
            QPushButton#CreateBtn {
                background-color: #008000;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                margin-top: 5px;
            }
            QPushButton#CreateBtn:hover {
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
                margin-top: 10px;
            }
            QPushButton#SaveBtn:hover {
                background-color: #0078d4;
            }
            QPushButton#TemplateBtn {
                background-color: #6a0dad;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                margin-top: 10px;
            }
            QPushButton#TemplateBtn:hover {
                background-color: #8000ff;
            }
            QPushButton#ImportBtn {
                background-color: #d83b01;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                margin-top: 5px;
            }
            QPushButton#ImportBtn:hover {
                background-color: #ea4a1f;
            }
            QPushButton#DeleteBtn {
                background-color: #8b0000;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin-top: 5px;
            }
            QPushButton#DeleteBtn:hover {
                background-color: #a00000;
            }
            QCheckBox {
                spacing: 10px;
                margin-top: 10px;
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

    # --- History Functions ---
    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
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
                color_val = sectors[i].get("color", "white")
                self.color_inputs[i].setText(color_val)
                self.color_inputs[i].setStyleSheet(f"background-color: {color_val}; color: black;")
            else:
                self.az_inputs[i].clear()
                self.color_inputs[i].setText("white")
                self.color_inputs[i].setStyleSheet("background-color: white; color: black;")

    def clear_history(self):
        reply = QMessageBox.question(self, 'Confirm', 'Are you sure you want to clear all history?', 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.history_data = {}
            self.save_history()
            self.populate_history_list()
            QMessageBox.information(self, "Success", "History cleared successfully.")

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
            except:
                raise ValueError("Coordinate format invalid. Use 'Lat, Long'.")

            sectors_data = []
            for i in range(4):
                sectors_data.append({
                    "azimuth": self.az_inputs[i].text(),
                    "color": self.color_inputs[i].text() or "white"
                })

            self.history_data[site_name] = {
                "site_name": site_name,
                "option_name": option_name,
                "coords": coord_text,
                "length": self.input_length.text(),
                "width": self.input_width.text(),
                "sectorization": self.chk_sectorization.isChecked(),
                "sectors": sectors_data
            }
            
            self.save_history()
            self.populate_history_list()
            
            if show_message:
                QMessageBox.information(self, "Saved", f"Site '{site_name}' saved to history successfully.")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    # --- Export Template Function ---
    def export_template(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV Template", "site_template.csv", "CSV Files (*.csv)")
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Exact columns requested by user
                writer.writerow(["site name", "option", "lat", "long", "az-a", "az-b", "az-c", "az-d", "line length"])
                
                # Example rows demonstrating the "-" and " " neglect feature
                writer.writerow(["Site_Alpha", "A", "30.0444", "31.2357", "0", "90", "-", " ", "1000"])
                writer.writerow(["Site_Beta", "B", "30.0555", "31.2444", "45", "135", "225", "315", "1500"])
                
            QMessageBox.information(self, "Success", "Template exported successfully!\n\nNote: Cells containing '-' or ' ' (space) will be ignored during import.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    # --- Math & KML Functions ---
    def calculate_destination(self, lat, lon, bearing, distance):
        R = 6371000
        lat1 = math.radians(lat)
        lon1 = math.radians(lon)
        bearing = math.radians(bearing)

        lat2 = math.asin(math.sin(lat1) * math.cos(distance/R) + 
                         math.cos(lat1) * math.sin(distance/R) * math.cos(bearing))
        
        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(distance/R) * math.cos(lat1),
                                 math.cos(distance/R) - math.sin(lat1) * math.sin(lat2))

        return math.degrees(lat2), math.degrees(lon2)

    def get_kml_color(self, color_name):
        color_map = {
            "red": "ff0000ff", "green": "ff00ff00", "blue": "ffff0000",
            "yellow": "ff00ffff", "white": "ffffffff", "black": "ff000000",
            "cyan": "ffffff00", "magenta": "ffff00ff", "orange": "ff0080ff"
        }
        return color_map.get(color_name.lower(), "ffffffff")

    def generate_site_kml(self, fol, site_name, option_name, lat, lon, height, length, azims, colors, is_sectorization, sector_width):
        for i in range(4):
            az_text = str(azims[i]).strip() if i < len(azims) and azims[i] is not None else ""
            color_text = str(colors[i]).strip() if i < len(colors) and colors[i] is not None else "white"
            
            # Neglect if azimuth is empty, "-", or " "
            if not az_text or az_text == "-" or az_text == " ":
                continue

            try:
                azimuth = float(az_text)
            except:
                continue

            kml_outline_color = self.get_kml_color(color_text)
            
            if is_sectorization:
                pol = fol.newpolygon(name=f"S{i+1} Az:{azimuth}")
                start_bearing = azimuth - (sector_width / 2)
                end_bearing = azimuth + (sector_width / 2)
                
                arc_coords = []
                steps = int(sector_width / 5) + 1 
                bearing_step = sector_width / (steps - 1) if steps > 1 else 0
                
                for step in range(steps):
                    current_bearing = start_bearing + (step * bearing_step)
                    dest_lat, dest_lon = self.calculate_destination(lat, lon, current_bearing, length)
                    arc_coords.append((dest_lon, dest_lat, height))
                
                pol.outerboundaryis = [(lon, lat, height)] + arc_coords + [(lon, lat, height)]
                
                # USER REQUEST: Sector color #ffffff and opacity 30%
                # KML color format: aabbggrr. White = ffffff. 30% opacity = 4D.
                # So the fill color is "4Dffffff"
                pol.style.polystyle.color = "4Dffffff"
                pol.style.polystyle.fill = 1
                pol.style.polystyle.outline = 1
                
                # Outline uses the color from the color input
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

    def create_kml(self):
        try:
            self.save_to_history(show_message=False)
            
            site_name = self.input_name.text() or "Site"
            option_name = self.input_option.text()
            
            lat_str, lon_str = self.input_coords.text().split(',')
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())

            length = float(self.input_length.text())
            sector_width = float(self.input_width.text()) if self.input_width.text() else 60.0
            is_sectorization = self.chk_sectorization.isChecked()

            kml = simplekml.Kml()
            fol = kml.newfolder(name=f"{site_name} {option_name}")

            azims = [inp.text() for inp in self.az_inputs]
            colors = [inp.text() or "white" for inp in self.color_inputs]

            self.generate_site_kml(fol, site_name, option_name, lat, lon, 0.0, length, azims, colors, is_sectorization, sector_width)

            output_filename = f"{site_name}_design.kml"
            kml.save(output_filename)
            
            if sys.platform == 'win32':
                os.startfile(output_filename)
            elif sys.platform == 'darwin':
                os.system(f'open "{output_filename}"')
            else:
                os.system(f'xdg-open "{output_filename}"')

            QMessageBox.information(self, "Success", f"Layer created successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # --- Import Multi-Sites Function ---
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
                if val == "-" or val == "":
                    return ""
                return val

            with open(file_path, 'r', encoding='utf-8-sig') as f: 
                reader = csv.DictReader(f)
                
                reader.fieldnames = [name.strip().lower().replace(" ", "") for name in reader.fieldnames]
                
                # Updated required columns (height removed as per user request)
                required_cols = ['sitename', 'option', 'lat', 'long', 'az-a', 'az-b', 'az-c', 'az-d', 'linelength']
                for col in required_cols:
                    if col not in reader.fieldnames:
                        if col == 'sitename' and 'sitename/option' in reader.fieldnames:
                            continue
                        raise ValueError(f"Missing required column: '{col}'. Please ensure your CSV has columns: site name, option, lat, long, az-a, az-b, az-c, az-d, line length")

                count = 0
                for row in reader:
                    site_name = clean_cell(row.get('sitename', row.get('sitename/option', 'Unnamed')))
                    option = clean_cell(row.get('option', ''))
                    
                    lat_str = clean_cell(row.get('lat', '0'))
                    lon_str = clean_cell(row.get('long', '0'))
                    length_str = clean_cell(row.get('linelength', '0'))
                    
                    # If critical values are empty, skip the row
                    if not lat_str or not lon_str or not length_str:
                        continue
                        
                    lat = float(lat_str)
                    lon = float(lon_str)
                    length = float(length_str)
                    height = 0.0  # Default height since it's not in the import list
                    
                    azims = [
                        clean_cell(row.get('az-a')), 
                        clean_cell(row.get('az-b')), 
                        clean_cell(row.get('az-c')), 
                        clean_cell(row.get('az-d'))
                    ]
                    
                    colors = ["white", "white", "white", "white"]
                    
                    fol = kml.newfolder(name=f"{site_name} {option}")
                    
                    self.generate_site_kml(fol, site_name, option, lat, lon, height, length, azims, colors, is_sectorization, sector_width)
                    count += 1

            if count == 0:
                raise ValueError("No valid data rows found in the CSV file.")

            output_filename = "imported_multi_sites.kml"
            kml.save(output_filename)
            
            if sys.platform == 'win32':
                os.startfile(output_filename)
            elif sys.platform == 'darwin':
                os.system(f'open "{output_filename}"')
            else:
                os.system(f'xdg-open "{output_filename}"')

            QMessageBox.information(self, "Success", f"Successfully imported {count} sites and created {output_filename}!")

        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SiteLayerCreator()
    window.show()
    sys.exit(app.exec())