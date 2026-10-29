"""Sharpless Chart Builder: catalog data and file-name matching.

Everything else (the window, the chart, logs, framing, undo...) lives in chart_core.py,
which all seven apps share.
"""
import re

APP_NAME = "Sharpless Chart Builder"
CATALOG = "Sharpless"
FOLDER = "Sharpless Chart"                 # library folder in the user's home folder
CHART_FILE_NAME = "sharpless_chart.png"
ICON_ICO = "sharpless_icon.ico"             # Windows window icon
APP_ICON_PNG = "sharpless_icon.png"         # footer icon (in assets/)
DEFAULT_TITLE = "My Sharpless Chart"
OBJECTS = "nebulae"
COUNT = 313
COLS, ROWS = 20, 16
CELL_W, CELL_H = 256, 208
START_MAXIMIZED = True
EXAMPLES = ['Sh2-155.jpg', 'NGC 7000.jpg', 'Heart Nebula.jpg']          # example file names shown in the help
SPARE_LINES = [('Sharpless Catalog', 'title', 54, (120, 120, 140)), ('313 nebulae  ·  Sh2-1 to Sh2-313', 'sans', 28, (95, 95, 115))]           # text in the unused squares after the last object
DESCRIPTION = ('The Sharpless Catalogue: 313 H II regions - glowing clouds of hydrogen gas - catalogued by the American astronomer Stewart Sharpless in 1959 from the photographic plates of the Palomar Observatory Sky Survey.')

# Sharpless (Sh2) catalog: common names for the better-known objects.
# Objects not listed here are labelled with their Sh2 number only.
SH2_NAMES = {
    1: "", 3: "RCW 120", 6: "Bug Nebula", 8: "Cat's Paw Nebula", 9: "Gum 65",
    10: "RCW 130", 11: "War and Peace Nebula", 25: "Lagoon Nebula", 29: "NGC 6559",
    30: "Trifid Nebula", 34: "Forgotten Nebula", 37: "Twiddlebug Nebula",
    45: "Omega Nebula", 49: "Eagle Nebula", 64: "W 40", 68: "Flaming Skull Nebula",
    80: "M1-67", 82: "Little Cocoon Nebula", 86: "NGC 6820", 92: "SNR G65.3+5.7",
    101: "Tulip Nebula", 103: "Veil Nebula (Cygnus Loop)", 105: "Crescent Nebula",
    106: "Celestial Snow Angel", 108: "Sadr Region", 114: "Flying Dragon Nebula",
    117: "North America Nebula", 119: "Clamshell Nebula", 125: "Cocoon Nebula",
    129: "Flying Bat Nebula", 131: "Elephant's Trunk Nebula", 132: "Lion Nebula",
    136: "Ghost Nebula", 142: "Wizard Nebula", 155: "Cave Nebula",
    157: "Lobster Claw Nebula", 158: "NGC 7538", 162: "Bubble Nebula",
    170: "Little Rosette Nebula", 171: "NGC 7822", 173: "Phantom of the Opera",
    184: "Pacman Nebula", 188: "Dolphin Nebula (Simeis 22)", 190: "Heart Nebula",
    191: "Maffei 1", 197: "Maffei 2", 199: "Soul Nebula", 211: "Tribble Nebula",
    212: "Tribble Nebula (NGC 1624)", 220: "California Nebula", 222: "NGC 1579",
    229: "Flaming Star Nebula", 234: "Spider Nebula", 236: "Tadpoles Nebula",
    237: "Fly Nebula (NGC 1931)", 238: "Hind's Variable Nebula",
    240: "Spaghetti Nebula (Simeis 147)", 244: "Crab Nebula", 248: "Jellyfish Nebula",
    252: "Monkey Head Nebula", 261: "Lower's Nebula", 264: "Lambda Orionis Ring",
    273: "Cone Nebula region", 274: "Medusa Nebula", 275: "Rosette Nebula",
    276: "Barnard's Loop", 277: "Flame Nebula", 279: "Running Man Nebula",
    281: "Orion Nebula", 290: "Abell 31", 292: "Seagull Nebula", 298: "Thor's Helmet",
    302: "RCW 7", 308: "Dolphin Head Nebula", 311: "Skull and Crossbones Nebula",
    313: "Abell 35",
}
SH2_NAMES = {k: v for k, v in SH2_NAMES.items() if v}
NAMES = {n: SH2_NAMES.get(n, f"Sharpless {n}") for n in range(1, 314)}

