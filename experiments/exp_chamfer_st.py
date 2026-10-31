"""Grid over (lam, mu) for chamfer_st, evaluated on the same ground truth as the main table."""
import csv
import json
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from glyphsim.chamfer_st import count_holes, distance_matrix, to_similarity  # noqa: E402
from glyphsim.evaluate import (auc, curated_pairs, ranks, read_chars, same_stroke_pairs,  # noqa: E402
                               summarize, unicode_pairs)

render = sys.argv[1]
out_json = sys.argv[2]
chars = read_chars("data/charset.tsv")
idx = {c: i for i, c in enumerate(chars)}
ink = np.load(render)["ink"]
gts = {
    "unicode": unicode_pairs("vendor/groundtruth/unicode_confusables_v18.txt", idx),
    "curated": curated_pairs("groundtruth/curated_pairs.tsv", idx),
    "same_stroke": same_stroke_pairs("vendor/groundtruth/pycorrector_same_stroke.txt", idx),
}
types = {}
for r in csv.DictReader(open("groundtruth/curated_pairs.tsv", encoding="utf-8"), delimiter="\t"):
    if r["a"] in idx and r["b"] in idx:
        types.setdefault(r["type"], []).extend([(r["a"], r["b"]), (r["b"], r["a"])])

t = time.time()
lams = (0.5, 1.0, 2.0)
dists, binary = distance_matrix(ink, lams=lams)
holes = count_holes(binary, min_area=6)
print(f"distances in {time.time() - t:.0f}s; holes 0/O/8/B/日/目 =",
      [int(holes[idx[c]]) for c in "0O8B日目"], flush=True)
np.save("data/holes_" + render.split("render_")[-1].replace(".npz", ".npy"), holes)

results = {}
probe = "0Ol1I5S"
for lam in lams:
    for mu in (0.0, 0.2, 0.4):
        sim = to_similarity(dists[lam], holes, mu=mu, tau=3.0)
        key = f"lam{lam}_mu{mu}"
        res = {}
        for name, pairs in list(gts.items()) + [("curated:" + k, v) for k, v in types.items()]:
            s = summarize(ranks(sim, pairs, idx))
            if ":" not in name:
                s["AUC"] = auc(sim, pairs, idx)
            res[name] = s
        nb = {}
        for c in probe:
            row = sim[idx[c]].astype(np.int16)
            row[idx[c]] = -1
            top = np.argsort(-row, kind="stable")[:6]
            nb[c] = " ".join(f"{chars[j]}{row[j] / 255:.2f}" for j in top)
        res["probe"] = nb
        results[key] = res
        u, cu = res["unicode"], res["curated"]
        print(f"{key:14s} unicode R@1 {u['R@1']:.3f} R@5 {u['R@5']:.3f} R@10 {u['R@10']:.3f} | "
              f"curated R@1 {cu['R@1']:.3f} R@5 {cu['R@5']:.3f} R@10 {cu['R@10']:.3f} | "
              f"han R@10 {res['curated:han-han']['R@10']:.3f} digit R@1 {res['curated:latin-digit']['R@1']:.3f} "
              f"| 0: {nb['0']}", flush=True)
        if lam == 1.0 and mu == 0.2:
            np.save("data/sim_tmp_st.npy", sim)
json.dump(results, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
