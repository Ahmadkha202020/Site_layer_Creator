# GIS Layer Creator

GIS Layer Creator is a Python-based desktop application designed for creating accurate KML layers for telecom, GIS, and site-planning projects. It allows users to generate site markers, sector polygons, azimuth lines, and multi-band layer overlays for use in Google Earth, QGIS, ArcGIS Earth, and web-based map visualization.

The application is built to simplify field planning and RF design workflows by converting geographic site data and azimuth values into structured KML output. It is especially useful for telecom operators, RF engineers, GIS specialists, and project teams who need to visualize site coverage, antenna sectors, and location-based network planning data quickly and consistently.

## Features

- One-site mode for creating a single site design
- Multi-sites mode for importing CSV or Excel files
- KML generation for:
  - Pin markers
  - Sector polygons
  - Azimuth lines
  - Combined pin + sector + line output
- Multi-band layer support for:
  - Band 700
  - Band 1800
  - Band 2600
  - C-Band
- Custom sector and border configuration
- Adjustable sector length, beamwidth, transparency, and color
- Optional band and sector customization through a dedicated settings dialog
- Simple CSV and Excel template export
- Custom template generation with selected fields and grouped categories
- Import of filled templates and automatic mapping of columns
- Automatic site history saving and loading
- 2D interactive map preview
- Direct KML opening in Google Earth, QGIS, or ArcGIS Earth
- Dark mode and always-on-top options
- Help and support dialogs for guided use

## Main Functionalities

### 1. One Site Mode
This mode allows the user to create a single site layout manually by entering:
- Site name
- Option name
- Latitude and longitude
- Default length and width
- Four sector azimuth values

The app then calculates sector geometry and generates KML layers based on the selected output type:
- Pin Only
- Sectorized Only
- Lines
- Both

### 2. Multi Sites Mode
This mode allows bulk generation from a CSV or Excel file. The app reads each row, extracts required site information, and creates a multi-site KML file.

The program supports:
- Basic template export
- Customized template export
- Import of filled templates
- Data mapping for site name, latitude, longitude, azimuths, length, width, and additional RF attributes

### 3. Band and Sector Customization
The app includes a band customization panel where the user can:
- enable or disable band layers
- set length, beamwidth, transparency, and color
- adjust border visibility and border color
- define per-sector custom settings for S1 to S4

This makes it possible to generate visually distinct sectors and frequency bands for different project requirements.

### 4. KML Layer Generation
The core of the application is the generation of KML features based on:
- site coordinates
- sector azimuths
- distance and width values
- band configuration
- transparency and color settings

The app creates:
- point markers
- polygon sectors
- line segments representing the azimuth direction

Each feature includes a popup description with site information and custom metadata.

### 5. 2D Map Viewer
The app can render generated site data in a 2D map using Leaflet and a satellite/base-map source. This allows users to preview the created site layers before saving or publishing the KML.

### 6. History Management
The app automatically saves site entries to a local JSON file so users can:
- revisit previous site designs
- load them into the app
- remove entries
- export history to CSV or Excel

### 7. Output and Opening
Once the KML is created, the user can:
- save it to a chosen output folder
- open it directly in Google Earth, QGIS, or ArcGIS Earth
- preview it in the built-in 2D map viewer

## How It Works

The application follows a structured workflow:

1. The user chooses either One Site Mode or Multi Sites Mode.
2. In One Site Mode, the user enters the site coordinates and sector azimuths.
3. In Multi Sites Mode, the user imports a CSV or Excel file that contains site data.
4. The app validates the input and cleans the values.
5. It reads the band and sector customization settings, including colors and transparency.
6. The app computes sector geometry using latitude/longitude and directional calculations.
7. It creates KML features such as markers, polygon sectors, and azimuth lines.
8. Each feature receives a popup description with site metadata and custom attributes.
9. The user saves the final KML file or previews it in the map viewer.
10. The file can be opened directly in a GIS viewer for further use.

## Technical Overview

The app relies on:
- Python
- PyQt6 for the desktop interface
- simplekml for KML generation
- CSV and Excel support for template import/export
- JSON for site history storage
- custom geospatial calculations for directional geometry
- Leaflet-based browser map rendering for the 2D preview

## Core Logic in the Code

The main code contains several essential functions responsible for the application behavior, including:

- `generate_site_kml()` – creates KML content for one site
- `build_site_map_feature()` – prepares map data for 2D display
- `parse_multi_sites_file()` – reads and validates CSV/XLSX site imports
- `create_single_kml()` – generates a single-site KML file
- `create_multi_sites_kml()` – generates a multi-site KML file
- `calculate_destination()` – computes the end point of a sector based on bearing and distance
- `get_active_bands_for_site()` – determines active bands for the site
- `get_sector_parameters()` – returns sector length, width, transparency, and color
- `save_to_history()` and `load_from_history()` – manage saved site history
- `export_simple_template_csv()` and `export_simple_template_excel()` – create starter templates
- `open_kml_file()` – launches the exported file in a selected viewer
- `build_one_site_page()` and `build_multi_sites_page()` – create the main user interfaces
- `show_history_popup()` and `show_about_dialog()` – provide additional app actions

## Summary

GIS Layer Creator is a practical and powerful tool for generating KML maps for telecom and GIS workflows. It brings together data entry, site geometry calculation, multi-band customization, template import/export, map preview, and KML output in one desktop application. It is especially useful for teams that need to produce organized, visually structured site layers quickly and efficiently.
