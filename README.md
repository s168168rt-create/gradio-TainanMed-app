# 🏯 台南市開放資料瀏覽器(PWA + RWD)

以 Gradio + FastAPI 製作的台南市政府開放資料瀏覽器。可搜尋、篩選、統計、下載 CSV,
並支援 **PWA(可安裝到手機/桌面主畫面)** 與 **RWD(手機、平板、桌機自動適應版面)**。

## 功能
- 📋 **資料瀏覽**:全欄位關鍵字搜尋、選擇顯示欄位、依欄位值篩選、下載查詢結果
- 📊 **統計圖表**:任選分類欄位繪製前 N 名長條圖,並提供數值欄位摘要
- ⚙️ **資料來源**:可更換 CSV 連結並重新下載
- 📱 **PWA**:Web App Manifest、Service Worker、離線提示頁、「安裝 App」按鈕、iOS 主畫面圖示
- 📐 **RWD**:統計卡片 4 → 2 欄、版面直向堆疊、觸控按鈕 ≥ 44px、輸入框 16px(避免 iOS 自動放大)、表格橫向捲動、支援瀏海安全區

欄位皆自動偵測,更換資料連結即可套用到其他開放資料集。

## 專案結構
```
.
├── app.py                    # Gradio 介面 + FastAPI(提供 PWA 檔案)
├── requirements.txt
├── render.yaml               # Render Blueprint(選用)
├── .python-version
├── make_icons.py             # 產生 PWA 圖示的工具(選用,需 pillow)
└── static/
    ├── manifest.webmanifest  # PWA 設定(名稱、圖示、主題色…)
    ├── sw.js                 # Service Worker(由 /sw.js 提供,作用範圍為整站)
    ├── offline.html          # 離線時顯示的頁面
    └── icons/                # 192 / 512 / maskable / apple-touch-icon
```

## 本機執行
```bash
pip install -r requirements.txt
python app.py
```
開啟 http://localhost:7860 (可用環境變數 `PORT` 更改埠號)。
(本機 `localhost` 也可測試 PWA;正式環境需 HTTPS,Render 預設即為 HTTPS。)

## 部署到 Render
1. 將專案推上 GitHub。
2. Render → **New +** → **Web Service** → 選擇該儲存庫。
3. 設定:
   - **Runtime**:Python 3
   - **Build Command**:`pip install -r requirements.txt`
   - **Start Command**:`python app.py`
   - **Health Check Path**:`/healthz`(選用)
   - **Instance Type**:Free
4. 建立後取得 `https://xxx.onrender.com`。

或使用 Blueprint:**New +** → **Blueprint**,選擇本儲存庫,Render 會讀取 `render.yaml`。

> 免費方案閒置約 15 分鐘會休眠,首次開啟需等待冷啟動。
> 若啟動時下載失敗,程式會改用上次存下的 `data01.csv`;從未成功下載過則會啟動失敗,請查看 Render Logs。

## 安裝成 App
- **Android / Chrome / Edge**:開啟網站後點右下角「⬇ 安裝 App」,或瀏覽器選單的「安裝應用程式」。
- **iPhone / iPad(Safari)**:分享 → **加入主畫面**。

## 自訂
- 更換資料來源:改 `app.py` 的 `URL`、設環境變數 `DATA_URL`,或在網頁「資料來源」分頁貼上連結。
- 更新快取版本:修改 `static/sw.js` 的 `VERSION`,舊快取會自動清除。
- 更換圖示:修改並執行 `python make_icons.py`(需 `pip install pillow`),或直接替換 `static/icons/` 內的 PNG。
- 主題色:`static/manifest.webmanifest` 的 `theme_color`、`app.py` `HEAD` 內的 `theme-color`。

## 注意
- 下載資料時使用 `verify=False`(政府網站憑證常有問題),僅用於讀取公開資料。
- Service Worker 只快取靜態資源與離線頁,資料與 Gradio API 一律走網路,因此「離線」時無法瀏覽資料,只會顯示離線提示。
- 資料來源:[台南市政府資料開放平台](https://data.tainan.gov.tw)
