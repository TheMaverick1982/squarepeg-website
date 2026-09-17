#!/usr/bin/env python3
"""
Look up each location's Google place ID and save it to data/google_places.json.

Run once (GitHub > Actions > "Find Google place IDs" > Run workflow), then check the
summary: every location should match the right address. Existing IDs are kept unless
you run it with --force.

  GOOGLE_PLACES_API_KEY=... python3 scripts/find_google_place_ids.py [--force]

Uses Google Places API (New), Text Search. Standard library only.
"""
import json, os, re, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))
from content import LOCATIONS, DAYS  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
from sync_google_hours import weekly, fmt  # noqa: E402

PLACES_FILE = ROOT / "data" / "google_places.json"


def search(q, key):
    req = urllib.request.Request(
        "https://places.googleapis.com/v1/places:searchText",
        data=json.dumps({"textQuery": q, "pageSize": 5}).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key,
                 "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.businessStatus,places.regularOpeningHours"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("places", [])


def main():
    key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    if not key:
        sys.exit("GOOGLE_PLACES_API_KEY is not set.")
    force = "--force" in sys.argv
    saved = json.loads(PLACES_FILE.read_text()) if PLACES_FILE.exists() else {}
    rows = ["| Location | Match on Google | Address on Google | Status |", "|---|---|---|---|"]
    diffs = []
    for l in LOCATIONS:
        if saved.get(l["slug"]) and not force:
            rows.append(f"| {l['name']} | (already saved) | `{saved[l['slug']]}` | kept |")
            continue
        q = f"Square Peg Pizzeria, {l['street']}, {l['city']}, {l['state']} {l['zip']}"
        try:
            results = search(q, key)
        except urllib.error.HTTPError as e:
            sys.exit(f"Google returned HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:400]}")
        num = re.match(r"\d+", l["street"])
        pick, note = None, "NOT FOUND, add by hand"
        for p in results:
            name = (p.get("displayName") or {}).get("text", "")
            addr = p.get("formattedAddress", "")
            if "square peg" in name.lower() and (l["city"].lower() in addr.lower() or (num and addr.startswith(num.group()))):
                pick, note = p, "matched"
                break
        if not pick and results:
            pick, note = results[0], "CHECK: best guess"
        if pick:
            saved[l["slug"]] = pick["id"]
            rows.append(f"| {l['name']} | {(pick.get('displayName') or {}).get('text', '')} | {pick.get('formattedAddress', '')} | {note} ({pick.get('businessStatus', '')}) |")
            periods = (pick.get("regularOpeningHours") or {}).get("periods")
            if not periods:
                diffs.append(f"- **{l['name']}**: no hours listed on Google")
            else:
                g = weekly(periods, lambda m, n=l["name"]: diffs.append(f"- **{n}**: {m}"))
                for d in DAYS:
                    site = list(l["hours"][d]) if l["hours"][d] else None
                    if site != g[d]:
                        diffs.append(f"- **{l['name']} {d}**: website {fmt(site)}, Google {fmt(g[d])}")
        else:
            saved.setdefault(l["slug"], "")
            rows.append(f"| {l['name']} | — | — | {note} |")

    ordered = {"_note": "Google place ID for each location (slug from data/content.py). Used by scripts/sync_google_hours.py."}
    ordered.update({l["slug"]: saved.get(l["slug"], "") for l in LOCATIONS})
    PLACES_FILE.write_text(json.dumps(ordered, indent=2) + "\n")
    out = "## Google place IDs\n\nCheck that each row is the right store.\n\n" + "\n".join(rows) + "\n"
    out += ("\n## Hours: website vs Google\n\nWhen the sync is turned on, the website will switch to the Google hours below. "
            "Fix anything wrong in Google Business Profile first.\n\n" + ("\n".join(diffs) if diffs else "All hours already match.") + "\n")
    print(out)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(out)


if __name__ == "__main__":
    main()
