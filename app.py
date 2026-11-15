# 台南市開放資料瀏覽器 — Gradio + FastAPI,具備 PWA 與 RWD,部署於 Render
import io
import os
import time
from pathlib import Path
import urllib3
import pandas as pd
import requests
import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------- 設定 ----------
URL = os.environ.get("DATA_URL", "https://data.tainan.gov.tw/File/ResourceCsvDownload/6c16b2c8-92b6-49d9-98b5-02966462172c")  # 換連結(或設定環境變數 DATA_URL)
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
CSV_PATH = str(BASE_DIR / "data01.csv")
MAX_ROWS_SHOWN = 1000  # 表格最多顯示列數,避免瀏覽器過重


# ---------- 資料處理 ----------
def _read_csv(raw: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(raw), encoding="big5", encoding_errors="replace")
    return df.dropna().reset_index(drop=True)


def download_data(url: str = URL) -> pd.DataFrame:
    """下載 CSV 並存檔;若下載失敗且本機有上次的快取檔,就改用快取。"""
    last_err = None
    for _ in range(3):  # 簡單重試,避免冷啟動時偶發失敗
        try:
            response = requests.get(url, verify=False, timeout=60)
            response.raise_for_status()
            with open(CSV_PATH, "wb") as f:
                f.write(response.content)
            return _read_csv(response.content)
        except requests.RequestException as e:
            last_err = e
            time.sleep(2)
    if os.path.exists(CSV_PATH):
        print(f"[warn] 下載失敗,改用本機快取:{last_err}")
        with open(CSV_PATH, "rb") as f:
            return _read_csv(f.read())
    raise RuntimeError(f"無法下載資料:{last_err}")


DF = download_data()


def column_info(df: pd.DataFrame):
    cols = list(df.columns)
    num_cols = list(df.select_dtypes("number").columns)
    cat_cols = [c for c in cols if c not in num_cols]
    return cols, num_cols, cat_cols


def stat_cards(df: pd.DataFrame, total: int) -> str:
    _, num_cols, cat_cols = column_info(df)
    items = [
        ("符合筆數", f"{len(df):,}"),
        ("總筆數", f"{total:,}"),
        ("欄位數", f"{df.shape[1]}"),
        ("數值 / 文字欄位", f"{len(num_cols)} / {len(cat_cols)}"),
    ]
    cards = "".join(
        f"<div class='card'><div class='v'>{v}</div><div class='k'>{k}</div></div>"
        for k, v in items
    )
    return f"<div class='cards'>{cards}</div>"


# ---------- 互動函式 ----------
def query(keyword, show_cols, filter_col, filter_vals):
    df = DF
    if keyword and keyword.strip():
        kw = keyword.strip()
        mask = df.astype(str).apply(lambda s: s.str.contains(kw, case=False, regex=False)).any(axis=1)
        df = df[mask]
    if filter_col and filter_vals:
        df = df[df[filter_col].astype(str).isin(filter_vals)]
    if show_cols:
        df = df[[c for c in show_cols if c in df.columns]]
    shown = df.head(MAX_ROWS_SHOWN)
    out_path = "filtered_result.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    return shown, stat_cards(df, len(DF)), out_path


def update_filter_values(col):
    if not col:
        return gr.update(choices=[], value=[])
    vals = DF[col].astype(str).value_counts().head(200).index.tolist()
    return gr.update(choices=vals, value=[])


def make_chart(col, top_n):
    if not col:
        return pd.DataFrame({"類別": [], "數量": []})
    vc = DF[col].astype(str).value_counts().head(int(top_n)).reset_index()
    vc.columns = ["類別", "數量"]
    return vc


def describe_numeric():
    _, num_cols, _ = column_info(DF)
    if not num_cols:
        return pd.DataFrame({"訊息": ["此資料集沒有數值欄位"]})
    return DF[num_cols].describe().T.round(2).reset_index().rename(columns={"index": "欄位"})


def refresh(url):
    global DF
    try:
        DF = download_data(url.strip() or URL)
    except Exception as e:  # noqa: BLE001
        raise gr.Error(f"下載失敗:{e}")
    cols, _, cat_cols = column_info(DF)
    gr.Info(f"已更新資料,共 {len(DF):,} 筆")
    return (
        gr.update(choices=cols, value=cols),
        gr.update(choices=cat_cols or cols, value=None),
        gr.update(choices=cat_cols or cols, value=(cat_cols or cols)[0]),
    )


