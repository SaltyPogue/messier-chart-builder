"""Messier Chart Builder: catalog data and file-name matching.

Everything else (the window, the chart, logs, framing, undo...) lives in chart_core.py,
which all seven apps share.
"""
import re

APP_NAME = "Messier Chart Builder"
CATALOG = "Messier"
FOLDER = "Messier Chart"                 # library folder in the user's home folder
CHART_FILE_NAME = "messier_chart.png"
ICON_ICO = "icon.ico"             # Windows window icon
APP_ICON_PNG = "messier_icon.png"         # footer icon (in assets/)
DEFAULT_TITLE = "My Messier Chart"
OBJECTS = "objects"
COUNT = 110
COLS, ROWS = 10, 11
CELL_W, CELL_H = 320, 260
START_MAXIMIZED = False
EXAMPLES = ['M31.jpg', 'Messier 81.png', 'Andromeda Galaxy.jpg']          # example file names shown in the help
SPARE_LINES = []           # text in the unused squares after the last object
DESCRIPTION = ('The Messier Catalogue: 110 nebulae, star clusters and galaxies compiled by the French astronomer Charles Messier between 1771 and 1781, so that comet hunters would not mistake them for comets. M104 to M110 were added from his notes by later astronomers.')

NAMES = {
    1: "Crab Nebula", 2: "Globular Cluster", 3: "Globular Cluster",
    4: "Globular Cluster", 5: "Globular Cluster", 6: "Butterfly Cluster",
    7: "Ptolemy Cluster", 8: "Lagoon Nebula", 9: "Globular Cluster",
    10: "Globular Cluster", 11: "Wild Duck Cluster", 12: "Globular Cluster",
    13: "Hercules Cluster", 14: "Globular Cluster", 15: "Globular Cluster",
    16: "Eagle Nebula", 17: "Omega Nebula", 18: "Open Cluster",
    19: "Globular Cluster", 20: "Trifid Nebula", 21: "Open Cluster",
    22: "Sagittarius Cluster", 23: "Open Cluster", 24: "Sagittarius Star Cloud",
    25: "Open Cluster", 26: "Open Cluster", 27: "Dumbbell Nebula",
    28: "Globular Cluster", 29: "Cooling Tower Cluster", 30: "Globular Cluster",
    31: "Andromeda Galaxy", 32: "Elliptical Galaxy", 33: "Triangulum Galaxy",
    34: "Open Cluster", 35: "Open Cluster", 36: "Pinwheel Cluster",
    37: "Open Cluster", 38: "Starfish Cluster", 39: "Open Cluster",
    40: "Winnecke 4 (double star)", 41: "Open Cluster", 42: "Orion Nebula",
    43: "De Mairan's Nebula", 44: "Beehive Cluster", 45: "Pleiades",
    46: "Open Cluster", 47: "Open Cluster", 48: "Open Cluster",
    49: "Elliptical Galaxy", 50: "Open Cluster", 51: "Whirlpool Galaxy",
    52: "Open Cluster", 53: "Globular Cluster", 54: "Globular Cluster",
    55: "Globular Cluster", 56: "Globular Cluster", 57: "Ring Nebula",
    58: "Barred Spiral Galaxy", 59: "Elliptical Galaxy", 60: "Elliptical Galaxy",
    61: "Spiral Galaxy", 62: "Globular Cluster", 63: "Sunflower Galaxy",
    64: "Black Eye Galaxy", 65: "Leo Triplet Galaxy", 66: "Leo Triplet Galaxy",
    67: "Open Cluster", 68: "Globular Cluster", 69: "Globular Cluster",
    70: "Globular Cluster", 71: "Globular Cluster", 72: "Globular Cluster",
    73: "Asterism", 74: "Phantom Galaxy", 75: "Globular Cluster",
    76: "Little Dumbbell Nebula", 77: "Cetus A", 78: "Reflection Nebula",
    79: "Globular Cluster", 80: "Globular Cluster", 81: "Bode's Galaxy",
    82: "Cigar Galaxy", 83: "Southern Pinwheel Galaxy", 84: "Lenticular Galaxy",
    85: "Lenticular Galaxy", 86: "Lenticular Galaxy", 87: "Virgo A",
    88: "Spiral Galaxy", 89: "Elliptical Galaxy", 90: "Spiral Galaxy",
    91: "Barred Spiral Galaxy", 92: "Globular Cluster", 93: "Open Cluster",
    94: "Cat's Eye Galaxy", 95: "Barred Spiral Galaxy", 96: "Spiral Galaxy",
    97: "Owl Nebula", 98: "Spiral Galaxy", 99: "Coma Pinwheel Galaxy",
    100: "Spiral Galaxy", 101: "Pinwheel Galaxy", 102: "Spindle Galaxy",
    103: "Open Cluster", 104: "Sombrero Galaxy", 105: "Elliptical Galaxy",
    106: "Spiral Galaxy", 107: "Globular Cluster", 108: "Surfboard Galaxy",
    109: "Barred Spiral Galaxy", 110: "Elliptical Galaxy",
}

