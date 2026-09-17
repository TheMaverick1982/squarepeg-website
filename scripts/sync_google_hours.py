#!/usr/bin/env python3
"""
Copy each location's hours from its Google Business Profile into data/hours_google.json.

Google is the one place to edit hours. This script runs every night on GitHub
(.github/workflows/sync-hours.yml). When anything changed, the workflow rebuilds the
site and pushes, and Vercel redeploys.

  GOOGLE_PLACES_API_KEY=... python3 scripts/sync_google_hours.py
  python3 scripts/sync_google_hours.py --mock tests/google_mock.json   (offline test)

Needs: data/google_places.json  ({"glastonbury-ct": "ChIJ...", ...}); see find_google_place_ids.py.
Uses Google Places API (New), Place Details. Standard library only.

Safety rules
- A location Google can't return (error, no hours listed) keeps its last known hours.
- If every lookup fails, the script exits with an error so GitHub emails you.
- A location Google marks as closed is flagged as a warning; its hours are not removed.
"""
import json, os, sys, urllib.request, urllib.error
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))
from content import LOCATIONS, DAYS  # noqa: E402

PLACES_FILE = ROOT / "data" / "google_places.json"
OUT_FILE = ROOT / "data" / "hours_google.json"
FIELDS = "id,displayName,formattedAddress,businessStatus,regularOpeningHours,currentOpeningHours"
GDAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]   # Google: 0 = Sunday


def hhmm(pt):
    return f"{pt.get('hour', 0):02d}:{pt.get('minute', 0):02d}"


def weekly(periods, warn):
    """Google periods -> {"Mon": ["11:30","21:00"] | None, ...}. One open window per day."""
    out = {d: None for d in DAYS}
    if len(periods) == 1 and "close" not in periods[0]:
        return {d: ["00:00", "00:00"] for d in DAYS}          # open 24/7
    for p in periods:
        o, c = p.get("open"), p.get("close")
        if not o:
            continue
        day = GDAY[o["day"]]
        close = hhmm(c) if c else "00:00"
        if out[day]:
            # Split hours (e.g. lunch + dinner): the site shows one window per day,
            # so use first open to last close and flag it.
            warn(f"{day} has more than one opening window on Google; showing {out[day][0]}–{close}")
            out[day] = [out[day][0], close]
        else:
            out[day] = [hhmm(o), close]
    return out


def special_days(place, regular):
    """Holiday / special hours in Google's next-7-days window that differ from the weekly hours."""
    cur = place.get("currentOpeningHours") or {}
    out = {}
    for sd in cur.get("specialDays", []):
        d = sd.get("date") or {}
        try:
            dt = date(d["year"], d["month"], d["day"])
        except (KeyError, ValueError):
            continue
        iso = dt.isoformat()
        wins = []
        for p in cur.get("periods", []):
            o = p.get("open") or {}
            od = o.get("date") or {}
            if (od.get("year"), od.get("month"), od.get("day")) == (dt.year, dt.month, dt.day):
                c = p.get("close")
                wins.append([hhmm(o), hhmm(c) if c else "00:00"])
        hours = [wins[0][0], wins[-1][1]] if wins else None
        if hours != regular[DAYS[dt.weekday()]]:
            out[iso] = hours
    return out


def fetch(place_id, key):
    req = urllib.request.Request(
        f"https://places.googleapis.com/v1/places/{place_id}",
        headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELDS})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fmt(v):
    return "Closed" if not v else f"{v[0]}–{v[1]}"


def not_ready(msg):
    print(f"::notice::Hours sync is not set up yet: {msg} The website keeps the hours in data/content.py.")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write("changed=false\n")


