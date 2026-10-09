"""Keep the poll engine and the site in step.

Two jobs, both safe to run any time:

  --allowlist   Regenerate supabase/functions/cast-vote/polls.json from
                data/play.py, so the Edge Function will only accept polls and
                options that actually exist on the site. Run this after adding
                a debate question or a confession, then redeploy the function.

  (default)     Fetch the current vote totals into data/poll_tallies.json so the
                next build bakes them into the HTML.

Why the tallies are fetched at build time rather than by the browser: a page
whose results only appear after a JavaScript call is, to Google, a page with no
results on it. The whole SEO case for the debate pages is that they carry real,
quotable numbers, so the numbers have to be in the server-rendered HTML. The
page still updates live in the browser after someone votes — that part is for
the visitor, not the crawler.

Reads SUPABASE_URL and SUPABASE_ANON_KEY from the environment, falling back to
the values in data/content.py. The anon key is public by design and only has
select on the totals view.

Run:  python3 scripts/sync_polls.py [--allowlist]
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))

ALLOWLIST = ROOT / "supabase" / "functions" / "cast-vote" / "polls.json"
TALLIES = ROOT / "data" / "poll_tallies.json"


def poll_map():
    """Every poll the site has, and the options each one accepts.

    This is the single source of truth. The Edge Function gets a copy; the
    build reads the same structure to render the pages.
    """
    from play import CONFESSIONS, DEBATES
    polls = {f"debate:{d['slug']}": [o for o, _ in d["options"]] for d in DEBATES}
    polls["confession"] = [k for k, _ in CONFESSIONS["items"]]
    return polls


def patch(path, start, end, body):
    """Replace the generated block between two marker comments, in place.

    The Edge Functions are deployed by pasting them into the Supabase dashboard,
    so each has to be a single self-contained file. Generating into a marked
    block keeps that true without letting the lists drift from data/play.py."""
    p = ROOT / path
    s = p.read_text()
    i, j = s.index(start), s.index(end)
    p.write_text(s[:i] + start + "\n" + body + "\n" + s[j:])
    return p


def write_allowlist():
    polls = poll_map()
    body = ("const POLLS: Record<string, string[]> = " +
            json.dumps(polls, indent=2, sort_keys=True) + ";")
    f = patch("supabase/functions/cast-vote/index.ts", "// POLLS-START", "// POLLS-END", body)
    n = sum(len(v) for v in polls.values())
    print(f"  patched {f.relative_to(ROOT)}: {len(polls)} polls, {n} options")


def write_ingredients():
    """The Pizza Lab's fixed lists, for the Edge Function to validate against.

    The page offers these and the function accepts only these, so a crafted
    request cannot put free text into what looks like a structured field. Only
    the pizza's name and the submitter's name are free text, and both go to a
    human before they are published."""
    from play import LAB
    body = "const INGREDIENTS = " + json.dumps({
        "sauce": LAB["sauce"], "cheese": LAB["cheese"],
        "toppings": LAB["toppings"], "finish": LAB["finish"],
        "max": LAB["max_toppings"],
    }, indent=2) + ";"
    f = patch("supabase/functions/lab-submit/index.ts",
              "// INGREDIENTS-START", "// INGREDIENTS-END", body)
    print(f"  patched {f.relative_to(ROOT)}: {len(LAB['toppings'])} toppings")
    print("  both functions are single files — paste them into the Supabase dashboard,")
    print("  or deploy with the CLI if you have it.")


def fetch_tallies():
    from content import SITE
    url = os.environ.get("SUPABASE_URL") or SITE.get("supabase_url") or ""
    key = os.environ.get("SUPABASE_ANON_KEY") or SITE.get("supabase_anon_key") or ""
    if not url or not key:
        print("  no Supabase credentials — leaving the existing tallies alone")
        return 1

    req = urllib.request.Request(
        url.rstrip("/") + "/rest/v1/poll_totals?select=poll,option,region,votes",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            rows = json.load(r)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        # A failed fetch must never blank the numbers on the site. Keep whatever
        # we last had and let the build carry on.
        print(f"  could not reach Supabase ({e}) — keeping the existing tallies")
        return 1

    # {poll: {option: {"all": n, "CT": n, "FL": n}}}
    out = {}
    for row in rows:
        p = out.setdefault(row["poll"], {}).setdefault(row["option"], {"all": 0, "CT": 0, "FL": 0})
        v = int(row["votes"] or 0)
        p["all"] += v
        if row["region"] in ("CT", "FL"):
            p[row["region"]] += v

    TALLIES.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    total = sum(o["all"] for poll in out.values() for o in poll.values())
    print(f"  wrote {TALLIES.relative_to(ROOT)}: {len(out)} polls, {total} votes")
    return 0


if __name__ == "__main__":
    if "--allowlist" in sys.argv:
        write_allowlist()
        write_ingredients()
    else:
        sys.exit(fetch_tallies())
