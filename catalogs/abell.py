"""Abell Chart Builder: catalog data and file-name matching.

Everything else (the window, the chart, logs, framing, undo...) lives in chart_core.py,
which all seven apps share.
"""
import re

APP_NAME = "Abell Chart Builder"
CATALOG = "Abell"
FOLDER = "Abell Chart"                 # library folder in the user's home folder
CHART_FILE_NAME = "abell_chart.png"
ICON_ICO = "abell_icon.ico"             # Windows window icon
APP_ICON_PNG = "abell_icon.png"         # footer icon (in assets/)
DEFAULT_TITLE = "My Abell Chart"
OBJECTS = "planetary nebulae"
COUNT = 86
COLS, ROWS = 10, 9
CELL_W, CELL_H = 320, 260
START_MAXIMIZED = True
EXAMPLES = ['Abell 21.jpg', 'A39.png', 'NGC 6742.jpg']          # example file names shown in the help
SPARE_LINES = [('Abell Catalog', 'title', 54, (120, 120, 140)), ('86 planetary nebulae  ·  Abell 1 to Abell 86', 'sans', 28, (95, 95, 115))]           # text in the unused squares after the last object
DESCRIPTION = ('The Abell Catalog of Planetary Nebulae: 86 faint planetary nebulae found by George Abell on the Palomar Observatory Sky Survey plates and published in 1966. Later study showed that four of them (Abell 11, 32, 76 and 85) are not planetary nebulae.')

# Abell Catalog of Planetary Nebulae (1966): Abell 1 to Abell 86.
ABELL_NAMES = {
    21: "Medusa Nebula", 31: "Sh2-290", 33: "Diamond Ring", 35: "Sh2-313",
    37: "IC 972", 50: "NGC 6742", 75: "NGC 7076", 81: "IC 1454",
}
ABELL_NOTES = {
    11: "Not a PN (reflection nebula)", 32: "Not a PN (plate flaw)",
    76: "Not a PN (ring galaxy)", 85: "Not a PN (SNR CTB 1)",
}
IDS = [None] + list(range(1, 87))               # square number -> Abell number
LABEL = {i: f"Abell {i}" for i in range(1, 87)}
SLUG = {i: f"Abell{i}" for i in range(1, 87)}
NAMES = {i: ABELL_NAMES.get(i) or ABELL_NOTES.get(i) or "Planetary nebula" for i in range(1, 87)}
SUB1 = {i: ABELL_NAMES.get(i) or ABELL_NOTES.get(i, "") for i in range(1, 87)}
SUB2 = {i: ABELL_NOTES.get(i, "") if i in ABELL_NAMES else "" for i in range(1, 87)}
INDEX = {i: i for i in range(1, 87)}
NUMBER_WORD = "Abell number"

# Other designations of Abell planetaries, so "NGC 6742.jpg" or "Sh2-274.jpg" work too
_ALIASES = {("NGC", 6742): 50, ("NGC", 7076): 75, ("IC", 972): 37, ("IC", 1454): 81,
            ("SH2", 274): 21, ("SH2", 290): 31, ("SH2", 313): 35}
_ABELL_RE = re.compile(r"(?<![a-z0-9])(?:pn[\s_\-.]*)?a(?:bell)?[\s_\-.]*(?:66[\s_\-.]+)?0*(\d{1,2})(?!\d)", re.I)
_CAT_RE = re.compile(r"(?<![a-z0-9])(ngc|ic|sh[\s_\-.]*2)[\s_\-.]*0*(\d{1,4})(?!\d)", re.I)


def index_for_number(num):
    return INDEX.get(num)


def parse_number(name):
    """Return the square for a file name such as 'Abell 21.jpg', 'A39.png', 'PN A66 31' or 'NGC 6742', or None."""
    for m in _ABELL_RE.finditer(name):
        hit = INDEX.get(int(m.group(1)))
        if hit:
            return hit
    for m in _CAT_RE.finditer(name):
        cat = re.sub(r"[\s_\-.]", "", m.group(1)).upper()
        hit = _ALIASES.get((cat, int(m.group(2))))
        if hit:
            return hit
    if re.search(r"medusa", name, re.I):
        return 21
    return None
