"""Package a computed table for publication.

Writes, for one stack/metric:
  neighbors_<name>.tsv   top-K neighbours per character (human-readable)
  matrix_<name>.npz      full N x N uint8 matrix, compressed (score = value / 255)
  manifest_<name>.json   parameters, character index, row counts, SHA-256 of files
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os

import numpy as np


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="e.g. android_aosp_zh_tw_chamfer_t3")
    ap.add_argument("--data", default="data")
    ap.add_argument("--charset", default="data/charset.tsv")
    ap.add_argument("-k", type=int, default=50)
    ap.add_argument("--min-score", type=float, default=0.0)
    ap.add_argument("--outdir", default="release")
    ap.add_argument("--no-matrix", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    with open(args.charset, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    chars = [r["char"] for r in rows]
    with np.load(os.path.join(args.data, f"topk_{args.name}.npz")) as tk:
        top_idx, top_sc = tk["idx"], tk["score"]
        params = json.loads(str(tk["params"]))
    k = min(args.k, top_idx.shape[1])

    tsv = os.path.join(args.outdir, f"neighbors_{args.name}.tsv")
    with open(tsv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["char", "codepoint", "rank", "neighbor", "neighbor_codepoint", "score"])
        for i, c in enumerate(chars):
            cp = f"U+{ord(c):04X}"
            for r in range(k):
                j, s = int(top_idx[i, r]), float(top_sc[i, r])
                if s < args.min_score:
                    break
                w.writerow([c, cp, r + 1, chars[j], f"U+{ord(chars[j]):04X}", f"{s:.4f}"])

    files = [tsv]
    if not args.no_matrix:
        # The matrix is symmetric: store only the upper triangle (row-major, diagonal included)
        # as raw uint8 compressed with xz. Rebuild with glyphsim.load_matrix().
        mat = np.load(os.path.join(args.data, f"sim_{args.name}.npy"), mmap_mode="r")
        out = os.path.join(args.outdir, f"matrix_{args.name}.triu.u8.xz")
        import lzma
        n = mat.shape[0]
        with lzma.open(out, "wb", preset=6) as f:
            for i in range(n):
                f.write(np.ascontiguousarray(mat[i, i:]).tobytes())
        files.append(out)

    manifest = {
        "name": args.name,
        "n_chars": len(chars),
        "score": "similarity in [0,1]; matrix stores round(score*255) as uint8",
        "params": params,
        "files": {os.path.basename(p): {"bytes": os.path.getsize(p), "sha256": sha256(p)} for p in files},
    }
    with open(os.path.join(args.outdir, f"manifest_{args.name}.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    for p in files:
        print(f"{p}: {os.path.getsize(p) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
