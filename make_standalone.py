#!/usr/bin/env python3
"""Builds one self-contained HTML file (images + fonts embedded) that opens by double-clicking."""
import re, base64
from pathlib import Path
ROOT = Path(__file__).parent
src = (ROOT / "preview" / "square-peg-site.html").read_text()

def b64(p, mime):
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()

# 1) one image per <picture>: drop <source> tags, drop srcset/sizes on <img>
# keep art-directed <source media=...> (hero): one file each, filled in by script; drop the rest
def keep_media(m):
    tag = m.group(0)
    if "media=" not in tag or 'type="image/webp"' not in tag:
        return ""
    first = re.search(r'srcset="img/([^ "]+)', tag).group(1)
    last = re.findall(r'img/([^ ",]+)', tag)[-1]
    return re.sub(r'srcset="[^"]*"', f'data-emb-srcset="{last}"', tag)
html = re.sub(r"<source [^>]*>", keep_media, src)
html = re.sub(r'\s(?:srcset|sizes)="[^"]*"', "", html)
# 2) embed every img/... reference
cache = {}
def emb(m):
    f = m.group(1)
    if f not in cache:
        cache[f] = b64(ROOT / "preview" / "img" / f, "image/webp")
    return f'data-emb="{f}"'
html = re.sub(r'src="img/([^"]+)"', emb, html)
for f in re.findall(r'data-emb-srcset="([^"]+)"', html):
    cache.setdefault(f, b64(ROOT / "preview" / "img" / f, "image/webp"))
# each image is stored once and filled in on load (images repeat across pages)
import json
html += ("<script>(function(){var I=" + json.dumps(cache) + ";"
         "document.querySelectorAll('source[data-emb-srcset]').forEach(function(s){s.srcset=I[s.getAttribute('data-emb-srcset')];});"
         "document.querySelectorAll('img[data-emb]').forEach(function(i){i.src=I[i.getAttribute('data-emb')];});})();</script>")
# 3) fonts embedded (no internet needed)
html = re.sub(r'<link rel="preconnect"[^>]*>', "", html)
html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>', "", html)
faces = [("Big Shoulders Display", "big-shoulders-display", w) for w in (800, 900)] + [("Figtree", "figtree", w) for w in (400, 600, 700, 800)]
css = "".join(f'@font-face{{font-family:"{n}";font-weight:{w};font-style:normal;font-display:swap;src:url({b64(ROOT/"src"/"fonts"/f"{s}-latin-{w}-normal.woff2","font/woff2")}) format("woff2")}}' for n, s, w in faces)
html = html.replace("<style>", "<style>" + css, 1)
# 4) full document wrapper
title = re.search(r"<title>.*?</title>", html).group(0)
html = html.replace(title, "", 1)
doc = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
       '<title>Square Peg Pizzeria: New Website Preview</title><meta name="robots" content="noindex">'
       + html.replace("<header class=\"site-header\">", "</head><body><header class=\"site-header\">", 1)
       + "\n</body></html>\n")
# head content must precede body: move the skip link after <body>
doc = doc.replace('<a class="skip" href="#main">Skip to content</a>\n</head><body>', '</head><body><a class="skip" href="#main">Skip to content</a>\n', 1)
out = ROOT / "Square-Peg-Website-Preview.html"
out.write_text(doc)
print(out, round(out.stat().st_size / 1e6, 2), "MB", len(cache), "images")
