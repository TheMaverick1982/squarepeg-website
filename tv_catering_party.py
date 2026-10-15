"""Two 1920x1080 TV slides — Catering, and Large Party Reservations.

Both carry a QR to their page on the site. The QR URLs carry utm_source=tv and
utm_medium=qr, which src/site.js captures into sp_attribution and attaches to
the form submission — so a lead that started on a TV screen says so in the
inbox. Don't drop those params.

The two are deliberately unalike. They sit in the same rotation, so a passer-by
should be able to tell at a glance that the screen changed:

  Catering      dark, cinematic, one photo bled across the whole frame
  Large party   light paper, editorial split, photo in a column on the right

Same grid, same fonts, same red. Different silhouette.

Run:  python3 tv_catering_party.py
"""
import subprocess
from pathlib import Path

import qrcode
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, HexColor

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
IMG = ROOT / "assets" / "img-src"
LOGO = Path("/root/.claude/uploads/4ff3a4eb-23fa-5425-8635-6d1c14f758c6/040f81d0-image.png")
OUT = Path("/mnt/user-data/outputs/tv-catering-party")

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

RED = HexColor("#D50117")
RED_LIT = HexColor("#FF3B4E")      # red that still reads on near-black
AMBER = HexColor("#FFB524")
AMBER_LIT = HexColor("#FFC957")    # brand amber, lifted for reversed type on a photo
INK = HexColor("#17120F")
GREY = HexColor("#5C5450")
PAPER = HexColor("#FFFDF9")
CARD = HexColor("#F4F1EB")
LINE = HexColor("#E2DCD4")
WHITE = HexColor("#FFFFFF")
DIM = HexColor("#E8E0DA")          # body copy on the dark slide

W, H = 1920, 1080
SAFE = 96                          # TV overscan: nothing meaningful inside this

CATERING_URL = "https://squarepegpizzeria.com/catering/?utm_source=tv&utm_medium=qr"
PARTY_URL = "https://squarepegpizzeria.com/large-party-reservations/?utm_source=tv&utm_medium=qr"


# ---------------------------------------------------------------- helpers

def centered(c, t, f, s, cx, y, fill=INK):
    c.setFont(f, s)
    c.setFillColor(fill)
    c.drawCentredString(cx, y, t)


def left(c, t, f, s, x, y, fill=INK):
    c.setFont(f, s)
    c.setFillColor(fill)
    c.drawString(x, y, t)


def tracked(c, t, f, s, x, y, track, fill=INK):
    """Letter-spaced small caps. Returns the width drawn."""
    c.setFont(f, s)
    c.setFillColor(fill)
    for ch in t:
        c.drawString(x, y, ch)
        x += c.stringWidth(ch, f, s) + track
    return x


def fit(c, t, f, hi, lo, width):
    s = hi
    while s > lo and c.stringWidth(t, f, s) > width:
        s -= 1
    return s


def wrap(c, text, f, s, width):
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if c.stringWidth(trial, f, s) <= width:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def cover(path, w, h):
    """Crop-to-fill, centred, like CSS object-fit: cover."""
    im = Image.open(path).convert("RGB")
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    nw, nh = int(round(sw * scale)), int(round(sh * scale))
    im = im.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - w) // 2, (nh - h) // 2
    return im.crop((x, y, x + w, y + h))


SCRATCH = Path("/tmp/claude-0/-home-claude/4ff3a4eb-23fa-5425-8635-6d1c14f758c6/scratchpad/tvslides")


def logo_reversed():
    """Red script stays red; the dark 'PIZZERIA' goes white so it reads on black.

    Written out to a file because reportlab's ImageReader only honours alpha
    from a PNG on disk — hand it an RGBA PIL object and the logo silently
    doesn't draw at all, which is exactly what happened the first time.
    """
    SCRATCH.mkdir(parents=True, exist_ok=True)
    out = SCRATCH / "logo-reversed.png"
    im = Image.open(LOGO).convert("RGBA")
    px = im.load()
    for yy in range(im.height):
        for xx in range(im.width):
            r, g, b, a = px[xx, yy]
            if a and not (r > g + 40 and r > b + 40):     # not the red script
                px[xx, yy] = (255, 255, 255, a)
    im.save(out)
    return str(out)


def scrimmed(path, w, h, flat=0.60, ramp=0.72, ramp_to=0.62, power=1.4):
    """Photo with the darkening baked in, as one image.

    Drawing the ramp as a stack of translucent reportlab rects leaves a visible
    hairline at every seam where the alpha overlaps — fine on paper, a row of
    vertical stripes on a backlit screen. So the gradient is composited here,
    in the pixels, and the slide draws a single opaque image.
    """
    base = cover(path, w, h).convert("RGBA")
    ov = Image.new("RGBA", (w, h))
    px = ov.load()
    edge = w * ramp_to
    for xx in range(w):
        a = flat
        if xx < edge:
            t = xx / edge
            a = 1 - (1 - flat) * (1 - ramp * (1 - t) ** power)
        col = (10, 6, 5, int(round(a * 255)))
        for yy in range(h):
            px[xx, yy] = col
    return Image.alpha_composite(base, ov).convert("RGB")


