"""Render every character in the index with one platform font stack.

A font stack mimics how a phone picks a font for each character: the first
font in the list whose cmap contains the character is used (font fallback).
All characters share one canvas size, one font size and one baseline, so a
narrow Latin "l" and a full-width CJK "一" keep their real relative size and
position, as they would appear side by side in an SMS.

Output: an .npz with
  ink   uint8 [N, H, W]   0 = background, 255 = full ink (anti-aliased)
  font  int16 [N]         index into the stack, -1 = no font has the glyph
  meta  json string       stack definition and rendering parameters
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

import numpy as np
from fontTools.ttLib import TTCollection, TTFont
from PIL import Image, ImageDraw, ImageFont


def load_cmap(path: str, index: int) -> set[int]:
    if path.lower().endswith((".ttc", ".otc")):
        font = TTCollection(path, lazy=True).fonts[index]
    else:
        font = TTFont(path, lazy=True)
    return set(font.getBestCmap().keys())


def typo_ascent_ratio(path: str, index: int) -> float:
    if path.lower().endswith((".ttc", ".otc")):
        font = TTCollection(path, lazy=True).fonts[index]
    else:
        font = TTFont(path, lazy=True)
    os2 = font["OS/2"]
    asc, desc = os2.sTypoAscender, os2.sTypoDescender
    return asc / float(asc - desc)


def open_font(spec: dict, size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(spec["path"], size=size, index=spec.get("index", 0),
                              layout_engine=ImageFont.Layout.BASIC)
    try:
        if "variation_name" in spec:
            font.set_variation_by_name(spec["variation_name"])
        elif "variation_axes" in spec:
            # values in the font's axis order, e.g. Roboto: [wght, wdth]
            font.set_variation_by_axes(spec["variation_axes"])
    except Exception as e:  # keep going with the font's default instance, but say so
        print(f"warning: could not set variation for {spec['label']}: {e}; using default instance",
              file=sys.stderr)
        spec["variation_error"] = str(e)
    return font


def render_stack(chars: list[str], stack: dict, canvas: int, size: int):
    specs = stack["fonts"]
    cmaps = [load_cmap(s["path"], s.get("index", 0)) for s in specs]
    fonts = [open_font(s, size) for s in specs]
    primary = stack.get("baseline_font", len(specs) - 1)
    ratio = typo_ascent_ratio(specs[primary]["path"], specs[primary].get("index", 0))
    top = (canvas - size) / 2.0
    baseline = top + size * ratio

    n = len(chars)
    ink = np.zeros((n, canvas, canvas), dtype=np.uint8)
    used = np.full(n, -1, dtype=np.int16)
    for i, ch in enumerate(chars):
        cp = ord(ch)
        fi = next((k for k, cm in enumerate(cmaps) if cp in cm), -1)
        used[i] = fi
        if fi < 0:
            continue
        font = fonts[fi]
        img = Image.new("L", (canvas, canvas), 0)
        draw = ImageDraw.Draw(img)
        adv = font.getlength(ch)
        draw.text(((canvas - adv) / 2.0, baseline), ch, fill=255, font=font, anchor="ls")
        ink[i] = np.asarray(img, dtype=np.uint8)
    meta = {
        "stack": stack,
        "canvas": canvas,
        "font_size": size,
        "baseline_y": baseline,
        "ascent_ratio": ratio,
        "renderer": f"Pillow {Image.__version__} / FreeType, grayscale anti-aliased",
    }
    return ink, used, meta


def read_charset(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [r["char"] for r in csv.DictReader(f, delimiter="\t")]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--charset", default="data/charset.tsv")
    ap.add_argument("--stacks", default="stacks.json")
    ap.add_argument("--stack", required=True, help="stack name in stacks.json")
    ap.add_argument("--canvas", type=int, default=64)
    ap.add_argument("--size", type=int, default=56)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    with open(args.stacks, encoding="utf-8") as f:
        stack = json.load(f)[args.stack]
    chars = read_charset(args.charset)
    ink, used, meta = render_stack(chars, stack, args.canvas, args.size)
    meta["stack_name"] = args.stack
    np.savez_compressed(args.out, ink=ink, font=used, meta=json.dumps(meta, ensure_ascii=False))

    missing = [chars[i] for i in np.where(used < 0)[0]]
    print(f"{len(chars)} glyphs -> {args.out}")
    for k, s in enumerate(stack["fonts"]):
        print(f"  font {k} {s['label']}: {int((used == k).sum())}")
    print(f"  missing: {len(missing)} {''.join(missing[:40])}", file=sys.stderr if missing else sys.stdout)


if __name__ == "__main__":
    main()
