"""Backward-compatible helpers; see glyphsim.api for the full interface.

    from glyphsim.load import load_charset, load_matrix
    chars = load_charset("charset.tsv")
    sim = load_matrix("matrix_android_aosp_zh_tw_chamfer_st.triu.u8.xz", len(chars))
"""
from __future__ import annotations

from .api import read_charset as load_charset  # noqa: F401
from .api import read_triu_xz as load_matrix  # noqa: F401
