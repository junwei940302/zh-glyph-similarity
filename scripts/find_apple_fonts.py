#!/usr/bin/env python3
"""Locate the Apple system fonts on this Mac and print a stacks JSON for iOS.

Run on macOS only. The fonts are read in place and never copied: Apple's
licence does not allow redistributing them.

    python3 scripts/find_apple_fonts.py > stacks.local.json
"""
from __future__ import annotations

import glob
import json
import os
import sys

from fontTools.ttLib import TTCollection, TTFont

SEARCH = [
    "/System/Library/Fonts",
    "/System/Library/AssetsV2",
    "/System/Library/PrivateFrameworks/FontServices.framework/Resources/Reserved",
    "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
]


def faces(path):
    if path.lower().endswith((".ttc", ".otc")):
        for i, f in enumerate(TTCollection(path, lazy=True).fonts):
            yield i, f
    else:
        yield 0, TTFont(path, lazy=True)


def names(font):
    n = font["name"]
    fam = n.getDebugName(16) or n.getDebugName(1) or ""
    sub = n.getDebugName(17) or n.getDebugName(2) or ""
    return fam, sub


def find_face(pattern, family):
    hits = []
    for root in SEARCH:
        hits += glob.glob(os.path.join(root, "**", pattern), recursive=True)
    best = None
    for path in sorted(set(hits)):
        try:
            for i, f in faces(path):
                fam, sub = names(f)
                if fam.lstrip(".") == family and sub == "Regular":
                    rank = 0 if not fam.startswith(".") else 1  # prefer the public face
                    if best is None or rank < best[0]:
                        best = (rank, path, i, fam)
        except Exception as e:  # unreadable asset, skip
            print(f"skip {path}: {e}", file=sys.stderr)
    return best


def sf_axes(path):
    font = TTFont(path, lazy=True)
    axes = []
    for a in font["fvar"].axes:
        if a.axisTag == "wght":
            v = 400.0
        elif a.axisTag == "opsz":
            v = min(max(17.0, a.minValue), a.maxValue)  # iMessage body text is 17 pt
        else:
            v = a.defaultValue
        axes.append({"tag": a.axisTag, "value": v})
    return axes


def main():
    if sys.platform != "darwin":
        sys.exit("Run this on macOS: the iOS stack uses fonts that ship with macOS.")
    tc = find_face("PingFang*.tt?", "PingFang TC")
    sc = find_face("PingFang*.tt?", "PingFang SC")
    sf_path = "/System/Library/Fonts/SFNS.ttf"
    missing = [n for n, v in [("PingFang TC", tc), ("PingFang SC", sc)] if v is None]
    if missing or not os.path.exists(sf_path):
        sys.exit(f"Not found: {missing or [sf_path]}. Open Font Book, search PingFang TC/SC, "
                 "and click Download if the font is shown as not installed.")
    axes = sf_axes(sf_path)
    stacks = json.load(open(os.path.join(os.path.dirname(__file__), "..", "stacks.json"), encoding="utf-8"))
    ios = stacks["ios_zh_tw"]
    ios["fonts"] = [
        {"label": "SF Pro (SFNS) Regular, opsz 17", "path": sf_path,
         "variation_axes": [a["value"] for a in axes], "axes": axes},
        {"label": f"{tc[3]} Regular", "path": tc[1], "index": tc[2]},
        {"label": f"{sc[3]} Regular", "path": sc[1], "index": sc[2]},
    ]
    stacks["ios_zh_tw"] = ios
    json.dump(stacks, sys.stdout, ensure_ascii=False, indent=2)
    print(file=sys.stderr)
    for f in ios["fonts"]:
        print(f"found {f['label']}: {f['path']} (index {f.get('index', 0)})", file=sys.stderr)


if __name__ == "__main__":
    main()
