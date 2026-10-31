"""Check a similarity matrix against lists of known look-alike pairs.

For each known pair (a, b) we look at a's row and ask how high b ranks
(self excluded, ties get the mid rank). Reported per ground-truth source:
Recall@1/5/10/50, MRR, median rank, and AUC against random pairs.

Ground-truth sources (pairs are kept only if both characters are in the index)
  unicode    UTS #39 confusables.txt: characters with the same skeleton
  same_stroke pycorrector data/same_stroke.txt (Apache-2.0): each line is a
             head character and its shape-similar characters (Simplified)
  curated    hand-written list in groundtruth/curated_pairs.tsv
"""
from __future__ import annotations

import argparse
import csv
import json
import unicodedata

import numpy as np


def read_chars(path):
    with open(path, encoding="utf-8") as f:
        return [r["char"] for r in csv.DictReader(f, delimiter="\t")]


def unicode_pairs(path, idx):
    m = {}
    for line in open(path, encoding="utf-8"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        src, tgt = [x.strip() for x in line.split(";")[:2]]
        m[chr(int(src, 16))] = "".join(chr(int(c, 16)) for c in tgt.split())

    def skel(s):
        s = unicodedata.normalize("NFD", s)
        return unicodedata.normalize("NFD", "".join(m.get(c, c) for c in s))

    groups = {}
    for c in idx:
        groups.setdefault(skel(c), []).append(c)
    pairs = []
    for g in groups.values():
        for a in g:
            for b in g:
                if a != b:
                    pairs.append((a, b))
    return pairs


def same_stroke_pairs(path, idx):
    pairs = []
    for line in open(path, encoding="utf-8"):
        cs = [c for c in line.strip().split() if len(c) == 1]
        if len(cs) < 2 or cs[0] not in idx:
            continue
        for b in cs[1:]:
            if b in idx and b != cs[0]:
                pairs.append((cs[0], b))
    return pairs


def curated_pairs(path, idx):
    pairs = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            a, b = r["a"], r["b"]
            if a in idx and b in idx:
                pairs.append((a, b))
                pairs.append((b, a))
    return pairs


def ranks(sim, pairs, idx):
    out = []
    for a, b in pairs:
        i, j = idx[a], idx[b]
        row = sim[i].astype(np.int16)
        row[i] = -1
        s = row[j]
        gt = int((row > s).sum())
        eq = int((row == s).sum()) - 1
        out.append(1 + gt + eq / 2.0)
    return np.array(out)


def auc(sim, pairs, idx, n_neg=200000, seed=0):
    rng = np.random.default_rng(seed)
    n = sim.shape[0]
    a = rng.integers(0, n, n_neg)
    b = rng.integers(0, n, n_neg)
    keep = a != b
    neg = sim[a[keep], b[keep]].astype(np.float64)
    pos = np.array([sim[idx[x], idx[y]] for x, y in pairs], dtype=np.float64)
    neg_sorted = np.sort(neg)
    lo = np.searchsorted(neg_sorted, pos, side="left")
    hi = np.searchsorted(neg_sorted, pos, side="right")
    return float(((lo + (hi - lo) / 2.0) / len(neg_sorted)).mean())


def summarize(r):
    return {
        "pairs": int(len(r)),
        "R@1": float((r <= 1).mean()), "R@5": float((r <= 5).mean()),
        "R@10": float((r <= 10).mean()), "R@50": float((r <= 50).mean()),
        "MRR": float((1.0 / r).mean()), "median_rank": float(np.median(r)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sims", nargs="+", help="sim_*.npy files")
    ap.add_argument("--charset", default="data/charset.tsv")
    ap.add_argument("--unicode", default="vendor/groundtruth/unicode_confusables_v18.txt")
    ap.add_argument("--same-stroke", default="vendor/groundtruth/pycorrector_same_stroke.txt")
    ap.add_argument("--curated", default="groundtruth/curated_pairs.tsv")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    chars = read_chars(args.charset)
    idx = {c: i for i, c in enumerate(chars)}
    gts = {
        "unicode": unicode_pairs(args.unicode, idx),
        "same_stroke": same_stroke_pairs(args.same_stroke, idx),
        "curated": curated_pairs(args.curated, idx),
    }
    results = {}
    for path in args.sims:
        sim = np.load(path, mmap_mode="r")
        results[path] = {}
        for name, pairs in gts.items():
            r = ranks(sim, pairs, idx)
            s = summarize(r)
            s["AUC"] = auc(sim, pairs, idx)
            results[path][name] = s
    for path, res in results.items():
        print(path)
        for name, s in res.items():
            print(f"  {name:12s} n={s['pairs']:5d}  R@1={s['R@1']:.3f} R@5={s['R@5']:.3f} "
                  f"R@10={s['R@10']:.3f} R@50={s['R@50']:.3f} MRR={s['MRR']:.3f} "
                  f"med={s['median_rank']:.0f} AUC={s['AUC']:.3f}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