def main():
    args = sys.argv[1:]
    mock = json.loads(Path(args[args.index("--mock") + 1]).read_text()) if "--mock" in args else None
    key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    places = json.loads(PLACES_FILE.read_text()) if PLACES_FILE.exists() else {}
    places = {k: v for k, v in places.items() if v and not k.startswith("_")}
    # Not set up yet: skip quietly (no nightly failure emails). See HOURS_SYNC.md.
    if not mock and not key:
        return not_ready("GOOGLE_PLACES_API_KEY is not set yet (GitHub > Settings > Secrets and variables > Actions).")
    if not places:
        return not_ready("data/google_places.json has no place IDs yet. Run the 'Find Google place IDs' workflow.")

    old = json.loads(OUT_FILE.read_text()) if OUT_FILE.exists() else {"locations": {}}
    new = {"_note": "Written by scripts/sync_google_hours.py from Google Business Profile. Don't edit by hand; change hours in Google.",
           "locations": {}}
    names = {l["slug"]: l["name"] for l in LOCATIONS}
    typed = {l["slug"]: {d: (list(v) if v else None) for d, v in l["hours"].items()} for l in LOCATIONS}
    warnings, changes, ok, failed = [], [], 0, 0

    for slug in [l["slug"] for l in LOCATIONS]:
        prev = old.get("locations", {}).get(slug)
        pid = places.get(slug)
        if not pid:
            warnings.append(f"{names[slug]}: no Google place ID in data/google_places.json (using the hours in content.py)")
            continue
        def warn(msg, _n=names[slug]):
            warnings.append(f"{_n}: {msg}")
        try:
            place = mock[pid] if mock is not None else fetch(pid, key)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            warn(f"Google returned HTTP {e.code}; kept last known hours. {body}")
            failed += 1
            if prev: new["locations"][slug] = prev
            continue
        except Exception as e:  # network, timeout, bad mock
            warn(f"lookup failed ({e}); kept last known hours")
            failed += 1
            if prev: new["locations"][slug] = prev
            continue

        status = place.get("businessStatus", "OPERATIONAL")
        if status != "OPERATIONAL":
            warn(f"Google lists this location as {status}. Check the Google Business Profile.")
        periods = (place.get("regularOpeningHours") or {}).get("periods")
        if not periods:
            warn("Google has no regular hours for this location; kept last known hours")
            failed += 1
            if prev: new["locations"][slug] = prev
            continue
        ok += 1
        hours = weekly(periods, warn)
        entry = {"place_id": pid, "google_name": (place.get("displayName") or {}).get("text", ""),
                 "hours": hours, "special": special_days(place, hours)}
        new["locations"][slug] = entry

        before = (prev or {}).get("hours")
        if not before:
            changes.append(f"{names[slug]}: now using Google hours")
            before = typed[slug]   # first sync: show where Google differs from the hours typed into the site
        for d in DAYS:
            if before.get(d) != hours[d]:
                changes.append(f"{names[slug]} {d}: {fmt(before.get(d))} → {fmt(hours[d])}")
        was = (prev or {}).get("special") or {}
        for iso, v in entry["special"].items():
            if was.get(iso, "missing") != v:
                changes.append(f"{names[slug]} {iso}: special hours {fmt(v)}")
        for iso in was:
            if iso not in entry["special"]:
                changes.append(f"{names[slug]} {iso}: special hours removed")

    if ok == 0 and failed:
        for w in warnings:
            print(f"::error::{w}")
        sys.exit("Every Google lookup failed. Nothing was changed.")

    changed = json.dumps(new.get("locations"), sort_keys=True) != json.dumps(old.get("locations"), sort_keys=True)
    if changed:
        OUT_FILE.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n")

    for w in warnings:
        print(f"::warning::{w}")
    print(f"Checked {ok + failed} locations: {ok} from Google, {failed} kept as before.")
    print("Changes:\n  " + "\n  ".join(changes) if changes else "No hour changes.")

    summary = ["## Google hours sync", f"Checked {ok + failed} locations ({ok} updated from Google, {failed} kept as before).", ""]
    summary += (["**Changes**", ""] + [f"- {c}" for c in changes]) if changes else ["No hour changes."]
    if warnings:
        summary += ["", "**Check these**", ""] + [f"- {w}" for w in warnings]
    msg = "Update hours from Google\n\n" + "\n".join(f"- {c}" for c in changes)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("\n".join(summary) + "\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
    (Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "hours-commit-msg.txt").write_text(msg + "\n")


if __name__ == "__main__":
    main()
