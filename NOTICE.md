# 第三方資料與字型

## 隨專案附帶的驗證資料

- `vendor/groundtruth/unicode_confusables_v18.txt`：Unicode Technical Standard #39 confusables.txt（版本 18.0.0，2026-08-06），© Unicode, Inc.，依 Unicode License v3 散布。取自 github.com/unicode-org/unicodetools。
- `vendor/groundtruth/pycorrector_same_stroke.txt`：pycorrector 1.1.4 的 `data/same_stroke.txt`，© shibing624，Apache License 2.0。

## 建置時下載的字表（不隨專案附帶）

- 教育部《常用國字標準字體表》（1982，4,808 字）、《次常用國字標準字體表》（1982，6,343 字）、中華人民共和國《通用规范汉字表》（2013，8,105 字）。機器可讀的版本取自 github.com/ButTaiwan/cjktables（固定在 commit 92cbab3），由 `scripts/fetch_charlists.sh` 下載並核對 SHA-256。該 repo 沒有授權檔，所以本專案不重新散布這些檔案；`data/charset.tsv` 只記錄每個字屬於哪些字集。

## 不隨專案附帶的字型

- Noto Sans CJK、Roboto：SIL Open Font License 1.1，由 `scripts/fetch_android_fonts.sh` 從 GitHub 下載。
- jf open 粉圓 2.1（只用於字型敏感度測試）：SIL Open Font License 1.1，github.com/justfont/open-huninn-font。
- SF Pro、蘋方（PingFang）：Apple 專有字型，見下節。

## 為什麼不提供 iOS 表，只提供程式

本專案**不發布**用 iOS 字型（SF Pro、蘋方）算出的表，只提供產生它的程式。需要 iOS 表的人，請在自己的 Mac 上執行 `scripts/run_stack.sh ios_zh_tw` 產生。

原因：

1. **macOS 內建字型的授權限於「在 Apple 軟體上顯示與列印內容」**，並且不得散布字型。本專案的程式只在使用者自己的 Mac 上讀取系統內建的字型檔來渲染，符合這個用途，也不複製字型檔、不上傳到雲端（包括 Colab）。
2. **SF Pro 的獨立下載版授權更窄**，只允許用來製作 Apple 平台 App 的介面模型（mock-up）。
3. iOS 表雖然只含相似度數值，不含字型檔或字形圖片，但它是由 Apple 字型計算出的衍生資料。授權條款沒有明確允許散布這類衍生資料，為避免爭議，本專案選擇不散布，改由使用者在本機產生。

Android 表使用 Noto Sans CJK 與 Roboto（SIL OFL 1.1），授權允許自由使用與散布，所以直接發布。
