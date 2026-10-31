#!/usr/bin/env bash
# Build one table end to end.
#   scripts/run_stack.sh android_aosp_zh_tw            # anywhere (fonts are downloaded)
#   scripts/run_stack.sh ios_zh_tw                     # macOS only (uses the Mac's own fonts)
# Optional: OUT=/Volumes/AndroidAVD/glyphsim-data to keep the 240 MB matrices off the internal disk.
set -euo pipefail
cd "$(dirname "$0")/.."
stack=${1:?stack name}
out=${OUT:-data}
py=${PYTHON:-python3}
mkdir -p "$out"

stacks=stacks.json
if [[ "$stack" == ios_* ]]; then
  "$py" scripts/find_apple_fonts.py > stacks.local.json
  stacks=stacks.local.json
elif [[ ! -f vendor/fonts/NotoSansCJK-Regular.ttc ]]; then
  scripts/fetch_android_fonts.sh
fi

if [[ ! -f data/charset.tsv ]]; then
  [[ -f vendor/charlists/tongyong_guifan.txt ]] || scripts/fetch_charlists.sh
  "$py" -m glyphsim.charset -o data/charset.tsv
fi
"$py" -m glyphsim.render --stacks "$stacks" --stack "$stack" -o "$out/render_$stack.npz"
"$py" -m glyphsim.similarity "$out/render_$stack.npz" --metric chamfer_st --tau 3 --lam 0.5 --tag "" --outdir "$out"
"$py" -m glyphsim.evaluate "$out/sim_${stack}_chamfer_st.npy" --json "$out/eval_${stack}.json"
"$py" -m glyphsim.preview "$out/render_$stack.npz" "$out/topk_${stack}_chamfer_st.npz" \
  --queries 'ㄧㄚㄦㄇㄅㄉ0Ol1S未己土鳥侯撤賴飆股詐' -o "$out/preview_${stack}.png"
echo "done: $out/sim_${stack}_chamfer_st.npy, $out/topk_${stack}_chamfer_st.npz, $out/preview_${stack}.png"