# ---------- 介面 ----------
CSS = """
:root { --brand:#2563eb; }
.gradio-container {max-width: 1200px !important; margin: auto; padding-left: max(12px, env(safe-area-inset-left)) !important;
                   padding-right: max(12px, env(safe-area-inset-right)) !important;}
#title {text-align:center; padding: 22px 0 6px;}
#title h1 {font-size: clamp(1.4rem, 5vw, 2.1rem); margin: 0; background: linear-gradient(90deg,#2563eb,#06b6d4);
           -webkit-background-clip:text; -webkit-text-fill-color:transparent;}
#title p {color:#64748b; margin:6px 0 0; font-size: clamp(.85rem, 3vw, 1rem);}
.cards {display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:8px 0 14px;}
.card {border-radius:14px; padding:16px 10px; text-align:center; color:#fff;
       background: linear-gradient(135deg,#3b82f6,#06b6d4); box-shadow:0 4px 12px rgba(37,99,235,.25);}
.card:nth-child(2) {background: linear-gradient(135deg,#8b5cf6,#6366f1);}
.card:nth-child(3) {background: linear-gradient(135deg,#10b981,#14b8a6);}
.card:nth-child(4) {background: linear-gradient(135deg,#f59e0b,#f97316);}
.card .v {font-size: clamp(1.2rem, 4.5vw, 1.8rem); font-weight:700;}
.card .k {font-size:.85rem; opacity:.9; margin-top:2px;}

.gradio-container, .gradio-container * {box-sizing: border-box;}
.gradio-container {width: 100% !important; overflow-x: hidden;}
.cards .card, .cards .card .v, .cards .card .k {color:#fff !important;}

/* 表格可橫向捲動,避免撐破版面 */
.table-wrap, .table-wrap > div {overflow-x:auto;}

/* 平板 */
@media (max-width: 900px) {
  .cards {grid-template-columns:repeat(2,1fr); gap:10px;}
  #main-row {flex-direction: column !important;}
  #main-row > div {min-width: 100% !important; width: 100% !important;}
}
/* 手機 */
@media (max-width: 560px) {
  .gradio-container main.fillable, main.fillable {padding: 6px 4px !important;}
  .gradio-container {padding-top: 4px !important;}
  #title {padding: 14px 0 2px;}
  .card {padding: 12px 6px; border-radius: 12px;}
  .card .k {font-size:.75rem;}
  button, .gr-button {min-height: 44px;}          /* 觸控友善 */
  input, textarea, select {font-size: 16px !important;}  /* 避免 iOS 聚焦時自動放大 */
  .tab-wrapper, .tab-container {overflow-x:auto;}
}
/* 安裝 App 浮動按鈕 */
#pwa-install {position:fixed; right:16px; bottom:max(16px, env(safe-area-inset-bottom)); z-index:9999; display:none;
  background:#2563eb; color:#fff; border:0; border-radius:999px; padding:12px 18px; font-size:15px;
  box-shadow:0 6px 18px rgba(37,99,235,.4); cursor:pointer;}
"""

HEAD = """
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#2563eb">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="台南資料">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="/static/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/static/icons/icon-192.png">
<script>
  // 註冊 Service Worker
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(console.warn);
    });
  }
  // 「安裝 App」按鈕(Chrome / Edge / Android)
  let deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    let btn = document.getElementById("pwa-install");
    if (!btn) {
      btn = document.createElement("button");
      btn.id = "pwa-install";
      btn.textContent = "⬇ 安裝 App";
      document.body.appendChild(btn);
    }
    btn.style.display = "block";
    btn.onclick = async () => {
      btn.style.display = "none";
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
    };
  });
  window.addEventListener("appinstalled", () => {
    const btn = document.getElementById("pwa-install");
    if (btn) btn.remove();
  });
</script>
"""

ALL_COLS, NUM_COLS, CAT_COLS = column_info(DF)
theme = gr.themes.Soft(primary_hue="blue", secondary_hue="cyan", font=["Noto Sans TC", "sans-serif"])

