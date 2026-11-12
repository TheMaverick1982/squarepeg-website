"""Lift each float glass off its dark tile in the source menu.

The tiles are a dark warm brown and the glasses are far brighter, so a
luminance ramp separates them with no halo on a light ground. What luminance
alone does NOT separate is the neon border around each tile, the cream name
plates under the kids' drinks and the red price badges -- all bright too. So the
work is done with two thresholds and a handful of shape tests; see cut().

Regenerate after changing anything here:  python3 tools/float_glasses.py
Source artwork: src/floats-src.png. Output: src/floats/<drink>.png
"""
from PIL import Image
import numpy as np
from pathlib import Path

from scipy import ndimage

SRC_FILE = Path(__file__).resolve().parent.parent / "src" / "floats-src.png"
SRC = Image.open(SRC_FILE).convert("RGB")
OUT = Path(__file__).resolve().parent.parent / 'src' / 'floats'
OUT.mkdir(exist_ok=True)

# Generous search boxes: the whole tile, trimmed only where something bright
# that is NOT separate from the glass would otherwise merge with it -- the
# kids' name plates sit against the glass base, so those stop above the plate.
F = 3    # a thin frame blanked so a border hugging the box edge cannot win

# Pixels shaved off the base, where a sliver of the tile's lit band is
# welded to the glass and no width test separates it.
MIRROR = {"dragon", "blueberry", "coconut"}

TRIM_TOP = {"baileys": 13}   # a slab of tile glow sits over this scoop

TRIM = {"baileys": 12, "jackcoke": 9, "createsoda": 9, "jager": 5,
        "blueberry": 11}

BOXES = {
    # (search box, price-badge corner to punch out or None). Boxes stop short
    # of the tile's neon border, the drink name and the kids' name plates --
    # all bright, any of them inside the box and the blob test picks wrong.
    # A badge only needs punching out where it actually touches a glass: the
    # corner given is below and right of where that glass has tapered to.
    "jager":      ((120, 382, 257, 760), None),
    "dragon":     ((306, 292, 436, 500), (401, 437)),
    "blueberry":  ((599, 292, 729, 500), (694, 437)),
    "coconut":    ((891, 292, 1021, 500), (987, 437)),
    "pumpkin":    ((318, 506, 508, 681), (456, 610)),
    "baileys":    ((744, 506, 934, 681), (880, 610)),
    "jackcoke":   ((318, 690, 476, 847), None),
    "createsoda": ((744, 690, 902, 847), None),
    "cola":       ((54, 944, 290, 1056), None),
    "sprite":     ((332, 944, 568, 1056), None),
    "dietcoke":   ((610, 944, 846, 1056), None),
    "rootbeer":   ((888, 944, 1124, 1056), None),
}


def span_fill(sil):
    """Fill each row between its leftmost and rightmost pixel.

    Every glass here -- tumbler, pint, martini -- is a single solid span at
    any height, bowl, stem and foot alike. So this closes the bites that the
    unlit cola and the darker scallops leave behind, and it cannot invent
    anything outside the glass's own outline.
    """
    out = np.zeros_like(sil)
    cols = np.arange(sil.shape[1])[None, :]
    has = sil.any(axis=1)
    left = np.where(has, sil.argmax(axis=1), 0)[:, None]
    right = np.where(has, sil.shape[1] - 1 - sil[:, ::-1].argmax(axis=1), -1)[:, None]
    out[:] = (cols >= left) & (cols <= right) & has[:, None]
    return out


def biggest(sil):
    """Keep only the largest piece, so a stray scrap of tile cannot be widened
    into a bar by the row fill below."""
    lab, n = ndimage.label(sil)
    if n < 2:
        return sil
    sizes = [((lab == i).sum() if i else 0, i) for i in range(n + 1)]
    return lab == max(sizes)[1]


def drop_shelf(sil):
    """Cut the tile's glow band off the bottom of a glass.

    Each drink sits on a lit band that runs the width of its tile and touches
    the base, and it survives every test that looks at brightness or at what
    the glass connects to. What gives it away is width: far wider than the
    foot it is stuck to. Only the bottom is trimmed this way -- on a martini
    the widest row IS the top one, and trimming by width there eats the bowl.
    """
    span = sil.sum(axis=1)
    rows = np.flatnonzero(span)
    if not len(rows):
        return sil
    top, bot = rows[0], rows[-1]
    body = span[top + int((bot - top) * 0.45):top + int((bot - top) * 0.85)]
    if not (body > 0).any():
        return sil
    limit = np.median(body[body > 0]) * 1.22

    lo = bot
    while lo > top and span[lo] > limit:
        lo -= 1
    out = sil.copy()
    out[lo + 1:] = False
    return out


