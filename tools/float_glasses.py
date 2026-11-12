"""Lift each float glass off its dark tile in the Scoop & Sip source board.

Every glass is cut by shape, not by hand. The hard part is that everything
contaminating the cut is bright too -- the neon border around each tile, the
cream name plates under the kids' drinks, the red price badges and the lit
band each glass stands on -- so no single threshold separates them. What does
work is in cut(): two thresholds, a proximity test, a burr remover and a row
fill, each undoing one specific thing the board does.

Regenerate after changing anything here:  python3 tools/float_glasses.py
Source artwork: src/floats-src.png.  Output: src/floats/<drink>.png
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
SRC = Image.open(ROOT / "src" / "floats-src.png").convert("RGB")
OUT = ROOT / "src" / "floats"
OUT.mkdir(parents=True, exist_ok=True)

F = 3   # a thin frame blanked so a border hugging the box edge cannot win

# Three badges sit on top of a glass rather than beside it. Punching one out
# takes a bite of the glass with it, so those three are repaired from their
# own mirror image afterwards.
MIRROR = {"dragon", "blueberry", "coconut"}

BOXES = {
    # (search box, price-badge corner to punch out or None). Boxes stop short
    # of the tile's neon border, the drink name beside it and the kids' name
    # plates: all bright, and any of them inside the box wins the blob test.
    # A badge corner is only given where the badge actually touches a glass,
    # and sits just outside where that glass has tapered to at that height.
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


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def biggest(mask):
    """The largest piece, so a scrap of tile cannot be widened into a bar by
    the row fill below."""
    lab, n = ndimage.label(mask)
    if n < 2:
        return mask
    sizes = [((lab == i).sum() if i else 0, i) for i in range(n + 1)]
    return lab == max(sizes)[1]


def deburr(sil, r=4):
    """Strip the tile's glow off a glass without cutting the glass.

    What comes along with a drink is always thin: the lit band under a tile is
    a bar three or four pixels tall welded to the base, and the slab over a
    scoop is no thicker. Opening with a disk deletes anything that thin in any
    direction, which is all of them and no part of a glass -- where shaving a
    flat band off the bottom took the base's curve with it and left a cut edge.

    Opening erodes and then dilates with the same disk, so whatever survives
    comes back its own size -- the glass is not shrunk, and a martini's foot,
    thin as it is, is held on by a stem the disk still fits inside. Growing
    the survivor back out INSIDE the original shape, which is the textbook
    next step, is wrong here: the burr is attached to the glass, so the
    regrowth flows straight back into it.
    """
    core = ndimage.binary_opening(sil, disk(r))
    return biggest(core) if core.any() else sil


def span_fill(sil):
    """Fill each row between its leftmost and rightmost pixel.

    Every glass here -- tumbler, pint, martini -- is a single solid span at
    any height, bowl, stem and foot alike. So this closes the bites that unlit
    cola and the darker scallops leave behind, and it cannot invent anything
    outside the glass's own outline.
    """
    out = np.zeros_like(sil)
    cols = np.arange(sil.shape[1])[None, :]
    has = sil.any(axis=1)
    left = np.where(has, sil.argmax(axis=1), 0)[:, None]
    right = np.where(has, sil.shape[1] - 1 - sil[:, ::-1].argmax(axis=1), -1)[:, None]
    out[:] = (cols >= left) & (cols <= right) & has[:, None]
    return out


# Two knobs that a couple of drinks need their own value for. REACH is how
# far from the bright structure a pixel may be and still count as glass --
# too small and the unlit corner of a dark cola is dropped; too large and the
# tile's glow is picked up. BURR is the disk that strips the tile's lit band
# off a base; it has to be smaller than a martini stem is wide.
REACH = {"rootbeer": 7, "cola": 7, "sprite": 7, "dietcoke": 7}
BURR = {"blueberry": 8}
# And the outline threshold, for a glass whose lower corner is darker than
# the usual 95 copes with.
LOW = {}

# The four kids' drinks are the same glass rendered four times, in cells of
# the same size and pitch, so their search boxes line up pixel for pixel.
# Diet Coke's lower corner is dark enough that no threshold finds its edge
# without taking tile with it, and it comes out with a bite missing. Rather
# than tune a number until that one glass looks right, it borrows the shape
# of a sibling that came out clean and keeps its own colour.
SHAPE_FROM = {"dietcoke": "cola"}


def cut(key, box, tag=None, mirror=False):
    c = SRC.crop(box)
    a = np.asarray(c).astype(float)
    lum = a.max(axis=2)

    # Two thresholds, each doing one job. The high one finds the glass: every
    # pixel that belongs to one peaks at 227+, so the biggest bright blob in
    # the box is always the drink. But a tumbler of cola is mostly DARK, and
    # filling that bright blob leaves a ragged base where the unlit liquid was
    # never enclosed. So the outline comes from the low threshold instead,
    # just above the tile's own 37-54.
    hi = lum > 140
    hi[:F, :] = hi[-F:, :] = False
    hi[:, :F] = hi[:, -F:] = False
    lab, n = ndimage.label(hi)
    sizes = [((lab == i).sum() if i else 0, i) for i in range(n + 1)]
    best, which = max(sizes)
    if not best:
        raise SystemExit(f"no glass found in {box}")
    seed = lab == which

    lab2, _ = ndimage.label(lum > LOW.get(key, 95))
    ids, counts = np.unique(lab2[seed], return_counts=True)
    ids, counts = ids[ids > 0], counts[ids > 0]
    if not len(ids):
        raise SystemExit(f"no outline found in {box}")

    # The low threshold also reaches the glow shelf under the tile and the
    # badge beside it. Keeping only what is near the bright structure cuts
    # those back, since a glass is never far from its own rim or bubbles.
    near = ndimage.binary_dilation(seed, iterations=REACH.get(key, 5))
    sil = ndimage.binary_fill_holes((lab2 == ids[counts.argmax()]) & near)
    sil = ndimage.binary_closing(sil, np.ones((5, 5)))
    sil = ndimage.binary_fill_holes(sil)
    sil = biggest(sil)
    sil = deburr(sil, BURR.get(key, 4))
    sil = span_fill(sil)

    # Pull the edge in before feathering. The outermost ring of the silhouette
    # is pixels that are part glass and part dark tile, and left in they print
    # as a grey outline around every drink on a white page.
    sil = ndimage.binary_erosion(sil, disk(2))
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
        # reach any lower and the base comes into view mirrored as well.
        cols = np.flatnonzero(sil.any(axis=0))
        cx = (cols[0] + cols[-1]) / 2
        xs = np.clip((2 * cx - np.arange(alpha.shape[1])).round().astype(int),
                     0, alpha.shape[1] - 1)
        gap = np.zeros_like(sil)
        gap[ty:ty + 52, tx:] = True
        gap &= (alpha < 0.5) & sil
        a[gap] = a[:, xs][gap]
        alpha = np.where(gap, alpha[:, xs], alpha)

    return a, alpha, seed


def _origin(mask):
    ys, xs = np.where(mask)
    return ys.min(), xs.min()


def render(key, box, tag=None, mirror=False):
    a, alpha, seed = cut(key, box, tag, mirror)
    lend = SHAPE_FROM.get(key)
    if lend:
        _, borrowed, lend_seed = cut(lend, BOXES[lend][0], BOXES[lend][1],
                                     lend in MIRROR)
        if borrowed.shape != alpha.shape:
            raise SystemExit(f"{key} cannot borrow {lend}: boxes differ in size")
        # The cells are the same size but the art is not placed identically in
        # each, so line the two up on their own bright structure before
        # swapping the shape over. A few pixels out and the tile shows along
        # one side.
        dy = _origin(seed)[0] - _origin(lend_seed)[0]
        dx = _origin(seed)[1] - _origin(lend_seed)[1]
        alpha = np.roll(np.roll(borrowed, dy, axis=0), dx, axis=1)
    img = Image.fromarray(
        np.dstack([a.astype("uint8"), (alpha * 255).astype("uint8")]), "RGBA")
    return img.crop(img.getbbox())


if __name__ == "__main__":
    for k, (box, tag) in BOXES.items():
        g = render(k, box, tag, k in MIRROR)
        g.save(OUT / f"{k}.png")
        print(f"  {k:<11} {g.size[0]:>4} x {g.size[1]}")
    print(f"  -> {OUT}")