def qr_image(url, ecc=qrcode.constants.ERROR_CORRECT_M):
    q = qrcode.QRCode(version=None, error_correction=ecc, box_size=10, border=0)
    q.add_data(url)
    q.make(fit=True)
    modules = len(q.get_matrix())
    return q.make_image(fill_color="black", back_color="white").convert("RGB"), modules


def qr_block(c, url, cx, top, target, label, sub,
             bg=WHITE, label_fill=INK, sub_fill=GREY, border=None):
    """Card, QR, and the two label lines under it. Returns (width, height).

    The drawn QR is snapped to a whole number of pixels per module — a module
    that lands on a half pixel blurs, and a blurred module is a QR a phone has
    to work at from across a dining room. The card's own padding is the quiet
    zone, so it is never allowed below the four modules the spec asks for.
    """
    img, modules = qr_image(url)
    px_per = max(5, round(target / modules))
    side = px_per * modules
    quiet = px_per * 4
    pad = max(32, quiet)
    gap = max(26, quiet)                     # white between QR and the label
    label_h = 62

    # The card has to clear the wider of the QR and the two label lines, or the
    # URL runs off the card and onto whatever is behind it.
    ls, ss = 28, 21
    widest = max(c.stringWidth(label, "B", ls), c.stringWidth(sub, "R", ss))
    cw = max(side + pad * 2, widest + 48)
    ch = pad + side + gap + label_h

    x = cx - cw / 2
    y = top - ch
    c.setFillColor(bg)
    c.roundRect(x, y, cw, ch, 16, fill=1, stroke=0)
    if border is not None:
        c.setStrokeColor(border)
        c.setLineWidth(2)
        c.roundRect(x, y, cw, ch, 16, fill=0, stroke=1)

    qx = cx - side / 2
    qy = top - pad - side
    c.drawImage(ImageReader(img), qx, qy, side, side)

    centered(c, label, "B", ls, cx, qy - gap - 26, label_fill)
    centered(c, sub, "R", ss, cx, qy - gap - 52, sub_fill)
    return cw, ch, modules, side


def save(c, name, title):
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = OUT / f"{name}.pdf"
    c.setTitle(title)
    c.showPage()
    c.save()
    png = OUT / f"{name}.png"
    subprocess.run(["pdftoppm", "-r", "72", "-png", "-singlefile", str(pdf),
                    str(png.with_suffix(""))], check=True)
    Image.open(png).convert("RGB").save(OUT / f"{name}.jpg", quality=92)
    print("wrote", png.name)


# ------------------------------------------------------- slide 1: catering

CATERING_POINTS = [
    "48 hours' notice is all we need",
    "No minimum — ten people or a hundred",
    "Boxed hot. Nothing to set up, nothing to send back",
]


def catering():
    pdf = OUT / "tv-slide-catering-1920x1080.pdf"
    OUT.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(pdf), pagesize=(W, H))

    c.drawImage(ImageReader(scrimmed(IMG / "catering-table.webp", W, H)), 0, 0, W, H)

    lw = 300
    lh = lw * 460 / 1357
    c.drawImage(ImageReader(logo_reversed()), SAFE + 24, H - 118 - lh, lw, lh, mask="auto")

    x = SAFE + 24
    col = 1030

    tracked(c, "CATERING  ·  PICKUP  ·  ALL 10 LOCATIONS", "B", 30, x, 790, 5.5, AMBER_LIT)

    left(c, "HOLIDAY PARTIES.", "D", 128, x, 640, WHITE)
    left(c, "OFFICE PARTIES.", "D", 128, x, 522, WHITE)

    c.setFillColor(RED_LIT)
    c.rect(x, 470, 190, 9, fill=1, stroke=0)

    sub = ("Trays of pasta, wings, salads, sandwiches and dessert — "
           "plus pizza off the regular menu.")
    yy = 410
    for ln in wrap(c, sub, "R", 36, col):
        left(c, ln, "R", 36, x, yy, DIM)
        yy -= 46

    yy -= 26
    for p in CATERING_POINTS:
        c.setFillColor(RED_LIT)
        c.rect(x + 3, yy + 7, 15, 15, fill=1, stroke=0)
        left(c, p, "M", 33, x + 40, yy, WHITE)
        yy -= 54

    qr_block(c, CATERING_URL, W - SAFE - 24 - 180, 866, 270,
             "SCAN TO PLAN IT", "squarepegpizzeria.com/catering")

    # House footer strip, same red ramp as the daily-specials slide.
    for i in range(120):
        t = i / 119
        c.setFillColor(Color(0.835 + (1.0 - 0.835) * t,
                             0.004 + (0.710 - 0.004) * t,
                             0.090 + (0.141 - 0.090) * t))
        c.rect(W * i / 120, 0, W / 120 + 1, 14, fill=1, stroke=0)

    save(c, "tv-slide-catering-1920x1080", "Square Peg Pizzeria - Catering")


