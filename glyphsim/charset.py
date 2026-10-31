"""Build the character index shared by every similarity matrix.

The index is the union of (in this order, so earlier indices never move):
  - Bopomofo: the 37 standard letters U+3105-U+3129 and the 5 tone marks
  - ASCII digits 0-9 and Latin letters A-Z, a-z
  - Big5 level 1 (A440-C67E) and level 2 (C940-F9D5)     [Python codec]
  - GB2312 level 1 (B0A1-D7F9) and level 2 (D8A1-F7FE)   [Python codec]
  - 教育部《常用國字標準字體表》4,808 and《次常用國字標準字體表》6,343
  - 《通用规范汉字表》8,105, levels 1/2/3 = 3,500/3,000/1,605 in file order
The two official lists are read from vendor/charlists (scripts/fetch_charlists.sh).
Use --no-lists to build the codec-only index (15,537 characters).

Output: TSV with one row per character, in a fixed order (index = row number);
the `sets` column lists every source that contains the character.
"""
from __future__ import annotations

import argparse
import csv
import unicodedata

BOPOMOFO = [chr(c) for c in range(0x3105, 0x312A)]          # ㄅ..ㄩ (37)
TONES = ["ˉ", "ˊ", "ˇ", "ˋ", "˙"]  # ˉ ˊ ˇ ˋ ˙
DIGITS = [chr(c) for c in range(0x30, 0x3A)]
LATIN = [chr(c) for c in range(0x41, 0x5B)] + [chr(c) for c in range(0x61, 0x7B)]


def _decode_range(codec: str, lead_lo: int, lead_hi: int, trail_ranges) -> list[str]:
    out = []
    for lead in range(lead_lo, lead_hi + 1):
        for lo, hi in trail_ranges:
            for trail in range(lo, hi + 1):
                try:
                    ch = bytes([lead, trail]).decode(codec)
                except UnicodeDecodeError:
                    continue
                if len(ch) == 1 and unicodedata.category(ch) == "Lo":
                    out.append(ch)
    return out


def big5_levels() -> tuple[list[str], list[str]]:
    trails = [(0x40, 0x7E), (0xA1, 0xFE)]
    lvl1 = [c for c in _decode_range("big5", 0xA4, 0xC6, trails)]
    # level 1 ends at C67E; drop anything decoded beyond it
    lvl1 = [c for c in lvl1 if c.encode("big5") <= b"\xc6\x7e"]
    lvl2 = _decode_range("big5", 0xC9, 0xF9, trails)
    lvl2 = [c for c in lvl2 if c.encode("big5") <= b"\xf9\xd5"]
    return lvl1, lvl2


def gb2312_levels() -> tuple[list[str], list[str]]:
    trails = [(0xA1, 0xFE)]
    lvl1 = _decode_range("gb2312", 0xB0, 0xD7, trails)
    lvl2 = _decode_range("gb2312", 0xD8, 0xF7, trails)
    return lvl1, lvl2


def read_list(path: str) -> list[str]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            ch = line.split("\t")[0].strip()
            if len(ch) != 1 or unicodedata.category(ch) != "Lo":
                raise ValueError(f"{path}: unexpected entry {line!r}")
            out.append(ch)
    return out


def official_lists(folder: str) -> list[tuple[str, list[str]]]:
    moe1 = read_list(f"{folder}/edu_standard_1.txt")
    moe2 = read_list(f"{folder}/edu_standard_2.txt")
    tgh = read_list(f"{folder}/tongyong_guifan.txt")
    if (len(moe1), len(moe2), len(tgh)) != (4808, 6343, 8105):
        raise ValueError(f"unexpected list sizes {len(moe1)}, {len(moe2)}, {len(tgh)}")
    return [("moe_1", moe1), ("moe_2", moe2),
            ("tgh_1", tgh[:3500]), ("tgh_2", tgh[3500:6500]), ("tgh_3", tgh[6500:])]


def build(lists_dir: str | None = "vendor/charlists") -> list[dict]:
    b1, b2 = big5_levels()
    g1, g2 = gb2312_levels()
    groups = [
        ("bopomofo", BOPOMOFO),
        ("tone", TONES),
        ("digit", DIGITS),
        ("latin", LATIN),
        ("big5_1", b1),
        ("big5_2", b2),
        ("gb2312_1", g1),
        ("gb2312_2", g2),
    ]
    if lists_dir:
        groups += official_lists(lists_dir)
    rows: dict[str, dict] = {}
    for tag, chars in groups:
        for ch in chars:
            if ch not in rows:
                rows[ch] = {"char": ch, "codepoint": f"U+{ord(ch):04X}", "sets": []}
            if tag not in rows[ch]["sets"]:
                rows[ch]["sets"].append(tag)
    out = list(rows.values())
    for i, r in enumerate(out):
        r["index"] = i
        r["sets"] = ",".join(r["sets"])
        r["name"] = unicodedata.name(r["char"], "")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default="data/charset.tsv")
    ap.add_argument("--lists", default="vendor/charlists", help="folder with the official lists")
    ap.add_argument("--no-lists", action="store_true", help="codec-only index (15,537 characters)")
    args = ap.parse_args()
    rows = build(None if args.no_lists else args.lists)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["index", "char", "codepoint", "sets", "name"], delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    counts: dict[str, int] = {}
    for r in rows:
        for s in r["sets"].split(","):
            counts[s] = counts.get(s, 0) + 1
    print(f"{len(rows)} characters -> {args.out}")
    for k, v in counts.items():
        print(f"  {k:10s} {v}")


if __name__ == "__main__":
    main()
