"""TV slide — Serve & Savor: A Taste of Italy, Delray Beach Open.

An away night, so the slide is not built like the in-store ones: the event's
own artwork carries the right-hand panel and our logo sits top-left, the way
a co-branded notice should read. Dark ground, one big date, one QR.

The QR goes to the Open's ticket page. Tagged utm_source=tv so the Open can
see the traffic came off our screens.

Run:  python3 tv_serve_savor.py
Out:  Claude outputs/tv-slide-serve-savor-1920x1080.{png,jpg,pdf}
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
EVENT_LOGO = ROOT / "src" / "partners" / "serve-savor-logo.png"
SP_LOGO = ROOT / "src" / "brand" / "logo-src.png"
OUT = ROOT / "Claude outputs"

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

# The event's own palette, so the slide and the tent match.
PINK = HexColor("#EC4E86")
LIME = HexColor("#A6CE39")
BLUE = HexColor("#3F9CC4")
INK = HexColor("#1C2A08")
CREAM = HexColor("#FFFDF9")
DIM = HexColor("#CFC6BF")
GREY = HexColor("#6B635D")
WHITE = HexColor("#FFFFFF")

W, H = 1920, 1080
SAFE = 96
URL = "https://www.delraybeachopen.com/en/serve-and-savor?utm_source=tv&utm_medium=qr"


def centered(c, t, f, s, cx, y, fill):
    c.setFont(f, s); c.setFillColor(fill); c.drawCentredString(cx, y, t)


def left(c, t, f, s, x, y, fill):
    c.setFont(f, s); c.setFillColor(fill); c.drawString(x, y, t)


def tracked(c, t, f, s, x, y, track, fill):
    c.setFont(f, s); c.setFillColor(fill)
    for ch in t:
        c.drawString(x, y, ch); x += c.stringWidth(ch, f, s) + track
    return x


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


def white_mark():
    """Our logo flattened to white; the on-dark file is still the red mark."""
    src = Image.open(SP_LOGO).convert("RGBA")
    flat = Image.new("RGBA", src.size, (255, 255, 255, 0))
    flat.putalpha(src.getchannel("A"))
    return flat


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


def tracked_w(t, f, s, track):
    return sum(pdfmetrics.stringWidth(ch, f, s) + track for ch in t) - track


def draw():
    """Bright, in the event's own colours. Every display line is hand-tracked:
    Big Shoulders sets its ampersand hard against the letter before it, so
    "SERVE & SAVOR" collides unless the glyphs are placed one at a time."""
    c = canvas.Canvas(str(OUT / "tv-slide-serve-savor-1920x1080.pdf"), pagesize=(W, H))

    # ---- bright ground, with the logo's three colours top and bottom ----
    c.setFillColor(CREAM); c.rect(0, 0, W, H, stroke=0, fill=1)
    band = 16
    for i, col in enumerate((PINK, LIME, BLUE)):
        c.setFillColor(col)
        c.rect(i * W / 3, H - band, W / 3, band, stroke=0, fill=1)
        c.rect(i * W / 3, 0, W / 3, band, stroke=0, fill=1)

    # confetti: a few soft shapes so it reads as a tasting party, not a notice
    c.setFillColor(HexColor("#FDEAF0")); c.circle(1230, 300, 190, stroke=0, fill=1)
    c.setFillColor(HexColor("#F2F7E4")); c.circle(305, 215, 120, stroke=0, fill=1)
    c.setFillColor(HexColor("#E8F2F6")); c.circle(980, 940, 86, stroke=0, fill=1)

    panel_w, panel_m = 560, 60
    px = W - panel_m - panel_w
    x = SAFE
    inner = px - 70 - x

    # ---- left: who, what, when ------------------------------------------
    place(c, Image.open(SP_LOGO), x, H - SAFE - 56, 56)

    y = H - SAFE - 146
    tracked(c, "WE ARE POURING AND PLATING AT", "B", 25, x, y, 5.2, BLUE)

    y -= 104
    tracked(c, "SERVE & SAVOR", "D", 116, x, y, 5, LIME)
    y -= 76
    tracked(c, "A TASTE OF ITALY", "D", 70, x, y, 6, PINK)

    y -= 64
    c.setFillColor(BLUE); c.rect(x, y, 168, 6, stroke=0, fill=1)

    y -= 80
    dw = tracked_w("SAT FEB 20", "D", 92, 4)
    tracked(c, "SAT FEB 20", "D", 92, x, y, 4, INK)
    c.setFillColor(PINK)
    c.roundRect(x + dw + 30, y - 6, 186, 62, 31, stroke=0, fill=1)
    centered(c, "6\u20138 PM", "B", 34, x + dw + 30 + 93, y + 14, WHITE)

    y -= 70
    for line in wrap(c, "Italian bites from the area\u2019s best kitchens in the "
                        "hospitality tent at the Delray Beach Open, poured "
                        "alongside wines from Caymus Vineyards.", "R", 32, inner):
        left(c, line, "R", 32, x, y, GREY); y -= 44

    y -= 30
    pill_w = c.stringWidth("Come find our table and say hi.", "B", 33) + 60
    c.setFillColor(LIME)
    c.roundRect(x, y - 20, pill_w, 70, 35, stroke=0, fill=1)
    left(c, "Come find our table and say hi.", "B", 33, x + 30, y + 4, HexColor("#2E3D0C"))

    tracked(c, "PART OF THE DELRAY BEACH OPEN FOOD & WINE SERIES",
            "B", 23, x, SAFE + 26, 4.4, HexColor("#9A918B"))

    # ---- right: the event's mark over the QR, on a white card -----------
    c.setFillColor(WHITE)
    c.roundRect(px, 120, panel_w, H - 240, 28, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#EFE8E0")); c.setLineWidth(2)
    c.roundRect(px, 120, panel_w, H - 240, 28, stroke=1, fill=0)
    cx = px + panel_w / 2

    place(c, Image.open(EVENT_LOGO), cx, H - 120 - 60 - 300, 300, "c")

    img, modules = qr_image(URL)
    px_per = max(5, round(290 / modules))
    side = px_per * modules
    qx, qy = cx - side / 2, 258
    c.drawImage(ImageReader(img), qx, qy, side, side)

    centered(c, "SCAN FOR TICKETS", "B", 31, cx, qy - 56, INK)
    centered(c, "delraybeachopen.com", "R", 23, cx, qy - 88, GREY)

    c.setTitle("Square Peg Pizzeria \u2014 Serve & Savor: A Taste of Italy")
    c.showPage(); c.save()
    return modules, side


def main():
    OUT.mkdir(exist_ok=True)
    modules, side = draw()
    stem = OUT / "tv-slide-serve-savor-1920x1080"
    subprocess.run(["pdftoppm", "-r", "72", "-png", "-singlefile",
                    str(stem) + ".pdf", str(stem)], check=True)
    Image.open(str(stem) + ".png").convert("RGB").save(str(stem) + ".jpg", quality=92)
    print("QR: %d modules at %dpx" % (modules, side))
    print("wrote", stem.name + ".png / .jpg / .pdf")


if __name__ == "__main__":
    main()
