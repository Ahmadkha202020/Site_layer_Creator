import base64
import math

def decode_base64_safely(b64_input):
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

def calculate_destination(lat, lon, bearing, distance):
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