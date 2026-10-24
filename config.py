import os

HISTORY_FILE = "site_history.json"
BAND_SETTINGS_FILE = "band_sector_settings.json"

# الشعار المدمج بصيغة Base64
LOGO_B64 = (
    "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"
    "lGVIpqv3R0J2qN/f"
)

DEFAULT_BAND_SECTOR_SETTINGS = {
    "border": {"enabled": True, "color": "#ffffff"},
    "bands": {
        "Band 700": {"enabled": True, "length": 140.0, "width": 60.0, "transparency": 50, "color": "#00e5ff"},
        "Band 1800": {"enabled": True, "length": 170.0, "width": 60.0, "transparency": 50, "color": "#ffeb3b"},
        "Band 2600": {"enabled": True, "length": 100.0, "width": 60.0, "transparency": 50, "color": "#ff5252"},
        "C-Band": {"enabled": True, "length": 300.0, "width": 60.0, "transparency": 50, "color": "#000000"}
    },
    "sectors": {
        "S1": {"use_custom": False, "length": 120.0, "width": 60.0, "transparency": 50, "color": "#00e5ff"},
        "S2": {"use_custom": False, "length": 120.0, "width": 60.0, "transparency": 50, "color": "#ffeb3b"},
        "S3": {"use_custom": False, "length": 120.0, "width": 60.0, "transparency": 50, "color": "#ff5252"},
        "S4": {"use_custom": False, "length": 120.0, "width": 60.0, "transparency": 50, "color": "#69f0ae"}
    }
}

SIMPLE_TEMPLATE_COLS = ["site name", "lat", "long", "az-a", "az-b", "az-c", "az-d"]

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