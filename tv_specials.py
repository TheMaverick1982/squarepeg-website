"""1920x1080 TV slide — the daily specials from /promotions/.

Light treatment to match the reversed $10 Lunch handout. Vector text, rendered
to PNG at exactly 1920x1080 (page is sized in points, output at 72dpi).

Run:  python3 tv_specials.py
"""
import subprocess
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, HexColor

ROOT = Path(__file__).parent
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
AMBER = HexColor("#FFB524")
INK = HexColor("#17120F")
GREY = HexColor("#5C5450")
PAPER = HexColor("#FFFDF9")
CARD = HexColor("#F4F1EB")
LINE = HexColor("#E2DCD4")

W, H = 1920, 1080

DAILY = [
    ("Tuesday", "Pasta Night", "$15", "Carb up, wind down."),
    ("Wednesday", "Wing Night", "$1", "per wing", "You bring the appetite, we bring the heat."),
    ("Friday", "Wine Night", "1/2", "price bottles", "Because you survived the week."),
]


def centered(c, t, f, s, cx, y, fill=INK):
    c.setFont(f, s)
    c.setFillColor(fill)
    c.drawCentredString(cx, y, t)


def tracked(c, t, f, s, cx, y, track, fill=INK):
    c.setFont(f, s)
    c.setFillColor(fill)
    total = c.stringWidth(t, f, s) + track * (len(t) - 1)
    x = cx - total / 2
    for ch in t:
        c.drawString(x, y, ch)
        x += c.stringWidth(ch, f, s) + track
    return total


def fit(c, t, f, hi, lo, width):
    s = hi
    while s > lo and c.stringWidth(t, f, s) > width:
        s -= 1
    return s


def gradient_strip(c, y, h, steps=120):
    for i in range(steps):
        t = i / (steps - 1)
        c.setFillColor(Color(0.835 + (1.0 - 0.835) * t,
                             0.004 + (0.710 - 0.004) * t,
                             0.090 + (0.141 - 0.090) * t))
        c.rect(W * i / steps, y, W / steps + 1, h, fill=1, stroke=0)


def card(c, x, y, w, h, day, name, price, price_sub, note):
    c.setFillColor(CARD)
    c.roundRect(x, y, w, h, 10, fill=1, stroke=0)
    c.setStrokeColor(LINE); c.setLineWidth(2)
    c.roundRect(x, y, w, h, 10, fill=0, stroke=1)
    c.setFillColor(RED)
    c.roundRect(x, y + h - 14, w, 14, 7, fill=1, stroke=0)
    c.setFillColor(CARD)
    c.rect(x + 2, y + h - 16, w - 4, 8, fill=1, stroke=0)
    c.setFillColor(RED)
    c.rect(x, y + h - 14, w, 10, fill=1, stroke=0)

    cx = x + w / 2
    tracked(c, day.upper(), "B", 30, cx, y + h - 76, 5.5, GREY)
    s = fit(c, name.upper(), "D", 76, 48, w - 70)
    centered(c, name.upper(), "D", s, cx, y + h - 160, INK)

    # price — the number carries the slide, so it gets the room
    ps = fit(c, price, "D", 190, 90, w - 90)
    centered(c, price, "D", ps, cx, y + h - 352, RED)
    if price_sub:
        centered(c, price_sub, "B", 34, cx, y + h - 398, RED)

    c.setStrokeColor(LINE); c.setLineWidth(2)
    c.line(x + 70, y + 108, x + w - 70, y + 108)
    centered(c, "After 5pm", "B", 30, cx, y + 64, INK)
    ns = fit(c, note, "R", 28, 20, w - 60)
    centered(c, note, "R", ns, cx, y + 26, GREY)


def draw(c, items, happy_hour=True):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    gradient_strip(c, H - 16, 16)

    lw = 330
    lh = lw * 460 / 1357
    c.drawImage(ImageReader(str(LOGO)), (W - lw) / 2, H - 56 - lh, lw, lh, mask="auto")

    centered(c, "DAILY SPECIALS", "D", 104, W / 2, 790, INK)
    c.setStrokeColor(RED); c.setLineWidth(6)
    c.line(W / 2 - 120, 762, W / 2 + 120, 762)

    n = len(items)
    gap = 44
    side = 110
    cw = (W - side * 2 - gap * (n - 1)) / n
    cy, ch = 190, 520
    for i, it in enumerate(items):
        day, name, price = it[0], it[1], it[2]
        sub = it[3] if len(it) == 5 else ""
        note = it[-1]
        card(c, side + i * (cw + gap), cy, cw, ch, day, name, price, sub, note)

    if happy_hour:
        c.setFillColor(RED)
        c.rect(0, 0, W, 120, fill=1, stroke=0)
        tracked(c, "HAPPY HOUR", "D", 62, W / 2 - 300, 42, 4, PAPER)
        centered(c, "Every day  ·  2–6pm", "B", 44, W / 2 + 230, 46, AMBER)
        c.setStrokeColor(Color(1, 1, 1, alpha=0.35)); c.setLineWidth(2)
        c.line(W / 2 - 20, 26, W / 2 - 20, 94)
    else:
        c.setFillColor(RED)
        c.rect(0, 0, W, 120, fill=1, stroke=0)
        centered(c, "Dough made fresh from scratch.", "B", 46, W / 2, 46, PAPER)


def build(name, items, happy_hour=True):
    pdf = OUT / f"{name}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H))
    c.setTitle("Square Peg Pizzeria - Daily Specials")
    draw(c, items, happy_hour)
    c.showPage(); c.save()
    png = OUT / f"{name}.png"
    subprocess.run(["pdftoppm", "-r", "72", "-png", "-singlefile", str(pdf),
                    str(png.with_suffix(""))], check=True)
    print("wrote", png.name, "and", pdf.name)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    build("tv-slide-daily-specials-1920x1080", DAILY, happy_hour=True)
    # Bolton has no bar: no wine night, no happy hour.
    build("tv-slide-daily-specials-1920x1080-BOLTON", DAILY[:2], happy_hour=False)
