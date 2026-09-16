#!/usr/bin/env python3
"""
Square Peg Pizzeria static site builder.

  python3 build.py            -> production site in ./dist  (deploy this folder)
  python3 build.py --preview  -> single-file preview bundle in ./preview

Content lives in data/content.py. Styles in src/site.css. Behavior in src/site.js.
Photos: drop originals into assets/img-src/<name>.(webp|jpg|png) and rebuild.
"""
import json, re, shutil, sys, html, hashlib
from datetime import date
from pathlib import Path
from jinja2 import Environment, DictLoader, select_autoescape
from PIL import Image

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "data"))
from content import SITE, LOCATIONS, REGIONS, DEAL, POINTS, APP_PERKS, SIGNATURES, REVIEWS, FUNDRAISER_FAQ, CATERING_FAQ, DAYS, SMS_TERMS, DICE, EMBEDS, LARGE_PARTY_FAQ, CONTACT_TOPICS, ENTERTAINMENT, PROMOS  # noqa

PREVIEW = "--preview" in sys.argv
STAGING = "--staging" in sys.argv   # team review deploy: hidden from Google
OUT = ROOT / ("preview" if PREVIEW else "dist-staging" if STAGING else "dist")
IMG_SRC = ROOT / "assets" / "img-src"
WIDTHS = [360, 480, 640, 800, 1200, 1600]
TODAY = date.today().isoformat()

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

def hours_rows(loc):
    rows = []
    names = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}
    for d in DAYS:
        v = loc["hours"][d]
        rows.append((d, names[d], "Closed" if not v else f"{fmt_time(v[0])} – {fmt_time(v[1])}"))
    return rows

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
        lines.append(f"{label} {'Closed' if not v else fmt_time(v[0]) + '–' + fmt_time(v[1])}")
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
            r = im.resize((x, round(h * x / w)), Image.LANCZOS) if x != w else im
            r.save(dest / f"{name}-{x}.webp", "WEBP", quality=74, method=6)
            if not PREVIEW:
                r.save(dest / f"{name}-{x}.avif", "AVIF", quality=50, speed=6)
        IMG_META[name] = {"w": w, "h": h, "widths": widths, "alpha": has_alpha}
    print(f"  images: {len(IMG_META)} processed")

