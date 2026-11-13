"""Trivia night graphics for Instagram and Facebook.

One square for the feed and one 4:5, which is the taller frame Instagram
gives a post on a phone. Same artwork, laid out for each shape rather than
scaled, so the type never ends up half size in one of them.

The nights come out of ENTERTAINMENT in data/content.py, which is also what
the website reads, so this graphic cannot drift from the site or from what
the floor is actually running. Change a night there, run this again.

Dark and loud on purpose: this is a screen, not the office printer.

Run:  python3 social_trivia.py
Out:  Claude outputs/social-trivia-1080.png   (1:1, feed and Facebook)
      Claude outputs/social-trivia-1350.png   (4:5, Instagram feed)
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
from content import ENTERTAINMENT, LOCATIONS, GAME_DEAL  # noqa: E402

FONTS = ROOT / "src" / "fonts-ttf"
OUT = ROOT / "Claude outputs"
LOGO_LIGHT = ROOT / "src" / "brand" / "logo-on-dark.png"

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

CHAR = HexColor("#141110")
OVEN = HexColor("#1F1A17")
EMBER = HexColor("#D61B24")
FLAME = HexColor("#FFB524")
CREAM = HexColor("#FBF6EC")
SMOKE = HexColor("#8A807A")
LINE = HexColor("#332B27")
CAP = 0.72

DAYS = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday",
        "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}


def nights():
    """Every trivia night we run, in day order then alphabetically."""
    by_slug = {l["slug"]: l for l in LOCATIONS}
    order = list(DAYS)
    out = []
    for slug, rows in ENTERTAINMENT.items():
        for day, what, when, *_ in rows:
            if "Trivia" not in what:
                continue
            l = by_slug[slug]
            out.append({"town": l.get("short") or l["name"], "state": l["state"],
                        "day": day, "when": when, "what": what})
    # Day first, then home state before Florida: almost everyone seeing this
    # is in Connecticut, and Delray sorting to the top of the list by its
    # first letter reads like the list is in no order at all.
    return sorted(out, key=lambda e: (order.index(e["day"]), e["state"] != "CT", e["town"]))


def wide(c, text, x, y, font, size, track, color, anchor="l"):
    """Letter-spaced text. reportlab has no tracking, so place each glyph."""
    c.setFont(font, size)
    c.setFillColor(color)
    total = sum(pdfmetrics.stringWidth(ch, font, size) + track for ch in text) - track
    if anchor == "c":
        x -= total / 2
    elif anchor == "r":
        x -= total
    for ch in text:
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, size) + track
    return total


def fit(text, font, size, limit):
    while size > 6 and pdfmetrics.stringWidth(text, font, size) > limit:
        size -= 0.5
    return size


def white_mark():
    """The logo in flat white. The on-dark file is still the red mark."""
    from PIL import Image
    src = Image.open(LOGO_LIGHT).convert("RGBA")
    flat = Image.new("RGBA", src.size, (255, 255, 255, 0))
    flat.putalpha(src.getchannel("A"))
    return flat


def logo(c, img, cx, y, h):
    im = ImageReader(img)
    iw, ih = im.getSize()
    w = h * iw / ih
    c.drawImage(im, cx - w / 2, y, w, h, mask="auto")


def draw(c, W, H, rows, mark):
    """Every vertical position is worked out before anything is drawn.

    Laying it out as it was painted is what put the headline through the
    eyebrow and the list over the price bar: each block was measured from a
    different end and they met in the middle.
    """
    pad = W * 0.072
    c.setFillColor(CHAR); c.rect(0, 0, W, H, fill=1, stroke=0)

    # --- down from the top
    logo_h = H * 0.055
    logo_y = H - pad - logo_h
    eyebrow_y = logo_y - H * 0.034
    head_size = fit("TRIVIA NIGHT", "D", W * 0.158, W - pad * 2)
    head_y = eyebrow_y - H * 0.030 - head_size * CAP

    # --- up from the bottom
    footer_y = pad * 0.78
    bar_h = H * 0.082
    bar_y = footer_y + H * 0.030
    band_bottom = bar_y + bar_h + H * 0.028
    band_top = head_y - H * 0.034

    # --- the list, filling what is left between them
    c.setFillColor(OVEN)
    c.rect(0, band_bottom, W, band_top - band_bottom, fill=1, stroke=0)
    step = (band_top - band_bottom) / len(rows)
    y = band_top - step / 2 - W * 0.014
    for i, e in enumerate(rows):
        town = e["town"] + ("" if e["state"] == "CT" else f", {e['state']}")
        c.setFont("S", W * 0.042); c.setFillColor(CREAM)
        c.drawString(pad, y, town)

        when = f"{DAYS[e['day']]}  {e['when']}"
        c.setFont("M", W * 0.0325); c.setFillColor(FLAME)
        c.drawRightString(W - pad, y + W * 0.002, when)

        if i < len(rows) - 1:
            c.setStrokeColor(LINE); c.setLineWidth(1.2)
            c.line(pad, y - step * 0.36, W - pad, y - step * 0.36)
        y -= step

    # --- the reason to turn up
    deal = f"{GAME_DEAL['price']}  {GAME_DEAL['what'][0].lower()} and a fountain drink"
    c.setFillColor(EMBER); c.rect(0, bar_y, W, bar_h, fill=1, stroke=0)
    s2 = fit(deal, "B", W * 0.038, W - pad * 2)
    c.setFont("B", s2); c.setFillColor(CREAM)
    c.drawCentredString(W / 2, bar_y + (bar_h - s2 * CAP) / 2, deal)

    c.setFont("R", W * 0.0245); c.setFillColor(SMOKE)
    c.drawCentredString(W / 2, footer_y, "squarepegpizzeria.com  \u00b7  dine-in during trivia")

    # --- masthead
    logo(c, mark, W / 2, logo_y, logo_h)
    wide(c, "EVERY WEEK AT SQUARE PEG", W / 2, eyebrow_y, "B",
         W * 0.0195, W * 0.0062, FLAME, anchor="c")
    c.setFont("D", head_size); c.setFillColor(CREAM)
    c.drawCentredString(W / 2, head_y, "TRIVIA NIGHT")


def render(name, W, H, rows, mark):
    pdf = OUT / f"{name}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H))
    draw(c, W, H, rows, mark)
    c.showPage(); c.save()
    png = OUT / name
    subprocess.run(["pdftoppm", "-png", "-r", "72", "-singlefile", str(pdf), str(png)],
                   check=True)
    pdf.unlink()
    print("  ", png.with_suffix(".png").name)


def main():
    OUT.mkdir(exist_ok=True)
    rows = nights()
    mark = white_mark()
    render("social-trivia-1080", 1080, 1080, rows, mark)
    render("social-trivia-1350", 1080, 1350, rows, mark)


if __name__ == "__main__":
    main()
