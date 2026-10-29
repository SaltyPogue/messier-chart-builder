#!/usr/bin/env python3
"""
SaltyPogue Chart Builders - shared engine
=========================================
Created by SaltyPogue  ·  www.saltypogue.com

All seven apps (Messier, Caldwell, Sharpless, Herschel, Barnard, Abell, vdB) run on
this one file. Each app's catalog data and file-name matching live in catalogs/<name>.py,
and each app's start file (messier_chart.py etc.) is three lines that pick a catalog.

  * Drag photos onto the window. Files whose name contains the object's number
    (M31.jpg) or its name (Andromeda Galaxy.jpg) go to the right square automatically.
    You can drop many files, or a whole folder.
  * Click a square to choose a photo for it. Right-click for more: adjust the framing,
    add a log / notes, open the original or remove it.
  * Undo puts back photos you removed, replaced or cleared.
  * The chart is re-saved automatically after every change.

Your photos are copied into the app's library folder; your originals are never changed.

Requirements:  pip install pillow tkinterdnd2 numpy tifffile
"""

import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

try:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps, ImageTk
except ImportError:
    print("This program needs Pillow. Install it with:  pip install pillow tkinterdnd2")
    sys.exit(1)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except Exception:
    HAS_DND = False

Image.MAX_IMAGE_PIXELS = None  # large mosaics are fine

APP_VERSION = "1.2"            # keep in step with the VERSION file
AUTHOR = "SaltyPogue"
WEBSITE = "www.saltypogue.com"
WEBSITE_URL = "https://www.saltypogue.com"
SOCIAL_LINKS = [
    (WEBSITE, WEBSITE_URL),
    ("Instagram", "https://www.instagram.com/saltypogue"),
    ("Facebook", "https://www.facebook.com/saltypogue"),
    ("X (Twitter)", "https://x.com/saltypogue"),
]
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".gif"}
GAP = 5                         # white grid lines
TITLE_H = 240
BORDER = 400                    # star border width
HOVER_SIZE = 300
WORK_SIZE = 3000                # photos are read at up to this size for tiles and framing
MAX_ZOOM = 8.0

# Filled in by configure() from the catalog file
CAT = None
APP_NAME = CATALOG = ""
COUNT = COLS = ROWS = CELL_W = CELL_H = 0
LABEL = SLUG = NAMES = SUB1 = SUB2 = {}
LIBRARY = ORIG_DIR = CELL_DIR = UNDO_DIR = SETTINGS_FILE = CHART_FILE = None
CHART_W = CHART_H = FOOTER_H = 0
BIG_CELLS = False