def build_brand():
    dest = OUT / "img"
    dest.mkdir(parents=True, exist_ok=True)
    src = Image.open(ROOT / "src" / "brand" / "logo-on-dark.png").convert("RGBA")
    orig = Image.open(ROOT / "src" / "brand" / "logo-src.png").convert("RGBA")
    for w in (160, 280, 480):
        src.resize((w, round(src.height * w / src.width)), Image.LANCZOS).save(dest / f"logo-on-dark-{w}.webp", "WEBP", quality=72, method=6)
    if not PREVIEW:
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
    page = abs_url(f"/locations/{l['slug']}/")
    o = {
        "@type": "Restaurant", "@id": page + "#restaurant",
        "name": f"Square Peg Pizzeria {l['name']}",
        "url": page, "telephone": tel(l["phone"]),
        "address": {"@type": "PostalAddress", "streetAddress": l["street"], "addressLocality": l["city"], "addressRegion": l["state"], "postalCode": l["zip"], "addressCountry": "US"},
        "servesCuisine": ["Pizza", "Italian", "American"], "priceRange": "$$",
        "hasMenu": order_url(l), "menu": order_url(l), "parentOrganization": {"@id": ORG_ID},
        "openingHoursSpecification": spec,
        "hasMap": maps_url(l),
        "areaServed": [{"@type": "City", "name": f"{t}, {l['state']}"} for t in [l["city"]] + l["nearby"]],
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
ICONS = {
    "bag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M5 8h14l-1 12H6L5 8Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg>',
    "tag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M3 12V3h9l9 9-9 9-9-9Z"/><circle cx="7.5" cy="7.5" r="1.5"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
}

NAV = [("Menu", "MENU"), ("Locations", "/locations/"), ("Specials", "/promotions/"), ("Catering", "/catering/"),
       ("Large Parties", "/large-party-reservations/"), ("Entertainment", "/entertainment/")]
MORE = [("Private Events & Classes", "/private-events/"), ("Food Truck", "/food-truck/"), ("Tuesday Fundraisers", "/fundraisers/"),
        ("Rewards & Monthly Deals", "/deals/"), ("Gift Cards", "GIFT"), ("Roll the Dice", "/roll-the-dice/"),
        ("Our Story", "/about/"), ("Careers", "/careers/"), ("Contact", "/contact/")]
DRAWER_EXTRA = []
DRAWER_GROUPS = [
    ("Eat", [("Menu", "MENU"), ("Locations", "/locations/"), ("Specials", "/promotions/"), ("Rewards & Deals", "/deals/")]),
    ("Plan", [("Catering", "/catering/"), ("Large Parties", "/large-party-reservations/"), ("Private Events & Classes", "/private-events/"), ("Food Truck", "/food-truck/"), ("Tuesday Fundraisers", "/fundraisers/")]),
    ("Fun", [("Entertainment", "/entertainment/"), ("Roll the Dice", "/roll-the-dice/"), ("Gift Cards", "GIFT")]),
    ("Square Peg", [("Our Story", "/about/"), ("Careers", "/careers/"), ("Contact", "/contact/")]),
]
DAY_NAMES = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}

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
      <img src="{{ imgbase }}logo-on-dark-280.webp" srcset="{{ imgbase }}logo-on-dark-160.webp 160w, {{ imgbase }}logo-on-dark-280.webp 280w, {{ imgbase }}logo-on-dark-480.webp 480w" sizes="(min-width:980px) 153px, 135px" width="160" height="{{ (160 * logo_ratio)|round|int }}" alt="Square Peg Pizzeria">
    </a>
    <nav class="nav" aria-label="Main">{% for n, p in nav %}{% if p == 'MENU' %}<a href="{{ site.menu_url }}" data-open-picker="menu">{{ n }}</a>{% else %}<a href="{{ u(p) }}"{% if p == path %} aria-current="page"{% endif %}>{{ n }}</a>{% endif %}{% endfor %}
      <details class="more"><summary>More</summary><div class="more-menu">{% for n, p in more %}{% if p == 'GIFT' %}<a href="{{ site.gift_cards_url }}" rel="noopener"{{ ext|safe }}>{{ n }}</a>{% else %}<a href="{{ u(p) }}"{% if p == path %} aria-current="page"{% endif %}>{{ n }}</a>{% endif %}{% endfor %}</div></details></nav>
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
          {% for n, p in links %}{% if p == 'MENU' %}<a href="{{ site.menu_url }}" data-open-picker="menu">{{ n }}</a>{% elif p == 'GIFT' %}<a href="{{ site.gift_cards_url }}" rel="noopener"{{ ext|safe }}>{{ n }}</a>{% else %}<a href="{{ u(p) }}"{% if p == path %} aria-current="page"{% endif %}>{{ n }}</a>{% endif %}{% endfor %}
        </div>{% endfor %}
      </nav>
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
        <img class="foot-logo" src="{{ imgbase }}logo-on-dark-480.webp" width="480" height="{{ (480 * logo_ratio)|round|int }}" alt="Square Peg Pizzeria" loading="lazy">
        <p class="foot-title">10 Square Pegs</p>
        <div class="foot-locs">
          {% for l in locs %}<div><a href="{{ u('/locations/' ~ l.slug ~ '/') }}">{{ l.name }}</a><span>{{ l.street }}, {{ l.city }}, {{ l.state }}</span><a class="ph" href="tel:{{ tel(l.phone) }}">{{ l.phone }}</a></div>{% endfor %}
        </div>
      </div>
      <div class="foot-links">
        <a href="{{ site.menu_url }}" data-open-picker="menu">Menu</a><a href="{{ u('/catering/') }}">Catering</a><a href="{{ u('/large-party-reservations/') }}">Large Parties</a><a href="{{ u('/food-truck/') }}">Food Truck</a>
        <a href="{{ u('/promotions/') }}">Specials</a><a href="{{ u('/deals/') }}">Rewards & Deals</a><a href="{{ u('/entertainment/') }}">Entertainment</a><a href="{{ u('/private-events/') }}">Private Events & Classes</a><a href="{{ u('/fundraisers/') }}">Tuesday Fundraisers</a><a href="{{ u('/about/') }}">Our Story</a><a href="{{ u('/contact/') }}">Contact</a>
        <a href="{{ site.gift_cards_url }}" rel="noopener"{{ ext|safe }}>Gift Cards</a><a href="{{ u('/roll-the-dice/') }}">Roll the Dice</a><a href="{{ u('/careers/') }}">Careers</a><a href="{{ site.app_link }}" rel="noopener"{{ ext|safe }}>Get the App</a>
        {% if site.facebook %}<a href="{{ site.facebook }}" rel="noopener"{{ ext|safe }}>Facebook</a>{% endif %}
        {% if site.instagram %}<a href="{{ site.instagram }}" rel="noopener"{{ ext|safe }}>Instagram</a>{% endif %}
      </div>
    </div>
    <div class="be-nice" aria-hidden="true" data-text="Be Nice."></div>
    <div class="foot-base">
      <span>© {{ year }} Square Peg Pizzeria. Wood-fired in Connecticut & Delray Beach, FL.</span>
      <span><a href="{{ u('/privacy/') }}">Privacy</a> · <a href="{{ u('/sms-terms/') }}">SMS Terms</a> · <a href="{{ site.loyalty_signin }}" rel="noopener"{{ ext|safe }}>Rewards sign-in</a></span>
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
  {% if ent.get(l.slug) %}<div class="card-ent" aria-label="Weekly entertainment">{% for d, e, t in ent[l.slug] %}<span class="ent-chip" data-ent-day="{{ d }}"><b>{{ d }}</b> {{ e }}</span>{% endfor %}</div>{% endif %}
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
{% include "header" %}
<main id="main">{{ body|safe }}</main>
{% include "footer" %}
{% if not preview %}<script src="/site.js?v={{ jsv }}" defer></script>
</body></html>{% endif %}"""

# ---------- HOME
T["home"] = """
<section class="hero on-dark">
  {{ hero_picture('margherita-board', 'oven-fire', 'A wood-fired margherita pizza fresh from the Square Peg oven')|safe }}
  <div class="wrap">
    <h1><span class="eyebrow h1-eyebrow"><span>Wood-fired pizza in Connecticut & Delray Beach, FL</span></span>Pizza worth <em>remembering.</em></h1>
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

<div class="ribbon"><div class="wrap">
  <strong>{{ deal.headline }}</strong><span>{{ deal.eyebrow }} · Mon–Fri dine-in · {{ deal.expires_label }}</span>
  <a href="{{ u('/deals/') }}">See all deals →</a>