with gr.Blocks(theme=theme, css=CSS, head=HEAD, title="台南市開放資料瀏覽器") as demo:
    gr.HTML("<div id='title'><h1>🏯 台南市開放資料瀏覽器</h1>"
            "<p>搜尋 · 篩選 · 統計 · 下載</p></div>")
    cards = gr.HTML(stat_cards(DF, len(DF)))

    with gr.Tabs():
        # ---- 分頁 1:資料瀏覽 ----
        with gr.Tab("📋 資料瀏覽"):
            with gr.Row(elem_id="main-row"):
                with gr.Column(scale=1, min_width=280):
                    keyword = gr.Textbox(label="🔎 關鍵字搜尋(全欄位)", placeholder="輸入文字,例如:東區")
                    show_cols = gr.Dropdown(ALL_COLS, value=ALL_COLS, multiselect=True, label="顯示欄位")
                    filter_col = gr.Dropdown(CAT_COLS or ALL_COLS, value=None, label="篩選欄位")
                    filter_vals = gr.Dropdown([], multiselect=True, label="篩選值")
                    with gr.Row():
                        btn = gr.Button("查詢", variant="primary")
                        reset = gr.Button("重設")
                    download = gr.File(label="⬇️ 下載查詢結果 (CSV)")
                with gr.Column(scale=3):
                    table = gr.Dataframe(value=DF.head(MAX_ROWS_SHOWN), interactive=False, elem_classes="table-wrap",
                                         wrap=True, max_height=520, label=f"資料表(最多顯示 {MAX_ROWS_SHOWN} 筆)")

        # ---- 分頁 2:統計圖表 ----
        with gr.Tab("📊 統計圖表"):
            with gr.Row(equal_height=False):
                chart_col = gr.Dropdown(CAT_COLS or ALL_COLS, value=(CAT_COLS or ALL_COLS)[0], label="分類欄位")
                top_n = gr.Slider(3, 30, value=10, step=1, label="顯示前 N 名")
            plot = gr.BarPlot(make_chart((CAT_COLS or ALL_COLS)[0], 10), x="類別", y="數量",
                              title="各類別數量", height=380, x_label_angle=-30)
            gr.Markdown("#### 數值欄位摘要")
            num_table = gr.Dataframe(describe_numeric(), interactive=False, elem_classes="table-wrap")

        # ---- 分頁 3:資料來源 ----
        with gr.Tab("⚙️ 資料來源"):
            url_box = gr.Textbox(value=URL, label="CSV 連結(可更換)")
            refresh_btn = gr.Button("🔄 重新下載資料", variant="primary")
            gr.Markdown("資料來源:[台南市政府資料開放平台](https://data.tainan.gov.tw)")

    # ---- 事件 ----
    outputs = [table, cards, download]
    inputs = [keyword, show_cols, filter_col, filter_vals]
    btn.click(query, inputs, outputs)
    keyword.submit(query, inputs, outputs)
    filter_col.change(update_filter_values, filter_col, filter_vals)
    reset.click(lambda: ("", ALL_COLS, None, [], DF.head(MAX_ROWS_SHOWN), stat_cards(DF, len(DF)), None),
                None, [keyword, show_cols, filter_col, filter_vals, table, cards, download])
    chart_col.change(make_chart, [chart_col, top_n], plot)
    top_n.change(make_chart, [chart_col, top_n], plot)
    refresh_btn.click(refresh, url_box, [show_cols, filter_col, chart_col]).then(
        query, inputs, outputs).then(describe_numeric, None, num_table)

# ---------- FastAPI:提供 PWA 所需檔案,並把 Gradio 掛在根路徑 ----------
app = FastAPI(title="台南市開放資料瀏覽器")


# Gradio 的 HTML 範本固定會連到 /manifest.json,因此兩個路徑都提供同一份 manifest
@app.get("/manifest.json", include_in_schema=False)
@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    # 放在根路徑,Service Worker 的作用範圍才能涵蓋整個網站
    return FileResponse(
        STATIC_DIR / "sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
    )


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok", "rows": len(DF)}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app = gr.mount_gradio_app(app, demo.queue(), path="/")  # 必須最後掛載

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))  # Render 會提供 PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
