#!/usr/bin/env python3
"""
fetch_bathymetry.py — Download NOAA ENC bathymetry for the race-night box and
bake it into bathymetry.json for race-night.html to load statically.

Charts change rarely, so this is run by hand — there is no scheduled workflow
for it (unlike fetch_lnm.py).

Source: NOAA ENC Direct to GIS, harbour-scale ENC data.
  https://gis.charttools.noaa.gov/arcgis/rest/services/encdirect/enc_harbour/MapServer
NOAA's raster (RNC) tile service was retired in Jan 2025; this vector service
is the live replacement.

Usage:
  python3 scripts/fetch_bathymetry.py

Requirements: requests  (see scripts/requirements.txt)
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests

# ── Config ─────────────────────────────────────────────────────────────────────

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "bathymetry.json")

BASE = ("https://gis.charttools.noaa.gov/arcgis/rest/services/"
        "encdirect/enc_harbour/MapServer")

# Race-night box: Y-A / G1 / G11 and the surrounding flats and channels,
# padded so the 1nm course never runs off the edge of the data.
BBOX = "-74.065,40.625,-74.010,40.695"

# ~9m of geometry simplification. Enough to cut the depth areas from 1.6MB to
# ~160KB without visibly moving a contour at the zooms this page uses.
SIMPLIFY = 0.00008

COORD_PRECISION = 5   # ~1m — well beyond what the source data justifies

# ENC layer ids, and the one attribute worth keeping from each.
#   DRVAL1/DRVAL2 — shallow/deep bound of a depth area, metres
#   VALDCO        — value of a depth contour, metres
#   Z             — sounding depth, metres
LAYERS = [
    ("depth_areas", 227, "DRVAL1,DRVAL2"),
    ("contours",    104, "VALDCO"),
    ("soundings",    76, "Z"),
]

TIMEOUT = 120

# ── Fetch ──────────────────────────────────────────────────────────────────────


def fetch_layer(layer_id, out_fields):
    """Query one ENC layer over BBOX and return its GeoJSON features."""
    params = {
        "geometry": BBOX,
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "outSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "returnGeometry": "true",
        "maxAllowableOffset": SIMPLIFY,
        "f": "geojson",
    }
    r = requests.get(f"{BASE}/{layer_id}/query", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()

    # ArcGIS reports failures with a 200 and an error body.
    if "error" in data:
        raise RuntimeError(f"layer {layer_id}: {data['error']}")

    return data.get("features", [])


def round_coords(obj):
    """Recursively round every coordinate to COORD_PRECISION decimal places."""
    if isinstance(obj, list):
        return [round_coords(x) for x in obj]
    if isinstance(obj, float):
        return round(obj, COORD_PRECISION)
    return obj


def clean(features):
    """Strip ArcGIS bookkeeping and shrink coordinates in place."""
    out = []
    for f in features:
        geom = f.get("geometry")
        if not geom or not geom.get("coordinates"):
            continue
        geom["coordinates"] = round_coords(geom["coordinates"])
        props = {k: v for k, v in (f.get("properties") or {}).items()
                 if v is not None}
        out.append({"type": "Feature", "geometry": geom, "properties": props})
    return out


def main():
    result = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "NOAA ENC Direct to GIS — enc_harbour",
        "bbox": [float(v) for v in BBOX.split(",")],
        "units": "meters",
    }

    for name, layer_id, fields in LAYERS:
        print(f"Fetching {name} (layer {layer_id})…", flush=True)
        try:
            features = clean(fetch_layer(layer_id, fields))
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            return 1
        if not features:
            print(f"  FAILED: no features returned for {name}", file=sys.stderr)
            return 1
        print(f"  {len(features)} features")
        result[name] = {"type": "FeatureCollection", "features": features}

    with open(OUTPUT_FILE, "w") as fh:
        json.dump(result, fh, separators=(",", ":"))

    size = os.path.getsize(OUTPUT_FILE)
    print(f"\nWrote {os.path.normpath(OUTPUT_FILE)} — {size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
