"""The flyer a group hands out before its Tuesday fundraiser.

Two files per booking, both generated from the same three facts:

  * an 8.5x11 PDF, no bleed and a white border, light enough for the office
    printer (ink coverage is reported at the end of every run);
  * a 1080x1080 PNG for Instagram, Facebook and the class group chat.

The design is built around the two things that quietly cost a group its money:
people ordering takeout, and people turning up on the wrong Tuesday or at the
wrong Square Peg. The date and the address are therefore the largest things on
the sheet after the group's own name, and DINE IN ONLY is a block of its own
rather than a line of fine print.

Rules text comes from data/content.py (FUNDRAISER_NIGHT), so it can't drift from
the website.

Run:
  python3 flyer_fundraiser.py --group "Lincoln Elementary PTO" \\
          --date 2026-11-11 --location glastonbury-ct
"""
import argparse
import subprocess
import sys
from datetime import date as _date
from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "data"))
from content import LOCATIONS, FUNDRAISER_NIGHT  # noqa: E402

FONTS = ROOT / "src" / "fonts-ttf"
LOGO_R = ROOT / "src" / "brand" / "logo-on-dark.png"     # the red mark, for light grounds
WORK = Path("/tmp/claude-0/fundflyer")
OUT = Path("/mnt/user-data/outputs")
SCAN_URL = "squarepegpizzeria.com/fundraiser-night"

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

INK = HexColor("#120E0C")
RED = HexColor("#D50117")
GOLD = HexColor("#FFB524")
GREY = HexColor("#6B625C")
HAIR = HexColor("#D9D2CA")
PAPER = HexColor("#FFFFFF")
SAND = HexColor("#F4F2F0")

PIL_FONT = {
    "D": FONTS / "big-shoulders-display-latin-900-normal.ttf",
    "B": FONTS / "figtree-latin-800-normal.ttf",
    "S": FONTS / "figtree-latin-700-normal.ttf",
    "M": FONTS / "figtree-latin-600-normal.ttf",
    "R": FONTS / "figtree-latin-400-normal.ttf",
}


# ---------------------------------------------------------------- helpers
def tw(t, f, s):
    return pdfmetrics.stringWidth(t, f, s)


def fit(t, f, maxw, start, floor=10):
    size = start
    while size > floor and tw(t, f, size) > maxw:
        size -= 1
    return size


def text(c, t, f, s, x, y, fill=INK):
    c.setFont(f, s); c.setFillColor(fill); c.drawString(x, y, t)


def centred(c, t, f, s, cx, y, fill=INK):
    c.setFont(f, s); c.setFillColor(fill); c.drawCentredString(cx, y, t)


def ink_box(t, f, size):
    pf = ImageFont.truetype(str(PIL_FONT[f]), int(size))
    ascent, _ = pf.getmetrics()
    x0, y0, x1, y1 = pf.getbbox(t)
    return y1 - y0, ascent - y1


def cap_top(t, f, size):
    pf = ImageFont.truetype(str(PIL_FONT[f]), int(size))
    ascent, _ = pf.getmetrics()
    return ascent - pf.getbbox(t)[1]


def band_text(c, t, f, size, cx, band_y, band_h, fill=PAPER):
    """Optically centre inside a coloured band, by the ink rather than the line box."""
    ink_h, below = ink_box(t, f, size)
    centred(c, t, f, size, cx, band_y + (band_h - ink_h) / 2 + below, fill)


def lines_for(body, f, size, maxw):
    out, line = [], ""
    for w in body.split():
        trial = (line + " " + w).strip()
        if tw(trial, f, size) > maxw and line:
            out.append(line); line = w
        else:
            line = trial
    if line:
        out.append(line)
    return out


def qr_png():
    WORK.mkdir(parents=True, exist_ok=True)
    p = WORK / "qr.png"
    if not p.exists():
        segno.make(f"https://{SCAN_URL}/", error="h").save(str(p), scale=20, border=1)
    return p


def logo_at(c, x, y, w):
    img = ImageReader(str(LOGO_R)); iw, ih = img.getSize()
    h = ih * w / iw
    c.drawImage(img, x, y, width=w, height=h, mask="auto", preserveAspectRatio=True)
    return h


