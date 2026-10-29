#!/usr/bin/env python3
"""vdB Chart Builder - created by SaltyPogue  ·  www.saltypogue.com

Start file for the vdB app. The app itself is chart_core.py (shared by all seven
apps); the vdB catalog data and file-name matching are in catalogs/vdb.py.

Run it with:  python vdb_chart.py      (needs: pip install pillow tkinterdnd2 numpy tifffile)
"""
import chart_core
from catalogs import vdb as catalog

if __name__ == "__main__":
    chart_core.main(catalog)
