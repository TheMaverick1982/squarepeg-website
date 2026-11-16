"""Meta hiring ads for Delray Beach.

Three concepts, each in the two sizes Meta actually serves: 4:5 for the
feed and 9:16 for stories and reels. Same artwork laid out for each shape
rather than scaled, so the type never ends up half size in one of them.

Photo on top, brand block underneath. The photo is cover-cropped, so a
landscape source and a portrait source both fill their band without
squashing, and nothing important gets cut because the crop is centred.

Every vertical position is worked out before anything is drawn.

Run:  python3 ads_hiring_delray.py
Out:  Claude outputs/ad-hiring-delray-<concept>-<w>x<h>.png
"""
import subprocess
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
IMGS = ROOT / "assets" / "img-src"
OUT = ROOT / "Claude outputs"
LOGO_LIGHT = ROOT / "src" / "brand" / "logo-on-dark.png"

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

OVEN = HexColor("#1F1A17")
EMBER = HexColor("#D61B24")
FLAME = HexColor("#FFB524")
CREAM = HexColor("#FBF6EC")
WHITE = HexColor("#FFFFFF")
CAP = 0.72          # Big Shoulders cap height as a share of point size
FCAP = 0.72         # Figtree, near enough for placement

CTA = "SQUAREPEGPIZZERIA.COM/CAREERS"

# Which market the run is for. The eyebrow is the only thing that changes:
# one Connecticut line covers all nine CT rooms without naming a town that
# happens not to be hiring that week.
MARKETS = {"delray": "DELRAY BEACH, FL", "ct": "CONNECTICUT"}

CONCEPTS = {
    "crew": {
        "photo": "sp-hero-board.webp",
        "sub": None,
        "roles": ["BARTENDERS", "SERVERS", "PIZZA COOKS", "SAUTÉ COOKS"],
    },
    "kitchen": {
        "photo": "margherita-board.webp",
        "sub": "IN THE KITCHEN",
        "roles": ["PIZZA COOKS", "SAUTÉ COOKS"],
    },
    "front": {
        "photo": "sp-drinks.webp",
        "focus": 0.0,
        "sub": "BAR & DINING ROOM",
        "roles": ["BARTENDERS", "SERVERS"],
    },
}


def white_mark():
    """The logo in flat white. The on-dark file is still the red mark."""
    src = Image.open(LOGO_LIGHT).convert("RGBA")
    flat = Image.new("RGBA", src.size, (255, 255, 255, 0))
    flat.putalpha(src.getchannel("A"))
    return flat


def cover(path, w, h, focus=0.5):
    """Crop to fill w x h without distorting.

    focus says which part of a too-tall source to keep: 0 the top, 0.5 the
    middle, 1 the bottom. A centre crop beheads anything standing up in the
    frame, which is how the cocktails lost their garnish.
    """
    im = Image.open(path).convert("RGB")
    want = w / h
    have = im.width / im.height
    if have > want:                      # too wide, trim the sides
        new_w = int(round(im.height * want))
        x = (im.width - new_w) // 2
        im = im.crop((x, 0, x + new_w, im.height))
    else:                                # too tall, trim top and bottom
        new_h = int(round(im.width / want))
        y = int(round((im.height - new_h) * focus))
        im = im.crop((0, y, im.width, y + new_h))
    return im.resize((int(w), int(h)), Image.LANCZOS)


def wide(c, text, x, y, font, size, track, color, anchor="c"):
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


def wide_width(text, font, size, track):
    return sum(pdfmetrics.stringWidth(ch, font, size) + track for ch in text) - track


def fit_tracked(text, font, size, track, limit):
    while size > 6 and wide_width(text, font, size, track) > limit:
        size -= 0.5
    return size


