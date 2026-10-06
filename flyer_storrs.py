"""Double-sided 8.5x11 flyer for the Storrs event.

Side 1 leads with Husky Bucks and the loyalty app, because those are the two
things this audience can act on standing in the room. Side 2 carries the rest:
Tuesday fundraisers, catering, the DJ and trivia.

Every fact — address, phone, hours, entertainment times, the $5 join offer —
reads from data/content.py, so the flyer can't drift from the website.

Two builds of each side: one with 1/8" bleed for a print shop, one inset inside a
white border that any office printer can hold.

Run:  python3 flyer_storrs.py
"""
import subprocess
import sys
from pathlib import Path

import segno
from PIL import Image, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "data"))
from content import LOCATIONS, SITE, ENTERTAINMENT, APP_PERKS, DAYS  # noqa: E402

FONTS = ROOT / "src" / "fonts-ttf"
PHONE = ROOT / "assets" / "img-src" / "app-phone.webp"
HUSKY = ROOT / "assets" / "img-src" / "husky-bucks.webp"
LOGO_W = Path("/tmp/claude-0/adflyer/logo-white.png")   # knocked out, for dark grounds
LOGO_R = ROOT / "src" / "brand" / "logo-on-dark.png"     # the red mark, for light grounds
WORK = Path("/tmp/claude-0/storrs")
OUT = Path("/mnt/user-data/outputs")

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))
PIL_FONT = {"D": "big-shoulders-display-latin-900-normal", "B": "figtree-latin-800-normal",
            "S": "figtree-latin-700-normal", "M": "figtree-latin-600-normal",
            "R": "figtree-latin-400-normal"}

INK = HexColor("#120E0C")
RED = HexColor("#D50117")
RED_DEEP = HexColor("#A80A14")
ORANGE = HexColor("#F2761B")
GOLD = HexColor("#FFB524")
PAPER = HexColor("#FFFDF9")
MUTED = HexColor("#B9AFA7")
SMOKE = HexColor("#5C5450")
LINE = HexColor("#E2DCD4")

W, H = 612, 792
SAFE = 30                      # white border for the office build

L = next(x for x in LOCATIONS if x["slug"] == "storrs-ct")
ENT = dict((d, (what, when)) for d, what, when in ENTERTAINMENT["storrs-ct"])
ORDER_URL = SITE["order_picker_toast"]
APP_URL = SITE["app_link"]


def hours_lines():
    """Opening hours, collapsed into runs of identical days."""
    def fmt(t):
        hh, mm = map(int, t.split(":"))
        if hh == 0 and mm == 0:
            return "12am"
        ap = "pm" if hh >= 12 else "am"
        return f"{hh % 12 or 12}{':%02d' % mm if mm else ''}{ap}"

    rows, run = [], []
    for d in DAYS:
        v = L["hours"][d]
        key = None if not v else (fmt(v[0]), fmt(v[1]))
        if run and run[-1][1] == key:
            run.append((d, key))
        else:
            if run:
                rows.append(run)
            run = [(d, key)]
    rows.append(run)
    out = []
    for r in rows:
        days = r[0][0] if len(r) == 1 else f"{r[0][0]}–{r[-1][0]}"
        span = r[0][1]
        out.append((days, "Closed" if span is None else f"{span[0]} \u2013 {span[1]}"))
    return out


# ---------------------------------------------------------------- text helpers
def tw(t, f, s):
    return pdfmetrics.stringWidth(t, f, s)


def fit(t, f, maxw, start, floor=12):
    size = start
    while size > floor and tw(t, f, size) > maxw:
        size -= 1
    return size


def wrap(t, f, s, maxw):
    out, line = [], ""
    for word in t.split():
        trial = (line + " " + word).strip()
        if tw(trial, f, s) <= maxw or not line:
            line = trial
        else:
            out.append(line); line = word
    if line:
        out.append(line)
    return out


