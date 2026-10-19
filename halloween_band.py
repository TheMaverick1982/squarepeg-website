"""The decorative band for the top of the costume contest email.

Email clients can't be given the page's CSS animations, pseudo-elements or
inline SVG — Outlook's Word engine renders none of it — so the page's own
artwork is composed into one flat image instead. The spider, ghost and web
paths below are copied from HW_ART in build.py, so the email is decorated with
the same drawings as the page rather than lookalikes.

Rendered as PNG, not JPEG: these are hard white edges on flat black, which is
exactly what JPEG rings around.

Run: python3 halloween_band.py
"""
import pathlib

import cairosvg
from PIL import Image

W, H = 1000, 200           # displays at 500x100 in the 500px canvas
INK = "#000000"            # must match the hero cell's bgcolor exactly

SPIDER = (
    '<g stroke="{c}" stroke-width="2.6" stroke-linecap="round" fill="none">'
    '<path d="M26 26 14 18 4 22"/><path d="M26 31 12 31 3 37"/>'
    '<path d="M26 36 13 43 6 51"/><path d="M27 22 20 12 22 4"/>'
    '<path d="M38 26 50 18 60 22"/><path d="M38 31 52 31 61 37"/>'
    '<path d="M38 36 51 43 58 51"/><path d="M37 22 44 12 42 4"/></g>'
    '<ellipse cx="32" cy="33" rx="11" ry="13" fill="{c}"/>'
    '<circle cx="32" cy="19" r="7" fill="{c}"/>'
    '<circle cx="29" cy="18" r="1.8" fill="#fff"/>'
    '<circle cx="35" cy="18" r="1.8" fill="#fff"/>'
)

GHOST = (
    '<path fill="{c}" d="M50 6c22 0 38 16 38 38v54c-5 0-8-6-12-6s-6 6-11 6-7-6-11-6'
    '-6 6-10 6-6-6-10-6-7 6-12 6V44C22 22 28 6 50 6z"/>'
    '<ellipse cx="38" cy="44" rx="6" ry="8" fill="#000"/>'
    '<ellipse cx="62" cy="44" rx="6" ry="8" fill="#000"/>'
    '<ellipse cx="50" cy="64" rx="7" ry="9" fill="#000" opacity=".75"/>'
)

WEB = ("M0 0L100.0 0.0M0 0L95.1 30.9M0 0L80.9 58.8M0 0L58.8 80.9M0 0L30.9 95.1"
       "M0 0L0.0 100.0M26.0 0.0Q19.3 3.1 24.7 8.0M24.7 8.0Q17.4 8.9 21.0 15.3"
       "M21.0 15.3Q13.8 13.8 15.3 21.0M15.3 21.0Q8.9 17.4 8.0 24.7"
       "M8.0 24.7Q3.1 19.3 0.0 26.0M46.0 0.0Q34.2 5.4 43.7 14.2"
       "M43.7 14.2Q30.8 15.7 37.2 27.0M37.2 27.0Q24.5 24.5 27.0 37.2"
       "M27.0 37.2Q15.7 30.8 14.2 43.7M14.2 43.7Q5.4 34.2 0.0 46.0"
       "M66.0 0.0Q49.0 7.8 62.8 20.4M62.8 20.4Q44.2 22.5 53.4 38.8"
       "M53.4 38.8Q35.1 35.1 38.8 53.4M38.8 53.4Q22.5 44.2 20.4 62.8"
       "M20.4 62.8Q7.8 49.0 0.0 66.0M88.0 0.0Q65.4 10.4 83.7 27.2"
       "M83.7 27.2Q59.0 30.1 71.2 51.7M71.2 51.7Q46.8 46.8 51.7 71.2"
       "M51.7 71.2Q30.1 59.0 27.2 83.7M27.2 83.7Q10.4 65.4 0.0 88.0")


def place(body, x, y, scale, opacity=1.0, flip=False):
    """x,y is the top-left of the drawing. A flipped piece mirrors about x, so
    it grows leftwards — pass the right edge, not the left."""
    t = (f"translate({x} {y}) scale({-scale} {scale})" if flip
         else f"translate({x} {y}) scale({scale})")
    return f'<g transform="{t}" opacity="{opacity}">{body}</g>'


# A web in each top corner, two ghosts drifting, and the spider on a thread
# dropped from the top edge — the same cast as the page's contest section.
parts = [
    f'<rect width="{W}" height="{H}" fill="{INK}"/>',
    place(f'<path d="{WEB}" fill="none" stroke="#FFFFFF" stroke-width="1.4"/>',
          0, 0, 1.35, opacity=0.30),
    place(f'<path d="{WEB}" fill="none" stroke="#FFFFFF" stroke-width="1.4"/>',
          W, 0, 1.35, opacity=0.30, flip=True),

    # three ghosts, drifting at different depths: the near one lit, the far one
    # barely there, and one in the page's pumpkin orange to tie them together
    place(GHOST.format(c="#FFFFFF"), 196, 44, 1.05, opacity=0.90),
    place(GHOST.format(c="#F2761B"), 470, 26, 0.50, opacity=0.80),
    place(GHOST.format(c="#FFFFFF"), 622, 76, 0.62, opacity=0.42),

    # the spider hangs off the top edge, as it does on the page
    f'<line x1="836" y1="0" x2="836" y2="94" stroke="#FFFFFF" '
    f'stroke-width="1.6" opacity="0.5"/>',
    place(SPIDER.format(c="#FFFFFF"), 796, 90, 1.25, opacity=0.95),
]


svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}">' + "".join(parts) + "</svg>")

out = pathlib.Path("out/halloween-band.png")
out.parent.mkdir(exist_ok=True)
cairosvg.svg2png(bytestring=svg.encode(), write_to=str(out),
                 output_width=W, output_height=H)

im = Image.open(out).convert("RGB")
im.save(out)

# the band has to blend into the hero cell, so its ground must be exactly #000
assert im.getpixel((2, H - 2)) == (0, 0, 0), (
    f"band corner is {im.getpixel((2, H - 2))}, not pure black — it will show a seam")
ink = sum(1 for p in im.get_flattened_data() if p != (0, 0, 0)) / (W * H)
assert 0.02 < ink < 0.30, f"decoration covers {ink:.1%} of the band — check the layout"
print(f"wrote {out}  {W}x{H}  {ink:.1%} ink  {out.stat().st_size // 1024}KB")
