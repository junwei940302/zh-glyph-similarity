"""Load a published table.

    from glyphsim.load import load_charset, load_matrix
    chars = load_charset("charset.tsv")
    sim = load_matrix("matrix_android_aosp_zh_tw_chamfer_t3.triu.u8.xz", len(chars))
    sim[chars.index("未"), chars.index("末")] / 255   # -> 0.94
"""
from __future__ import annotations

import csv
import lzma

import numpy as np


def load_charset(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [r["char"] for r in csv.DictReader(f, delimiter="\t")]


def load_matrix(path: str, n: int) -> np.ndarray:
    """Rebuild the full symmetric uint8 matrix from the upper-triangle file."""
    with lzma.open(path, "rb") as f:
        raw = np.frombuffer(f.read(), dtype=np.uint8)
    expected = n * (n + 1) // 2
    if raw.size != expected:
        raise ValueError(f"expected {expected} bytes for n={n}, got {raw.size}")
    sim = np.empty((n, n), dtype=np.uint8)
    pos = 0
    for i in range(n):
        row = raw[pos:pos + n - i]
        sim[i, i:] = row
        sim[i:, i] = row
        pos += n - i
    return sim
