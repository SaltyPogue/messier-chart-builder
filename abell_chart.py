#!/usr/bin/env python3
"""Abell Chart Builder - created by SaltyPogue  ·  www.saltypogue.com

Start file for the Abell app. The app itself is chart_core.py (shared by all seven
apps); the Abell catalog data and file-name matching are in catalogs/abell.py.

Run it with:  python abell_chart.py      (needs: pip install pillow tkinterdnd2 numpy tifffile)
"""
import chart_core
from catalogs import abell as catalog

if __name__ == "__main__":
    chart_core.main(catalog)