def pretty_date(iso):
    d = _date.fromisoformat(iso)
    if d.weekday() != 1:
        raise SystemExit(f"{iso} is a {d.strftime('%A')} — fundraisers run on Tuesdays.")
    return d.strftime("%A, %B %-d"), d.strftime("%b %-d").upper()


def store_for(slug):
    for l in LOCATIONS:
        if l["slug"] == slug:
            return l
    raise SystemExit(f"unknown location {slug!r}. One of: "
                     + ", ".join(l["slug"] for l in LOCATIONS))


# ---------------------------------------------------------------- the sheet
def flyer(group, iso, store):
    W, H = 8.5 * 72, 11 * 72
    M = 46                                  # white border for a home printer
    inner = W - M * 2
    cx = W / 2
    long_date, _ = pretty_date(iso)
    fn = FUNDRAISER_NIGHT

    OUT.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() else "-" for ch in group).strip("-")[:40]
    pdf = OUT / f"SquarePeg-Fundraiser-{safe}-{iso}.pdf"
    c = rl_canvas.Canvas(str(pdf), pagesize=(W, H))
    c.setTitle(f"{group} fundraiser night at Square Peg {store['name']}")

    # ---- header strip
    bh = 46
    by = H - M - bh
    c.setFillColor(RED); c.rect(M, by, inner, bh, fill=1, stroke=0)
    band_text(c, "TUESDAY FUNDRAISER", "B", 17, cx, by, bh)

    y = by - 26

    # ---- whose night it is
    centred(c, "A FUNDRAISER FOR", "B", 12, cx, y, RED)
    y -= 12
    gs = fit(group.upper(), "D", inner, 50)
    y -= cap_top(group.upper(), "D", gs)
    centred(c, group.upper(), "D", gs, cx, y, INK)
    y -= 18

    # ---- the date, as big as anything on the page
    dh = 80
    dy = y - dh
    c.setFillColor(SAND); c.rect(M, dy, inner, dh, fill=1, stroke=0)
    c.setFillColor(RED); c.rect(M, dy, 7, dh, fill=1, stroke=0)
    # Stack the date and its sub-line as one block, measured by ink. Centring them
    # in two guessed sub-bands is what put "4PM TO CLOSE" through the comma.
    dtxt = long_date.upper()
    stxt = f"{fn['window'].upper()}  ·  DINE IN"
    ds, ss = fit(dtxt, "D", inner - 60, 46), 14
    d_h, d_below = ink_box(dtxt, "D", ds)
    s_h, s_below = ink_box(stxt, "B", ss)
    gap = 13
    block_top = dy + (dh - (d_h + gap + s_h)) / 2 + d_h + gap + s_h
    d_base = block_top - d_h - d_below
    s_base = (d_base + d_below) - gap - s_h - s_below
    centred(c, dtxt, "D", ds, cx, d_base, INK)
    centred(c, stxt, "B", ss, cx, s_base, RED)
    assert s_base + s_below + s_h <= d_base + d_below, "the date and its sub-line overlap"
    y = dy - 22

    # ---- which Square Peg, equally unmissable
    centred(c, "AT SQUARE PEG", "B", 12, cx, y, RED)
    y -= 12
    ns = fit(store["name"].upper(), "D", inner, 36)
    y -= cap_top(store["name"].upper(), "D", ns)
    centred(c, store["name"].upper(), "D", ns, cx, y, INK)
    y -= 15
    addr = f"{store['street']}, {store['city']}, {store['state']}  ·  {store['phone']}"
    centred(c, addr, "M", fit(addr, "M", inner, 15), cx, y, GREY)
    y -= 22

    # ---- the 20%, and the one rule people get wrong
    bh2 = 54
    by2 = y - bh2
    half = inner / 2 - 6
    c.setFillColor(RED); c.rect(M, by2, half, bh2, fill=1, stroke=0)
    band_text(c, f"{fn['share']} BACK", "D", 34, M + half / 2, by2 + 18, bh2 - 18, PAPER)
    band_text(c, "OF DINE-IN FOOD SALES", "B", 10, M + half / 2, by2 + 2, 18, GOLD)
    c.setFillColor(INK); c.rect(W - M - half, by2, half, bh2, fill=1, stroke=0)
    band_text(c, "DINE IN ONLY", "D", 34, W - M - half / 2, by2 + 18, bh2 - 18, PAPER)
    band_text(c, "TAKEOUT & DELIVERY DON’T COUNT", "B", 10,
              W - M - half / 2, by2 + 2, 18, HexColor("#C9BFB7"))
    y = by2 - 26

    # ---- three steps
    centred(c, "HOW TO MAKE IT COUNT", "B", 12, cx, y, RED)
    y -= 18
    col = inner / 3
    top = y
    low = y
    for i, (head, body) in enumerate(fn["steps"]):
        x0 = M + col * i
        c.setFillColor(RED); c.circle(x0 + 17, top - 8, 11, fill=1, stroke=0)
        ih, below = ink_box(str(i + 1), "B", 12)
        centred(c, str(i + 1), "B", 12, x0 + 17, top - 8 - ih / 2 + below, PAPER)
        # The headings are written for the web page and some are too long to sit
        # beside the number at a readable size, so they wrap instead of shrinking
        # to nothing — fit() was bottoming out at its floor and overhanging the margin.
        hs = 12.5
        hw = col - 40
        hl = lines_for(head, "S", hs, hw)
        for n, ln in enumerate(hl):
            assert tw(ln, "S", hs) <= hw + 0.5, f"step heading overflows: {ln!r}"
            text(c, ln, "S", hs, x0 + 34, top - 11 - n * 14, INK)
        yy = top - 11 - (len(hl) - 1) * 14 - 19
        for ln in lines_for(body, "R", 9.3, col - 18):
            text(c, ln, "R", 9.3, x0 + 2, yy, GREY); yy -= 11.6
        low = min(low, yy)
    y = low - 8

    # ---- QR and the page that answers everything else
    qs = 68
    qx = M
    qy = y - qs
    c.drawImage(ImageReader(str(qr_png())), qx, qy, width=qs, height=qs, mask="auto")
    tx = qx + qs + 18
    tw_ = W - M - tx
    # Stack heading, body and URL from the top of the QR rather than pinning the URL
    # to the bottom — with a shorter QR the body was landing on top of it.
    body = ("Scan for what counts, what doesn’t, and the menu. "
            "No ticket needed — just say who you’re with.")
    bl = lines_for(body, "R", 10.5, tw_)
    ty = qy + qs - 22
    text(c, "QUESTIONS?", "D", 24, tx, ty, INK)
    ty -= 17
    for ln in bl:
        text(c, ln, "R", 10.5, tx, ty, GREY); ty -= 13
    ty -= 3
    text(c, SCAN_URL, "B", 11.5, tx, ty, RED)
    assert ty >= qy - 2, "the QR caption runs below the code"
    y = min(qy, ty) - 22

    # ---- footer: the exclusions, in full, and the mark
    foot_bottom = M + 2
    fine = ("Doesn’t count: " + "; ".join(fn["excluded"])
            + ". " + fn["share"] + " of qualifying dine-in food sales, excluding tax and "
            "alcohol, donated to the organization after the event.")
    fl = lines_for(fine, "R", 8, inner - 150)
    lh = logo_at(c, M, foot_bottom, 108)
    fy = foot_bottom + len(fl) * 10.5 - 8
    for ln in fl:
        text(c, ln, "R", 8, M + 128, fy, GREY); fy -= 10.5
    rule_y = foot_bottom + max(lh, len(fl) * 10.5) + 14
    c.setStrokeColor(HAIR); c.setLineWidth(1)
    c.line(M, rule_y, W - M, rule_y)

    assert y > rule_y + 8, f"the QR block runs into the footer ({y:.0f} vs {rule_y:.0f})"
    c.showPage(); c.save()

    png = str(pdf.with_suffix(""))
    subprocess.run(["pdftoppm", "-r", "150", "-png", "-singlefile", str(pdf), png], check=True)
    return pdf, Path(png + ".png")


