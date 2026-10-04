"""1920x1080 TV slides — the Delray Beach happy hour menu.

Two slides, one per printed page: Drinks and Bites. Light treatment matching the
printed menu. Vector text, rendered to PNG at exactly 1920x1080 (the page is
sized in points, output at 72dpi).

Menu content comes from data/content.py, so the slides and the website can never
drift apart. Pass another slug once that location's menu is finalised.

Run:  python3 tv_happy_hour.py [slug]
"""
import subprocess
import sys
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "data"))
from content import HAPPY_HOUR, LOCATIONS  # noqa: E402

FONTS = ROOT / "src" / "fonts-ttf"
LOGO = Path("/root/.claude/uploads/4ff3a4eb-23fa-5425-8635-6d1c14f758c6/040f81d0-image.png")
OUT = Path("/mnt/user-data/outputs")

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

RED = HexColor("#D50117")
INK = HexColor("#17120F")
GREY = HexColor("#5C5450")
PAPER = HexColor("#FFFDF9")
LINE = HexColor("#E2DCD4")

W, H = 1920, 1080
MARGIN = 86


# ---------------------------------------------------------------- text helpers
def tw(t, f, s):
    return pdfmetrics.stringWidth(t, f, s)


def wrap(t, f, s, maxw):
    """Greedy wrap. Returns a list of lines that each fit inside maxw."""
    out, line = [], ""
    for word in t.split():
        trial = (line + " " + word).strip()
        if tw(trial, f, s) <= maxw or not line:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def text(c, t, f, s, x, y, fill=INK):
    c.setFont(f, s)
    c.setFillColor(fill)
    c.drawString(x, y, t)


def right(c, t, f, s, x, y, fill=INK):
    c.setFont(f, s)
    c.setFillColor(fill)
    c.drawRightString(x, y, t)


def centered(c, t, f, s, cx, y, fill=INK):
    c.setFont(f, s)
    c.setFillColor(fill)
    c.drawCentredString(cx, y, t)


# ---------------------------------------------------------------- slide parts
def header(c, kicker, city):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    logo = ImageReader(str(LOGO))
    lw, lh = logo.getSize()
    h = 112
    c.drawImage(logo, MARGIN, H - 60 - h, width=h * lw / lh, height=h,
                mask="auto", preserveAspectRatio=True)

    right(c, kicker, "B", 40, W - MARGIN, H - 112, RED)
    right(c, city.upper(), "B", 29, W - MARGIN, H - 152, INK)

    c.setFillColor(RED)
    c.rect(0, H - 196, W, 7, fill=1, stroke=0)


def hours_bar(c, hh, y):
    """One centered line: every window the menu runs."""
    parts = []
    for days, time in hh["hours"]:
        parts.append((days.upper(), time.upper().replace("PM", " PM").replace("  ", " ")))
    gap, seg = 26, []
    for days, time in parts:
        seg.append((days, "B", 32, INK))
        seg.append((time, "B", 32, RED))
    total = sum(tw(t, f, s) for t, f, s, _ in seg) + gap * (len(seg) - 1) + 44 * (len(parts) - 1)
    x = (W - total) / 2
    for i, (t, f, s, col) in enumerate(seg):
        text(c, t, f, s, x, y, col)
        x += tw(t, f, s) + (44 + gap if (i % 2 and i < len(seg) - 1) else gap)
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(MARGIN, y - 26, W - MARGIN, y - 26)