def cut(box, tag=None, trim=0, mirror=False, trim_top=0):
    c = SRC.crop(box)
    a = np.asarray(c).astype(float)
    lum = a.max(axis=2)

    # A luminance ramp was letting the tile's glow through as a brown haze
    # around every glass, because the tile sits at 37-54 and the glow runs
    # straight up from there. So the alpha is a silhouette instead: find the
    # glass well above the tile (everything that belongs to a glass is 227+),
    # fill it, and feather the edge by a pixel. The dark cola inside a glass
    # survives because it is enclosed; the price badges, the neon borders and
    # the kids' name plates do not, because each is its own smaller blob.
    # Two thresholds, each doing one job. The high one finds the glass
    # reliably -- everything that belongs to a glass peaks at 227+, so the
    # biggest bright blob in the box is always the drink. But a tumbler of
    # cola is mostly DARK, and filling that bright blob leaves a ragged base
    # where the unlit liquid was never enclosed. So the silhouette comes from
    # the low threshold instead, just above the tile's 37-54: that outlines
    # the whole glass, dark liquid included. The high blob only says which of
    # the low blobs is the drink.
    hi = lum > 140
    hi[:F, :] = hi[-F:, :] = False
    hi[:, :F] = hi[:, -F:] = False
    lab, n = ndimage.label(hi)
    sizes = [((lab == i).sum() if i else 0, i) for i in range(n + 1)]
    best, which = max(sizes)
    if not best:
        raise SystemExit(f"no glass found in {box}")
    seed = lab == which

    lab2, _ = ndimage.label(lum > 85)
    ids, counts = np.unique(lab2[seed], return_counts=True)
    ids, counts = ids[ids > 0], counts[ids > 0]
    if not len(ids):
        raise SystemExit(f"no outline found in {box}")

    # The low threshold also reaches the glow shelf under each tile and the
    # price badge beside it, both of which touch the glass. Keeping only what
    # is near the bright structure cuts those off without cutting the glass,
    # which is never far from its own rim, bubbles or scoop.
    near = ndimage.binary_dilation(seed, iterations=7)
    sil = ndimage.binary_fill_holes((lab2 == ids[counts.argmax()]) & near)
    sil = ndimage.binary_closing(sil, np.ones((5, 5)))
    sil = ndimage.binary_fill_holes(sil)
    sil = biggest(sil)
    sil = drop_shelf(sil)
    sil = span_fill(sil)
    alpha = np.clip(ndimage.gaussian_filter(sil.astype(float), 0.9), 0, 1)
    tx = ty = 0
    if tag:
        tx = max(0, tag[0] - box[0]); ty = max(0, tag[1] - box[1])
        alpha[ty:, tx:] = 0

    if tag and mirror:
        # Punching the badge out takes a bite of the glass with it, and that
        # bite is a flat step on an otherwise round glass. These glasses are
        # symmetrical, so it is filled from the mirror of itself about the
        # glass's own centre. Only the badge's own band of rows is repaired:
        # reach any lower and the base, where the tile shelf was, gets
        # mirrored into view as well.
        cols = np.flatnonzero(sil.any(axis=0))
        cx = (cols[0] + cols[-1]) / 2
        xs = np.clip((2 * cx - np.arange(alpha.shape[1])).round().astype(int),
                     0, alpha.shape[1] - 1)
        gap = np.zeros_like(sil)
        gap[ty:ty + 52, tx:] = True
        gap &= (alpha < 0.5) & sil
        a[gap] = a[:, xs][gap]
        alpha = np.where(gap, alpha[:, xs], alpha)

    if trim or trim_top:
        rows = np.flatnonzero(alpha.max(axis=1) > 0.5)
        if len(rows):
            if trim:
                alpha[rows[-1] - trim + 1:] = 0
            if trim_top:
                alpha[:rows[0] + trim_top] = 0

    img = Image.fromarray(
        np.dstack([a.astype('uint8'), (alpha * 255).astype('uint8')]), 'RGBA')
    return img.crop(img.getbbox())


if __name__ == "__main__":
    for k, (box, tag) in BOXES.items():
        g = cut(box, tag, TRIM.get(k, 0), k in MIRROR, TRIM_TOP.get(k, 0))
        g.save(OUT / f"{k}.png")
        print(f"  {k:<11} {g.size[0]:>4} x {g.size[1]}")
    print(f"  -> {OUT}")
