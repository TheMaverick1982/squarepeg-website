#!/usr/bin/env python3
"""
Daily health check for the live site: pages load, redirects work, security headers are set.

Runs on GitHub (.github/workflows/site-health.yml) every morning, and on demand.
If anything fails, the workflow fails and GitHub emails you.

  python3 scripts/check_site_health.py https://squarepegpizzeria.com
"""
import json, os, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))
from content import LOCATIONS  # noqa: E402

UA = "SquarePegHealthCheck/1.0 (+https://squarepegpizzeria.com)"
MUST_HEADERS = {
    "x-content-type-options": "nosniff",
    "referrer-policy": None,
    "content-security-policy": None,
    "strict-transport-security": None,
}
REDIRECTS = [("/monthly-deals", "/deals/"), ("/tuesday-charity-night", "/fundraisers/"),
             ("/events/trivia-night", "/entertainment/"), ("/gift-cards", "gift"), ("/menu-plainville", "/order/")]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        return None


def get(url, follow=True):
    op = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with op.open(req, timeout=25) as r:
            return r.status, dict((k.lower(), v) for k, v in r.headers.items()), r.read(400_000).decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, dict((k.lower(), v) for k, v in e.headers.items()), "", e.headers.get("location", "")
    except Exception as e:
        return 0, {}, str(e), ""


def main():
    base = (sys.argv[1] if len(sys.argv) > 1 else "https://squarepegpizzeria.com").rstrip("/")
    rows, problems = [], []

    def check(label, ok, detail=""):
        rows.append(f"| {'✅' if ok else '❌'} | {label} | {detail} |")
        if not ok:
            problems.append(f"{label}: {detail}")

    # 1. Key pages
    pages = ["/", "/locations/", "/our-menu/", "/catering/", "/contact/", "/areas-we-serve/",
             "/deals/", "/fundraisers/", "/sitemap.xml", "/robots.txt", "/llms.txt"]
    pages += [f"/locations/{l['slug']}/" for l in LOCATIONS]
    home_headers = {}
    for path in pages:
        code, headers, body, final = get(base + path)
        ok = code == 200 and len(body) > 500
        check(f"Page {path}", ok, f"HTTP {code}, {len(body)} bytes")
        if path == "/":
            home_headers = headers
            check("Home has a title", "<title>" in body, "")
            check("Home has structured data", "application/ld+json" in body, "")
            check("Not accidentally noindex", "noindex" not in body.lower(), "found a noindex tag" if "noindex" in body.lower() else "")

    # 2. Security headers (on the home page)
    for h, expect in MUST_HEADERS.items():
        val = home_headers.get(h, "")
        ok = bool(val) and (expect is None or expect in val.lower())
        check(f"Header {h}", ok, val[:70] or "missing")

    # 3. Redirects still work
    for src, expect in REDIRECTS:
        code, headers, _, loc = get(base + src, follow=False)
        loc = headers.get("location", loc) or ""
        ok = code in (301, 308) and expect in loc
        check(f"Redirect {src}", ok, f"HTTP {code} → {loc[:70]}")

    # 4. Sitemap and robots sanity
    code, _, body, _ = get(base + "/sitemap.xml")
    check("Sitemap lists pages", code == 200 and body.count("<loc>") >= 25, f"{body.count('<loc>')} URLs")
    code, _, body, _ = get(base + "/robots.txt")
    check("Robots allows crawling", code == 200 and "Disallow: /\n" not in body, "robots.txt blocks everything" if "Disallow: /\n" in body else "")

    out = [f"## Site health: {base}", "",
           ("Everything looks good." if not problems else f"**{len(problems)} problem(s) found.**"), "",
           "| | Check | Detail |", "|---|---|---|"] + rows
    print("\n".join(out))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("\n".join(out) + "\n")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
