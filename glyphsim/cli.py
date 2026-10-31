"""Command-line queries against the published table.

    glyphsim neighbors 賴 -k 8
    glyphsim sim 0 O
    glyphsim pattern LINE --min-score 0.85
"""
from __future__ import annotations

import argparse
import sys

from .api import DEFAULT_TABLE, DEFAULT_VERSION, GlyphSim


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="glyphsim", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", default=DEFAULT_TABLE)
    ap.add_argument("--version", default=DEFAULT_VERSION)
    ap.add_argument("--charset", help="use a local charset.tsv instead of the release")
    ap.add_argument("--matrix", help="use a local .npy or .triu.u8.xz instead of the release")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("neighbors", help="most similar characters")
    p.add_argument("char")
    p.add_argument("-k", type=int, default=10)
    p.add_argument("--min-score", type=float, default=0.0)
    p = sub.add_parser("sim", help="similarity of two characters")
    p.add_argument("a")
    p.add_argument("b")
    p = sub.add_parser("pattern", help="regex matching a word and its look-alike spellings")
    p.add_argument("text")
    p.add_argument("--min-score", type=float, default=0.85)
    args = ap.parse_args(argv)

    if args.charset and args.matrix:
        gs = GlyphSim.from_files(args.charset, args.matrix)
    else:
        gs = GlyphSim.from_release(args.table, args.version)

    try:
        if args.cmd == "neighbors":
            for rank, (c, s) in enumerate(gs.neighbors(args.char, args.k, args.min_score), 1):
                print(f"{rank:>3}  {c}  U+{ord(c):04X}  {s:.3f}")
        elif args.cmd == "sim":
            print(f"{gs.similarity(args.a, args.b):.3f}")
        elif args.cmd == "pattern":
            print(gs.pattern(args.text, args.min_score))
    except KeyError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
