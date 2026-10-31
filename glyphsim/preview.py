"""Draw a preview grid: each row is a query glyph followed by its top neighbours."""
from __future__ import annotations

import argparse
import csv

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("render")
    ap.add_argument("topk")
    ap.add_argument("--charset", default="data/charset.tsv")
    ap.add_argument("--queries", required=True, help="string of query characters")
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--label-font", default="vendor/fonts/Roboto[wdth,wght].ttf")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    with open(args.charset, encoding="utf-8") as f:
        chars = [r["char"] for r in csv.DictReader(f, delimiter="\t")]
    idx = {c: i for i, c in enumerate(chars)}
    ink = np.load(args.render)["ink"]
    with np.load(args.topk) as z:
        tk = {"idx": z["idx"], "score": z["score"]}
    cell, gap, lab = ink.shape[1], 6, 14
    queries = [q for q in args.queries if q in idx]
    w = (cell + gap) * (args.n + 1) + gap * 3
    h = (cell + lab + gap) * len(queries) + gap
    img = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(args.label_font, 11)
    except OSError:  # e.g. the iOS run on a Mac does not download the Android fonts
        font = ImageFont.load_default(size=11)
    for r, q in enumerate(queries):
        y = gap + r * (cell + lab + gap)
        i = idx[q]
        img.paste(Image.fromarray(255 - ink[i]), (gap, y))
        draw.rectangle([gap - 1, y - 1, gap + cell, y + cell], outline=0)
        for k in range(args.n):
            j, s = int(tk["idx"][i, k]), float(tk["score"][i, k])
            x = gap * 3 + (k + 1) * (cell + gap)
            img.paste(Image.fromarray(255 - ink[j]), (x, y))
            draw.text((x + 2, y + cell + 1), f"{s:.2f}", fill=0, font=font)
    img.save(args.out)
    print(f"{len(queries)} rows -> {args.out}")


if __name__ == "__main__":
    main()
