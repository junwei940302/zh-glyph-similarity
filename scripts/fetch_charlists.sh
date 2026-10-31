#!/usr/bin/env bash
# Download the official character lists used by glyphsim.charset into vendor/charlists.
#   - 教育部《常用國字標準字體表》(4,808) and《次常用國字標準字體表》(6,343)
#   - 《通用规范汉字表》(2013, 8,105: levels 1/2/3 = 3,500 / 3,000 / 1,605, in file order)
# The machine-readable files come from github.com/ButTaiwan/cjktables, pinned to one commit.
# That repository has no licence file, so the files are downloaded at build time and not
# redistributed here; the lists themselves are published government standards.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p vendor/charlists
rev=92cbab35939a4a751e6bc29e5ffed74a9e3e8f14
base="https://raw.githubusercontent.com/ButTaiwan/cjktables/$rev"
curl -fsSL -o vendor/charlists/edu_standard_1.txt "$base/taiwan/standard/edu_standard_1.txt"
curl -fsSL -o vendor/charlists/edu_standard_2.txt "$base/taiwan/standard/edu_standard_2.txt"
curl -fsSL -o vendor/charlists/tongyong_guifan.txt "$base/china/standard/tongyong_guifan.txt"
cd vendor/charlists
cat > SHA256SUMS <<'SUMS'
2c3668383543aa46ea936f5b71e5c73145ce516e627de396df8aad4658300232  edu_standard_1.txt
1fa22bb3dc6c8b36ec43b959b6fc3cf9313842dac55126ffd04351df040afcbe  edu_standard_2.txt
f4cef819e93067b6e115ebe90a2946e09399f538f77ed55a9d43246170cf5093  tongyong_guifan.txt
SUMS
if command -v shasum >/dev/null; then shasum -a 256 -c SHA256SUMS; else sha256sum -c SHA256SUMS; fi