def draw(c, W, H, spec, mark, eyebrow):
    tall = H / W > 1.4                   # 9:16 rather than 4:5
    c.setFillColor(OVEN)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # --- photo band across the top, with a red rule closing it off -------
    photo_h = H * (0.50 if tall else 0.455)
    rule_h = max(6, H * 0.006)
    img = cover(IMGS / spec["photo"], W, photo_h, spec.get("focus", 0.5))
    c.drawImage(ImageReader(img), 0, H - photo_h, W, photo_h)
    c.setFillColor(EMBER)
    c.rect(0, H - photo_h - rule_h, W, rule_h, stroke=0, fill=1)

    # --- bottom call to action -------------------------------------------
    cta_h = H * (0.070 if tall else 0.082)
    c.setFillColor(EMBER)
    c.rect(0, 0, W, cta_h, stroke=0, fill=1)
    cta_s = fit_tracked(CTA, "B", W * 0.040, W * 0.0030, W * 0.86)
    c.setFillColor(WHITE)
    wide(c, "APPLY AT " + CTA, W / 2,
         cta_h / 2 - cta_s * FCAP / 2, "B",
         fit_tracked("APPLY AT " + CTA, "B", cta_s, W * 0.0022, W * 0.88),
         W * 0.0022, WHITE)

    # --- the block between them, measured first, then centred -------------
    top = H - photo_h - rule_h
    avail = top - cta_h

    logo_h = H * (0.040 if tall else 0.050)
    eye_s = W * (0.034 if tall else 0.030)
    head_s = W * (0.170 if tall else 0.165)
    sub_s = W * (0.062 if tall else 0.056)
    role_s = W * (0.058 if tall else 0.052)
    role_gap = role_s * 0.62

    items = [("logo", logo_h, H * 0.030),
             ("eyebrow", eye_s * FCAP, H * 0.024),
             ("head", head_s * CAP, H * (0.018 if spec["sub"] else 0.026))]
    if spec["sub"]:
        items.append(("sub", sub_s * FCAP, H * 0.030))
    roles_h = len(spec["roles"]) * role_s * FCAP + (len(spec["roles"]) - 1) * role_gap
    items.append(("roles", roles_h, 0))

    block = sum(h for _, h, _ in items) + sum(g for _, _, g in items)
    floor = H * 0.040                             # clear air above the red bar
    slack = max(0.0, avail - block)
    cur = cta_h + avail - min(slack / 2, max(0.0, slack - floor))

    for kind, h, gap in items:
        base = cur - h                            # baseline of this element
        if kind == "logo":
            iw, ih = mark.size
            w = h * iw / ih
            c.drawImage(ImageReader(mark), W / 2 - w / 2, base, w, h, mask="auto")
        elif kind == "eyebrow":
            wide(c, eyebrow, W / 2, base,
                 "B", fit_tracked(eyebrow, "B", eye_s, W * 0.012, W * 0.82),
                 W * 0.012, FLAME)
        elif kind == "head":
            wide(c, "NOW HIRING", W / 2, base, "D",
                 fit_tracked("NOW HIRING", "D", head_s, W * 0.004, W * 0.88),
                 W * 0.004, CREAM)
        elif kind == "sub":
            wide(c, spec["sub"], W / 2, base, "S",
                 fit_tracked(spec["sub"], "S", sub_s, W * 0.006, W * 0.84),
                 W * 0.006, CREAM)
        elif kind == "roles":
            ry = cur - role_s * FCAP
            for r in spec["roles"]:
                wide(c, r, W / 2, ry, "B",
                     fit_tracked(r, "B", role_s, W * 0.010, W * 0.84),
                     W * 0.010, FLAME)
                ry -= role_s * FCAP + role_gap
        cur -= h + gap


def render(name, W, H, spec, mark, eyebrow):
    OUT.mkdir(exist_ok=True)
    scratch = Path.home() / "_adwork"
    scratch.mkdir(exist_ok=True)
    pdf = scratch / f"{name}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H))
    draw(c, W, H, spec, mark, eyebrow)
    c.showPage(); c.save()
    png = OUT / name
    subprocess.run(["pdftoppm", "-png", "-r", "72", "-singlefile", str(pdf), str(png)],
                   check=True)
    print("  ", png.with_suffix(".png").name)


def main():
    mark = white_mark()
    for market, eyebrow in MARKETS.items():
        for key, spec in CONCEPTS.items():
            stem = f"ad-hiring-{market}-{key}"
            render(f"{stem}-1080x1350", 1080, 1350, spec, mark, eyebrow)
            render(f"{stem}-1080x1920", 1080, 1920, spec, mark, eyebrow)


if __name__ == "__main__":
    main()