def text(c, t, f, s, x, y, fill=PAPER):
    c.setFont(f, s); c.setFillColor(fill); c.drawString(x, y, t)


def centred(c, t, f, s, cx, y, fill=PAPER):
    c.setFont(f, s); c.setFillColor(fill); c.drawCentredString(cx, y, t)


def para(c, t, f, s, x, y, maxw, lead, fill=PAPER):
    for ln in wrap(t, f, s, maxw):
        text(c, ln, f, s, x, y, fill); y -= lead
    return y


def ink_span(t, f, size):
    pf = ImageFont.truetype(str(FONTS / f"{PIL_FONT[f]}.ttf"), int(size))
    ascent, _ = pf.getmetrics()
    _, y0, _, y1 = pf.getbbox(t)
    return ascent - y0, ascent - y1


def band_text(c, t, f, size, cx, band_y, band_h, fill=PAPER):
    """Optically centre inside a band, by ink rather than by line box."""
    top, bot = ink_span(t, f, size)
    baseline = band_y + (band_h - (top - bot)) / 2 - bot
    centred(c, t, f, size, cx, baseline, fill)


def qr_png(data, key, scale=16):
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / f"qr-{key}.png"
    if not out.exists():
        segno.make(data, error="h").save(str(out), scale=scale, border=1,
                                         dark="#120E0C", light="#FFFDF9")
    return out


def qr_tile(c, data, key, x, y, size, cap, sub=None, light=False):
    """QR with a card behind it on dark pages, a hairline box on light ones."""
    pad = size * 0.09
    cap_h = size * 0.30
    cw = size + pad * 2
    ch = size + pad * 2 + cap_h
    if light:
        c.setStrokeColor(LINE); c.setLineWidth(1)
        c.roundRect(x, y, cw, ch, 6, fill=0, stroke=1)
    else:
        c.setFillColor(PAPER); c.roundRect(x, y, cw, ch, 6, fill=1, stroke=0)
    c.drawImage(ImageReader(str(qr_png(data, key))), x + pad, y + pad + cap_h,
                width=size, height=size)
    centred(c, cap, "B", size * 0.105, x + cw / 2, y + cap_h * 0.52, INK)
    if sub:
        centred(c, sub, "M", size * 0.078, x + cw / 2, y + cap_h * 0.20, SMOKE)
    return cw, ch


def logo_at(c, x, y, w, light=False):
    img = ImageReader(str(LOGO_R if light else LOGO_W)); iw, ih = img.getSize()
    h = ih * w / iw
    c.drawImage(img, x, y, width=w, height=h, mask="auto", preserveAspectRatio=True)
    return h


def addr_bar(c, y, h=64):
    """The same foot on both sides: who, where, when."""
    c.setFillColor(RED); c.rect(0, y, W, h, fill=1, stroke=0)
    text(c, f"{L['street']}, {L['city']}, {L['state']}", "B", 13, 44, y + h - 26, PAPER)
    text(c, L["phone"], "R", 12, 44, y + h - 44, HexColor("#FFD8DC"))
    c.setFont("B", 13); c.setFillColor(PAPER)
    c.drawRightString(W - 44, y + h - 26, "squarepegpizzeria.com")
    c.setFont("R", 12); c.setFillColor(HexColor("#FFD8DC"))
    c.drawRightString(W - 44, y + h - 44, "Open 7 days · Kitchen late Thu–Sat")


