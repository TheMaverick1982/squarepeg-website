#!/usr/bin/env python3
"""
Square Peg Pizzeria static site builder.

  python3 build.py            -> production site in ./dist  (deploy this folder)
  python3 build.py --preview  -> single-file preview bundle in ./preview

Content lives in data/content.py. Styles in src/site.css. Behavior in src/site.js.
Photos: drop originals into assets/img-src/<name>.(webp|jpg|png) and rebuild.
"""
import json, os, re, shutil, sys, html, hashlib
from datetime import date, timedelta
from html import escape
from urllib.parse import quote_plus
from pathlib import Path
from jinja2 import Environment, DictLoader, select_autoescape
from PIL import Image

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "data"))
from town_pages import TOWN_PAGES  # noqa
from content import HALLOWEEN, HAPPY_HOUR, DEALS, TOAST_ON_SUBDOMAIN, TOAST_SUBDOMAIN, TOAST_MAIN_DOMAIN, TOAST_HOST, TOAST_PATHS, SITE, LOCATIONS, REGIONS, DEAL, POINTS, APP_PERKS, SIGNATURES, REVIEWS, FUNDRAISER_FAQ, FUNDRAISER_NIGHT, CATERING_FAQ, CATERING, TRUCK, TRUCK_FAQ, EVENT_ROUTES, DAYS, SMS_TERMS, DICE, EMBEDS, LARGE_PARTY_FAQ, CONTACT_TOPICS, ENTERTAINMENT, PROMOS, MENU, GAME_DAY, EVENTS, ENT_DATES, LTO, PAIRING, LINKS, CALC, PIZZA_FAQ, PIZZA_TRIVIA, QUIZ, DATE_NIGHT  # noqa

PREVIEW = "--preview" in sys.argv
STAGING = "--staging" in sys.argv   # team review deploy: hidden from Google
OUT = ROOT / ("preview" if PREVIEW else "dist-staging" if STAGING else "dist")
# How long analytics waits before loading itself when the visitor does nothing at
# all. Lower it to lose fewer three-second bounces; raise it for a better score.
TAG_DELAY = 5000
IMG_SRC = ROOT / "assets" / "img-src"
WIDTHS = [360, 480, 640, 800, 1200, 1600]
TODAY = date.today().isoformat()

# Hours-only rebuilds (the nightly Google hours sync on GitHub): reuse the images that are
# already built instead of re-encoding them, so the commit only touches pages.
REUSE = os.environ.get("SP_REUSE_ASSETS") == "1" and not PREVIEW
PREV = OUT.parent / (OUT.name + ".prev")

def reuse(path):
    if not REUSE:
        return False
    old = PREV / path.relative_to(OUT)
    # A zero-byte file means the previous encode failed part way. Treat it as missing
    # so the asset is rebuilt instead of being copied forward run after run.
    if not old.exists() or old.stat().st_size == 0:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(old, path)
    return True

# ---------------------------------------------------------------- hours from Google
# scripts/sync_google_hours.py writes data/hours_google.json from each location's
# Google Business Profile. When a location is in that file, its Google hours replace
# the hours typed into data/content.py (which stay as the fallback).
GOOGLE_HOURS_FILE = ROOT / "data" / "hours_google.json"
DOW_LONG = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}

# ---------------------------------------------------------------- towns served
# data/service_areas.json (scripts/build_service_areas.py): towns within 15 miles of each store.
SERVICE_FILE = ROOT / "data" / "service_areas.json"
STATE_NAMES = {"CT": "Connecticut", "RI": "Rhode Island", "MA": "Massachusetts", "NY": "New York", "FL": "Florida"}
BANDS = [(5, "Under 5 miles"), (10, "5–10 miles"), (15.01, "10–15 miles")]

TOWN_COUNT = 0

def band(mi):
    return next(label for top, label in BANDS if mi < top)

def apply_service_areas():
    data = json.loads(SERVICE_FILE.read_text())["locations"] if SERVICE_FILE.exists() else {}
    for l in LOCATIONS:
        rows = data.get(l["slug"], [])
        l["areas"] = rows
        l["area_bands"] = [(label, [r for r in rows if band(r["mi"]) == label]) for _, label in BANDS]
        l["area_bands"] = [(label, rs) for label, rs in l["area_bands"] if rs]

def town_directory():
    """[(state name, [(town, st, [(loc, mi), ...nearest first]), ...]), ...]"""
    towns = {}
    for l in LOCATIONS:
        for r in l.get("areas", []):
            towns.setdefault((r["name"], r["state"]), []).append((l, r["mi"]))
        towns.setdefault((l["city"], l["state"]), []).insert(0, (l, 0.0))
    out = {}
    for (name, st), hits in towns.items():
        hits = sorted({id(h[0]): h for h in sorted(hits, key=lambda h: -h[1])}.values(), key=lambda h: h[1])
        out.setdefault(st, []).append((name, st, hits))
    order = ["CT", "RI", "MA", "NY", "FL"]
    return [(STATE_NAMES[st], sorted(out[st], key=lambda t: t[0])) for st in order if st in out]

def apply_google_hours():
    if not GOOGLE_HOURS_FILE.exists():
        return 0
    data = json.loads(GOOGLE_HOURS_FILE.read_text()).get("locations", {})
    n = 0
    for l in LOCATIONS:
        l.setdefault("special", {})
        l.setdefault("hours_source", "site")
        g = data.get(l["slug"])
        if not g or not g.get("hours") or set(g["hours"]) != set(DAYS):
            continue
        l["hours"] = {d: (tuple(g["hours"][d]) if g["hours"][d] else None) for d in DAYS}
        l["special"] = {k: (list(v) if v else None) for k, v in sorted(g.get("special", {}).items()) if k >= TODAY}
        l["hours_source"] = "google"
        n += 1
    return n

# ---------------------------------------------------------------- helpers
def url(path):
    """Internal link. Production = clean URLs. Preview = hash routes."""
    if PREVIEW:
        return "#" + path
    return path

def abs_url(path):
    return SITE["domain"].rstrip("/") + path

def tel(phone):
    return "+1" + re.sub(r"\D", "", phone)

def order_url(loc):
    return SITE["order_base"] + loc["toast"]

def maps_url(loc):
    q = f'Square Peg Pizzeria {loc["street"]} {loc["city"]} {loc["state"]} {loc["zip"]}'
    return "https://www.google.com/maps/search/?api=1&query=" + q.replace(" ", "+").replace(",", "")

def maps_embed(loc):
    q = f'Square Peg Pizzeria, {loc["street"]}, {loc["city"]}, {loc["state"]} {loc["zip"]}'
    from urllib.parse import quote_plus
    return "https://www.google.com/maps?output=embed&q=" + quote_plus(q)

def fmt_time(t):
    hh, mm = map(int, t.split(":"))
    if hh == 0 and mm == 0:
        return "12am"
    ap = "pm" if hh >= 12 else "am"
    h12 = hh % 12 or 12
    return f"{h12}{':%02d' % mm if mm else ''}{ap}"

def review_url(l):
    """Where 'Leave a review' goes.

    Prefer the store's own Google review link (the short g.page/r/.../review one from its
    Business Profile) — that opens the review box directly. Until those are filled in, fall
    back to a Maps lookup for the exact address, which opens the Google Maps app on a phone
    and puts the visitor one tap from Reviews.
    """
    own = (l.get("review_url") or "").strip()
    if own:
        return own
    q = quote_plus(f"Square Peg Pizzeria {l['street']} {l['city']} {l['state']} {l['zip']}")
    return f"https://www.google.com/maps/search/?api=1&query={q}"

def hours_rows(loc):
    """(day, full name, hours text, kitchen text or None).

    Several stores keep the bar open after the kitchen stops. Where loc["kitchen"] gives an
    earlier closing time for a day, that day gets a second line so nobody turns up at 10pm
    expecting food. Days without a kitchen entry close together and get no extra line.
    """
    rows = []
    names = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}
    kitchen = loc.get("kitchen") or {}
    for d in DAYS:
        v = loc["hours"][d]
        k = kitchen.get(d)
        note = f"Kitchen closes {fmt_time(k)}" if (v and k and k != v[1]) else None
        rows.append((d, names[d], hours_text(v, " – "), note))
    return rows

def hours_text(v, sep="–"):
    if not v:
        return "Closed"
    if v[0] == "00:00" and v[1] == "00:00":
        return "Open 24 hours"
    return f"{fmt_time(v[0])}{sep}{fmt_time(v[1])}"

def special_rows(loc):
    """Holiday / special hours from Google, e.g. ('2026-11-26', 'Thu, Nov 26', 'Closed')."""
    out = []
    for iso, v in sorted((loc.get("special") or {}).items()):
        if iso < TODAY:
            continue
        dt = date.fromisoformat(iso)
        out.append((iso, f"{dt:%a}, {dt:%b} {dt.day}", hours_text(v, " – ")))
    return out

def hours_summary(loc):
    """Compact lines like 'Mon–Tue 11:30am–9pm'."""
    groups = []
    for d in DAYS:
        v = loc["hours"][d]
        if groups and groups[-1][2] == v:
            groups[-1][1] = d
        else:
            groups.append([d, d, v])
    lines = []
    for a, b, v in groups:
        label = a if a == b else f"{a}–{b}"
        lines.append(f"{label} {hours_text(v)}")
    return lines

# ---------------------------------------------------------------- images
IMG_META = {}

def build_images():
    dest = OUT / "img"
    dest.mkdir(parents=True, exist_ok=True)
    for src in sorted(IMG_SRC.glob("*")):
        if src.suffix.lower() not in (".webp", ".jpg", ".jpeg", ".png"):
            continue
        try:
            im = Image.open(src)
            im.load()
        except Exception:
            print("  ! skipping unreadable image", src.name)
            continue
        im = im.convert("RGBA") if im.mode in ("P", "LA") else im
        has_alpha = im.mode == "RGBA" and im.getextrema()[3][0] < 255
        if not has_alpha:
            im = im.convert("RGB")
        name = src.stem
        w, h = im.size
        widths = [x for x in WIDTHS if x < w] + [min(w, 2000)]
        widths = sorted(set(widths))
        if PREVIEW:
            widths = [x for x in widths if x <= 1200][-2:] or widths[:1]
        for x in widths:
            wp, ap = dest / f"{name}-{x}.webp", dest / f"{name}-{x}.avif"
            if reuse(wp) and reuse(ap):
                continue
            r = im.resize((x, round(h * x / w)), Image.LANCZOS) if x != w else im
            r.save(wp, "WEBP", quality=74, method=6)
            if not PREVIEW:
                r.save(ap, "AVIF", quality=50, speed=6)
        IMG_META[name] = {"w": w, "h": h, "widths": widths, "alpha": has_alpha}
    print(f"  images: {len(IMG_META)} processed")

def build_brand():
    dest = OUT / "img"
    dest.mkdir(parents=True, exist_ok=True)
    src = Image.open(ROOT / "src" / "brand" / "logo-on-dark.png").convert("RGBA")
    orig = Image.open(ROOT / "src" / "brand" / "logo-src.png").convert("RGBA")
    # 360 is the size a 2.6x phone actually needs for the 135px header slot; without
    # it the browser jumps to 480. AVIF carries this logo's soft alpha edges in about
    # 60% of WebP's bytes, so it leads the picture element.
    for w in (160, 280, 360, 480):
        r = None
        if not reuse(dest / f"logo-on-dark-{w}.webp"):
            r = src.resize((w, round(src.height * w / src.width)), Image.LANCZOS)
            r.save(dest / f"logo-on-dark-{w}.webp", "WEBP", quality=72, method=6)
        if not PREVIEW and not reuse(dest / f"logo-on-dark-{w}.avif"):
            r = r or src.resize((w, round(src.height * w / src.width)), Image.LANCZOS)
            r.save(dest / f"logo-on-dark-{w}.avif", "AVIF", quality=50, speed=6)
    if not PREVIEW and not all(reuse(p) for p in (dest / "logo.png", OUT / "favicon-32.png", OUT / "apple-touch-icon.png", OUT / "icon-512.png")):
        orig.resize((1200, round(orig.height * 1200 / orig.width)), Image.LANCZOS).save(dest / "logo.png", optimize=True)
        fav = Image.open(ROOT / "src" / "brand" / "favicon-512.png")
        fav.resize((32, 32), Image.LANCZOS).save(OUT / "favicon-32.png")
        fav.resize((180, 180), Image.LANCZOS).convert("RGB").save(OUT / "apple-touch-icon.png")
        fav.save(OUT / "icon-512.png")
    return round(src.height * 160 / src.width) / 160

PLACEHOLDER = ("data:image/svg+xml," + re.sub(r"\s+", " ", """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 600'><defs><radialGradient id='g' cx='50%' cy='55%' r='60%'>
<stop offset='0' stop-color='%23e0321c'/><stop offset='.55' stop-color='%236b1a0e'/><stop offset='1' stop-color='%23141110'/></radialGradient></defs>
<rect width='800' height='600' fill='url(%23g)'/></svg>""").strip())

def img(name, alt, sizes="100vw", cls="", eager=False, ratio=None):
    m = IMG_META.get(name)
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    c = f' class="{cls}"' if cls else ""
    if not m:
        w, h = (1200, 900)
        return f'<img{c} src="{PLACEHOLDER}" alt="{html.escape(alt)}" width="{w}" height="{h}" {loading}>'
    base = "img/" if PREVIEW else "/img/"
    ws = m["widths"]
    webp = ", ".join(f"{base}{name}-{x}.webp {x}w" for x in ws)
    fallback = f"{base}{name}-{ws[min(len(ws)-1, 1)]}.webp"
    w, h = m["w"], m["h"]
    parts = ["<picture>"]
    if not PREVIEW:
        avif = ", ".join(f"{base}{name}-{x}.avif {x}w" for x in ws)
        parts.append(f'<source type="image/avif" srcset="{avif}" sizes="{sizes}">')
    parts.append(f'<source type="image/webp" srcset="{webp}" sizes="{sizes}">')
    parts.append(f'<img{c} src="{fallback}" alt="{html.escape(alt)}" width="{w}" height="{h}" {loading}>')
    parts.append("</picture>")
    return "".join(parts)

from PIL import ImageDraw, ImageFont

def _font(name, size):
    return ImageFont.truetype(str(ROOT / "src" / "fonts-ttf" / f"{name}.ttf"), size)

def _wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def make_og(key, photo, eyebrow, headline, sub):
    """1200x630 branded social share image."""
    W, H = 1200, 630
    out_dir = OUT / "img" / "og"
    out_dir.mkdir(parents=True, exist_ok=True)
    if reuse(out_dir / f"{key}.jpg"):
        return abs_url(f"/img/og/{key}.jpg")
    canvas = Image.new("RGB", (W, H), (20, 17, 16))
    src_path = next((p for p in IMG_SRC.glob(photo + ".*")), None)
    if src_path:
        ph = Image.open(src_path).convert("RGB")
        tw, th = 760, H
        r = max(tw / ph.width, th / ph.height)
        ph = ph.resize((round(ph.width * r), round(ph.height * r)), Image.LANCZOS)
        left = (ph.width - tw) // 2; top = (ph.height - th) // 2
        canvas.paste(ph.crop((left, top, left + tw, top + th)), (W - tw, 0))
    fade = Image.new("L", (W, 1))
    for x in range(W):
        fade.putpixel((x, 0), 255 if x < 470 else max(0, int(255 * (1 - (x - 470) / 330))))
    canvas.paste(Image.new("RGB", (W, H), (20, 17, 16)), (0, 0), fade.resize((W, H)))
    d = ImageDraw.Draw(canvas)
    logo = Image.open(ROOT / "src" / "brand" / "logo-on-dark.png").convert("RGBA")
    lw = 250; logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    canvas.paste(logo, (64, 52), logo)
    y = 52 + logo.height + 46
    ef = _font("figtree-latin-800-normal", 22)
    d.rectangle((64, y + 5, 78, y + 19), fill=(255, 181, 36))
    d.text((92, y), eyebrow.upper(), font=ef, fill=(255, 181, 36))
    y += 48
    size = 92
    while True:
        hf = _font("big-shoulders-display-latin-900-normal", size)
        lines = _wrap(d, headline.upper(), hf, 620)
        if len(lines) <= 3 or size <= 52: break
        size -= 6
    for ln in lines[:3]:
        d.text((64, y), ln, font=hf, fill=(255, 255, 255))
        y += int(size * 0.98)
    if sub:
        y += 14
        sf = _font("figtree-latin-700-normal", 26)
        for ln in _wrap(d, sub, sf, 620)[:2]:
            y += 8
            d.text((64, y), ln, font=sf, fill=(230, 221, 214))
            y += 30
    d.rectangle((0, H - 14, W, H), fill=(214, 27, 36))
    canvas.save(out_dir / f"{key}.jpg", "JPEG", quality=84, optimize=True, progressive=True)
    return abs_url(f"/img/og/{key}.jpg")

# filled in by build_brand(), which measures the wordmark
LOGO_RATIO = [0.339]


def logo_img(sizes, width, widths=(160, 280, 360, 480), cls="", lazy=False, alt="Square Peg Pizzeria", ratio=None):
    """The wordmark as a <picture>, so browsers that take AVIF get the small file.

    It is the one image on every page, so its bytes are worth the extra markup."""
    base = "img/" if PREVIEW else "/img/"
    h = round(width * (ratio if ratio is not None else LOGO_RATIO[0]))
    c = f' class="{cls}"' if cls else ""
    ld = ' loading="lazy" decoding="async"' if lazy else ""
    webp = ", ".join(f"{base}logo-on-dark-{w}.webp {w}w" for w in widths)
    fallback = f"{base}logo-on-dark-{widths[min(len(widths) - 1, 1)]}.webp"
    out = ["<picture>"]
    if not PREVIEW:
        avif = ", ".join(f"{base}logo-on-dark-{w}.avif {w}w" for w in widths)
        out.append(f'<source type="image/avif" srcset="{avif}" sizes="{sizes}">')
    out.append(f'<source type="image/webp" srcset="{webp}" sizes="{sizes}">')
    out.append(f'<img{c} src="{fallback}" width="{width}" height="{h}" alt="{html.escape(alt)}"{ld}>')
    out.append("</picture>")
    return "".join(out)


def img_url(name, width=1200):
    m = IMG_META.get(name)
    if not m:
        return ""
    x = max([v for v in m["widths"] if v <= width] or m["widths"][:1])
    return abs_url(f"/img/{name}-{x}.webp")

def hero_picture(desk, mob, alt):
    """Art-directed hero: a full photo on desktop, a quiet fire texture on phones."""
    base = "img/" if PREVIEW else "/img/"
    md, mm = IMG_META.get(desk), IMG_META.get(mob)
    if not md or not mm:
        return img(mob, alt, cls="hero-img", eager=True)
    parts = ["<picture>"]
    for fmt in ([] if PREVIEW else ["avif"]) + ["webp"]:
        parts.append(f'<source media="(min-width:900px)" type="image/{fmt}" srcset="' + ", ".join(f"{base}{desk}-{x}.{fmt} {x}w" for x in md["widths"]) + '" sizes="56vw">')
        parts.append(f'<source type="image/{fmt}" srcset="' + ", ".join(f"{base}{mob}-{x}.{fmt} {x}w" for x in mm["widths"]) + '" sizes="100vw">')
    fb = mm["widths"][-1]
    parts.append(f'<img class="hero-img" src="{base}{mob}-{fb}.webp" alt="{html.escape(alt)}" width="{md["w"]}" height="{md["h"]}" fetchpriority="high">')
    parts.append("</picture>")
    return "".join(parts)

def preload(name, sizes="100vw"):
    m = IMG_META.get(name)
    if not m or PREVIEW:
        return ""
    ws = m["widths"]
    srcset = ", ".join(f"/img/{name}-{x}.avif {x}w" for x in ws)
    return f'<link rel="preload" as="image" type="image/avif" imagesrcset="{srcset}" imagesizes="{sizes}" fetchpriority="high">'

# ---------------------------------------------------------------- schema
def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"

