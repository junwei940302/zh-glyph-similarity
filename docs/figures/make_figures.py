"""Build the README figures (light and dark variants) into docs/assets/.

Only open fonts are used (Noto Sans CJK, Roboto, jf open 粉圓); no Apple glyph is drawn.
Inputs are the files produced by scripts/run_stack.sh for the Android stack and the
font-sensitivity stack, plus experiments/results/*.json.

    python docs/figures/make_figures.py --data data
"""
from __future__ import annotations

import argparse
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from scipy.ndimage import distance_transform_edt, map_coordinates  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS = os.path.join(ROOT, "vendor", "fonts")
NOTO_TTC = os.path.join(FONTS, "NotoSansCJK-Regular.ttc")
NOTO_TC_OTF = os.path.join(FONTS, "NotoSansTC-Regular.otf")
ROBOTO = os.path.join(FONTS, "Roboto[wdth,wght].ttf")
HUNINN = os.path.join(FONTS, "jf-openhuninn-2.1.ttf")
OUT = os.path.join(ROOT, "docs", "assets")

THEMES = {
    "light": dict(card="#ffffff", border="#d0d7de", text="#1f2328", text2="#59636e", muted="#8c959f",
                  track="#eaeef2", s1="#2a78d6", s2="#eb6834", s3="#1baf7a",
                  ramp=["#f6f8fa", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]),
    "dark": dict(card="#161b22", border="#30363d", text="#e6edf3", text2="#9198a1", muted="#6e7681",
                 track="#21262d", s1="#3987e5", s2="#d95926", s3="#199e70",
                 ramp=["#0d1117", "#0d366b", "#104281", "#184f95", "#1c5cab", "#256abf", "#3987e5", "#86b6ef"]),
}
S = 2  # pixel scale for crisp images on high-density screens


# ---------------------------------------------------------------- helpers
def is_alnum(ch: str) -> bool:
    return ch.isascii() or ch in "ˉˊˇˋ˙"


def glyph_font(ch: str, px: int, family: str = "noto") -> ImageFont.FreeTypeFont:
    if family == "huninn" and not is_alnum(ch):
        return ImageFont.truetype(HUNINN, px)
    if is_alnum(ch):
        f = ImageFont.truetype(ROBOTO, px)
        f.set_variation_by_axes([400, 100])
        return f
    return ImageFont.truetype(NOTO_TTC, px, index=3)


def ui_font(px: int, bold: bool = False, cjk: bool = False) -> ImageFont.FreeTypeFont:
    if cjk:
        return ImageFont.truetype(NOTO_TC_OTF, px)
    f = ImageFont.truetype(ROBOTO, px)
    f.set_variation_by_axes([700 if bold else 400, 100])
    return f


def draw_glyph(draw, ch, cx, cy, px, color, family="noto"):
    f = glyph_font(ch, px, family)
    draw.text((cx, cy), ch, font=f, fill=color, anchor="mm")


