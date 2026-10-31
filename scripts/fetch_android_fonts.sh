#!/usr/bin/env bash
# Download the AOSP default fonts (both SIL OFL 1.1) into vendor/fonts.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p vendor/fonts
base=https://raw.githubusercontent.com
curl -fL -o vendor/fonts/NotoSansCJK-Regular.ttc "$base/notofonts/noto-cjk/main/Sans/OTC/NotoSansCJK-Regular.ttc"
curl -fL -o "vendor/fonts/Roboto[wdth,wght].ttf" "$base/google/fonts/main/ofl/roboto/Roboto%5Bwdth,wght%5D.ttf"

# Optional: rounded design used only for the font-sensitivity check (stack sensitivity_jf_openhuninn)
if [[ "${WITH_SENSITIVITY:-0}" == 1 ]]; then
  curl -fL -o vendor/fonts/jf-openhuninn-2.1.ttf "$base/justfont/open-huninn-font/master/font/jf-openhuninn-2.1.ttf"
fi
shasum -a 256 vendor/fonts/* 2>/dev/null || sha256sum vendor/fonts/*
