"""TV slide — Holiday Art Class, Delray Beach, Dec 8 2026.

Built to look unlike the other slides on the wall. The in-store ones are
dark grounds with a photo panel; this one is a bright sand-to-sky wash with
a string of holiday lights across the top and the canvases shown as three
tilted boards, because the class itself is a beach scene in December and the
flyer is doing the same joke.

The canvases drawn here are plain original beach scenes -- sky, sea, sand,
a sail. Audrey's actual designs are hers, so nothing of hers is reproduced.

Registration is by Zelle or Venmo on Audrey's side, so the slide carries
those directly: this is a screen on the wall inside the restaurant, not a
public web page. The QR goes to the Delray page for anyone who wants the
detail on their phone.

Run:  python3 tv_holiday_art.py
Out:  Claude outputs/tv-slide-holiday-art-class-1920x1080.{png,jpg,pdf}
"""
import subprocess
from pathlib import Path

import qrcode
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
SP_LOGO = ROOT / "src" / "brand" / "logo-src.png"
OUT = ROOT / "Claude outputs"

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

SAND = HexColor("#F7E6C8")
SAND_D = HexColor("#EFD6AE")
SEA = HexColor("#1E7FA8")
SEA_L = HexColor("#49A7C9")
SKY = HexColor("#BFE4F2")
FOAM = HexColor("#FFFFFF")
INK = HexColor("#20242B")
GREY = HexColor("#6A6258")
EMBER = HexColor("#C4342C")
PINE = HexColor("#2F6B3C")
GOLD = HexColor("#E2A32B")
WHITE = HexColor("#FFFFFF")

W, H = 1920, 1080
SAFE = 92
URL = ("https://squarepegpizzeria.com/locations/delray-beach-fl/"
       "?utm_source=tv&utm_medium=qr")


def centered(c, t, f, s, cx, y, fill):
    c.setFont(f, s); c.setFillColor(fill); c.drawCentredString(cx, y, t)


def left(c, t, f, s, x, y, fill):
    c.setFont(f, s); c.setFillColor(fill); c.drawString(x, y, t)


def tracked(c, t, f, s, x, y, track, fill):
    """Big Shoulders sets & $ % hard against the next glyph, so display lines
    are placed one character at a time."""
    c.setFont(f, s); c.setFillColor(fill)
    for ch in t:
        c.drawString(x, y, ch); x += c.stringWidth(ch, f, s) + track
    return x


def tracked_w(t, f, s, track):
    return sum(pdfmetrics.stringWidth(ch, f, s) + track for ch in t) - track


def wrap(c, text, f, s, width):
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if c.stringWidth(trial, f, s) <= width:
            line = trial
        else:
            out.append(line); line = word
    if line:
        out.append(line)
    return out


def place(c, img, x, y, h, anchor="l"):
    im = ImageReader(img)
    iw, ih = im.getSize()
    w = h * iw / ih
    if anchor == "c":
        x -= w / 2
    c.drawImage(im, x, y, w, h, mask="auto")
    return w


def qr_image(url):
    q = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=10, border=0)
    q.add_data(url); q.make(fit=True)
    return q.make_image(fill_color="black", back_color="white").convert("RGB"), len(q.get_matrix())


