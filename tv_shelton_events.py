"""1920x1080 TV slides for the Shelton one-off nights.

Three slides, three layouts. They are deliberately not a template: a run of
identical slides on the screens reads as wallpaper and people stop seeing it,
so each one is built around whatever that night is actually selling -- the
name for the music, the $5 menu for Santa, the two happy hours for the
appreciation day.

The dates and times come from EVENTS in data/content.py, so a slide cannot
drift from the website.

Run:  python3 tv_shelton_events.py
Out:  Claude outputs/tv-shelton-<slug>.png
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "data"))
from content import EVENTS  # noqa: E402

W, H = 1920, 1080
FONTS = ROOT / "src" / "fonts-ttf"
OUT = ROOT / "Claude outputs"
LOGO_LIGHT = ROOT / "src" / "brand" / "logo-on-dark.png"   # white mark, for dark grounds
LOGO_DARK = ROOT / "src" / "brand" / "logo-src.png"        # red mark, for light grounds

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

RED = HexColor("#D50117")
DEEP = HexColor("#9E0512")
INK = HexColor("#17120F")
NIGHT = HexColor("#0D0A08")
GOLD = HexColor("#E7B14A")
GOLD_PALE = HexColor("#F5DCA4")
CREAM = HexColor("#FBF6EC")
GREEN = HexColor("#14502F")
WHITE = HexColor("#FFFFFF")
SMOKE = HexColor("#6B625C")

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


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
    """Shrink until it fits. A headline that runs off a TV is worse than a small one."""
    while size > 8 and pdfmetrics.stringWidth(text, font, size) > limit:
        size -= 2
    return size


_WHITE_MARK = [None]


def white_mark():
    """The logo in flat white, for grounds the red mark disappears into."""
    if _WHITE_MARK[0] is None:
        from PIL import Image
        src = Image.open(LOGO_LIGHT).convert("RGBA")
        flat = Image.new("RGBA", src.size, (255, 255, 255, 0))
        flat.putalpha(src.getchannel("A"))
        _WHITE_MARK[0] = flat
    return _WHITE_MARK[0]


def logo(c, img, x, y, h, anchor="l"):
    im = ImageReader(img if not isinstance(img, Path) else str(img))
    iw, ih = im.getSize()
    w = h * iw / ih
    if anchor == "c":
        x -= w / 2
    c.drawImage(im, x, y, w, h, mask="auto")
    return w


def when(ev):
    d = date.fromisoformat(ev["date"])
    return f"{DAYS[d.weekday()]}, {MONTHS[d.month - 1]} {d.day}"


def render(name, draw):
    pdf = OUT / f"tv-shelton-{name}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H))
    draw(c)
    c.showPage()
    c.save()
    png = OUT / f"tv-shelton-{name}"
    subprocess.run(["pdftoppm", "-png", "-r", "72", "-singlefile", str(pdf), str(png)],
                   check=True)
    pdf.unlink()
    print("  ", png.with_suffix(".png").name)


# --------------------------------------------------------------- the three
def music(ev):
    def draw(c):
        c.setFillColor(NIGHT); c.rect(0, 0, W, H, fill=1, stroke=0)
        # A gold rail down the left, so the slide reads as one tall block of
        # stage light rather than a centred poster like the other two.
        c.setFillColor(GOLD); c.rect(0, 0, 22, H, fill=1, stroke=0)
        c.setFillColor(HexColor("#171009")); c.rect(22, 0, 150, H, fill=1, stroke=0)

        logo(c, white_mark(), 250, H - 200, 104)
        wide(c, "SHELTON", 252, H - 252, "B", 28, 11, GOLD)

        # A staff line across the dead space on the right, so the top half is
        # not just empty black.
        c.setStrokeColor(HexColor("#2A1E10")); c.setLineWidth(3)
        for i in range(5):
            c.line(1180, 800 - i * 26, W - 120, 800 - i * 26)

        wide(c, "THE SMOOTH SOUNDS OF", 250, 640, "B", 38, 11, GOLD_PALE)
        size = fit(ev["title"].replace("The Smooth Sounds of ", ""), "D", 290, W - 400)
        c.setFont("D", size); c.setFillColor(GOLD)
        c.drawString(250, 400, ev["title"].replace("The Smooth Sounds of ", ""))

        c.setFillColor(GOLD); c.rect(250, 330, 760, 5, fill=1, stroke=0)

        c.setFont("D", 110); c.setFillColor(WHITE)
        c.drawString(250, 190, when(ev).upper())
        c.setFont("D", 110); c.setFillColor(GOLD)
        c.drawString(250 + pdfmetrics.stringWidth(when(ev).upper(), "D", 110) + 50, 190,
                     ev["meta"][0])

        wide(c, "320 HOWE AVENUE  ·  SHELTON, CT", 250, 100, "M", 30, 7, SMOKE)
    return draw


def santa(ev):
    def draw(c):
        c.setFillColor(CREAM); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(GREEN); c.rect(0, H - 26, W, 26, fill=1, stroke=0)
        c.setFillColor(RED); c.rect(0, 0, W, 26, fill=1, stroke=0)

        # Split: everything that matters on the left, the price as a badge on
        # the right. A parent walking past reads "$5" before anything else.
        logo(c, LOGO_DARK, 130, H - 230, 92)
        wide(c, "PIZZERIA · SHELTON", 132, H - 272, "B", 24, 9, GREEN)

        c.setFont("D", 170); c.setFillColor(GREEN)
        c.drawString(128, 560, "LUNCH WITH")
        c.setFont("D", 170); c.setFillColor(RED)
        c.drawString(128, 400, "SANTA")

        c.setFont("B", 56); c.setFillColor(INK)
        c.drawString(132, 300, when(ev))
        c.setFont("D", 96); c.setFillColor(GREEN)
        c.drawString(132, 180, ev["meta"][0])

        wide(c, "HAPPY HOUR 2–6 PM   ·   320 HOWE AVENUE   ·   203-538-5044",
             132, 100, "M", 28, 6, SMOKE)

        bx, by, bw, bh = 1230, 420, 520, 360
        c.setFillColor(RED)
        c.roundRect(bx, by, bw, bh, 36, fill=1, stroke=0)
        c.setFont("D", 210); c.setFillColor(WHITE)
        t = "$5"
        c.drawString(bx + bw / 2 - pdfmetrics.stringWidth(t, "D", 210) / 2, by + 150, t)
        wide(c, "KIDS MENU", bx + bw / 2, by + 70, "B", 44, 8, WHITE, "c")
    return draw


def appreciation(ev):
    def draw(c):
        c.setFillColor(RED); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(DEEP); c.rect(0, 0, W, 150, fill=1, stroke=0)

        # Centred, and built around the two windows, because two happy hours in
        # one day is the whole offer.
        logo(c, white_mark(), W / 2, H - 196, 92, "c")
        wide(c, "SHELTON", W / 2, H - 244, "B", 26, 10, GOLD_PALE, "c")

        for i, line in enumerate(["CUSTOMER", "APPRECIATION DAY"]):
            size = fit(line, "D", 142, W - 320)
            c.setFont("D", size); c.setFillColor(WHITE)
            c.drawString(W / 2 - pdfmetrics.stringWidth(line, "D", size) / 2,
                         700 - i * 132, line)

        wide(c, when(ev).upper(), W / 2, 498, "B", 44, 10, GOLD, "c")

        for i, (lab, hrs) in enumerate([("HAPPY HOUR", "2–6 PM"),
                                        ("HAPPY HOUR", "8:30–11 PM")]):
            bw, bh = 560, 230
            bx = W / 2 - bw - 30 + i * (bw + 60)
            by = 215
            c.setFillColor(WHITE)
            c.roundRect(bx, by, bw, bh, 26, fill=1, stroke=0)
            wide(c, lab, bx + bw / 2, by + 155, "B", 34, 8, RED, "c")
            size = fit(hrs, "D", 110, bw - 60)
            c.setFont("D", size); c.setFillColor(INK)
            c.drawString(bx + bw / 2 - pdfmetrics.stringWidth(hrs, "D", size) / 2,
                         by + 45, hrs)

        wide(c, "320 HOWE AVENUE  ·  SHELTON, CT", W / 2, 60, "M", 30, 7, GOLD_PALE, "c")
    return draw


BUILD = {
    "The Smooth Sounds of Billy Lopez": ("billy-lopez", music),
    "Lunch with Santa": ("lunch-with-santa", santa),
    "Customer Appreciation Day": ("customer-appreciation", appreciation),
}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for ev in EVENTS["shelton-ct"]:
        if ev["title"] in BUILD:
            slug, fn = BUILD[ev["title"]]
            render(slug, fn(ev))
