<p align="center">
  <img src="docs/assets/logo-256.png" width="128" alt="zh-glyph-similarity logo">
</p>

<h1 align="center">zh-glyph-similarity</h1>

<p align="center">
  <b>Which characters look alike on a phone?</b><br>
  A visual-similarity table for 16,203 Traditional and Simplified Chinese characters, Bopomofo, digits and Latin letters.<br>
  Every pair is scored with one formula, on glyphs rendered with real phone fonts.
</p>

<p align="center">
  <a href="https://github.com/junwei940302/zh-glyph-similarity/releases"><img src="https://img.shields.io/github/v/release/junwei940302/zh-glyph-similarity?label=release&color=2a78d6" alt="Latest release"></a>
  <a href="#character-set"><img src="https://img.shields.io/badge/characters-16%2C203-2a78d6" alt="16,203 characters"></a>
  <a href="#character-set"><img src="https://img.shields.io/badge/scripts-Hant%20%C2%B7%20Hans%20%C2%B7%20Bopomofo%20%C2%B7%200--9%20%C2%B7%20A--z-555" alt="Scripts"></a>
  <a href="#fonts-and-platforms"><img src="https://img.shields.io/badge/fonts-Android%20%C2%B7%20iOS%20(build%20locally)-555" alt="Fonts"></a>
  <br>
  <a href="#quick-start"><img src="https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python 3.9+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/code-MIT-yellow" alt="Code: MIT"></a>
  <a href="LICENSE-DATA"><img src="https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey" alt="Data: CC BY 4.0"></a>
  <a href="https://github.com/junwei940302/zh-glyph-similarity/releases"><img src="https://img.shields.io/github/downloads/junwei940302/zh-glyph-similarity/total?color=2a78d6" alt="Downloads"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#results">Results</a> ·
  <a href="#data-files">Data files</a> ·
  <a href="https://github.com/junwei940302/zh-glyph-similarity/releases">Download</a> ·
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/hero-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/hero-light.png">
    <img alt="Characters and their look-alikes with similarity scores: 0 and O 0.93, l and I 0.95, ㄚ and 丫 0.83, 未 and 末 0.94, 撤 and 徹 0.95, 賴 and 頛 0.88" src="docs/assets/hero-light.png" width="100%">
  </picture>
</p>

Scam messages dodge keyword filters by swapping characters that look the same: `L1NE` for `LINE`, Bopomofo `ㄚ` for `丫`, a rare `頛` for `賴`. This project measures how alike any two of 16,203 characters look when a phone draws them, so filters, normalisers and test sets can account for those swaps.

## Highlights

- **Every pair, one formula.** 16,203 × 16,203 ≈ 262 million scores, all computed the same way, so a 0.90 means the same thing anywhere in the table.
- **Rendered the way phones render.** Per-character font fallback, one canvas, one font size, one baseline. The Android table is published; the iOS table builds on your own Mac.
- **Tolerates width, not shape.** A stroke-distance metric that lets glyphs stretch a little, so `0` and `O` come out as near-identical (0.93) while `0` and `8` do not top the list.
- **Checked against known look-alikes.** Unicode confusables, a curated list of look-alike pairs, a second font, and Android vs iOS.
- **Easy to use.** `pip install`, three lines of Python, a command-line tool, or a plain TSV.
- **Open and reproducible.** Open fonts, pinned character lists, SHA-256 manifests. Code under MIT, data under CC BY 4.0.

## Quick start

```bash
pip install "git+https://github.com/junwei940302/zh-glyph-similarity"
```

```python
from glyphsim import GlyphSim

gs = GlyphSim.from_release()      # downloads the table once (~90 MB), then loads from cache

gs.similarity("0", "O")           # 0.933
gs.similarity("ㄚ", "丫")          # 0.831
gs.neighbors("賴", k=3)            # [('頛', 0.878), ('赖', 0.867), ('轒', 0.847)]
gs.lookalikes("l")                # ['i', 'I', '丨']   (score >= 0.85)
```

From the command line:

```console
$ glyphsim neighbors ㄚ -k 3
  1  丫  U+4E2B  0.831
  2  Y  U+0059  0.800
  3  T  U+0054  0.627

$ glyphsim sim 未 末
0.941
```

The first call caches the table in `~/.cache/zh-glyph-similarity` (set `GLYPHSIM_CACHE` to change it). Later calls take about 0.2 s.