</div></div>

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
        <div class="sig-photo">{{ img(p, n ~ ' pizza from Square Peg Pizzeria', sizes='(min-width:900px) 25vw, 78vw')|safe }}<span class="sig-size">12″ · 18″</span></div>
        <div class="sig-body"><h3>{{ n }}</h3><p>{{ d }}</p><a class="btn btn--sm" href="{{ u('/locations/') }}" data-open-picker="order" aria-label="Order this: {{ n }}">Order this</a></div>
      </article>{% endfor %}
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap craft">
    <div class="craft-photo">{{ img('dough', 'A ball of fresh Square Peg pizza dough', sizes='(min-width:900px) 50vw, 100vw')|safe }}
      <div class="stamp">Never<br>frozen<small>Dough made daily</small></div></div>
    <div class="stack">
      <span class="eyebrow">How we make it</span>
      <h2>Water. Flour. Time. Fire.</h2>
      <p class="prose" style="font-size:18px">Every dough ball starts in our East Hartford kitchen and gets stretched by hand before it hits the wood-fired oven. We roast, simmer and season with purpose, and it’s worth it for the head-tilt, the smile and the “wow” after the first bite.</p>
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
      <a class="tile on-dark" href="{{ u('/catering/') }}">{{ img('table-spread', 'A catering spread of wings, meatballs, salads and drinks', sizes='(min-width:900px) 50vw, 100vw')|safe }}
        <div class="tile-body"><span class="eyebrow">Catering</span><h3 style="font-size:clamp(34px,4vw,48px)">Enough pizza for everyone. We promise.</h3><p>Tell us your headcount and date, and we’ll make sure there’s enough wood-fired pizza for everyone, ready when you pick it up.</p><span class="btn">Plan my catering {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/large-party-reservations/') }}">{{ img('friends-holiday', 'A group of friends celebrating over pizza', sizes='(min-width:1000px) 33vw, 100vw')|safe }}
        <div class="tile-body"><span class="eyebrow">Large parties</span><h3 style="font-size:clamp(34px,4vw,48px)">Bring the whole crew.</h3><p>Birthdays, team dinners and reunions. We’ll save the tables and plan the food so it lands together.</p><span class="btn">Reserve for a group {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/food-truck/') }}">{{ img('food-truck', 'The Square Peg Pizzeria wood-fired food truck', sizes='(min-width:900px) 50vw, 100vw')|safe }}
        <div class="tile-body"><span class="eyebrow">Food truck</span><h3 style="font-size:clamp(34px,4vw,48px)">We bring the oven to you.</h3><p>A wood-fired oven on wheels for backyard parties, schools, breweries and corporate events.</p><span class="btn">Book the truck {{ icons.arrow|safe }}</span></div></a>
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap band">
    <div class="band-media">{{ img('team-kids', 'A youth sports team celebrating their fundraiser night at Square Peg', sizes='(min-width:900px) 40vw, 100vw')|safe }}<div class="band-num"><div class="big-num" aria-hidden="true">20<sup>%</sup></div><p>of dine-in food sales, back to your cause</p></div></div>
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
    <p class="lede">Ten wood-fired kitchens, all making dough from scratch every day. Find the closest one, check if it’s open, and order in a tap.</p>
    <div class="btn-row"><button class="btn btn--flame" type="button" id="geo-quick">{{ icons.pin|safe }}Sort by closest to me</button><a class="btn btn--ghost" href="{{ u('/locations/') }}" data-open-picker="order">{{ icons.bag|safe }}Order now</a></div>
  </div>
</section>
<section class="section section--dark on-dark" style="padding-top:32px">
  <div class="wrap">
    <h2 class="sr-only">All 10 Square Peg Pizzeria locations</h2>
    <div class="loc-grid loc-grid--all" id="loc-grid">
      {% for r in regions %}{% for l in locs if l.region == r %}{% include "loc_card" %}{% endfor %}{% endfor %}
      <div class="loc-card loc-cta"><span class="eyebrow">Can’t decide?</span><h3>Let us pick the closest Peg.</h3><p>Share your location and we’ll sort all ten by distance, with live open/closed status.</p><div class="btn-row"><button class="btn btn--flame" type="button" onclick="document.getElementById('geo-quick').click()">{{ icons.pin|safe }}Find my closest</button><a class="btn btn--ghost" href="{{ u('/catering/') }}">Catering from any Peg</a></div></div>
    </div>
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
    <h1>Square Peg Pizzeria {{ l.name }}<span class="h1-sub">Wood-fired pizza in {{ l.city }}, {{ l.state }}</span></h1>
    <p class="lede">Wood-fired pizza, pasta, wings and more at {{ l.street }} in {{ l.city }}, {{ l.state }}. Order online for pickup or delivery, or come hang out.</p>
    <div><span class="status" data-status="{{ l.slug }}">{{ l.summary[0] }}</span></div>
    <div class="loc-actions">
      <a class="btn" href="{{ order(l) }}" data-pick="{{ l.slug }}" data-track="order_click" data-src="loc-hero" rel="noopener">{{ icons.bag|safe }}Order {{ l.short or l.name }} online</a>
      <a class="btn btn--ghost" href="tel:{{ tel(l.phone) }}" data-pick="{{ l.slug }}" data-track="call_click" data-loc="{{ l.slug }}">{{ icons.phone|safe }}<span class="narrow-only">Call</span><span class="wide-only">{{ l.phone }}</span></a>
      <a class="btn btn--ghost" href="{{ maps(l) }}" rel="noopener" data-track="directions_click" data-loc="{{ l.slug }}"{{ ext|safe }}>{{ icons.pin|safe }}Directions</a>
    </div>
  </div>
</section>

{% if ent.get(l.slug) %}<section class="ent-strip on-dark" aria-label="Weekly entertainment at Square Peg {{ l.short or l.name }}">
  <div class="wrap">
    <div class="ent-strip-head"><span class="eyebrow">Weekly entertainment</span><a href="{{ u('/entertainment/') }}">All locations →</a></div>
    <div class="ent-cards">{% for d, e, t in ent[l.slug] %}<div class="ent-card-sm" data-ent-day="{{ d }}"><span class="d">{{ day_names[d] }}</span><b>{{ e }}</b><span>{{ t }}</span></div>{% endfor %}</div>
  </div>
</section>{% endif %}
<section class="section section--paper">
  <div class="wrap info">
    <div class="info-card">
      <h2>Hours</h2>
      <table class="hours"><caption class="sr-only">Opening hours for Square Peg Pizzeria {{ l.name }}</caption>
        <tbody>{% for d, name, v in rows %}<tr data-day="{{ d }}"><th scope="row">{{ name }}</th><td>{{ v }}</td></tr>{% endfor %}</tbody></table>
      <p class="note">Holiday hours may vary. Online ordering shows live availability.</p>
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
</section>

<section class="section">
  <div class="wrap two-col">
    <div class="stack local">
      <span class="eyebrow">About this Peg</span>
      <h2>Wood-fired pizza in {{ l.city }}</h2>
      <p>{{ l.blurb }}</p>
      <p>Every pie starts with dough made fresh daily and never frozen. Choose a red or white signature pie, build your own, or go gluten-free with our 12″ crust. Vegan cheese is available on any pizza.</p>
      <div><p class="note" style="font-weight:700;margin-bottom:6px">Close to</p><div class="chips">{% for n in l.nearby %}<span class="chip">{{ n }}</span>{% endfor %}</div></div>
    </div>
    <div class="stack">
      <span class="eyebrow">Popular here</span>
      <div>
        {% for n, d, p in sigs %}<div class="item"><h3>{{ n }}</h3><p>{{ d }}</p></div>{% endfor %}
      </div>
      <div class="btn-row"><a class="btn" href="{{ order(l) }}" data-pick="{{ l.slug }}" data-track="order_click" data-src="loc-menu" rel="noopener">{{ icons.bag|safe }}See live menu & order</a><a class="btn btn--line" href="tel:{{ tel(l.phone) }}" data-track="call_click" data-loc="{{ l.slug }}">{{ icons.phone|safe }}Call in an order</a></div>
    </div>
  </div>
</section>

<section class="section section--paper">
  <div class="wrap">
    <div class="tiles">
      <a class="tile on-dark" href="{{ u('/fundraisers/') }}" style="min-height:360px">{{ img('team-kids', 'A youth team at a Square Peg Tuesday fundraiser', sizes='(min-width:900px) 50vw, 100vw')|safe }}
        <div class="tile-body"><span class="eyebrow">Tuesday fundraisers</span><h3 style="font-size:40px">20% back to your cause</h3><p>Book a Tuesday night at {{ l.short or l.name }} for your school, team or nonprofit.</p><span class="btn">Request a Tuesday {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/deals/') }}" style="min-height:360px">{{ img('pizza-boxes', 'Stacked Square Peg pizza boxes', sizes='(min-width:900px) 50vw, 100vw')|safe }}
        <div class="tile-body"><span class="eyebrow">{{ deal.eyebrow }}</span><h3 style="font-size:40px">{{ deal.headline }}</h3><p>Join free in the Square Peg app and start earning points on every visit.</p><span class="btn">See deals {{ icons.arrow|safe }}</span></div></a>
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
  <small>We reply within one business day. Prefer to talk? Call {{ site.catering_phone }}.</small>
</form>"""

T["booking_form"] = """{% set e = embeds.get(embed_key) %}{% if e %}<div class="form-embed" id="{{ fid }}-booking" style="--h-m:{{ e.mobile }}px;--h-d:{{ e.desktop }}px;--crop:{{ e.crop }}px">
  <div class="embed-frame"><iframe src="{{ e.src }}?embed=1" title="{{ e.title }}" loading="lazy" allow="clipboard-write"></iframe></div>
  <p class="embed-help">Trouble with the form? <a href="{{ e.src }}" rel="noopener" target="_blank">Open it in a new tab</a> or call {{ site.catering_phone }}.</p>
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
    <div class="btn-row"><a class="btn" href="#quote">Get a catering quote</a><a class="btn btn--ghost" href="tel:{{ tel(site.catering_phone) }}">{{ icons.phone|safe }}{{ site.catering_phone }}</a></div>
  </div>
</section>
<section class="section section--paper" id="quote">
  <div class="wrap two-col">
    <div class="stack">
      <span class="eyebrow">Be at your own party</span>
      <h2>One less thing to worry about.</h2>
      <p class="prose">Hosting is enough work already. Order wood-fired pizza, wings, salads and desserts from us, pick it up hot from your closest Square Peg, and spend the party with your guests instead of in the kitchen.</p>
      <ul class="checks">
        <li>Wood-fired pizzas, wings, salads, pasta & desserts</li>
        <li>Ready for pickup at your closest Square Peg</li>
        <li>Gluten-free crust & vegan cheese on request</li>
        <li>Headcount help, so you never run short</li>
        <li>Available from every Square Peg location</li>
      </ul>
      {{ feature('friends-sharing', 'Friends sharing a Square Peg pizza', 'Wood-fired pies, sized for a crowd') }}
    </div>
    {% with form_title='Get a catering quote', fid='cat', embed_key='catering', submit='Send my request', default_type='Catering pickup' %}{% include "booking_form" %}{% endwith %}
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
      <p class="sr-only"><label>Leave blank <input name="company_website"></label></p>
      <h2>Send us a message</h2>
      <div class="field-row field-row--pair">
        <div class="field"><label for="ct-first">First name</label><input id="ct-first" name="first_name" autocomplete="given-name" required></div>
        <div class="field"><label for="ct-last">Last name</label><input id="ct-last" name="last_name" autocomplete="family-name"></div>
      </div>
      <div class="field-row">
        <div class="field"><label for="ct-email">Email</label><input id="ct-email" type="email" name="email" autocomplete="email" required></div>
        <div class="field"><label for="ct-phone">Phone</label><input id="ct-phone" type="tel" name="phone" autocomplete="tel"></div>
      </div>
      <div class="field-row">
        <div class="field"><label for="ct-topic">Topic</label><select id="ct-topic" name="event_type">{% for t in contact_topics %}<option>{{ t }}</option>{% endfor %}</select></div>
        <div class="field"><label for="ct-loc">Location</label><select id="ct-loc" name="location"><option value="">Not location-specific</option>{% for l in locs %}<option value="{{ l.name }}">{{ l.name }}</option>{% endfor %}</select></div>
      </div>
      <div class="field"><label for="ct-notes">Message</label><textarea id="ct-notes" name="notes" required></textarea></div>
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
    <div class="btn-row"><a class="btn" href="#book">Check truck availability</a><a class="btn btn--ghost" href="{{ u('/catering/') }}">Prefer drop-off catering?</a></div>
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
        <li><div><b>Send the form</b><span>Date, location and a rough headcount.</span></div></li>
        <li><div><b>We confirm & plan the menu</b><span>We’ll match the menu to your crowd and your budget.</span></div></li>
        <li><div><b>The oven rolls up</b><span>We park, fire up and serve. You enjoy your event.</span></div></li>
      </ol>
      <p class="note">Truck dates fill fast from May through October. Book early.</p>
    </div>
    {% with form_title='Book the food truck', fid='truck', embed_key='food_truck', submit='Check availability', default_type='Food truck' %}{% include "booking_form" %}{% endwith %}
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
    <div class="form" style="gap:14px">
      <span class="eyebrow">{{ deal.eyebrow }}</span>
      <h2 style="font-size:clamp(48px,7vw,80px)">{{ deal.headline }}</h2>
      <p style="font-weight:700">{{ deal.expires_label }}, 2026</p>
      <p class="note">{{ deal.detail }}</p>
      <div class="btn-row"><a class="btn" href="{{ site.app_link }}" rel="noopener" data-track="app_click" data-src="deal-card"{{ ext|safe }}>Get the app to unlock</a></div>
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
      <p>Every day, our team makes dough from scratch in our East Hartford kitchen. It’s never frozen. It isn’t the easy way to do it, but it’s the way that gets the head-tilt, the smile and the “wow.”</p>
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
      <span class="eyebrow">Monday–Friday · dine-in</span>
      <h2>Lunch specials. Only $10.</h2>
      <p class="prose" style="color:#e6ddd6">Drink included. Clean. Fast. Tasty. That’s lunch done right.</p>
      <p class="note" style="color:#cfc6bf">{{ promos.lunch_note }}</p>
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

T["entertainment"] = """
<section class="page-head on-dark">
  {{ img('friends-holiday', 'Friends enjoying a night out at Square Peg', eager=True, cls='bg')|safe }}
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{{ u('/') }}">Home</a><span aria-hidden="true">/</span><span>Entertainment</span></nav>
    <span class="eyebrow">Trivia · Bingo · DJ nights</span>
    <h1>Trivia, bingo & live DJ nights</h1>
    <p class="lede">More than dinner. It’s a night out. Weekly entertainment at seven Square Pegs, plus private celebrations any night of the week.</p>
    <div class="btn-row"><a class="btn" href="#lineup">See the weekly lineup</a><a class="btn btn--ghost" href="{{ u('/large-party-reservations/') }}">Reserve for a group</a></div>
  </div>
</section>
<section class="section section--paper" id="tonight">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Happening today</span><h2>Tonight at Square Peg</h2></div>
    <div class="tonight" data-tonight><p class="note">Loading tonight’s lineup…</p></div>
  </div>
</section>
<section class="section" id="lineup">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Every week</span><h2>What’s happening at each Square Peg</h2></div>
    <div class="ent-grid">{% for slug, rows in ent.items() %}{% set l = loc_by_slug[slug] %}<article class="ent-card">
      <header><h3><a href="{{ u('/locations/' ~ slug ~ '/') }}">{{ l.short or l.name }}</a></h3><span class="note">{{ l.city }}, {{ l.state }}</span></header>
      {% for d, e, t in rows %}<div class="ent-row" data-ent-day="{{ d }}"><b>{{ day_names[d] }}</b><span>{{ e }}</span><em>{{ t }}</em></div>{% endfor %}
      <a class="btn btn--sm btn--line" href="{{ u('/locations/' ~ slug ~ '/') }}" aria-label="Hours & directions: Square Peg {{ l.short or l.name }}">Hours & directions</a>
    </article>{% endfor %}</div>
    <p class="note" style="margin-top:20px">Schedules can change for holidays and special events. Call your location to confirm.</p>
    <div class="class-band"><div><span class="eyebrow">Monthly</span><h3>Pizza-making classes</h3><p>Adult classes every month, plus free kids’ classes. Stretch, top and fire your own pie.</p></div><div class="btn-row"><a class="btn" href="{{ site.events_calendar_url }}" target="_blank" rel="noopener" data-track="classes_click" data-src="entertainment">See dates & get tickets</a><a class="btn btn--line" href="{{ u('/private-events/') }}#classes">About the classes</a></div></div>
  </div>
</section>
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
    <div class="section-head"><span class="eyebrow">Pick your kind of party</span><h2>Three ways to celebrate</h2></div>
    <div class="tiles tiles--3">
      <a class="tile on-dark" href="{{ u('/large-party-reservations/') }}">{{ img('dining-room-kids', 'A group celebrating at Square Peg', sizes='(min-width:1000px) 33vw, 100vw')|safe }}<div class="tile-body"><span class="eyebrow">At the restaurant</span><h3>Large party reservations</h3><p>Birthdays, team dinners, showers and reunions.</p><span class="btn">Request a date {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/catering/') }}">{{ img('pizza-boxes', 'Stacked Square Peg pizza boxes', sizes='(min-width:1000px) 33vw, 100vw')|safe }}<div class="tile-body"><span class="eyebrow">At your place</span><h3>Catering</h3><p>Wood-fired pizza for any headcount, ready for pickup.</p><span class="btn">Get a quote {{ icons.arrow|safe }}</span></div></a>
      <a class="tile on-dark" href="{{ u('/food-truck/') }}">{{ img('truck-tent', 'The Square Peg food truck at an event', sizes='(min-width:1000px) 33vw, 100vw')|safe }}<div class="tile-body"><span class="eyebrow">Anywhere</span><h3>The food truck</h3><p>A wood-fired oven on wheels at your event.</p><span class="btn">Book the truck {{ icons.arrow|safe }}</span></div></a>
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
def location_faqs(l):
    name = (l.get("short") or l["name"])
    lines = "; ".join(hours_summary(l))
    return [
        (f"What are Square Peg {name}’s hours?", f"{lines}. Holiday hours may vary; online ordering always shows live availability."),
        (f"Can I order online from Square Peg {name}?", f"Yes. Tap “Order {name} online” to order for pickup, or choose delivery at checkout where it’s available."),
        ("Do you have gluten-free or vegan options?", "Yes. We offer a 12″ gluten-free crust, and vegan cheese can be added to any pizza."),
        (f"Does Square Peg {name} do catering?", f"Yes. {name} caters birthdays, office lunches, team events and more. Send a quick request on our catering page, or call {l['phone']}."),
        (f"Is Square Peg {name} close to {l['nearby'][0]} and {l['nearby'][1]}?", f"Yes. Square Peg {name} at {l['street']} in {l['city']} is a short drive from {', '.join(l['nearby'][:-1])} and {l['nearby'][-1]}. Order ahead online for pickup, or check delivery availability at checkout."),
        ("Can our group host a fundraiser here?", "Yes. Every Tuesday from 4pm to close, one organization earns 20% of dine-in food sales from its supporters."),
    ]

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    build_images()
    logo_ratio = build_brand()
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
        "lat": l["lat"], "lng": l["lng"], "hours": l["hours"], "region": l["region"]} for l in LOCATIONS], separators=(",", ":"))
    cfg_json = json.dumps({"chatSrc": "" if PREVIEW else SITE["chat_src"], "chatId": SITE["chat_widget_id"], "locationsUrl": url("/locations/"),
                           "supabaseUrl": SITE.get("supabase_url", ""), "supabaseKey": SITE.get("supabase_anon_key", ""), "thanksUrl": url("/thanks/")})

    analytics = ""
    if SITE["ga4_id"]:
        analytics += f'<script async src="https://www.googletagmanager.com/gtag/js?id={SITE["ga4_id"]}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{SITE["ga4_id"]}");</script>'
    if SITE["meta_pixel_id"]:
        analytics += ("<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};"
                      "if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];"
                      "s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
                      f"fbq('init','{SITE['meta_pixel_id']}');fbq('track','PageView');</script>")

    base_ctx = dict(
        u=url, tel=tel, order=order_url, hero_picture=hero_picture, drawer_extra=DRAWER_EXTRA, drawer_groups=DRAWER_GROUPS, more=MORE, ent=ENTERTAINMENT, day_names=DAY_NAMES, promos=PROMOS, loc_by_slug={l["slug"]: l for l in LOCATIONS}, embeds=EMBEDS, contact_topics=CONTACT_TOPICS, maps=maps_url, embed=maps_embed, img=img, icons=ICONS, nav=NAV,
        site=SITE, locs=LOCATIONS, regions=REGIONS, deal=DEAL, points=POINTS, perks=APP_PERKS,
        sigs=SIGNATURES, reviews=REVIEWS, preview=PREVIEW, css=css, jsv=jsv, locs_json=locs_json, cfg_json=cfg_json,
        year=date.today().year, analytics=analytics, ent_json=json.dumps({l["slug"]: {"name": l.get("short") or l["name"], "url": url(f"/locations/{l['slug']}/"), "events": ENTERTAINMENT.get(l["slug"], [])} for l in LOCATIONS if ENTERTAINMENT.get(l["slug"])}, separators=(",", ":")), logo_ratio=logo_ratio, imgbase="img/" if PREVIEW else "/img/",
        ext=' target="_blank"' if PREVIEW else "", staging=STAGING,
        event_types=["Catering pickup", "Food truck", "Party at the restaurant", "Corporate / office", "School or team event", "Wedding or large event"],
    )

    pages = []  # (path, title, desc, body_template, extra ctx, schema, og, hero)

    pages.append(("/", "Square Peg Pizzeria | Wood-Fired Pizza in CT & Delray Beach",
                  "Wood-fired pizza made fresh daily at 10 Square Peg Pizzeria locations in CT and Delray Beach, FL. Order pickup or delivery, or book catering and our food truck.",
                  "home", {}, org_schema(), "margherita-board", None))
    pages.append(("/locations/", "Pizza Near You: 10 Square Peg Pizzeria Locations in CT & FL",
                  "Square Peg Pizzeria in Glastonbury, East Hartford, Vernon, Bolton, Storrs, Preston, Plainville, Berlin, Shelton, CT and Delray Beach, FL. Hours & ordering.",
                  "locations", {}, graph(breadcrumbs([("Home", "/"), ("Locations", "/locations/")]),
                  {"@type": "ItemList", "name": "Square Peg Pizzeria locations", "itemListElement": [
                      {"@type": "ListItem", "position": i + 1, "url": abs_url(f"/locations/{l['slug']}/"), "name": f"Square Peg Pizzeria {l.get('short') or l['name']}"} for i, l in enumerate(LOCATIONS)]}), "margherita-board", None))

    for l in LOCATIONS:
        name = l.get("short") or l["name"]
        others = sorted([o for o in LOCATIONS if o is not l], key=lambda o: (o["lat"] - l["lat"]) ** 2 + (o["lng"] - l["lng"]) ** 2)[:3]
        faqs = location_faqs(l)
        schema = graph(restaurant_schema(l), breadcrumbs([("Home", "/"), ("Locations", "/locations/"), (l["name"], f"/locations/{l['slug']}/")]), faq_schema(faqs))
        title = f"Wood-Fired Pizza in {l['city']}, {l['state']} | Square Peg Pizzeria"
        desc = f"Wood-fired pizza in {l['city']}, {l['state']} at {l['street']}. See hours, call {l['phone']}, and order pickup or delivery from Square Peg Pizzeria {name}."
        pages.append((f"/locations/{l['slug']}/", title, desc, "location",
                      dict(l=l, rows=hours_rows(l), near=others, faqs=faqs), schema, l["photo"], l["photo"]))

    pages.append(("/catering/", "Pizza Catering in Connecticut | Square Peg Pizzeria",
                  "Wood-fired pizza catering for parties, offices, schools and events from all 10 Square Peg Pizzeria locations. Get a quote in 60 seconds.",
                  "catering", dict(faqs=CATERING_FAQ), graph(faq_schema(CATERING_FAQ), breadcrumbs([("Home", "/"), ("Catering", "/catering/")])), "table-spread", "table-spread"))
    pages.append(("/large-party-reservations/", "Large Party & Group Reservations | Square Peg Pizzeria",
                  "Reserve for a big group at any Square Peg Pizzeria in CT or Delray Beach, FL. Birthdays, team dinners, showers and reunions with wood-fired pizza.",
                  "parties", dict(faqs=LARGE_PARTY_FAQ), graph(faq_schema(LARGE_PARTY_FAQ), breadcrumbs([("Home", "/"), ("Large Parties", "/large-party-reservations/")])), "friends-holiday", "friends-holiday"))
    pages.append(("/contact/", "Contact Us | Square Peg Pizzeria",
                  "Contact Square Peg Pizzeria: phone numbers for all 10 locations, email, and a message form for catering, large parties, gift cards, jobs and more.",
                  "contact", {}, graph({"@type": "ContactPage", "url": abs_url("/contact/"), "name": "Contact Square Peg Pizzeria",
                                        "about": {"@id": ORG_ID}},
                                       {"@type": "Organization", "@id": ORG_ID, "name": SITE["name"], "email": SITE["email"],
                                        "contactPoint": [{"@type": "ContactPoint", "contactType": "customer service", "email": SITE["email"], "telephone": tel(SITE["catering_phone"]), "areaServed": ["US-CT", "US-FL"], "availableLanguage": "en"}]},
                                       breadcrumbs([("Home", "/"), ("Contact", "/contact/")])), None, None))
    pages.append(("/promotions/", "Pizza Specials, $10 Lunch & App Rewards | Square Peg Pizzeria",
                  "Square Peg Pizzeria specials: Tuesday pasta night, $1 wings Wednesday, half-price wine Friday, $10 weekday lunch, app rewards, punch cards and 15% off for heroes.",
                  "promotions", {}, graph(breadcrumbs([("Home", "/"), ("Specials", "/promotions/")])), "oven-pizza", "oven-pizza"))
    pages.append(("/entertainment/", "Trivia, Bingo & DJ Nights | Square Peg Pizzeria",
                  "Weekly trivia, bingo and DJ nights at Square Peg Pizzeria in Plainville, Shelton, East Hartford, Glastonbury, Preston, Storrs and Delray Beach.",
                  "entertainment", {}, graph(breadcrumbs([("Home", "/"), ("Entertainment", "/entertainment/")])), "friends-holiday", "friends-holiday"))
    pages.append(("/private-events/", "Private Events & Pizza-Making Classes | Square Peg Pizzeria",
                  "Plan a private event at Square Peg Pizzeria, and join our monthly pizza-making classes for adults plus free kids' classes. Parties, catering and the food truck.",
                  "private_events", {}, graph(breadcrumbs([("Home", "/"), ("Private Events & Classes", "/private-events/")])), "table-spread", "table-spread"))
    pages.append(("/careers/", "Careers: Now Hiring | Square Peg Pizzeria",
                  "Join the Square Peg Pizzeria crew. Now hiring managers, servers, bartenders, kitchen staff and pizza cooks at locations across Connecticut and Delray Beach, FL.",
                  "careers", {}, graph(breadcrumbs([("Home", "/"), ("Careers", "/careers/")])), "oven-fire", "oven-fire"))
    pages.append(("/food-truck/", "Wood-Fired Pizza Food Truck for Events in CT | Square Peg",
                  "Book the Square Peg Pizzeria wood-fired pizza food truck for backyard parties, weddings, schools, breweries and corporate events in Connecticut.",
                  "truck", {}, graph(breadcrumbs([("Home", "/"), ("Food Truck", "/food-truck/")])), "food-truck", "food-truck"))
    pages.append(("/deals/", "Pizza Deals & Rewards | Square Peg Pizzeria",
                  f"This month at Square Peg: {DEAL['headline']} for loyalty members. Join free in the app and earn points toward free pizza, pasta and reward cards.",
                  "deals", {}, graph(breadcrumbs([("Home", "/"), ("Deals & Rewards", "/deals/")])), "pizza-boxes", "pizza-boxes"))
    pages.append(("/fundraisers/", "Tuesday Night Restaurant Fundraisers | Square Peg Pizzeria",
                  "Earn 20% of dine-in food sales for your school, team or nonprofit with a Square Peg Pizzeria Tuesday Night Fundraiser. Request your date.",
                  "fundraisers", dict(faqs=FUNDRAISER_FAQ), graph(faq_schema(FUNDRAISER_FAQ), breadcrumbs([("Home", "/"), ("Fundraisers", "/fundraisers/")])), "team-kids", "dining-room-kids"))
    pages.append(("/about/", "Our Story | Square Peg Pizzeria",
                  "Square Peg Pizzeria was started by UConn alumni in Glastonbury in 2020. Dough made from scratch daily, never frozen, and a whole lot of Be Nice.",
                  "about", {}, graph(breadcrumbs([("Home", "/"), ("Our Story", "/about/")])), "dough", "dough"))
    pages.append(("/roll-the-dice/", "Roll the Dice: Win Free Pizza at Lunch | Square Peg Pizzeria",
                  "Order any appetizer Monday–Thursday before 4pm at Square Peg Pizzeria, roll two dice, and win a free small cheese pizza or a $20 gift card.",
                  "dice", dict(dice=DICE), graph(breadcrumbs([("Home", "/"), ("Roll the Dice", "/roll-the-dice/")])), "table-spread", "table-spread"))
    pages.append(("/sms-terms/", "SMS Terms | Square Peg Pizzeria", "Terms for the Square Peg Pizzeria text message program: frequency, costs, how to opt out, and support.",
                  "sms", dict(sms=SMS_TERMS), None, None, None))
    pages.append(("/thanks/", "Thank You | Square Peg Pizzeria", "Thanks for reaching out to Square Peg Pizzeria.", "simple",
                  dict(eyebrow="Request received", h1="Thank you!", lede="We got your request and will get back to you within one business day. While you wait, there’s pizza.", prose=""), None, None, None))
    pages.append(("/privacy/", "Privacy | Square Peg Pizzeria", "How Square Peg Pizzeria handles information you share on this website.", "simple",
                  dict(eyebrow="Privacy", h1="Privacy notice", lede="Plain-language summary of how this website handles your information.",
                       prose="<p><strong>DRAFT, to be reviewed before launch.</strong></p><p>When you send a catering, food truck or fundraiser request, we use your name, email, phone and event details only to respond and plan your event.</p><p>Online orders are processed by our ordering provider, Toast, under its own <a href='https://pos.toasttab.com/privacy' rel='noopener'>privacy statement</a>. Rewards are managed in the Square Peg app.</p><p>This site may use analytics and advertising cookies to understand visits and measure our ads. You can block cookies in your browser settings.</p><p>Questions? Call any Square Peg location.</p>"),
                  None, None, None))
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
            key = "home" if path == "/" else path.strip("/").replace("/", "-")
            og_url = make_og(key, og or "margherita-board", eyebrow, head_txt, sub)
            og_alt = head_txt if "Square Peg" in head_txt else f"{head_txt} | Square Peg Pizzeria"
        ctx.update(title=title, desc=desc, body=body, canonical=abs_url(path if path != "/404.html" else "/"),
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
            if path in ("/thanks/",):
                doc = doc.replace('<meta name="description"', '<meta name="robots" content="noindex"><meta name="description"', 1)
            dest = OUT / (path.lstrip("/") if path.endswith(".html") else path.lstrip("/") + "index.html")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(doc)

    if PREVIEW:
        build_preview(rendered, base_ctx, js)
    else:
        import subprocess
        try:
            mini = subprocess.run(["/tmp/fs/node_modules/.bin/terser", "-c", "-m"], input=js, capture_output=True, text=True, timeout=60)
            (OUT / "site.js").write_text(mini.stdout if mini.returncode == 0 and mini.stdout.strip() else js)
        except Exception:
            (OUT / "site.js").write_text(js)
        write_extras([p for p in pages if p[0] not in ("/404.html", "/thanks/")])
    print(f"  pages: {len(rendered)} -> {OUT}")

def write_extras(pages):
    urls = "".join(f"<url><loc>{abs_url(p[0])}</loc><lastmod>{TODAY}</lastmod></url>" for p in pages)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    bots = ["Googlebot", "Bingbot", "Applebot", "Google-Extended", "Applebot-Extended", "GPTBot", "OAI-SearchBot", "ChatGPT-User",
            "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User", "CCBot", "Amazonbot", "DuckAssistBot"]
    robots = "# Search engines and AI assistants are welcome to read this site.\n"
    robots += "".join(f"User-agent: {b}\n" for b in bots) + "Allow: /\nDisallow: /thanks/\n\n"
    robots += "User-agent: *\nAllow: /\nDisallow: /thanks/\n\n" + f"Sitemap: {abs_url('/sitemap.xml')}\n"
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
        "/img/*",
        "  Cache-Control: public, max-age=31536000, immutable",
        "/fonts/*",
        "  Cache-Control: public, max-age=31536000, immutable",
        "/*.html",
        "  Cache-Control: public, max-age=0, must-revalidate",
        "",
    ]))
    (OUT / "netlify.toml").write_text('[build]\n  publish = "."\n\n[build.processing.html]\n  pretty_urls = true\n')

ORDER_HOST = "https://order.squarepegpizzeria.com"

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
        ("/privacy-policy", "/privacy/"), ("/terms", "/privacy/"),
        # Toast-powered pages -> Toast on the order subdomain (same paths, so every deep link keeps working)
        ("/order", ORDER_HOST + "/order"), ("/order/*", ORDER_HOST + "/order/:splat"),
        ("/menu", ORDER_HOST + "/menu"), ("/menu/*", ORDER_HOST + "/menu/:splat"),
        ("/account/*", ORDER_HOST + "/account/:splat"), ("/checkout/*", ORDER_HOST + "/checkout/:splat"),
        ("/cart/*", ORDER_HOST + "/cart/:splat"), ("/confirm/*", ORDER_HOST + "/confirm/:splat"),
    ]
    # Redirects that already exist on the old Toast site (Toast > Website > Path redirects), pointed straight at their new homes
    m += [("/party-request", "/large-party-reservations/"), ("/popmenu-order", ORDER_HOST + "/menu"),
          ("/events/*", "/entertainment/")]
    for l in LOCATIONS:
        town = l["city"].lower().replace(" ", "-")
        m.append((f"/menu-{town}", ORDER_HOST + "/order/" + l["toast"]))
    gc = SITE["gift_cards_url"]
    target = gc if not gc.startswith(SITE["domain"]) else ORDER_HOST + "/gift-cards"
    m += [("/gift-card", target), ("/gift-cards", target)]
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
            # /order/anything, plus the bare /order/ that Vercel's trailing-slash step can produce
            redirects.append({"source": base + "/:path*", "destination": dst, "permanent": True})
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
            {"key": "Content-Security-Policy", "value": "frame-ancestors 'self'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests"},
            {"key": "Cross-Origin-Opener-Policy", "value": "same-origin-allow-popups"},
            {"key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains"}]
            + ([{"key": "X-Robots-Tag", "value": "noindex, nofollow"}] if STAGING else [])},
        {"source": "/img/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
        {"source": "/fonts/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
    ]
    return {"$schema": "https://openapi.vercel.sh/vercel.json", "trailingSlash": True, "cleanUrls": False,
            "redirects": redirects, "headers": headers}

def llms_txt():
    out = ["# Square Peg Pizzeria", "", "> Wood-fired pizza made from scratch daily, with 10 locations in Connecticut and Delray Beach, Florida. Online ordering for pickup and delivery, catering, a wood-fired food truck, Tuesday night fundraisers, and a rewards app.", "",
           "## Locations"]
    for l in LOCATIONS:
        out.append(f"- [{l['name']}]({abs_url('/locations/' + l['slug'] + '/')}): {l['street']}, {l['city']}, {l['state']} {l['zip']} · {l['phone']} · order: {order_url(l)}")
    out += ["", "## Pages",
            f"- [Catering]({abs_url('/catering/')})", f"- [Large party reservations]({abs_url('/large-party-reservations/')})", f"- [Contact]({abs_url('/contact/')})", f"- [Food truck]({abs_url('/food-truck/')})", f"- [Deals & rewards]({abs_url('/deals/')})",
            f"- [Tuesday fundraisers]({abs_url('/fundraisers/')})", f"- [Our story]({abs_url('/about/')})", ""]
    return "\n".join(out)

SAFE_CLASSES = {"open", "menu-open", "is-open", "is-closed", "is-soon", "is-today", "is-near", "is-pref", "is-sized",
                "pick", "pick-name", "pick-addr", "pick-meta", "pick-call", "tonight-card", "note", "status", "btn", "btn--sm", "sp-embed", "today"}

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
