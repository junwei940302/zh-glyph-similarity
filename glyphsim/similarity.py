"""Compute an N x N visual-similarity matrix from rendered glyphs.

Every cell is produced by the same formula, so scores are comparable across
the whole table. Both metrics reduce to matrix products, so the full table
fits on a laptop CPU in minutes.

Metrics
  blurcos  Gaussian-blur each glyph (sigma in px), flatten, L2-normalise,
           similarity = cosine (dot product). Tolerant to 1-2 px offsets.
  chamfer  Symmetric chamfer distance between ink pixels (ink > 50%):
           d(A,B) = 0.5 * (mean over A's ink of distance to nearest B ink
                         + mean over B's ink of distance to nearest A ink),
           similarity = exp(-d / tau). Sensitive to stroke structure.
  chamfer_st  (default) chamfer that tolerates width differences: either
           glyph may be stretched horizontally by s in {0.8 .. 1.25}, the
           best match is kept, and lam * |ln s| px is added for the stretch.
           Fixes cases like "0" vs "O", which differ mainly in width.
           See glyphsim/chamfer_st.py.

Outputs (in --outdir)
  sim_<stack>_<metric>.npy  uint8 [N, N], round(similarity * 255), diagonal = 255
  topk_<stack>_<metric>.npz idx int32 [N, K], score float32 [N, K] (self excluded)
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter


def blurcos_features(ink: np.ndarray, sigma: float) -> np.ndarray:
    x = ink.astype(np.float32) / 255.0
    if sigma > 0:
        x = np.stack([gaussian_filter(g, sigma) for g in x])
    x = x.reshape(len(x), -1)
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(norm, 1e-8)


def chamfer_features(ink: np.ndarray):
    binary = ink >= 128
    dt = np.stack([distance_transform_edt(~b) if b.any() else np.full(b.shape, 99.0) for b in binary])
    b = binary.reshape(len(binary), -1).astype(np.float32)
    count = np.maximum(b.sum(1), 1.0)
    return b, dt.reshape(len(dt), -1).astype(np.float32), count


def compute(ink: np.ndarray, metric: str, sigma: float, tau: float, k: int, block: int, out_npy: str,
            lam: float = 0.5):
    n = len(ink)
    sim_u8 = np.lib.format.open_memmap(out_npy, mode="w+", dtype=np.uint8, shape=(n, n))
    top_idx = np.zeros((n, k), dtype=np.int32)
    top_sc = np.zeros((n, k), dtype=np.float32)

    if metric == "blurcos":
        f = blurcos_features(ink, sigma)
    elif metric == "chamfer":
        b, dt, count = chamfer_features(ink)
    elif metric == "chamfer_st":
        from .chamfer_st import distance_matrix
        dists, _ = distance_matrix(ink, lams=(lam,), block=block, log=lambda m: None)
        dist = dists[lam]
    else:
        raise ValueError(metric)

    for s in range(0, n, block):
        e = min(n, s + block)
        if metric == "blurcos":
            sim = f[s:e] @ f.T
        elif metric == "chamfer":
            d = 0.5 * ((b[s:e] @ dt.T) / count[s:e, None] + (dt[s:e] @ b.T) / count[None, :])
            sim = np.exp(-d / tau)
        else:
            sim = np.exp(-dist[s:e] / tau)
        np.clip(sim, 0.0, 1.0, out=sim)
        rows = np.arange(e - s)
        sim[rows, rows + s] = 1.0
        sim_u8[s:e] = np.rint(sim * 255).astype(np.uint8)
        sim[rows, rows + s] = -1.0  # exclude self from neighbours
        part = np.argpartition(-sim, k, axis=1)[:, :k]
        psc = np.take_along_axis(sim, part, axis=1)
        order = np.argsort(-psc, axis=1)
        top_idx[s:e] = np.take_along_axis(part, order, axis=1)
        top_sc[s:e] = np.take_along_axis(psc, order, axis=1)
    sim_u8.flush()
    return top_idx, top_sc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("render", help="npz from glyphsim.render")
    ap.add_argument("--metric", choices=["blurcos", "chamfer", "chamfer_st"], required=True)
    ap.add_argument("--sigma", type=float, default=1.5, help="blur sigma in px (blurcos)")
    ap.add_argument("--tau", type=float, default=3.0, help="distance scale in px (chamfer, chamfer_st)")
    ap.add_argument("--lam", type=float, default=0.5, help="stretch penalty in px per |ln s| (chamfer_st)")
    ap.add_argument("-k", type=int, default=50)
    ap.add_argument("--block", type=int, default=1024)
    ap.add_argument("--outdir", default="data")
    ap.add_argument("--tag", default="", help="suffix for output names, e.g. s1.5")
    args = ap.parse_args()

    d = np.load(args.render)
    meta = json.loads(str(d["meta"]))
    stack = meta["stack_name"]
    name = f"{stack}_{args.metric}{('_' + args.tag) if args.tag else ''}"
    out_npy = os.path.join(args.outdir, f"sim_{name}.npy")
    t = time.time()
    idx, sc = compute(d["ink"], args.metric, args.sigma, args.tau, args.k, args.block, out_npy, lam=args.lam)
    params = {"metric": args.metric, "sigma": args.sigma, "tau": args.tau, "k": args.k, "render_meta": meta}
    if args.metric == "chamfer_st":
        from .chamfer_st import SCALES
        params.update({"lam": args.lam, "scales": list(SCALES), "mu": 0.0})
    np.savez(os.path.join(args.outdir, f"topk_{name}.npz"), idx=idx, score=sc,
             params=json.dumps(params, ensure_ascii=False))
    print(f"{name}: {len(idx)}x{len(idx)} in {time.time() - t:.1f}s -> {out_npy}")


if __name__ == "__main__":
    main()
