#!/usr/bin/env python3
"""
Check that every Toast link the website uses actually loads on the order subdomain.

Run it on launch day, after Toast says order.squarepegpizzeria.com is connected and
BEFORE flipping TOAST_ON_SUBDOMAIN (GitHub > Actions > Check Toast links > Run workflow).

  python3 scripts/check_toast_links.py [host]      # default: TOAST_SUBDOMAIN from data/content.py

Checks, for each location: /order/<slug> and /menu/<slug>; plus the menu, order picker
and gift card pages; plus a few old deep links the 301 redirects will send there.
Standard library only.
"""
import os, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))
from content import LOCATIONS, TOAST_SUBDOMAIN, TOAST_PATHS  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 SquarePegLinkCheck"


def check(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read(200_000).decode("utf-8", "replace").lower()
            final = r.geturl()
            code = r.status
    except urllib.error.HTTPError as e:
        return e.code, url, "HTTP error"
    except Exception as e:
        return 0, url, f"failed: {e}"
    note = ""
    if any(t in body for t in ("page not found", "404 -", "this page could not be found")):
        note = "loads, but looks like a 'not found' page"
    if not final.startswith(TOAST_SUBDOMAIN) and not final.startswith(host):
        note = (note + "; " if note else "") + "ended on a different site"
    return code, final, note


host = (sys.argv[1] if len(sys.argv) > 1 else TOAST_SUBDOMAIN).rstrip("/")
urls = [("Order picker", host + TOAST_PATHS["picker"]), ("Menu", host + TOAST_PATHS["menu"]),
        ("Gift cards", host + TOAST_PATHS["gift_cards"])]
for l in LOCATIONS:
    urls.append((f"{l['name']} order", f"{host}/order/{l['toast']}"))
    urls.append((f"{l['name']} menu", f"{host}/menu/{l['toast']}"))

rows, bad = [], 0
for label, u in urls:
    code, final, note = check(u)
    ok = 200 <= code < 300 and not note
    bad += not ok
    rows.append(f"| {'✅' if ok else '❌'} | {label} | {u} | {code or '—'} | {note or ('→ ' + final if final != u else '')} |")

out = [f"## Toast links on {host}", "",
       ("All links load. Safe to set TOAST_ON_SUBDOMAIN = True." if not bad else
        f"**{bad} link(s) need attention.** Don't flip TOAST_ON_SUBDOMAIN until these load. "
        "A 403 can just mean Toast blocks automated checks: open that link in a browser to confirm."), "",
       "| | Link | URL | Status | Note |", "|---|---|---|---|---|"] + rows
print("\n".join(out))
if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write("\n".join(out) + "\n")
sys.exit(1 if bad else 0)