def ld_raw(obj):
    """JSON for a page to read at runtime (not schema). Escaped so a '<' in the data
    can't close the script tag early."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

ORG_ID = abs_url("/#org")

def org_schema():
    same = [u for u in (SITE["facebook"], SITE["instagram"]) if u]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": ORG_ID, "name": SITE["name"], "url": abs_url("/"), "email": SITE["email"],
             "founder": [{"@type": "Person", "name": n} for n in ("Jay Maffe", "Carla Boudreau", "Todd Boudreau")],
             "foundingDate": SITE["founded"], "sameAs": same,
             "logo": abs_url("/img/logo.png"), "image": abs_url("/img/logo.png"),
             "subOrganization": [{"@id": abs_url(f"/locations/{l['slug']}/#restaurant")} for l in LOCATIONS]},
            {"@type": "WebSite", "@id": abs_url("/#website"), "url": abs_url("/"), "name": SITE["name"], "publisher": {"@id": ORG_ID}},
        ] + [
            # A short Restaurant node per location, sharing the @id of the full node on that
            # location's own page, so the home page itself carries local-business markup instead
            # of only pointing at it. Same entity, partial description — what @id is for.
            {"@type": "Restaurant", "@id": abs_url(f"/locations/{l['slug']}/") + "#restaurant",
             "name": f"Square Peg Pizzeria {l['name']}", "url": abs_url(f"/locations/{l['slug']}/"),
             "telephone": tel(l["phone"]),
             "address": {"@type": "PostalAddress", "streetAddress": l["street"], "addressLocality": l["city"],
                         "addressRegion": l["state"], "postalCode": l["zip"], "addressCountry": "US"},
             "servesCuisine": ["Italian", "Pizza", "Italian-American", "American"], "priceRange": "$$",
             "parentOrganization": {"@id": ORG_ID}}
            for l in LOCATIONS
        ],
    }

def restaurant_schema(l):
    spec = []
    for d in DAYS:
        v = l["hours"][d]
        if not v:
            continue
        spec.append({"@type": "OpeningHoursSpecification",
                     "dayOfWeek": {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}[d],
                     "opens": v[0], "closes": "23:59" if v[1] == "00:00" else v[1]})
    special = []
    for iso, v in sorted((l.get("special") or {}).items()):
        if iso < TODAY:
            continue
        # Closed all day = opens and closes at 00:00 (Google's recommended markup)
        special.append({"@type": "OpeningHoursSpecification", "validFrom": iso, "validThrough": iso,
                        "opens": v[0] if v else "00:00", "closes": ("23:59" if v[1] == "00:00" else v[1]) if v else "00:00"})
    page = abs_url(f"/locations/{l['slug']}/")
    o = {
        "@type": "Restaurant", "@id": page + "#restaurant",
        "name": f"Square Peg Pizzeria {l['name']}",
        "url": page, "telephone": tel(l["phone"]),
        "address": {"@type": "PostalAddress", "streetAddress": l["street"], "addressLocality": l["city"], "addressRegion": l["state"], "postalCode": l["zip"], "addressCountry": "US"},
        "servesCuisine": ["Italian", "Pizza", "Italian-American", "American"], "priceRange": "$$",
        "hasMenu": order_url(l), "menu": order_url(l), "parentOrganization": {"@id": ORG_ID},
        "openingHoursSpecification": spec,
        **({"specialOpeningHoursSpecification": special} if special else {}),
        "hasMap": maps_url(l),
        "areaServed": [{"@type": "City", "name": f"{t}, {st}"} for t, st in dict.fromkeys(
                           [(l["city"], l["state"])] + [(t, l["state"]) for t in l["nearby"]] + [(r["name"], r["state"]) for r in l.get("areas", [])])]
                       + [{"@type": "GeoCircle", "geoMidpoint": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lng"]}, "geoRadius": "24140"}],
        "sameAs": l.get("same_as", []),
        "currenciesAccepted": "USD",
        "potentialAction": {"@type": "OrderAction", "target": {"@type": "EntryPoint", "urlTemplate": order_url(l), "actionPlatform": ["http://schema.org/DesktopWebPlatform", "http://schema.org/MobileWebPlatform"]}, "deliveryMethod": ["http://purl.org/goodrelations/v1#DeliveryModePickUp"]},
    }
    if img_url(l["photo"]):
        o["image"] = img_url(l["photo"])
    if l.get("geo_exact"):
        o["geo"] = {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lng"]}
    return o

def breadcrumbs(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(p)} for i, (n, p) in enumerate(items)]}

def faq_schema(faqs):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}

def graph(*nodes):
    return {"@context": "https://schema.org", "@graph": list(nodes)}

# ---------------------------------------------------------------- templates
# ---------------------------------------------------------------- Halloween art
# Drawn here rather than loaded as files: a handful of flat shapes that inherit
# currentColor, so one CSS rule tints them per section. All decorative, so all
# aria-hidden.
HW_ART = {
    "web": ('<svg class="hw-web" viewBox="0 0 100 100" fill="none" stroke="currentColor" '
            'stroke-width="1.4" aria-hidden="true"><path d="@@WEB@@"/></svg>'),

    "spider": ('<svg class="hw-spider-svg" viewBox="0 0 64 54" fill="none" aria-hidden="true">'
               '<g stroke="currentColor" stroke-width="2.6" stroke-linecap="round">'
               '<path d="M26 26 14 18 4 22"/><path d="M26 31 12 31 3 37"/>'
               '<path d="M26 36 13 43 6 51"/><path d="M27 22 20 12 22 4"/>'
               '<path d="M38 26 50 18 60 22"/><path d="M38 31 52 31 61 37"/>'
               '<path d="M38 36 51 43 58 51"/><path d="M37 22 44 12 42 4"/></g>'
               '<ellipse cx="32" cy="33" rx="11" ry="13" fill="currentColor"/>'
               '<circle cx="32" cy="19" r="7" fill="currentColor"/>'
               '<circle cx="29" cy="18" r="1.8" fill="#fff"/><circle cx="35" cy="18" r="1.8" fill="#fff"/>'
               '</svg>'),

    "ghost": ('<svg class="hw-ghost-svg" viewBox="0 0 100 110" aria-hidden="true">'
              '<path fill="currentColor" d="M50 6c22 0 38 16 38 38v54c-5 0-8-6-12-6s-6 6-11 6-7-6-11-6'
              '-6 6-10 6-6-6-10-6-7 6-12 6V44C22 22 28 6 50 6z"/>'
              '<ellipse cx="38" cy="44" rx="6" ry="8" fill="#17120F"/>'
              '<ellipse cx="62" cy="44" rx="6" ry="8" fill="#17120F"/>'
              '<ellipse cx="50" cy="64" rx="7" ry="9" fill="#17120F" opacity=".75"/></svg>'),

    "pumpkin": ('<svg class="hw-pumpkin-svg" viewBox="0 0 110 100" aria-hidden="true">'
                '<path d="M55 20c3-9 10-14 18-13-3 7-8 11-14 13" fill="#3F7A2E"/>'
                '<rect x="51" y="12" width="8" height="14" rx="3" fill="#3F7A2E"/>'
                '<ellipse cx="30" cy="62" rx="24" ry="33" fill="currentColor" opacity=".82"/>'
                '<ellipse cx="80" cy="62" rx="24" ry="33" fill="currentColor" opacity=".82"/>'
                '<ellipse cx="55" cy="62" rx="31" ry="35" fill="currentColor"/>'
                '<path d="M36 50l11 10H25zM74 50l11 10H63z" fill="#17120F"/>'
                '<path d="M33 74h44l-6 9h-8l-5-6-5 6h-8z" fill="#17120F"/></svg>'),

    "costumes": ('<svg class="hw-costumes" aria-hidden="true" preserveAspectRatio="none"><defs><pattern id="hw-cos" width="440" height="300" patternUnits="userSpaceOnUse"><g transform="translate(10 6) rotate(-11 50 50) scale(0.52)"><path d="M50 6c3 20 9 44 18 62H32c9-18 15-42 18-62zM10 70c0-6 18-10 40-10s40 4 40 10-18 10-40 10-40-4-40-10z" fill="currentColor" fill-rule="nonzero"/></g><g transform="translate(112 30) rotate(7 50 50) scale(0.46)"><path d="M50 6c20 0 34 15 34 36v50c-5 0-7-6-11-6s-5 6-10 6-6-6-10-6-5 6-10 6-6-6-10-6-6 6-11 6V42C22 21 30 6 50 6zM38 38a5 7 0 1 0 .1 0zM62 38a5 7 0 1 0 .1 0z" fill="currentColor" fill-rule="evenodd"/></g><g transform="translate(206 2) rotate(-5 50 50) scale(0.6)"><path d="M50 34c3 0 5 2 6 5 6-8 15-12 24-13-4 4-6 9-5 15 5-3 10-3 14 0-8 2-13 7-15 15-7-5-16-7-24-5-8-2-17 0-24 5-2-8-7-13-15-15 4-3 9-3 14 0-1-6 1-11-5-15 9 1 18 5 24 13 1-3 3-5 6-5z" fill="currentColor" fill-rule="nonzero"/></g><g transform="translate(302 28) rotate(9 50 50) scale(0.5)"><path d="M50 26c20 0 34 15 34 35S70 96 50 96 16 81 16 61s14-35 34-35zM46 14h8v14h-8zM50 20c3-8 9-12 16-11-3 6-7 10-12 12z" fill="currentColor" fill-rule="nonzero"/></g><g transform="translate(388 4) rotate(-6 50 50) scale(0.46)"><path d="M26 98V46c0-13 11-24 24-24s24 11 24 24v52zM16 92h68v10H16z" fill="currentColor" fill-rule="nonzero"/></g><g transform="translate(56 150) rotate(5 50 50) scale(0.5)"><path d="M34 24l-6-18 16 10zM66 24l6-18-16 10zM50 14c14 0 24 10 24 23 0 7-3 13-8 17 6 7 10 18 10 30 0 8-12 12-26 12s-26-4-26-12c0-12 4-23 10-30-5-4-8-10-8-17 0-13 10-23 24-23zM72 92c10-1 16-8 16-17 0-7-4-12-10-13v8c3 1 4 3 4 6 0 5-4 8-10 9z" fill="currentColor" fill-rule="nonzero"/></g><g transform="translate(158 170) rotate(-8 50 50) scale(0.44)"><path d="M50 8c21 0 36 15 36 35 0 12-5 19-10 24v13c0 5-4 8-9 8H33c-5 0-9-3-9-8V67C19 62 14 55 14 43 14 23 29 8 50 8zM36 38a8 9 0 1 0 .1 0zM64 38a8 9 0 1 0 .1 0zM50 54l-6 10h12z" fill="currentColor" fill-rule="evenodd"/></g><g transform="translate(252 158) rotate(4 50 50) scale(0.5)"><path d="M18 46h64c0 23-14 38-32 38S18 69 18 46zM10 38h80v10H10zM28 80l-8 14 7 4 8-14zM72 80l8 14-7 4-8-14z" fill="currentColor" fill-rule="nonzero"/></g><g transform="translate(348 150) rotate(16 50 50) scale(0.48)"><path d="M44 4h12v54H44zM28 58h44l9 38-7 2-7-28-3 30h-8l-4-30-4 30h-8l-3-30-7 28-7-2z" fill="currentColor" fill-rule="nonzero"/></g><g transform="translate(-34 164) rotate(-4 50 50) scale(0.4)"><path d="M50 6c20 0 34 15 34 36v50c-5 0-7-6-11-6s-5 6-10 6-6-6-10-6-5 6-10 6-6-6-10-6-6 6-11 6V42C22 21 30 6 50 6zM38 38a5 7 0 1 0 .1 0zM62 38a5 7 0 1 0 .1 0z" fill="currentColor" fill-rule="evenodd"/></g></pattern></defs><rect width="100%" height="100%" fill="url(#hw-cos)"/></svg>'),

    "bat": ('<svg class="hw-bat-svg" viewBox="0 0 120 56" aria-hidden="true">'
            '<path fill="currentColor" d="M60 12c4 0 7 3 8 7 7-9 17-14 28-15-5 5-7 11-6 18 5-3 11-3 16 0'
            '-9 2-15 8-18 17-8-6-18-8-28-6-10-2-20 0-28 6-3-9-9-15-18-17 5-3 11-3 16 0-1-7 1-13-6-18'
            ' 11 1 21 6 28 15 1-4 4-7 8-7z"/></svg>'),
}
HW_ART["web"] = HW_ART["web"].replace("@@WEB@@", "M0 0L100.0 0.0M0 0L95.1 30.9M0 0L80.9 58.8M0 0L58.8 80.9M0 0L30.9 95.1M0 0L0.0 100.0M26.0 0.0Q19.3 3.1 24.7 8.0M24.7 8.0Q17.4 8.9 21.0 15.3M21.0 15.3Q13.8 13.8 15.3 21.0M15.3 21.0Q8.9 17.4 8.0 24.7M8.0 24.7Q3.1 19.3 0.0 26.0M46.0 0.0Q34.2 5.4 43.7 14.2M43.7 14.2Q30.8 15.7 37.2 27.0M37.2 27.0Q24.5 24.5 27.0 37.2M27.0 37.2Q15.7 30.8 14.2 43.7M14.2 43.7Q5.4 34.2 0.0 46.0M66.0 0.0Q49.0 7.8 62.8 20.4M62.8 20.4Q44.2 22.5 53.4 38.8M53.4 38.8Q35.1 35.1 38.8 53.4M38.8 53.4Q22.5 44.2 20.4 62.8M20.4 62.8Q7.8 49.0 0.0 66.0M88.0 0.0Q65.4 10.4 83.7 27.2M83.7 27.2Q59.0 30.1 71.2 51.7M71.2 51.7Q46.8 46.8 51.7 71.2M51.7 71.2Q30.1 59.0 27.2 83.7M27.2 83.7Q10.4 65.4 0.0 88.0")

ICONS = {
    "bag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M5 8h14l-1 12H6L5 8Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg>',
    "tag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M3 12V3h9l9 9-9 9-9-9Z"/><circle cx="7.5" cy="7.5" r="1.5"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
}

NAV = [("Menu", "MENU"), ("Locations", "/locations/"), ("Specials", "/promotions/"), ("Catering", "/catering/"),
       ("Entertainment", "/entertainment/")]
# The desktop "More" dropdown, grouped into columns. A flat list of eighteen links is
# a wall; the grouping mirrors the mobile drawer so the site reads the same either way.
# Game Day is injected into "Fun" by the template because it is season-gated.
MORE_GROUPS = [
    ("Eat", [("LTO Menu", "/monthly-specials/"), ("What\u2019s on the Menu", "/our-menu/"),
             ("Pairing Guide", "/pairing/"), ("Rewards & Monthly Deals", "/deals/")]),
    ("Plan", [("Large Parties", "/large-party-reservations/"), ("Private Events & Classes", "/private-events/"),
              ("Food Truck", "/food-truck/"), ("Tuesday Fundraisers", "/fundraisers/")]),
    ("Fun", [("Halloween", "/halloween/"), ("Roll the Dice", "/roll-the-dice/"), ("Date Night", "/date-night/"),
             ("What Pizza Are You?", "/what-pizza-are-you/"), ("Pizza Trivia", "/pizza-trivia/")]),
    ("Helpful", [("Pizza Calculator", "/pizza-calculator/"), ("Pizza FAQ", "/pizza-faq/"),
                 ("Gift Cards", "GIFT")]),
    ("Square Peg", [("Our Story", "/about/"), ("Careers", "/careers/"), ("Contact", "/contact/")]),
]
# Flat list kept for anything that still wants every "more" destination in one go.
MORE = [item for _, items in MORE_GROUPS for item in items]
DRAWER_EXTRA = []
DRAWER_GROUPS = [
    ("Eat", [("Menu", "MENU"), ("LTO Menu", "/monthly-specials/"), ("Pairing Guide", "/pairing/"), ("What’s on the Menu", "/our-menu/"), ("Locations", "/locations/"), ("Specials", "/promotions/"), ("Rewards & Deals", "/deals/")]),
    ("Plan", [("Catering", "/catering/"), ("Large Parties", "/large-party-reservations/"), ("Private Events & Classes", "/private-events/"), ("Food Truck", "/food-truck/"), ("Tuesday Fundraisers", "/fundraisers/")]),
    ("Fun", [("Entertainment", "/entertainment/"), ("Roll the Dice", "/roll-the-dice/"), ("Gift Cards", "GIFT")]),
    ("Square Peg", [("Our Story", "/about/"), ("Careers", "/careers/"), ("Contact", "/contact/")]),
]
DAY_NAMES = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}

# Entertainment rows are (day, event, time) or (day, event, time, start date). Pad to four so
# every template can unpack the same shape.
ENTERTAINMENT = {slug: [tuple(r) + (None,) * (4 - len(r)) for r in rows] for slug, rows in ENTERTAINMENT.items()}

def ent_from(iso):
    """'2026-09-26' -> 'Sept 26', for the 'starts soon' badge."""
    if not iso:
        return ""
    d = date.fromisoformat(iso)
    return f'{["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"][d.month - 1]} {d.day}'


_NUMS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]

def _count(n):
    """Small numbers read better spelled out in share-card copy."""
    return _NUMS[n] if 0 <= n <= 10 else str(n)

def _qty(n, one, many):
    return f"{_count(n)} {one if n == 1 else many}"

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def ent_dated(loc):
    """One-off entertainment dates for a location, sorted, with a short label.

    Each card carries its own hide date, so a night that has passed drops off
    on its own while the later ones stay."""
    out = []
    for iso, what, when in sorted(ENT_DATES.get(loc["slug"], [])):
        d = date.fromisoformat(iso)
        out.append((iso, what, when,
                    f"{_WEEKDAYS[d.weekday()][:3]} {_MONTHS[d.month - 1]} {d.day}"))
    return out


def location_events(loc):
    """Ticketed events for one location, with the date pre-formatted for the card.

    The block hides itself in the browser the day after the event (see
    paintSeason in site.js), so nobody has to remember to pull it down."""
    out = []
    for e in EVENTS.get(loc["slug"], []):
        d = date.fromisoformat(e["date"])
        out.append(dict(e,
                        mon=_MONTHS[d.month - 1],
                        day=d.day,
                        weekday=_WEEKDAYS[d.weekday()],
                        long_date=f"{_WEEKDAYS[d.weekday()]}, {_MONTHS[d.month - 1]} {d.day}",
                        announce=e.get("announce", "2000-01-01")))
    return out

# The three photos the /what-you-did/ flyer promises. Real shots, evidence captions.
CAUGHT_SHOTS = [
    ("sp-pies-board", "Exhibit A", "The board",
     "Two of them. Side by side, in broad daylight. No attempt whatsoever to hide it."),
    ("sp-wings", "Exhibit B", "Garlic parm wings",
     "You told someone you were “just grabbing a salad.” The plate tells a different story."),
    ("sp-drinks", "Exhibit C", "Two o'clock",
     "Happy hour runs 2–6pm, every day. We are not saying the timing is related. We are showing it."),
]

T = {}

T["head"] = """<title>{{ title }}</title>
{% if staging %}<meta name="robots" content="noindex, nofollow">{% endif %}<meta name="description" content="{{ desc }}">
{% if not preview %}<link rel="canonical" href="{{ canonical }}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Square Peg Pizzeria"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{{ title }}"><meta property="og:description" content="{{ desc }}">
<meta property="og:url" content="{{ canonical }}">{% if og_image %}<meta property="og:image" content="{{ og_image }}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{{ og_alt }}">{% endif %}
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{{ title }}"><meta name="twitter:description" content="{{ desc }}">{% if og_image %}<meta name="twitter:image" content="{{ og_image }}">{% endif %}
<meta name="theme-color" content="#141110">
<link rel="icon" href="/favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="/apple-touch-icon.png">{% endif %}
{% if preview %}<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@800;900&family=Figtree:wght@400;600;700;800&display=swap">{% else %}
<link rel="preload" href="/fonts/big-shoulders-display-latin-800-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/figtree-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>{% endif %}
{{ preload_tag|safe }}
<style>{{ css|safe }}</style>
{{ schema|safe }}"""

T["header"] = """<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="logo" href="{{ u('/') }}" aria-label="Square Peg Pizzeria home">
      {{ logo_img("(min-width:980px) 153px, 135px", 160)|safe }}
    </a>
    <nav class="nav" aria-label="Main">{% for n, p in nav %}{% if p == 'MENU' %}<a href="{{ site.menu_url }}" data-open-picker="menu">{{ n }}</a>{% else %}<a href="{{ u(p) }}"{% if p == path %} aria-current="page"{% endif %}>{{ n }}</a>{% endif %}{% endfor %}
      <details class="more"><summary>More</summary><div class="more-menu more-mega">{% for group, items in more_groups %}<div class="more-col">
        <span class="more-h">{{ group }}</span>
        {% if group == 'Fun' %}<a class="nav-gd" href="{{ u('/game-day/') }}" data-season-from="{{ gd.season_from }}" data-season-to="{{ gd.season_to }}"{% if path == '/game-day/' %} aria-current="page"{% endif %}>Game Day</a>{% endif %}
        {% for n, p in items %}{% if p == 'GIFT' %}<a href="{{ site.gift_cards_url }}" rel="noopener"{{ ext|safe }}>{{ n }}</a>{% else %}<a href="{{ u(p) }}"{% if p == path %} aria-current="page"{% endif %}>{{ n }}</a>{% endif %}{% endfor %}
      </div>{% endfor %}</div></details></nav>
    <details class="more signin"><summary>Sign in</summary><div class="more-menu more-menu--right">
      <a href="{{ site.toast_account }}" rel="noopener"{{ ext|safe }}>Ordering account <span>Toast: saved cards &amp; past orders</span></a>
      <a href="{{ site.loyalty_signin }}" rel="noopener"{{ ext|safe }}>Rewards account <span>Points, offers &amp; rewards</span></a>
      <a href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="signin"{{ ext|safe }}>Get the app <span>$5 off your first order</span></a>
    </div></details>
    <a class="btn btn--sm header-order" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.bag|safe }}Order<span class="for" data-for-loc></span></a>
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="drawer" aria-label="Open menu">{{ icons.menu|safe }}</button>
  </div>
  <div class="drawer" id="drawer">
    <div class="wrap drawer-inner">
      <div class="drawer-cta">
        <a class="btn" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.bag|safe }}Order online</a>
        <a class="btn btn--ghost" href="{{ u('/locations/') }}" data-open-picker="call">{{ icons.phone|safe }}Call</a>
      </div>
      <nav aria-label="Mobile">
        {% for title, links in drawer_groups %}<div class="drawer-group"><p class="drawer-title">{{ title }}</p>
          {% for n, p in links %}{% if p == 'MENU' %}<a href="{{ site.menu_url }}" data-open-picker="menu">{{ n }}</a>{% elif p == 'GIFT' %}<a href="{{ site.gift_cards_url }}" rel="noopener"{{ ext|safe }}>{{ n }}</a>{% else %}<a href="{{ u(p) }}"{% if p == path %} aria-current="page"{% endif %}>{{ n }}</a>{% endif %}{% endfor %}{% if title == 'Fun' %}<a href="{{ u('/game-day/') }}" data-season-from="{{ gd.season_from }}" data-season-to="{{ gd.season_to }}"{% if path == '/game-day/' %} aria-current="page"{% endif %}>Game Day</a>{% endif %}
        </div>{% endfor %}
      </nav>
      <div class="drawer-group"><p class="drawer-title">Sign in</p>
        <a href="{{ site.toast_account }}" rel="noopener"{{ ext|safe }}>Ordering account (Toast)</a>
        <a href="{{ site.loyalty_signin }}" rel="noopener"{{ ext|safe }}>Rewards account</a>
      </div>
      <a class="drawer-app" href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="drawer"{{ ext|safe }}><b>Get the Square Peg app</b><span>$5 off your next order + rewards every visit</span></a>
    </div>
  </div>
</header>"""

T["footer"] = """<section class="cta-band">
  <div class="wrap">
    <span class="eyebrow" style="color:#fff">Hungry yet?</span>
    <h2>The oven’s already hot.</h2>
    <div class="btn-row">
      <a class="btn" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.bag|safe }}Order pickup or delivery</a>
      <a class="btn btn--ghost" href="{{ u('/locations/') }}">Find a Square Peg</a>
    </div>
  </div>
</section>
<footer class="site-footer">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        {{ logo_img("220px", 480, cls="foot-logo", lazy=True)|safe }}
        <p class="foot-title">10 Square Pegs</p>
        <div class="foot-locs">
          {% for l in locs %}<div><a href="{{ u('/locations/' ~ l.slug ~ '/') }}">{{ l.name }}</a><span>{{ l.street }}, {{ l.city }}, {{ l.state }}</span><a class="ph" href="tel:{{ tel(l.phone) }}">{{ l.phone }}</a></div>{% endfor %}
        </div>
      </div>
      <div class="foot-links">
        <a href="{{ site.menu_url }}" data-open-picker="menu">Order &amp; Live Menu</a><a href="{{ u('/our-menu/') }}">What’s on the Menu</a><a href="{{ u('/catering/') }}">Catering</a><a href="{{ u('/large-party-reservations/') }}">Large Parties</a><a href="{{ u('/food-truck/') }}">Food Truck</a>
        <a href="{{ u('/promotions/') }}">Specials</a><a href="{{ u('/deals/') }}">Rewards & Deals</a><a href="{{ u('/entertainment/') }}">Entertainment</a><a href="{{ u('/private-events/') }}">Private Events & Classes</a><a href="{{ u('/fundraisers/') }}">Tuesday Fundraisers</a><a href="{{ u('/about/') }}">Our Story</a><a href="{{ u('/contact/') }}">Contact</a><a href="{{ u('/areas-we-serve/') }}">Towns We Serve</a>
        <a href="{{ site.gift_cards_url }}" rel="noopener"{{ ext|safe }}>Gift Cards</a><a href="{{ u('/roll-the-dice/') }}">Roll the Dice</a><a href="{{ u('/careers/') }}">Careers</a><a href="{{ site.app_link }}" rel="noopener"{{ ext|safe }}>Get the App</a>
        {% if site.facebook %}<a href="{{ site.facebook }}" rel="noopener"{{ ext|safe }}>Facebook</a>{% endif %}
        {% if site.instagram %}<a href="{{ site.instagram }}" rel="noopener"{{ ext|safe }}>Instagram</a>{% endif %}
      </div>
    </div>
    <div class="be-nice" aria-hidden="true" data-text="Be Nice."></div>
    <div class="foot-base">
      <span>© {{ year }} Square Peg Pizzeria. Wood-fired in Connecticut & Delray Beach, FL.</span>
      <span><a href="{{ u('/privacy/') }}">Privacy Policy</a> · <a href="{{ u('/terms/') }}">Terms &amp; Conditions</a> · <a href="{{ u('/sms-terms/') }}">SMS Terms</a> · <a href="{{ site.loyalty_signin }}" rel="noopener"{{ ext|safe }}>Rewards sign-in</a></span>
    </div>
  </div>
</footer>
<nav class="mbar" aria-label="Quick actions">
  <a class="mbar-order" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.bag|safe }}<span>Order</span></a>
  <a id="mbar-call" href="{{ u('/locations/') }}" data-open-picker="call">{{ icons.phone|safe }}Call</a>
  <a href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find us</a>
</nav>
<dialog class="sheet" id="picker" aria-labelledby="picker-title">
  <div class="sheet-inner">
    <div class="sheet-head"><h2 id="picker-title">Pick your Peg</h2><button class="sheet-close" type="button" data-close aria-label="Close">×</button></div>
    <div class="sheet-tools"><button class="geo-btn" id="geo-sheet" type="button">Use my location to sort nearest</button><span class="note" id="picker-sub">Pickup or delivery, chosen at checkout</span></div>
    <div class="sheet-list" id="picker-list"></div>
  </div>
</dialog>
<script type="application/json" id="sp-locs">{{ locs_json|safe }}</script>
<script type="application/json" id="sp-cfg">{{ cfg_json|safe }}</script>
<script type="application/json" id="sp-ent">{{ ent_json|safe }}</script>"""

T["loc_card"] = """<article class="loc-card" data-slug="{{ l.slug }}">
  <header><div><span class="tag">{{ l.tag }}</span><h3><a href="{{ u('/locations/' ~ l.slug ~ '/') }}">{{ l.name }}</a></h3></div><span class="status" data-status="{{ l.slug }}">{{ l.summary[0] }}</span></header>
  <address>{{ l.street }}<br>{{ l.city }}, {{ l.state }} {{ l.zip }}</address>
  {% if ent.get(l.slug) %}<div class="card-ent" aria-label="Weekly entertainment">{% for d, e, t, fr in ent[l.slug] %}<span class="ent-chip" data-ent-day="{{ d }}"{% if fr %} data-ent-from="{{ fr }}"{% endif %}><b>{{ d }}</b> {{ e }}{% if fr %} <i class="ent-soon">from {{ ent_from(fr) }}</i>{% endif %}</span>{% endfor %}</div>{% endif %}
  <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><a class="phone" href="tel:{{ tel(l.phone) }}" data-track="call_click" data-loc="{{ l.slug }}">{{ l.phone }}</a><span class="dist"></span></div>
  <div class="btn-row">
    <a class="btn btn--sm" href="{{ order(l) }}" data-pick="{{ l.slug }}" data-track="order_click" data-src="loc-card" rel="noopener" aria-label="Order: Square Peg {{ l.short or l.name }}">{{ icons.bag|safe }}Order</a>
    <a class="btn btn--sm btn--ghost" href="{{ u('/locations/' ~ l.slug ~ '/') }}" aria-label="Hours & info: Square Peg {{ l.short or l.name }}">Hours & info</a>
  </div>
</article>"""

T["page"] = """{% if not preview %}<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{% endif %}{% include "head" %}{% if not preview %}
{{ analytics|safe }}
</head><body>{% endif %}
{% if not bare %}{% include "header" %}{% endif %}
<main id="main">{{ body|safe }}</main>
{% if not bare %}{% include "footer" %}{% endif %}
{% if not preview %}<script src="/site.js?v={{ jsv }}" defer></script>
</body></html>{% endif %}"""

# ---------- HOME
T["home"] = """
<section class="hero on-dark">
  {{ hero_picture('margherita-board', 'oven-fire', 'A wood-fired margherita pizza fresh from the Square Peg oven')|safe }}
  <div class="wrap">
    <h1><span class="eyebrow h1-eyebrow"><span>Italian restaurant &amp; wood-fired pizza · CT &amp; Delray Beach, FL</span></span>Pizza worth <em>remembering.</em></h1>
    <p class="lede">Hand-stretched dough, a screaming-hot oven, and ten Square Pegs across Connecticut and Delray Beach. Order in under a minute.</p>
    <div class="hero-meta"><span>Pickup & delivery</span><span>12″ gluten-free crust</span><span>Catering for any crowd</span></div>
    <form class="quick" onsubmit="return false" aria-label="Quick order">
      <div class="stack" style="gap:8px">
        <label for="quick-loc">Order from</label>
        <select class="select" id="quick-loc" name="location">
          <option value="">Choose your Square Peg…</option>
          {% for r in regions %}<optgroup label="{{ r }}">{% for l in locs if l.region == r %}<option value="{{ l.slug }}">{{ l.name }} · {{ l.city }}, {{ l.state }}</option>{% endfor %}</optgroup>{% endfor %}
        </select>
        <div class="quick-status" id="quick-status"><button class="geo-btn" id="geo-quick" type="button">Find the one closest to me</button></div>
      </div>
      <div class="quick-actions">
        <a class="btn" id="quick-order" href="{{ u('/locations/') }}" data-open-picker="order" data-track="order_click" data-src="hero-quick" rel="noopener">{{ icons.bag|safe }}<span>Start my order</span></a>
        <a class="btn btn--line" id="quick-call" href="{{ u('/locations/') }}">{{ icons.phone|safe }}Call</a>
        <a class="btn btn--line" id="quick-info" href="{{ u('/locations/') }}">Hours</a>
      </div>
    </form>
  </div>
</section>

{% for d in deals %}<div class="ribbon" data-season-from="{{ d.starts }}" data-season-to="{{ d.expires }}" hidden><div class="wrap">
  <strong>{{ d.headline }}</strong><span>{{ d.eyebrow }} · Mon–Fri dine-in · {{ d.expires_label }}</span>
  <a href="{{ u('/deals/') }}">See all deals →</a>
</div></div>{% endfor %}

<aside class="gd-strip" aria-label="Game day specials" data-season-from="{{ gd.season_from }}" data-season-to="{{ gd.season_to }}"><div class="wrap">
  <div class="gd-strip-copy">
    <span class="gd-strip-tag">Game day</span>
    <p><strong>Football season tastes better here.</strong> <span>$4 Green Tea shots, $7 cocktails and $4 Miller Lite during every game.</span></p>
  </div>
  <a class="btn btn--sm" href="{{ u('/game-day/') }}" data-track="game_day_click" data-src="home-strip">See game day specials</a>
</div></aside>

<aside class="loyalty-strip" aria-label="Square Peg Rewards"><div class="wrap">
  <div class="loyalty-copy">
    <span class="loyalty-tag">Rewards</span>
    <p><strong>Join Square Peg Rewards. It's free.</strong> <span>$5 welcome reward, points every visit and members-only deals.</span></p>
  </div>
  <div class="loyalty-actions">
    <a class="btn btn--flame btn--sm" href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="home-loyalty">Get the app</a>
    <a class="btn btn--ghost btn--sm" href="{{ site.loyalty_signup }}" rel="noopener" data-track="loyalty_signup_click" data-src="home-loyalty">Sign up online</a>
  </div>
</div></aside>

<section class="section">
  <div class="wrap">
    <div class="section-head section-head--split">
      <div class="stack" style="gap:14px"><span class="eyebrow">The ones people drive for</span><h2>Signature pies</h2></div>
      <a class="link-arrow" href="{{ site.menu_url }}" data-open-picker="menu">See the full menu →</a>
    </div>
    <div class="sigs">
      {% for n, d, p in sigs %}<article class="sig">
        <div class="sig-photo">{{ img(p, n ~ ' pizza from Square Peg Pizzeria', sizes='(min-width:900px) 22vw, 63vw')|safe }}<span class="sig-size">12″ · 18″</span></div>
        <div class="sig-body"><h3>{{ n }}</h3><p>{{ d }}</p><a class="btn btn--sm" href="{{ u('/locations/') }}" data-open-picker="order" aria-label="Order this: {{ n }}">Order this</a></div>
      </article>{% endfor %}
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap two-col more-than">
    <figure class="feature-photo">{{ img('table-spread', 'Meatballs, wings, Caesar salad and drinks on a Square Peg table', sizes='(min-width:960px) 540px, 100vw')|safe }}</figure>
    <div class="stack">
      <span class="eyebrow">More than pizza</span>
      <h2>Pasta, parm &amp; Italian-American favorites</h2>
      <p class="lede">Square Peg is a full Italian-American restaurant, with beer, wine and cocktails at nearly every location. Bring the whole crew for dinner, lunch or a weeknight takeout run.</p>
      <div>{% for n, d in pasta_items[:4] %}<div class="item"><h3>{{ n }}</h3><p>{{ d }}</p></div>{% endfor %}</div>
      <div class="btn-row"><a class="btn" href="{{ u('/our-menu/') }}">See what’s on the menu</a><a class="btn btn--line" href="{{ site.menu_url }}" data-open-picker="menu">Live menu &amp; prices</a></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap craft">
    <div class="craft-photo">{{ img('dough', 'A ball of fresh Square Peg pizza dough', sizes='(min-width:900px) 50vw, 100vw')|safe }}
      <div class="stamp">Never<br>frozen<small>Dough made fresh</small></div></div>
    <div class="stack">
      <span class="eyebrow">How we make it</span>
      <h2>Water. Flour. Time. Fire.</h2>
      <p class="prose" style="font-size:18px">Every dough ball is made from scratch — in our commissary kitchen for the Connecticut Pegs, and in-house at Delray Beach — then stretched by hand before it hits the wood-fired oven. We roast, simmer and season with purpose, and it’s worth it for the head-tilt, the smile and the “wow” after the first bite.</p>
      <div class="facts">
        <div class="fact"><b>12″ / 18″</b><span>Small & large pies</span></div>
        <div class="fact"><b>GF</b><span>12″ gluten-free crust</span></div>
        <div class="fact"><b>0</b><span>Frozen dough balls. Ever.</span></div>
        <div class="fact"><b>10</b><span>Square Pegs in CT & FL</span></div>
      </div>
      <div class="btn-row" style="margin-top:8px"><a class="btn" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.bag|safe }}Order now</a><a class="btn btn--line" href="{{ u('/about/') }}">Our story</a></div>
    </div>
  </div>
</section>

<section class="section section--dark on-dark" id="locations">
  <div class="wrap">
    <div class="section-head section-head--split">
      <div class="stack" style="gap:14px"><span class="eyebrow">Find your Peg</span><h2>10 locations.<br>One oven temp: hot.</h2></div>
      <button class="btn btn--flame" id="geo-grid" type="button" onclick="document.getElementById('geo-quick')&&document.getElementById('geo-quick').click()">{{ icons.pin|safe }}Sort by closest</button>
    </div>
    <div class="loc-grid loc-grid--all" id="loc-grid">
      {% for r in regions %}{% for l in locs if l.region == r %}{% include "loc_card" %}{% endfor %}{% endfor %}
      <div class="loc-card loc-cta"><span class="eyebrow">Can’t decide?</span><h3>Let us pick the closest Peg.</h3><p>Share your location and we’ll sort all ten by distance, with live open/closed status.</p><div class="btn-row"><button class="btn btn--flame" type="button" onclick="document.getElementById('geo-quick')&&document.getElementById('geo-quick').click()">{{ icons.pin|safe }}Find my closest</button><a class="btn btn--ghost" href="{{ u('/catering/') }}">Catering from any Peg</a></div></div>
    </div>
  </div>
</section>

<section class="section section--paper ent-band">
  <div class="wrap">
    <div class="section-head section-head--split"><div class="stack" style="gap:14px"><span class="eyebrow">Trivia · Bingo · DJ nights</span><h2>More than dinner. It’s a night out.</h2></div><a class="link-arrow" href="{{ u('/entertainment/') }}">Full weekly lineup →</a></div>
    <div class="tonight" data-tonight><p class="note">Loading tonight’s lineup…</p></div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Catering, big groups & the food truck</span><h2>You host. We’ll make the pizza.</h2></div>
    <div class="tiles tiles--3">
      <a class="tile on-dark" href="{{ u('/catering/') }}">{{ img('catering-table', 'A table of wood-fired pizzas on stands, ready for a party', sizes='(min-width:900px) 30vw, 95vw')|safe }}
        <div class="tile-body"><span class="eyebrow">Catering</span><h3 style="font-size:clamp(34px,4vw,48px)">Enough pizza for everyone. We promise.</h3><p>Tell us your headcount and date, and we’ll make sure there’s enough wood-fired pizza for everyone, ready when you pick it up.</p><span class="btn">Plan my catering {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/large-party-reservations/') }}">{{ img('friends-holiday', 'A group of friends celebrating over pizza', sizes='(min-width:1000px) 33vw, 100vw')|safe }}
        <div class="tile-body"><span class="eyebrow">Large parties</span><h3 style="font-size:clamp(34px,4vw,48px)">Bring the whole crew.</h3><p>Birthdays, team dinners and reunions. We’ll save the tables and plan the food so it lands together.</p><span class="btn">Reserve for a group {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/food-truck/') }}">{{ img('food-truck', 'The Square Peg Pizzeria wood-fired food truck', sizes='(min-width:900px) 30vw, 95vw')|safe }}
        <div class="tile-body"><span class="eyebrow">Food truck</span><h3 style="font-size:clamp(34px,4vw,48px)">We bring the oven to you.</h3><p>A wood-fired oven on wheels for backyard parties, schools, breweries and corporate events.</p><span class="btn">Book the truck {{ icons.arrow|safe }}</span></div></a>
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap band">
    <div class="band-media">{{ img('team-kids', 'A youth sports team celebrating their fundraiser night at Square Peg', sizes='(min-width:900px) 35vw, 95vw')|safe }}<div class="band-num"><div class="big-num" aria-hidden="true">20<sup>%</sup></div><p>of dine-in food sales, back to your cause</p></div></div>
    <div class="stack">
      <span class="eyebrow">Tuesday Night Fundraisers</span>
      <h2>Turn Tuesday into a fundraiser.</h2>
      <ol class="steps">
        <li><div><b>Pick a Tuesday</b><span>One organization per night, per location.</span></div></li>
        <li><div><b>Bring your supporters</b><span>They dine in from 4pm to close and mention your group.</span></div></li>
        <li><div><b>Earn 20% back</b><span>We total it up and donate 20% of qualifying food sales.</span></div></li>
      </ol>
      <div class="btn-row"><a class="btn" href="{{ u('/fundraisers/') }}#apply">Request a Tuesday</a><a class="btn btn--line" href="{{ u('/fundraisers/') }}">How it works</a></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">From our guests</span><h2>The head-tilt. The smile. The “wow.”</h2></div>
    <div class="reviews"><div class="review-photo">{{ img('kid-slice', 'A happy kid eating a slice of Square Peg pizza', sizes='(min-width:900px) 25vw, 100vw')|safe }}</div>{% for q, n in reviews %}<figure class="review"><blockquote>{{ q }}</blockquote><figcaption>{{ n }}</figcaption></figure>{% endfor %}</div>
  </div>
</section>

<section class="section section--dark on-dark">
  <div class="wrap app">
    <div class="app-phone-wrap">{{ img('app-phone', 'The Square Peg Pizzeria app on a phone', sizes='340px', cls='app-phone')|safe }}</div>
    <div class="app-copy">
      <span class="eyebrow">Be nice. Earn more.</span>
      <h2>Your neighborhood’s best pizza, in your pocket.</h2>
      <ul class="perks">{% for p in perks %}<li>{{ p }}</li>{% endfor %}</ul>
      <div class="btn-row"><a class="btn btn--flame" href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="home"{{ ext|safe }}>Download the app</a><a class="btn btn--ghost" href="{{ u('/deals/') }}">How points work</a></div>
    </div>
      <div class="ladder app-ladder">{% for p in points[:4] %}<div class="rung"><b>{{ p[0] }}<small>PTS</small></b><span>{{ p[1] }}</span></div>{% endfor %}</div>
  </div>
</section>
"""

# ---------- LOCATIONS INDEX
T["locations"] = """
<section class="page-head on-dark">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Locations</span></nav>
    <span class="eyebrow">Connecticut + Delray Beach, FL</span>
    <h1>Square Peg Pizzeria locations</h1>
    <p class="lede">Ten Italian-American restaurants with wood-fired ovens, all making their dough fresh from scratch. Find the closest one, check if it’s open, and order in a tap.</p>
    <div class="btn-row"><button class="btn btn--flame" type="button" id="geo-quick">{{ icons.pin|safe }}Sort by closest to me</button><a class="btn btn--ghost" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.bag|safe }}Order now</a></div>
  </div>
