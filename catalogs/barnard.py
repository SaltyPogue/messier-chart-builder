"""Barnard Chart Builder: catalog data and file-name matching.

Everything else (the window, the chart, logs, framing, undo...) lives in chart_core.py,
which all seven apps share.
"""
import re

APP_NAME = "Barnard Chart Builder"
CATALOG = "Barnard"
FOLDER = "Barnard Chart"                 # library folder in the user's home folder
CHART_FILE_NAME = "barnard_chart.png"
ICON_ICO = "barnard_icon.ico"             # Windows window icon
APP_ICON_PNG = "barnard_icon.png"         # footer icon (in assets/)
DEFAULT_TITLE = "My Barnard Chart"
OBJECTS = "dark nebulae"
COUNT = 345
COLS, ROWS = 20, 18
CELL_W, CELL_H = 256, 208
START_MAXIMIZED = True
EXAMPLES = ['B33.jpg', 'Barnard 72.png', 'Horsehead.jpg']          # example file names shown in the help
SPARE_LINES = [('Barnard Catalog', 'title', 54, (120, 120, 140)), ('345 dark nebulae  ·  B1-B175 and B201-B370', 'sans', 28, (95, 95, 115)), ('(numbers 176-200 were never used)', 'sans', 22, (80, 80, 98))]           # text in the unused squares after the last object
DESCRIPTION = ('The Barnard Catalogue: dark nebulae - clouds of dust seen in silhouette against the Milky Way - photographed by the American astronomer Edward Emerson Barnard. His 1927 catalogue numbers them B1 to B175 and B201 to B370.')

# Barnard's dark nebulae (1927 catalogue). Numbers run 1-175 and 201-370;
# 176-200 were never used.
B_NUMBERS = list(range(1, 176)) + list(range(201, 371))
B_NAMES = {
    33: "Horsehead Nebula", 59: "Pipe Nebula (stem)", 68: "Bok globule",
    72: "Snake Nebula", 78: "Pipe Nebula (bowl)", 86: "Ink Spot Nebula",
    87: "Parrot's Head Nebula", 142: "Barnard's E", 143: "Barnard's E",
    150: "Seahorse Nebula", 168: "Cocoon Nebula dark lane",
}
IDS = [None] + B_NUMBERS                        # square number -> Barnard number
LABEL = {i: f"B{IDS[i]}" for i in range(1, len(IDS))}
SLUG = {i: f"B{IDS[i]}" for i in range(1, len(IDS))}
NAMES = {i: B_NAMES.get(IDS[i], "Dark nebula") for i in range(1, len(IDS))}
SUB1 = {i: B_NAMES.get(IDS[i], "") for i in range(1, len(IDS))}
SUB2 = {i: "" for i in range(1, len(IDS))}
INDEX = {b: i for i, b in enumerate(IDS) if b}
NUMBER_WORD = "Barnard number"

_KEYWORDS = [("horse ?head", 33), ("snake", 72), ("ink ?spot", 86), ("parrot", 87),
             ("sea ?horse", 150), ("barnard'?s ?e(?![a-z])", 142), ("pipe", 78)]
_B_RE = re.compile(r"(?<![a-z0-9])(?:barnard|b)[\s_\-.]*0*(\d{1,3})(?!\d)", re.I)
_IC434_RE = re.compile(r"(?<![a-z0-9])ic[\s_\-.]*434(?!\d)", re.I)


def index_for_number(num):
    return INDEX.get(num)


def parse_number(name):
    """Return the square for a file name such as 'B33.jpg', 'Barnard 72.png' or 'Horsehead.tif', or None."""
    for m in _B_RE.finditer(name):
        hit = INDEX.get(int(m.group(1)))
        if hit:
            return hit
    if _IC434_RE.search(name):
        return INDEX[33]
    for pattern, b in _KEYWORDS:
        if re.search(pattern, name, re.I):
            return INDEX[b]
    return None
