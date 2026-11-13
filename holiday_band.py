"""The holiday artwork behind the events band on the home page.

The band works the way the gift card one does -- a photo-sized image with a
dark gradient over it and the copy on top -- but there is no holiday photo in
the library, and the one holiday-ish shot we do have is 600px wide, which is
not enough to run full width behind a band. So it is drawn instead, the same
way halloween-band.png and the hero art were.

Deep red rather than the gift card band's green: the two run on the same page
a few hundred pixels apart, and the point of this band is to NOT look like its
neighbours. Everything sits under a gradient in the end, so this is texture
and warmth, not detail.

Run:  python3 holiday_band.py
Out:  assets/img-src/holiday-band.png  (rebuild the site to publish it)
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 2000, 560
OUT = Path(__file__).parent / "assets" / "img-src" / "holiday-band.png"

DEEP = (26, 9, 10)        # the ground, top
WARM = (58, 16, 17)       # the ground, bottom
FLAME = (255, 181, 36)
CREAM = (251, 246, 236)
EMBER = (214, 27, 36)


def ground(im):
    """A vertical wash, warmer at the foot, so the band is not a flat colour."""
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)],
               fill=tuple(round(DEEP[i] + (WARM[i] - DEEP[i]) * t) for i in range(3)))


def glow(size, color, strength=1.0):
    """One soft ball of light, as its own layer to be pasted with screen-ish add."""
    g = Image.new("RGB", (size, size), (0, 0, 0))
    d = ImageDraw.Draw(g)
    steps = 18
    for i in range(steps, 0, -1):
        r = size / 2 * i / steps
        a = (1 - i / steps) ** 2.2 * strength
        d.ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r],
                  fill=tuple(round(c * a) for c in color))
    return g.filter(ImageFilter.GaussianBlur(size / 14))


def swag(im, y0, sag, bulbs, size, phase=0.0):
    """A string of lights hung across the band.

    Two passes: the glow is added to the picture so the light spills into the
    ground the way a bulb does, then the bulb itself is drawn on top of it.
    """
    d = ImageDraw.Draw(im)
    pts = [(x, y0 + sag * math.sin(math.pi * (x / W + phase) % math.pi))
           for x in range(0, W + 1, 12)]
    d.line(pts, fill=(78, 40, 30), width=3)

    for i in range(bulbs + 1):
        x = W * i / bulbs
        y = y0 + sag * math.sin(math.pi * (x / W + phase) % math.pi)
        color = FLAME if i % 2 == 0 else CREAM if i % 4 == 1 else EMBER
        g = glow(size * 7, color, 0.55)
        box = (round(x - g.width / 2), round(y - g.height / 2))
        patch = im.crop((box[0], box[1], box[0] + g.width, box[1] + g.height))
        if patch.size == g.size:
            im.paste(Image.blend(patch, Image.new("RGB", g.size, (0, 0, 0)), 0)
                     .point(lambda v: v), box)
            im.paste(_add(patch, g), box)
        d.line([(x, y - size * 0.9), (x, y)], fill=(78, 40, 30), width=3)
        d.ellipse([x - size / 2, y, x + size / 2, y + size * 1.25], fill=color)


def _add(a, b):
    from PIL import ImageChops
    return ImageChops.add(a, b)


def bokeh(im, seed=7):
    """Out-of-focus lights in the deep background, for depth."""
    import random
    rnd = random.Random(seed)
    for _ in range(46):
        x, y = rnd.uniform(0, W), rnd.uniform(60, H)
        r = rnd.uniform(10, 46)
        color = FLAME if rnd.random() < 0.6 else EMBER
        g = glow(round(r * 6), color, rnd.uniform(0.10, 0.26))
        box = (round(x - g.width / 2), round(y - g.height / 2))
        patch = im.crop((box[0], box[1], box[0] + g.width, box[1] + g.height))
        if patch.size == g.size:
            im.paste(_add(patch, g), box)


def main():
    im = Image.new("RGB", (W, H), DEEP)
    ground(im)
    bokeh(im)
    swag(im, 86, 54, 13, 20)
    swag(im, 28, 38, 9, 15, phase=0.35)
    im = im.filter(ImageFilter.SMOOTH)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT)
    print("  ", OUT.relative_to(Path(__file__).parent), im.size)


if __name__ == "__main__":
    main()