<details>
<summary><b>Without installing anything</b></summary>

Download `charset.tsv` and `neighbors_android_aosp_zh_tw_chamfer_st.tsv` from [Releases](https://github.com/junwei940302/zh-glyph-similarity/releases) and read them with any tool:

```python
import pandas as pd

nb = pd.read_csv("neighbors_android_aosp_zh_tw_chamfer_st.tsv", sep="\t")
nb[nb.char == "賴"].head(3)
#  char codepoint  rank neighbor neighbor_codepoint   score
#     賴    U+8CF4     1        頛             U+981B  0.8793
#     賴    U+8CF4     2        赖             U+8D56  0.8683
#     賴    U+8CF4     3        轒             U+8F52  0.8466
```

</details>

## Use cases

**Harden keyword filters.** `pattern()` turns a keyword into a regular expression that also matches look-alike spellings:

```python
import re

rx = re.compile(gs.pattern("LINE", min_score=0.8))   # 'L[Ili丨1ft][NH]E'
bool(rx.search("加L1NE領飆股"))                       # True
bool(rx.search("加LlNE好友"))                         # True
```

Other uses:
- **Normalise text** before classification by mapping rare look-alikes to the common character they imitate.
- **Build adversarial test sets** by swapping characters for high-scoring look-alikes and checking how much a model degrades.
- **Rank OCR or spelling-correction candidates** by visual closeness.

## Gallery

The most similar characters for a few queries, from the Android table:

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/gallery-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/gallery-light.png">
    <img alt="Grid of query characters with their eight most similar characters and scores" src="docs/assets/gallery-light.png" width="90%">
  </picture>
</p>

## How it works

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/how-it-works-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/how-it-works-light.png">
    <img alt="Four steps: render 0 and O, measure stroke gaps (0.81), allow width changes (0.93), score every pair" src="docs/assets/how-it-works-light.png" width="100%">
  </picture>
</p>

1. **Render like a phone.** Each character is drawn with the first font in the platform's fallback list that contains it, on a 64 × 64 canvas at 56 px, all on the same baseline. A narrow `l` and a full-width `一` keep their real size and position.
2. **Measure stroke gaps.** Strokes become point sets; the symmetric chamfer distance averages how far each stroke pixel of one glyph is from the nearest stroke of the other.
3. **Allow width changes.** Either glyph may be stretched horizontally by 0.8–1.25×; the best fit is kept, plus a penalty of 0.5 px × |ln s|. Without this step, `O` ranks fourth for `0`, behind `D`, `B` and `8`: plain chamfer penalises the 7 px width difference along the whole outline.
4. **Score every pair.** similarity = exp(−distance / 3 px), stored as `round(similarity × 255)`.

A penalty for a different number of enclosed holes (0 vs 8) was also tried; hole counts are unstable for complex characters at 64 px and it hurt Chinese results, so it is not used. The parameter grid is in [`experiments/`](experiments/).

## Results

Each known look-alike pair counts as found if the partner appears among the top *k* neighbours. Android table, same 15,537-character set for all three metrics:

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/benchmark-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/benchmark-light.png">
    <img alt="Bar charts: share of known look-alikes found in the top 1, 5 and 10 neighbours for three metrics" src="docs/assets/benchmark-light.png" width="100%">
  </picture>
</p>

Final tables (16,203 characters):

| Ground truth | Pairs | Android top 1 | Android top 5 | Android top 10 | iOS top 1 | iOS top 5 | iOS top 10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Unicode confusables (UTS #39 v18, same skeleton) | 92 | 51% | 80% | 89% | 76% | 93% | 96% |
| Curated look-alike pairs ([`groundtruth/`](groundtruth/curated_pairs.tsv)) | 140 | 51% | 87% | 93% | 50% | 87% | 91% |
| — of which Chinese–Chinese (未/末, 戊/戌, …) | 80 | 56% | 94% | 98% | | | |
| — of which digit–letter (0/O, 1/l, 5/S, …) | 14 | 50% | 93% | 100% | | | |

The pycorrector `same_stroke` list (2,818 pairs) scores low (top 10: 14%) by design: it lists characters that *share a component* (丁/盯, 王/琴), which does not make the whole glyphs look alike.

### Fonts and platforms

Do the results depend on the font? Ranks do; look-alikes mostly do not.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/fonts-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/fonts-light.png">
    <img alt="Look-alike pairs keep high scores in a rounded font; scores of 300,000 random pairs correlate with Spearman 0.93" src="docs/assets/fonts-light.png" width="100%">
  </picture>
</p>

| Comparison | Spearman (random pairs) | Pairs ≥ 0.85 in A that stay ≥ 0.80 in B | …and stay in B's top 50 | Top-10 overlap |
|---|---:|---:|---:|---:|
| Noto Sans CJK vs jf open 粉圓 (rounded)¹ | 0.93 | 98.0% | 94.2% | 0.34 |
| Android (Noto + Roboto) vs iOS (PingFang + SF Pro) | 0.93 | 97.7% | 93.0% | 0.38 |

<sub>¹ Over the 8,564 Chinese characters both fonts cover. High-scoring pairs are taken from the top 10 of 4,000 random characters (`python -m glyphsim.compare --sim-a … --sim-b …`).</sub>

Use a **score threshold** rather than a rank cut-off, and take the maximum over platforms if you need to cover both. Differences come from glyph design. Noto draws `刂` in the right half of the box, where it sits inside `到`, so on Android its nearest characters have a vertical stroke on the right (习, 书, 泪); on iOS they are other narrow components (丬, 阝, 卩).

| Table | Latin and digits | Chinese and Bopomofo | Published |
|---|---|---|---|
| `android_aosp_zh_tw` | Roboto | Noto Sans CJK TC (SC as fallback) | ✅ in Releases |
| `ios_zh_tw` | SF Pro (text size) | PingFang TC (SC as fallback) | Build on your Mac, see [why](NOTICE.md#為什麼不提供-ios-表只提供程式) |

Android brands may ship their own fonts; the table uses the AOSP defaults. The comparisons above suggest that look-alikes carry over to other sans-serif designs, while exact ranks do not. PingFang TC lacks 238 of the characters (mostly from 通用规范汉字表), so PingFang SC draws them.

## Data files

Download from [Releases](https://github.com/junwei940302/zh-glyph-similarity/releases):

| File | Size | Contents |
|---|---:|---|
| `charset.tsv` | 1 MB | The index: `index`, `char`, `codepoint`, `sets`, `name`. Row *i* is row and column *i* of the matrix. |
| `matrix_android_aosp_zh_tw_chamfer_st.triu.u8.xz` | 90 MB | Full 16,203 × 16,203 matrix: upper triangle, row-major, uint8 (score × 255), xz-compressed. `GlyphSim.from_files()` or `glyphsim.load.load_matrix()` restores it. |
| `neighbors_android_aosp_zh_tw_chamfer_st.tsv` | 26 MB | Top 50 neighbours of every character with unrounded scores: `char`, `codepoint`, `rank`, `neighbor`, `neighbor_codepoint`, `score`. |
| `manifest_android_aosp_zh_tw_chamfer_st.json` | 2 KB | Parameters, fonts, renderer and SHA-256 of each file. |

The matrix stores scores in steps of 1/255; the TSV keeps the unrounded value, so ties in the matrix can order neighbours slightly differently.

## Character set

| Group | Source | Characters |
|---|---|---:|
| Bopomofo | U+3105–U+3129 and the five tone marks | 42 |
| Digits and Latin letters | ASCII 0–9, A–Z, a–z | 62 |
| Traditional (encoding) | Big5 level 1 + level 2 | 5,401 + 7,652 |
| Simplified (encoding) | GB2312 level 1 + level 2 | 3,755 + 3,008 |
| Taiwan standard lists | Ministry of Education common + less-common characters | 4,808 + 6,343 |
| Mainland standard list | 通用规范汉字表, levels 1–3 | 3,500 + 3,000 + 1,605 |

The union is 16,203 characters. The first 15,537 (Big5 ∪ GB2312) keep the same positions as in the first version; `python -m glyphsim.charset --no-lists` rebuilds that set. Each source adds characters the others lack. GB2312 has the radical components (冂 匚 勹 卩 厶 凵 攵) that the Bopomofo letters ㄇ ㄈ ㄅ ㄗ ㄙ ㄩ ㄆ were derived from, which 通用规范汉字表 omits; level 3 of 通用规范汉字表 adds name and place characters that are mostly missing from GB2312. The `sets` column (`big5_1`, `moe_1`, `tgh_3`, …) lets you slice the matrix to any subset without recomputing.

## Build from source

```bash
git clone https://github.com/junwei940302/zh-glyph-similarity
cd zh-glyph-similarity
python -m venv .venv && source .venv/bin/activate
pip install -e ".[build]"

# any OS; downloads the open fonts
scripts/run_stack.sh android_aosp_zh_tw
# macOS only; reads the fonts that ship with macOS
scripts/run_stack.sh ios_zh_tw
# writes release/
python -m glyphsim.export android_aosp_zh_tw_chamfer_st
# compare two tables
python -m glyphsim.compare data/topk_android_aosp_zh_tw_chamfer_st.npz data/topk_ios_zh_tw_chamfer_st.npz \
  --sim-a data/sim_android_aosp_zh_tw_chamfer_st.npy --sim-b data/sim_ios_zh_tw_chamfer_st.npy
```

On a MacBook Air M2 a table takes about a minute (export about two more) and needs about 2.5 GB of RAM and 300 MB of disk. Outputs go to `data/`; set `OUT=/path` to write elsewhere. `python docs/figures/make_figures.py` rebuilds the figures in this README.

The Android table built on Linux (OpenBLAS) and on macOS (Accelerate) gives identical evaluation scores. A few cells can differ by 1/255 because floating-point sums run in a different order, so the SHA-256 in `manifest_*.json` identifies the released files.

## Limitations

- **Shape only.** Sound-alike swaps (Bopomofo spelling such as `ㄌㄞˋ` for `賴`, homophones) are not covered.
- **One design per platform.** Brand fonts reorder neighbours; use thresholds, not ranks.
- **Regular weight, 64 px.** Bold text and very small sizes are not modelled.
- **Ground truth is limited.** The curated pairs were assembled by the maintainer; a human-rated benchmark is planned.
- **`pattern()` matches characters only.** Inserted spaces or symbols (`L I N E`) need separate normalisation.

## FAQ

<details>
<summary><b>Why not just use Unicode's confusables.txt?</b></summary>

It is built for identifiers and domain names. It contains only 15 lines involving Bopomofo, does not link `ㄧ` to `一`, and treats pairs such as 未/末 and 土/士 as the same character, which is too aggressive for running Chinese text. It also gives a yes/no answer, not a score.
</details>

<details>
<summary><b>Why is there no iOS table in Releases?</b></summary>

Apple's fonts may only be used on Apple systems and may not be redistributed. The scores are derived from those fonts, so this project ships the code and lets you build the table on your own Mac. Details in <a href="NOTICE.md">NOTICE.md</a>.
</details>

<details>
<summary><b>How do I get a smaller table?</b></summary>

Filter <code>charset.tsv</code> by the <code>sets</code> column (for example <code>moe_1</code> and <code>tgh_1</code> for common characters) and take those rows and columns of the matrix. Scores do not depend on which other characters are in the table.
</details>

## Citation

If you use this table, please cite it. GitHub's **Cite this repository** button reads [`CITATION.cff`](CITATION.cff).

```bibtex
@misc{huang2026zhglyphsimilarity,
  author       = {Huang, Jun-Wei},
  title        = {zh-glyph-similarity: A visual-similarity table for Chinese characters, Bopomofo, digits and Latin letters},
  year         = {2026},
  version      = {1.0.0},
  howpublished = {\url{https://github.com/junwei940302/zh-glyph-similarity}}
}
```

## Acknowledgements

- [Noto Sans CJK](https://github.com/notofonts/noto-cjk) and [Roboto](https://github.com/google/fonts/tree/main/ofl/roboto) (SIL OFL), [jf open 粉圓](https://github.com/justfont/open-huninn-font) (SIL OFL).
- [Unicode UTS #39](https://www.unicode.org/reports/tr39/) confusables and [pycorrector](https://github.com/shibing624/pycorrector) for ground truth.
- [ButTaiwan/cjktables](https://github.com/ButTaiwan/cjktables) for machine-readable standard character lists.
- Built for SpamGuard, a research project on detecting scam text messages in Taiwan.

## License

Code: [MIT](LICENSE). Data (character index, tables, curated pairs, evaluation results): [CC BY 4.0](LICENSE-DATA). Third-party data and fonts: [NOTICE.md](NOTICE.md).