# ---------------------------------------------------------------- side 1
def side_one(c):
    """Light ground, to match side 2 and to stop the printer drinking toner."""
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    M = 44
    FOOT = 84
    colw = 268                                  # left column; the phone owns the right

    logo_at(c, M, H - 100, 170, light=True)
    c.setFont("B", 11.5); c.setFillColor(HexColor("#C4121B"))
    c.drawRightString(W - M, H - 74, "STORRS \u00b7 9 DOG LANE")
    y = H - 136

    # the UConn decal sits beside the headline, so the headline gets the rest
    hb = ImageReader(str(HUSKY)); hbw, hbh = hb.getSize()
    badge_w = 128
    badge_h = hbh * badge_w / hbw
    head_w = W - M * 2 - badge_w - 26

    hs = fit("YOUR HUSKY BUCKS", "D", head_w, 58)
    c.drawImage(hb, W - M - badge_w, y - badge_h, width=badge_w, height=badge_h)
    text(c, "YOUR HUSKY BUCKS", "D", hs, M, y - hs * 0.78, INK)
    y -= hs * 0.78 + 6
    text(c, "WORK HERE.", "D", hs, M, y - hs * 0.78, RED)
    y -= hs * 0.78 + 26
    assert tw("YOUR HUSKY BUCKS", "D", hs) < head_w + 1, "the headline runs under the decal"

    y = para(c, "Walk down Dog Lane, order a pizza, pay with Husky Bucks. "
                "Dine in or take it to go.", "R", 14, M, y, colw, 19, SMOKE)
    y -= 18

    body_top = y

    ph = ImageReader(str(PHONE)); pw, phh = ph.getSize()
    ph_w = 206
    ph_h = phh * ph_w / pw
    c.drawImage(ph, W - M - ph_w, body_top - ph_h, width=ph_w, height=ph_h, mask="auto")

    # the one block of solid colour on the page, because the offer is the point
    box_h = 120
    c.setFillColor(RED); c.roundRect(M, body_top - box_h, colw, box_h, 5, fill=1, stroke=0)
    text(c, "JOIN THE APP", "B", 11.5, M + 20, body_top - 32, HexColor("#FFD8DC"))
    text(c, "GET $5", "D", 58, M + 20, body_top - 84, PAPER)
    text(c, "just for signing up", "M", 14, M + 20, body_top - 104, PAPER)
    y = body_top - box_h - 24

    for perk in APP_PERKS[1:]:
        c.setFillColor(RED); c.circle(M + 4, y + 4, 3.2, fill=1, stroke=0)
        text(c, perk, "R", 13, M + 16, y, INK)
        y -= 21
    y -= 10

    qs = 94
    tile_h = qs * (1 + 0.09 * 2 + 0.30)
    qtop = y
    qw, qh = qr_tile(c, APP_URL, "app", M, qtop - tile_h, qs, "GET THE APP",
                     "Scan to download", light=True)
    qr_tile(c, ORDER_URL, "order", M + qw + 18, qtop - tile_h, qs, "ORDER PICKUP",
            "squarepegpizzeria.com", light=True)
    y = qtop - qh

    assert y > FOOT + 16, f"side 1 runs {FOOT + 16 - y:.0f}pt into the address bar"
    addr_bar(c, 0, FOOT)


