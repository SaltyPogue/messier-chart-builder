"""Caldwell Chart Builder: catalog data and file-name matching.

Everything else (the window, the chart, logs, framing, undo...) lives in chart_core.py,
which all seven apps share.
"""
import re

APP_NAME = "Caldwell Chart Builder"
CATALOG = "Caldwell"
FOLDER = "Caldwell Chart"                 # library folder in the user's home folder
CHART_FILE_NAME = "caldwell_chart.png"
ICON_ICO = "caldwell_icon.ico"             # Windows window icon
APP_ICON_PNG = "caldwell_icon.png"         # footer icon (in assets/)
DEFAULT_TITLE = "My Caldwell Chart"
OBJECTS = "objects"
COUNT = 109
COLS, ROWS = 10, 11
CELL_W, CELL_H = 320, 260
START_MAXIMIZED = False
EXAMPLES = ['C20.jpg', 'NGC 7000.jpg', 'Bubble Nebula.jpg']          # example file names shown in the help
SPARE_LINES = [('Caldwell Catalog', 'sans', 24, (110, 110, 130)), ('109 objects', 'sans', 22, (80, 80, 98))]           # text in the unused squares after the last object
DESCRIPTION = ("The Caldwell Catalogue: 109 bright deep-sky objects chosen by Sir Patrick Moore in 1995 as a companion to the Messier list, including many southern-sky targets that Messier never saw. It is named after Moore's full surname, Caldwell-Moore.")

# Caldwell catalog: number -> (designation, name or type)
CALDWELL = {
    1: ("NGC 188", "Open Cluster"), 2: ("NGC 40", "Bow-Tie Nebula"),
    3: ("NGC 4236", "Barred Spiral Galaxy"), 4: ("NGC 7023", "Iris Nebula"),
    5: ("IC 342", "Hidden Galaxy"), 6: ("NGC 6543", "Cat's Eye Nebula"),
    7: ("NGC 2403", "Spiral Galaxy"), 8: ("NGC 559", "Open Cluster"),
    9: ("Sh2-155", "Cave Nebula"), 10: ("NGC 663", "Open Cluster"),
    11: ("NGC 7635", "Bubble Nebula"), 12: ("NGC 6946", "Fireworks Galaxy"),
    13: ("NGC 457", "Owl (E.T.) Cluster"), 14: ("NGC 869 / 884", "Double Cluster"),
    15: ("NGC 6826", "Blinking Planetary"), 16: ("NGC 7243", "Open Cluster"),
    17: ("NGC 147", "Dwarf Spheroidal Galaxy"), 18: ("NGC 185", "Dwarf Spheroidal Galaxy"),
    19: ("IC 5146", "Cocoon Nebula"), 20: ("NGC 7000", "North America Nebula"),
    21: ("NGC 4449", "Irregular Galaxy"), 22: ("NGC 7662", "Blue Snowball Nebula"),
    23: ("NGC 891", "Silver Sliver Galaxy"), 24: ("NGC 1275", "Perseus A"),
    25: ("NGC 2419", "Intergalactic Wanderer"), 26: ("NGC 4244", "Silver Needle Galaxy"),
    27: ("NGC 6888", "Crescent Nebula"), 28: ("NGC 752", "Open Cluster"),
    29: ("NGC 5005", "Spiral Galaxy"), 30: ("NGC 7331", "Spiral Galaxy"),
    31: ("IC 405", "Flaming Star Nebula"), 32: ("NGC 4631", "Whale Galaxy"),
    33: ("NGC 6992", "Eastern Veil Nebula"), 34: ("NGC 6960", "Western Veil Nebula"),
    35: ("NGC 4889", "Coma B Galaxy"), 36: ("NGC 4559", "Spiral Galaxy"),
    37: ("NGC 6885", "Open Cluster"), 38: ("NGC 4565", "Needle Galaxy"),
    39: ("NGC 2392", "Eskimo Nebula"), 40: ("NGC 3626", "Lenticular Galaxy"),
    41: ("Melotte 25", "Hyades"), 42: ("NGC 7006", "Globular Cluster"),
    43: ("NGC 7814", "Little Sombrero Galaxy"), 44: ("NGC 7479", "Barred Spiral Galaxy"),
    45: ("NGC 5248", "Spiral Galaxy"), 46: ("NGC 2261", "Hubble's Variable Nebula"),
    47: ("NGC 6934", "Globular Cluster"), 48: ("NGC 2775", "Spiral Galaxy"),
    49: ("NGC 2237", "Rosette Nebula"), 50: ("NGC 2244", "Satellite Cluster"),
    51: ("IC 1613", "Dwarf Irregular Galaxy"), 52: ("NGC 4697", "Elliptical Galaxy"),
    53: ("NGC 3115", "Spindle Galaxy"), 54: ("NGC 2506", "Open Cluster"),
    55: ("NGC 7009", "Saturn Nebula"), 56: ("NGC 246", "Skull Nebula"),
    57: ("NGC 6822", "Barnard's Galaxy"), 58: ("NGC 2360", "Caroline's Cluster"),
    59: ("NGC 3242", "Ghost of Jupiter"), 60: ("NGC 4038", "Antennae Galaxies"),
    61: ("NGC 4039", "Antennae Galaxies"), 62: ("NGC 247", "Needle's Eye Galaxy"),
    63: ("NGC 7293", "Helix Nebula"), 64: ("NGC 2362", "Tau Canis Majoris Cluster"),
    65: ("NGC 253", "Sculptor Galaxy"), 66: ("NGC 5694", "Globular Cluster"),
    67: ("NGC 1097", "Barred Spiral Galaxy"), 68: ("NGC 6729", "R CrA Nebula"),
    69: ("NGC 6302", "Bug Nebula"), 70: ("NGC 300", "Spiral Galaxy"),
    71: ("NGC 2477", "Open Cluster"), 72: ("NGC 55", "String of Pearls Galaxy"),
    73: ("NGC 1851", "Globular Cluster"), 74: ("NGC 3132", "Southern Ring Nebula"),
    75: ("NGC 6124", "Open Cluster"), 76: ("NGC 6231", "Open Cluster"),
    77: ("NGC 5128", "Centaurus A"), 78: ("NGC 6541", "Globular Cluster"),
    79: ("NGC 3201", "Globular Cluster"), 80: ("NGC 5139", "Omega Centauri"),
    81: ("NGC 6352", "Globular Cluster"), 82: ("NGC 6193", "Open Cluster"),
    83: ("NGC 4945", "Spiral Galaxy"), 84: ("NGC 5286", "Globular Cluster"),
    85: ("IC 2391", "Omicron Velorum Cluster"), 86: ("NGC 6397", "Globular Cluster"),
    87: ("NGC 1261", "Globular Cluster"), 88: ("NGC 5823", "Open Cluster"),
    89: ("NGC 6087", "S Normae Cluster"), 90: ("NGC 2867", "Planetary Nebula"),
    91: ("NGC 3532", "Wishing Well Cluster"), 92: ("NGC 3372", "Eta Carinae Nebula"),
    93: ("NGC 6752", "Great Peacock Globular"), 94: ("NGC 4755", "Jewel Box"),
    95: ("NGC 6025", "Open Cluster"), 96: ("NGC 2516", "Southern Beehive Cluster"),
    97: ("NGC 3766", "Pearl Cluster"), 98: ("NGC 4609", "Open Cluster"),
    99: ("Coalsack", "Dark Nebula"), 100: ("IC 2944", "Lambda Centauri Nebula"),
    101: ("NGC 6744", "Spiral Galaxy"), 102: ("IC 2602", "Southern Pleiades"),
    103: ("NGC 2070", "Tarantula Nebula"), 104: ("NGC 362", "Globular Cluster"),
    105: ("NGC 4833", "Globular Cluster"), 106: ("NGC 104", "47 Tucanae"),
    107: ("NGC 6101", "Globular Cluster"), 108: ("NGC 4372", "Globular Cluster"),
    109: ("NGC 3195", "Planetary Nebula"),
}
NAMES = {n: (f"{d} · {t}" if not d.startswith(("Melotte", "Coalsack")) else t) for n, (d, t) in CALDWELL.items()}