def configure(cat):
    """Set up the engine for one catalog (a module from the catalogs package)."""
    global CAT, APP_NAME, CATALOG, COUNT, COLS, ROWS, CELL_W, CELL_H, LABEL, SLUG, NAMES, SUB1, SUB2
    global LIBRARY, ORIG_DIR, CELL_DIR, UNDO_DIR, SETTINGS_FILE, CHART_FILE, CHART_W, CHART_H, FOOTER_H
    global BIG_CELLS
    CAT = cat
    APP_NAME, CATALOG, COUNT = cat.APP_NAME, cat.CATALOG, cat.COUNT
    COLS, ROWS, CELL_W, CELL_H = cat.COLS, cat.ROWS, cat.CELL_W, cat.CELL_H
    LABEL, SLUG, NAMES, SUB1, SUB2 = cat.LABEL, cat.SLUG, cat.NAMES, cat.SUB1, cat.SUB2
    BIG_CELLS = CELL_W >= 300
    LIBRARY = Path.home() / cat.FOLDER
    ORIG_DIR = LIBRARY / "originals"
    CELL_DIR = LIBRARY / "cells"
    UNDO_DIR = LIBRARY / ".undo"
    SETTINGS_FILE = LIBRARY / "settings.json"
    CHART_FILE = LIBRARY / cat.CHART_FILE_NAME
    CHART_W = COLS * CELL_W + (COLS + 1) * GAP
    FOOTER_H = max(170, CHART_W * 2 // 45)   # strip under the grid with a short description
    CHART_H = TITLE_H + ROWS * CELL_H + (ROWS + 1) * GAP + FOOTER_H
    _NAME_INDEX.clear()


def resource(name):
    """Path to a file bundled with the app (works in the .exe / .app and as a script)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    for p in (base / name, base / "assets" / name):
        if p.exists():
            return p
    return base / name


# --------------------------------------------------------------------------
# Matching file names to objects: catalog numbers first, then names
# --------------------------------------------------------------------------
_GENERIC = set("""open globular cluster clusters spiral barred elliptical lenticular galaxy galaxies
nebula nebulae dark reflection planetary irregular dwarf spheroidal asterism star stars
bok globule region not a pn snr the of and emission supernova remnant h ii cloud object plate
flaw ring-galaxy intergalactic""".split())
_NAME_INDEX = []      # [(normalised name, square)], longest first


def _norm(text):
    text = text.lower().replace("'", "").replace("’", "")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def _build_name_index():
    raw = {}
    sources = getattr(CAT, "MATCH_NAMES", None) or {n: [NAMES[n], SUB1.get(n, ""), SUB2.get(n, "")]
                                                    for n in range(1, COUNT + 1)}
    for n, names in sources.items():
        for name in names:
            if not name:
                continue
            parts = [re.sub(r"\(.*?\)", "", name)] + re.findall(r"\((.*?)\)", name)
            for part in parts:
                key = _norm(part.split("·")[-1])
                if not key or re.search(r"\d", key):
                    continue
                words = key.split()
                if all(w in _GENERIC for w in words):
                    continue
                raw.setdefault(key, set()).add(n)
                core = list(words)
                while core and core[-1] in _GENERIC:
                    core.pop()
                core = " ".join(core)
                if core and core != key and len(core) >= 4:
                    raw.setdefault(core, set()).add(n)
    index = {k: next(iter(v)) for k, v in raw.items() if len(v) == 1}
    for k, v in getattr(CAT, "EXTRA_NAMES", {}).items():
        index[_norm(k)] = v
    _NAME_INDEX[:] = sorted(index.items(), key=lambda kv: -len(kv[0]))


def match_name(stem):
    """Square for a file name that contains an object's name ('Andromeda Galaxy final'), or None."""
    if not _NAME_INDEX:
        _build_name_index()
    text = f" {_norm(stem)} "
    squashed = text.replace(" ", "")
    for key, n in _NAME_INDEX:
        if f" {key} " in text:
            return n            # None here means "a different object with a similar name"
        if " " in key and len(key) >= 8 and key.replace(" ", "") in squashed:
            return n
    return None


def find_square(stem):
    """Which square a file belongs to, from its name. Returns (square or None, how)."""
    n = CAT.parse_number(stem)
    if n:
        return n, "number"
    n = match_name(stem)
    return (n, "name") if n else (None, None)


# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------
_font_cache = {}
_FONT_NAMES = {
    "title": ["georgiaz.ttf", "Georgia Bold Italic.ttf", "georgiai.ttf",
              "Georgia Italic.ttf", "timesbi.ttf", "Times New Roman Bold Italic.ttf",
              "DejaVuSerif-BoldItalic.ttf", "LiberationSerif-BoldItalic.ttf"],
    "sans": ["arial.ttf", "Arial.ttf", "Helvetica.ttc", "DejaVuSans.ttf",
             "LiberationSans-Regular.ttf"],
    "bold": ["arialbd.ttf", "Arial Bold.ttf", "HelveticaNeue.ttc",
             "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
}


def font(kind, size):
    key = (kind, size)
    if key not in _font_cache:
        f = None
        for name in _FONT_NAMES[kind]:
            try:
                f = ImageFont.truetype(name, size)
                break
            except OSError:
                continue
        if f is None:
            try:
                f = ImageFont.load_default(size=size)
            except TypeError:
                f = ImageFont.load_default()
        _font_cache[key] = f
    return _font_cache[key]


# --------------------------------------------------------------------------
# Reading photos: 8-bit, 16-bit and 32-bit, stretched automatically if still linear
# --------------------------------------------------------------------------
class PhotoError(Exception):
    pass


def _array_to_rgb(arr):
    """Any numpy image (grey or colour, integer or float) -> (8-bit RGB PIL image, was_stretched)."""
    import numpy as np
    arr = np.asarray(arr)
    if arr.ndim == 3 and arr.shape[0] in (1, 3, 4) and arr.shape[-1] not in (1, 3, 4):
        arr = np.moveaxis(arr, 0, -1)                     # planar (channels first) -> channels last
    if arr.ndim == 3:
        arr = arr[..., :3] if arr.shape[-1] >= 3 else arr[..., 0]
    if arr.ndim != 2 and arr.ndim != 3:
        raise PhotoError("unsupported image layout")
    step = max(1, math.ceil(max(arr.shape[:2]) / WORK_SIZE))
    if step > 1:
        arr = arr[::step, ::step]
    kind = arr.dtype.kind
    x = arr.astype(np.float32)
    x[~np.isfinite(x)] = 0
    top = float(x.max()) if x.size else 1.0
    if kind == "f":
        hi = 1.0 if top <= 1.0 else (255.0 if top <= 255 else (65535.0 if top <= 65535 else top))
    elif arr.dtype.itemsize == 1:
        hi = 255.0
    elif arr.dtype.itemsize == 2:
        hi = 65535.0
    else:
        hi = top if top > 0 else 1.0
    x = np.clip(x / hi, 0.0, 1.0)
    x, stretched = auto_stretch(x, strict=(kind != "f" and arr.dtype.itemsize == 1))
    out = (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)
    im = Image.fromarray(out, "L" if out.ndim == 2 else "RGB")
    return im.convert("RGB"), stretched


def auto_stretch(x, strict=False):
    """A stack straight out of stacking software is "linear": almost black. Stretch it so it shows.

    x is a 0-1 float array. 8-bit pictures (strict=True) must be much darker before
    they are touched, so finished, processed photos are never changed.
    """
    import numpy as np
    lum = x if x.ndim == 2 else x.mean(axis=2)
    sample = lum[::4, ::4].ravel()
    if not sample.size:
        return x, False
    med = float(np.median(sample))
    bright = float(np.percentile(sample, 99.5))
    limit_med, limit_bright = (0.035, 0.24) if strict else (0.02, 0.3)
    if med < limit_med and bright < limit_bright:
        mad = float(np.median(np.abs(sample - med))) * 1.4826
        black = max(0.0, med - 2.8 * mad)
        x = np.clip((x - black) / max(1e-6, 1.0 - black), 0.0, 1.0)
        m0 = max(1e-6, (med - black) / max(1e-6, 1.0 - black))
        t = 0.22                                            # target background level
        m = m0 * (t - 1) / (2 * t * m0 - t - m0)            # midtones balance that maps m0 -> t
        x = ((m - 1) * x) / ((2 * m - 1) * x - m)
        return x, True
    return x, False


def _tiff_is_high_bit(im):
    try:
        bits = im.tag_v2.get(258)
        bits = bits if isinstance(bits, (tuple, list)) else (bits,)
        return any(b and b > 8 for b in bits)
    except Exception:
        return False


def _read_tiff_array(path):
    import tifffile
    try:
        return tifffile.imread(str(path))
    except Exception as ex:
        if "imagecodecs" in str(ex) or "LZW" in str(ex).upper():
            raise PhotoError("this 32-bit TIFF uses LZW compression, which isn't supported. "
                             "Save it again without compression (or as a 16-bit TIFF).")
        raise PhotoError(f"couldn't read this TIFF ({ex})")


def open_photo(path, max_size=WORK_SIZE):
    """Open any supported photo as 8-bit RGB, at most about max_size pixels across.

    Returns (image, stretched). Handles 16-bit and 32-bit (float) TIFFs from Siril,
    PixInsight, APP etc., and brightens images that are still linear.
    """
    path = Path(path)
    try:
        im = Image.open(path)
    except Exception:
        im = None
    if im is None:
        if path.suffix.lower() not in (".tif", ".tiff"):
            raise PhotoError("this file isn't a picture this app can read")
        return _array_to_rgb(_read_tiff_array(path))     # e.g. 32-bit colour TIFFs
    if im.format == "TIFF" and im.mode == "RGB" and _tiff_is_high_bit(im):
        try:                       # 16-bit colour: read at full depth so linear stacks can be stretched
            arr = _read_tiff_array(path)
            im.close()
            return _array_to_rgb(arr)
        except Exception:
            pass                   # fall back to Pillow's 8-bit version
    with im:
        if im.format == "JPEG":
            im.draft("RGB", (max_size, max_size))           # fast decode of big JPEGs
        try:
            im = ImageOps.exif_transpose(im)
        except Exception:
            pass
        if im.mode in ("F", "I") or im.mode.startswith("I;16"):
            import numpy as np
            return _array_to_rgb(np.asarray(im))
        if im.mode in ("RGBA", "LA", "PA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
            im = Image.alpha_composite(bg, im)
        im = im.convert("RGB")
        factor = max(im.size) // max_size
        if factor >= 2:
            im = im.reduce(factor)
        im.load()
    return _stretch_if_dark_8bit(im)


def _stretch_if_dark_8bit(im):
    """8-bit pictures are only stretched if nearly the whole picture is black (an unstretched stack)."""
    small = im.copy()
    small.thumbnail((400, 400))
    hist = small.convert("L").histogram()
    total = sum(hist)
    acc, med, p995 = 0, None, 255
    for v, c in enumerate(hist):
        acc += c
        if med is None and acc >= total * 0.5:
            med = v
        if acc >= total * 0.995:
            p995 = v
            break
    if med is None or med > 8 or p995 > 60:
        return im, False
    import numpy as np
    x, stretched = auto_stretch(np.asarray(im, dtype=np.float32) / 255.0, strict=True)
    if not stretched:
        return im, False
    return Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB"), True


def to_rgb(im):
    """Convert a Pillow image (8-bit, 16-bit, float or transparent) to 8-bit RGB."""
    if im.mode == "RGB":
        return im
    if im.mode in ("F", "I") or im.mode.startswith("I;16"):
        import numpy as np
        return _array_to_rgb(np.asarray(im))[0]
    if im.mode in ("RGBA", "LA", "PA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB")


# --------------------------------------------------------------------------
# Framing (crop) of a photo into its square
# --------------------------------------------------------------------------
DEFAULT_CROP = (0.5, 0.5, 1.0)        # centre x, centre y (0-1 of the photo), zoom


def fit_zoom(w, h):
    """Zoom at which the whole photo fits inside the square (the furthest you can zoom out)."""
    aspect = CELL_W / CELL_H
    base_w = min(w, h * aspect)
    return base_w / max(w, h * aspect)


def crop_box(w, h, crop):
    """Pixel box (may reach outside the photo) for a crop of a w x h photo."""
    cx, cy, z = crop
    aspect = CELL_W / CELL_H
    z = max(fit_zoom(w, h), min(MAX_ZOOM, z))
    bw = min(w, h * aspect) / z
    bh = bw / aspect
    x = cx * w
    y = cy * h
    x = min(max(x, bw / 2), w - bw / 2) if bw <= w else w / 2
    y = min(max(y, bh / 2), h - bh / 2) if bh <= h else h / 2
    return (x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2), (x / w, y / h, z)


def make_tile(im, crop=DEFAULT_CROP, size=None):
    size = size or (CELL_W, CELL_H)
    (x0, y0, x1, y1), _ = crop_box(im.width, im.height, crop)
    box = (round(x0), round(y0), max(round(x0) + 1, round(x1)), max(round(y0) + 1, round(y1)))
    return im.crop(box).resize(size, Image.LANCZOS)    # areas outside the photo come out black


# --------------------------------------------------------------------------
# Library files
# --------------------------------------------------------------------------
def cell_path(n):
    return CELL_DIR / f"{SLUG[n]}.png"


def crop_path(n):
    return CELL_DIR / f"{SLUG[n]}.crop.json"


def originals_for(n):
    return [p for p in ORIG_DIR.glob(f"{SLUG[n]}.*")
            if p.is_file() and p.suffix.lower() in IMAGE_EXT]


def read_crop(n):
    try:
        c = json.loads(crop_path(n).read_text(encoding="utf-8"))
        return float(c[0]), float(c[1]), float(c[2])
    except Exception:
        return DEFAULT_CROP


class Undo:
    """One level of undo: files an action replaced or removed are parked in .undo and can be put back."""

    def __init__(self):
        self.label = None
        self.moved = []        # (parked copy, original location)
        self.created = []      # files the action made
        shutil.rmtree(UNDO_DIR, ignore_errors=True)

    def begin(self, label):
        shutil.rmtree(UNDO_DIR, ignore_errors=True)
        UNDO_DIR.mkdir(parents=True, exist_ok=True)
        self.label, self.moved, self.created = label, [], []

    def park(self, path):
        path = Path(path)
        if not path.exists():
            return
        UNDO_DIR.mkdir(parents=True, exist_ok=True)
        dest = UNDO_DIR / f"{len(self.moved)}_{path.name}"
        shutil.move(str(path), str(dest))
        self.moved.append((dest, path))

    def made(self, path):
        self.created.append(Path(path))

    @property
    def available(self):
        return bool(self.label and (self.moved or self.created))

    def undo(self):
        for p in self.created:
            if p.exists() and not any(p == orig for _, orig in self.moved):
                p.unlink()
        for dest, orig in reversed(self.moved):
            orig.parent.mkdir(parents=True, exist_ok=True)
            if orig.exists():
                orig.unlink()
            shutil.move(str(dest), str(orig))
        label = self.label
        self.label, self.moved, self.created = None, [], []
        shutil.rmtree(UNDO_DIR, ignore_errors=True)
        _tile_cache.clear()
        _hover_cache.clear()
        return label


def import_photo(src, n, undo):
    """Copy the photo into the library and make its chart tile. Returns True if it was stretched."""
    src = Path(src)
    im, stretched = open_photo(src)          # fails here, before anything is changed
    tile = make_tile(im)
    dest = ORIG_DIR / f"{SLUG[n]}{src.suffix.lower()}"
    same = dest.exists() and src.resolve() == dest.resolve()
    undo.park(cell_path(n))
    undo.park(crop_path(n))
    if not same:
        for old in originals_for(n):
            undo.park(old)
    tile.save(cell_path(n))
    undo.made(cell_path(n))
    if not same:
        shutil.copy2(src, dest)
        undo.made(dest)
    return stretched


def remove_photo(n, undo):
    undo.park(cell_path(n))
    undo.park(crop_path(n))
    for p in originals_for(n):
        undo.park(p)


_hover_cache = {}


def hover_image(n):
    """The whole photo for object n, fitted inside a HOVER_SIZE x HOVER_SIZE square."""
    origs = originals_for(n)
    src = origs[0] if origs else cell_path(n)
    if not src.exists():
        return None
    key = (str(src), src.stat().st_mtime)
    hit = _hover_cache.get(n)
    if hit and hit[0] == key:
        return hit[1]
    try:
        im, _ = open_photo(src, HOVER_SIZE * 2)
        im.thumbnail((HOVER_SIZE, HOVER_SIZE), Image.LANCZOS)
    except Exception:
        return None
    sq = Image.new("RGB", (HOVER_SIZE, HOVER_SIZE), (0, 0, 0))
    sq.paste(im, ((HOVER_SIZE - im.width) // 2, (HOVER_SIZE - im.height) // 2))
    _hover_cache[n] = (key, sq)
    return sq


_tile_cache = {}


def load_tile(n):
    p = cell_path(n)
    if not p.exists():
        _tile_cache.pop(n, None)
        return None
    mtime = p.stat().st_mtime
    hit = _tile_cache.get(n)
    if hit and hit[0] == mtime:
        return hit[1]
    with Image.open(p) as im:
        tile = to_rgb(im)
        if tile.size != (CELL_W, CELL_H):
            tile = ImageOps.fit(tile, (CELL_W, CELL_H), Image.LANCZOS)
        tile.load()
    _tile_cache[n] = (mtime, tile)
    return tile


def filled():
    return [n for n in range(1, COUNT + 1) if cell_path(n).exists()]


# --------------------------------------------------------------------------
# The chart image
# --------------------------------------------------------------------------
def cell_rect(n):
    """Pixel rectangle of object n in the full-size chart."""
    r, c = divmod(n - 1, COLS)
    x = GAP + c * (CELL_W + GAP)
    y = TITLE_H + GAP + r * (CELL_H + GAP)
    return x, y, x + CELL_W, y + CELL_H


def _fit_size(d, text, kind, size, width, smallest=11):
    while size > smallest and d.textlength(text, font=font(kind, size)) > width:
        size -= 1
    return size


def draw_description(d):
    """Write the catalog description, word-wrapped and centred, in the strip under the grid."""
    max_w = CHART_W - 240
    for size in range(max(40, CHART_W // 80), 23, -4):
        f = font("sans", size)
        lines, line = [], ""
        for word in CAT.DESCRIPTION.split():
            trial = f"{line} {word}".strip()
            if d.textlength(trial, font=f) <= max_w or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
        step = size + 12
        if len(lines) * step <= FOOTER_H - 30:
            break
    top = CHART_H - FOOTER_H + (FOOTER_H - len(lines) * step) // 2 + step // 2
    for i, text in enumerate(lines):
        d.text((CHART_W // 2, top + i * step), text, font=f, fill=(185, 192, 212), anchor="mm")


def draw_placeholder(d, n):
    x0, y0, x1, y1 = cell_rect(n)
    d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=(13, 13, 19))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    big = 54 if BIG_CELLS else 42
    subs = [(SUB1.get(n, ""), 21 if BIG_CELLS else 19, (84, 84, 104)),
            (SUB2.get(n, ""), 20 if BIG_CELLS else 16, (72, 72, 92))]
    subs = [s for s in subs if s[0]]
    size = _fit_size(d, LABEL[n], "bold", big, CELL_W - 16, 26)
    gap = 14 if BIG_CELLS else 10
    heights = [size] + [s[1] for s in subs]
    total = sum(heights) + gap * len(subs)
    y = cy - total / 2 + size / 2
    d.text((cx, y), LABEL[n], font=font("bold", size), fill=(70, 70, 88), anchor="mm")
    y += size / 2 + gap
    for text, base, colour in subs:
        s = _fit_size(d, text, "sans", base, CELL_W - 14)
        d.text((cx, y + base / 2), text, font=font("sans", s), fill=colour, anchor="mm")
        y += base + gap


def render_chart(title):
    """Build the full-resolution chart image."""
    img = Image.new("RGB", (CHART_W, CHART_H), "black")
    d = ImageDraw.Draw(img)
    d.rectangle([0, TITLE_H, CHART_W - 1, CHART_H - FOOTER_H - 1], fill="white")
    draw_description(d)
    corner = 30 if BIG_CELLS else 25
    done = 0
    for n in range(1, COUNT + 1):
        x0, y0, x1, y1 = cell_rect(n)
        tile = load_tile(n)
        if tile is not None:
            done += 1
            img.paste(tile, (x0, y0))
            pad = 12 if BIG_CELLS else 9
            d.text((x1 - pad, y1 - pad), LABEL[n], font=font("sans", corner),
                   fill="white", anchor="rs", stroke_width=3, stroke_fill="black")
        else:
            draw_placeholder(d, n)
    spare = [cell_rect(n) for n in range(COUNT + 1, COLS * ROWS + 1)]
    if spare:                                   # unused squares after the last object
        d.rectangle([spare[0][0], spare[0][1], spare[-1][2] - 1, spare[-1][3] - 1], fill=(0, 0, 0))
        cx = (spare[0][0] + spare[-1][2]) // 2
        cy = (spare[0][1] + spare[-1][3]) // 2
        width = spare[-1][2] - spare[0][0] - 20
        lines = CAT.SPARE_LINES
        total = sum(s for _, _, s, _ in lines) + 18 * (len(lines) - 1)
        y = cy - total / 2
        for text, kind, size, colour in lines:
            s = _fit_size(d, text, kind, size, width)
            d.text((cx, y + size / 2), text, font=font(kind, s), fill=colour, anchor="mm")
            y += size + 18
    d.text((CHART_W // 2, int(TITLE_H * 0.44)), title,
           font=font("title", _fit_size(d, title, "title", 120 if BIG_CELLS else 140, CHART_W - 80, 40)),
           fill="white", anchor="mm")
    d.text((CHART_W // 2, int(TITLE_H * 0.84)), f"{done} of {COUNT} {CATALOG} objects",
           font=font("sans", 32), fill=(150, 150, 165), anchor="mm")
    return img, done


# --------------------------------------------------------------------------
# Star border: solid black with pin-point stars
# --------------------------------------------------------------------------
_bg_cache = {}


def starfield(w, h, seed=7):
    """Solid black with tiny pin-point stars of varying brightness."""
    key = (w, h, seed)
    if key in _bg_cache:
        return _bg_cache[key]
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    tints = [(255, 255, 255), (215, 228, 255), (255, 244, 225)]
    for _ in range(int(w * h / 2600)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        k = 0.25 + 0.75 * rnd.random() ** 2.5
        col = tuple(int(v * k) for v in rnd.choice(tints))
        if rnd.random() < 0.18:
            d.rectangle([x, y, x + 1, y + 1], fill=col)
        else:
            d.point((x, y), fill=col)
    _bg_cache[key] = img
    return img


def frame_chart(inner):
    """Put the chart inside a BORDER-wide black star border."""
    img = starfield(inner.width + 2 * BORDER, inner.height + 2 * BORDER).copy()
    img.paste(inner, (BORDER, BORDER))
    return img


# --------------------------------------------------------------------------
# Imaging log / notes (one small text file per object, next to its photo)
# --------------------------------------------------------------------------
LOG_FIELDS = [
    ("date", "Date(s) captured"),
    ("total", "Total exposure time"),
    ("sub_length", "Sub length"),
    ("sub_count", "Number of subs"),
    ("gain", "Gain / ISO"),
    ("telescope", "Telescope / lens"),
    ("camera", "Camera"),
    ("mount", "Mount"),
    ("filters", "Filters"),
    ("other", "Other equipment"),
]
EQUIPMENT_KEYS = ("gain", "telescope", "camera", "mount", "filters", "other")
LOG_SUFFIX = "_log.txt"


def log_path(n):
    return ORIG_DIR / f"{SLUG[n]}{LOG_SUFFIX}"


def read_log(n):
    """Read an object's log file back into {field: text, "notes": text}."""
    data = {key: "" for key, _ in LOG_FIELDS}
    data["notes"] = ""
    path = log_path(n)
    if not path.exists():
        return data
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return data
    labels = {label.lower(): key for key, label in LOG_FIELDS}
    for i, line in enumerate(lines):
        if line.strip().lower() == "notes:":
            data["notes"] = "\n".join(lines[i + 1:]).strip("\n")
            break
        if ":" in line:
            label, value = line.split(":", 1)
            key = labels.get(label.strip().lower())
            if key:
                data[key] = value.strip()
    return data


def write_log(n, data):
    """Save the log as a plain text file. An empty log removes the file."""
    path = log_path(n)
    if not any(str(v).strip() for v in data.values()):
        if path.exists():
            path.unlink()
        return None
    width = max(len(label) for _, label in LOG_FIELDS) + 1
    out = [f"{LABEL[n]} - {NAMES[n]}", f"Imaging log ({APP_NAME})", ""]
    for key, label in LOG_FIELDS:
        out.append(f"{(label + ':').ljust(width)} {data.get(key, '').strip()}".rstrip())
    out += ["", "Notes:", data.get("notes", "").strip("\n"), ""]
    path.write_text("\n".join(out), encoding="utf-8")
    return path


def log_summary(n):
    """One short line for the hover preview, e.g. '2h 30m · 75 x 120s · gain 100'."""
    if not log_path(n).exists():
        return ""
    d = read_log(n)
    parts = []
    if d["total"]:
        parts.append(d["total"])
    if d["sub_count"] and d["sub_length"]:
        parts.append(f"{d['sub_count']} x {d['sub_length']}")
    elif d["sub_length"]:
        parts.append(f"subs {d['sub_length']}")
    if d["gain"]:
        parts.append(f"gain {d['gain']}")
    text = "  ·  ".join(parts) or "Log / notes saved"
    return text if len(text) <= 52 else text[:51] + "…"


def total_exposure_text(sub_length, sub_count):
    """'120' or '120s' or '2 min' times a count -> '2h 30m'. Returns '' if it can't tell."""
    m = re.match(r"^\s*([\d.]+)\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes)?\s*$", sub_length, re.I)
    c = re.match(r"^\s*(\d+)\s*$", sub_count)
    if not m or not c:
        return ""
    try:
        secs = float(m.group(1))
    except ValueError:
        return ""
    if (m.group(2) or "s").lower().startswith("m"):
        secs *= 60
    total = round(secs * int(c.group(1)))
    if total <= 0:
        return ""
    h, rem = divmod(total, 3600)
    mins, sec = divmod(rem, 60)
    if h:
        return f"{h}h {mins:02d}m" if mins else f"{h}h"
    if mins:
        return f"{mins}m {sec:02d}s" if sec else f"{mins}m"
    return f"{sec}s"


def load_settings():
    try:
        s = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if isinstance(s, dict):
            return s
    except Exception:
        pass
    return {"title": CAT.DEFAULT_TITLE}


def save_settings(s):
    """Save settings; returns False (instead of crashing) if the file can't be written."""
    try:
        SETTINGS_FILE.write_text(json.dumps(s, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# Widgets that look the same on Windows and Mac
# --------------------------------------------------------------------------
IS_MAC = sys.platform == "darwin" or bool(os.environ.get("FORCE_MAC_UI"))
MOD = "Command" if IS_MAC else "Control"
MOD_NAME = "Cmd" if IS_MAC else "Ctrl"


def Btn(parent, **kw):
    """A button that keeps its dark colours on every platform.

    macOS draws tk.Button natively and ignores background colours (white text on
    a white button), so there a styled Label that acts like a button is used.
    """
    if not IS_MAC:
        return tk.Button(parent, **kw)
    command = kw.pop("command", None)
    bg = kw.pop("bg", "#2b2b36")
    fg = kw.pop("fg", "#111111")
    active = kw.pop("activebackground", bg)
    for k in ("activeforeground", "relief", "bd", "highlightthickness"):
        kw.pop(k, None)
    kw.setdefault("padx", 12)
    kw.setdefault("pady", 6)
    kw.setdefault("cursor", "hand2")
    lbl = tk.Label(parent, bg=bg, fg=fg, **kw)
    lbl._enabled = True
    lbl._fg = fg
    lbl.bind("<Enter>", lambda e: lbl._enabled and lbl.config(bg=active))
    lbl.bind("<Leave>", lambda e: lbl.config(bg=bg))
    if command:
        lbl.bind("<ButtonRelease-1>", lambda e: lbl._enabled and command())
    return lbl


def set_enabled(widget, on):
    if isinstance(widget, tk.Button):
        widget.config(state="normal" if on else "disabled")
    else:
        widget._enabled = on
        widget.config(fg=widget._fg if on else "#6b6b78", cursor="hand2" if on else "arrow")


def Check(parent, text, variable, command, bg, fg):
    """A checkbox that is readable on dark backgrounds on every platform."""
    if not IS_MAC:
        return tk.Checkbutton(parent, text=text, variable=variable, command=command,
                              bg=bg, fg=fg, selectcolor="#2b2b36", activebackground=bg,
                              activeforeground=fg, bd=0, highlightthickness=0)
    lbl = tk.Label(parent, bg=bg, fg=fg, cursor="hand2", padx=6)

    def refresh():
        lbl.config(text=f"{text}: {'On' if variable.get() else 'Off'}")

    def click(_e):
        variable.set(not variable.get())
        refresh()
        command()

    lbl.bind("<ButtonRelease-1>", click)
    refresh()
    return lbl


def open_path(path):
    path = str(path)
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def center_on(win, parent, third=True):
    win.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width()) // 2
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - win.winfo_height()) // (3 if third else 2))
    win.geometry(f"+{max(0, x)}+{max(0, y)}")


def wheel_steps(e):
    """Mouse-wheel direction as +1 / -1 on Windows, Mac and Linux."""
    if getattr(e, "num", None) == 4:
        return 1
    if getattr(e, "num", None) == 5:
        return -1
    return 1 if e.delta > 0 else -1 if e.delta < 0 else 0


# --------------------------------------------------------------------------
# Live twinkling stars in the border
# --------------------------------------------------------------------------
class SpaceAnimator:
    TICK_MS = 50
    COUNT = 160

    def __init__(self, app):
        self.app = app
        self.canvas = app.canvas
        self.rnd = random.Random()
        self.running = False
        self.t = 0.0
        self.twinkles = []
        self._job = None

    def bands(self):
        a = self.app
        s = a.scale
        W, H = a.preview_src.width * s, a.preview_src.height * s
        b = BORDER * s
        x0, y0 = a.ox, a.oy
        return b, [(x0, y0, x0 + W, y0 + b), (x0, y0 + H - b, x0 + W, y0 + H),
                   (x0, y0 + b, x0 + b, y0 + H - b), (x0 + W - b, y0 + b, x0 + W, y0 + H - b)]

    def start(self):
        self.stop()
        if not self.app.border_on or self.app.preview_src is None:
            return
        b, bands = self.bands()
        if b < 8:
            return
        areas = [(x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in bands]
        self.twinkles = []
        for _ in range(self.COUNT):
            x0, y0, x1, y1 = self.rnd.choices(bands, weights=areas)[0]
            x, y = self.rnd.uniform(x0 + 1, x1 - 1), self.rnd.uniform(y0 + 1, y1 - 1)
            r = self.rnd.choice([0.6, 0.8, 0.8, 1.0, 1.3])
            item = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#000000",
                                           outline="", tags="anim")
            tint = self.rnd.choice([(255, 255, 255), (215, 228, 255), (255, 244, 225)])
            self.twinkles.append((item, self.rnd.uniform(0, 6.28), self.rnd.uniform(0.6, 2.6),
                                  self.rnd.uniform(0.55, 1.0), tint))
        self.running = True
        self._job = self.canvas.after(self.TICK_MS, self.tick)

    def stop(self):
        self.running = False
        if self._job:
            try:
                self.canvas.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        self.canvas.delete("anim")

    def tick(self):
        self._job = None
        if not self.running:
            return
        self.t += self.TICK_MS / 1000
        try:
            for item, ph, sp, peak, tint in self.twinkles:
                k = peak * (0.5 + 0.5 * math.sin(ph + self.t * sp)) ** 3
                self.canvas.itemconfig(item, fill="#%02x%02x%02x" % tuple(int(c * k) for c in tint))
            for tag in ("hint", "hl", "hover"):
                self.canvas.tag_raise(tag)
        except tk.TclError:
            return
        self._job = self.canvas.after(self.TICK_MS, self.tick)


# --------------------------------------------------------------------------
# The window
# --------------------------------------------------------------------------
BAR_BG = "#1b1b22"
BTN = dict(bg="#2b2b36", fg="white", activebackground="#3a3a4a",
           activeforeground="white", relief="flat", padx=12, pady=6, bd=0)
LIGHT = "#f4f4f7"
BLUE = "#2f35b8"


class App:
    def __init__(self):
        for d in (LIBRARY, ORIG_DIR, CELL_DIR):
            d.mkdir(parents=True, exist_ok=True)
        self.settings = load_settings()
        self.undo_log = Undo()

        self.root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
        self.root.title(f"{APP_NAME}  ·  by {AUTHOR}")
        self.root.configure(bg="#111")
        try:
            ico = resource(CAT.ICON_ICO)
            if ico.exists() and sys.platform.startswith("win"):
                self.root.iconbitmap(default=str(ico))
        except Exception:
            pass
        sh = self.root.winfo_screenheight()
        h = int(sh * 0.85)
        self.border_on = bool(self.settings.get("border", True))
        fw, fh = (CHART_W + 2 * BORDER, CHART_H + 2 * BORDER) if self.border_on else (CHART_W, CHART_H)
        w = int((h - 150) * fw / fh)
        w = min(max(w, 1060), self.root.winfo_screenwidth() - 40)   # room for the whole toolbar
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(500, 520)
        if CAT.START_MAXIMIZED:
            try:                                   # lots of squares: start with as much room as possible
                if sys.platform.startswith("win"):
                    self.root.state("zoomed")
                else:
                    self.root.geometry(f"{self.root.winfo_screenwidth() - 20}x{self.root.winfo_screenheight() - 90}+0+0")
            except tk.TclError:
                pass

        bar = tk.Frame(self.root, bg=BAR_BG)
        bar.pack(fill="x")
        Btn(bar, text="Add photos…", command=self.add_photos, **BTN).pack(side="left", padx=(8, 3), pady=6)
        Btn(bar, text="Export chart…", command=self.export, **BTN).pack(side="left", padx=3, pady=6)
        Btn(bar, text="Edit title…", command=self.edit_title, **BTN).pack(side="left", padx=3, pady=6)
        Btn(bar, text="Missing list", command=self.show_missing, **BTN).pack(side="left", padx=3, pady=6)
        self.undo_btn = Btn(bar, text="Undo", command=self.do_undo, **BTN)
        self.undo_btn.pack(side="left", padx=3, pady=6)
        Btn(bar, text="Library folder", command=lambda: open_path(LIBRARY), **BTN).pack(side="left", padx=3, pady=6)
        Btn(bar, text="Help", command=self.show_welcome, **BTN).pack(side="left", padx=3, pady=6)
        Btn(bar, text="Clear all…", command=self.clear_all, bg="#5a1f24", fg="white",
            activebackground="#7a2a31", activeforeground="white", relief="flat",
            padx=12, pady=6, bd=0).pack(side="left", padx=3, pady=6)
        self.border_var = tk.BooleanVar(value=self.border_on)
        Check(bar, "Star border", self.border_var, self.toggle_border, BAR_BG, "white").pack(side="left", padx=6)
        self.count_var = tk.StringVar()
        tk.Label(bar, textvariable=self.count_var, bg=BAR_BG, fg="#9ad",
                 font=("TkDefaultFont", 11, "bold")).pack(side="right", padx=12)
        self.update_undo_button()

        self.build_credit_bar()

        self.status_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.status_var, bg=BAR_BG, fg="#bbb",
                 anchor="w", padx=10, pady=4).pack(side="bottom", fill="x")

        self.canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        ex = CAT.EXAMPLES
        self.default_status = (f"Drag photos onto the chart. Files named like {ex[0]} or {ex[-1]} go to "
                               "their square automatically; others go where you drop them.")
        if not HAS_DND:
            self.default_status = ("Drag and drop is off (pip install tkinterdnd2). "
                                   "Click a square or use Add photos.")
        self.status_var.set(self.default_status)

        self.chart = None
        self.preview_src = None
        self.done = 0
        self._hover_n = None
        self._hover_job = None
        self._hover_photo = None
        self._missing = None
        self._busy = False
        self.bx = 0
        self.scale, self.ox, self.oy = 1.0, 0, 0
        self._resize_job = None

        self.canvas.bind("<Configure>", self._schedule_preview)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", lambda e: (self.highlight(None), self.hide_hover(),
                                               self.status_var.set(self.default_status)))
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        if sys.platform == "darwin":
            self.canvas.bind("<Button-2>", self.on_right_click)
        self.root.bind(f"<{MOD}-o>", lambda e: self.add_photos())
        self.root.bind(f"<{MOD}-e>", lambda e: self.export())
        self.root.bind(f"<{MOD}-z>", lambda e: self.do_undo())
        if IS_MAC:
            self.canvas.bind("<Control-Button-1>", self.on_right_click)

        if HAS_DND:
            self.canvas.drop_target_register(DND_FILES)
            self.canvas.dnd_bind("<<Drop>>", self.on_drop)
            self.canvas.dnd_bind("<<DropPosition>>", self.on_drop_position)
            self.canvas.dnd_bind("<<DropLeave>>", lambda e: self.highlight(None))

        self.anim = SpaceAnimator(self)
        self.status_var.set("Preparing the star field…")
        self.root.update_idletasks()
        self.rebuild()
        self.status_var.set(self.default_status)
        if not self.settings.get("welcome_shown"):
            self.root.after(400, self.first_run)

    def save_settings(self):
        if not save_settings(self.settings):
            self.status_var.set(f"Couldn't save your settings in {LIBRARY} - check the folder isn't read-only.")

    def first_run(self):
        self.settings["welcome_shown"] = APP_VERSION
        self.save_settings()
        self.show_welcome()

    def toggle_border(self):
        self.border_on = bool(self.border_var.get())
        self.settings["border"] = self.border_on
        self.save_settings()
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            self.rebuild()
        finally:
            self.root.config(cursor="")

    # ---------- credit / about / help ----------
    def load_logo(self, height):
        try:
            with Image.open(resource("saltypogue_logo.png")) as im:
                im = to_rgb(im)
                w = max(1, round(im.width * height / im.height))
                return ImageTk.PhotoImage(im.resize((w, height), Image.LANCZOS))
        except Exception:
            return None

    def link_label(self, parent, text, url, bg, size=10):
        lbl = tk.Label(parent, text=text, bg=bg, fg="#6fb3ff", cursor="hand2",
                       font=("TkDefaultFont", size, "underline"))
        lbl.bind("<Button-1>", lambda e: webbrowser.open(url))
        lbl.bind("<Enter>", lambda e: lbl.config(fg="#a8d1ff"))
        lbl.bind("<Leave>", lambda e: lbl.config(fg="#6fb3ff"))
        return lbl

    def load_app_icon(self, size, bg):
        try:
            with Image.open(resource(CAT.APP_ICON_PNG)) as im:
                im = im.convert("RGBA").resize((size, size), Image.LANCZOS)
                back = Image.new("RGBA", im.size, bg)
                back.alpha_composite(im)
                return ImageTk.PhotoImage(back.convert("RGB"))
        except Exception:
            return None

    def build_credit_bar(self):
        bg = "#14141b"
        foot = tk.Frame(self.root, bg=bg)
        foot.pack(side="bottom", fill="x")
        self.small_logo = self.load_app_icon(46, bg)
        if self.small_logo:
            icon = tk.Label(foot, image=self.small_logo, bg=bg, bd=0, cursor="hand2")
            icon.pack(side="left", padx=(10, 8), pady=6)
            icon.bind("<Button-1>", lambda e: self.show_about())
        tk.Label(foot, text=APP_NAME, bg=bg, fg="#dfe3ee",
                 font=("TkDefaultFont", 10, "bold")).pack(side="left", pady=6)
        tk.Label(foot, text=f"  v{APP_VERSION}", bg=bg, fg="#777").pack(side="left", pady=6)
        links = tk.Frame(foot, bg=bg)
        links.pack(side="right", padx=10)
        tk.Label(links, text="Follow:", bg=bg, fg="#999").pack(side="left", padx=(0, 4))
        for i, (name, url) in enumerate(SOCIAL_LINKS):
            if i:
                tk.Label(links, text="·", bg=bg, fg="#666").pack(side="left", padx=2)
            self.link_label(links, name, url, bg).pack(side="left", padx=4)

    def show_about(self):
        if getattr(self, "_about", None) and self._about.winfo_exists():
            self._about.lift()
            return
        win = tk.Toplevel(self.root)
        self._about = win
        win.title(f"About {APP_NAME}")
        win.configure(bg="white")
        win.resizable(False, False)
        win.transient(self.root)
        self.big_logo = self.load_logo(300)
        if self.big_logo:
            tk.Label(win, image=self.big_logo, bg="white").pack(padx=30, pady=(24, 8))
        tk.Label(win, text=APP_NAME, bg="white", fg="#111",
                 font=("TkDefaultFont", 16, "bold")).pack()
        tk.Label(win, text=f"Created by {AUTHOR}", bg="white", fg=BLUE,
                 font=("TkDefaultFont", 12, "bold")).pack(pady=(2, 4))
        tk.Label(win, text=f"Build a chart of all {COUNT} {CATALOG} {CAT.OBJECTS} from your own astrophotos.",
                 bg="white", fg="#555").pack(padx=20)
        row = tk.Frame(win, bg="white")
        row.pack(pady=(14, 6))
        for name, url in SOCIAL_LINKS:
            Btn(row, text=name, command=lambda u=url: webbrowser.open(u),
                bg=BLUE, fg="white", activebackground="#4148d6",
                activeforeground="white", relief="flat", bd=0, padx=14, pady=6,
                cursor="hand2", font=("TkDefaultFont", 10, "bold")).pack(side="left", padx=5)
        tk.Label(win, text=f"Version {APP_VERSION}  ·  @saltypogue", bg="white", fg="#888").pack(pady=(4, 0))
        Btn(win, text="Close", command=win.destroy, relief="flat", bd=0,
            bg="#e6e6ec", activebackground="#d6d6de", padx=16, pady=4).pack(pady=(14, 20))
        win.bind("<Escape>", lambda e: win.destroy())
        center_on(win, self.root)
        win.grab_set()

    def show_welcome(self):
        """Short how-to, shown the first time the app opens and from the Help button."""
        if getattr(self, "_welcome", None) and self._welcome.winfo_exists():
            self._welcome.lift()
            return
        win = tk.Toplevel(self.root)
        self._welcome = win
        win.title(f"Welcome to {APP_NAME}")
        win.configure(bg="white")
        win.resizable(False, False)
        win.transient(self.root)
        top = tk.Frame(win, bg="white")
        top.pack(fill="x", padx=26, pady=(22, 6))
        self._welcome_icon = self.load_app_icon(64, "white")
        if self._welcome_icon:
            tk.Label(top, image=self._welcome_icon, bg="white").pack(side="left", padx=(0, 14))
        head = tk.Frame(top, bg="white")
        head.pack(side="left", fill="x")
        tk.Label(head, text=f"Welcome to {APP_NAME}", bg="white", fg="#111",
                 font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        tk.Label(head, text=f"Build a chart of all {COUNT} {CATALOG} {CAT.OBJECTS} from your own photos.",
                 bg="white", fg="#555").pack(anchor="w")

        ex = CAT.EXAMPLES
        steps = [
            ("Drag your photos onto the chart",
             "Drop one photo, lots of photos, or a whole folder. JPG, PNG and TIFF all work, "
             "including 16-bit and 32-bit TIFFs straight from your stacking software."),
            ("Name your files so they find their square",
             "A file name with the object's number or name goes to the right square by itself: "
             + ", ".join(ex) + ". No match? Drop the photo right on the square you want."),
            ("Right-click a photo for more",
             "Adjust framing (move and zoom the crop), add a log with your exposure and equipment, "
             "open the original, or remove it."),
            ("Your chart saves itself",
             f"After every change the chart is saved to {CHART_FILE}. "
             "Use Export chart to save a copy anywhere else."),
        ]
        body = tk.Frame(win, bg="white")
        body.pack(fill="x", padx=26, pady=(8, 0))
        for i, (title, text) in enumerate(steps, 1):
            row = tk.Frame(body, bg="white")
            row.pack(fill="x", pady=6)
            tk.Label(row, text=str(i), bg=BLUE, fg="white", width=2,
                     font=("TkDefaultFont", 12, "bold")).pack(side="left", anchor="n", padx=(0, 12), ipady=2)
            col = tk.Frame(row, bg="white")
            col.pack(side="left", fill="x")
            tk.Label(col, text=title, bg="white", fg="#111", font=("TkDefaultFont", 11, "bold"),
                     anchor="w").pack(anchor="w")
            tk.Label(col, text=text, bg="white", fg="#444", justify="left", wraplength=470,
                     anchor="w").pack(anchor="w")
        tips = tk.Frame(win, bg="#eef1fb")
        tips.pack(fill="x", padx=26, pady=(12, 0))
        tk.Label(tips, text=(f"Tips:  Missing list shows what's left to photograph.  "
                             f"Undo ({MOD_NAME}+Z) puts back a photo you removed or replaced.  "
                             "Rest the mouse on a photo for a bigger view."),
                 bg="#eef1fb", fg="#333", justify="left", wraplength=500).pack(padx=12, pady=8, anchor="w")
        row = tk.Frame(win, bg="white")
        row.pack(fill="x", padx=26, pady=(14, 20))
        Btn(row, text="Get started", command=win.destroy, bg=BLUE, fg="white", activebackground="#4148d6",
            activeforeground="white", relief="flat", bd=0, padx=20, pady=6,
            font=("TkDefaultFont", 10, "bold")).pack(side="right")
        Btn(row, text="About", command=lambda: (win.destroy(), self.show_about()), bg="#e6e6ec", fg="#111",
            activebackground="#d6d6de", relief="flat", bd=0, padx=14, pady=6).pack(side="left")
        win.bind("<Escape>", lambda e: win.destroy())
        win.bind("<Return>", lambda e: win.destroy())
        center_on(win, self.root)
        win.grab_set()

    # ---------- chart / preview ----------
    def rebuild(self):
        inner, self.done = render_chart(self.settings.get("title", CAT.DEFAULT_TITLE))
        if self.border_on:
            self.chart = self.preview_src = frame_chart(inner)
            self.bx = BORDER
        else:
            self.chart = self.preview_src = inner
            self.bx = 0
        try:
            self.chart.save(CHART_FILE)
        except OSError as e:
            messagebox.showerror("Save failed", f"Couldn't save the chart:\n{e}")
        self.count_var.set(f"{self.done} / {COUNT}")
        self.draw_preview()
        self.refresh_missing()

    def _schedule_preview(self, _e=None):
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(60, self.draw_preview)

    def draw_preview(self):
        self._resize_job = None
        if self.preview_src is None:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        src = self.preview_src
        self.scale = min(cw / src.width, ch / src.height)
        w, h = max(1, int(src.width * self.scale)), max(1, int(src.height * self.scale))
        self.ox, self.oy = (cw - w) // 2, (ch - h) // 2
        self.anim.stop()
        self.photo = ImageTk.PhotoImage(src.resize((w, h), Image.LANCZOS))
        self.hide_hover()
        self.canvas.delete("all")
        self.canvas.create_image(self.ox, self.oy, anchor="nw", image=self.photo)
        if self.done == 0:
            self.draw_hint(cw, ch)
        self.anim.start()

    def draw_hint(self, cw, ch):
        """Big friendly hint over an empty chart."""
        c = self.canvas
        bw, bh = min(560, cw - 40), 130
        x0, y0 = (cw - bw) / 2, (ch - bh) / 2
        c.create_rectangle(x0, y0, x0 + bw, y0 + bh, fill="#10131f", outline="#4da3ff", width=2,
                           dash=(6, 4), tags="hint")
        c.create_text(cw / 2, y0 + 42, text="Drag your photos here", fill="white",
                      font=("TkDefaultFont", 18, "bold"), tags="hint")
        c.create_text(cw / 2, y0 + 80, text=f"Name them like {CAT.EXAMPLES[0]} or {CAT.EXAMPLES[-1]},"
                                            " or click any square to choose a photo.",
                      fill="#b8c4e0", font=("TkDefaultFont", 11), width=bw - 30, tags="hint")
        c.create_text(cw / 2, y0 + 108, text="Help shows a quick guide.", fill="#7f8aa8",
                      font=("TkDefaultFont", 10), tags="hint")

    def cell_at(self, cx, cy):
        x = (cx - self.ox) / self.scale - self.bx - GAP
        y = (cy - self.oy) / self.scale - self.bx - TITLE_H - GAP
        if x < 0 or y < 0:
            return None
        c, r = int(x // (CELL_W + GAP)), int(y // (CELL_H + GAP))
        if c >= COLS or r >= ROWS:
            return None
        n = r * COLS + c + 1
        return n if n <= COUNT else None

    def highlight(self, n):
        self.canvas.delete("hl")
        if n:
            x0, y0, x1, y1 = (v + self.bx for v in cell_rect(n))
            s = self.scale
            self.canvas.create_rectangle(self.ox + x0 * s, self.oy + y0 * s,
                                         self.ox + x1 * s, self.oy + y1 * s,
                                         outline="#4da3ff", width=3, tags="hl")

    # ---------- hover preview ----------
    def schedule_hover(self, n, x, y):
        self._hover_xy = (x, y)
        if n != self._hover_n:
            self.hide_hover()
            self._hover_n = n
            if n and cell_path(n).exists():
                self._hover_job = self.root.after(350, lambda: self.show_hover(n))
        elif self.canvas.find_withtag("hover"):
            self.place_hover()

    def hide_hover(self):
        if self._hover_job:
            self.root.after_cancel(self._hover_job)
            self._hover_job = None
        self.canvas.delete("hover")
        self._hover_n = None

    def show_hover(self, n):
        self._hover_job = None
        if n != self._hover_n:
            return
        im = hover_image(n)
        if im is None:
            return
        self._hover_photo = ImageTk.PhotoImage(im)
        c = self.canvas
        c.delete("hover")
        summary = log_summary(n)
        S, cap = HOVER_SIZE, 28 + (20 if summary else 0)
        self._hover_h = S + cap + 8
        c.create_rectangle(0, 0, S + 8, S + cap + 8, fill="#0b0d16", outline="#4da3ff",
                           width=2, tags=("hover", "hover_box"))
        c.create_image(4, 4, anchor="nw", image=self._hover_photo, tags=("hover", "hover_img"))
        c.create_text(S / 2 + 4, S + 4 + 14, text=f"{LABEL[n]}  ·  {NAMES[n]}",
                      fill="white", font=("TkDefaultFont", 10, "bold"), tags=("hover", "hover_txt"))
        if summary:
            c.create_text(S / 2 + 4, S + 4 + 35, text=summary, fill="#9fc4ff",
                          font=("TkDefaultFont", 9), tags=("hover", "hover_log"))
        self.place_hover()

    def place_hover(self):
        c = self.canvas
        x, y = self._hover_xy
        W, H = HOVER_SIZE + 8, getattr(self, "_hover_h", HOVER_SIZE + 36)
        cw, ch = c.winfo_width(), c.winfo_height()
        px = x + 22 if x + 22 + W <= cw else x - 22 - W
        py = y + 22 if y + 22 + H <= ch else y - 22 - H
        px = max(0, min(px, cw - W))
        py = max(0, min(py, ch - H))
        bx = c.coords("hover_box")
        if bx:
            c.move("hover", px - bx[0], py - bx[1])
        c.tag_raise("hover")

    # ---------- mouse ----------
    def on_motion(self, e):
        n = self.cell_at(e.x, e.y)
        self.highlight(n)
        self.schedule_hover(n, e.x, e.y)
        if n:
            state = ("click to replace, right-click to adjust framing, add notes or remove"
                     if cell_path(n).exists() else "empty - drop a photo here or click to choose one")
            self.status_var.set(f"{LABEL[n]}  ·  {NAMES[n]}  ·  {state}")
        else:
            self.status_var.set(self.default_status)

    def on_click(self, e):
        self.hide_hover()
        n = self.cell_at(e.x, e.y)
        if n and not self._busy:
            self.choose_for(n)

    def on_right_click(self, e):
        self.hide_hover()
        n = self.cell_at(e.x, e.y)
        if not n or self._busy:
            return
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label=f"{LABEL[n]} - {NAMES[n]}", state="disabled")
        m.add_separator()
        has = cell_path(n).exists()
        origs = originals_for(n)
        m.add_command(label="Choose photo…" if not has else "Replace photo…", command=lambda: self.choose_for(n))
        m.add_command(label="Adjust framing…", state="normal" if origs else "disabled",
                      command=lambda: self.adjust_framing(n))
        m.add_command(label="Edit log / notes…" if log_path(n).exists() else "Add log / notes…",
                      state="normal" if (has or log_path(n).exists()) else "disabled",
                      command=lambda: self.edit_log(n))
        m.add_command(label="Open original", state="normal" if origs else "disabled",
                      command=lambda: open_path(origs[0]))
        m.add_separator()
        m.add_command(label="Remove photo", state="normal" if has else "disabled",
                      command=lambda: self.remove(n))
        m.tk_popup(e.x_root, e.y_root)

    # ---------- drag and drop ----------
    def _event_cell(self, e):
        return self.cell_at(e.x_root - self.canvas.winfo_rootx(),
                            e.y_root - self.canvas.winfo_rooty())

    def on_drop_position(self, e):
        self.hide_hover()
        self.highlight(self._event_cell(e))
        return e.action

    def on_drop(self, e):
        target = self._event_cell(e)
        self.highlight(None)
        paths = self.root.tk.splitlist(e.data)
        self.root.after(10, lambda: self.import_files(paths, target))
        return e.action

    # ---------- undo ----------
    def update_undo_button(self):
        set_enabled(self.undo_btn, self.undo_log.available)

    def do_undo(self):
        if self._busy:
            return
        if not self.undo_log.available:
            self.status_var.set("Nothing to undo.")
            return
        try:
            label = self.undo_log.undo()
        except OSError as ex:
            messagebox.showerror("Couldn't undo", str(ex))
            return
        self.update_undo_button()
        self.rebuild()
        self.status_var.set(f"Undone: {label}.")

    # ---------- adding photos ----------
    def collect_files(self, paths):
        files = []
        for p in paths:
            p = Path(p)
            if p.is_dir():
                files += sorted(f for f in p.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXT)
            elif p.suffix.lower() in IMAGE_EXT:
                files.append(p)
        return files

    def import_files(self, paths, target=None):
        if self._busy:
            return
        files = self.collect_files(paths)
        if not files:
            messagebox.showinfo("No photos", "None of those files are supported images "
                                "(JPG, PNG, TIFF, BMP, WebP, GIF).")
            return
        if len(files) == 1:
            self.import_single(files[0], target)
        else:
            self.import_batch(files)

    def import_single(self, f, target):
        n, how = find_square(f.stem)
        if n is None:
            n = target or self.ask_number(f)
        if n is None:
            return
        if cell_path(n).exists() and not messagebox.askyesno(
                "Replace photo?", f"{LABEL[n]} already has a photo. Replace it with {f.name}?\n\n"
                                  "(You can Undo this.)"):
            return
        self.undo_log.begin(f"adding {f.name} to {LABEL[n]}")
        self.status_var.set(f"Adding {f.name} to {LABEL[n]}…")
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            stretched = import_photo(f, n, self.undo_log)
        except Exception as ex:
            self.root.config(cursor="")
            messagebox.showerror("Couldn't add photo", f"{f.name}\n\n{ex}")
            return
        self.root.config(cursor="")
        self.update_undo_button()
        self.rebuild()
        msg = f"Added {f.name} to {LABEL[n]} ({NAMES[n]})"
        if how == "name":
            msg += " - matched by name"
        if stretched:
            msg += ". It looked unstretched (linear), so it was brightened for the chart"
        self.status_var.set(msg + ". Chart saved.")

    def import_batch(self, files):
        """Add many photos, one at a time, with a progress window the user can cancel."""
        self._busy = True
        self.undo_log.begin(f"adding {len(files)} photos")
        state = dict(i=0, added=[], skipped=[], replaced=0, stretched=0, by_name=0, cancel=False)

        win = tk.Toplevel(self.root)
        win.title("Adding photos")
        win.configure(bg=LIGHT)
        win.resizable(False, False)
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", lambda: state.update(cancel=True))
        head = tk.StringVar(value=f"Adding 1 of {len(files)}…")
        tk.Label(win, textvariable=head, bg=LIGHT, fg="#111",
                 font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=20, pady=(16, 4))
        sub = tk.StringVar()
        tk.Label(win, textvariable=sub, bg=LIGHT, fg="#555", width=52, anchor="w").pack(anchor="w", padx=20)
        bar_w = 380
        bar = tk.Canvas(win, width=bar_w, height=16, bg="#dcdce4", highlightthickness=0)
        bar.pack(padx=20, pady=12)
        fill = bar.create_rectangle(0, 0, 0, 16, fill=BLUE, width=0)
        Btn(win, text="Cancel", command=lambda: state.update(cancel=True), bg="#dcdce4", fg="#111",
            activebackground="#cdcdd8", relief="flat", bd=0, padx=16, pady=5).pack(pady=(0, 16))
        center_on(win, self.root, third=False)
        try:
            win.grab_set()
        except tk.TclError:
            pass

        def step():
            i = state["i"]
            if state["cancel"] or i >= len(files):
                return finish()
            f = files[i]
            head.set(f"Adding {i + 1} of {len(files)}…")
            sub.set(f.name if len(f.name) < 60 else f.name[:57] + "…")
            bar.coords(fill, 0, 0, bar_w * i / len(files), 16)
            win.update_idletasks()
            n, how = find_square(f.stem)
            if n is None:
                state["skipped"].append(f"{f.name}: no {CATALOG} number or name found in the file name")
            else:
                try:
                    if cell_path(n).exists() and n not in state["added"]:
                        state["replaced"] += 1
                    state["stretched"] += bool(import_photo(f, n, self.undo_log))
                    state["added"].append(n)
                    state["by_name"] += how == "name"
                except Exception as ex:
                    state["skipped"].append(f"{f.name}: {ex}")
            state["i"] = i + 1
            self.root.after(1, step)

        def finish():
            try:
                win.grab_release()
            except tk.TclError:
                pass
            win.destroy()
            self._busy = False
            self.update_undo_button()
            added = sorted(set(state["added"]))
            if added:
                self.root.config(cursor="watch")
                self.root.update_idletasks()
                try:
                    self.rebuild()
                finally:
                    self.root.config(cursor="")
                labels = ", ".join(LABEL[n] for n in added[:30]) + (" …" if len(added) > 30 else "")
                extra = []
                if state["replaced"]:
                    extra.append(f"replaced {state['replaced']} (Undo puts them back)")
                if state["stretched"]:
                    extra.append(f"brightened {state['stretched']} linear image(s)")
                self.status_var.set(f"Added {len(added)}: {labels}" + (f"  ·  {'; '.join(extra)}" if extra else ""))
            if state["cancel"]:
                self.status_var.set(f"Stopped after {state['i']} of {len(files)} files. "
                                    + ("Undo removes the ones that were added." if added else ""))
            if state["skipped"]:
                sk = state["skipped"]
                ex = CAT.EXAMPLES
                messagebox.showwarning(
                    "Some photos were skipped",
                    "\n".join(sk[:25]) + ("\n…" if len(sk) > 25 else "") +
                    f"\n\nTip: name files like {ex[0]} or {ex[-1]}, or drop them one at a time onto a square.")

        self.root.after(30, step)

    def ask_number(self, f):
        num = simpledialog.askinteger(
            "Which object?",
            f"Couldn't tell which object {f.name} is from its name.\n\nWhich {CAT.NUMBER_WORD} is it?",
            minvalue=1, parent=self.root)
        if num is None:
            return None
        n = CAT.index_for_number(num)
        if n is None:
            messagebox.showerror("Not in this catalog",
                                 f"{num} isn't a {CAT.NUMBER_WORD} in the {CATALOG} list.", parent=self.root)
        return n

    def choose_for(self, n):
        f = filedialog.askopenfilename(
            title=f"Choose a photo for {LABEL[n]} - {NAMES[n]}",
            filetypes=[("Images", " ".join(f"*{x}" for x in sorted(IMAGE_EXT))), ("All files", "*.*")])
        if f:
            self.import_single_to(Path(f), n)

    def import_single_to(self, f, n):
        if cell_path(n).exists() and not messagebox.askyesno(
                "Replace photo?", f"{LABEL[n]} already has a photo. Replace it?\n\n(You can Undo this.)"):
            return
        self.undo_log.begin(f"adding {f.name} to {LABEL[n]}")
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            stretched = import_photo(f, n, self.undo_log)
        except Exception as ex:
            messagebox.showerror("Couldn't open photo", f"{f.name}\n\n{ex}")
            return
        finally:
            self.root.config(cursor="")
        self.update_undo_button()
        self.rebuild()
        self.status_var.set(f"Added {LABEL[n]}" + (" (brightened: it looked linear)" if stretched else "")
                            + ". Chart saved.")

    def add_photos(self):
        if self._busy:
            return
        files = filedialog.askopenfilenames(
            title=f"Add {CATALOG} photos (name them like {CAT.EXAMPLES[0]})",
            filetypes=[("Images", " ".join(f"*{x}" for x in sorted(IMAGE_EXT))), ("All files", "*.*")])
        if files:
            self.import_files(files)

    def remove(self, n):
        self.undo_log.begin(f"removing {LABEL[n]}")
        try:
            remove_photo(n, self.undo_log)
        except OSError as ex:
            messagebox.showerror("Couldn't remove photo", str(ex))
        self.update_undo_button()
        self.rebuild()
        self.status_var.set(f"Removed {LABEL[n]}. Changed your mind? Click Undo ({MOD_NAME}+Z).")

    # ---------- framing ----------
    def adjust_framing(self, n):
        origs = originals_for(n)
        if not origs:
            return
        self.hide_hover()
        try:
            full, _ = open_photo(origs[0])
        except Exception as ex:
            messagebox.showerror("Couldn't open photo", f"{origs[0].name}\n\n{ex}")
            return
        FramingDialog(self, n, full)

    def save_framing(self, n, full, crop):
        self.undo_log.begin(f"framing of {LABEL[n]}")
        try:
            tile = make_tile(full, crop)
            self.undo_log.park(cell_path(n))
            self.undo_log.park(crop_path(n))
            tile.save(cell_path(n))
            self.undo_log.made(cell_path(n))
            if crop != DEFAULT_CROP:
                crop_path(n).write_text(json.dumps([round(v, 5) for v in crop]), encoding="utf-8")
                self.undo_log.made(crop_path(n))
        except OSError as ex:
            messagebox.showerror("Couldn't save the framing", str(ex))
        self.update_undo_button()
        self.rebuild()
        self.status_var.set(f"New framing saved for {LABEL[n]}.")

    # ---------- missing list ----------
    def show_missing(self):
        if self._missing and self._missing.winfo_exists():
            self._missing.lift()
            return
        win = tk.Toplevel(self.root)
        self._missing = win
        win.title(f"Missing list - {CATALOG}")
        win.configure(bg=LIGHT)
        win.transient(self.root)
        win.minsize(360, 300)
        self._missing_head = tk.StringVar()
        tk.Label(win, textvariable=self._missing_head, bg=LIGHT, fg="#111",
                 font=("TkDefaultFont", 13, "bold")).pack(anchor="w", padx=16, pady=(14, 0))
        tk.Label(win, text="Click an object to find it on the chart. Double-click to choose a photo for it.",
                 bg=LIGHT, fg="#666", wraplength=380, justify="left").pack(anchor="w", padx=16, pady=(2, 8))
        self._missing_all = tk.BooleanVar(value=False)
        tk.Checkbutton(win, text="Show photographed objects too", variable=self._missing_all,
                       command=self.refresh_missing, bg=LIGHT, activebackground=LIGHT,
                       highlightthickness=0).pack(anchor="w", padx=12)
        box = tk.Frame(win, bg=LIGHT)
        box.pack(fill="both", expand=True, padx=16, pady=6)
        lb = tk.Listbox(box, width=48, height=20, activestyle="none", relief="solid", bd=1,
                        selectbackground="#c9d6ff", selectforeground="#111", exportselection=False)
        sc = tk.Scrollbar(box, command=lb.yview)
        lb.configure(yscrollcommand=sc.set)
        lb.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self._missing_lb = lb

        def selected():
            sel = lb.curselection()
            return self._missing_rows[sel[0]] if sel else None

        lb.bind("<<ListboxSelect>>", lambda e: self.highlight(selected()))
        lb.bind("<Double-Button-1>", lambda e: selected() and self.choose_for(selected()))
        row = tk.Frame(win, bg=LIGHT)
        row.pack(fill="x", padx=16, pady=(4, 14))
        Btn(row, text="Save checklist…", command=self.save_checklist, bg=BLUE, fg="white",
            activebackground="#4148d6", activeforeground="white", relief="flat", bd=0,
            padx=14, pady=5).pack(side="left")
        Btn(row, text="Close", command=win.destroy, bg="#dcdce4", fg="#111", activebackground="#cdcdd8",
            relief="flat", bd=0, padx=16, pady=5).pack(side="right")
        win.bind("<Escape>", lambda e: win.destroy())
        self.refresh_missing()
        win.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() - win.winfo_width() - 30
        win.geometry(f"+{max(0, x)}+{self.root.winfo_rooty() + 60}")

    def refresh_missing(self):
        if not (self._missing and self._missing.winfo_exists()):
            return
        have = set(filled())
        show_all = self._missing_all.get()
        self._missing_head.set(f"{COUNT - len(have)} of {COUNT} still to photograph"
                               if len(have) < COUNT else f"All {COUNT} photographed - well done!")
        lb = self._missing_lb
        lb.delete(0, "end")
        self._missing_rows = []
        for n in range(1, COUNT + 1):
            if n in have and not show_all:
                continue
            mark = "✓ " if n in have else "    "
            lb.insert("end", f"{mark}{LABEL[n]}  ·  {NAMES[n]}")
            if n in have:
                lb.itemconfig("end", fg="#2a7a3a")
            self._missing_rows.append(n)

    def save_checklist(self):
        f = filedialog.asksaveasfilename(
            title="Save checklist", defaultextension=".txt",
            initialfile=f"{CAT.CHART_FILE_NAME.replace('_chart.png', '')}_checklist.txt",
            filetypes=[("Text file", "*.txt"), ("CSV (spreadsheet)", "*.csv")])
        if not f:
            return
        have = set(filled())
        try:
            if f.lower().endswith(".csv"):
                import csv
                with open(f, "w", newline="", encoding="utf-8-sig") as fh:
                    w = csv.writer(fh)
                    w.writerow(["Object", "Name", "Photographed"])
                    for n in range(1, COUNT + 1):
                        w.writerow([LABEL[n], NAMES[n], "yes" if n in have else ""])
            else:
                lines = [f"{APP_NAME} checklist", f"{len(have)} of {COUNT} photographed", ""]
                lines += [f"[{'x' if n in have else ' '}] {LABEL[n]} - {NAMES[n]}" for n in range(1, COUNT + 1)]
                Path(f).write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as ex:
            messagebox.showerror("Couldn't save", str(ex))
            return
        self.status_var.set(f"Checklist saved to {f}")

    # ---------- log ----------
    def edit_log(self, n):
        self.hide_hover()
        path = log_path(n)
        is_new = not path.exists()
        data = read_log(n)
        last = self.settings.get("last_equipment", {}) if is_new else {}
        for k in EQUIPMENT_KEYS:
            if is_new and last.get(k):
                data[k] = last[k]

        BG = LIGHT
        win = tk.Toplevel(self.root)
        win.title(f"Log / notes - {LABEL[n]}")
        win.configure(bg=BG)
        win.transient(self.root)
        win.resizable(False, False)

        tk.Label(win, text=f"{LABEL[n]}  ·  {NAMES[n]}", bg=BG, fg="#111",
                 font=("TkDefaultFont", 14, "bold")).pack(anchor="w", padx=18, pady=(14, 0))
        hint = "Fill in whatever you like - every box is optional."
        if is_new and any(last.get(k) for k in EQUIPMENT_KEYS):
            hint = "Equipment is filled in from your last log. Change anything that differs."
        tk.Label(win, text=hint, bg=BG, fg="#666").pack(anchor="w", padx=18, pady=(2, 8))

        form = tk.Frame(win, bg=BG)
        form.pack(padx=18, fill="x")
        variables, entries = {}, {}
        for row, (key, label) in enumerate(LOG_FIELDS):
            if key == "telescope":
                tk.Label(form, text="Equipment", bg=BG, fg=BLUE,
                         font=("TkDefaultFont", 10, "bold")).grid(row=row + 100, column=0, columnspan=2,
                                                                 sticky="w", pady=(10, 2))
            r = row + (101 if key in ("telescope", "camera", "mount", "filters", "other") else 0)
            tk.Label(form, text=label, bg=BG, fg="#222", anchor="w").grid(row=r, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=data.get(key, ""))
            ent = tk.Entry(form, textvariable=var, width=46, relief="solid", bd=1)
            ent.grid(row=r, column=1, sticky="we", padx=(12, 0), pady=3, ipady=2)
            variables[key], entries[key] = var, ent
        form.columnconfigure(1, weight=1)

        def fill_total(_e=None):
            if not variables["total"].get().strip():
                text = total_exposure_text(variables["sub_length"].get(), variables["sub_count"].get())
                if text:
                    variables["total"].set(text)
        entries["sub_length"].bind("<FocusOut>", fill_total)
        entries["sub_count"].bind("<FocusOut>", fill_total)

        tk.Label(win, text="Notes", bg=BG, fg=BLUE,
                 font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=18, pady=(12, 2))
        box = tk.Frame(win, bg=BG)
        box.pack(padx=18, fill="both")
        notes = tk.Text(box, width=58, height=8, wrap="word", relief="solid", bd=1,
                        font=("TkDefaultFont", 10), undo=True)
        scroll = tk.Scrollbar(box, command=notes.yview)
        notes.configure(yscrollcommand=scroll.set)
        notes.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        notes.insert("1.0", data.get("notes", ""))

        tk.Label(win, text=f"Saved as a text file next to the photo:\n{path}", bg=BG, fg="#777",
                 justify="left", wraplength=470).pack(anchor="w", padx=18, pady=(10, 0))

        def save(_e=None):
            fill_total()
            new = {key: variables[key].get().strip() for key, _ in LOG_FIELDS}
            new["notes"] = notes.get("1.0", "end").strip("\n")
            try:
                saved = write_log(n, new)
            except OSError as ex:
                messagebox.showerror("Couldn't save the log", str(ex), parent=win)
                return
            equipment = {k: new[k] for k in EQUIPMENT_KEYS if new[k]}
            if equipment:
                self.settings["last_equipment"] = equipment
                self.save_settings()
            win.destroy()
            self.status_var.set(f"Log saved for {LABEL[n]}: {saved}" if saved
                                else f"Log for {LABEL[n]} was empty, so nothing was saved.")

        row = tk.Frame(win, bg=BG)
        row.pack(fill="x", padx=18, pady=(12, 16))
        Btn(row, text="Save", command=save, bg=BLUE, fg="white", activebackground="#4148d6",
            activeforeground="white", relief="flat", bd=0, padx=20, pady=6,
            font=("TkDefaultFont", 10, "bold")).pack(side="right")
        Btn(row, text="Cancel", command=win.destroy, bg="#dcdce4", fg="#111", activebackground="#cdcdd8",
            relief="flat", bd=0, padx=16, pady=6).pack(side="right", padx=8)
        Btn(row, text="Open folder", command=lambda: open_path(ORIG_DIR), bg="#dcdce4", fg="#111",
            activebackground="#cdcdd8", relief="flat", bd=0, padx=12, pady=6).pack(side="left")

        win.bind("<Escape>", lambda e: win.destroy())
        win.bind(f"<{MOD}-s>", save)
        center_on(win, self.root)
        win.grab_set()
        entries["date"].focus_set()
        self._log_win = win

    # ---------- other actions ----------
    def clear_all(self):
        have = filled()
        if not have:
            messagebox.showinfo("Nothing to clear", "The chart has no photos yet.")
            return
        if not messagebox.askyesno(
                "Clear all photos?",
                f"Remove all {len(have)} photos from the chart and start over?\n\n"
                "Your original photo files are not touched - only the app's copies are removed. "
                "Any logs / notes you saved are kept.\n\n"
                f"Changed your mind afterwards? Click Undo ({MOD_NAME}+Z).",
                icon="warning"):
            return
        self.undo_log.begin(f"clearing {len(have)} photos")
        try:
            for n in have:
                remove_photo(n, self.undo_log)
            for p in list(ORIG_DIR.iterdir()):
                if p.is_file() and not p.name.endswith(LOG_SUFFIX):
                    self.undo_log.park(p)
        except OSError as ex:
            messagebox.showerror("Couldn't clear everything", str(ex))
        self.update_undo_button()
        self.rebuild()
        self.status_var.set(f"Chart cleared. Click Undo ({MOD_NAME}+Z) to put the photos back.")

    def edit_title(self):
        t = simpledialog.askstring("Chart title", "Title shown at the top of the chart:",
                                   initialvalue=self.settings.get("title", ""), parent=self.root)
        if t is not None:
            self.settings["title"] = t.strip()
            self.save_settings()
            self.rebuild()

    def export(self):
        f = filedialog.asksaveasfilename(
            title="Export chart", defaultextension=".png", initialfile=CAT.CHART_FILE_NAME,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("TIFF", "*.tif")])
        if not f:
            return
        try:
            if f.lower().endswith((".jpg", ".jpeg")):
                self.chart.save(f, quality=95, subsampling=0)
            else:
                self.chart.save(f)
            self.status_var.set(f"Exported to {f}")
        except Exception as ex:
            messagebox.showerror("Export failed", str(ex))

    def run(self):
        self.root.mainloop()


# --------------------------------------------------------------------------
# Adjust framing: drag to move, scroll (or the slider) to zoom
# --------------------------------------------------------------------------
class FramingDialog:
    VIEW_W, VIEW_H = 640, 470

    def __init__(self, app, n, full):
        self.app, self.n, self.full = app, n, full
        self.root = app.root
        self.zmin = fit_zoom(full.width, full.height)
        _, self.crop = crop_box(full.width, full.height, read_crop(n))

        # Display copy: big enough to fill the view when fully zoomed out
        aspect = CELL_W / CELL_H
        fw = max(full.width, full.height * aspect)            # width of the "whole photo" box
        fh = fw / aspect
        self.k = min((self.VIEW_W - 40) / fw, (self.VIEW_H - 40) / fh)   # photo px -> screen px
        dw, dh = max(1, round(full.width * self.k)), max(1, round(full.height * self.k))
        self.disp = full.resize((dw, dh), Image.LANCZOS)
        self.dim = ImageEnhance.Brightness(self.disp).enhance(0.32)
        self.ix, self.iy = (self.VIEW_W - dw) // 2, (self.VIEW_H - dh) // 2   # photo's place in the view

        win = self.win = tk.Toplevel(self.root)
        win.title(f"Adjust framing - {LABEL[n]}")
        win.configure(bg=LIGHT)
        win.resizable(False, False)
        win.transient(self.root)
        tk.Label(win, text=f"{LABEL[n]}  ·  {NAMES[n]}", bg=LIGHT, fg="#111",
                 font=("TkDefaultFont", 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w",
                                                          padx=18, pady=(14, 0))
        tk.Label(win, text="Drag the bright box to move it. Scroll, or use the slider, to zoom. "
                           "The bright part is what shows on the chart.",
                 bg=LIGHT, fg="#555").grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(2, 8))
        self.cv = tk.Canvas(win, width=self.VIEW_W, height=self.VIEW_H, bg="#000", highlightthickness=0,
                            cursor="fleur")
        self.cv.grid(row=2, column=0, padx=(18, 10), sticky="n")

        side = tk.Frame(win, bg=LIGHT)
        side.grid(row=2, column=1, padx=(0, 18), sticky="n")
        tk.Label(side, text="On the chart", bg=LIGHT, fg=BLUE,
                 font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        pw = 240
        self.pv_size = (pw, round(pw * CELL_H / CELL_W))
        self.pv = tk.Label(side, bg="#000", bd=1, relief="solid")
        self.pv.pack(pady=(4, 14))
        tk.Label(side, text="Zoom", bg=LIGHT, fg=BLUE, font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.zoom_var = tk.DoubleVar(value=self.z_to_slider(self.crop[2]))
        tk.Scale(side, from_=0, to=100, orient="horizontal", showvalue=False, length=pw,
                 variable=self.zoom_var, command=lambda v: self.set_zoom(self.slider_to_z(float(v))),
                 bg=LIGHT, highlightthickness=0, troughcolor="#dcdce4").pack(anchor="w")
        Btn(side, text="Show whole photo", command=self.fit_whole, bg="#dcdce4", fg="#111",
            activebackground="#cdcdd8", relief="flat", bd=0, padx=12, pady=5).pack(fill="x", pady=(12, 4))
        Btn(side, text="Fill the square (default)", command=self.reset, bg="#dcdce4", fg="#111",
            activebackground="#cdcdd8", relief="flat", bd=0, padx=12, pady=5).pack(fill="x", pady=4)

        row = tk.Frame(win, bg=LIGHT)
        row.grid(row=3, column=0, columnspan=2, sticky="we", padx=18, pady=(12, 16))
        Btn(row, text="Save", command=self.save, bg=BLUE, fg="white", activebackground="#4148d6",
            activeforeground="white", relief="flat", bd=0, padx=22, pady=6,
            font=("TkDefaultFont", 10, "bold")).pack(side="right")
        Btn(row, text="Cancel", command=win.destroy, bg="#dcdce4", fg="#111", activebackground="#cdcdd8",
            relief="flat", bd=0, padx=16, pady=6).pack(side="right", padx=8)

        self.cv.bind("<ButtonPress-1>", self.press)
        self.cv.bind("<B1-Motion>", self.drag)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.cv.bind(seq, self.wheel)
        for key, dx, dy in (("Left", -1, 0), ("Right", 1, 0), ("Up", 0, -1), ("Down", 0, 1)):
            win.bind(f"<{key}>", lambda e, dx=dx, dy=dy: self.nudge(dx, dy))
        win.bind("<plus>", lambda e: self.set_zoom(self.crop[2] * 1.1))
        win.bind("<equal>", lambda e: self.set_zoom(self.crop[2] * 1.1))
        win.bind("<minus>", lambda e: self.set_zoom(self.crop[2] / 1.1))
        win.bind("<Escape>", lambda e: win.destroy())
        win.bind("<Return>", lambda e: self.save())
        self.redraw()
        center_on(win, self.root)
        win.grab_set()
        win.focus_set()

    # zoom slider is logarithmic: 0 = whole photo, 100 = MAX_ZOOM
    def z_to_slider(self, z):
        if MAX_ZOOM <= self.zmin:
            return 0
        return 100 * math.log(z / self.zmin) / math.log(MAX_ZOOM / self.zmin)

    def slider_to_z(self, s):
        return self.zmin * (MAX_ZOOM / self.zmin) ** (s / 100)

    def set_crop(self, cx, cy, z, sync=True):
        _, self.crop = crop_box(self.full.width, self.full.height, (cx, cy, z))
        if sync:
            self.zoom_var.set(self.z_to_slider(self.crop[2]))
        self.redraw()

    def set_zoom(self, z):
        if getattr(self, "_zooming", False):
            return
        self._zooming = True
        try:
            self.set_crop(self.crop[0], self.crop[1], z, sync=False)
            self.zoom_var.set(self.z_to_slider(self.crop[2]))
        finally:
            self._zooming = False

    def fit_whole(self):
        self.set_crop(0.5, 0.5, self.zmin)

    def reset(self):
        self.set_crop(*DEFAULT_CROP)

    def press(self, e):
        self._drag = (e.x, e.y, self.crop)

    def drag(self, e):
        x0, y0, (cx, cy, z) = self._drag
        dx = (e.x - x0) / self.k / self.full.width
        dy = (e.y - y0) / self.k / self.full.height
        self.set_crop(cx + dx, cy + dy, z)        # the box follows the mouse

    def nudge(self, dx, dy):
        (x0, y0, x1, y1), _ = crop_box(self.full.width, self.full.height, self.crop)
        step = 0.04
        self.set_crop(self.crop[0] + dx * step * (x1 - x0) / self.full.width,
                      self.crop[1] + dy * step * (y1 - y0) / self.full.height, self.crop[2])

    def wheel(self, e):
        s = wheel_steps(e)
        if s:
            self.set_zoom(self.crop[2] * (1.12 if s > 0 else 1 / 1.12))

    def redraw(self):
        (x0, y0, x1, y1), _ = crop_box(self.full.width, self.full.height, self.crop)
        k = self.k
        view = Image.new("RGB", (self.VIEW_W, self.VIEW_H), (0, 0, 0))
        view.paste(self.dim, (self.ix, self.iy))
        bx0, by0 = self.ix + x0 * k, self.iy + y0 * k
        bx1, by1 = self.ix + x1 * k, self.iy + y1 * k
        inner = (max(0, round(x0 * k)), max(0, round(y0 * k)),
                 min(self.disp.width, round(x1 * k)), min(self.disp.height, round(y1 * k)))
        if inner[2] > inner[0] and inner[3] > inner[1]:
            view.paste(self.disp.crop(inner), (self.ix + inner[0], self.iy + inner[1]))
        self._view = ImageTk.PhotoImage(view)
        self.cv.delete("all")
        self.cv.create_image(0, 0, anchor="nw", image=self._view)
        self.cv.create_rectangle(bx0, by0, bx1, by1, outline="#4da3ff", width=2)
        self._pv = ImageTk.PhotoImage(make_tile(self.disp, self.crop, self.pv_size))
        self.pv.config(image=self._pv)

    def save(self):
        crop = tuple(round(v, 5) for v in self.crop)
        if all(abs(a - b) < 1e-4 for a, b in zip(crop, DEFAULT_CROP)):
            crop = DEFAULT_CROP
        self.win.destroy()
        self.app.save_framing(self.n, self.full, crop)


def main(catalog):
    configure(catalog)
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # crisp on HiDPI screens
        except Exception:
            pass
    App().run()