# ---------------------------------------------------------------- the square
def social(group, iso, store):
    """1080x1080 for Instagram, Facebook and the class group chat."""
    S = 1080
    fn = FUNDRAISER_NIGHT
    long_date, _ = pretty_date(iso)
    im = Image.new("RGB", (S, S), "#FFFFFF")
    d = ImageDraw.Draw(im)

    def F(key, size):
        return ImageFont.truetype(str(PIL_FONT[key]), size)

    def mid(t, f, y, fill):
        w = d.textlength(t, font=f)
        d.text(((S - w) / 2, y), t, font=f, fill=fill)

    def shrink(t, key, maxw, start):
        s = start
        while s > 12 and d.textlength(t, font=F(key, s)) > maxw:
            s -= 2
        return F(key, s)

    d.rectangle([0, 0, S, 86], fill="#D50117")
    f = F("B", 30)
    mid("TUESDAY FUNDRAISER", f, 86 / 2 - 18, "#FFFFFF")

    mid("A FUNDRAISER FOR", F("B", 22), 140, "#D50117")
    gf = shrink(group.upper(), "D", S - 110, 92)
    mid(group.upper(), gf, 176, "#120E0C")

    d.rectangle([60, 300, S - 60, 452], fill="#F4F2F0")
    d.rectangle([60, 300, 72, 452], fill="#D50117")
    df = shrink(long_date.upper(), "D", S - 180, 80)
    mid(long_date.upper(), df, 322, "#120E0C")
    mid(f"{fn['window'].upper()}  ·  DINE IN", F("B", 26), 408, "#D50117")

    mid("AT SQUARE PEG", F("B", 22), 486, "#D50117")
    nf = shrink(store["name"].upper(), "D", S - 120, 72)
    mid(store["name"].upper(), nf, 518, "#120E0C")
    addr = f"{store['street']}, {store['city']}"
    mid(addr, shrink(addr, "M", S - 120, 26), 600, "#6B625C")

    d.rectangle([60, 660, S / 2 - 6, 790], fill="#D50117")
    mid_l = (60 + S / 2 - 6) / 2
    t = f"{fn['share']} BACK"
    d.text((mid_l - d.textlength(t, font=F("D", 64)) / 2, 672), t, font=F("D", 64), fill="#FFFFFF")
    t2 = "OF DINE-IN FOOD SALES"
    d.text((mid_l - d.textlength(t2, font=F("B", 18)) / 2, 752), t2, font=F("B", 18), fill="#FFB524")

    d.rectangle([S / 2 + 6, 660, S - 60, 790], fill="#120E0C")
    mid_r = (S / 2 + 6 + S - 60) / 2
    t3 = "DINE IN ONLY"
    d.text((mid_r - d.textlength(t3, font=F("D", 64)) / 2, 672), t3, font=F("D", 64), fill="#FFFFFF")
    t4 = "TAKEOUT DOESN’T COUNT"
    d.text((mid_r - d.textlength(t4, font=F("B", 18)) / 2, 752), t4, font=F("B", 18), fill="#C9BFB7")

    mid("Tell your server you’re with " + group, shrink(
        "Tell your server you’re with " + group, "M", S - 120, 30), 832, "#120E0C")
    mid(SCAN_URL, F("B", 24), 884, "#D50117")

    logo = Image.open(LOGO_R).convert("RGBA")
    lw = 240
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    im.paste(logo, (int((S - lw) / 2), 940), logo)

    OUT.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() else "-" for ch in group).strip("-")[:40]
    p = OUT / f"SquarePeg-Fundraiser-{safe}-{iso}-social.png"
    im.save(p, "PNG")
    return p


def ink_coverage(png):
    import numpy as np
    a = np.array(Image.open(png).convert("L")).astype(float)
    return (255 - a).mean() / 255 * 100


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", required=True, help="the organisation's name, as they write it")
    ap.add_argument("--date", required=True, help="the Tuesday, as YYYY-MM-DD")
    ap.add_argument("--location", required=True, help="location slug, e.g. glastonbury-ct")
    a = ap.parse_args()
    store = store_for(a.location)
    pdf, preview = flyer(a.group, a.date, store)
    sq = social(a.group, a.date, store)
    print("  ", pdf.name)
    print("  ", sq.name)
    print(f"   ink coverage: {ink_coverage(preview):.1f}%  (letter, no bleed, white border)")
