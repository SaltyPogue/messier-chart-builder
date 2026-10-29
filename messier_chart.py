#!/usr/bin/env python3
"""Messier Chart Builder - created by SaltyPogue  ·  www.saltypogue.com

Start file for the Messier app. The app itself is chart_core.py (shared by all seven
apps); the Messier catalog data and file-name matching are in catalogs/messier.py.

Run it with:  python messier_chart.py      (needs: pip install pillow tkinterdnd2 numpy tifffile)
"""
import chart_core
from catalogs import messier as catalog

if __name__ == "__main__":
    chart_core.main(catalog)
