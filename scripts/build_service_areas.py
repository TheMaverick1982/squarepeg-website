#!/usr/bin/env python3
"""
Build data/service_areas.json: every town within RADIUS miles (straight line) of each store.

Run this only when a location is added or moved; the site build reads the saved JSON.

  pip install zipcodes            # US ZIP code list with postal town names
  npm pack cities.json && tar xzf cities.json-*.tgz   # GeoNames places (CC BY 4.0), for accurate town centers
  python3 scripts/build_service_areas.py [path/to/package/cities.json]

Town names come from USPS postal town names (what people put in their address), so
villages like Mystic, Uncasville and Plantsville are included. Coordinates use the
GeoNames town center when available, otherwise the average of the town's ZIP centers.
Distances are straight-line, so the site shows them as bands (under 5, 5-10, 10-15 mi).
"""
import json, math, sys, collections
from pathlib import Path

import zipcodes

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))
from content import LOCATIONS  # noqa: E402

RADIUS = 15.0
STATES = ("CT", "FL", "RI", "MA", "NY")
OUT = ROOT / "data" / "service_areas.json"

# Postal names -> the name people use. None = skip (duplicate or not a real place name).
RENAME = {
    ("Vernon Rockville", "CT"): "Vernon",
    ("Storrs Mansfield", "CT"): "Mansfield",
    ("Lake Worth", "FL"): None,             # same area as Lake Worth Beach
    ("Greenacres City", "FL"): "Greenacres",
    ("West Delray Beach", "FL"): None,      # part of the Delray Beach area
    ("Green Acres", "FL"): None,            # = Greenacres
    ("Lake Clarke", "FL"): None,            # = Lake Clarke Shores
}
ABBREV = (" Bch", " Pt", " Pnes", " Gdns", " Plm", "Vlg ", " Wellingtn", "Laud ", "Sw ", "N ", "W ", "Halndle", "Hallandle", "Ft ")


def miles(a, b, c, d):
    r = math.pi / 180
    x = math.sin((c - a) * r / 2) ** 2 + math.cos(a * r) * math.cos(c * r) * math.sin((d - b) * r / 2) ** 2
    return 2 * 3958.8 * math.asin(math.sqrt(x))


def main():
    geo_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("package/cities.json")
    geonames = {}
    if geo_path.exists():
        for c in json.loads(geo_path.read_text()):
            if c["country"] == "US" and c["admin1"] in STATES:
                geonames.setdefault((c["name"], c["admin1"]), (float(c["lat"]), float(c["lng"])))
    else:
        print(f"! {geo_path} not found: using ZIP centers only (less accurate)")

    pts = collections.defaultdict(list)
    for st in STATES:
        for z in zipcodes.filter_by(state=st):
            if z["zip_code_type"] != "STANDARD" or not z["active"] or not z["lat"]:
                continue
            ll = (float(z["lat"]), float(z["long"]))
            names = [z["city"].title()]
            if st == "FL":  # FL ZIPs cover several cities; keep their full "acceptable" names
                names += [n for n in z["acceptable_cities"] if not any(a in n + " " for a in ABBREV)]
            for n in names:
                if n.startswith("Village Of "):   # duplicates of "Golf", "Palm Springs", ...
                    continue
                key = (n, st)
                if key in RENAME:
                    if RENAME[key] is None:
                        continue
                    key = (RENAME[key], st)
                pts[key].append(ll)

    towns = {}
    for key, ll in pts.items():
        towns[key] = geonames.get(key) or (sum(p[0] for p in ll) / len(ll), sum(p[1] for p in ll) / len(ll))

    out = {"_note": ("Towns within 15 miles (straight line) of each store. Built by scripts/build_service_areas.py "
                     "from USPS town names (zipcodes package) and GeoNames town centers (geonames.org, CC BY 4.0)."),
           "radius_miles": RADIUS, "locations": {}}
    for l in LOCATIONS:
        own = {l["city"].lower()}
        rows = []
        for (name, st), (lat, lng) in towns.items():
            if name.lower() in own and st == l["state"]:
                continue
            d = miles(l["lat"], l["lng"], lat, lng)
            if d <= RADIUS:
                rows.append({"name": name, "state": st, "mi": round(d, 1)})
        rows.sort(key=lambda r: (r["mi"], r["name"]))
        out["locations"][l["slug"]] = rows
        print(f"{l['name']}: {len(rows)} towns")
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