</section>
<section class="section section--dark on-dark" style="padding-top:32px">
  <div class="wrap">
    <h2 class="sr-only">All 10 Square Peg Pizzeria locations</h2>
    <div class="loc-grid loc-grid--all" id="loc-grid">
      {% for r in regions %}{% for l in locs if l.region == r %}{% include "loc_card" %}{% endfor %}{% endfor %}
      <div class="loc-card loc-cta"><span class="eyebrow">Can’t decide?</span><h3>Let us pick the closest Peg.</h3><p>Share your location and we’ll sort all ten by distance, with live open/closed status.</p><div class="btn-row"><button class="btn btn--flame" type="button" onclick="document.getElementById('geo-quick').click()">{{ icons.pin|safe }}Find my closest</button><a class="btn btn--ghost" href="{{ u('/areas-we-serve/') }}">Look up your town</a></div></div>
    </div>
    <p class="note" style="margin-top:20px;color:#e6ddd6">Serving {{ town_count }} towns across Connecticut, Rhode Island and South Florida. <a href="{{ u('/areas-we-serve/') }}" style="color:#fff">See every town we serve →</a></p>
  </div>
</section>
"""

# ---------- MENU OVERVIEW
T["our_menu"] = """
<section class="page-head on-dark">
  {{ img('table-spread', 'Pasta, meatballs, wings and salads at Square Peg Pizzeria', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Menu</span></nav>
    <span class="eyebrow">Italian-American kitchen · wood-fired oven</span>
    <h1>Our menu</h1>
    <p class="lede">Wood-fired pizza, pasta, chicken parm, Italian subs, salads, wings, desserts, and beer, wine and cocktails. Dough and sauce made from scratch: our commissary kitchen supplies the Connecticut Pegs, and Delray Beach makes its own in-house.</p>
    <div class="btn-row"><a class="btn btn--flame" href="{{ site.menu_url }}" data-open-picker="menu">{{ icons.bag|safe }}Live menu &amp; prices for your Peg</a><a class="btn btn--ghost" href="{{ u('/catering/') }}">Catering menu</a></div>
  </div>
</section>
<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">The pizza</span><h2>Wood-fired, three ways</h2></div>
    <div class="menu-styles">{% for n, d in menu.pizza_styles %}<div class="item"><h3>{{ n }}</h3><p>{{ d }}</p></div>{% endfor %}</div>
    <div class="menu-sigs">{% for n, d, p in sigs %}<div class="item"><h3>{{ n }}</h3><p>{{ d }}</p></div>{% endfor %}</div>
  </div>
</section>
{% for title, key, items in menu.sections %}<section class="section{% if loop.index is even %} section--paper{% endif %}" id="{{ key }}">
  <div class="wrap two-col">
    <div class="stack"><span class="eyebrow">{{ {'pasta': 'Italian classics', 'sandwiches': 'From the deli side', 'starters': 'For the table', 'salads': 'Fresh & crisp', 'kids': 'For the little ones', 'drinks': 'From the bar', 'desserts': 'Save room'}[key] }}</span><h2>{{ title }}</h2>
      {% if key == 'pasta' %}<p>Hearty Italian-American pasta dishes, finished to order. Most locations carry all six; a few carry a shorter list.</p>{% endif %}
      {% if key == 'drinks' %}<p>{{ menu.drinks_note }} Ask your server about seasonal cocktails and what’s on draft.</p>{% endif %}
      {% if key == 'kids' %}<p>Every Square Peg has a kids’ menu, plus room for big family tables. <a href="{{ u('/large-party-reservations/') }}">Reserve for a large party →</a></p>{% endif %}
    </div>
    <div>{% for n, d in items %}<div class="item"><h3>{{ n }}</h3><p>{{ d }}</p></div>{% endfor %}</div>
  </div>
</section>{% endfor %}
<section class="section section--dark on-dark">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Only at certain locations</span><h2>Location specials</h2></div>
    <div class="menu-styles">{% for l in locs if l.menu_extra %}<div class="item"><h3><a href="{{ u('/locations/' ~ l.slug ~ '/') }}">{{ l.short or l.name }}</a></h3><p>{{ l.menu_extra|join('. ') }}.</p></div>{% endfor %}</div>
    <p class="note" style="margin-top:20px;color:#e6ddd6">{{ menu.note }}</p>
    <div class="btn-row" style="margin-top:18px"><a class="btn btn--flame" href="{{ site.menu_url }}" data-open-picker="menu">{{ icons.bag|safe }}Open my Peg’s menu</a><a class="btn btn--ghost" href="{{ u('/locations/') }}">Find a location</a></div>
  </div>
</section>
"""

# ---------- TOWNS WE SERVE
T["areas"] = """
<section class="page-head on-dark">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><a href="{{ u('/locations/') }}">Locations</a><span aria-hidden="true">/</span><span>Towns we serve</span></nav>
    <span class="eyebrow">Within 15 miles of a Square Peg</span>
    <h1>Towns we serve</h1>
    <p class="lede">{{ town_count }} towns in Connecticut, Rhode Island and South Florida are a short drive from one of our 10 Italian restaurants and wood-fired pizza kitchens. Find your town to see your closest Square Peg, then order ahead for pickup or check delivery at checkout.</p>
    <div class="town-search"><label for="town-filter" class="sr-only">Find your town</label><input id="town-filter" type="search" placeholder="Type your town, e.g. Manchester" autocomplete="address-level2"><button class="btn btn--flame" type="button" id="geo-quick">{{ icons.pin|safe }}Use my location</button></div>
  </div>
</section>
<section class="section section--paper">
  <div class="wrap">
    <p class="town-geo" id="town-geo" hidden></p>
    <p class="note town-empty" id="town-empty" hidden>No match. Try a nearby town, or <a href="{{ u('/locations/') }}">see all 10 locations</a>.</p>
    {% for state, rows in towns %}<div class="town-group">
      <h2>{{ state }}</h2>
      <ul class="town-list">{% for name, st, hits in rows %}<li data-town="{{ name|lower }}">
        <b>{{ name }}</b>
        <span>Closest: <a href="{{ u('/locations/' ~ hits[0][0].slug ~ '/') }}">Square Peg {{ hits[0][0].short or hits[0][0].name }}</a> · {{ 'in town' if hits[0][1] == 0 else band(hits[0][1])|lower }}</span>
        {% if hits|length > 1 %}<span class="also">Also near: {% for h in hits[1:3] %}<a href="{{ u('/locations/' ~ h[0].slug ~ '/') }}">{{ h[0].short or h[0].name }}</a>{% if not loop.last %}, {% endif %}{% endfor %}</span>{% endif %}
      </li>{% endfor %}</ul>
    </div>{% endfor %}
    <p class="note" style="margin-top:24px">Distances are straight-line from each restaurant, grouped as under 5, 5–10 and 10–15 miles.</p>
  </div>
</section>
<section class="section">
  <div class="wrap two-col">
    <div class="stack"><span class="eyebrow">Having a party?</span><h2>Catering &amp; the food truck</h2><p>Pick up a catering order from any Square Peg, or book our wood-fired food truck for backyard parties, schools, breweries and corporate events.</p>
      <div class="btn-row"><a class="btn" href="{{ u('/catering/') }}">Catering</a><a class="btn btn--line" href="{{ u('/food-truck/') }}">Food truck</a></div></div>
    <div class="stack"><span class="eyebrow">For your school or team</span><h2>Tuesday fundraisers</h2><p>Groups from all of these towns can earn 20% of dine-in food sales with a Tuesday Night Fundraiser at their closest Square Peg.</p>
      <div class="btn-row"><a class="btn" href="{{ u('/fundraisers/') }}">Request a Tuesday</a></div></div>
  </div>
</section>
"""

# ---------- LOCATION PAGE
T["location"] = """
<section class="page-head on-dark">
  {{ img(l.photo, 'Pizza at Square Peg Pizzeria ' ~ l.city, eager=True, cls='bg')|safe }}
  <div class="wrap loc-top">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><a href="{{ u('/locations/') }}">Locations</a><span aria-hidden="true">/</span><span>{{ l.name }}</span></nav>
    <span class="eyebrow">{{ l.tag }}</span>
    <h1>Square Peg Pizzeria {{ l.name }}<span class="h1-sub">Italian restaurant &amp; {% if lm.wood %}wood-fired {% endif %}pizza in {{ l.city }}, {{ l.state }}</span></h1>
    <p class="lede">{% if lm.wood %}Wood-fired pizza{% else %}Pizza{% endif %}, {{ lm.words[0] }}, {{ lm.words[1] }}, wings and more at {{ l.street }} in {{ l.city }}, {{ l.state }}. Dine in with family and friends, or order online for pickup or delivery.</p>
    <div class="loc-badges"><span class="status" data-status="{{ l.slug }}">{{ l.summary[0] }}</span>{% if l.get('husky_bucks') %}<span class="hb-badge">Husky Bucks accepted</span>{% endif %}</div>
    <div class="loc-actions">
      <a class="btn" href="{{ order(l) }}" data-pick="{{ l.slug }}" data-track="order_click" data-src="loc-hero" rel="noopener">{{ icons.bag|safe }}Order {{ l.short or l.name }} online</a>
      <a class="btn btn--ghost" href="tel:{{ tel(l.phone) }}" data-pick="{{ l.slug }}" data-track="call_click" data-loc="{{ l.slug }}">{{ icons.phone|safe }}<span class="narrow-only">Call</span><span class="wide-only">{{ l.phone }}</span></a>
      <a class="btn btn--ghost" href="{{ maps(l) }}" rel="noopener" data-track="directions_click" data-loc="{{ l.slug }}"{{ ext|safe }}>{{ icons.pin|safe }}Directions</a>
    </div>
  </div>
</section>

{% if l.get('bar', True) %}<aside class="hh-bar" aria-label="Happy hour at Square Peg {{ l.short or l.name }}"><div class="wrap">
  <span class="hh-tag">Happy hour</span>
  {% if hh %}<p>{% for days, time in hh.hours %}<b>{{ days }}, {{ time }}</b>{% if not loop.last %} &middot; {% endif %}{% endfor %} <a href="#happy-hour">See the menu &rarr;</a></p>
  {% else %}<p><b>{{ promos.happy_hour.days }}, {{ promos.happy_hour.time }}</b> <span>at the bar in {{ l.city }}. Ask your bartender what’s running.</span></p>{% endif %}
</div></aside>{% endif %}
{% if l.sunday_ticket %}<section class="st-strip" aria-label="NFL Sunday Ticket at Square Peg {{ l.short or l.name }}" data-season-from="{{ gd.season_from }}" data-season-to="{{ gd.season_to }}" hidden>
  <div class="wrap">
    <figure class="st-strip-art">{{ img('sunday-ticket', 'NFL Sunday Ticket for Business from EverPass', sizes='180px')|safe }}</figure>
    <div class="st-strip-copy">
      <span class="eyebrow">Sundays here</span>
      <h2>NFL Sunday Ticket in {{ l.city }}</h2>
      <p>Every live out-of-market Sunday afternoon game is on our screens. Watch your team in {{ l.city }} even when the local channels aren’t carrying it — with a pie and a cold one in front of you.</p>
      <a class="link-arrow" href="{{ u('/game-day/') }}">Game day specials &amp; pizzas →</a>
    </div>
  </div>
</section>{% endif %}
{% for e in events %}<section class="section section--paper loc-event-wrap" aria-label="{{ e.title }} at Square Peg {{ l.short or l.name }}" data-season-from="{{ e.announce }}" data-season-to="{{ e.date }}" hidden>
  <div class="wrap">
    <article class="loc-event">
      <div class="loc-event-when">
        <span class="mo">{{ e.mon }}</span><b>{{ e.day }}</b><span class="dow">{{ e.weekday }}</span>
      </div>
      <div class="loc-event-body">
        <span class="eyebrow">Ticketed event · {{ l.city }}</span>
        <h2>{{ e.title }}</h2>
        <p>{{ e.blurb }}</p>
        <ul class="loc-event-meta">{% for m in e.meta %}<li>{{ m }}</li>{% endfor %}</ul>
        {% if e.host %}<p class="note">{{ e.host }}</p>{% endif %}
      </div>
      <div class="loc-event-cta">
        <a class="btn" href="{{ e.url }}" rel="noopener"{{ ext|safe }} data-track="event_ticket_click" data-src="{{ l.slug }}">{{ e.cta or 'Get tickets' }}</a>
        <span class="note">{{ e.long_date }} · Square Peg {{ l.short or l.name }}</span>
      </div>
    </article>
  </div>
</section>{% endfor %}
{% if ent.get(l.slug) or ent_dates %}<section class="ent-strip on-dark" aria-label="Entertainment at Square Peg {{ l.short or l.name }}">
  <div class="wrap">
    <div class="ent-strip-head"><span class="eyebrow">{% if ent.get(l.slug) %}Weekly entertainment{% else %}What's on{% endif %}</span><a href="{{ u('/entertainment/') }}">All locations →</a></div>
    {% if ent.get(l.slug) %}<div class="ent-cards">{% for d, e, t, fr in ent[l.slug] %}<div class="ent-card-sm" data-ent-day="{{ d }}"{% if fr %} data-ent-from="{{ fr }}"{% endif %}><span class="d">{{ day_names[d] }}</span><b>{{ e }}</b><span>{{ t }}{% if fr %} <i class="ent-soon">from {{ ent_from(fr) }}</i>{% endif %}</span></div>{% endfor %}</div>{% endif %}
    {% if ent_dates %}<div class="ent-dated" data-season-from="2000-01-01" data-season-to="{{ ent_dates[-1][0] }}" hidden>
      <span class="ent-dated-label">One night only</span>
      <div class="ent-cards">{% for iso, what, when, label in ent_dates %}<div class="ent-card-sm is-dated" data-season-from="2000-01-01" data-season-to="{{ iso }}" hidden><span class="d">{{ label }}</span><b>{{ what }}</b><span>{{ when }}</span></div>{% endfor %}</div>
    </div>{% endif %}
  </div>
</section>{% endif %}
{% if hh %}<section class="section hh" id="happy-hour" aria-label="Happy hour menu at Square Peg {{ l.short or l.name }}">
  <div class="wrap">
    {% if hh.starts %}<p class="hh-soon" data-season-to="{{ hh.starts_eve }}" hidden><b>Starts {{ hh.starts_long }}</b> &mdash; our new happy hour menu in {{ l.city }}.</p>{% endif %}
    <div class="section-head">
      <span class="eyebrow">Happy hour</span>
      <h2>{{ hh.tagline }}</h2>
    </div>

    <div class="hh-when">
      {% for days, time in hh.hours %}<div class="hh-when-row"><span>{{ days }}</span><b>{{ time }}</b></div>{% endfor %}
      <p class="hh-note">{{ hh.note }}</p>
    </div>

    {% if hh.local %}<p class="hh-local"><span>Local on tap</span> {{ hh.local|join(' &middot; ')|safe }}</p>{% endif %}

    <div class="hh-cols">
      <div class="hh-col">
        <h3 class="hh-side">Drinks</h3>
        {% for head, blurb, items in hh.drinks %}{{ hh_group(head, blurb, items)|safe }}{% endfor %}
      </div>
      <div class="hh-col">
        <h3 class="hh-side">Bites</h3>
        {% for head, blurb, items in hh.food %}{{ hh_group(head, blurb, items)|safe }}{% endfor %}
      </div>
    </div>

    <p class="hh-foot">Happy hour pricing is dine-in only at Square Peg {{ l.short or l.name }}, {{ l.street }}. Prices and selection can change &mdash; ask your bartender what&rsquo;s pouring.</p>
  </div>
</section>{% endif %}
<section class="section section--paper">
  <div class="wrap info">
    <div class="info-card">
      <h2>Hours</h2>
      <table class="hours"><caption class="sr-only">Opening hours for Square Peg Pizzeria {{ l.name }}</caption>
        <tbody>{% for d, name, v, kit in rows %}<tr data-day="{{ d }}"><th scope="row">{{ name }}</th><td>{{ v }}{% if kit %}<span class="kitchen-note">{{ kit }}</span>{% endif %}</td></tr>{% endfor %}</tbody></table>
      {% if specials %}<div class="special-hours" role="note"><h3>Holiday &amp; special hours</h3><ul>{% for iso, label, v in specials %}<li data-date="{{ iso }}"><span>{{ label }}</span><b>{{ v }}</b></li>{% endfor %}</ul></div>{% endif %}
      {% if l.get('bar', True) %}<p class="hours-flag" data-season-from="{{ gd.season_from }}" data-season-to="{{ gd.season_to }}" hidden><b>Hours extended during football games.</b> We stay open while the game is on.</p>{% endif %}
      <p class="note">{% if l.hours_note %}{{ l.hours_note }} {% endif %}{% if l.hours_source == 'google' %}Hours update daily from our Google listing, including holidays.{% else %}Holiday hours may vary.{% endif %} Online ordering shows live availability.</p>
    </div>
    <div class="map">
      <div class="map-fallback"><span class="pin" aria-hidden="true"><span></span></span><b>{{ l.street }}, {{ l.city }}, {{ l.state }}</b><a class="btn btn--sm btn--ghost" href="{{ maps(l) }}" rel="noopener"{{ ext|safe }}>Open in Google Maps</a></div>
      <iframe src="{{ embed(l) }}" title="Map of Square Peg Pizzeria {{ l.name }}, {{ l.street }}, {{ l.city }}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </div>
    <div class="info-card">
      <h2>Find us</h2>
      <address>Square Peg Pizzeria {{ l.name }}<br>{{ l.street }}<br>{{ l.city }}, {{ l.state }} {{ l.zip }}</address>
      <a class="link-arrow" href="tel:{{ tel(l.phone) }}" style="justify-self:start">{{ l.phone }}</a>

      <div class="btn-row"><a class="btn btn--sm btn--line" href="{{ maps(l) }}" rel="noopener"{{ ext|safe }}>Get directions</a><a class="btn btn--sm btn--dark" href="{{ u('/catering/') }}?location={{ l.slug }}">Catering from {{ l.short or l.name }}</a><a class="btn btn--sm btn--dark" href="{{ u('/large-party-reservations/') }}?location={{ l.slug }}">Large party here</a></div>
    </div>
  </div>
  <div class="wrap">
    <aside class="review-cta">
      <div>
        <span class="eyebrow">Been in lately?</span>
        <p><strong>Tell people how we did.</strong> <span>A minute of your time helps neighbors find {{ l.short or l.name }} — good or bad, we read every one.</span></p>
      </div>
      <a class="btn btn--sm" href="{{ review(l) }}" rel="noopener"{{ ext|safe }} data-track="review_click" data-src="{{ l.slug }}">Leave a review</a>
    </aside>
  </div>
</section>

<section class="section">
  <div class="wrap two-col">
    <div class="stack local">
      <span class="eyebrow">About this Peg</span>
      <h2>Italian food &amp; {% if lm.wood %}wood-fired {% endif %}pizza in {{ l.city }}</h2>
      <p>{{ l.blurb }}</p>
      {% if l.get('husky_bucks') %}<div class="hb-row">
        {{ img('husky-bucks', 'UConn One Card Husky Bucks accepted here', sizes='150px')|safe }}
        <p><b>We take Husky Bucks.</b> Dine in or order ahead for pickup and pay with your UConn One Card, same as cash.</p>
      </div>{% endif %}
      {% if local_page %}<p class="local-link"><a class="link-arrow" href="{{ u('/' ~ local_page.slug ~ '/') }}">{{ local_page.h1 }}</a> &mdash; what&rsquo;s here for you if that&rsquo;s where you&rsquo;re coming from.</p>{% endif %}
      <p>Every pie starts with dough made fresh from scratch and never frozen. Choose a red or white {% if lm.detroit %}Neo-Neapolitan round or a crispy-edged Detroit-style pie{% else %}signature pie{% endif %}, build your own, or go gluten-free with our 12″ crust. Vegan cheese is available on any pizza.</p>
      <p>Not in a pizza mood? The kitchen turns out Italian-American comfort food too: {{ join_and(lm.words + lm.rest) }}.{% if lm.bar %} Pair it with a cocktail, a glass of wine or a cold beer.{% endif %}{% if lm.extra %} Also here: {{ lm.extra|join('; ')|lower }}.{% endif %}</p>
      <div><p class="note" style="font-weight:700;margin-bottom:6px">Close to</p><div class="chips">{% for n in l.nearby %}<span class="chip">{{ n }}</span>{% endfor %}</div></div>
    </div>
    <div class="stack">
      <span class="eyebrow">On the menu here</span>
      <div>
        {% for n, d, p in sigs[:2] %}<div class="item"><h3>{{ n }} pizza</h3><p>{{ d }}</p></div>{% endfor %}
        {% for n, d in pasta_items if n in lm.pastas %}{% if loop.index <= 3 %}<div class="item"><h3>{{ n }}</h3><p>{{ d }}</p></div>{% endif %}{% endfor %}
        <div class="item"><h3>{{ lm.parm[:1]|upper }}{{ lm.parm[1:] }}</h3><p>House-made pork meatballs{% if 'chicken' in lm.parm %} or crispy chicken{% endif %}, marinara and mozzarella on toasted bread.</p></div>
      </div>
      <a class="link-arrow" href="{{ u('/our-menu/') }}" style="justify-self:start">Pasta, parm, salads &amp; more →</a>
      <div class="btn-row"><a class="btn" href="{{ order(l) }}" data-pick="{{ l.slug }}" data-track="order_click" data-src="loc-menu" rel="noopener">{{ icons.bag|safe }}See live menu & order</a><a class="btn btn--line" href="tel:{{ tel(l.phone) }}" data-track="call_click" data-loc="{{ l.slug }}">{{ icons.phone|safe }}Call in an order</a></div>
    </div>
  </div>
</section>

{% if l.areas %}<section class="section section--paper" id="towns" aria-labelledby="towns-h">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Towns we serve</span><h2 id="towns-h">Pizza, pasta &amp; Italian food near {{ l.nearby[:3]|join(', ') }} &amp; {{ l.areas|length - 3 }}+ more towns</h2>
      <p class="lede">Square Peg {{ l.short or l.name }} is a quick drive from these towns{% if l.state == 'CT' %} around {{ l.city }}{% endif %}. Order ahead for pickup, check delivery at checkout, or book catering and the food truck for your event.</p></div>
    <div class="area-bands">{% for label, rows in l.area_bands %}<div class="area-band"><h3>{{ label }}</h3><ul class="area-list">{% for r in rows %}<li>{{ r.name }}{% if r.state != l.state %}, {{ r.state }}{% endif %}</li>{% endfor %}</ul></div>{% endfor %}</div>
    <p class="note" style="margin-top:18px">Straight-line distance from {{ l.street }}, {{ l.city }}. <a href="{{ u('/areas-we-serve/') }}">Find the closest Square Peg to any town →</a></p>
  </div>
</section>{% endif %}

<section class="section">
  <div class="wrap">
    <div class="tiles">
      <a class="tile on-dark" href="{{ u('/fundraisers/') }}" style="min-height:360px">{{ img('team-kids', 'A youth team at a Square Peg Tuesday fundraiser', sizes='(min-width:900px) 50vw, 100vw')|safe }}
        <div class="tile-body"><span class="eyebrow">Tuesday fundraisers</span><h3 style="font-size:40px">20% back to your cause</h3><p>Book a Tuesday night at {{ l.short or l.name }} for your school, team or nonprofit.</p><span class="btn">Request a Tuesday {{ icons.arrow|safe }}</span></div></a>
      {% for d in deals %}<a class="tile on-dark" href="{{ u('/deals/') }}" style="min-height:360px" data-season-from="{{ d.starts }}" data-season-to="{{ d.expires }}" hidden>{{ img('pizza-boxes', 'Stacked Square Peg pizza boxes', sizes='(min-width:900px) 50vw, 100vw')|safe }}
        <div class="tile-body"><span class="eyebrow">{{ d.eyebrow }}</span><h3 style="font-size:40px">{{ d.headline }}</h3><p>Join free in the Square Peg app and start earning points on every visit.</p><span class="btn">See deals {{ icons.arrow|safe }}</span></div></a>{% endfor %}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Good to know</span><h2>{{ l.name }} FAQ</h2></div>
    <div class="faq">{% for q, a in faqs %}<details><summary>{{ q }}</summary><p>{{ a }}</p></details>{% endfor %}</div>
  </div>
</section>

<section class="section section--dark on-dark">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Also nearby</span><h2>Other Square Pegs close to {{ l.city }}</h2></div>
    <div class="loc-grid">{% for l in near %}{% include "loc_card" %}{% endfor %}</div>
  </div>
</section>
"""

# ---------- CATERING
T["form_catering"] = """{% set fname = form_name|default('catering') %}<form class="form" name="{{ fname }}" method="POST" action="{{ u('/thanks/') }}" data-netlify="true" netlify-honeypot="company_website" id="{{ fid }}-form">
  <input type="hidden" name="form-name" value="{{ fname }}">
  <p class="sr-only"><label>Leave blank <input name="company_website"></label></p>
  <h2>{{ form_title }}</h2>
  <div class="field-row field-row--pair">
    <div class="field"><label for="{{ fid }}-first">First name</label><input id="{{ fid }}-first" name="first_name" autocomplete="given-name" required></div>
    <div class="field"><label for="{{ fid }}-last">Last name</label><input id="{{ fid }}-last" name="last_name" autocomplete="family-name" required></div>
  </div>
  <div class="field-row">
    <div class="field"><label for="{{ fid }}-email">Email</label><input id="{{ fid }}-email" type="email" name="email" autocomplete="email" required></div>
    <div class="field"><label for="{{ fid }}-phone">Phone</label><input id="{{ fid }}-phone" type="tel" name="phone" autocomplete="tel" required></div>
  </div>
  <div class="field-row">
    <div class="field"><label for="{{ fid }}-type">Event type</label><select id="{{ fid }}-type" name="event_type">{% for o in event_types %}<option{% if o == default_type %} selected{% endif %}>{{ o }}</option>{% endfor %}</select></div>
    <div class="field"><label for="{{ fid }}-loc">Closest location</label><select id="{{ fid }}-loc" name="location" required><option value="">Choose…</option>{% for l in locs %}<option value="{{ l.name }}">{{ l.name }}</option>{% endfor %}</select></div>
  </div>
  <div class="field-row">
    <div class="field"><label for="{{ fid }}-date">Date & time</label><input id="{{ fid }}-date" type="datetime-local" name="event_datetime" required></div>
    <div class="field"><label for="{{ fid }}-count">Number of guests</label><input id="{{ fid }}-count" type="number" min="1" name="guests" inputmode="numeric" required></div>
  </div>
  <div class="field"><label for="{{ fid }}-notes">Anything else?</label><textarea id="{{ fid }}-notes" name="notes" placeholder="Venue, dietary needs (gluten-free, vegan), budget…"></textarea></div>
  <button class="btn btn--block" type="submit" data-track="lead_submit" data-src="{{ fid }}">{{ submit }}</button>
  <small>We reply within one business day. Prefer to talk? Call the location closest to your event.</small>
</form>"""

T["booking_form"] = """{% set e = embeds.get(embed_key) %}{% if e %}<div class="form-embed" id="{{ fid }}-booking" style="--h-m:{{ e.mobile }}px;--h-d:{{ e.desktop }}px;--crop:{{ e.crop }}px">
  {% if pick %}<p class="embed-pick">Under <b>&ldquo;Where would you prefer your order?&rdquo;</b> choose <b>{{ pick }}</b>.</p>{% endif %}
  <div class="embed-frame"><iframe src="{{ e.src }}?embed=1" title="{{ e.title }}" loading="lazy" allow="clipboard-write"></iframe></div>
  <p class="embed-help">Trouble with the form? <a href="{{ e.src }}" rel="noopener" target="_blank">Open it in a new tab</a>, or call <a href="{{ u('/locations/') }}">any location</a>.</p>
</div>{% else %}{% include "form_catering" %}{% endif %}"""

T["catering"] = """{% macro bento(items) %}<div class="bento">{% for p, a, cap in items %}<figure class="{{ 'b-main' if loop.first else 'b-side' }}">{{ img(p, a, sizes=('(min-width:800px) 60vw, 100vw' if loop.first else '(min-width:800px) 36vw, 50vw'))|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endfor %}</div>{% endmacro %}
{% macro feature(p, a, cap) %}<figure class="feature-photo">{{ img(p, a, sizes='(min-width:960px) 540px, 100vw')|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endmacro %}

<section class="page-head on-dark">
  {{ img('table-spread', 'A Square Peg catering spread', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Catering</span></nav>
    <span class="eyebrow">Catering at all 10 locations</span>
    <h1>Pizza catering & events</h1>
    <p class="lede">Birthdays, office lunches, team banquets, graduations, holiday parties. Tell us roughly how many people and we’ll plan the order with you.</p>
    <div class="btn-row"><a class="btn" href="#quote">Get a catering quote</a><a class="btn btn--ghost" href="{{ u('/locations/') }}" data-open-picker="call">{{ icons.phone|safe }}Call a location</a></div>
  </div>
</section>
<section class="section section--paper" id="quote">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">Be at your own party</span>
      <h2>One less thing to worry about.</h2>
      <p class="prose">Hosting is enough work already. Order wood-fired pizza, wings, salads and desserts from us, pick it up hot from your closest Square Peg, and spend the party with your guests instead of in the kitchen.</p>
      <ul class="checks">
        <li>Trays of pasta, wings, salads, sandwiches &amp; dessert &mdash; plus wood-fired pizza</li>
        <li>Ready for pickup at your closest Square Peg</li>
        <li>No minimum order and no headcount we can&rsquo;t take on</li>
        <li>Gluten-free crust &amp; vegan cheese on request</li>
        <li>Available from every Square Peg location</li>
      </ul>
      {{ feature('friends-sharing', 'Friends sharing a Square Peg pizza', 'Wood-fired pies, sized for a crowd') }}
    </div>
    {% with form_title='Get a catering quote', fid='cat', embed_key='catering', submit='Send my request', default_type='Catering pickup', pick='Pick-up catering' %}{% include "booking_form" %}{% endwith %}
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Three steps</span>
      <h2>How catering works</h2>
      <p>No portal, no account, no guessing. A person calls you back.</p>
    </div>
    <ol class="steps steps--row">
      {% for head, body in cat.steps %}<li><div><b>{{ head }}</b><span>{{ body }}</span></div></li>{% endfor %}
    </ol>
    <p class="cat-note"><b>Give us {{ cat.lead_time }} where you can.</b> It isn&rsquo;t a rule &mdash;
      if your date is sooner than that, call and we&rsquo;ll tell you honestly whether we can do it
      justice. We&rsquo;d rather say no than hand you a rushed order.</p>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">The question everyone asks</span>
      <h2>How much food do I need?</h2>
      <p>Catering comes in trays. A <b>half tray feeds {{ cat.tray_half }}</b> and a
        <b>full tray feeds {{ cat.tray_full }}</b> &mdash; so the maths is mostly a
        question of how many dishes you want on the table, not how many trays.</p>
    </div>
    <div class="cat-table-wrap">
      <table class="cat-table">
        <thead><tr><th scope="col">Guests</th><th scope="col">Order</th><th scope="col">In practice</th></tr></thead>
        <tbody>{% for n, size, extra in cat.feeds %}<tr><th scope="row">{{ n }}</th><td><b>{{ size }}</b></td><td>{{ extra }}</td></tr>{% endfor %}</tbody>
      </table>
    </div>
    <p class="cat-note"><b>Adding pizza?</b> One 18&Prime; round feeds about three and a half
      adults, so fifty people is around fourteen pies. Make it one for every two and a
      half if it&rsquo;s teenagers or a game-day crowd.
      <a class="link-arrow" href="{{ u('/pizza-calculator/') }}">Run your own numbers</a></p>
  </div>
</section>

<section class="section">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">What it costs</span>
      <h2>About {{ cat.per_head }} a head.</h2>
      <p class="prose">{{ cat.per_head_note }} You&rsquo;ll get a real number before you commit
        to anything &mdash; our catering manager sends an estimate once they&rsquo;ve been
        through the menu with you.</p>
      <p class="prose">There&rsquo;s no minimum order and no headcount we won&rsquo;t take on with
        enough notice. Ten people in an office or a hundred at a graduation party,
        it&rsquo;s the same conversation.</p>
    </div>
    <div class="stack">
      <span class="eyebrow">What you can order</span>
      <h2>Beyond the pizza.</h2>
      <ul class="def-list">
        {% for name, note in cat.menu %}<li><b>{{ name }}</b><span>{{ note }}</span></li>{% endfor %}
      </ul>
      <p class="note"><b>Wing flavours:</b> {{ cat.wing_flavors }}.<br>
        Gluten-free 12&Prime; crust and vegan cheese on request &mdash; say so in the notes
        and we&rsquo;ll plan for it.</p>
    </div>
  </div>
</section>

<section class="section section--dark">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">Worth saying plainly</span>
      <h2>We don&rsquo;t deliver.</h2>
      <p class="prose">Every catering order is pickup, from whichever Square Peg you choose.
        No van, no chafing dishes, no setup crew &mdash; we&rsquo;d rather tell you that now than
        promise it and let you down on the day.</p>
      <p class="prose">What you get instead is the thing a host is actually anxious about:
        it&rsquo;s made fresh, it&rsquo;s boxed, and it&rsquo;s waiting at the time we agreed. Pull up,
        load up, go.</p>
    </div>
    <div class="stack">
      <span class="eyebrow">Unless you want the truck</span>
      <h2>The one that comes to you.</h2>
      <p class="prose">{{ cat.truck }} It runs a real wood-fired oven, so guests get pizza
        out of the fire rather than out of a box &mdash; parties, schools, corporate days
        and fundraisers.</p>
      <div class="btn-row"><a class="btn btn--line" href="{{ u('/food-truck/') }}">See the food truck</a></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Planning questions</span><h2>Catering FAQ</h2></div>
    <div class="faq">{% for q, a in faqs %}<details><summary>{{ q }}</summary><p>{{ a }}</p></details>{% endfor %}</div>
  </div>
</section>
"""

T["parties"] = """{% macro bento(items) %}<div class="bento">{% for p, a, cap in items %}<figure class="{{ 'b-main' if loop.first else 'b-side' }}">{{ img(p, a, sizes=('(min-width:800px) 60vw, 100vw' if loop.first else '(min-width:800px) 36vw, 50vw'))|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endfor %}</div>{% endmacro %}
{% macro feature(p, a, cap) %}<figure class="feature-photo">{{ img(p, a, sizes='(min-width:960px) 540px, 100vw')|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endmacro %}

<section class="page-head on-dark">
  {{ img('friends-holiday', 'A group celebrating together over pizza', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Large Parties</span></nav>
    <span class="eyebrow">Group reservations at all 10 locations</span>
    <h1>Large party reservations</h1>
    <p class="lede">Birthdays, team dinners, showers, reunions and office nights out. Tell us how many are coming and we’ll save the tables and plan the food so it lands hot and together.</p>
    <div class="btn-row"><a class="btn" href="#reserve">Request a reservation</a><a class="btn btn--ghost" href="{{ u('/locations/') }}" data-open-picker="call">{{ icons.phone|safe }}Call a location</a></div>
  </div>
</section>
<section class="section section--paper" id="reserve">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">Bring the whole crew</span>
      <h2>Your group. Our tables.</h2>
      <p class="prose">Getting a big group to one place is the hard part. We’ll handle the rest: the tables, the timing and enough wood-fired pizza for everyone.</p>
      <ul class="checks">
        <li>Tables saved together for your group</li>
        <li>Food planned ahead so it hits the table together</li>
        <li>Birthdays, team dinners, showers, reunions, rehearsal dinners, office parties</li>
        <li>Available at every Square Peg (space varies by location)</li>
        <li>Gluten-free crust & vegan cheese on request</li>
      </ul>
      {{ feature('dining-room-kids', 'Families and friends dining together at Square Peg', 'Your tables, saved and ready') }}
      <ol class="steps">
        <li><div><b>Send your request</b><span>Date, time, location and headcount.</span></div></li>
        <li><div><b>We confirm the details</b><span>We’ll check space at your location and plan the food with you.</span></div></li>
        <li><div><b>Show up and celebrate</b><span>Your tables are ready when you walk in.</span></div></li>
      </ol>
    </div>
    {% with form_title='Request a large party reservation', fid='party', embed_key='large_party', form_name='large_party', submit='Send my request', default_type='Party at the restaurant' %}{% include "booking_form" %}{% endwith %}
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">The simple rule</span>
      <h2>Ten or more? Send the form.</h2>
      <p>Below ten you can usually just walk in and we&rsquo;ll sort you out. At ten and
        above, tables have to be moved and the kitchen wants a heads-up &mdash; so a
        request beats turning up and hoping, especially on a Friday or Saturday.</p>
    </div>
    <div class="route-grid">
      {% for when, name, blurb, href in routes %}
      <a class="route" href="{{ u(href) }}">
        <span class="eyebrow">{{ when }}</span>
        <b>{{ name }}</b>
        <span class="route-blurb">{{ blurb }}</span>
      </a>{% endfor %}
    </div>
  </div>
</section>
<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Planning questions</span><h2>Large party FAQ</h2></div>
    <div class="faq">{% for q, a in faqs %}<details><summary>{{ q }}</summary><p>{{ a }}</p></details>{% endfor %}</div>
  </div>
</section>
"""

T["contact"] = """
<section class="page-head on-dark">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Contact</span></nav>
    <span class="eyebrow">We’re here to help</span>
    <h1>Contact Square Peg Pizzeria</h1>
    <p class="lede">The fastest way to reach us is to call your location. For everything else, send a note below and the right person will get back to you.</p>
    <div class="btn-row"><a class="btn" href="{{ u('/locations/') }}" data-open-picker="call">{{ icons.phone|safe }}Call a location</a><a class="btn btn--ghost" href="mailto:{{ site.email }}">Email {{ site.email }}</a></div>
  </div>
</section>
<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Looking for something specific?</span><h2>Get to the right place</h2></div>
    <div class="quicklinks">
      <a href="{{ u('/locations/') }}" data-open-picker="order"><b>Place an order</b><span>Pickup or delivery from any location</span></a>
      <a href="{{ u('/catering/') }}"><b>Catering</b><span>Quotes for any size event</span></a>
      <a href="{{ u('/large-party-reservations/') }}"><b>Large parties</b><span>Reserve for a big group</span></a>
      <a href="{{ u('/food-truck/') }}"><b>Food truck</b><span>Book the wood-fired truck</span></a>
      <a href="{{ u('/fundraisers/') }}"><b>Fundraisers</b><span>Tuesday nights, 20% back</span></a>
      <a href="{{ u('/deals/') }}"><b>Rewards & app</b><span>Points, deals and sign-in</span></a>
      <a href="{{ site.gift_cards_url }}" rel="noopener"{{ ext|safe }}><b>Gift cards</b><span>Buy or check a balance</span></a>
      <a href="{{ u('/careers/') }}"><b>Jobs</b><span>Apply at any location</span></a>
    </div>
  </div>
</section>
<section class="section" id="message">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">Call your Square Peg</span>
      <h2>Locations & phone numbers</h2>
      <div class="contact-list">{% for l in locs %}<div class="contact-row"><div><a href="{{ u('/locations/' ~ l.slug ~ '/') }}"><b>{{ l.name }}</b></a><span>{{ l.street }}, {{ l.city }}, {{ l.state }} {{ l.zip }}</span></div><div class="contact-meta"><span class="status" data-status="{{ l.slug }}">{{ l.summary[0] }}</span><a class="btn btn--sm btn--line" href="tel:{{ tel(l.phone) }}" data-track="call_click" data-loc="{{ l.slug }}">{{ l.phone }}</a></div></div>{% endfor %}</div>
    </div>
    <form class="form" name="contact" method="POST" action="{{ u('/thanks/') }}" data-supabase="contact_messages" netlify-honeypot="company_website">
      <input type="hidden" name="form-name" value="contact">
      <div class="hp" aria-hidden="true"><label>Leave this field empty<input name="company_website" type="text" tabindex="-1" autocomplete="off"></label></div>
      <input type="hidden" name="form_loaded" value="">
      <h2>Send us a message</h2>
      <div class="field-row field-row--pair">
        <div class="field"><label for="ct-first">First name</label><input id="ct-first" name="first_name" autocomplete="given-name" maxlength="80" required></div>
        <div class="field"><label for="ct-last">Last name</label><input id="ct-last" name="last_name" autocomplete="family-name" maxlength="80"></div>
      </div>
      <div class="field-row">
        <div class="field"><label for="ct-email">Email</label><input id="ct-email" type="email" name="email" autocomplete="email" required></div>
        <div class="field"><label for="ct-phone">Phone</label><input id="ct-phone" type="tel" name="phone" autocomplete="tel"></div>
      </div>
      <div class="field-row">
        <div class="field"><label for="ct-topic">Topic</label><select id="ct-topic" name="event_type">{% for t in contact_topics %}<option>{{ t }}</option>{% endfor %}</select></div>
        <div class="field"><label for="ct-loc">Location</label><select id="ct-loc" name="location"><option value="">Not location-specific</option>{% for l in locs %}<option value="{{ l.name }}">{{ l.name }}</option>{% endfor %}</select></div>
      </div>
      <div class="field"><label for="ct-notes">Message</label><textarea id="ct-notes" name="notes" maxlength="3000" required></textarea></div>
      {% if site.turnstile_site_key and not preview %}<div class="cf-turnstile" data-sitekey="{{ site.turnstile_site_key }}" data-theme="light" data-size="flexible"></div>
      <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>{% endif %}
      <button class="btn btn--block" type="submit" data-track="lead_submit" data-src="contact">Send message</button>
      <small>We reply within one business day. Need something right now? Call your location.</small>
    </form>
  </div>
</section>
"""

T["truck"] = """{% macro bento(items) %}<div class="bento">{% for p, a, cap in items %}<figure class="{{ 'b-main' if loop.first else 'b-side' }}">{{ img(p, a, sizes=('(min-width:800px) 60vw, 100vw' if loop.first else '(min-width:800px) 36vw, 50vw'))|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endfor %}</div>{% endmacro %}
{% macro feature(p, a, cap) %}<figure class="feature-photo">{{ img(p, a, sizes='(min-width:960px) 540px, 100vw')|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endmacro %}

<section class="page-head on-dark">
  {{ img('food-truck', 'The Square Peg Pizzeria food truck', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Food Truck</span></nav>
    <span class="eyebrow">Let us bring the party to you</span>
    <h1>Wood-fired pizza food truck</h1>
    <p class="lede">A real wood-fired oven on wheels, cooking fresh pies on site for backyard parties, weddings, schools, breweries, festivals and corporate events across Connecticut.</p>
    <div class="btn-row"><a class="btn" href="#book">Check truck availability</a><a class="btn btn--ghost" href="{{ u('/catering/') }}">Prefer pick-up catering?</a></div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    {{ bento([('truck-tent', 'The Square Peg food truck and tent set up at an event', 'Set up in your driveway, lot or lawn'), ('truck-menu', 'The food truck menu board at a private party', 'Custom menu boards'), ('kid-slice', 'A young guest enjoying a slice', 'Fresh from the oven, on site')]) }}
  </div>
</section>
<section class="section section--paper" id="book">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">How booking works</span>
      <h2>Tell us the when & where.</h2>
      <ol class="steps">
        {% for head, body in truck.steps %}<li><div><b>{{ head }}</b><span>{{ body }}</span></div></li>{% endfor %}
      </ol>
      <p class="note">Truck dates fill fast from {{ truck.season }}. Book early.</p>
      <p class="cat-note">We don&rsquo;t publish a travel radius or a minimum, because both
        depend on the date and the job. Tell us where you are and when, and we&rsquo;ll give
        you a straight answer rather than a policy.</p>
    </div>
    {% with form_title='Book the food truck', fid='truck', embed_key='food_truck', submit='Check availability', default_type='Food truck', pick='Food truck private service' %}{% include "booking_form" %}{% endwith %}
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Truck or trays?</span>
      <h2>Which one do you actually want?</h2>
      <p>Most people come to us knowing they need food for a crowd and not much
        else. Both of these are good answers &mdash; they&rsquo;re just good at different things.</p>
    </div>
    <div class="cat-table-wrap">
      <table class="cat-table">
        <thead><tr><th scope="col"></th><th scope="col">Pick-up catering</th><th scope="col">The food truck</th></tr></thead>
        <tbody>{% for label, a, b in truck.vs %}<tr><th scope="row">{{ label }}</th><td>{{ a }}</td><td>{{ b }}</td></tr>{% endfor %}</tbody>
      </table>
    </div>
    <div class="btn-row"><a class="btn btn--line" href="{{ u('/catering/') }}">See pickup catering</a></div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">Where it goes</span>
      <h2>What the truck turns up to.</h2>
      <ul class="checks">{% for e in truck.events %}<li>{{ e }}</li>{% endfor %}</ul>
      <p class="prose">It&rsquo;s a genuine wood-fired oven, not a warming cabinet with a
        wrap on it. That means the pizza comes out of the fire about ninety seconds
        after it goes in, and your guests watch it happen &mdash; which for a lot of
        events is half the reason to book it.</p>
    </div>
    <div class="stack">
      <span class="eyebrow">Worth knowing</span>
      <h2>Before you book.</h2>
      <ul class="def-list">
        <li><b>The menu is yours</b><span>Nothing fixed. We build it around your crowd,
          your timing and your budget when we talk.</span></li>
        <li><b>Summer books out</b><span>{{ truck.season }} is the busy stretch, and
          Saturdays go first. If you have a date, send it early.</span></li>
        <li><b>We need somewhere to park</b><span>Driveway, lot or lawn. We&rsquo;ll go
          through space and access with you before the day.</span></li>
        <li><b>One form for everything</b><span>The truck shares the catering form.
          Choose <i>Food truck private service</i> and we&rsquo;ll know.</span></li>
      </ul>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Before you ask</span><h2>Food truck FAQ</h2></div>
    <div class="faq">{% for q, a in faqs %}<details><summary>{{ q }}</summary><p>{{ a }}</p></details>{% endfor %}</div>
  </div>
</section>
"""

T["deals"] = """
<section class="page-head on-dark">
  {{ img('pizza-boxes', 'Square Peg pizza boxes', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Deals & Rewards</span></nav>
    <span class="eyebrow">This month</span>
    <h1>Pizza deals & rewards</h1>
    <p class="lede">Monthly promos for members, points on every visit, and rewards you redeem right in the Square Peg app. Joining is free.</p>
    <div class="btn-row"><a class="btn btn--flame" href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="deals-head"{{ ext|safe }}>Join free in the app</a><a class="btn btn--ghost" href="{{ site.loyalty_signin }}" rel="noopener"{{ ext|safe }}>Member sign-in</a></div>
  </div>
</section>
<section class="section">
  <div class="wrap two-col">
    <div>{% for d in deals %}
      <div class="form" style="gap:14px" data-season-from="{{ d.starts }}" data-season-to="{{ d.expires }}" hidden>
        <span class="eyebrow">{{ d.eyebrow }}</span>
        <h2 style="font-size:clamp(48px,7vw,80px)">{{ d.headline }}</h2>
        <p style="font-weight:700">{{ d.expires_label }}, 2026</p>
        <p class="note">{{ d.detail }}</p>
        <div class="btn-row"><a class="btn" href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="deal-card"{{ ext|safe }}>Get the app to unlock</a></div>
      </div>{% endfor %}
    </div>
    <div class="stack">
      <span class="eyebrow">Not a member yet?</span>
      <h2>Be nice. Earn more.</h2>
      <ul class="perks">{% for p in perks %}<li>{{ p }}</li>{% endfor %}</ul>
      <p class="prose">Download the Square Peg app, create your free account, and you’re in. Points add up on every visit, and members get first dibs on flash promos.</p>
    </div>
  </div>
</section>
<section class="section section--dark on-dark">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Points shop</span><h2>What your points get you</h2><p>Redeem in the app.</p></div>
    <div class="ladder">{% for p in points %}<div class="rung"><b>{{ p[0] }}<small>PTS</small></b><span>{{ p[1] }}</span>{% if p|length > 2 %}<em>{{ p[2] }}</em>{% endif %}</div>{% endfor %}</div>
    <div class="btn-row" style="margin-top:28px"><a class="btn btn--flame" href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="points"{{ ext|safe }}>Start earning</a><a class="btn btn--ghost" href="{{ u('/locations/') }}" data-open-picker="order">Order now</a></div>
  </div>
</section>
"""

T["fundraisers"] = """
<section class="page-head on-dark">
  {{ img('dining-room-kids', 'Families dining in at Square Peg', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Fundraisers</span></nav>
    <span class="eyebrow">Every Tuesday · 4pm to close</span>
    <h1>Tuesday Night Fundraisers</h1>
    <p class="lede">Partner with Square Peg and receive 20% of dine-in food sales from your supporters. Schools, teams, booster clubs, nonprofits: you promote, they dine in, we handle the rest.</p>
    <div class="btn-row"><a class="btn" href="#apply">Request a Tuesday</a></div>
  </div>
</section>
<section class="section section--paper">
  <div class="wrap band">
    <div><div class="big-num" aria-hidden="true">20<sup>%</sup></div><p class="note">of qualifying dine-in food sales, excluding tax & alcohol</p></div>
    <div class="stack">
      <h2>How it works</h2>
      <ol class="steps">
        <li><div><b>Pick a Tuesday</b><span>We partner with one local organization per Tuesday at each location.</span></div></li>
        <li><div><b>Bring your supporters</b><span>They dine in between 4pm and close and tell their server who they’re supporting.</span></div></li>
        <li><div><b>Earn 20% back</b><span>We total qualifying dine-in food sales and donate 20% to your organization.</span></div></li>
      </ol>
      <p style="font-weight:800">Included: a custom digital flyer, social-ready graphics, server tracking & reporting, and a donation issued after the event.</p>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap two-col" style="align-items:center">
    <div class="stack">
      <span class="eyebrow">Once your date is booked</span>
      <h2>Send your people here.</h2>
      <p class="prose">This page is for you &mdash; the people you&rsquo;re inviting need
        something different. We&rsquo;ve written them their own: what to do on the night,
        what counts and what doesn&rsquo;t, and how to find the right Square Peg.</p>
      <p class="prose">Put the link in your newsletter, on your website or in the
        class group. Half the money a night leaves on the table is somebody ordering
        takeout by mistake.</p>
      <div class="btn-row"><a class="btn" href="{{ u('/fundraiser-night/') }}">See the page for supporters</a></div>
    </div>
    <div class="stack">
      <div class="cat-note" style="padding:20px;background:var(--paper);border-left:3px solid var(--ember)">
        <b>Ready to paste:</b><br>
        Join us at Square Peg in [town] on [date]. Eat dinner, bring friends, and 20%
        of what everyone spends on food comes back to us. Dine in only &mdash; just tell
        your server you&rsquo;re with [group].<br>
        What to know: {{ site.domain|replace('https://','') }}/fundraiser-night/
      </div>
    </div>
  </div>
</section>
<section class="section" id="apply">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">Limited: one group per night</span>
      <h2>Request your Tuesday</h2>
      <p class="prose">Tuesdays book quickly. If your preferred date is taken, we’ll put you on our priority waiting list for the next opening.</p>
      <div class="faq" style="margin-top:12px">{% for q, a in faqs %}<details><summary>{{ q }}</summary><p>{{ a }}</p></details>{% endfor %}</div>
    </div>
    {% if embeds.fundraiser %}{% with e = embeds.fundraiser, fid = 'fundraiser' %}<div class="form-embed" id="fundraiser-booking" style="--h-m:{{ e.mobile }}px;--h-d:{{ e.desktop }}px;--crop:{{ e.crop }}px">
      <div class="embed-frame"><iframe src="{{ e.src }}?embed=1" title="{{ e.title }}" loading="lazy" allow="clipboard-write"></iframe></div>
      <p class="embed-help">Trouble with the form? <a href="{{ e.src }}" rel="noopener" target="_blank">Open it in a new tab</a>.</p>
    </div>{% endwith %}{% else %}
    <form class="form" name="fundraiser" method="POST" action="{{ u('/thanks/') }}" data-netlify="true" netlify-honeypot="company_website">
      <input type="hidden" name="form-name" value="fundraiser">
      <p class="sr-only"><label>Leave blank <input name="company_website"></label></p>
      <h2>Fundraiser request</h2>
      <div class="field"><label for="fr-org">Organization name</label><input id="fr-org" name="organization" required></div>
      <div class="field-row">
        <div class="field"><label for="fr-name">Your name</label><input id="fr-name" name="contact_name" autocomplete="name" required></div>
        <div class="field"><label for="fr-phone">Phone</label><input id="fr-phone" type="tel" name="phone" autocomplete="tel" required></div>
      </div>
      <div class="field"><label for="fr-email">Email</label><input id="fr-email" type="email" name="email" autocomplete="email" required></div>
      <div class="field-row">
        <div class="field"><label for="fr-loc">Location</label><select id="fr-loc" name="location" required><option value="">Choose…</option>{% for l in locs %}<option>{{ l.name }}</option>{% endfor %}</select></div>
        <div class="field"><label for="fr-date">Preferred Tuesday</label><input id="fr-date" type="date" name="preferred_date" required></div>
      </div>
      <div class="field"><label for="fr-notes">Tell us about your cause</label><textarea id="fr-notes" name="notes"></textarea></div>
      <button class="btn btn--block" type="submit" data-track="lead_submit" data-src="fundraiser">Request my Tuesday</button>
    </form>{% endif %}
  </div>
</section>
"""

T["about"] = """{% macro bento(items) %}<div class="bento">{% for p, a, cap in items %}<figure class="{{ 'b-main' if loop.first else 'b-side' }}">{{ img(p, a, sizes=('(min-width:800px) 60vw, 100vw' if loop.first else '(min-width:800px) 36vw, 50vw'))|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endfor %}</div>{% endmacro %}
{% macro feature(p, a, cap) %}<figure class="feature-photo">{{ img(p, a, sizes='(min-width:960px) 540px, 100vw')|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endmacro %}

<section class="page-head on-dark">
  {{ img('dough', 'Square Peg dough being made from scratch', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Our Story</span></nav>
    <span class="eyebrow">Tradition-fueled · Community-driven · Fire-finished</span>
    <h1>The Square Peg Pizzeria story</h1>
    <p class="lede">Great restaurants aren’t built on flour and fire alone. They’re built on people, and on the reactions they feel the moment they walk through the door.</p>
  </div>
</section>
<section class="section">
  <div class="wrap two-col">
    <div class="prose">
      <p>Square Peg Pizzeria was started by UConn alumni who grew up in Hartford and came home to build the kind of place they’d want to hang out in. The first oven was lit in Glastonbury in 2020. Today there are ten Square Pegs, from Storrs Center to Shelton to Delray Beach, Florida.</p>
      <p class="pull">That moment is the product. The pizza is how we get there.</p>
      <p>Our team makes dough fresh from scratch: in our commissary kitchen for the Connecticut Pegs, and in-house at Delray Beach. It’s never frozen. It isn’t the easy way to do it, but it’s the way that gets the head-tilt, the smile and the “wow.”</p>
      <p>We roast, stretch, simmer, press and season with purpose, turning simple ingredients into something that feels familiar and still special. Water. Flour. Time. Heat. Hands that care.</p>
      <p>So this page isn’t really about us. It’s about the families, friends, neighbors and regulars who turn a pizza night into a shared memory: victory slices after long games, first dates, Tuesday fundraisers, and the table that keeps getting bigger.</p>
      <p style="font-weight:800">Whether you’re here for a quick bite, a family tradition, or the start of something new: your table is ready.</p>
      <div class="btn-row" style="margin-top:24px"><a class="btn" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.bag|safe }}Order now</a><a class="btn btn--line" href="{{ u('/careers/') }}">Join the crew</a></div>
    </div>
    <div>{{ bento([('margherita-board', 'A wood-fired margherita on a board', ''), ('team-kids', 'A local youth team celebrating at Square Peg', ''), ('table-spread', 'A table full of Square Peg favorites', '')]) }}</div>
  </div>
</section>
"""

T["dice"] = """
<section class="page-head on-dark">
  {{ img('table-spread', 'Appetizers on the table at Square Peg', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Roll the Dice</span></nav>
    <span class="eyebrow">{{ dice.when }}</span>
    <h1>{{ dice.headline }}</h1>
    <p class="lede">Order any full-price appetizer at lunch, roll two dice at your table, and match them for free pizza. No app, no code, nothing to sign up for.</p>
    <div class="btn-row"><a class="btn" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find your Square Peg</a><a class="btn btn--ghost" href="#rules">The rules</a></div>
  </div>
</section>
<section class="section section--paper">
  <div class="wrap band">
    <div class="dice" aria-hidden="true"><span class="die"><i></i><i></i><i></i><i></i><i></i><i></i></span><span class="die"><i></i><i></i><i></i><i></i><i></i><i></i></span></div>
    <div class="stack">
      <h2>Two dice. Three outcomes.</h2>
      <ol class="steps">{% for a, b in dice.how %}<li><div><b>{{ a }}</b><span>{{ b }}</span></div></li>{% endfor %}</ol>
      <p style="font-weight:800">{{ dice.odds }} Better than most afternoons.</p>
    </div>
  </div>
</section>
<section class="section" id="rules">
  <div class="wrap prose"><h2 style="margin-bottom:18px">The rules, in plain English</h2><p>{{ dice.terms }}</p></div>
</section>
"""

T["sms"] = """
<section class="page-head on-dark"><div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>SMS Terms</span></nav>
  <span class="eyebrow">Text messages</span><h1>SMS terms</h1>
  <p class="lede">How the Square Peg Pizzeria text message program works.</p></div></section>
<section class="section"><div class="wrap prose">
  {% for h, t in sms %}<h2 style="font-size:28px;margin:28px 0 8px">{{ h }}</h2><p>{{ t }}</p>{% endfor %}
</div></section>
"""

T["promotions"] = """
<section class="page-head on-dark">
  {{ img('oven-pizza', 'A pizza baking in the wood-fired oven', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Specials</span></nav>
    <span class="eyebrow">Your slice of rewards lives here</span>
    <h1>Specials & promotions</h1>
    <p class="lede">Daily specials, $10 lunches, app rewards and a thank-you for our local heroes. Here’s every way to get more out of your next Square Peg visit.</p>
    <div class="btn-row"><a class="btn btn--flame" href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="promos-head"{{ ext|safe }}>Get the app</a><a class="btn btn--ghost" href="{{ u('/deals/') }}">This month’s deal</a></div>
  </div>
</section>
<nav class="menu-jump" aria-label="On this page"><div class="wrap"><a href="#daily">Daily specials</a><a href="#lunch">$10 lunch</a><a href="#app">App rewards</a><a href="#punch">Punch cards</a><a href="#heroes">Local heroes</a><a href="#gift">Gift cards</a></div></nav>
<section class="section" id="daily">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">After 5pm</span><h2>Daily specials</h2></div>
    <div class="deal-grid">{% for d, name, price, note in promos.daily %}<article class="deal-card" data-ent-day="{{ d[:3] }}"><span class="deal-day">{{ d }}</span><h3>{{ name }}</h3><b class="deal-price">{{ price }}</b><p>{{ note }}</p></article>{% endfor %}</div>
  </div>
</section>
<section class="section section--dark on-dark" id="lunch">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">Monday–Friday · 11am–2pm where open · dine-in</span>
      <h2>Lunch specials. Only $10.</h2>
      <p class="prose" style="color:#e6ddd6">Drink included. Clean. Fast. Tasty. That’s lunch done right.</p>
      <p class="note" style="color:#cfc6bf">{{ promos.lunch_note }}</p>
      <ul class="lunch-where">{% for w in lunch_where %}<li><a href="{{ u('/locations/' ~ w.slug ~ '/') }}">{{ w.name }}</a><span>{{ w.when }}, {{ w["from"] }}</span></li>{% endfor %}</ul>
      <div class="btn-row"><a class="btn" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find a Square Peg</a><a class="btn btn--ghost" href="{{ u('/roll-the-dice/') }}">Roll the dice at lunch</a></div>
    </div>
    <div class="lunch-list">{% for n, dsc in promos.lunch %}<div class="lunch-item"><b>{{ n }}</b><span>{{ dsc }}</span><em>$10</em></div>{% endfor %}</div>
  </div>
</section>
<section class="section" id="app">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Inside the Square Peg app</span><h2>Be nice. Earn more.</h2><p>Get $5 off your next order, exclusive in-app deals, flash promos and rewards every time you visit.</p></div>
    <div class="deal-grid">{% for t, dsc in promos.app %}<article class="deal-card"><h3>{{ t }}</h3><p>{{ dsc }}</p></article>{% endfor %}</div>
    <ul class="perks perks--row">{% for pk in promos.app_perks %}<li>{{ pk }}</li>{% endfor %}</ul>
    <div class="btn-row"><a class="btn btn--dark" href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="promos-app"{{ ext|safe }}>Download the app</a><a class="btn btn--line" href="{{ u('/deals/') }}">Points shop & monthly deal</a></div>
  </div>
</section>
<section class="section section--paper" id="punch">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Digital punch cards, in the app</span><h2>Buy six. The next one’s on us.</h2></div>
    <div class="punch-grid">{% for t, when in promos.punch %}<article class="punch"><div class="holes" aria-hidden="true">{% for i in range(6) %}<i></i>{% endfor %}<i class="free">FREE</i></div><h3>{{ t }}</h3><p class="note">{{ when }}</p></article>{% endfor %}</div>
  </div>
</section>
<section class="section" id="heroes">
  <div class="wrap heroes">
    <div class="big-num" aria-hidden="true">15<sup>%</sup></div>
    <div class="stack"><span class="eyebrow">A salute to our local heroes</span><h2>15% off for those who serve.</h2><p class="prose">{{ promos.heroes }}</p></div>
  </div>
</section>
<section class="section section--dark on-dark" id="gift">
  <div class="wrap gift-band">
    <div class="stack"><span class="eyebrow">Gift cards</span><h2>Give the gift of pizza.</h2><p class="prose" style="color:#e6ddd6">Birthdays, teachers, coaches, thank-yous. Square Peg gift cards work at every location.</p></div>
    <a class="btn btn--flame" href="{{ site.gift_cards_url }}" rel="noopener" data-track="giftcard_click" data-src="promos"{{ ext|safe }}>Buy a gift card</a>
  </div>
</section>
"""

T["game_day"] = """
<section class="page-head on-dark gd-head">
  {{ img('oven-fire', 'Pizza in the wood-fired oven', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><a href="{{ u('/promotions/') }}">Specials</a><span aria-hidden="true">/</span><span>Game Day</span></nav>
    <span class="eyebrow">{{ gd.tagline }}</span>
    <h1>Game day <span class="gd-hot">specials</span></h1>
    <p class="lede">Food, drinks, football. Wood-fired pizza, cold drinks and every game on — all season long at nine Square Pegs.</p>
    <div class="btn-row"><a class="btn" href="#pizzas">See the game day pizzas</a><a class="btn btn--ghost" href="{{ u('/locations/') }}">Find your Peg</a></div>
  </div>
</section>

<div class="gd-off" data-season-from="{{ gd.season_from }}" data-season-to="{{ gd.season_to }}" data-season-invert hidden>
  <div class="wrap">
    <h2>Game day specials are back next season.</h2>
    <p>Our football specials run from September through the big game. In the meantime there’s still plenty on — daily specials, rewards and a wood-fired oven that never cools down.</p>
    <div class="btn-row"><a class="btn" href="{{ u('/promotions/') }}">See what’s on now</a><a class="btn btn--ghost" href="{{ u('/entertainment/') }}">Trivia, bingo &amp; DJ nights</a></div>
  </div>
</div>

<div data-season-from="{{ gd.season_from }}" data-season-to="{{ gd.season_to }}">
<section class="section section--dark on-dark gd-band-wrap">
  <div class="wrap">
    <div class="gd-band">{% for price, what, when, pic in gd.band %}<div class="gd-band-item">
      <div class="gd-band-text"><b>{{ price }}</b><span>{{ what }}</span><em>{{ when }}</em></div>
      <div class="gd-band-pic">{{ img(pic, what, sizes='110px')|safe }}</div>
    </div>{% endfor %}</div>
    <p class="note gd-band-note">Game day pricing runs while football is on. Ask your server what’s playing.</p>
  </div>
</section>

<nav class="menu-jump" aria-label="On this page"><div class="wrap"><a href="#cocktails">Cocktails</a><a href="#mocktails">Mocktails</a><a href="#pizzas">Game day pizzas</a><a href="#sunday-ticket">Sunday Ticket</a><a href="#where">Where</a></div></nav>

<section class="section" id="cocktails">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">{{ gd.cocktails_price }}</span><h2>Game day cocktails</h2></div>
    <div class="gd-grid">{% for name, style, parts, garnish in gd.cocktails %}<article class="gd-card">
      <header><h3>{{ name }}</h3>{% if style %}<span class="gd-style">{{ style }}</span>{% endif %}</header>
      <ul>{% for p in parts %}<li>{{ p }}</li>{% endfor %}</ul>
      <p class="gd-garnish">{{ garnish }}</p>
    </article>{% endfor %}</div>
  </div>
</section>

<section class="section section--paper" id="mocktails">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">{{ gd.mocktails_price }} · no alcohol</span><h2>Mocktails</h2></div>
    <div class="gd-grid gd-grid--two">{% for name, style, parts, garnish in gd.mocktails %}<article class="gd-card gd-card--zero">
      <header><h3>{{ name }}</h3>{% if style %}<span class="gd-style">{{ style }}</span>{% endif %}</header>
      <ul>{% for p in parts %}<li>{{ p }}</li>{% endfor %}</ul>
      <p class="gd-garnish">{{ garnish }}</p>
    </article>{% endfor %}</div>
  </div>
</section>

<section class="section section--dark on-dark" id="pizzas">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">{{ gd.pizza_price }} · same price on both</span><h2>Game day pizzas</h2></div>
    <div class="gd-pizzas">{% for name, pic, style, parts in gd.pizzas %}<article class="gd-pizza">
      <div class="gd-pizza-pic">{{ img(pic, name ~ ' — ' ~ style ~ ' pizza at Square Peg', sizes='(min-width:760px) 50vw, 100vw')|safe }}</div>
      <div class="gd-pizza-body">
        <span class="gd-pizza-kicker">{{ style }}</span>
        <h3>{{ name }}</h3>
        <p class="gd-pizza-parts">{{ parts|join(' · ') }}</p>
      </div>
    </article>{% endfor %}</div>
    <div class="btn-row gd-order"><a class="btn" href="{{ site.order_picker_toast }}" rel="noopener" data-track="order_click" data-src="game-day"{{ ext|safe }}>Order a game day pie</a><a class="btn btn--ghost" href="{{ u('/our-menu/') }}">See the full menu</a></div>
  </div>
</section>

<section class="section section--paper" id="sunday-ticket">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Sundays start here</span><h2>NFL Sunday Ticket</h2></div>
    <div class="gd-st">
      <div class="gd-st-copy">
        <p class="lede">Every live out-of-market Sunday afternoon game, on our screens. Bring the crew, order a pie, and watch your team even when the local channels aren’t carrying them.</p>
        <p class="gd-st-at"><b>Watch it at:</b> {% for l in st_locs %}<a href="{{ u('/locations/' ~ l.slug ~ '/') }}">{{ l.short or l.name }}</a>{% if not loop.last %} · {% endif %}{% endfor %}</p>
        <p class="note">{{ gd.sunday_ticket_note }}</p>
        <div class="btn-row"><a class="btn" href="{{ u('/locations/') }}">Hours &amp; directions</a></div>
      </div>
      <figure class="gd-st-art">{{ img('sunday-ticket', 'NFL Sunday Ticket for Business from EverPass: watch every live out-of-market Sunday game here', sizes='(min-width:900px) 420px, 92vw')|safe }}</figure>
    </div>
  </div>
</section>

<section class="section" id="where">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">All games. All season long.</span><h2>Where to watch</h2></div>
    <p class="lede">Game day drinks are on at every Square Peg with a bar, and a full bar is coming soon to Bolton. Wherever you watch, the pizza is on.</p>
    <ul class="town-list gd-where">{% for l in gd_locs %}<li><a href="{{ u('/locations/' ~ l.slug ~ '/') }}"><b>{{ l.short or l.name }}</b><span>{{ l.city }}, {{ l.state }}{% if l.sunday_ticket %} · <em>Sunday Ticket</em>{% endif %}</span></a></li>{% endfor %}</ul>
    <p class="note">Please drink responsibly. Must be 21+ to order alcohol; ID required.</p>
  </div>
</section>
</div>
"""

T["entertainment"] = """
<section class="page-head on-dark">
  {{ img('friends-holiday', 'Friends enjoying a night out at Square Peg', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Entertainment</span></nav>
    <span class="eyebrow">Trivia · Bingo · DJ nights</span>
    <h1>Trivia, bingo & live DJ nights</h1>
    <p class="lede">More than dinner. It’s a night out. Weekly entertainment at {{ ent_count }} Square Pegs, plus private celebrations any night of the week.</p>
    <div class="btn-row"><a class="btn" href="#lineup">See the weekly lineup</a><a class="btn btn--ghost" href="{{ u('/large-party-reservations/') }}">Reserve for a group</a></div>
  </div>
</section>
{% if events_all %}<section class="section ev-band" id="tickets" data-season-from="2000-01-01" data-season-to="{{ events_all[-1].date }}" hidden>
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Buy a ticket</span><h2>Special events</h2></div>
    <div class="ev-grid">{% for e in events_all %}<article class="ev-card" data-season-from="{{ e.announce }}" data-season-to="{{ e.date }}" hidden>
      <div class="ev-when"><span class="mo">{{ e.mon }}</span><b>{{ e.day }}</b><span class="dow">{{ e.weekday[:3] }}</span></div>
      <div class="ev-body">
        <h3>{{ e.title }}</h3>
        <p class="note">Square Peg {{ e.loc.short or e.loc.name }} · {{ e.loc.city }}, {{ e.loc.state }}</p>
        <ul class="ev-meta">{% for m in e.meta %}<li>{{ m }}</li>{% endfor %}</ul>
        <a class="link-arrow" href="{{ e.url }}" rel="noopener"{{ ext|safe }} data-track="event_ticket_click" data-src="{{ e.loc.slug }}-entertainment">{{ e.cta or 'Get tickets' }} →</a>
      </div>
    </article>{% endfor %}</div>
  </div>
</section>{% endif %}
<section class="section section--paper" id="tonight">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Happening today</span><h2>Tonight at Square Peg</h2></div>
    <div class="tonight" data-tonight><p class="note">Loading tonight’s lineup…</p></div>
  </div>
</section>
<section class="section" id="lineup">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Every week</span><h2>What’s happening at each Square Peg</h2></div>
    <div class="ent-grid">{% for slug in ent_slugs %}{% set l = loc_by_slug[slug] %}<article class="ent-card">
      <header><h3><a href="{{ u('/locations/' ~ slug ~ '/') }}">{{ l.short or l.name }}</a></h3><span class="note">{{ l.city }}, {{ l.state }}</span></header>
      {% for d, e, t, fr in ent.get(slug, []) %}<div class="ent-row" data-ent-day="{{ d }}"{% if fr %} data-ent-from="{{ fr }}"{% endif %}><b>{{ day_names[d] }}</b><span>{{ e }}{% if fr %} <i class="ent-soon">from {{ ent_from(fr) }}</i>{% endif %}</span><em>{{ t }}</em></div>{% endfor %}
      {% for iso, what, when, label in ent_dates_all.get(slug, []) %}<div class="ent-row is-dated" data-season-from="2000-01-01" data-season-to="{{ iso }}" hidden><b>{{ label }}</b><span>{{ what }} <i class="ent-once">one night</i></span><em>{{ when }}</em></div>{% endfor %}
      {% for e in events_by_slug.get(slug, []) %}<div class="ent-row is-ticketed" data-season-from="{{ e.announce }}" data-season-to="{{ e.date }}" hidden><b>{{ e.weekday[:3] }} {{ e.mon }} {{ e.day }}</b><span><a href="{{ e.url }}" rel="noopener"{{ ext|safe }} data-track="event_ticket_click" data-src="{{ slug }}-lineup">{{ e.title }}</a> <i class="ent-ticket">tickets</i></span><em>{{ e.meta[0] }}</em></div>{% endfor %}
      <a class="btn btn--sm btn--line" href="{{ u('/locations/' ~ slug ~ '/') }}" aria-label="Hours & directions: Square Peg {{ l.short or l.name }}">Hours & directions</a>
    </article>{% endfor %}</div>
    <p class="note" style="margin-top:20px">Schedules can change for holidays and special events. Call your location to confirm.</p>
    <div class="class-band"><div><span class="eyebrow">Monthly</span><h3>Pizza-making classes</h3><p>Adult classes every month, plus free kids’ classes. Stretch, top and fire your own pie.</p></div><div class="btn-row"><a class="btn" href="{{ site.events_calendar_url }}" target="_blank" rel="noopener" data-track="classes_click" data-src="entertainment">See dates & get tickets</a><a class="btn btn--line" href="{{ u('/private-events/') }}#classes">About the classes</a></div></div>
  </div>
</section>
"""

T["caught"] = """
<section class="page-head on-dark caught-head">
  {{ img('sp-hero-board', 'Wood-fired pizzas on a board beside Square Peg Pizzeria boxes', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <span class="eyebrow">The evidence</span>
    <h1>Fine. Here are<br>the photos.</h1>
    <p class="lede">Nobody cheated on anybody. There is no Kevin. But somebody around here has been settling for worse pizza, and we have reason to believe it&rsquo;s you.</p>
    <p class="caught-sub">You scanned it. Honestly? Respect.</p>
  </div>
</section>

<section class="section section--dark on-dark">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Submitted into evidence</span><h2>What you did</h2></div>
    <div class="shots">
      {% for pic, ex, name, line in shots %}<figure class="shot">
        {{ img(pic, name ~ ' at Square Peg Pizzeria', sizes='(min-width:900px) 33vw, 100vw')|safe }}
        <figcaption><b>{{ ex }} &middot; {{ name }}</b><span>{{ line }}</span></figcaption>
      </figure>{% endfor %}
    </div>
    <p class="note caught-note">Every pie wood-fired, on dough made fresh from scratch. Never frozen. That&rsquo;s the whole case.</p>
  </div>
</section>

<section class="section section--paper" id="rewards">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">We&rsquo;re willing to move past this</span>
      <h2>Here&rsquo;s $5 to start over.</h2>
      <p class="prose">Join Square Peg Rewards and a <b>$5 welcome reward</b> lands in your account. It&rsquo;s free, it takes about a minute, and you earn points on every visit after that.</p>
      <ul class="checks">{% for perk in app_perks %}<li><div>{{ perk }}</div></li>{% endfor %}</ul>
      <div class="btn-row">
        <a class="btn" href="{{ site.loyalty_signup }}" rel="noopener"{{ ext|safe }} data-track="rewards_join" data-src="caught">Claim my $5</a>
        <a class="btn btn--line" href="{{ site.app_link }}" rel="noopener"{{ ext|safe }} data-track="app_click" data-src="caught">Get the app</a>
      </div>
      <p class="note">New members only. One welcome reward per person, because we&rsquo;ve been burned before.</p>
      <div class="already"><b>Already a member?</b> <span>Your points are sitting right there, quietly judging you.</span> <a class="link-arrow" href="{{ site.loyalty_signin }}" rel="noopener"{{ ext|safe }} data-track="rewards_signin" data-src="caught">Check your balance &rarr;</a></div>
    </div>
    <div class="stack">
      <div class="points-card">
        <span class="eyebrow">Then it keeps going</span>
        <ul class="points">{% for row in points[:5] %}<li><b>{{ row[0] }} pts</b><span>{{ row[1] }}</span></li>{% endfor %}</ul>
        <p class="note">Points on every order, in-store or online.</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Ten locations</span><h2>Go make it right</h2></div>
    <p class="prose">Nine across Connecticut and one in Delray Beach, Florida. Pick the one closest to wherever you are being suspicious.</p>
    <div class="btn-row"><a class="btn" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find your Square Peg</a><a class="btn btn--line" href="{{ site.menu_url }}" data-open-picker="menu">See the menu</a></div>
    <p class="note caught-fine">No Kevins were harmed in the making of this flyer. Any resemblance to an actual Kevin is a coincidence and, frankly, his business.</p>
  </div>
</section>
"""

T["evidence"] = """
<section class="page-head on-dark ev-head">
  {{ img('sp-three-pies', 'Three wood-fired pizzas on a board at Square Peg Pizzeria', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <span class="eyebrow">Case closed</span>
    <h1>Here&rsquo;s the<br>evidence.</h1>
    <p class="lede">Your motivation to cook is not coming back. It has been gone since about 5:30. We checked, and honestly we didn&rsquo;t look that hard, because the alternative is right here.</p>
    <div class="btn-row">
      <a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="evidence">{{ icons.bag|safe }}Order now</a>
      <a class="btn btn--ghost" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find your Square Peg</a>
    </div>
  </div>
</section>

<section class="section section--dark on-dark">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Exhibit one</span><h2>The pizza</h2></div>
    <p class="prose ev-sub">Dough made fresh from scratch, never frozen. Eighty seconds in a wood fire. Red or white, Neo-Neapolitan rounds or crispy-edged Detroit style, gluten-free 12&Prime; crust and vegan cheese on anything.</p>
    <div class="ev-pies">{% for n, d, pic in sigs %}<figure class="ev-pie">
      {{ img(pic, n ~ ' pizza at Square Peg Pizzeria', sizes='(min-width:900px) 25vw, 50vw')|safe }}
      <figcaption><b>{{ n }}</b><span>{{ d }}</span></figcaption>
    </figure>{% endfor %}</div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Exhibit two</span><h2>Everything else</h2></div>
    <p class="prose">Not in a pizza mood? Nobody has to know what you ordered.</p>
    <div class="ev-menu">{% for title, items in menu_bits %}<div class="ev-col">
      <h3>{{ title }}</h3>
      <ul>{% for n, d in items %}<li><b>{{ n }}</b><span>{{ d }}</span></li>{% endfor %}</ul>
    </div>{% endfor %}</div>
    <div class="btn-row ev-order">
      <a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="evidence-menu">{{ icons.bag|safe }}Start an order</a>
      <a class="btn btn--line" href="{{ u('/our-menu/') }}">See the full menu</a>
    </div>
  </div>
</section>

<section class="section section--dark on-dark">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">While you&rsquo;re not cooking</span>
      <h2>Get $5 for showing up.</h2>
      <p class="prose" style="color:#e6ddd6">Join Square Peg Rewards and a <b>$5 welcome reward</b> lands in your account. Free, takes a minute, and you earn points every visit after that.</p>
      <div class="btn-row">
        <a class="btn" href="{{ site.loyalty_signup }}" rel="noopener"{{ ext|safe }} data-track="rewards_join" data-src="evidence">Claim my $5</a>
        <a class="btn btn--ghost" href="{{ site.app_link }}" rel="noopener"{{ ext|safe }} data-track="app_click" data-src="evidence">Get the app</a>
      </div>
      <p class="note" style="color:#cfc6bf">Already a member? <a href="{{ site.loyalty_signin }}" rel="noopener"{{ ext|safe }} data-track="rewards_signin" data-src="evidence">Check your balance &rarr;</a></p>
    </div>
    <div class="stack">
      <div class="ev-box">
        <span class="eyebrow">Ten locations</span>
        <h3>Pickup, delivery or a table</h3>
        <p>Nine across Connecticut and one in Delray Beach, Florida. Order online, or come sit down and let someone else do the dishes too.</p>
        <div class="btn-row"><a class="btn btn--sm" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find the closest one</a></div>
      </div>
    </div>
  </div>
  <div class="wrap"><p class="note ev-fine">No motivation was recovered in the making of this page. We&rsquo;re not looking for it either.</p></div>
</section>
"""

T["links"] = """
<section class="linkpage">
  <div class="wrap">
    <a class="link-logo" href="{{ u('/') }}" aria-label="Square Peg Pizzeria home">
      {{ logo_img("260px", 280, widths=(280, 360, 480))|safe }}
    </a>
    <p class="link-lede">Wood-fired pizza, ten locations, dough made fresh from scratch.<br>Everything you might be looking for is right here.</p>

    <ul class="link-list">{% for label, dest, sub, hot in links_rows %}
      <li><a class="link-row{{ ' is-hot' if hot }}"
             href="{% if dest == 'ORDER' %}{{ site.order_picker_toast }}{% elif dest == 'GIFT' %}{{ site.gift_cards_url }}{% elif dest.startswith('http') %}{{ dest }}{% else %}{{ u(dest) }}{% endif %}"
             {% if dest in ('ORDER', 'GIFT') or dest.startswith('http') %}rel="noopener"{{ ext|safe }}{% endif %}
             data-track="link_click" data-src="{{ label|lower|replace(' ', '-') }}">
        <span class="link-label">{{ label }}</span>
        {% if sub %}<span class="link-sub">{{ sub }}</span>{% endif %}
        <span class="link-arrow" aria-hidden="true">{{ icons.arrow|safe }}</span>
      </a></li>{% endfor %}
    </ul>

    <div class="link-social">
      <a href="{{ site.facebook }}" rel="noopener"{{ ext|safe }}>Facebook</a>
      <a href="{{ site.instagram }}" rel="noopener"{{ ext|safe }}>Instagram</a>
      <a href="{{ u('/contact/') }}">Contact</a>
    </div>
    <p class="link-foot">Be Nice. &mdash; Square Peg Pizzeria</p>
  </div>
</section>
"""

T["townpage"] = """
<section class="page-head on-dark">
  {{ img(tp.hero, tp.h1 ~ ' at Square Peg Pizzeria', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><a href="{{ u('/locations/') }}">Locations</a><span aria-hidden="true">/</span><span>{{ tp.h1 }}</span></nav>
    <span class="eyebrow">{{ tp.eyebrow }}</span>
    <h1>{{ tp.h1 }}</h1>
    <p class="lede">{{ tp.lede|safe }}</p>
    <div class="btn-row">
      <a class="btn" href="{{ order(store) }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="{{ tp.slug }}">{{ icons.bag|safe }}Order from {{ store.name }}</a>
      <a class="btn btn--ghost" href="tel:{{ store.tel }}" data-track="call_click" data-src="{{ tp.slug }}">{{ icons.phone|safe }}{{ store.phone }}</a>
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="loc-strip">
      <div><span class="eyebrow">Where</span><p><b>{{ store.street }}</b><br>{{ store.city }}, {{ store.state }} {{ store.zip }}</p></div>
      <div><span class="eyebrow">Open now?</span><p><span class="status" data-status="{{ store.slug }}">Hours</span></p></div>
      <div><span class="eyebrow">The full page</span><p><a class="link-arrow" href="{{ u('/locations/' ~ store.slug ~ '/') }}">{{ store.name }} hours, menu &amp; directions</a></p></div>
    </div>
  </div>
</section>

{% for sec in tp.sections %}
<section class="section{{ ' section--paper' if loop.index0 % 2 else '' }}">
  <div class="wrap{{ ' two-col' if sec.img else '' }}"{% if sec.img %} style="align-items:center"{% endif %}>
    <div class="stack">
      <div class="section-head"><span class="eyebrow">{{ sec.eyebrow|safe }}</span><h2>{{ sec.head|safe }}</h2></div>
      <div class="prose-block">{% for para in sec.paras %}<p>{{ para|safe }}</p>{% endfor %}</div>
      {% if sec.ctas %}<div class="btn-row">{% for label, href in sec.ctas %}<a class="btn{{ ' btn--line' if not loop.first else '' }}" href="{{ u(href) }}">{{ label }}</a>{% endfor %}</div>{% endif %}
    </div>
    {% if sec.img %}<figure class="feature-photo tp-art">{{ img(sec.img[0], sec.img[1], sizes='(min-width:960px) 380px, 70vw')|safe }}</figure>{% endif %}
  </div>
</section>
{% endfor %}

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Asked and answered</span><h2>{{ tp.h1 }}: the questions</h2></div>
    <div class="faq">{% for q, a in tp.faq %}<details><summary>{{ q|safe }}</summary><p>{{ a|safe }}</p></details>{% endfor %}</div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap cta-foot">
    <h2>Eat at {{ store.name }}.</h2>
    <p class="prose">{{ store.street }}, {{ store.city }}, {{ store.state }} {{ store.zip }} &middot; {{ store.phone }}</p>
    <div class="btn-row">
      <a class="btn" href="{{ order(store) }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="{{ tp.slug }}-foot">{{ icons.bag|safe }}Order from {{ store.name }}</a>
      <a class="btn btn--line" href="{{ u('/locations/' ~ store.slug ~ '/') }}">Hours &amp; directions</a>
      <a class="btn btn--line" href="{{ u('/our-menu/') }}">See the menu</a>
    </div>
  </div>
</section>
"""

T["fundraiser_night"] = """
<section class="page-head on-dark">
  {{ img('team-kids', 'A group celebrating a Tuesday fundraiser at Square Peg', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><a href="{{ u('/fundraisers/') }}">Fundraisers</a><span aria-hidden="true">/</span><span>Fundraiser night</span></nav>
    <span class="eyebrow">Tuesdays &middot; {{ fn.window }}</span>
    <h1>Fundraiser night at Square Peg</h1>
    <p class="lede">Somebody sent you here because their group has a Tuesday with us.
      Here&rsquo;s the whole thing: come in, eat dinner, mention them, and
      <b>{{ fn.share }} of what you spend on food goes back to them</b>.</p>
    <div class="btn-row">
      <a class="btn" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.pin|safe }}Find your Square Peg</a>
      <a class="btn btn--ghost" href="{{ u('/our-menu/') }}">See the menu</a>
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Three things, and that&rsquo;s it</span>
      <h2>What to do on the night</h2>
    </div>
    <ol class="steps steps--row">
      {% for head, body in fn.steps %}<li><div><b>{{ head }}</b><span>{{ body }}</span></div></li>{% endfor %}
    </ol>
  </div>
</section>

<section class="section">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">Counts towards the total</span>
      <h2>What raises money</h2>
      <ul class="checks">{% for i in fn.counts %}<li>{{ i }}</li>{% endfor %}</ul>
    </div>
    <div class="stack">
      <span class="eyebrow">Doesn&rsquo;t count</span>
      <h2>What doesn&rsquo;t</h2>
      <ul class="checks checks--no">{% for i in fn.excluded %}<li>{{ i }}</li>{% endfor %}</ul>
      <p class="note">None of this is us being difficult &mdash; it&rsquo;s how the night gets
        counted fairly at the end. The short version: eat in, and say the name.</p>
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Before you come</span><h2>Questions</h2></div>
    <div class="faq">{% for q, a in fn.faq %}<details><summary>{{ q }}</summary><p>{{ a }}</p></details>{% endfor %}</div>
  </div>
</section>

<section class="section">
  <div class="wrap cta-foot">
    <span class="eyebrow">Run a group yourself?</span>
    <h2>Book your own Tuesday.</h2>
    <p class="prose">Schools, teams, clubs and nonprofits can claim a Tuesday at any
      Square Peg. We handle the tracking and send the donation after the night.</p>
    <div class="btn-row">
      <a class="btn" href="{{ u('/fundraisers/') }}">How fundraisers work</a>
      <a class="btn btn--line" href="{{ u('/locations/') }}">Find a Square Peg</a>
    </div>
  </div>
</section>
"""

T["pizzafaq"] = """
<section class="page-head on-dark">
  {{ img('oven-pizza', 'A pizza coming out of the wood-fired oven', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Pizza FAQ</span></nav>
    <span class="eyebrow">Straight answers</span>
    <h1>Pizza questions,<br>answered properly</h1>
    <p class="lede">Slice counts, reheating, gluten-free, how much to order. Answered by the people who make it, not scraped off another pizzeria&rsquo;s site.</p>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <nav class="faq-jump" aria-label="Jump to a section">{% for group, items in faq_groups %}<a href="#{{ group|lower|replace(' ', '-')|replace('&', 'and') }}">{{ group }}</a>{% endfor %}</nav>
  </div>
</section>

{% for group, items in faq_groups %}
<section class="section {{ 'section--dark on-dark' if loop.index is odd else 'section--paper' }}" id="{{ group|lower|replace(' ', '-')|replace('&', 'and') }}">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">{{ loop.index }} of {{ loop.length }}</span><h2>{{ group }}</h2></div>
    <div class="faq-list">{% for q, a in items %}
      <details class="faq-item"{% if loop.first %} open{% endif %}>
        <summary><h3>{{ q }}</h3><span class="faq-mark" aria-hidden="true"></span></summary>
        <div class="faq-body"><p>{{ a|safe }}</p></div>
      </details>{% endfor %}
    </div>
  </div>
</section>
{% endfor %}

<section class="section section--paper">
  <div class="wrap cta-foot">
    <h2>Still working out how much to order?</h2>
    <div class="btn-row">
      <a class="btn" href="{{ u('/pizza-calculator/') }}">Use the pizza calculator</a>
      <a class="btn btn--line" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="faq">{{ icons.bag|safe }}Order online</a>
    </div>
  </div>
</section>
"""

T["trivia"] = """
<section class="page-head on-dark">
  {{ img('dough', 'Dough being made by hand at Square Peg', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Pizza trivia</span></nav>
    <span class="eyebrow">Pizza trivia</span>
    <h1>Things that are<br>true about pizza</h1>
    <p class="lede">And three things everyone repeats that aren&rsquo;t. We checked before printing them, which is more than the internet usually manages.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Verified</span><h2>Actually true</h2></div>
    <div class="triv-grid">{% for head, body, ok in trivia.facts %}
      <article class="triv-card"><span class="triv-tag triv-true">True</span><h3>{{ head }}</h3><p>{{ body }}</p></article>{% endfor %}
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Hold on</span><h2>Three myths worth retiring</h2></div>
    <div class="triv-grid">{% for head, body in trivia.myths %}
      <article class="triv-card triv-card--myth"><span class="triv-tag triv-myth">Myth</span><h3>{{ head }}</h3><p>{{ body }}</p></article>{% endfor %}
    </div>
  </div>
</section>

<section class="section section--dark on-dark">
  <div class="wrap cta-foot">
    <h2>Settle it over a pizza.</h2>
    <p class="prose">Bingo and trivia nights run at most of our locations &mdash; and yes, pizza questions come up.</p>
    <div class="btn-row">
      <a class="btn" href="{{ u('/entertainment/') }}">See what&rsquo;s on</a>
      <a class="btn btn--ghost" href="{{ u('/what-pizza-are-you/') }}">What pizza are you?</a>
    </div>
  </div>
</section>
"""

T["datenight"] = """
<section class="page-head on-dark">
  {{ img('friends-sharing', 'Sharing a wood-fired pizza at Square Peg', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Date night</span></nav>
    <span class="eyebrow">Date night</span>
    <h1>A good night out,<br>without the production</h1>
    <p class="lede">{{ datenight.lede }}</p>
    <div class="btn-row">
      <a class="btn" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find a table</a>
      <a class="btn btn--ghost" href="{{ u('/pairing/') }}">What should we drink?</a>
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Why here</span><h2>Four reasons it works</h2></div>
    <div class="dn-grid">{% for head, body in datenight.reasons %}
      <article class="dn-card"><h3>{{ head }}</h3><p>{{ body }}</p></article>{% endfor %}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">How to order</span><h2>A night, in four moves</h2></div>
    <ol class="dn-steps">{% for label, body in datenight.order %}
      <li><b>{{ label }}</b><span>{{ body|safe }}</span></li>{% endfor %}
    </ol>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Worth timing</span><h2>Nights that are already good</h2></div>
    <div class="dn-grid">
      {% for d, name, price, note in promos.daily %}<article class="dn-card dn-card--deal"><span class="eyebrow">{{ d }}</span><h3>{{ name }}</h3><b class="dn-price">{{ price }}</b><p>{{ note }}</p></article>{% endfor %}
      <article class="dn-card dn-card--deal"><span class="eyebrow">{{ promos.happy_hour.days }}</span><h3>Happy hour</h3><b class="dn-price">{{ promos.happy_hour.time }}</b><p>At every location with a bar. Bolton doesn&rsquo;t have one yet.</p></article>
    </div>
    <p class="note" style="margin-top:18px">Live music, trivia and bingo run most weeks too &mdash; the <a href="{{ u('/entertainment/') }}">entertainment page</a> has the current lineup by location.</p>
  </div>
</section>

<section class="section section--dark on-dark">
  <div class="wrap cta-foot">
    <h2>Pick a night.</h2>
    <div class="btn-row">
      <a class="btn" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find your Square Peg</a>
      <a class="btn btn--ghost" href="{{ u('/large-party-reservations/') }}">Bringing more than two?</a>
    </div>
  </div>
</section>
"""

T["quiz"] = """
<section class="page-head on-dark">
  {{ img('sp-three-pies', 'Three Square Peg pizzas on a board', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>What pizza are you?</span></nav>
    <span class="eyebrow">Six questions</span>
    <h1>What pizza<br>are you?</h1>
    <p class="lede">Entirely unscientific. Takes about thirty seconds, and the answer is something you can actually order.</p>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div id="quiz" class="quiz" data-order="{{ site.order_picker_toast }}" data-total="{{ quiz.questions|length }}">
      <noscript><p class="note">This one needs JavaScript. The <a href="{{ u('/our-menu/') }}">menu</a> works fine without it.</p></noscript>
    </div>
    <script type="application/json" id="quiz-cfg">{{ quiz_json|safe }}</script>
  </div>
</section>

<section class="section">
  <div class="wrap cta-foot">
    <h2>Or skip the quiz.</h2>
    <div class="btn-row">
      <a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="quiz">{{ icons.bag|safe }}Order online</a>
      <a class="btn btn--line" href="{{ u('/our-menu/') }}">See the whole menu</a>
    </div>
  </div>
</section>
"""

T["calculator"] = """
<section class="page-head on-dark">
  {{ img('pizza-boxes', 'Stacked Square Peg pizza boxes', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Pizza calculator</span></nav>
    <span class="eyebrow">Stop guessing</span>
    <h1>How many pizzas<br>do I need?</h1>
    <p class="lede">Tell us who&rsquo;s eating. We&rsquo;ll tell you what to order &mdash; based on how much pizza is actually on the pie, not a flat slices-per-person rule.</p>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <form class="calc" id="pizza-calc" novalidate>
      <div class="calc-grid">
        <label class="calc-f"><span>Adults</span>
          <input type="number" id="calc-adults" min="0" max="400" step="1" value="4" inputmode="numeric"></label>
        <label class="calc-f"><span>Kids</span>
          <input type="number" id="calc-kids" min="0" max="400" step="1" value="0" inputmode="numeric"></label>
        <label class="calc-f"><span>Appetite</span>
          <select id="calc-appetite">{% for key, label, area in calc.appetites %}<option value="{{ area }}"{{ ' selected' if key == 'normal' }}>{{ label }}</option>{% endfor %}</select></label>
      </div>
      <label class="calc-check"><input type="checkbox" id="calc-sides"><span>We&rsquo;re also getting appetizers, wings or salads</span></label>
    </form>

    {#- A real answer for the default inputs, so the page works without JS and so the
        answer styles are in the stylesheet the page inlines. JS replaces it on input. -#}
    {% set need = 4 * calc.appetites[1][2] %}
    {% set larges = (need / calc.sizes[0][3])|round(0, 'ceil')|int %}
    <output class="calc-out" id="calc-out" for="pizza-calc" aria-live="polite">
      <div class="calc-answer"><span class="calc-eyebrow">Order about</span>
        <b class="calc-big">{{ larges }} large pizza{{ '' if larges == 1 else 's' }}</b>
        <span class="calc-sub">{{ larges * calc.sizes[0][2] }} slices for 4 people</span></div>
      <p class="calc-detail">Tighter option: <b>{{ larges - 1 }} large + 1 small</b>.</p>
    </output>

    <div class="btn-row calc-cta">
      <a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="calculator">{{ icons.bag|safe }}Order online</a>
      <a class="btn btn--line" href="{{ u('/catering/') }}">Feeding a crowd? See catering</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">The sizes</span><h2>What you&rsquo;re actually ordering</h2></div>
    <div class="calc-table" role="table" aria-label="Pizza sizes and slice counts">
      <div class="calc-row calc-head" role="row"><span role="columnheader">Size</span><span role="columnheader">Slices</span><span role="columnheader">Feeds</span></div>
      {% for label, dim, slices, area in calc.sizes %}<div class="calc-row" role="row">
        <span role="cell"><b>{{ label }}</b></span>
        <span role="cell">{{ slices }}</span>
        <span role="cell">{{ (area / 70)|round(1) }}&ndash;{{ (area / 48)|round(1) }} adults</span>
      </div>{% endfor %}
    </div>
    <p class="note" style="margin-top:16px">Feeds assumes pizza is the whole meal. With appetizers on the table, each pie stretches about 20% further.</p>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Worth knowing</span><h2>Four things that change the answer</h2></div>
    <div class="calc-notes">{% for head, body in calc.notes %}
      <article><h3>{{ head }}</h3><p>{{ body }}</p></article>{% endfor %}
    </div>
  </div>
</section>

<section class="section section--dark on-dark">
  <div class="wrap cta-foot">
    <h2>Got your number?</h2>
    <p class="prose">Order online for pickup or delivery, or book catering for {{ calc.catering_threshold }} or more.</p>
    <div class="btn-row">
      <a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="calculator-foot">{{ icons.bag|safe }}Order online</a>
      <a class="btn btn--ghost" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find a location</a>
    </div>
  </div>
</section>

<script type="application/json" id="calc-cfg">{{ calc_json|safe }}</script>
"""

T["halloween"] = """
<section class="page-head on-dark hw-head">
  {{ img('oven-fire', 'Pizza in the wood-fired oven at Square Peg', eager=True, cls='bg')|safe }}
  <span class="hw-web-wrap hw-web-l">{{ hwart.web|safe }}</span>
  <span class="hw-web-wrap hw-web-r">{{ hwart.web|safe }}</span>
  <span class="hw-bat hw-bat-1">{{ hwart.bat|safe }}</span>
  <span class="hw-bat hw-bat-2">{{ hwart.bat|safe }}</span>
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Halloween</span></nav>

    <p class="hw-state hw-soon" data-season-to="{{ hw.eve }}" hidden>Starts {{ hw.starts_long }}</p>
    <p class="hw-state hw-now" data-season-from="{{ hw.starts }}" data-season-to="{{ hw.ends }}" hidden>On now &mdash; through Halloween</p>
    <p class="hw-state hw-done" data-season-from="{{ hw.after }}" hidden>That&rsquo;s a wrap. Winners being picked now.</p>

    <h1><span class="eyebrow h1-eyebrow"><span>{{ hw.when }}</span></span>{{ hw.name }}</h1>
    <p class="lede">{{ hw.lede }}</p>
    <div class="btn-row">
      <a class="btn" href="#enter">{{ icons.arrow|safe }}How to enter</a>
      <a class="btn btn--ghost" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find your Peg</a>
    </div>
  </div>
</section>

<section class="section hw-three">
  <div class="wrap">
    <div class="hw-grid">
      <article class="hw-card">
        <span class="hw-art">{{ hwart.ghost|safe }}</span>
        <span class="hw-num">01</span>
        <h2>Come in costume</h2>
        <p>Any of the six days, not just Halloween. Kids, grown-ups, whole families in a group costume.</p>
      </article>
      <article class="hw-card">
        <span class="hw-art">{{ hwart.pumpkin|safe }}</span>
        <span class="hw-num">02</span>
        <h2>{{ hw.kids.price }} kids meals</h2>
        <p>{{ hw.kids.line }}</p>
        <a class="hw-jump" href="#kids">See the menu {{ icons.arrow|safe }}</a>
      </article>
      <article class="hw-card">
        <span class="hw-art">{{ hwart.bat|safe }}</span>
        <span class="hw-num">03</span>
        <h2>Win {{ hw.prize }}</h2>
        <p>Best costume at every location takes a {{ hw.prize }} &mdash; {{ hw.prize_extra }}.</p>
      </article>
    </div>
  </div>
</section>

<section class="section section--paper hw-spidered" id="enter">
  {{ hwart.costumes|safe }}
  <span class="hw-spider" aria-hidden="true"><i class="hw-thread"></i>{{ hwart.spider|safe }}</span>
  <div class="wrap">
    <div class="hw-head-row">
      <div class="section-head">
        <span class="eyebrow">The costume contest</span>
        <h2>Three steps. None of them hard.</h2>
        <p>{{ hw.winners }} {{ hw.judged }}</p>
      </div>
      <figure class="hw-gc">
        {{ img('gift-card-25', 'A $25 Square Peg Pizzeria gift card', sizes='(min-width:900px) 32vw, 70vw')|safe }}
        <figcaption>What the best costume at your Square Peg takes home.</figcaption>
      </figure>
    </div>
    <ol class="hw-steps">
      {% for head, body in hw.enter %}<li><b>{{ head }}</b><span>{{ body }}</span></li>{% endfor %}
    </ol>
    <p class="hw-tag">Tag it <b>{{ hw.hashtag }}</b></p>
  </div>
</section>

<section class="section section--dark on-dark hw-wall">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">The photo op</span>
      <h2>A wall of cheese pizza. In every location.</h2>
      <p>Eight feet of molten mozzarella mid-stretch. It is, objectively, the best thing in the building to stand in front of in a costume.</p>
      <p>Ask anyone working and they&rsquo;ll take the picture for you &mdash; then post it and tag us.</p>
      <div class="btn-row"><a class="btn" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find your closest Peg</a></div>
    </div>
    <div class="hw-wall-stage">
      <span class="hw-lurk hw-lurk-ghost">{{ hwart.ghost|safe }}</span>
      <span class="hw-lurk hw-lurk-bat">{{ hwart.bat|safe }}</span>
      <span class="hw-lurk hw-lurk-web">{{ hwart.web|safe }}</span>
      <span class="hw-lurk hw-lurk-pumpkin">{{ hwart.pumpkin|safe }}</span>
      <div class="hw-wall-img">{{ img('pizza-wall', 'The pizza wall photo backdrop at Square Peg Pizzeria', sizes='(min-width:900px) 46vw, 100vw')|safe }}</div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="hw-two">
      <article class="hw-panel" id="kids">
        <span class="eyebrow">All six days</span>
        <h2>Kids eat for {{ hw.kids.price }}</h2>
        <p>{{ hw.kids.note }}</p>
        {% for group, items in hw.kids.get('menu', []) %}<h3 class="hw-sub">{{ group }}</h3>
        <ul class="hw-menu">{% for i in items %}<li><span class="hw-dish">{{ i }}</span><span class="hw-dots"></span><span class="hw-price">{{ hw.kids.price }}</span></li>{% endfor %}</ul>{% endfor %}
        {% if hw.drinks.kids %}<h3 class="hw-sub">To drink</h3>
        <ul class="hw-list">{% for n, d in hw.drinks.kids %}<li><b>{{ n }}</b><span>{{ d }}</span></li>{% endfor %}</ul>{% endif %}
        <p class="note">Dine-in, all six days. Drinks priced as usual.</p>
      </article>
      <article class="hw-panel">
        <span class="eyebrow">For the grown-ups</span>
        <h2>Adult drinks, in costume</h2>
        <p>{{ hw.drinks.note }}</p>
        {% if hw.drinks.adults %}<h3 class="hw-sub">Cocktails</h3>
        <ul class="hw-list">{% for n, d in hw.drinks.adults %}<li><span class="hw-row"><span class="hw-dish">{{ n }}</span><span class="hw-dots"></span><span class="hw-price">{{ hw.drinks.adults_price }}</span></span><span>{{ d }}</span></li>{% endfor %}</ul>{% endif %}
        <p class="note">21 and over. At locations with a bar &mdash; Bolton doesn&rsquo;t have one yet.</p>
      </article>
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap cta-foot">
    <h2>See you in costume.</h2>
    <p class="prose">{{ hw.when }}, at all ten Square Pegs.</p>
    <div class="btn-row">
      <a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="halloween">{{ icons.bag|safe }}Order online</a>
      <a class="btn btn--line" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find your Peg</a>
      <a class="btn btn--line" href="{{ u('/monthly-specials/') }}">This month&rsquo;s menu</a>
    </div>
  </div>
</section>

<section class="section hw-rules">
  <span class="hw-web-wrap hw-web-rules">{{ hwart.web|safe }}</span>
  <div class="wrap">
    <h2>The fine print</h2>
    <ul>{% for r in hw.rules %}<li>{{ r }}</li>{% endfor %}</ul>
  </div>
</section>
"""

T["pairing"] = """
<section class="page-head on-dark">
  {{ img('pie-spicy-margherita', 'A Square Peg pizza fresh from the wood-fired oven', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Pairing guide</span></nav>
    <span class="eyebrow">Ask Sal</span>
    <h1>What should I<br>drink with this?</h1>
    <p class="lede">{{ pairing.lede }}</p>
  </div>
</section>

<section class="section section--paper pair-wrap">
  <div class="wrap">
    <div class="pair-intro">
      <figure class="pair-sal">{{ img('sal-pairing-guide', 'Sal, the Square Peg Pizzeria pairing guide', sizes='(min-width:900px) 300px, 150px')|safe }}</figure>
      <div class="pair-intro-copy">
        <span class="eyebrow">Meet Sal</span>
        <h2>He knows what goes with what.</h2>
        <p class="prose">No account, no app, no waiting on a sommelier. Tell him what you&rsquo;re eating and he&rsquo;ll tell you what to drink &mdash; and why that one.</p>
        <p class="pair-cue"><span>Ask him right here</span>
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 4v14m0 0l-6-6m6 6l6-6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </p>
      </div>
    </div>
    <div id="embedded-widget-container" class="pair-widget" style="height:600px;width:100%;margin:0 auto"></div>
    <noscript><p class="note">Sal needs JavaScript to run. The pairings below work either way &mdash; or just ask your server, they know.</p></noscript>
    <p class="note pair-note">Sal is an assistant, not a sommelier with a tasting note for every bottle. Pours vary by location; your server has the current list.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Try asking</span><h2>However you&rsquo;d say it out loud</h2></div>
    <ul class="pair-asks">{% for a in pairing.asks %}<li>{{ a }}</li>{% endfor %}</ul>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">House rules</span><h2>Six pairings we stand behind</h2></div>
    <p class="prose">You don&rsquo;t need an app to get these right. This is most of what we&rsquo;d tell you at the table anyway.</p>
    <div class="pair-grid">{% for dish, drink, why in pairing.classics %}
      <article class="pair-card">
        <h3>{{ dish }}</h3>
        <b class="pair-drink">{{ drink }}</b>
        <p>{{ why }}</p>
      </article>{% endfor %}
    </div>
  </div>
</section>

<section class="section section--dark on-dark">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">How it works</span><h2>Three steps, no account</h2></div>
    <ol class="pair-steps">{% for t, d in pairing.steps %}<li><b>{{ t }}</b><span>{{ d }}</span></li>{% endfor %}</ol>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap cta-foot">
    <h2>Found your drink?</h2>
    <p class="prose">Everything on the bar is better with something out of the oven next to it.</p>
    <div class="btn-row">
      <a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="pairing">{{ icons.bag|safe }}Order online</a>
      <a class="btn btn--line" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find a table</a>
      <a class="btn btn--line" href="{{ u('/monthly-specials/') }}">This month&rsquo;s specials</a>
    </div>
  </div>
</section>

<script src="{{ site.chat_src }}" data-widget-id="{{ pairing.widget_id }}" data-embed-mode="embedded" data-embed-target="embedded-widget-container" defer></script>
"""

T["lto"] = """
<section class="page-head on-dark lto-head">
  {{ img(lto.sections[2][1][0][2], lto.sections[2][1][0][0] ~ ' pizza at Square Peg Pizzeria', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Monthly specials</span></nav>
    <span class="eyebrow">{{ lto.month }} {{ lto.year }} &middot; limited time</span>
    <h1>{{ lto.month }}<br>specials</h1>
    <p class="lede">{{ lto.blurb }}</p>
    <div class="btn-row">
      <a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="lto">{{ icons.bag|safe }}Order online</a>
      <a class="btn btn--ghost" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find a table</a>
    </div>
  </div>
</section>

<div data-season-from="2000-01-01" data-season-to="{{ lto.ends }}" data-season-invert hidden>
  <section class="section section--paper">
    <div class="wrap lto-gone">
      <span class="eyebrow">Between menus</span>
      <h2>Next month&rsquo;s specials are on the way.</h2>
      <p class="prose">{{ lto.month }}&rsquo;s run has ended. The new menu lands in a few days &mdash; in the meantime, the full menu is very much open.</p>
      <div class="btn-row"><a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="lto-gone">{{ icons.bag|safe }}Order online</a><a class="btn btn--line" href="{{ u('/our-menu/') }}">See the full menu</a></div>
    </div>
  </section>
</div>

<div data-season-from="2000-01-01" data-season-to="{{ lto.ends }}" hidden>
{% for title, items in lto.sections %}
<section class="section {{ 'section--dark on-dark' if loop.index is odd else 'section--paper' }}">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">{{ lto.month }} only</span><h2>{{ title }}</h2></div>
    <div class="lto-grid{{ ' lto-grid--two' if items|length > 1 else '' }}">{% for name, price, pic, desc in items %}<article class="lto-item">
      <div class="lto-pic">{{ img(pic, name ~ ' at Square Peg Pizzeria', sizes='(min-width:900px) 50vw, 100vw')|safe }}</div>
      <div class="lto-body">
        <h3>{{ name }}</h3>
        <span class="lto-price">{{ price }}</span>
        <p>{{ desc }}</p>
      </div>
    </article>{% endfor %}</div>
  </div>
</section>
{% endfor %}

<section class="section section--dark on-dark">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">{{ lto.month }} only &middot; at the bar</span><h2>Cocktails</h2></div>
    <div class="lto-drinks">{% for name, price, desc in lto.cocktails %}<article class="lto-drink">
      <h3>{{ name }}</h3><span class="lto-price">{{ price }}</span><p>{{ desc }}</p>
    </article>{% endfor %}</div>
    <p class="note lto-note">Cocktails at locations with a full bar.</p>
  </div>
</section>

<section class="section lto-cta">
  <div class="wrap">
    <h2>Gone on the <em>{{ lto.ends[-2:]|int }}{{ 'st' if lto.ends[-2:]|int in [1,21,31] else 'nd' if lto.ends[-2:]|int in [2,22] else 'rd' if lto.ends[-2:]|int in [3,23] else 'th' }}</em>.</h2>
    <p>Ten Square Pegs across Connecticut and Delray Beach. Order it, or come sit down and have the whole thing.</p>
    <div class="btn-row">
      <a class="btn" href="{{ site.order_picker_toast }}" rel="noopener"{{ ext|safe }} data-track="order_click" data-src="lto-footer">{{ icons.bag|safe }}Order online</a>
      <a class="btn btn--line" href="{{ u('/locations/') }}">{{ icons.pin|safe }}Find your Square Peg</a>
    </div>
  </div>
</section>
</div>
"""

T["private_events"] = """{% macro bento(items) %}<div class="bento">{% for p, a, cap in items %}<figure class="{{ 'b-main' if loop.first else 'b-side' }}">{{ img(p, a, sizes=('(min-width:800px) 60vw, 100vw' if loop.first else '(min-width:800px) 36vw, 50vw'))|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endfor %}</div>{% endmacro %}
{% macro feature(p, a, cap) %}<figure class="feature-photo">{{ img(p, a, sizes='(min-width:960px) 540px, 100vw')|safe }}{% if cap %}<figcaption>{{ cap }}</figcaption>{% endif %}</figure>{% endmacro %}

<section class="page-head on-dark">
  {{ img('table-spread', 'A table full of Square Peg pizzas and appetizers', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Private Events & Classes</span></nav>
    <span class="eyebrow">Private events · Pizza-making classes</span>
    <h1>Plan your next event with us</h1>
    <p class="lede">From small gatherings to larger celebrations, we offer flexible options, great food and seamless service to make your event effortless and memorable.</p>
    <div class="btn-row"><a class="btn" href="{{ u('/large-party-reservations/') }}">Book now</a><a class="btn btn--ghost" href="#classes">Pizza-making classes</a></div>
  </div>
</section>
<section class="section section--paper">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Pick your kind of party</span>
      <h2>Four ways to celebrate</h2>
      <p>The one you want usually comes down to a single question: do you want to be
        somewhere else, or do you want us somewhere else? Ten or more at our tables is a
        large party. Food at your place is catering, which you collect. The truck is the
        only one where we turn up. And if the point of the night is raising money, a
        Tuesday fundraiser beats all three.</p>
    </div>
    <div class="tiles tiles--3">
      <a class="tile on-dark" href="{{ u('/large-party-reservations/') }}">{{ img('dining-room-kids', 'A group celebrating at Square Peg', sizes='(min-width:1000px) 33vw, 100vw')|safe }}<div class="tile-body"><span class="eyebrow">At the restaurant</span><h3>Large party reservations</h3><p>Birthdays, team dinners, showers and reunions.</p><span class="btn">Request a date {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/catering/') }}">{{ img('pizza-boxes', 'Stacked Square Peg pizza boxes', sizes='(min-width:1000px) 33vw, 100vw')|safe }}<div class="tile-body"><span class="eyebrow">At your place</span><h3>Catering</h3><p>Wood-fired pizza for any headcount, ready for pickup.</p><span class="btn">Get a quote {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/food-truck/') }}">{{ img('truck-tent', 'The Square Peg food truck at an event', sizes='(min-width:1000px) 33vw, 100vw')|safe }}<div class="tile-body"><span class="eyebrow">Anywhere</span><h3>The food truck</h3><p>A wood-fired oven on wheels at your event.</p><span class="btn">Book the truck {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/fundraisers/') }}">{{ img('team-kids', 'A youth team at a Square Peg Tuesday fundraiser', sizes='(min-width:1000px) 33vw, 100vw')|safe }}<div class="tile-body"><span class="eyebrow">For your cause</span><h3>Tuesday fundraisers</h3><p>20% of dine-in food sales back to your school, team or cause.</p><span class="btn">Pick a Tuesday {{ icons.arrow|safe }}</span></div></a>
    </div>
  </div>
</section>
<section class="section" id="classes">
  <div class="wrap two-col" style="align-items:center">
    {{ feature('dough', 'A ball of fresh pizza dough ready to stretch', 'Everyone’s a chef here') }}
    <div class="stack">
      <span class="eyebrow">Monthly · adults & kids</span>
      <h2>Pizza-making classes</h2>
      <p class="prose">Square Peg believes everyone is a chef, and we want to bring your inner chef to life. Every month we host adult pizza-making classes, plus <strong>free</strong> kids’ pizza-making classes.</p>
      <ul class="checks"><li>Stretch, top and fire your own pie</li><li>Adult classes every month</li><li>Free classes for kids</li></ul>
      <div class="btn-row"><a class="btn" href="{{ site.events_calendar_url or u('/entertainment/') }}"{% if site.events_calendar_url %} target="_blank" rel="noopener" data-track="classes_click" data-src="private-events"{% endif %}>See dates & get tickets</a>{% if site.instagram %}<a class="btn btn--line" href="{{ site.instagram }}" rel="noopener"{{ ext|safe }}>Follow on Instagram</a>{% endif %}</div>
    </div>
  </div>
</section>
"""

T["careers"] = """
<section class="page-head on-dark">
  {{ img('oven-fire', 'The fire inside a Square Peg wood-fired oven', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Careers</span></nav>
    <span class="eyebrow">Now hiring at every location</span>
    <h1>Join the Square Peg crew</h1>
    <p class="lede">We hire for attitude and instinct, and we’ll teach you the rest. Managers, servers, bartenders, kitchen and pizza cooks: start anywhere, grow everywhere.</p>
    <div class="btn-row"><a class="btn" href="#apply">See open roles</a></div>
  </div>
</section>
<section class="section section--paper" id="apply">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Pick your location & position when you apply</span><h2>Open positions</h2></div>
    <div class="careers-embed"><iframe id="wingman-careers" src="{{ site.careers_embed_src }}" title="Careers at Square Peg Pizzeria: we're hiring" loading="lazy"></iframe></div>
    <p class="note" style="margin-top:14px">Trouble loading? <a href="{{ site.careers_external }}" rel="noopener" target="_blank">Open the careers page</a>.</p>
  </div>
</section>
"""

T["simple"] = """
<section class="page-head on-dark"><div class="wrap"><span class="eyebrow">{{ eyebrow }}</span><h1>{{ h1 }}</h1><p class="lede">{{ lede }}</p>
<div class="btn-row"><a class="btn" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.bag|safe }}Order now</a><a class="btn btn--ghost" href="{{ u('/') }}">Back to home</a></div></div></section>
{% if prose %}<section class="section"><div class="wrap prose">{{ prose|safe }}</div></section>{% endif %}
"""

env = Environment(loader=DictLoader(T), autoescape=select_autoescape(default_for_string=True, default=True))

# ---------------------------------------------------------------- build
PASTA_NAMES = [n for n, _ in dict((k, v) for _, k, v in MENU["sections"])["pasta"]]

def halloween():
    """Halloween week with the dates the page gates itself on: the day before it
    starts, and the day after it ends."""
    hw = dict(HALLOWEEN)
    a = date.fromisoformat(hw["starts"])
    b = date.fromisoformat(hw["ends"])
    hw["eve"] = (a - timedelta(days=1)).isoformat()
    hw["after"] = (b + timedelta(days=1)).isoformat()
    hw["starts_long"] = f"{a.strftime('%A')}, {a.strftime('%B')} {a.day}"
    return hw


def hh_group(head, blurb, items):
    """One happy hour group: heading, optional blurb, then name / price / detail rows."""
    rows = []
    for name, price, detail, tag in items:
        badge = f'<span class="hh-badge">{escape(tag)}</span>' if tag else ""
        rows.append(
            f'<li class="hh-item"><div class="hh-line"><span class="hh-name">{escape(name)}{badge}</span>'
            f'<span class="hh-dot" aria-hidden="true"></span>'
            f'<span class="hh-price">{escape(price)}</span></div>'
            f'<p class="hh-desc">{escape(detail)}</p></li>')
    lede = f'<p class="hh-blurb">{escape(blurb)}</p>' if blurb else ""
    return (f'<div class="hh-group"><h4>{escape(head)}</h4>{lede}'
            f'<ul class="hh-list">{"".join(rows)}</ul></div>')


def happy_hour(l):
    """Happy hour for one location, or None. Adds the display + gating dates for
    the "starts <date>" flag, which hides itself the day the menu goes live."""
    hh = HAPPY_HOUR.get(l["slug"])
    if not hh:
        return None
    hh = dict(hh)
    if hh.get("starts"):
        d = date.fromisoformat(hh["starts"])
        hh["starts_long"] = f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}"
        hh["starts_eve"] = (d - timedelta(days=1)).isoformat()
    return hh


LUNCH_END = "14:00"   # the $10 lunch runs until 2pm


def lunch_windows():
    """Which locations can actually serve the $10 lunch, worked out from their own
    opening times rather than typed by hand, so changing hours updates the list.

    A store qualifies on a weekday when it opens before 2pm; the window starts at
    11am or at opening, whichever is later."""
    def mins(t):
        hh, mm = map(int, t.split(":"))
        return hh * 60 + mm

    out = []
    for l in LOCATIONS:
        days = []
        for d in DAYS[:5]:
            v = l["hours"].get(d)
            if v and mins(v[0]) < mins(LUNCH_END):
                days.append((d, v[0] if mins(v[0]) > mins("11:00") else "11:00"))
        if not days:
            continue
        # "Mon-Fri" when it is every weekday, otherwise name the days
        names = [d for d, _ in days]
        if names == DAYS[:5]:
            when = "Monday\u2013Friday"
        elif len(names) == 1:
            when = DAY_NAMES[names[0]] + " only"
        elif names == DAYS[:5][DAYS[:5].index(names[0]):]:
            when = f"{DAY_NAMES[names[0]]}\u2013Friday"
        else:
            when = ", ".join(DAY_NAMES[d] for d in names)
        # Lead with the latest opening so nobody turns up to a locked door, then
        # name the days that open earlier.
        by_start = {}
        for d, st in days:
            by_start.setdefault(st, []).append(d)
        starts = sorted(by_start, key=mins)
        frm = f"from {fmt_time(starts[-1])}"
        for st in starts[:-1]:
            ds = ", ".join(DAY_NAMES[d] for d in by_start[st])
            frm += f" ({fmt_time(st)} {ds})"
        out.append({"name": l.get("short") or l["name"], "slug": l["slug"],
                    "when": when, "from": frm,
                    "all_week": names == DAYS[:5]})
    return out


def loc_menu(l):
    pastas = l.get("pastas") or PASTA_NAMES
    words = [("eggplant parm" if p == "The Bella Parmigiana" else p.lower()) for p in pastas]
    kids, salads = l.get("kids_menu", True), l.get("salads", True)
    parm = l.get("parm_line", "chicken and meatball parm sandwiches")
    wood = l.get("wood", True)
    rest = [parm] + (["salads"] if salads else []) + [("wood-fired wings" if wood else "wings")] + (["a kids’ menu"] if kids else [])
    return {"pastas": pastas, "words": words, "extra": l.get("menu_extra", []), "detroit": l.get("detroit", True), "bar": l.get("bar", True),
            "kids": kids, "rest": rest, "parm": parm, "wood": wood}

def join_and(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]

def location_faqs(l):
    name = (l.get("short") or l["name"])
    lines = "; ".join(hours_summary(l))
    return [
        (f"What are Square Peg {name}’s hours?", f"{lines}. " + ("Holiday hours are posted on this page as soon as they change." if l.get("hours_source") == "google" else "Holiday hours may vary; online ordering always shows live availability.")),
        (f"Is Square Peg {name} an Italian restaurant?",
         f"Yes. Along with {'wood-fired ' if l.get('wood', True) else ''}pizza, Square Peg {name} serves Italian-American favorites like {join_and(loc_menu(l)['words'][:4])}, plus {join_and([r for r in loc_menu(l)['rest'] if 'kids' not in r] + ['desserts'])}."),
    ] + ([
        (f"Is Square Peg {name} a good restaurant for families?",
         f"Yes. There’s a kids’ menu (pasta, spaghetti and meatballs, chicken fingers, mac and cheese), room for big groups, and large party reservations for birthdays and team dinners."),
    ] if loc_menu(l)["kids"] else []) + ([
        (f"Does Square Peg {name} serve beer, wine and cocktails?",
         f"Yes. Square Peg {name} serves beer, wine and cocktails with dine-in meals, so it works for date nights, game nights and dinner with friends."),
    ] if loc_menu(l)["bar"] else []) + [
        (f"Can I order online from Square Peg {name}?", f"Yes. Tap “Order {name} online” to order for pickup, or choose delivery at checkout where it’s available."),
        ("Do you have gluten-free or vegan options?", "Yes. We offer a 12″ gluten-free crust, and vegan cheese can be added to any pizza."),
        (f"Does Square Peg {name} do catering?", f"Yes. {name} caters birthdays, office lunches, team events and more. Send a quick request on our catering page, or call {l['phone']}."),
        (f"Is Square Peg {name} close to {l['nearby'][0]} and {l['nearby'][1]}?", f"Yes. Square Peg {name} at {l['street']} in {l['city']} is a short drive from {', '.join(l['nearby'][:-1])} and {l['nearby'][-1]}. Order ahead online for pickup, or check delivery availability at checkout."),
        ("Can our group host a fundraiser here?", "Yes. Every Tuesday from 4pm to close, one organization earns 20% of dine-in food sales from its supporters."),
    ]

PRIVACY_TEXT = """<p class="note">Last updated: April 13, 2026</p>
<h2>Who we are</h2>
<p>Square Peg Pizzeria operates restaurants, catering, and food truck services across Connecticut and Florida. This Privacy Policy explains how we collect, use, and protect your personal information when you interact with our website, contact forms, rewards program, or SMS messaging service.</p>
<h2>What information we collect</h2>
<p>We may collect the following personal information:</p>
<ul><li>Name</li><li>Email address</li><li>Phone number</li><li>Location preference (which restaurant location you are associated with)</li><li>Messages or inquiries you submit through our contact form</li><li>Order and transaction history when you order through our platform</li></ul>
<h2>How we use your information</h2>
<p>We use your personal information to:</p>
<ul><li>Respond to your inquiries and customer service requests</li><li>Process online orders and catering bookings</li><li>Administer our loyalty and rewards program</li><li>Send you SMS messages you have explicitly opted into, including promotions, event announcements, order confirmations, and loyalty rewards updates</li><li>Send you email communications you have opted into</li><li>Improve our services and website experience</li></ul>
<h2>SMS messaging</h2>
<p>If you opt into our SMS program, the following terms apply:</p>
<ul><li><strong>Program:</strong> Square Peg Pizzeria SMS Alerts</li><li><strong>Message Type:</strong> Promotions &amp; deals, event announcements, order confirmations, loyalty &amp; rewards updates</li><li><strong>Frequency:</strong> Message frequency varies. You may receive up to 8 messages per month.</li><li><strong>Rates:</strong> Message and data rates may apply. Check with your mobile carrier.</li><li><strong>Opt-Out:</strong> Reply STOP, CANCEL, END, QUIT, or UNSUBSCRIBE at any time to opt out. You will receive one final confirmation message and no further messages.</li><li><strong>Help:</strong> Reply HELP for assistance, or contact us at <a href="mailto:info@squarepegpizzeria.com">info@squarepegpizzeria.com</a> or (860) 286-0415.</li></ul>
<h2>Data sharing</h2>
<p>We do not sell your personal information to third parties.</p>
<p>No mobile information will be shared with third parties or affiliates for marketing or promotional purposes.</p>
<p>SMS opt-in data and consent will not be shared with any third party under any circumstances.</p>
<p>We may share your information with service providers who assist us in operating our website and fulfilling orders, solely for that purpose and under strict confidentiality obligations.</p>
<h2>Data retention</h2>
<p>We retain your personal information for as long as necessary to provide our services and comply with legal obligations. You may request deletion of your data at any time.</p>
<h2>Your rights</h2>
<p>You have the right to:</p>
<ul><li>Access the personal information we hold about you</li><li>Request correction of inaccurate information</li><li>Request deletion of your personal information</li><li>Opt out of SMS messages at any time by replying STOP</li><li>Opt out of marketing emails by clicking the unsubscribe link in any email</li></ul>
<h2>How to contact us</h2>
<p>To exercise any of your rights, or if you have questions about this Privacy Policy, contact us at:</p>
<p><strong>Business:</strong> Square Peg Pizzeria<br><strong>Email:</strong> <a href="mailto:info@squarepegpizzeria.com">info@squarepegpizzeria.com</a><br><strong>Phone:</strong> (860) 286-0415<br><strong>Website:</strong> <a href="https://squarepegpizzeria.com">https://squarepegpizzeria.com</a></p>
<h2>Changes to this policy</h2>
<p>We may update this Privacy Policy from time to time. The date at the top of this page reflects the most recent revision. Continued use of our services after any update constitutes your acceptance of the revised policy.</p>"""
TERMS_TEXT = """<p class="note">Last updated: April 13, 2026</p>
<p>These Terms &amp; Conditions govern your use of the Square Peg Pizzeria website and SMS messaging program. By using our website or opting into our SMS program, you agree to these terms.</p>
<h2>SMS messaging program</h2>
<h3>Enrollment</h3>
<p>By providing your phone number and checking the opt-in box on any of our forms, you consent to receive recurring automated text messages from Square Peg Pizzeria. Your consent is not a condition of any purchase.</p>
<h3>Message types</h3>
<p>Messages may include: promotional offers and deals, event and entertainment announcements, order confirmations and updates, loyalty and rewards program notifications.</p>
<h3>Message frequency</h3>
<p>Message frequency varies. You may receive up to 8 messages per month.</p>
<h3>Charges</h3>
<p>Message and data rates may apply. Square Peg Pizzeria does not charge for SMS messages, but your mobile carrier’s standard messaging rates may apply.</p>
<h3>How to opt out</h3>
<p>Reply STOP, CANCEL, END, QUIT, or UNSUBSCRIBE at any time to opt out of all future messages. You will receive one confirmation message and will receive no further messages from this program.</p>
<h3>How to get help</h3>
<p>Reply HELP to any message. You may also contact us at <a href="mailto:info@squarepegpizzeria.com">info@squarepegpizzeria.com</a> or call us at (860) 286-0415.</p>
<h3>Supported carriers</h3>
<p>Service is available on all major US carriers including AT&amp;T, Verizon, T-Mobile, Sprint, Boost, Cricket, MetroPCS, US Cellular, and others. Carrier support may vary.</p>
<h2>Website use</h2>
<p>The Square Peg Pizzeria website is provided for informational and ordering purposes. We reserve the right to update or modify the website and its content at any time without notice.</p>
<h2>Intellectual property</h2>
<p>All content on this website, including text, images, logos, and graphics, is the property of Square Peg Pizzeria and may not be reproduced without written permission.</p>
<h2>Limitation of liability</h2>
<p>Square Peg Pizzeria is not liable for any indirect, incidental, or consequential damages arising from your use of our website or SMS program.</p>
<h2>Changes to these terms</h2>
<p>We may update these Terms &amp; Conditions at any time. The date at the top of this page reflects the most recent update. Continued use of our website or SMS program constitutes acceptance of any updated terms.</p>
<h2>Contact us</h2>
<p>Questions about these terms? Contact us at <a href="mailto:info@squarepegpizzeria.com">info@squarepegpizzeria.com</a> or (860) 286-0415.</p>
<p><strong>Business:</strong> Square Peg Pizzeria<br><strong>Website:</strong> <a href="https://squarepegpizzeria.com">https://squarepegpizzeria.com</a><br><strong>Email:</strong> <a href="mailto:info@squarepegpizzeria.com">info@squarepegpizzeria.com</a><br><strong>Phone:</strong> (860) 286-0415</p>"""

def main():
    if PREV.exists():
        shutil.rmtree(PREV)
    if OUT.exists():
        if REUSE:
            OUT.rename(PREV)
        else:
            shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    g = apply_google_hours()
    print("  toast: " + (f"order/menu links -> {TOAST_SUBDOMAIN} (launch mode)" if TOAST_ON_SUBDOMAIN
                         else f"order/menu links -> {TOAST_MAIN_DOMAIN} (pre-launch). Set TOAST_ON_SUBDOMAIN = True in data/content.py on launch day."))
    apply_service_areas()
    global TOWN_COUNT
    TOWN_COUNT = sum(len(rows) for _, rows in town_directory())
    print(f"  hours: {g} of {len(LOCATIONS)} locations from Google" if g else "  hours: from data/content.py")
    build_images()
    logo_ratio = build_brand()
    LOGO_RATIO[0] = logo_ratio
    css = (ROOT / "src" / "site.css").read_text()
    if not PREVIEW:
        faces = [("Big Shoulders Display", "big-shoulders-display", w) for w in (800, 900)] + [("Figtree", "figtree", w) for w in (400, 600, 700, 800)]
        css = "".join(f'@font-face{{font-family:"{f}";font-style:normal;font-weight:{w};font-display:swap;src:url(/fonts/{slug}-latin-{w}-normal.woff2) format("woff2")}}' for f, slug, w in faces) + css
        shutil.copytree(ROOT / "src" / "fonts", OUT / "fonts")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s*\n\s*", "", css)
    js = (ROOT / "src" / "site.js").read_text()
    jsv = hashlib.md5(js.encode()).hexdigest()[:8]

    for l in LOCATIONS:
        l["summary"] = hours_summary(l)
        l.setdefault("short", None)
    locs_json = json.dumps([{
        "slug": l["slug"], "name": l["name"], "short": l.get("short") or l["name"], "street": l["street"], "city": l["city"], "state": l["state"],
        "phone": l["phone"], "tel": tel(l["phone"]), "order": order_url(l), "url": url(f"/locations/{l['slug']}/"),
        "lat": l["lat"], "lng": l["lng"], "hours": l["hours"], "special": l.get("special") or {}, "region": l["region"]} for l in LOCATIONS], separators=(",", ":"))
    cfg_json = json.dumps({"chatSrc": "" if PREVIEW else SITE["chat_src"], "chatId": SITE["chat_widget_id"], "locationsUrl": url("/locations/"),
                           "supabaseUrl": SITE.get("supabase_url", ""), "supabaseKey": SITE.get("supabase_anon_key", ""), "thanksUrl": url("/thanks/"),
                           "contactEndpoint": "" if PREVIEW else SITE.get("contact_endpoint", "")})

    # gtag.js is about a megabyte of JavaScript and costs roughly a second of
    # main-thread time on a mid-range phone — it was the whole gap between the
    # desktop and mobile PageSpeed scores. The stub and the dataLayer queue stay
    # inline, so gtag() calls from site.js are recorded from the first paint; only
    # the download waits, for the first sign of a real visitor or TAG_DELAY,
    # whichever comes first. gtag.js replays the queue when it lands, so nothing
    # queued is lost — only a visitor who leaves within TAG_DELAY without
    # touching the page goes uncounted.
    analytics = ""
    tags = []
    if SITE["ga4_id"]:
        analytics += ('<script>window.dataLayer=window.dataLayer||[];'
                      'function gtag(){dataLayer.push(arguments)}'
                      'gtag("js",new Date());'
                      f'gtag("config","{SITE["ga4_id"]}");</script>')
        tags.append(f'https://www.googletagmanager.com/gtag/js?id={SITE["ga4_id"]}')
    if SITE["meta_pixel_id"]:
        analytics += ("<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};"
                      "if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[]}(window,document,'script');"
                      f"fbq('init','{SITE['meta_pixel_id']}');fbq('track','PageView');</script>")
        tags.append("https://connect.facebook.net/en_US/fbevents.js")
    if tags:
        analytics += ("<script>(function(){var T=" + json.dumps(tags) + ",d=0,"
                      "E=['pointerdown','keydown','touchstart','scroll','mousemove'];"
                      "function go(){if(d)return;d=1;clearTimeout(t);"
                      "E.forEach(function(e){removeEventListener(e,go)});"
                      "T.forEach(function(u){var s=document.createElement('script');"
                      "s.async=!0;s.src=u;document.head.appendChild(s)})}"
                      f"var t=setTimeout(go,{TAG_DELAY});"
                      "E.forEach(function(e){addEventListener(e,go,{passive:!0})});"
                      "})();</script>")

    base_ctx = dict(
        u=url, tel=tel, order=order_url, hero_picture=hero_picture, drawer_extra=DRAWER_EXTRA, drawer_groups=DRAWER_GROUPS, more=MORE, review=review_url, gd=GAME_DAY, gd_locs=[l for l in LOCATIONS if l.get('bar', True)], st_locs=[l for l in LOCATIONS if l.get('sunday_ticket')], ent=ENTERTAINMENT, ent_from=ent_from, ent_dates_all={l['slug']: ent_dated(l) for l in LOCATIONS if ENT_DATES.get(l['slug'])}, events_all=sorted(([dict(e, loc=l) for l in LOCATIONS for e in location_events(l)]), key=lambda e: e['date']), events_by_slug={l['slug']: location_events(l) for l in LOCATIONS if EVENTS.get(l['slug'])}, ent_slugs=[l['slug'] for l in LOCATIONS if ENTERTAINMENT.get(l['slug']) or ENT_DATES.get(l['slug']) or EVENTS.get(l['slug'])],  ent_count=["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"][len(ENTERTAINMENT)], day_names=DAY_NAMES, promos=PROMOS, loc_by_slug={l["slug"]: l for l in LOCATIONS}, embeds=EMBEDS, contact_topics=CONTACT_TOPICS, maps=maps_url, embed=maps_embed, img=img, icons=ICONS, nav=NAV,
        site=dict(SITE, toast_account=TOAST_HOST + SITE["toast_account_path"]), locs=LOCATIONS, regions=REGIONS, more_groups=MORE_GROUPS, deal=DEAL, deals=DEALS, pairing=PAIRING, links_rows=LINKS, calc=CALC, faq_groups=PIZZA_FAQ, trivia=PIZZA_TRIVIA, quiz=QUIZ, datenight=DATE_NIGHT, points=POINTS, perks=APP_PERKS,
        sigs=SIGNATURES, reviews=REVIEWS, preview=PREVIEW, logo_img=logo_img, css=css, jsv=jsv, locs_json=locs_json, cfg_json=cfg_json,
        year=date.today().year, analytics=analytics, ent_json=json.dumps({l["slug"]: {"name": l.get("short") or l["name"], "url": url(f"/locations/{l['slug']}/"), "events": ENTERTAINMENT.get(l["slug"], []), "dates": ENT_DATES.get(l["slug"], [])} for l in LOCATIONS if ENTERTAINMENT.get(l["slug"]) or ENT_DATES.get(l["slug"])}, separators=(",", ":")), logo_ratio=logo_ratio, imgbase="img/" if PREVIEW else "/img/",
        ext=' target="_blank"' if PREVIEW else "", staging=STAGING, band=band, town_count=TOWN_COUNT, pasta_items=dict((k, v) for _, k, v in MENU["sections"])["pasta"], join_and=join_and, hh_group=hh_group, hwart=HW_ART, lunch_where=lunch_windows(),
        event_types=["Catering pickup", "Food truck", "Party at the restaurant", "Corporate / office", "School or team event", "Wedding or large event"],
    )

    pages = []  # (path, title, desc, body_template, extra ctx, schema, og, hero)

    pages.append(("/", "Square Peg Pizzeria | Italian Restaurant & Wood-Fired Pizza",
                  "Wood-fired pizza, pasta and Italian-American favorites at 10 Square Peg restaurants in CT and Delray Beach, FL. Order pickup, delivery or catering.",
                  "home", {}, org_schema(), "margherita-board", None))
    pages.append(("/locations/", "Italian Restaurants & Pizza Near You | Square Peg Pizzeria",
                  "Square Peg Pizzeria restaurants in Glastonbury, East Hartford, Vernon, Bolton, Storrs, Preston, Plainville, Berlin, Shelton, CT and Delray Beach, FL.",
                  "locations", {}, graph(breadcrumbs([("Home", "/"), ("Locations", "/locations/")]),
                  {"@type": "ItemList", "name": "Square Peg Pizzeria locations", "itemListElement": [
                      {"@type": "ListItem", "position": i + 1, "url": abs_url(f"/locations/{l['slug']}/"), "name": f"Square Peg Pizzeria {l.get('short') or l['name']}"} for i, l in enumerate(LOCATIONS)]}), "margherita-board", None))

    for l in LOCATIONS:
        name = l.get("short") or l["name"]
        others = sorted([o for o in LOCATIONS if o is not l], key=lambda o: (o["lat"] - l["lat"]) ** 2 + (o["lng"] - l["lng"]) ** 2)[:3]
        faqs = location_faqs(l)
        schema = graph(restaurant_schema(l), breadcrumbs([("Home", "/"), ("Locations", "/locations/"), (l["name"], f"/locations/{l['slug']}/")]), faq_schema(faqs))
        title = f"Italian Restaurant & Pizza in {l['city']}, {l['state']} | Square Peg"
        oven = "wood-fired " if l.get("wood", True) else ""
        desc = f"Italian restaurant and {oven}pizza at {l['street']}, {l['city']}, {l['state']}: pasta, chicken parm, wings and kids' meals. Hours, {l['phone']}, order online."
        pages.append((f"/locations/{l['slug']}/", title, desc, "location",
                      dict(l=l, lm=loc_menu(l), hh=happy_hour(l), rows=hours_rows(l), specials=special_rows(l), near=others, faqs=faqs, events=location_events(l), ent_dates=ent_dated(l),
                           local_page=next((t for t in TOWN_PAGES if t["store"] == l["slug"]), None)), schema, l["photo"], l["photo"]))

    menu_schema = {"@type": "Menu", "@id": abs_url("/our-menu/#menu"), "name": "Square Peg Pizzeria menu", "url": abs_url("/our-menu/"),
                   "inLanguage": "en", "hasMenuSection": [
                       {"@type": "MenuSection", "name": "Wood-fired pizza", "hasMenuItem": [{"@type": "MenuItem", "name": n, "description": d} for n, d, _ in SIGNATURES]}] + [
                       {"@type": "MenuSection", "name": t, "hasMenuItem": [{"@type": "MenuItem", "name": n, "description": d} for n, d in items]} for t, _, items in MENU["sections"]]}
    pages.append(("/our-menu/", "Menu: Pasta, Chicken Parm & Wood-Fired Pizza | Square Peg",
                  "The Square Peg Pizzeria menu: wood-fired and Detroit-style pizza, pasta alla vodka, chicken parmesan, Italian subs, wings, kids' meals, beer, wine and cocktails.",
                  "our_menu", dict(menu=MENU), graph(menu_schema, breadcrumbs([("Home", "/"), ("Menu", "/our-menu/")])), "table-spread", "table-spread"))
    dir_towns = town_directory()
    pages.append(("/areas-we-serve/", "Towns We Serve in CT, RI & South FL | Square Peg Pizzeria",
                  f"Find the closest Square Peg Pizzeria to your town. {TOWN_COUNT} towns in Connecticut, Rhode Island and South Florida are within 15 miles of one of our kitchens.",
                  "areas", dict(towns=dir_towns), graph(breadcrumbs([("Home", "/"), ("Locations", "/locations/"), ("Towns we serve", "/areas-we-serve/")])), "oven-pizza", None))
    pages.append(("/catering/", "Pizza Catering in Connecticut | Square Peg Pizzeria",
                  "Wood-fired pizza catering for parties, offices, schools and events from all 10 Square Peg Pizzeria locations. Get a quote in 60 seconds.",
                  "catering", dict(faqs=CATERING_FAQ, cat=CATERING), graph(faq_schema(CATERING_FAQ), breadcrumbs([("Home", "/"), ("Catering", "/catering/")])), "table-spread", "table-spread"))
    pages.append(("/large-party-reservations/", "Large Party & Group Reservations | Square Peg Pizzeria",
                  "Reserve for a big group at any Square Peg Pizzeria in CT or Delray Beach, FL. Birthdays, team dinners, showers and reunions with wood-fired pizza.",
                  "parties", dict(faqs=LARGE_PARTY_FAQ, routes=EVENT_ROUTES), graph(faq_schema(LARGE_PARTY_FAQ), breadcrumbs([("Home", "/"), ("Large Parties", "/large-party-reservations/")])), "friends-holiday", "friends-holiday"))
    pages.append(("/contact/", "Contact Us | Square Peg Pizzeria",
                  "Contact Square Peg Pizzeria: phone numbers for all 10 locations, email, and a message form for catering, large parties, gift cards, jobs and more.",
                  "contact", {}, graph({"@type": "ContactPage", "url": abs_url("/contact/"), "name": "Contact Square Peg Pizzeria",
                                        "about": {"@id": ORG_ID}},
                                       {"@type": "Organization", "@id": ORG_ID, "name": SITE["name"], "email": SITE["email"],
                                        "contactPoint": [{"@type": "ContactPoint", "contactType": "customer service", "email": SITE["email"], "areaServed": ["US-CT", "US-FL"], "availableLanguage": "en"}]},
                                       breadcrumbs([("Home", "/"), ("Contact", "/contact/")])), None, None))
    pages.append(("/promotions/", "Pizza Specials, $10 Lunch & App Rewards | Square Peg Pizzeria",
                  "Square Peg Pizzeria specials: Tuesday pasta night, $1 wings Wednesday, half-price wine Friday, $10 weekday lunch, app rewards, punch cards and 15% off for heroes.",
                  "promotions", {}, graph(breadcrumbs([("Home", "/"), ("Specials", "/promotions/")])), "oven-pizza", "oven-pizza"))
    pages.append(("/game-day/", "Game Day Specials | Square Peg Pizzeria",
                  "Football season at Square Peg: $4 Green Tea shots, $7 game day cocktails, $4 Miller Lite and two game day pizzas at nine Connecticut and Florida locations.",
                  "game_day", {}, graph(breadcrumbs([("Home", "/"), ("Specials", "/promotions/"), ("Game Day", "/game-day/")])), "oven-fire", "oven-fire"))
    pages.append(("/entertainment/", "Trivia, Bingo & DJ Nights | Square Peg Pizzeria",
                  "Weekly trivia, bingo and DJ nights at Square Peg Pizzeria in Plainville, Shelton, East Hartford, Glastonbury, Preston, Storrs and Delray Beach.",
                  "entertainment", {}, graph(breadcrumbs([("Home", "/"), ("Entertainment", "/entertainment/")])), "friends-holiday", "friends-holiday"))
    pages.append(("/private-events/", "Private Events & Pizza-Making Classes | Square Peg Pizzeria",
                  "Plan a private event at Square Peg Pizzeria, and join our monthly pizza-making classes for adults plus free kids' classes. Parties, catering and the food truck.",
                  "private_events", dict(routes=EVENT_ROUTES), graph(breadcrumbs([("Home", "/"), ("Private Events & Classes", "/private-events/")])), "table-spread", "table-spread"))
    pages.append(("/careers/", "Careers: Now Hiring | Square Peg Pizzeria",
                  "Join the Square Peg Pizzeria crew. Now hiring managers, servers, bartenders, kitchen staff and pizza cooks at locations across Connecticut and Delray Beach, FL.",
                  "careers", {}, graph(breadcrumbs([("Home", "/"), ("Careers", "/careers/")])), "oven-fire", "oven-fire"))
    # The local pages. Each one is hand-written in data/town_pages.py and only
    # exists because it says something its location page can't — Husky Bucks,
    # the casinos, the Boca drive. Never generate these per town.
    for tp in TOWN_PAGES:
        store = next(l for l in LOCATIONS if l["slug"] == tp["store"])
        pages.append((f"/{tp['slug']}/", tp["title"], tp["desc"], "townpage",
                      dict(tp=tp, store=store),
                      graph(faq_schema([(re.sub(r"<[^>]+>", "", q), re.sub(r"<[^>]+>", "", a))
                                        for q, a in tp["faq"]]),
                            breadcrumbs([("Home", "/"), ("Locations", "/locations/"),
                                         (tp["h1"], f"/{tp['slug']}/")])),
                      tp["hero"], tp["hero"]))
    pages.append(("/fundraiser-night/", "Fundraiser Night at Square Peg | How It Works for Guests",
                  "Supporting a school, team or nonprofit at Square Peg Pizzeria? Dine in on "
                  "their Tuesday, mention the group, and 20% of food sales goes back to them.",
                  "fundraiser_night", dict(fn=FUNDRAISER_NIGHT),
                  graph(faq_schema(FUNDRAISER_NIGHT["faq"]),
                        breadcrumbs([("Home", "/"), ("Fundraisers", "/fundraisers/"),
                                     ("Fundraiser night", "/fundraiser-night/")])),
                  "team-kids", "team-kids"))
    pages.append(("/food-truck/", "Wood-Fired Pizza Food Truck for Events in CT | Square Peg",
                  "Book the Square Peg Pizzeria wood-fired pizza food truck for backyard parties, weddings, schools, breweries and corporate events in Connecticut.",
                  "truck", dict(truck=TRUCK, faqs=TRUCK_FAQ), graph(faq_schema(TRUCK_FAQ), breadcrumbs([("Home", "/"), ("Food Truck", "/food-truck/")])), "food-truck", "food-truck"))
    pages.append(("/deals/", "Pizza Deals & Rewards | Square Peg Pizzeria",
                  "Square Peg Pizzeria deals and rewards: a members-only dine-in offer every month, points on every visit, and rewards you redeem in the app. Joining is free.",
                  "deals", {}, graph(breadcrumbs([("Home", "/"), ("Deals & Rewards", "/deals/")])), "pizza-boxes", "pizza-boxes"))
    pages.append(("/fundraisers/", "Tuesday Night Restaurant Fundraisers | Square Peg Pizzeria",
                  "Earn 20% of dine-in food sales for your school, team or nonprofit with a Square Peg Pizzeria Tuesday Night Fundraiser. Request your date.",
                  "fundraisers", dict(faqs=FUNDRAISER_FAQ), graph(faq_schema(FUNDRAISER_FAQ), breadcrumbs([("Home", "/"), ("Fundraisers", "/fundraisers/")])), "team-kids", "dining-room-kids"))
    pages.append(("/about/", "Our Story | Square Peg Pizzeria",
                  "Square Peg Pizzeria was started by UConn alumni in Glastonbury in 2020. Dough made fresh from scratch, never frozen, and a whole lot of Be Nice.",
                  "about", {}, graph(breadcrumbs([("Home", "/"), ("Our Story", "/about/")])), "dough", "dough"))
    hw = halloween()
    pages.append(("/halloween/",
                  f"{hw['name']}: Halloween at Square Peg Pizzeria",
                  f"{hw['when']}. Come in costume, {hw['kids']['price']} kids meals all week, and a "
                  f"costume contest at every Square Peg — best costume wins a {hw['prize']}.",
                  "halloween", dict(hw=hw),
                  graph(breadcrumbs([("Home", "/"), (hw["name"], "/halloween/")]),
                        {"@type": "Event", "name": f"{hw['name']} at Square Peg Pizzeria",
                         "startDate": hw["starts"], "endDate": hw["ends"],
                         "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                         "eventStatus": "https://schema.org/EventScheduled",
                         "description": hw["lede"],
                         "image": img_url("sp-three-pies", 1200),
                         "location": [{"@type": "Restaurant", "name": f"Square Peg Pizzeria {l['name']}",
                                       "address": {"@type": "PostalAddress", "streetAddress": l["street"],
                                                   "addressLocality": l["city"], "addressRegion": l["state"],
                                                   "postalCode": l["zip"], "addressCountry": "US"}}
                                      for l in LOCATIONS],
                         "organizer": {"@type": "Organization", "name": "Square Peg Pizzeria",
                                       "url": abs_url("/")}}),
                  "sp-three-pies", "oven-fire"))

    pages.append(("/roll-the-dice/", "Roll the Dice: Win Free Pizza at Lunch | Square Peg Pizzeria",
                  "Order any appetizer Monday–Thursday before 4pm at Square Peg Pizzeria, roll two dice, and win a free small cheese pizza or a $20 gift card.",
                  "dice", dict(dice=DICE), graph(breadcrumbs([("Home", "/"), ("Roll the Dice", "/roll-the-dice/")])), "table-spread", "table-spread"))
    pages.append(("/what-you-did/", "Square Peg Rewards: $5 Welcome Reward | Square Peg Pizzeria",
                  "Join Square Peg Rewards free and get a $5 welcome reward, points on every visit and members-only deals at all ten Square Peg Pizzeria locations.",
                  "caught", dict(shots=CAUGHT_SHOTS, app_perks=APP_PERKS, points=POINTS),
                  graph(breadcrumbs([("Home", "/"), ("Square Peg Rewards", "/what-you-did/")])), "sp-hero-board", "sp-hero-board"))
    _m = dict((k, v) for _, k, v in MENU["sections"])
    evidence_menu = [("Pasta", _m["pasta"][:4]), ("Parm & subs", _m["sandwiches"][:4]), ("Starters & wings", _m["starters"][:4])]
    pages.append(("/evidence/", "Order Square Peg Pizzeria | Wood-Fired Pizza, Pasta & Subs",
                  "Wood-fired pizza, pasta, parm subs and wings from Square Peg Pizzeria. Order online for pickup or delivery from ten locations in Connecticut and Delray Beach, FL.",
                  "evidence", dict(sigs=SIGNATURES, menu_bits=evidence_menu),
                  graph(breadcrumbs([("Home", "/"), ("Order", "/evidence/")])), "sp-three-pies", "sp-three-pies"))
    pages.append(("/links/", "Square Peg Pizzeria | All Our Links",
                  "Order online, find a location, see this month's specials, book catering or a fundraiser, and join the Square Peg Pizzeria rewards app.",
                  "links", {}, "", "margherita-board", "margherita-board"))
    pages.append(("/pizza-faq/", "Pizza FAQ: Slices, Reheating, Sizes & More | Square Peg Pizzeria",
                  "How many slices in a large pizza, how to reheat wood-fired pizza without ruining it, and how much to order. Answered by Square Peg Pizzeria.",
                  "pizzafaq", {}, graph(faq_schema([(q, re.sub(r"<[^>]+>", "", a)) for _, items in PIZZA_FAQ for q, a in items]),
                                        breadcrumbs([("Home", "/"), ("Pizza FAQ", "/pizza-faq/")])),
                  "oven-pizza", "oven-pizza"))
    pages.append(("/pizza-trivia/", "Pizza Trivia: Facts, Myths & History | Square Peg Pizzeria",
                  "Pizza facts worth knowing and three myths worth retiring, including the truth about Queen Margherita. From the wood-fired ovens at Square Peg Pizzeria.",
                  "trivia", {}, graph(breadcrumbs([("Home", "/"), ("Pizza trivia", "/pizza-trivia/")])),
                  "dough", "dough"))
    pages.append(("/date-night/", "Date Night Ideas in CT & Delray Beach | Square Peg",
                  "A good date night without the production. Wood-fired pizza, a proper bar, happy hour every day and half-price bottles on Fridays, at ten Square Pegs.",
                  "datenight", {}, graph(breadcrumbs([("Home", "/"), ("Date night", "/date-night/")])),
                  "friends-sharing", "friends-sharing"))
    pages.append(("/what-pizza-are-you/", "Quiz: What Pizza Are You? | Square Peg Pizzeria",
                  "Six questions, one answer you can actually order. Take the Square Peg Pizzeria pizza personality quiz and find the pie that matches you.",
                  "quiz", dict(quiz_json=ld_raw(dict(QUIZ, photos={k: img_url(v[1], 800).replace(SITE["domain"], "") for k, v in QUIZ["results"].items()}))),
                  graph(breadcrumbs([("Home", "/"), ("What pizza are you?", "/what-pizza-are-you/")])),
                  "sp-three-pies", "sp-three-pies"))
    pages.append(("/pizza-calculator/", "Pizza Calculator: How Many Pizzas? | Square Peg Pizzeria",
                  "How many pizzas for your party? Enter adults and kids and get the answer, based on what is actually on a 12-inch and an 18-inch pie.",
                  "calculator", dict(calc_json=ld_raw(CALC)), graph(breadcrumbs([("Home", "/"), ("Pizza calculator", "/pizza-calculator/")])),
                  "pizza-boxes", "pizza-boxes"))
    pages.append(("/pairing/", "What to Drink With Pizza | Ask Sal | Square Peg Pizzeria",
                  "Tell Sal what you're ordering and get a drink that actually fits. Plus six pizza and drink pairings worth knowing, from the team at Square Peg Pizzeria.",
                  "pairing", {}, graph(breadcrumbs([("Home", "/"), ("Pairing guide", "/pairing/")])),
                  "pie-spicy-margherita", "pie-spicy-margherita"))
    pages.append(("/monthly-specials/", f"{LTO['month']} Specials | Square Peg Pizzeria",
                  f"Square Peg Pizzeria's {LTO['month']} {LTO['year']} limited-time menu: new pizzas, starters, dessert and seasonal cocktails. Order online or dine in at ten locations.",
                  "lto", dict(lto=LTO), graph(breadcrumbs([("Home", "/"), ("Monthly specials", "/monthly-specials/")])),
                  LTO["sections"][2][1][0][2], LTO["sections"][2][1][0][2]))
    pages.append(("/sms-terms/", "SMS Terms | Square Peg Pizzeria", "Terms for the Square Peg Pizzeria text message program: message frequency, carrier costs, how to opt out at any time, and where to get help.",
                  "sms", dict(sms=SMS_TERMS), None, None, None))
    pages.append(("/thanks/", "Thank You | Square Peg Pizzeria", "Thanks for reaching out to Square Peg Pizzeria.", "simple",
                  dict(eyebrow="Request received", h1="Thank you!", lede="We got your request and will get back to you within one business day. While you wait, there’s pizza.", prose=""), None, None, None))
    pages.append(("/privacy/", "Privacy Policy | Square Peg Pizzeria", "How Square Peg Pizzeria collects, uses and protects the information you share on this website, in our rewards program and by text.", "simple",
                  dict(eyebrow="Privacy", h1="Privacy policy", lede="What we collect, how we use it, and the choices you have.",
                       prose=PRIVACY_TEXT), None, None, None))
    pages.append(("/terms/", "Terms & Conditions | Square Peg Pizzeria", "The terms for using the Square Peg Pizzeria website, our offers, promotions and rewards program, gift cards, and our text message program.", "simple",
                  dict(eyebrow="Terms", h1="Terms & conditions", lede="The rules for using this website, our offers and our text messages.",
                       prose=TERMS_TEXT), None, None, None))
    pages.append(("/404.html", "Page Not Found | Square Peg Pizzeria", "That page doesn’t exist.", "simple",
                  dict(eyebrow="404", h1="This page is a square peg.", lede="It doesn’t fit anywhere. Let’s get you back to the pizza."), None, None, None))

    rendered = []
    for path, title, desc, tpl, extra, schema, og, hero in pages:
        ctx = dict(base_ctx, **extra)
        ctx["path"] = path
        body = env.get_template(tpl).render(**ctx)
        og_url, og_alt = "", ""
        if not PREVIEW and path not in ("/404.html", "/thanks/"):
            h1m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
            h1_html = re.sub(r'<span class="(?:eyebrow h1-eyebrow|h1-sub)">.*?</span></?span>|<span class="(?:eyebrow h1-eyebrow|h1-sub)">.*?</span>', "", h1m.group(1) if h1m else title, flags=re.S)
            head_txt = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", h1_html)).split())
            ebm = re.search(r'<span class="eyebrow">(.*?)</span>', body, re.S)
            eyebrow = " ".join(html.unescape(re.sub(r"<[^>]+>", "", ebm.group(1))).split()) if ebm else "Square Peg Pizzeria"
            sub = ""
            if path.startswith("/locations/") and "l" in extra:
                l = extra["l"]; eyebrow = f"Wood-fired pizza · {l['city']}, {l['state']}"; sub = f"{l['street']}, {l['city']} · {l['phone']}"
            if path == "/":
                head_txt, eyebrow, sub = "Pizza worth remembering.", "Wood-fired pizza · CT & Delray Beach", "10 locations · Order pickup or delivery"
            if path == "/monthly-specials/":
                y, mo, dy = LTO["ends"].split("-")
                head_txt = f"{LTO['month']} Limited Time Menu"
                eyebrow = f"Limited time · through {_MONTHS[int(mo) - 1]} {int(dy)}"
                nf = sum(len(i) for _, i in LTO["sections"])
                nd = len(LTO["cocktails"])
                sub = _qty(nf, "dish", "dishes").capitalize()
                if nd:
                    sub += " and " + _qty(nd, "cocktail", "cocktails")
                sub += f", only in {LTO['month']}."
            key = "home" if path == "/" else path.strip("/").replace("/", "-")
            # Month-stamped so each month's card gets a fresh URL — Facebook and
            # LinkedIn cache share images by URL and will not re-scrape the old one.
            if path == "/monthly-specials/":
                key += "-" + LTO["ends"][:7]
            og_url = make_og(key, og or "margherita-board", eyebrow, head_txt, sub)
            og_alt = head_txt if "Square Peg" in head_txt else f"{head_txt} | Square Peg Pizzeria"
        ctx.update(bare=(path == "/links/"), title=title, desc=desc, body=body, canonical=abs_url(path if path != "/404.html" else "/"),
                   og_image=og_url, og_alt=og_alt, schema=ld(schema) if schema else "",
                   preload_tag="")
        if path == "/" and not PREVIEW and IMG_META.get("margherita-board") and IMG_META.get("oven-fire"):
            md, mm = IMG_META["margherita-board"], IMG_META["oven-fire"]
            ctx["preload_tag"] = ('<link rel="preload" as="image" type="image/avif" media="(min-width:900px)" imagesizes="56vw" fetchpriority="high" imagesrcset="' + ", ".join(f"/img/margherita-board-{x}.avif {x}w" for x in md["widths"]) + '">'
                                  '<link rel="preload" as="image" type="image/avif" media="(max-width:899px)" imagesizes="100vw" fetchpriority="high" imagesrcset="' + ", ".join(f"/img/oven-fire-{x}.avif {x}w" for x in mm["widths"]) + '">')
        elif hero:
            ctx["preload_tag"] = preload(hero, "100vw")
        rendered.append((path, title, desc, body, ctx))
        if not PREVIEW:
            doc = env.get_template("page").render(**ctx)
            full_css = ctx["css"]
            slim = purge_css(full_css, doc)
            doc = doc.replace("<style>" + full_css + "</style>", "<style>" + slim + "</style>", 1)
            doc = external_new_tab(doc)
            if path == "/404.html":
                doc = doc.replace('<meta name="description"', '<meta name="robots" content="noindex"><meta name="description"', 1)
            if path in ("/thanks/", "/what-you-did/", "/evidence/", "/links/"):
                doc = doc.replace('<meta name="description"', '<meta name="robots" content="noindex"><meta name="description"', 1)
            dest = OUT / (path.lstrip("/") if path.endswith(".html") else path.lstrip("/") + "index.html")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(doc)

    if PREVIEW:
        build_preview(rendered, base_ctx, js)
    else:
        import subprocess
        try:
            terser = os.environ.get("TERSER") or shutil.which("terser") or "/tmp/fs/node_modules/.bin/terser"
            mini = subprocess.run([terser, "-c", "-m"], input=js, capture_output=True, text=True, timeout=60)
            (OUT / "site.js").write_text(mini.stdout if mini.returncode == 0 and mini.stdout.strip() else js)
        except Exception:
            (OUT / "site.js").write_text(js)
        write_extras([p for p in pages if p[0] not in ("/404.html", "/thanks/", "/what-you-did/", "/evidence/", "/links/")])
    if PREV.exists():
        shutil.rmtree(PREV)
    print(f"  pages: {len(rendered)} -> {OUT}")

# Google uses <lastmod> only where it looks consistently accurate, and stamping
# every page with the build date on every build is exactly how a sitemap teaches
# it to stop looking. This keeps a small ledger of when each page's content last
# genuinely changed, so a date in the sitemap means something.
LASTMOD_FILE = ROOT / "data" / "lastmod.json"


def content_fingerprint(html):
    """Hash what a reader would notice changing.

    The inlined stylesheet and the cache-busting query on site.js are stripped
    first: a CSS tweak or a JS rebuild is not a change to this page's content,
    and letting either in would mark all 41 pages modified over a one-line fix."""
    h = re.sub(r"(?is)<style>.*?</style>", "", html)
    h = re.sub(r"site\.js\?v=[0-9a-f]+", "site.js", h)
    return hashlib.md5(h.encode("utf-8")).hexdigest()


def lastmod_dates(pages):
    """path -> the date its content last changed, persisted across builds."""
    try:
        ledger = json.loads(LASTMOD_FILE.read_text())
    except Exception:
        ledger = {}
    out, changed = {}, 0
    for path, *_ in pages:
        rel = path.lstrip("/") or "index.html"
        f = OUT / (rel if rel.endswith(".html") else rel + "/index.html")
        try:
            fp = content_fingerprint(f.read_text(encoding="utf-8"))
        except Exception:
            out[path] = TODAY
            continue
        prev = ledger.get(path)
        if prev and prev.get("hash") == fp:
            out[path] = prev["date"]
        else:
            out[path] = TODAY
            changed += 1
        ledger[path] = {"hash": fp, "date": out[path]}
    if not PREVIEW and not STAGING:
        LASTMOD_FILE.write_text(json.dumps(ledger, indent=1, sort_keys=True))
        print(f"  sitemap: {changed} of {len(pages)} pages changed today")
    return out


def write_extras(pages):
    mod = lastmod_dates(pages)
    urls = "".join(f"<url><loc>{abs_url(p[0])}</loc><lastmod>{mod.get(p[0], TODAY)}</lastmod></url>" for p in pages)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    bots = ["Googlebot", "Bingbot", "Applebot", "Google-Extended", "Applebot-Extended", "GPTBot", "OAI-SearchBot", "ChatGPT-User",
            "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User", "CCBot", "Amazonbot", "DuckAssistBot"]
    robots = "# Search engines and AI assistants are welcome to read this site.\n"
    # /thanks/ is kept out of search by its own noindex tag, not by robots.txt. Blocking it here
    # too would stop Google reading that tag, which is how a "blocked" URL ends up indexed anyway
    # and shows up in Search Console as "Blocked by robots.txt".
    robots += "".join(f"User-agent: {b}\n" for b in bots) + "Allow: /\n\n"
    robots += "User-agent: *\nAllow: /\n\n" + f"Sitemap: {abs_url('/sitemap.xml')}\n"
    (OUT / "robots.txt").write_text(robots)
    order = SITE["order_base"]
    # Old Toast-site URLs -> new pages, and old ordering links -> the Toast ordering subdomain.
    (OUT / "_redirects").write_text(redirects_file())
    (OUT / "llms.txt").write_text(llms_txt())
    (OUT / "vercel.json").write_text(json.dumps(vercel_config(), indent=2))
    if STAGING:
        (OUT / "robots.txt").write_text("# Team review copy. Not for search engines.\nUser-agent: *\nDisallow: /\n")
    with open(ROOT / "REDIRECTS.csv", "w") as f:
        f.write("old_url,new_url,status\n")
        for a, b in redirect_map():
            f.write(f"{SITE['domain']}{a},{b if b.startswith('http') else SITE['domain'] + b},301\n")
    (OUT / "_headers").write_text("\n".join([
        "/*",
        "  X-Content-Type-Options: nosniff",
        "  Referrer-Policy: strict-origin-when-cross-origin",
        "  Permissions-Policy: geolocation=(self), camera=(), microphone=()",
        "  X-Frame-Options: SAMEORIGIN",
        "  Cross-Origin-Opener-Policy: same-origin-allow-popups",
        "  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload",
        f"  Content-Security-Policy: {CSP_ENFORCED}",
        f"  Content-Security-Policy-Report-Only: {CSP_FULL}",
        "/img/*",
        "  Cache-Control: public, max-age=31536000, immutable",
        "/fonts/*",
        "  Cache-Control: public, max-age=31536000, immutable",
        "/site.js",
        "  Cache-Control: public, max-age=31536000, immutable",
        "/*.html",
        "  Cache-Control: public, max-age=0, must-revalidate",
        "",
    ]))
    (OUT / "netlify.toml").write_text('[build]\n  publish = "."\n\n[build.processing.html]\n  pretty_urls = true\n')

CSP_ENFORCED = "frame-ancestors 'self'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests"
# Everything the pages actually load: our own files, the Vendasta chat, analytics (when switched on),
# the Connect/Wingman form frames, Google Maps frames and Supabase for the contact form.
CSP_FULL = "; ".join([
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    "frame-ancestors 'self'",
    "form-action 'self'",
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    "style-src 'self' 'unsafe-inline'",
    "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com https://cdn.apigateway.co https://*.apigateway.co https://www.googletagmanager.com https://connect.facebook.net",
    "connect-src 'self' https://*.supabase.co https://*.functions.supabase.co https://challenges.cloudflare.com https://*.apigateway.co https://www.google-analytics.com https://*.analytics.google.com https://connect.facebook.net https://www.facebook.com",
    "frame-src https://challenges.cloudflare.com https://connect.squarepegpizzeria.com https://www.joinwingman.app https://www.google.com https://maps.google.com https://*.apigateway.co",
    "upgrade-insecure-requests",
])

ORDER_HOST = TOAST_SUBDOMAIN   # redirects from old main-domain Toast URLs always go here

def redirect_map():
    """Every URL in the old Toast sitemap -> its new home. 301 = permanent (passes SEO value)."""
    m = [
        # Old Toast website pages -> new pages
        ("/events-catering", "/catering/"), ("/catering-0", "/catering/"), ("/catering-5", "/catering/"),
        ("/catering-6", "/catering/"), ("/catering-booking", "/catering/"), ("/catering-form-test", "/catering/"),
        ("/party-requests", "/large-party-reservations/"),
        ("/tuesday-charity-night", "/fundraisers/"), ("/tuesday-charity-signup", "/fundraisers/#apply"),
        ("/monthly-deals", "/deals/"), ("/reward-program", "/deals/"),
        ("/gallery", "/about/"),
        ("/privacy-policy", "/privacy/"),
        # Toast-powered pages -> Toast on the order subdomain (same paths, so every deep link keeps working)
        ("/order", ORDER_HOST + "/order"), ("/order/*", ORDER_HOST + "/order/:splat"),
        ("/menu", ORDER_HOST + "/menu"),
        ("/account/*", ORDER_HOST + "/account/:splat"), ("/checkout/*", ORDER_HOST + "/checkout/:splat"),
        ("/cart/*", ORDER_HOST + "/cart/:splat"), ("/confirm/*", ORDER_HOST + "/confirm/:splat"),
    ]
    # Redirects that already exist on the old Toast site (Toast > Website > Path redirects), pointed straight at their new homes
    m += [("/party-request", "/large-party-reservations/"), ("/popmenu-order", ORDER_HOST + "/menu"),
          ("/events/*", "/entertainment/")]
    for l in LOCATIONS:
        town = l["city"].lower().replace(" ", "-")
        # /menu-<town> is what the old site's press coverage links to — CT Insider's
        # Storrs piece (DR 80) points at /menu-storrs. Sending it off to Toast hands
        # that link's value to Toast's domain, so it lands on our own location page,
        # which carries the order button anyway.
        m.append((f"/menu-{town}", f"/locations/{l['slug']}/"))
        # Old deep menu URLs: /menu/<toast slug>/group_.../item-... . Those exact paths 404 on the
        # subdomain now, so land the guest on that store's ordering page rather than a dead end.
        m.append((f"/menu/{l['toast']}", ORDER_HOST + "/order/" + l["toast"]))
        m.append((f"/menu/{l['toast']}/*", ORDER_HOST + "/order/" + l["toast"]))
    gc = SITE["gift_cards_url"]
    target = gc if not gc.startswith((SITE["domain"], ORDER_HOST)) else ORDER_HOST + TOAST_PATHS["gift_cards"]
    m += [("/gift-card", target), ("/gift-cards", target)]
    # Older (Popmenu-era) URLs still in Google's index, e.g. www.squarepegpizzeria.com/popmenu-digital-gift-cards
    m += [("/popmenu-digital-gift-cards", target),
          ("/menus", ORDER_HOST + "/menu"), ("/menus/*", ORDER_HOST + "/menu"), ("/dishes/*", ORDER_HOST + "/menu"),
          # Old Toast item pages, e.g. /items/bud-heavy?location=glastonbury — no way to map the
          # store from a static rule, so the menu picker is the honest landing place.
          ("/items", ORDER_HOST + "/menu"), ("/items/*", ORDER_HOST + "/menu"),
          # anything under /menu/ we haven't matched above
          ("/menu/*", ORDER_HOST + "/menu"),
          ("/food-trucks", "/food-truck/"),
          ("/reviews", "/about/"), ("/jobs", "/careers/")]
    return m

def redirects_file():
    lines = ["# Square Peg Pizzeria redirects (Netlify format). All permanent (301).",
             "# Pages that exist on the new site (/about, /contact, /entertainment, /food-truck, /locations, /private-events, /promotions, /roll-the-dice, /sms-terms) keep their URLs; no redirect needed.", ""]
    for a, b in redirect_map():
        lines.append(f"{a:<28} {b:<60} 301")
    return "\n".join(lines) + "\n"

def vercel_config():
    """Vercel equivalent of _redirects + _headers."""
    redirects = []
    for a, b in redirect_map():
        dst = b.replace(":splat", ":path*")
        if a.endswith("/*"):
            base = a[:-2]
            # /order/anything, plus the trailing-slash form. trailingSlash is on, so Vercel 308s
            # /order/foo to /order/foo/ BEFORE redirects run; without the twin that lands on a 404.
            for src in (base + "/:path*", base + "/:path*/"):
                redirects.append({"source": src, "destination": dst, "permanent": True})
            continue
        # match both /old-page and /old-page/ (Vercel adds the slash before redirects run)
        for src in (a, a + "/"):
            redirects.append({"source": src, "destination": dst, "permanent": True})
    headers = [
        {"source": "/(.*)", "headers": [
            {"key": "X-Content-Type-Options", "value": "nosniff"},
            {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
            {"key": "Permissions-Policy", "value": "geolocation=(self), camera=(), microphone=()"},
            {"key": "X-Frame-Options", "value": "SAMEORIGIN"},
            {"key": "Content-Security-Policy", "value": CSP_ENFORCED},
            # Full policy in report-only mode first: check the browser console for blocks, then
            # move this value into Content-Security-Policy above (see SECURITY_AND_BACKUPS.md).
            {"key": "Content-Security-Policy-Report-Only", "value": CSP_FULL},
            {"key": "Cross-Origin-Opener-Policy", "value": "same-origin-allow-popups"},
            {"key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains"}]
            + ([{"key": "X-Robots-Tag", "value": "noindex, nofollow"}] if STAGING else [])},
        {"source": "/img/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
        {"source": "/fonts/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
        # site.js is requested as /site.js?v=<hash of its contents>, so a new build
        # is a new URL and the old one can be cached as long as the browser likes.
        {"source": "/site.js", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
    ]
    return {"$schema": "https://openapi.vercel.sh/vercel.json", "trailingSlash": True, "cleanUrls": False,
            "redirects": redirects, "headers": headers}

def llms_txt():
    out = ["# Square Peg Pizzeria", "", "> Wood-fired pizza made fresh from scratch, with 10 locations in Connecticut and Delray Beach, Florida. Online ordering for pickup and delivery, catering, a wood-fired food truck, Tuesday night fundraisers, and a rewards app.", "",
           "## Locations"]
    for l in LOCATIONS:
        out.append(f"- [{l['name']}]({abs_url('/locations/' + l['slug'] + '/')}): {l['street']}, {l['city']}, {l['state']} {l['zip']} · {l['phone']} · order: {order_url(l)}")
        if l.get("areas"):
            out.append(f"  - Nearby towns (within 15 miles): {', '.join(r['name'] + ('' if r['state'] == l['state'] else ', ' + r['state']) for r in l['areas'])}")
    out += ["", "## Menu (Italian-American restaurant + wood-fired pizza)",
            "- Pizza: " + "; ".join(f"{n} ({d})" for n, d in MENU["pizza_styles"])]
    for t, _, items in MENU["sections"]:
        out.append(f"- {t}: " + ", ".join(n for n, _ in items))
    out += [f"- Full overview: {abs_url('/our-menu/')}. Live menus and prices: each location's order link above.", ""]
    out += ["## Pages",
            f"- [Catering]({abs_url('/catering/')})", f"- [Large party reservations]({abs_url('/large-party-reservations/')})", f"- [Contact]({abs_url('/contact/')})", f"- [Food truck]({abs_url('/food-truck/')})", f"- [Deals & rewards]({abs_url('/deals/')})",
            f"- [Tuesday fundraisers]({abs_url('/fundraisers/')})", f"- [Our story]({abs_url('/about/')})", f"- [Towns we serve]({abs_url('/areas-we-serve/')}): every town within 15 miles and its closest Square Peg", ""]
    return "\n".join(out)

SAFE_CLASSES = {"open", "is-past", "menu-open", "is-open", "is-closed", "is-soon", "is-today", "is-near", "is-pref", "is-sized",
                "pick", "pick-name", "pick-addr", "pick-meta", "pick-call", "tonight-card", "note", "status", "btn", "btn--sm", "sp-embed", "today",
                # injected by the quiz and the pizza calculator after load
                "quiz-prog", "quiz-bar", "quiz-q", "quiz-opts", "quiz-opt", "quiz-back",
                "quiz-result", "quiz-eyebrow", "quiz-pic", "btn--line", "btn-row",
                "calc-answer", "calc-eyebrow", "calc-big", "calc-sub", "calc-detail", "calc-empty"}

def split_rules(css):
    """Top-level CSS blocks: plain rules, @media blocks (split further), and other @-rules kept as-is."""
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        head = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{": depth += 1
            elif css[k] == "}": depth -= 1
            k += 1
        body = css[j + 1:k - 1]
        out.append((head, body))
        i = k
    return out

def purge_css(css, page_html):
    classes = set(re.findall(r'class="([^"]*)"', page_html))
    tokens = set(" ".join(classes).split()) | SAFE_CLASSES
    ids = set(re.findall(r'id="([^"]+)"', page_html))
    def keep_selector(sel):
        need_c = re.findall(r"\.([a-zA-Z0-9_-]+)", sel)
        need_i = re.findall(r"#([a-zA-Z0-9_-]+)", sel)
        return all(c in tokens for c in need_c) and all(i in ids for i in need_i)
    def process(block):
        res = []
        for head, body in split_rules(block):
            if head.startswith("@media") or head.startswith("@supports"):
                inner = process(body)
                if inner:
                    res.append(head + "{" + inner + "}")
            elif head.startswith("@"):
                res.append(head + "{" + body + "}")
            else:
                sels = [x for x in head.split(",") if keep_selector(x)]
                if sels:
                    res.append(",".join(sels) + "{" + body + "}")
        return "".join(res)
    return process(css)

def external_new_tab(doc):
    """Every link that leaves squarepegpizzeria.com opens in a new tab."""
    def fix(m):
        tag = m.group(0)
        href = re.search(r'href="([^"]+)"', tag).group(1)
        if not href.startswith("http"):
            return tag
        host = re.sub(r"^https?://", "", href).split("/")[0].lower()
        if host in ("squarepegpizzeria.com", "www.squarepegpizzeria.com") and not re.search(r"/(order|menu|gift-cards?)(/|$)", href):
            return tag
        if "target=" not in tag:
            tag = tag[:-1] + ' target="_blank">'
        if "rel=" not in tag:
            tag = tag[:-1] + ' rel="noopener">'
        return tag
    return re.sub(r'<a\s[^>]*href="[^"]+"[^>]*>', fix, doc)

def build_preview(rendered, ctx, js):
    """One self-contained page: every route is a section, switched by the URL hash."""
    home = rendered[0][4]
    sections = []
    titles = {}
    for path, title, desc, body, _ in rendered:
        if path == "/404.html":
            continue
        sections.append(f'<div class="route" data-route="{path}"{"" if path == "/" else " hidden"}>{body}</div>')
        titles[path] = title
    header = env.get_template("header").render(**dict(ctx, path="/"))
    footer = env.get_template("footer").render(**ctx)
    router = """
<script>
(function(){
  var titles=%s;
  function go(){
    var h=location.hash.replace(/^#/,'')||'/';
    var anchor='';
    if(h.indexOf('#')>-1){anchor=h.split('#')[1];h=h.split('#')[0];}
    h=h.split('?')[0];
    if(h.charAt(0)!=='/'){var el=document.getElementById(h);if(el)el.scrollIntoView();return;}
    var found=false;
    document.querySelectorAll('.route').forEach(function(r){var on=r.getAttribute('data-route')===h;r.hidden=!on;if(on)found=true;});
    if(!found){document.querySelector('.route[data-route="/"]').hidden=false;h='/';}
    document.title=titles[h]||titles['/'];
    document.querySelectorAll('.nav a').forEach(function(a){a.toggleAttribute('aria-current',a.getAttribute('href')==='#'+h)});
    var d=document.getElementById('drawer');if(d)d.classList.remove('open');
    if(anchor){var t=document.getElementById(anchor);if(t){t.scrollIntoView();return;}}
    window.scrollTo(0,0);
  }
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a[href^="#"]');if(!a)return;
    var href=a.getAttribute('href');
    if(href.charAt(1)!=='/'){ // in-page anchor: keep current route
      e.preventDefault();var t=document.getElementById(href.slice(1));if(t)t.scrollIntoView({behavior:'smooth'});
    }
  });
  addEventListener('hashchange',go);go();
})();
</script>""" % json.dumps(titles)
    # rewrite "/page/#anchor" style links produced by u()+'#x'
    head = env.get_template("head").render(**home)
    head = re.sub(r"<title>.*?</title>", "<title>Square Peg Site Preview</title>", head, count=1)
    doc = (head + header +
           '<main id="main">' + "".join(sections) + "</main>" + footer +
           "<script>" + js + "</script>" + router)
    doc = doc.replace(' data-supabase="contact_messages"', '')
    doc = doc.replace('<form class="form" name=', '<form class="form" onsubmit="event.preventDefault();location.hash=\'/thanks/\'" name=')
    (OUT / "square-peg-site.html").write_text(external_new_tab(doc))

if __name__ == "__main__":
    main()
