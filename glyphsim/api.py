"""High-level access to the published tables.

    from glyphsim import GlyphSim
    gs = GlyphSim.from_release()          # downloads once, then loads from the cache
    gs.similarity("0", "O")               # 0.933
    gs.neighbors("賴", k=5)                # [('頛', 0.882), ('赖', 0.871), ...]
    gs.lookalikes("l", min_score=0.85)    # ['i', 'I', '丨', '|']
    gs.pattern("LINE", min_score=0.85)    # regex character classes per character

Only numpy and the standard library are needed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import lzma
import os
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np

REPO = "junwei940302/zh-glyph-similarity"
DEFAULT_VERSION = "v1.0.0"
DEFAULT_TABLE = "android_aosp_zh_tw_chamfer_st"


def cache_dir() -> Path:
    root = os.environ.get("GLYPHSIM_CACHE") or os.path.join(
        os.environ.get("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache")), "zh-glyph-similarity")
    return Path(root)


def _download(url: str, dest: Path, quiet: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    if not quiet:
        print(f"downloading {url}", file=sys.stderr)
    with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dest)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_charset(path) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [r["char"] for r in csv.DictReader(f, delimiter="\t")]


def read_triu_xz(path, n: int) -> np.ndarray:
    """Rebuild the full symmetric uint8 matrix from a published upper-triangle file."""
    with lzma.open(path, "rb") as f:
        raw = np.frombuffer(f.read(), dtype=np.uint8)
    if raw.size != n * (n + 1) // 2:
        raise ValueError(f"expected {n * (n + 1) // 2} bytes for n={n}, got {raw.size}")
    sim = np.empty((n, n), dtype=np.uint8)
    pos = 0
    for i in range(n):
        row = raw[pos:pos + n - i]
        sim[i, i:] = row
        sim[i:, i] = row
        pos += n - i
    return sim


class GlyphSim:
    """A visual-similarity table: scores in [0, 1], 1 = identical glyph."""

    def __init__(self, chars: list[str], matrix: np.ndarray, name: str = ""):
        if matrix.shape != (len(chars), len(chars)):
            raise ValueError("matrix shape does not match the character list")
        self.chars = chars
        self.index = {c: i for i, c in enumerate(chars)}
        self.matrix = matrix  # uint8, score = value / 255
        self.name = name

    # ---------- loading ----------
    @classmethod
    def from_release(cls, table: str = DEFAULT_TABLE, version: str = DEFAULT_VERSION,
                     cache: str | os.PathLike | None = None, quiet: bool = False) -> "GlyphSim":
        """Download (once) and load a table published in this repo's GitHub Releases."""
        folder = Path(cache) if cache else cache_dir() / version
        base = f"https://github.com/{REPO}/releases/download/{version}"
        charset = folder / "charset.tsv"
        manifest = folder / f"manifest_{table}.json"
        xz = folder / f"matrix_{table}.triu.u8.xz"
        npy = folder / f"matrix_{table}.npy"
        for p in (charset, manifest):
            if not p.exists():
                _download(f"{base}/{p.name}", p, quiet)
        if not npy.exists():
            if not xz.exists():
                _download(f"{base}/{xz.name}", xz, quiet)
            want = json.loads(manifest.read_text(encoding="utf-8"))["files"][xz.name]["sha256"]
            if _sha256(xz) != want:
                xz.unlink()
                raise IOError(f"checksum mismatch for {xz.name}; deleted, please retry")
            chars = read_charset(charset)
            if not quiet:
                print("decompressing (first run only)...", file=sys.stderr)
            np.save(npy, read_triu_xz(xz, len(chars)))
            xz.unlink()  # the .npy cache replaces it
        chars = read_charset(charset)
        return cls(chars, np.load(npy, mmap_mode="r"), name=f"{table}@{version}")

    @classmethod
    def from_files(cls, charset: str | os.PathLike, matrix: str | os.PathLike) -> "GlyphSim":
        """Load local files: a charset.tsv plus a matrix as .npy or .triu.u8.xz."""
        chars = read_charset(charset)
        m = str(matrix)
        mat = np.load(m, mmap_mode="r") if m.endswith(".npy") else read_triu_xz(m, len(chars))
        return cls(chars, mat, name=Path(m).name)

    # ---------- queries ----------
    def __contains__(self, ch: str) -> bool:
        return ch in self.index

    def _i(self, ch: str) -> int:
        try:
            return self.index[ch]
        except KeyError:
            raise KeyError(f"{ch!r} (U+{ord(ch):04X}) is not in the table") from None

    def similarity(self, a: str, b: str) -> float:
        """Visual similarity of two characters, 0..1."""
        return round(int(self.matrix[self._i(a), self._i(b)]) / 255.0, 3)

    def neighbors(self, ch: str, k: int = 10, min_score: float = 0.0) -> list[tuple[str, float]]:
        """The k most similar characters (the character itself excluded)."""
        i = self._i(ch)
        row = np.asarray(self.matrix[i]).astype(np.int16)
        row[i] = -1
        top = np.argsort(-row, kind="stable")[:k]
        out = [(self.chars[int(j)], round(int(row[j]) / 255.0, 3)) for j in top]
        return [x for x in out if x[1] >= min_score]

    def lookalikes(self, ch: str, min_score: float = 0.85, limit: int = 50) -> list[str]:
        """Characters scoring at least min_score against ch, most similar first."""
        if ch not in self.index:
            return []
        return [c for c, _ in self.neighbors(ch, k=limit, min_score=min_score)]

    def pattern(self, text: str, min_score: float = 0.85, limit: int = 20) -> str:
        """A regular expression matching text and its look-alike spellings, one character class per character."""
        parts = []
        for ch in text:
            alts = [ch] + self.lookalikes(ch, min_score=min_score, limit=limit)
            parts.append(re.escape(ch) if len(alts) == 1 else
                         "[" + "".join(re.escape(c) for c in dict.fromkeys(alts)) + "]")
        return "".join(parts)

    def __repr__(self) -> str:
        return f"GlyphSim({self.name or 'table'}, {len(self.chars)} characters)"