# NGC / IC / Sh2 numbers that identify a Caldwell object, so "NGC 7000.jpg" works too
_ALIASES = {}
for _n, (_d, _t) in CALDWELL.items():
    for _m in re.finditer(r"(NGC|IC|Sh2)[\s-]*(\d+)", _d):
        _ALIASES[("Sh2" if _m.group(1).upper() == "SH2" else _m.group(1).upper(), int(_m.group(2)))] = _n
    for _m in re.finditer(r"/\s*(\d+)", _d):
        _ALIASES[("NGC", int(_m.group(1)))] = _n
_ALIASES[("NGC", 2238)] = _ALIASES[("NGC", 2239)] = _ALIASES[("NGC", 2246)] = 49   # Rosette parts
_ALIASES[("MEL", 25)] = 41


_CALDWELL_RE = re.compile(r"(?<![a-z0-9])(?:caldwell|c)[\s_\-.]*0*(\d{1,3})(?!\d)", re.I)
_CATNUM_RE = re.compile(r"(?<![a-z0-9])(ngc|ic|sh2|sh 2|mel|melotte)[\s_\-.]*0*(\d{1,4})(?!\d)", re.I)


def parse_number(name):
    """Return the Caldwell number found in a file name (C20, Caldwell 20, NGC 7000...), or None."""
    for m in _CALDWELL_RE.finditer(name):
        n = int(m.group(1))
        if 1 <= n <= COUNT:
            return n
    for m in _CATNUM_RE.finditer(name):
        cat = m.group(1).upper().replace(" ", "")
        cat = {"MELOTTE": "MEL", "SH2": "Sh2"}.get(cat, cat)
        cat = "Sh2" if cat.upper() == "SH2" else cat
        hit = _ALIASES.get((cat, int(m.group(2))))
        if hit:
            return hit
    if re.search(r"coal\s*sack", name, re.I):
        return 99
    if re.search(r"hyades", name, re.I):
        return 41
    return None

# Unified names used by the chart engine
LABEL = {n: f"C{n}" for n in range(1, COUNT + 1)}
SLUG = dict(LABEL)
SUB1 = {n: CALDWELL[n][0] for n in range(1, COUNT + 1)}
SUB2 = {n: CALDWELL[n][1] for n in range(1, COUNT + 1)}
INDEX = {n: n for n in range(1, COUNT + 1)}
NUMBER_WORD = "Caldwell number"
MATCH_NAMES = {n: [CALDWELL[n][1]] for n in range(1, COUNT + 1)}


def index_for_number(num):
    return INDEX.get(num)