def rounded(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def score_bar(draw, x, y, w, h, score, t, color):
    rounded(draw, (x, y, x + w, y + h), h // 2, fill=t["track"])
    rounded(draw, (x, y, x + max(h, int(w * score)), y + h), h // 2, fill=color)


def save(img: Image.Image, name: str):
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, name), optimize=True)
    print("wrote", name, img.size)


class Table:
    def __init__(self, data_dir: str, stack: str):
        with open(os.path.join(ROOT, "data", "charset.tsv"), encoding="utf-8") as f:
            self.rows = list(csv.DictReader(f, delimiter="\t"))
        self.chars = [r["char"] for r in self.rows]
        self.idx = {c: i for i, c in enumerate(self.chars)}
        self.sim = np.load(os.path.join(data_dir, f"sim_{stack}_chamfer_st.npy"), mmap_mode="r")

    def score(self, a, b):
        return int(self.sim[self.idx[a], self.idx[b]]) / 255.0

    def neighbors(self, ch, k):
        i = self.idx[ch]
        row = np.asarray(self.sim[i]).astype(np.int16)
        row[i] = -1
        top = np.argsort(-row, kind="stable")[:k]
        return [(self.chars[j], row[j] / 255.0) for j in top]


# ---------------------------------------------------------------- hero
HERO = [("0", ["O", "D"]), ("l", ["I", "丨"]), ("ㄚ", ["丫", "Y"]), ("ㄧ", ["一"]),
        ("未", ["末", "朱"]), ("土", ["士"]), ("撤", ["徹", "撒"]), ("賴", ["頛", "赖"])]


def hero(tab: Table, theme: str):
    t = THEMES[theme]
    cols, rows_ = 4, 2
    cw, ch_, gap, pad = 300 * S, 230 * S, 16 * S, 4 * S
    W = pad * 2 + cols * cw + (cols - 1) * gap
    H = pad * 2 + rows_ * ch_ + (rows_ - 1) * gap + 34 * S
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k, (q, alts) in enumerate(HERO):
        r, c = divmod(k, cols)
        x0 = pad + c * (cw + gap)
        y0 = pad + r * (ch_ + gap)
        rounded(d, (x0, y0, x0 + cw, y0 + ch_), 14 * S, fill=t["card"], outline=t["border"], width=S)
        # query glyph on the left
        qx, qy = x0 + 70 * S, y0 + ch_ // 2 - 8 * S
        draw_glyph(d, q, qx, qy, 84 * S, t["text"])
        d.text((qx, y0 + ch_ - 26 * S), f"U+{ord(q):04X}", font=ui_font(11 * S), fill=t["muted"], anchor="mm")
        d.text((x0 + 140 * S, qy), "≈", font=ui_font(26 * S), fill=t["muted"], anchor="mm")
        # look-alikes on the right
        n = len(alts)
        for j, a in enumerate(alts):
            sc = tab.score(q, a)
            ay = y0 + ch_ // 2 + (j - (n - 1) / 2) * 96 * S
            ax = x0 + 196 * S
            draw_glyph(d, a, ax, ay - 8 * S, 58 * S, t["text"])
            bx = x0 + 236 * S
            d.text((bx, ay - 24 * S), f"{sc:.2f}", font=ui_font(15 * S, bold=True), fill=t["text"], anchor="lm")
            score_bar(d, bx, ay - 4 * S, 48 * S, 6 * S, sc, t, t["s1"])
            d.text((bx, ay + 14 * S), f"U+{ord(a):04X}", font=ui_font(10 * S), fill=t["muted"], anchor="lm")
    d.text((W // 2, H - 16 * S), "Similarity on an Android phone (Noto Sans CJK + Roboto). 1.00 = identical glyphs.",
           font=ui_font(12 * S), fill=t["text2"], anchor="mm")
    save(img, f"hero-{theme}.png")


# ---------------------------------------------------------------- gallery
GALLERY = "0l1Sㄧㄚㄇ未己鳥撤賴詐"


def gallery(tab: Table, theme: str, k: int = 8):
    t = THEMES[theme]
    tile_w, tile_h, gap, pad, lab = 92 * S, 116 * S, 8 * S, 4 * S, 18 * S
    W = pad * 2 + (k + 1) * tile_w + k * gap + 14 * S
    H = pad * 2 + len(GALLERY) * tile_h + (len(GALLERY) - 1) * gap // 2 + lab + 8 * S
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((pad + tile_w // 2, pad + lab // 2), "query", font=ui_font(12 * S, bold=True), fill=t["text2"], anchor="mm")
    d.text((pad + tile_w + 14 * S + (k * (tile_w + gap)) // 2, pad + lab // 2),
           f"{k} most similar characters", font=ui_font(12 * S, bold=True), fill=t["text2"], anchor="mm")
    for r, q in enumerate(GALLERY):
        y0 = pad + lab + 8 * S + r * (tile_h + gap // 2)
        rounded(d, (pad, y0, pad + tile_w, y0 + tile_h - 6 * S), 10 * S, fill=t["card"], outline=t["s1"], width=2 * S)
        draw_glyph(d, q, pad + tile_w // 2, y0 + 46 * S, 60 * S, t["text"])
        d.text((pad + tile_w // 2, y0 + 92 * S), f"U+{ord(q):04X}", font=ui_font(10 * S), fill=t["muted"], anchor="mm")
        for j, (c, sc) in enumerate(tab.neighbors(q, k)):
            x0 = pad + tile_w + 14 * S + j * (tile_w + gap)
            rounded(d, (x0, y0, x0 + tile_w, y0 + tile_h - 6 * S), 10 * S, fill=t["card"], outline=t["border"], width=S)
            draw_glyph(d, c, x0 + tile_w // 2, y0 + 42 * S, 54 * S, t["text"])
            d.text((x0 + 12 * S, y0 + 86 * S), f"{sc:.2f}", font=ui_font(12 * S, bold=True), fill=t["text"], anchor="lm")
            score_bar(d, x0 + 48 * S, y0 + 84 * S, tile_w - 60 * S, 5 * S, sc, t, t["s1"])
    save(img, f"gallery-{theme}.png")


# ---------------------------------------------------------------- how it works
def how_it_works(tab: Table, theme: str, ink: np.ndarray):
    """Uses the Android render and glyphsim.chamfer_st, so the numbers match the published table."""
    import sys
    sys.path.insert(0, ROOT)
    from glyphsim.chamfer_st import SCALES, stretch
    t = THEMES[theme]
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("seq", t["ramp"][:5])
    i0, iO = tab.idx["0"], tab.idx["O"]
    g = ink[[i0, iO]].astype(np.float32) / 255.0
    b0, bO = g[0] >= 128 / 255, g[1] >= 128 / 255

    def chamfer(a, b):
        return 0.5 * (distance_transform_edt(~b)[a].mean() + distance_transform_edt(~a)[b].mean())

    d_plain = chamfer(b0, bO)
    cands = []
    for s_ in SCALES:
        st = stretch(g, g >= 128 / 255, s_)
        cands.append((chamfer(st[0], bO) + 0.5 * abs(np.log(s_)), s_, "0", st[0]))
        cands.append((chamfer(b0, st[1]) + 0.5 * abs(np.log(s_)), s_, "O", st[1]))
    d_st, s_best, which, st_img = min(cands, key=lambda c: c[0])
    sim_plain, sim_st = np.exp(-d_plain / 3), tab.score("0", "O")

    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.9), dpi=150, gridspec_kw={"width_ratios": [2.125, 1, 1, 1]})
    fig.patch.set_alpha(0)

    def layer(ax, bin_img, color, alpha):
        rgba = np.zeros((64, 64, 4))
        rgba[..., :3] = matplotlib.colors.to_rgb(color)
        rgba[..., 3] = bin_img * alpha
        ax.imshow(rgba, interpolation="nearest")

    ax = axes[0]
    pair = np.ones((64, 136, 3))
    pair[...] = matplotlib.colors.to_rgb(t["card"])
    for x0, gl in ((0, g[0]), (72, g[1])):
        for c in range(3):
            pair[:, x0:x0 + 64, c] = pair[:, x0:x0 + 64, c] * (1 - gl) + matplotlib.colors.to_rgb(t["text"])[c] * gl
    ax.imshow(pair, interpolation="nearest")
    ax.set_title("1  Render like a phone", loc="left", color=t["text"], fontsize=12)
    ax.set_xlabel("same 64×64 canvas, font size and baseline", color=t["text2"], fontsize=9.5)

    fixed, moving = (bO, b0) if which == "0" else (b0, bO)
    ax = axes[1]
    ax.imshow(distance_transform_edt(~bO), cmap=cmap, interpolation="nearest")
    layer(ax, bO, t["text"], 0.9)
    layer(ax, b0, t["s2"], 0.8)
    ax.set_title("2  Measure stroke gaps", loc="left", color=t["text"], fontsize=12)
    ax.set_xlabel(f"0 (orange) over O: gap {d_plain:.2f} px → {sim_plain:.2f}", color=t["text2"], fontsize=9.5)

    ax = axes[2]
    ax.imshow(distance_transform_edt(~fixed), cmap=cmap, interpolation="nearest")
    layer(ax, fixed, t["text"], 0.9)
    layer(ax, st_img, t["s2"], 0.8)
    ax.set_title("3  Allow width changes", loc="left", color=t["text"], fontsize=12)
    ax.set_xlabel(f"{which} stretched ×{s_best:g}: {d_st:.2f} px incl. penalty → {sim_st:.2f}",
                  color=t["text2"], fontsize=9.5)

    ax = axes[3]
    labels = list("0ODQC8B35S")
    m = np.array([[tab.score(a, b) for b in labels] for a in labels])
    heat = matplotlib.colors.LinearSegmentedColormap.from_list("heat", t["ramp"][1:])
    ax.imshow(m, cmap=heat, vmin=0.4, vmax=1.0, interpolation="nearest")
    ax.set_xticks(range(len(labels)), labels, color=t["text"], fontsize=9)
    ax.set_yticks(range(len(labels)), labels, color=t["text"], fontsize=9)
    ax.tick_params(length=0)
    ax.set_title("4  Score every pair", loc="left", color=t["text"], fontsize=12)
    ax.set_xlabel("16,203 × 16,203 pairs, one formula\n" + ("darker" if theme == "light" else "brighter") + " = more alike",
                  color=t["text2"], fontsize=9.5)
    for a in axes[:3]:
        a.set_xticks([])
        a.set_yticks([])
    for a in axes:
        for sp in a.spines.values():
            sp.set_color(t["border"])
    fig.tight_layout(w_pad=1.6)
    fig.savefig(os.path.join(OUT, f"how-it-works-{theme}.png"), transparent=True)
    plt.close(fig)
    print("wrote", f"how-it-works-{theme}.png", f"plain {d_plain:.3f}px/{sim_plain:.3f}; {which} x{s_best} {d_st:.3f}px/{sim_st:.3f}")


# ---------------------------------------------------------------- benchmark
def benchmark(theme: str):
    t = THEMES[theme]
    v1 = json.load(open(os.path.join(ROOT, "experiments", "results", "v1_metrics_android.json"), encoding="utf-8"))
    grid = json.load(open(os.path.join(ROOT, "experiments", "results", "chamfer_st_grid_android.json"), encoding="utf-8"))
    pick = {k.split("/")[-1]: v for k, v in v1.items()}
    methods = [
        ("blurred-image cosine", pick["sim_android_aosp_zh_tw_blurcos_s1.5.npy"], t["s3"]),
        ("chamfer", pick["sim_android_aosp_zh_tw_chamfer_t3.npy"], t["s2"]),
        ("chamfer_st (this table)", grid["lam0.5_mu0.0"], t["s1"]),
    ]
    sets = [("unicode", "Unicode confusables (88 pairs)"), ("curated", "Curated look-alike pairs (140 pairs)")]
    ks = ["R@1", "R@5", "R@10"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), dpi=150, sharey=True)
    fig.patch.set_alpha(0)
    w = 0.26
    for ax, (key, title) in zip(axes, sets):
        x = np.arange(len(ks))
        for m, (name, res, color) in enumerate(methods):
            vals = [res[key][k] * 100 for k in ks]
            bars = ax.bar(x + (m - 1) * (w + 0.02), vals, w, color=color, label=name, linewidth=0)
            if m == 2:
                for b, v in zip(bars, vals):
                    ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.0f}", ha="center", va="bottom",
                            color=t["text"], fontsize=9, fontweight="bold")
        ax.set_xticks(x, ["top 1", "top 5", "top 10"], color=t["text"], fontsize=10)
        ax.set_title(title, loc="left", color=t["text"], fontsize=11.5)
        ax.set_ylim(0, 105)
        ax.yaxis.grid(True, color=t["border"], linewidth=0.6)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(t["border"])
        ax.tick_params(colors=t["text2"], length=0)
        ax.patch.set_alpha(0)
    axes[0].set_ylabel("known look-alike found (%)", color=t["text2"], fontsize=10)
    handles, labels = axes[0].get_legend_handles_labels()
    leg = fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, fontsize=10,
                     bbox_to_anchor=(0.5, 1.02))
    for txt in leg.get_texts():
        txt.set_color(t["text"])
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(os.path.join(OUT, f"benchmark-{theme}.png"), transparent=True)
    plt.close(fig)
    print("wrote", f"benchmark-{theme}.png")


# ---------------------------------------------------------------- fonts
PAIRS = [("未", "末"), ("鳥", "島"), ("撤", "徹"), ("己", "已"), ("土", "士"), ("戊", "戌")]


def fonts(tab: Table, sens: np.ndarray, sens_font: np.ndarray, theme: str):
    t = THEMES[theme]
    n = sens.shape[0]
    han = np.array([("big5" in r["sets"] or "gb2312" in r["sets"]) for r in tab.rows[:n]]) & (sens_font == 1)
    idx = np.where(han)[0]
    rng = np.random.default_rng(0)
    p, q = rng.choice(idx, 300000), rng.choice(idx, 300000)
    a = np.asarray(tab.sim[p, q], dtype=np.float32) / 255
    b = np.asarray(sens[p, q], dtype=np.float32) / 255
    from scipy.stats import spearmanr
    rho = spearmanr(a, b)[0]

    fig = plt.figure(figsize=(11.5, 4.0), dpi=150)
    fig.patch.set_alpha(0)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1])
    ax = fig.add_subplot(gs[0])
    ax.set_xlim(0, len(PAIRS))
    ax.set_ylim(-0.1, 2.5)
    ax.axis("off")
    fp_noto = font_manager.FontProperties(fname=NOTO_TC_OTF)
    fp_hun = font_manager.FontProperties(fname=HUNINN)
    for row, (fp, label, getter) in enumerate([(fp_noto, "Noto Sans CJK (Android)", lambda x, y: tab.score(x, y)),
                                               (fp_hun, "jf open 粉圓 (rounded)", lambda x, y: sens[tab.idx[x], tab.idx[y]] / 255)]):
        y = 1.75 - row * 1.25
        ax.text(0.02, y + 0.42, label, color=t["text2"], fontsize=10, fontproperties=fp_noto)
        for k, (x1, x2) in enumerate(PAIRS):
            ax.text(k + 0.3, y, x1, fontproperties=fp, fontsize=24, color=t["text"], ha="center", va="center")
            ax.text(k + 0.7, y, x2, fontproperties=fp, fontsize=24, color=t["text"], ha="center", va="center")
            ax.text(k + 0.5, y - 0.36, f"{getter(x1, x2):.2f}", fontsize=10, color=t["text"], ha="center",
                    fontweight="bold")
    ax.set_title("Same pairs, different fonts", loc="left", color=t["text"], fontsize=11.5)

    ax = fig.add_subplot(gs[1])
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("seq", t["ramp"][1:])
    hb = ax.hexbin(a, b, gridsize=45, bins="log", cmap=cmap, mincnt=1, linewidths=0, extent=(0, 1, 0, 1))
    ax.plot([0, 1], [0, 1], color=t["muted"], linewidth=1, linestyle="--")
    ax.set_xlabel("similarity with Noto Sans CJK", color=t["text2"], fontsize=10)
    ax.set_ylabel("similarity with jf open 粉圓", color=t["text2"], fontsize=10, fontproperties=fp_noto)
    ax.set_title(f"300,000 random pairs · Spearman ρ = {rho:.2f}", loc="left", color=t["text"], fontsize=11.5)
    ax.tick_params(colors=t["text2"], length=0)
    for sp in ax.spines.values():
        sp.set_color(t["border"])
    ax.patch.set_alpha(0)
    fig.tight_layout(w_pad=2.5)
    fig.savefig(os.path.join(OUT, f"fonts-{theme}.png"), transparent=True)
    plt.close(fig)
    print("wrote", f"fonts-{theme}.png", f"rho {rho:.3f}")


# ---------------------------------------------------------------- logo
def logo():
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = Image.new("RGBA", (size, size))
    top, bot = np.array([57, 135, 229]), np.array([16, 66, 129])
    ramp = (top[None, :] * (1 - np.linspace(0, 1, size))[:, None] + bot[None, :] * np.linspace(0, 1, size)[:, None])
    arr = np.concatenate([np.repeat(ramp[:, None, :], size, axis=1), np.full((size, size, 1), 255)], axis=2)
    grad = Image.fromarray(arr.astype(np.uint8), "RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=230, fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(NOTO_TTC, 560, index=3)
    ghost = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(ghost).text((size // 2 - 70, size // 2 - 40), "ㄚ", font=f, fill=(255, 255, 255, 110), anchor="mm")
    img = Image.alpha_composite(img, ghost)
    d = ImageDraw.Draw(img)
    d.text((size // 2 + 70, size // 2 + 30), "丫", font=f, fill=(255, 255, 255, 255), anchor="mm")
    save(img, "logo.png")
    save(img.resize((256, 256), Image.LANCZOS), "logo-256.png")


def social(tab: Table):
    t = THEMES["light"]
    W, H = 1280, 640
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    lg = Image.open(os.path.join(OUT, "logo.png")).resize((300, 300), Image.LANCZOS)
    img.paste(lg, (130, 150), lg)
    d.text((500, 210), "zh-glyph-similarity", font=ui_font(78, bold=True), fill=t["text"], anchor="lm")
    d.text((500, 300), "Which characters look alike on a phone?", font=ui_font(40), fill=t["text2"], anchor="lm")
    d.text((500, 360), "16,203 Hant · Hans · Bopomofo · digits · Latin", font=ui_font(34), fill=t["text2"], anchor="lm")
    x = 500
    for q, a in [("0", "O"), ("ㄚ", "丫"), ("未", "末")]:
        rounded(d, (x, 440, x + 230, 550), 22, fill=t["card"], outline=t["border"], width=3)
        draw_glyph(d, q, x + 52, 492, 60, t["text"])
        draw_glyph(d, a, x + 122, 492, 60, t["text"])
        d.text((x + 188, 496), f"{tab.score(q, a):.2f}", font=ui_font(26, bold=True), fill=t["s1"], anchor="mm")
        x += 250
    save(img, "social-preview.png")


def main():
    font_manager.fontManager.addfont(NOTO_TC_OTF)
    plt.rcParams.update({"font.family": font_manager.FontProperties(fname=NOTO_TC_OTF).get_name()})
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    args = ap.parse_args()
    tab = Table(args.data, "android_aosp_zh_tw")
    ink = np.load(os.path.join(args.data, "render_android_aosp_zh_tw.npz"))["ink"]
    sens_path = os.path.join(args.data, "sim_sensitivity_jf_openhuninn_chamfer_st.npy")
    for theme in THEMES:
        hero(tab, theme)
        gallery(tab, theme)
        how_it_works(tab, theme, ink)
        benchmark(theme)
        if os.path.exists(sens_path):
            sens = np.load(sens_path, mmap_mode="r")
            sens_font = np.load(os.path.join(args.data, "render_sensitivity_jf_openhuninn.npz"))["font"]
            fonts(tab, sens, sens_font, theme)
    logo()
    social(tab)


if __name__ == "__main__":
    main()
