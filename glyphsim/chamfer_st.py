"""Stretch-tolerant, topology-aware chamfer similarity.

Plain chamfer distance treats a glyph as a point set and averages how far each
ink pixel is from the other glyph's ink. Two cues that people rely on are
missing from it:
  - width tolerance: "0" and "O" differ mainly in width, which shifts the
    whole outline and makes the plain distance large;
  - topology: "0" has one enclosed hole, "8" has two, which people notice at
    once even though the outlines overlap.

This metric adds both, with the same formula for every pair:
  d(A,B) = min over s in SCALES and over which glyph is stretched of
           chamfer(stretch_x(A, s), B) + lam * |ln s|
         + mu * min(|holes(A) - holes(B)|, hole_cap)
  similarity = exp(-d / tau)
stretch_x scales a glyph horizontally about its ink bounding-box centre.
Holes are background regions not touching the canvas edge with area >= min_hole.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, label, map_coordinates

SCALES = (0.8, 0.89, 1.0, 1.12, 1.25)


def count_holes(binary: np.ndarray, min_area: int) -> np.ndarray:
    out = np.zeros(len(binary), dtype=np.int16)
    for i, b in enumerate(binary):
        lab, n = label(~b)
        if n <= 1:
            continue
        border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
        areas = np.bincount(lab.ravel())
        out[i] = sum(1 for k in range(1, n + 1) if k not in border and areas[k] >= min_area)
    return out


def stretch(ink01: np.ndarray, binary: np.ndarray, s: float) -> np.ndarray:
    """Horizontally scale each glyph by s about its bbox centre; returns binary images."""
    n, h, w = ink01.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = np.zeros_like(binary)
    for i in range(n):
        cols = np.where(binary[i].any(0))[0]
        if len(cols) == 0:
            continue
        cx = (cols[0] + cols[-1]) / 2.0
        src_x = cx + (xx - cx) / s
        out[i] = map_coordinates(ink01[i], [yy, src_x], order=1, mode="constant", cval=0.0) >= 0.5
    return out


def features(binary: np.ndarray):
    dt = np.stack([distance_transform_edt(~b) if b.any() else np.full(b.shape, 99.0) for b in binary])
    b = binary.reshape(len(binary), -1).astype(np.float32)
    return b, dt.reshape(len(dt), -1).astype(np.float32), np.maximum(b.sum(1), 1.0)


def distance_matrix(ink: np.ndarray, lams=(1.0,), scales=SCALES, block=1024, log=print):
    """Returns {lam: D_stretch (float32 [N,N], symmetric)} before the hole term."""
    ink01 = ink.astype(np.float32) / 255.0
    binary = ink >= 128
    b0, dt0, c0 = features(binary)
    n = len(ink)
    best = {lam: np.full((n, n), np.inf, dtype=np.float32) for lam in lams}
    for s in scales:
        bs, dts, cs = (b0, dt0, c0) if s == 1.0 else features(stretch(ink01, binary, s))
        pen = abs(np.log(s))
        for st in range(0, n, block):
            e = min(n, st + block)
            d = 0.5 * ((bs[st:e] @ dt0.T) / cs[st:e, None] + (dts[st:e] @ b0.T) / c0[None, :])
            for lam in lams:
                np.minimum(best[lam][st:e], d + lam * pen, out=best[lam][st:e])
        log(f"  scale {s} done")
    for lam in lams:  # stretching either glyph: D = min(D, D^T), done blockwise to avoid aliasing
        m = best[lam]
        for i in range(0, n, block):
            for j in range(i, n, block):
                a = m[i:i + block, j:j + block]
                b = m[j:j + block, i:i + block].T
                mn = np.minimum(a, b)
                m[i:i + block, j:j + block] = mn
                m[j:j + block, i:i + block] = mn.T
    return best, binary


def to_similarity(dist: np.ndarray, holes: np.ndarray, mu: float, tau: float, hole_cap: int = 3,
                  block: int = 2048) -> np.ndarray:
    """uint8 similarity matrix from a stretch distance matrix plus the hole term."""
    n = len(dist)
    out = np.empty((n, n), dtype=np.uint8)
    h = holes.astype(np.float32)
    for st in range(0, n, block):
        e = min(n, st + block)
        d = dist[st:e] + mu * np.minimum(np.abs(h[st:e, None] - h[None, :]), hole_cap)
        s = np.exp(-d / tau)
        np.fill_diagonal(s[:, st:e], 1.0)
        out[st:e] = np.rint(np.clip(s, 0, 1) * 255).astype(np.uint8)
    return out