_MESSIER_RE = re.compile(r"(?<![a-z0-9])(?:messier|m)[\s_\-.]*0*(\d{1,3})(?!\d)", re.I)


def parse_messier(name):
    """Return the Messier number found in a file name, or None."""
    for m in _MESSIER_RE.finditer(name):
        n = int(m.group(1))
        if 1 <= n <= 110:
            return n
    return None

# Unified names used by the chart engine
LABEL = {n: f"M{n}" for n in range(1, COUNT + 1)}
SLUG = dict(LABEL)
SUB1 = dict(NAMES)
SUB2 = {n: "" for n in range(1, COUNT + 1)}
INDEX = {n: n for n in range(1, COUNT + 1)}
NUMBER_WORD = "Messier number"

# NGC / IC numbers of every Messier object, so "NGC 224.jpg" goes to M31
MESSIER_NGC = {
    1: 1952, 2: 7089, 3: 5272, 4: 6121, 5: 5904, 6: 6405, 7: 6475, 8: 6523, 9: 6333, 10: 6254,
    11: 6705, 12: 6218, 13: 6205, 14: 6402, 15: 7078, 16: 6611, 17: 6618, 18: 6613, 19: 6273, 20: 6514,
    21: 6531, 22: 6656, 23: 6494, 26: 6694, 27: 6853, 28: 6626, 29: 6913, 30: 7099,
    31: 224, 32: 221, 33: 598, 34: 1039, 35: 2168, 36: 1960, 37: 2099, 38: 1912, 39: 7092,
    41: 2287, 42: 1976, 43: 1982, 44: 2632, 46: 2437, 47: 2422, 48: 2548, 49: 4472, 50: 2323,
    51: 5194, 52: 7654, 53: 5024, 54: 6715, 55: 6809, 56: 6779, 57: 6720, 58: 4579, 59: 4621, 60: 4649,
    61: 4303, 62: 6266, 63: 5055, 64: 4826, 65: 3623, 66: 3627, 67: 2682, 68: 4590, 69: 6637, 70: 6681,
    71: 6838, 72: 6981, 73: 6994, 74: 628, 75: 6864, 76: 651, 77: 1068, 78: 2068, 79: 1904, 80: 6093,
    81: 3031, 82: 3034, 83: 5236, 84: 4374, 85: 4382, 86: 4406, 87: 4486, 88: 4501, 89: 4552, 90: 4569,
    91: 4548, 92: 6341, 93: 2447, 94: 4736, 95: 3351, 96: 3368, 97: 3587, 98: 4192, 99: 4254, 100: 4321,
    101: 5457, 102: 5866, 103: 581, 104: 4594, 105: 3379, 106: 4258, 107: 6171, 108: 3556, 109: 3992, 110: 205,
}
_NGC_TO_M = {ngc: m for m, ngc in MESSIER_NGC.items()}
_NGC_TO_M[650] = 76
_IC_TO_M = {4715: 24, 4725: 25}
_MEL_TO_M = {22: 45}
_CAT_RE = re.compile(r"(?<![a-z0-9])(ngc|ic|mel|melotte)[\s_\-.]*0*(\d{1,4})(?!\d)", re.I)

# Extra names people use in file names (the names on the chart are matched automatically)
EXTRA_NAMES = {
    "pinwheel": 101, "praesepe": 44, "seven sisters": 45, "subaru": 45, "swan nebula": 17,
    "horseshoe nebula": 17, "checkmark nebula": 17, "evil eye": 64, "great orion nebula": 42,
    "great hercules cluster": 13, "omega centauri": None, "jewel box": None, "leo triplet": None,
    "markarian": None, "running man": None, "kemble": None, "silver dollar": None,
    "great andromeda": 31, "southern pinwheel": 83, "phantom": 74, "virgo a": 87,
}
# (None = a different object with a similar name, so it is not matched by mistake)


def index_for_number(num):
    return INDEX.get(num)


def parse_number(name):
    """Messier number from a file name: M31, Messier 31, m_031, or the NGC / IC number (NGC 224)."""
    hit = parse_messier(name)
    if hit:
        return hit
    for m in _CAT_RE.finditer(name):
        cat, num = m.group(1).lower(), int(m.group(2))
        table = _NGC_TO_M if cat == "ngc" else _IC_TO_M if cat == "ic" else _MEL_TO_M
        if num in table:
            return table[num]
    return None