def group(c, head, blurb, items, x, y, colw, compact=False):
    """Draw one menu group downward from y. Returns the new y."""
    text(c, head, "D", 50 if not compact else 44, x, y, INK)
    y -= 16
    if blurb:
        y -= 28
        text(c, blurb, "R", 26, x, y, GREY)
    y -= 38

    for name, price, detail, tag in items:
        psize = 34
        ptext = price
        pw = tw(ptext, "B", psize)
        nsize = 34
        badge_w = 0
        if tag:
            badge_w = tw(tag.upper(), "B", 17) + 26
        nw = tw(name, "B", nsize)

        text(c, name, "B", nsize, x, y, INK)
        if tag:
            bx = x + nw + 12
            c.setFillColor(RED)
            c.roundRect(bx, y - 5, badge_w, 28, 4, fill=1, stroke=0)
            text(c, tag.upper(), "B", 17, bx + 13, y + 3, PAPER)
        right(c, ptext, "B", psize, x + colw, y, RED)

        # dotted leader between the name and the price
        lead_from = x + nw + (badge_w + 24 if tag else 16)
        lead_to = x + colw - pw - 16
        if lead_to > lead_from + 20:
            c.setStrokeColor(LINE)
            c.setLineWidth(2)
            c.setDash(2, 7)
            c.line(lead_from, y + 9, lead_to, y + 9)
            c.setDash()

        y -= 34
        for ln in wrap(detail, "R", 26, colw):
            text(c, ln, "R", 26, x, y, GREY)
            y -= 31
        y -= 12
    return y - 14


def footer(c, note):
    c.setFillColor(RED)
    c.rect(0, 0, W, 104, fill=1, stroke=0)
    text(c, "DINE-IN ONLY", "B", 34, MARGIN, 38, PAPER)
    right(c, note, "M", 30, W - MARGIN, 38, PAPER)


FLOOR = 134  # top of the red footer band plus breathing room


def _check(ends, name):
    """Loud failure beats a slide with text sitting under the footer band."""
    low = min(ends)
    if low < FLOOR:
        raise SystemExit(f"{name}: content runs {FLOOR - low:.0f}px into the footer")
    print(f"  {name}: {low - FLOOR:.0f}px clear of the footer")


# ---------------------------------------------------------------- slides
def slide_drinks(c, hh, city):
    header(c, "HAPPY HOUR  ·  DRINKS", city)
    hours_bar(c, hh, H - 258)

    colw = (W - MARGIN * 2 - 90) / 2
    left_x, right_x = MARGIN, MARGIN + colw + 90
    top = H - 322

    g = {h: (h, b, i) for h, b, i in hh["drinks"]}
    y = group(c, *g["Our signatures"], left_x, top, colw)
    ends = [group(c, *g["Well drinks"], left_x, y, colw),
            group(c, *g["Beer & wine"], right_x, top, colw)]
    _check(ends, "drinks")

    footer(c, " · ".join(hh["local"][:2]))


def slide_bites(c, hh, city):
    header(c, "HAPPY HOUR  ·  BITES", city)
    hours_bar(c, hh, H - 258)

    colw = (W - MARGIN * 2 - 90) / 2
    left_x, right_x = MARGIN, MARGIN + colw + 90
    top = H - 322

    g = {h: (h, b, i) for h, b, i in hh["food"]}
    y = group(c, *g["Wings"], left_x, top, colw)
    ends = [group(c, *g["Small pizza"], left_x, y, colw),
            group(c, *g["Starters & sides"], right_x, top, colw)]
    _check(ends, "bites")

    footer(c, "Why limit happy to an hour?")


def build(slug):
    hh = HAPPY_HOUR[slug]
    loc = next(l for l in LOCATIONS if l["slug"] == slug)
    city = f"{loc['city']}, {loc['state']}"
    stem = f"tv-slide-happy-hour-{slug}"

    OUT.mkdir(parents=True, exist_ok=True)
    for tag, fn in (("drinks", slide_drinks), ("bites", slide_bites)):
        pdf = OUT / f"{stem}-{tag}-1920x1080.pdf"
        c = canvas.Canvas(str(pdf), pagesize=(W, H))
        c.setTitle(f"Square Peg Pizzeria - Happy Hour {tag.title()} - {city}")
        fn(c, hh, city)
        c.showPage()
        c.save()
        png = pdf.with_suffix("")
        subprocess.run(["pdftoppm", "-r", "72", "-png", "-singlefile", str(pdf), str(png)],
                       check=True)
        print("wrote", png.name + ".png", "and", pdf.name)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "delray-beach-fl")
