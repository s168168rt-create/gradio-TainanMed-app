# 🏯 台南市開放資料瀏覽器

以 [Gradio](https://www.gradio.app/) 製作的台南市政府開放資料瀏覽器,支援關鍵字搜尋、欄位篩選、統計圖表與 CSV 下載。

## 功能
- 📋 **資料瀏覽**:全欄位關鍵字搜尋、選擇顯示欄位、依欄位值篩選、下載查詢結果
- 📊 **統計圖表**:任選分類欄位繪製前 N 名長條圖,並提供數值欄位摘要
- ⚙️ **資料來源**:可更換 CSV 連結並重新下載

欄位皆自動偵測,更換資料連結即可套用到其他開放資料集。

## 專案結構
```
.
├── app.py            # Gradio 主程式
├── requirements.txt  # 套件需求
├── render.yaml       # Render Blueprint(選用)
├── .python-version   # Python 版本
└── README.md
```

## 本機執行
```bash
pip install -r requirements.txt
python app.py
```
開啟 http://localhost:7860

## 部署到 Render
1. 將專案推上 GitHub。
2. 登入 [Render](https://render.com) → **New +** → **Web Service** → 連結該 GitHub 儲存庫。
3. 設定:
   - **Runtime**:Python 3
   - **Build Command**:`pip install -r requirements.txt`
   - **Start Command**:`python app.py`
   - **Instance Type**:Free
4. 按 **Create Web Service**,完成後取得 `https://xxx.onrender.com` 網址。

或使用 Blueprint:**New +** → **Blueprint**,選擇本儲存庫,Render 會讀取 `render.yaml` 自動建立。

> 程式會讀取 Render 提供的 `PORT` 環境變數並綁定 `0.0.0.0`,不需額外設定。
> 免費方案閒置約 15 分鐘會休眠,首次開啟需等待冷啟動(約 30–60 秒)。

## 更換資料來源
修改 `app.py` 最上方的 `URL`,或直接在網頁「資料來源」分頁貼上新連結。

## 注意
- 下載資料時使用 `verify=False`(政府網站憑證常有問題),僅用於讀取公開資料。
- 資料來源:[台南市政府資料開放平台](https://data.tainan.gov.tw)
