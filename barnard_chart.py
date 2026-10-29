#!/usr/bin/env python3
"""Barnard Chart Builder - created by SaltyPogue  ·  www.saltypogue.com

Start file for the Barnard app. The app itself is chart_core.py (shared by all seven
apps); the Barnard catalog data and file-name matching are in catalogs/barnard.py.

Run it with:  python barnard_chart.py      (needs: pip install pillow tkinterdnd2 numpy tifffile)
"""
import chart_core
from catalogs import barnard as catalog

if __name__ == "__main__":
    chart_core.main(catalog)