# --------------------------------------------------- slide 2: large party

PARTY_POINTS = [
    "Tables saved together for your group",
    "Food planned ahead so it lands together",
    "Birthdays, showers, reunions, office nights",
]


def qr_size(c, url, target, label, sub):
    """Exactly what qr_block will draw, so a caller can place it by an edge."""
    _, modules = qr_image(url)
    px_per = max(5, round(target / modules))
    side = px_per * modules
    pad = max(32, px_per * 4)
    gap = max(26, px_per * 4)
    widest = max(c.stringWidth(label, "B", 28), c.stringWidth(sub, "R", 21))
    return max(side + pad * 2, widest + 48), pad + side + gap + 62


def large_party():
    pdf = OUT / "tv-slide-large-party-1920x1080.pdf"
    OUT.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(pdf), pagesize=(W, H))

    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Photo column on the right, full bleed to three edges, on a red edge.
    pw = 560
    c.drawImage(ImageReader(cover(IMG / "table-spread.webp", pw, H)), W - pw, 0, pw, H)
    c.setFillColor(RED)
    c.rect(W - pw - 10, 0, 10, H, fill=1, stroke=0)

    x = SAFE + 24
    right = W - pw - 10 - 60                 # inner right edge of the type area
    col = right - x

    lw = 286
    lh = lw * 460 / 1357
    c.drawImage(ImageReader(str(LOGO)), x, H - 100 - lh, lw, lh, mask="auto")

    tracked(c, "LARGE PARTY & GROUP RESERVATIONS  ·  ALL 10 LOCATIONS",
            "B", 26, x, 806, 4.6, GREY)

    left(c, "TEN OR MORE?", "D", 118, x, 676, INK)
    left(c, "SEND THE FORM.", "D", 118, x, 566, RED)

    c.setStrokeColor(LINE)
    c.setLineWidth(2)
    c.line(x, 518, right, 518)

    # Lower half runs as two columns: the pitch on the left, the QR on the right.
    # This URL is the long one, so it needs more modules than the catering slide
    # does — which means a physically bigger QR to keep each module scannable
    # from a table across the room. 287px here reads at 25% scale; 232 did not.
    QR_LABEL, QR_SUB = "SCAN TO REQUEST A TABLE", "squarepegpizzeria.com/party-request"
    qw, qh = qr_size(c, PARTY_URL, 287, QR_LABEL, QR_SUB)
    qx = right - qw / 2
    lcol = (right - qw - 70) - x

    yy = 452
    for p in PARTY_POINTS:
        c.setFillColor(RED)
        c.circle(x + 9, yy + 11, 7, fill=1, stroke=0)
        s = fit(c, p, "M", 32, 24, lcol - 36)
        left(c, p, "M", s, x + 36, yy, INK)
        yy -= 54

    # Holiday chip — the reason to book now rather than in three weeks.
    yy -= 26
    chip = "HOLIDAY PARTIES — BOOK EARLY"
    cwid = c.stringWidth(chip, "B", 27) + 27 * 4.6 + 56
    c.setFillColor(HexColor("#FFF3D6"))
    c.roundRect(x, yy - 16, cwid, 60, 30, fill=1, stroke=0)
    c.setStrokeColor(AMBER)
    c.setLineWidth(2)
    c.roundRect(x, yy - 16, cwid, 60, 30, fill=0, stroke=1)
    tracked(c, chip, "B", 27, x + 28, yy + 4, 4.6, HexColor("#7A4F00"))

    yy -= 74
    left(c, "Fridays and Saturdays go first,", "R", 29, x, yy, GREY)
    left(c, "and the holidays go first of all.", "R", 29, x, yy - 38, GREY)

    # The QR carries the canonical URL; the line underneath is the short
    # redirect, for anyone who'd sooner type it than scan it.
    qr_block(c, PARTY_URL, qx, 516, 287, QR_LABEL, QR_SUB, bg=WHITE, border=LINE)

    # Footer runs under the type only, not under the photo — the asymmetry is
    # what stops this reading as the catering slide with the colours swapped.
    c.setFillColor(RED)
    c.rect(0, 0, W - pw - 10, 76, fill=1, stroke=0)
    head = "Every Square Peg."
    left(c, head, "B", 30, x, 28, PAPER)
    left(c, "Space varies by location — we'll confirm what works for your group.",
         "R", 25, x + c.stringWidth(head, "B", 30) + 22, 28, HexColor("#FFD9DC"))

    save(c, "tv-slide-large-party-1920x1080", "Square Peg Pizzeria - Large Parties")


if __name__ == "__main__":
    catering()
    large_party()
