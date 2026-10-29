#!/usr/bin/env python3
"""Herschel Chart Builder - created by SaltyPogue  ·  www.saltypogue.com

Start file for the Herschel app. The app itself is chart_core.py (shared by all seven
apps); the Herschel catalog data and file-name matching are in catalogs/herschel.py.

Run it with:  python herschel_chart.py      (needs: pip install pillow tkinterdnd2 numpy tifffile)
"""
import chart_core
from catalogs import herschel as catalog

if __name__ == "__main__":
    chart_core.main(catalog)
