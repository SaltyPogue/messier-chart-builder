#!/usr/bin/env python3
"""Caldwell Chart Builder - created by SaltyPogue  ·  www.saltypogue.com

Start file for the Caldwell app. The app itself is chart_core.py (shared by all seven
apps); the Caldwell catalog data and file-name matching are in catalogs/caldwell.py.

Run it with:  python caldwell_chart.py      (needs: pip install pillow tkinterdnd2 numpy tifffile)
"""
import chart_core
from catalogs import caldwell as catalog

if __name__ == "__main__":
    chart_core.main(catalog)
