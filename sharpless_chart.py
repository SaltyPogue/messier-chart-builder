#!/usr/bin/env python3
"""Sharpless Chart Builder - created by SaltyPogue  ·  www.saltypogue.com

Start file for the Sharpless app. The app itself is chart_core.py (shared by all seven
apps); the Sharpless catalog data and file-name matching are in catalogs/sharpless.py.

Run it with:  python sharpless_chart.py      (needs: pip install pillow tkinterdnd2 numpy tifffile)
"""
import chart_core
from catalogs import sharpless as catalog

if __name__ == "__main__":
    chart_core.main(catalog)