# Other catalog numbers that identify a Sharpless object, so "NGC 7000.jpg" or "M42.jpg" works too
_ALIASES = {
    ("NGC", 6302): 6, ("NGC", 6334): 8, ("NGC", 6357): 11, ("M", 8): 25, ("NGC", 6523): 25,
    ("NGC", 6559): 29, ("M", 20): 30, ("NGC", 6514): 30, ("M", 17): 45, ("NGC", 6618): 45,
    ("M", 16): 49, ("NGC", 6611): 49, ("NGC", 6820): 86, ("NGC", 6888): 105,
    ("NGC", 7000): 117, ("IC", 5146): 125, ("IC", 1396): 131, ("NGC", 7380): 142,
    ("NGC", 7538): 158, ("NGC", 7635): 162, ("NGC", 7822): 171, ("NGC", 281): 184,
    ("IC", 1805): 190, ("IC", 1848): 199, ("NGC", 1624): 212, ("NGC", 1499): 220,
    ("NGC", 1579): 222, ("IC", 405): 229, ("IC", 417): 234, ("IC", 410): 236,
    ("NGC", 1931): 237, ("NGC", 1555): 238, ("M", 1): 244, ("NGC", 1952): 244,
    ("IC", 443): 248, ("NGC", 2174): 252, ("NGC", 2175): 252, ("NGC", 2264): 273,
    ("NGC", 2237): 275, ("NGC", 2238): 275, ("NGC", 2239): 275, ("NGC", 2244): 275,
    ("NGC", 2246): 275, ("NGC", 2024): 277, ("NGC", 1977): 279, ("NGC", 1973): 279,
    ("NGC", 1975): 279, ("M", 42): 281, ("NGC", 1976): 281, ("IC", 2177): 292,
    ("NGC", 2359): 298, ("NGC", 2467): 311,
}

_SH_PATTERNS = [
    re.compile(r"(?<![a-z0-9])sh(?:arpless)?[\s_\-.]*2[\s_\-.]+0*(\d{1,3})(?!\d)", re.I),   # Sh2-155, Sh 2-155
    re.compile(r"(?<![a-z0-9])sharpless[\s_\-.]*0*(\d{1,3})(?!\d)", re.I),                   # Sharpless 155
    re.compile(r"(?<![a-z0-9])sh[\s_\-.]*0*(\d{1,3})(?!\d)(?![\s_\-.]+\d)", re.I),         # Sh155, Sh-155
]
_CATNUM_RE = re.compile(r"(?<![a-z0-9])(ngc|ic|messier|m)[\s_\-.]*0*(\d{1,4})(?!\d)", re.I)


def parse_number(name):
    """Return the Sharpless number found in a file name (Sh2-155, Sharpless 155, NGC 7000...), or None."""
    for pat in _SH_PATTERNS:
        for m in pat.finditer(name):
            n = int(m.group(1))
            if 1 <= n <= COUNT:
                return n
    for m in _CATNUM_RE.finditer(name):
        cat = m.group(1).upper()
        cat = "M" if cat == "MESSIER" else cat
        hit = _ALIASES.get((cat, int(m.group(2))))
        if hit:
            return hit
    return None

# Unified names used by the chart engine
LABEL = {n: f"Sh2-{n}" for n in range(1, COUNT + 1)}
SLUG = dict(LABEL)
SUB1 = {n: SH2_NAMES.get(n, "") for n in range(1, COUNT + 1)}
SUB2 = {n: "" for n in range(1, COUNT + 1)}
INDEX = {n: n for n in range(1, COUNT + 1)}
NUMBER_WORD = "Sharpless number"
MATCH_NAMES = {n: [SH2_NAMES[n]] for n in SH2_NAMES}


def index_for_number(num):
    return INDEX.get(num)
