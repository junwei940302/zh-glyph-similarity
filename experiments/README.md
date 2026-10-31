# 實驗紀錄

| 檔案 | 內容 |
|---|---|
| `results/v1_metrics_android.json` | 第一版比較：blurcos（σ=1.5、3）、純 chamfer、兩者平均（Android 基準） |
| `exp_chamfer_st.py`、`results/chamfer_st_grid_android.json` | chamfer_st 參數網格：拉伸代價 lam ∈ {0.5, 1, 2} × 洞數代價 mu ∈ {0, 0.2, 0.4}，含 0、O、l、1、I、5、S 的前 6 名鄰近字 |
| `results/chamfer_st_android.json` | 採用的設定（lam = 0.5、mu = 0）在三組驗證集上的結果 |

重現網格：`python3 experiments/exp_chamfer_st.py data/render_android_aosp_zh_tw.npz out.json`（需約 5 GB 記憶體）。
