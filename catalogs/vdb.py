"""vdB Chart Builder: catalog data and file-name matching.

Everything else (the window, the chart, logs, framing, undo...) lives in chart_core.py,
which all seven apps share.
"""
import re

APP_NAME = "vdB Chart Builder"
CATALOG = "van den Bergh"
FOLDER = "vdB Chart"                 # library folder in the user's home folder
CHART_FILE_NAME = "vdb_chart.png"
ICON_ICO = "vdb_icon.ico"             # Windows window icon
APP_ICON_PNG = "vdb_icon.png"         # footer icon (in assets/)
DEFAULT_TITLE = "My van den Bergh Chart"
OBJECTS = "reflection nebulae"
COUNT = 158
COLS, ROWS = 16, 10
CELL_W, CELL_H = 256, 208
START_MAXIMIZED = True
EXAMPLES = ['vdB 139.jpg', 'NGC 7023.jpg', 'Iris.jpg']          # example file names shown in the help
SPARE_LINES = [('van den Bergh', 'title', 48, (120, 120, 140)), ('158 reflection nebulae', 'sans', 26, (95, 95, 115))]           # text in the unused squares after the last object
DESCRIPTION = ('The van den Bergh Catalogue: 158 reflection nebulae - clouds of dust lit by nearby stars, glowing blue or golden - catalogued by the Canadian astronomer Sidney van den Bergh in 1966 from the plates of the Palomar Observatory Sky Survey.')

# van den Bergh catalogue of reflection nebulae (1966): vdB 1 to vdB 158.
VDB_NAMES = {
    1: "LBN 578", 4: "LBN 604", 5: "Gamma Cassiopeiae", 17: "Embryo Nebula (NGC 1333)", 19: "IC 348",
    20: "Electra (Pleiades)", 21: "Maia Nebula (Pleiades)", 22: "Merope Nebula (Pleiades)",
    23: "Alcyone (Pleiades)", 24: "LDN 1442", 27: "RY Tauri", 28: "Hind's Variable Nebula",
    31: "AB Aurigae", 33: "NGC 1788", 34: "Flaming Star Nebula", 36: "Witch Head Nebula",
    38: "Raspberry Nebula (Sh2-263)", 46: "NGC 1999", 59: "M78", 60: "M78",
    62: "Boogeyman Nebula (LDN 1622)", 63: "LDN 1622", 65: "LDN 1557",
    67: "Angel Nebula (NGC 2170)", 68: "Angel Nebula (NGC 2170)", 69: "Angel Nebula (NGC 2170)",
    72: "Angel Nebula (NGC 2170)", 75: "12 Geminorum", 81: "IC 448", 82: "NGC 2247", 85: "NGC 2282",
    88: "Seagull Nebula region", 90: "Seagull Nebula region", 93: "Seagull Nebula (IC 2177)",
    94: "Seagull Nebula region", 96: "Sh2-310", 99: "Pi Scorpii", 100: "Blue Horsehead (IC 4592)",
    104: "Sigma Scorpii (Sh2-9)", 105: "IC 4603", 106: "IC 4604", 108: "IC 4605", 114: "Sh2-38",
    115: "IC 4684", 118: "NGC 6589", 119: "NGC 6590", 124: "IC 1287", 126: "LBN 134",
    131: "NGC 6914B", 132: "NGC 6914A", 133: "44 Cygni", 134: "Omega-1 Cygni", 137: "IC 5076",
    139: "Iris Nebula (NGC 7023)", 141: "Ghost Nebula (Sh2-136)", 142: "Elephant's Trunk (IC 1396)",
    146: "NGC 7129", 147: "Cocoon Nebula (IC 5146)", 149: "Dark Shark (LDN 1235)",
    150: "Dark Shark (LDN 1235)", 152: "Barnard 175", 155: "LDN 1216", 158: "LBN 534",
}
IDS = [None] + list(range(1, 159))              # square number -> vdB number
LABEL = {i: f"vdB {i}" for i in range(1, 159)}
SLUG = {i: f"vdB{i}" for i in range(1, 159)}
NAMES = {i: VDB_NAMES.get(i, "Reflection nebula") for i in range(1, 159)}
SUB1 = {i: VDB_NAMES.get(i, "") for i in range(1, 159)}
SUB2 = {i: "" for i in range(1, 159)}
INDEX = {i: i for i in range(1, 159)}
NUMBER_WORD = "vdB number"

# Other designations of vdB objects, so "NGC 7023.jpg" or "IC 2118.jpg" work too
_ALIASES = {
    ("NGC", 1333): 17, ("IC", 348): 19, ("NGC", 1555): 28, ("NGC", 1788): 33, ("IC", 405): 34,
    ("IC", 2118): 36, ("NGC", 1909): 36, ("SH2", 263): 38, ("NGC", 1999): 46, ("M", 78): 59,
    ("NGC", 2068): 59, ("LDN", 1622): 62, ("NGC", 2170): 67, ("IC", 448): 81, ("NGC", 2247): 82,
    ("NGC", 2282): 85, ("IC", 2177): 93, ("SH2", 310): 96, ("IC", 4592): 100, ("SH2", 9): 104,
    ("SH2", 38): 114, ("IC", 4603): 105, ("IC", 4604): 106, ("IC", 4605): 108, ("IC", 4684): 115,
    ("NGC", 6589): 118, ("NGC", 6590): 119, ("IC", 1287): 124, ("NGC", 6914): 132, ("IC", 5076): 137,
    ("NGC", 7023): 139, ("SH2", 136): 141, ("IC", 1396): 142, ("NGC", 7129): 146, ("IC", 5146): 147,
    ("SH2", 125): 147, ("LDN", 1235): 149, ("B", 175): 152,
}
_KEYWORDS = [("iris", 139), ("witch", 36), ("ghost", 141), ("cocoon", 147), ("flaming ?star", 34),
             ("merope", 22), ("maia", 21), ("electra", 20), ("alcyone", 23), ("embryo", 17),
             ("angel", 67), ("seagull", 93), ("raspberry", 38), ("boog(ie|ey) ?man", 62),
             ("blue ?horse", 100), ("elephant", 142), ("dark ?shark", 149), ("hind", 28)]
_VDB_RE = re.compile(r"(?<![a-z0-9])(?:vdb|van[\s_\-.]*den[\s_\-.]*bergh)[\s_\-.]*0*(\d{1,3})(?!\d)", re.I)
_CAT_RE = re.compile(r"(?<![a-z0-9])(ngc|ic|ldn|messier|m|barnard|b|sh[\s_\-.]*2)[\s_\-.]*0*(\d{1,4})(?!\d)", re.I)


def index_for_number(num):
    return INDEX.get(num)


def parse_number(name):
    """Return the square for a file name such as 'vdB 139.jpg', 'vdb142.png', 'NGC 7023' or 'Iris.tif', or None."""
    for m in _VDB_RE.finditer(name):
        hit = INDEX.get(int(m.group(1)))
        if hit:
            return hit
    for m in _CAT_RE.finditer(name):
        cat = re.sub(r"[\s_\-.]", "", m.group(1)).upper()
        cat = {"MESSIER": "M", "BARNARD": "B"}.get(cat, cat)
        hit = _ALIASES.get((cat, int(m.group(2))))
        if hit:
            return hit
    for pattern, n in _KEYWORDS:
        if re.search(pattern, name, re.I):
            return n
    return None
