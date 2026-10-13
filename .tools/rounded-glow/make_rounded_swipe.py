"""Builds the rounded cooldown swipe sheet EllesmereUI_RoundedCorners.lua cuts
cells from (EllesmereUI.RoundedSwipe).

A Cooldown draws its swipe from one file stretched over its rect: it takes no
mask and no slices, so a rounded swipe needs art whose corners already have
the rect's proportions. swipe.png (white, the shape in alpha) is a sheet of
COLS x ROWS cells of CELL x CELL texels, one rounded rect per cell:

  column c (1..COLS)  corner radius = c / 64 of the rect's height
  row r (1..ROWS)     height / width = 0.5 + (r - 1) / (2 * (ROWS - 1))

A cell is stretched to the rect, so its corners are ellipses in texel space
(c texels tall, c * height / width wide) that come out round on screen. The
code samples a cell half a texel in from its edges, so the shape is drawn for
that inner rect and no neighbour bleeds in.

Run from the suite root: python .tools/rounded-glow/make_rounded_swipe.py
"""
import os
import struct
import zlib

COLS, ROWS, CELL, SUB = 32, 8, 64, 8

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "media", "rounded", "swipe.png")


def cell_alpha(col, row):
    """One cell as CELL rows of CELL alpha bytes."""
    lo, hi = 0.5, CELL - 0.5                    # the rect the code samples
    side = hi - lo
    ry = col / 64.0 * side
    rx = ry * (0.5 + (row - 1) / (2.0 * (ROWS - 1)))
    img = [[255] * CELL for _ in range(CELL)]
    # Only the corner boxes hold anything but full cover.
    nx, ny = int(lo + rx) + 1, int(lo + ry) + 1
    for ty in range(ny):
        for tx in range(nx):
            hits = 0
            for sy in range(SUB):
                y = min(max(ty + (sy + 0.5) / SUB, lo), hi) - lo
                for sx in range(SUB):
                    x = min(max(tx + (sx + 0.5) / SUB, lo), hi) - lo
                    if x >= rx or y >= ry or ((x - rx) / rx) ** 2 + ((y - ry) / ry) ** 2 <= 1.0:
                        hits += 1
            a = int(round(255.0 * hits / (SUB * SUB)))
            # The four corners are mirror images of each other.
            img[ty][tx] = img[ty][CELL - 1 - tx] = a
            img[CELL - 1 - ty][tx] = img[CELL - 1 - ty][CELL - 1 - tx] = a
    return img


def write_png(path, width, height, rows):
    """rows: height byte strings of width RGBA texels."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + r for r in rows)   # filter 0 on every row
    open(path, "wb").write(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b""))


def main():
    rows = []
    for row in range(1, ROWS + 1):
        cells = [cell_alpha(col, row) for col in range(1, COLS + 1)]
        for ty in range(CELL):
            line = bytearray()
            for img in cells:
                for a in img[ty]:
                    line += bytes((255, 255, 255, a))
            rows.append(bytes(line))
    write_png(OUT, COLS * CELL, ROWS * CELL, rows)
    print("wrote %d x %d cells of %d texels to %s" % (COLS, ROWS, CELL, OUT))


if __name__ == "__main__":
    main()