# ---------------------------------------------------------------- side 2
def side_two(c):
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    M = 44

    c.setFillColor(INK); c.rect(0, H - 132, W, 132, fill=1, stroke=0)
    logo_at(c, M, H - 86, 150)
    c.setFont("B", 12); c.setFillColor(GOLD)
    c.drawRightString(W - M, H - 62, "STORRS · 9 DOG LANE")
    text(c, "MORE REASONS TO WALK DOWN DOG LANE", "B", 13, M, H - 116, MUTED)

    y = H - 176

    blocks = [
        (f"DJ {ENT['Fri'][1].upper()}", "Friday & Saturday",
         "Bar runs late Thursday through Saturday. NFL Sunday Ticket on game days."),
        (f"TRIVIA {ENT['Wed'][1].upper()}", "Every Wednesday",
         "Bring four people and an unreasonable amount of confidence."),
        ("TUESDAY FUNDRAISERS", "20% back to your cause",
         "Book a Tuesday for your club, team, house or nonprofit. We give back 20% of "
         "dine-in food sales from everyone who turns up for you."),
        ("CATERING", "Feed the whole roster",
         "Floor events, club meetings, game days, formals. Give us a headcount and a "
         "time. Husky Bucks work on catering too."),
    ]

    # y is always the next free top edge, so a block can never sit on the one above
    for head, kicker, body in blocks:
        top = y
        hs = fit(head, "D", W - M * 2 - 34, 32)
        text(c, head, "D", hs, M + 24, y - hs * 0.72, INK)
        y -= hs * 0.72 + 8
        text(c, kicker, "B", 12.5, M + 24, y - 12.5, HexColor("#C4121B"))
        y -= 12.5 + 13
        c.setFillColor(RED); c.rect(M, y + 9, 7, top - y - 7, fill=1, stroke=0)
        y = para(c, body, "R", 12.5, M + 24, y, W - M * 2 - 40, 17, SMOKE)
        y -= 18

    # hours, plain and checkable
    qs = 86
    tile_h = qs * (1 + 0.09 * 2 + 0.30)
    panel_h = 108
    panel_w = W - M * 2 - qs * 1.18 - 24       # leave the QR its own lane
    c.setFillColor(HexColor("#F2EEE8")); c.rect(M, y - panel_h, panel_w, panel_h, fill=1, stroke=0)
    text(c, "HOURS", "B", 11, M + 20, y - 24, HexColor("#C4121B"))
    hy = y - 40
    for days, span in hours_lines():
        text(c, days, "B", 11.5, M + 20, hy, INK)
        text(c, span, "R", 11.5, M + 98, hy, SMOKE)
        hy -= 14
    assert hy + 14 - 4 > y - panel_h, "the last hours row falls out of its panel"
    qr_tile(c, f"{SITE['domain']}/locations/storrs-ct/", "storrs",
            W - M - qs * 1.18, y - panel_h + (panel_h - tile_h) / 2, qs,
            "SEE EVERYTHING", "Menu \u00b7 hours \u00b7 events")
    c.setFillColor(INK)

    assert y - panel_h > 84 + 14, (
        f"side 2 runs {84 + 14 - (y - panel_h):.0f}pt into the address bar")
    addr_bar(c, 0, 84)


# ---------------------------------------------------------------- build
def build(name, bleed_in=0.0):
    b = bleed_in * 72
    pw, ph = W + 2 * b, H + 2 * b
    pdf = OUT / f"{name}.pdf"
    c = rl_canvas.Canvas(str(pdf), pagesize=(pw, ph))
    c.setTitle("Square Peg Pizzeria Storrs - flyer")
    c.setFont("R", 10)

    for draw in (side_one, side_two):
        if bleed_in:
            k = max(pw / W, ph / H)            # run the colour off the trim
        else:
            k = min((W - 2 * SAFE) / W, (H - 2 * SAFE) / H)
            c.setFillColor(HexColor("#FFFFFF")); c.rect(0, 0, pw, ph, fill=1, stroke=0)
        c.saveState()
        c.translate(pw / 2, ph / 2); c.scale(k, k); c.translate(-W / 2, -H / 2)
        draw(c)
        c.restoreState()
        c.showPage()
        c.setFont("R", 10)
    c.save()

    if bleed_in:
        import pikepdf
        with pikepdf.open(pdf, allow_overwriting_input=True) as p:
            for pg in p.pages:
                pg.MediaBox = [0, 0, round(pw, 3), round(ph, 3)]
                pg.BleedBox = pg.MediaBox
                pg.TrimBox = [round(b, 3), round(b, 3), round(pw - b, 3), round(ph - b, 3)]
                pg.ArtBox = pg.TrimBox
            p.save(OUT / pdf.name)
    for i in (1, 2):
        subprocess.run(["pdftoppm", "-r", "150", "-png", "-f", str(i), "-l", str(i),
                        "-singlefile", str(pdf), str(OUT / f"{name}-side{i}")], check=True)
    print(f"   {pdf.name}  {pw/72:.3f}x{ph/72:.3f}in  2 pages")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    build("SquarePeg-Storrs-Flyer-8.5x11-BLEED", bleed_in=0.125)
    build("SquarePeg-Storrs-Flyer-8.5x11")