def lights(c, y, n=26):
    """A string of holiday lights swagging across the top."""
    import math
    c.setStrokeColor(HexColor("#3C4A3F")); c.setLineWidth(4)
    pts = []
    for i in range(n + 1):
        t = i / n
        x = t * W
        sag = math.sin(t * math.pi * 4) * 0  # flat base, swag added below
        pts.append((x, y - 34 * math.sin(t * math.pi * 6) ** 2 + sag))
    path = c.beginPath()
    path.moveTo(*pts[0])
    for pt in pts[1:]:
        path.lineTo(*pt)
    c.drawPath(path, stroke=1, fill=0)
    bulbs = [EMBER, GOLD, PINE, SEA_L]
    for i, (x, yy) in enumerate(pts):
        if i % 2:
            continue
        c.setFillColor(bulbs[(i // 2) % 4])
        c.circle(x, yy - 20, 11, stroke=0, fill=1)
        c.setStrokeColor(HexColor("#3C4A3F")); c.setLineWidth(3)
        c.line(x, yy, x, yy - 10)


def canvas_board(c, x, y, w, h, tilt, star=False):
    """A plain beach scene on a tilted board: sky, sea, foam, sand."""
    c.saveState()
    c.translate(x + w / 2, y + h / 2)
    c.rotate(tilt)
    c.translate(-w / 2, -h / 2)

    # board edge
    c.setFillColor(WHITE)
    c.rect(-12, -12, w + 24, h + 24, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#E2D4BC")); c.setLineWidth(2)
    c.rect(-12, -12, w + 24, h + 24, stroke=1, fill=0)

    sand_h = h * 0.30
    sea_h = h * 0.32
    c.setFillColor(SKY);   c.rect(0, sand_h + sea_h, w, h - sand_h - sea_h, stroke=0, fill=1)
    c.setFillColor(SEA);   c.rect(0, sand_h, w, sea_h, stroke=0, fill=1)
    c.setFillColor(SEA_L); c.rect(0, sand_h + sea_h * 0.62, w, sea_h * 0.38, stroke=0, fill=1)
    c.setFillColor(FOAM);  c.rect(0, sand_h - 7, w, 14, stroke=0, fill=1)
    c.setFillColor(SAND_D); c.rect(0, 0, w, sand_h, stroke=0, fill=1)

    # a cloud or two
    c.setFillColor(WHITE)
    c.circle(w * 0.22, h * 0.84, w * 0.055, stroke=0, fill=1)
    c.circle(w * 0.30, h * 0.86, w * 0.072, stroke=0, fill=1)
    c.circle(w * 0.38, h * 0.84, w * 0.050, stroke=0, fill=1)

    # hull and sail -- generic, no design on the sail
    hx, hy = w * 0.56, sand_h + sea_h * 0.30
    c.setFillColor(GOLD)
    pth = c.beginPath()
    pth.moveTo(hx - w * 0.14, hy)
    pth.lineTo(hx + w * 0.14, hy)
    pth.lineTo(hx + w * 0.09, hy - h * 0.055)
    pth.lineTo(hx - w * 0.09, hy - h * 0.055)
    pth.close()
    c.drawPath(pth, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#2B2B2B")); c.setLineWidth(3)
    c.line(hx, hy, hx, hy + h * 0.30)
    c.setFillColor(WHITE)
    sl = c.beginPath()
    sl.moveTo(hx + 4, hy + h * 0.30)
    sl.lineTo(hx + 4, hy + h * 0.02)
    sl.lineTo(hx + w * 0.13, hy + h * 0.02)
    sl.close()
    c.drawPath(sl, stroke=0, fill=1)

    if star:
        c.setFillColor(GOLD)
        c.circle(hx, hy + h * 0.33, 9, stroke=0, fill=1)

    c.restoreState()


def pay_chip(c, x, y, w, label, value, tint, vs=28):
    """Chip auto-shrinks its value until it clears the right padding -- the
    Venmo handle is longer than the Zelle number and was touching the edge."""
    c.setFillColor(WHITE)
    c.roundRect(x, y, w, 104, 18, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#E6D8C0")); c.setLineWidth(2)
    c.roundRect(x, y, w, 104, 18, stroke=1, fill=0)
    c.setFillColor(tint)
    c.roundRect(x + 18, y + 26, 52, 52, 14, stroke=0, fill=1)
    centered(c, label[0], "B", 30, x + 44, y + 43, WHITE)
    left(c, label, "B", 21, x + 88, y + 60, GREY)
    avail = w - 88 - 20
    while vs > 18 and pdfmetrics.stringWidth(value, "S", vs) > avail:
        vs -= 1
    left(c, value, "S", vs, x + 88, y + 26, INK)


def draw():
    c = canvas.Canvas(str(OUT / "tv-slide-holiday-art-class-1920x1080.pdf"),
                      pagesize=(W, H))

    # ---- ground: sand below, soft sky above -----------------------------
    c.setFillColor(SAND); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(HexColor("#FBF1DE")); c.rect(0, H * 0.46, W, H * 0.54, stroke=0, fill=1)
    # a lazy shoreline curve between them
    p = c.beginPath()
    p.moveTo(0, H * 0.46)
    p.curveTo(W * 0.30, H * 0.52, W * 0.66, H * 0.40, W, H * 0.47)
    p.lineTo(W, H * 0.46)
    p.lineTo(0, H * 0.46)
    p.close()
    c.setFillColor(HexColor("#F3E2C4")); c.drawPath(p, stroke=0, fill=1)

    lights(c, H - 30)

    # ---- headline, left -------------------------------------------------
    # Explicit baselines rather than cumulative subtraction: the left column
    # has to clear the QR block at the bottom, and a running cursor walked
    # straight through it.
    x = SAFE
    place(c, Image.open(SP_LOGO), x, 924, 54)

    tracked(c, "DELRAY BEACH, FLORIDA", "B", 24, x, 846, 5.4, EMBER)
    tracked(c, "HOLIDAY", "D", 104, x, 732, 4, INK)
    tracked(c, "ART CLASS", "D", 104, x, 636, 4, EMBER)

    c.setFillColor(SEA); c.rect(x, 594, 190, 7, stroke=0, fill=1)

    yb = 546
    for line in wrap(c, "A step-by-step canvas class. Paint the ocean, the sand "
                        "and a boat on the water, and take it home the same night.",
                     "R", 29, 880):
        left(c, line, "R", 29, x, yb, GREY); yb -= 42

    # ---- date band ------------------------------------------------------
    dy = 392
    dw = tracked_w("TUE DEC 8", "D", 80, 4)
    c.setFillColor(INK)
    c.roundRect(x - 2, dy - 14, dw + 34, 80, 14, stroke=0, fill=1)
    tracked(c, "TUE DEC 8", "D", 80, x + 16, dy + 4, 4, SAND)
    c.setFillColor(SEA)
    c.roundRect(x + dw + 52, dy - 14, 190, 80, 14, stroke=0, fill=1)
    centered(c, "6–8 PM", "B", 34, x + dw + 52 + 95, dy + 16, WHITE)

    # ---- price ----------------------------------------------------------
    pw = tracked_w("$45", "D", 68, 3)
    tracked(c, "$45", "D", 68, x, 300, 3, PINE)
    left(c, "per person", "B", 30, x + pw + 22, 310, INK)
    left(c, "A glass of wine and every art material included.",
         "R", 25, x + pw + 22, 276, GREY)

    # ---- canvases, right ------------------------------------------------
    canvas_board(c, 1180, 612, 290, 290, -6.5)
    canvas_board(c, 1492, 656, 290, 290, 5.0, star=True)
    centered(c, "STEP BY STEP — NO EXPERIENCE NEEDED", "B", 22, 1480, 530,
             HexColor("#A39A8E"))

    # ---- registration block, bottom right -------------------------------
    bx, by, bw = 1120, 120, 712
    c.setFillColor(HexColor("#FFF8EA"))
    c.roundRect(bx, by, bw, 318, 24, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#E6D8C0")); c.setLineWidth(2)
    c.roundRect(bx, by, bw, 318, 24, stroke=1, fill=0)

    tracked(c, "REGISTRATION REQUIRED", "B", 25, bx + 34, by + 252, 5.0, EMBER)
    left(c, "Seats are limited — reserve yours with Audrey.",
         "R", 25, bx + 34, by + 214, GREY)

    pay_chip(c, bx + 34, by + 88, 300, "Zelle", "954-242-9833", HexColor("#6D43C8"))
    pay_chip(c, bx + 350, by + 88, 328, "Venmo", "@Audrey-Weiss", HexColor("#008CFF"))

    left(c, "Questions? Ask any member of the team.", "M", 23, bx + 34, by + 44, GREY)

    # ---- QR, bottom left ------------------------------------------------
    img, modules = qr_image(URL)
    px_per = max(4, round(160 / modules))
    side = px_per * modules
    qx, qy = SAFE, 86
    c.setFillColor(WHITE)
    c.roundRect(qx - 16, qy - 16, side + 32, side + 32, 16, stroke=0, fill=1)
    c.drawImage(ImageReader(img), qx, qy, side, side)
    left(c, "Scan for details", "B", 25, qx + side + 40, qy + side / 2 + 6, INK)
    left(c, "squarepegpizzeria.com", "R", 21, qx + side + 40, qy + side / 2 - 24, GREY)

    centered(c, "Be there and be square.", "B", 28, 1476, 64, HexColor("#A39A8E"))

    c.setTitle("Square Peg Pizzeria — Holiday Art Class, Delray Beach")
    c.showPage(); c.save()
    return modules, side


def main():
    OUT.mkdir(exist_ok=True)
    modules, side = draw()
    stem = OUT / "tv-slide-holiday-art-class-1920x1080"
    subprocess.run(["pdftoppm", "-r", "72", "-png", "-singlefile",
                    str(stem) + ".pdf", str(stem)], check=True)
    Image.open(str(stem) + ".png").convert("RGB").save(str(stem) + ".jpg", quality=92)
    print("QR: %d modules at %dpx" % (modules, side))
    print("wrote", stem.name + ".png / .jpg / .pdf")


if __name__ == "__main__":
    main()
