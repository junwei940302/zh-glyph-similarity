"""Compare two tables (e.g. iOS vs Android) to see how much the font matters.

Always reported, from the top-K files:
  overlap of the top-K neighbour sets (Jaccard) and whether the #1 neighbour is
  the same, overall and per character group, plus the characters whose
  neighbours change the most.

With --sim-a/--sim-b (the full .npy matrices), also reported for Han characters:
  - Spearman and Pearson correlation of the scores of random pairs
  - of the pairs that table A rates >= --hi (within A's top 10), how many table
    B still rates >= --hi-b, and where B ranks them
"""
from __future__ import annotations

import argparse
import csv

import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("topk_a")
    ap.add_argument("topk_b")
    ap.add_argument("--sim-a", default="")
    ap.add_argument("--sim-b", default="")
    ap.add_argument("--charset", default="data/charset.tsv")
    ap.add_argument("-k", type=int, default=10)
    ap.add_argument("--show", type=int, default=20)
    ap.add_argument("--hi", type=float, default=0.85)
    ap.add_argument("--hi-b", type=float, default=0.80)
    ap.add_argument("--sample", type=int, default=4000, help="Han characters sampled for the high-pair check")
    args = ap.parse_args()

    with open(args.charset, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    chars = [r["char"] for r in rows]
    group = []
    for r in rows:
        s = r["sets"]
        group.append("bopomofo" if ("bopomofo" in s or "tone" in s) else
                     "alnum" if ("digit" in s or "latin" in s) else "han")
    group = np.array(group)
    with np.load(args.topk_a) as a, np.load(args.topk_b) as b:
        ia, ib = a["idx"][:, :args.k], b["idx"][:, :args.k]
    jac = np.array([len(set(x) & set(y)) / len(set(x) | set(y)) for x, y in zip(ia, ib)])
    top1 = ia[:, 0] == ib[:, 0]
    print(f"top-{args.k} Jaccard / same #1 neighbour")
    for g in ["bopomofo", "alnum", "han", "all"]:
        m = np.ones(len(chars), bool) if g == "all" else group == g
        print(f"  {g:9s} n={m.sum():5d}  Jaccard={jac[m].mean():.3f}  same#1={top1[m].mean():.3f}")
    print("most font-dependent characters (lowest Jaccard):")
    for i in np.argsort(jac)[:args.show]:
        print(f"  {chars[i]}  {jac[i]:.2f}  A: {''.join(chars[j] for j in ia[i])}  B: {''.join(chars[j] for j in ib[i])}")

    if not (args.sim_a and args.sim_b):
        return
    from scipy.stats import pearsonr, spearmanr
    A = np.load(args.sim_a, mmap_mode="r")
    B = np.load(args.sim_b, mmap_mode="r")
    han = np.where(group == "han")[0]
    rng = np.random.default_rng(0)
    p, q = rng.choice(han, 200000), rng.choice(han, 200000)
    va, vb = A[p, q].astype(np.float64), B[p, q].astype(np.float64)
    print(f"Han random pairs (n=200000): Spearman={spearmanr(va, vb)[0]:.3f}  Pearson={pearsonr(va, vb)[0]:.3f}")
    hi, hib = round(args.hi * 255), round(args.hi_b * 255)
    sample = rng.choice(han, min(args.sample, len(han)), replace=False)
    kept, ranks = [], []
    for i in sample:
        rowA = np.asarray(A[i])
        rowB = np.asarray(B[i]).astype(np.int16)
        rowB[i] = -1
        for j in ia[i]:
            if rowA[j] >= hi:
                kept.append(rowB[j] >= hib)
                ranks.append(1 + int((rowB > rowB[j]).sum()))
    kept, ranks = np.array(kept), np.array(ranks)
    print(f"pairs A>={args.hi} in A's top {args.k} (n={len(kept)}): B>={args.hi_b} {kept.mean():.3f}; "
          f"rank in B median {np.median(ranks):.0f}, <=10 {np.mean(ranks <= 10):.3f}, <=50 {np.mean(ranks <= 50):.3f}")


if __name__ == "__main__":
    main()
