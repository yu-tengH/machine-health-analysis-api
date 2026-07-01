# Machine Health Analysis API  
## 設備健康數據分析後端服務

本專案是一個使用 FastAPI 製作的後端數據分析 API 範例，使用 AI4I 2020 Predictive Maintenance Dataset 模擬設備感測資料，展示如何將資料分析邏輯包裝成可被前端、Dashboard 或內部系統呼叫的 REST API。

---

## 專案目的

在製造或設備監控場域中，設備會持續產生溫度、轉速、扭矩、工具磨耗與故障紀錄等資料。若這些資料只停留在 CSV、Excel 或 Notebook 中，較難被前端系統或內部平台即時使用。

本專案的目標是練習：

- 將設備資料整理成可分析的 KPI
- 使用規則式方法找出高風險設備紀錄
- 將資料分析結果透過 FastAPI API 化
- 讓分析結果以 JSON 格式提供給其他系統使用

---

## 呼叫方法
uvicorn app.test1:fun --reload

---

## 使用技術

- Python
- FastAPI
- pandas
- Pydantic
- Uvicorn
- REST API
- JSON Response
- AI4I 2020 Predictive Maintenance Dataset

---

## 資料集說明

本專案使用 AI4I 2020 Predictive Maintenance Dataset，資料包含 10,000 筆模擬工業設備資料。

主要欄位包含：

- Air temperature：空氣溫度
- Process temperature：製程溫度
- Rotational speed：轉速
- Torque：扭矩
- Tool wear：工具磨耗
- Machine failure：是否發生設備故障
- TWF / HDF / PWF / OSF / RNF：不同故障模式標籤

---

## API 功能

### GET `/`

機械健康檢查 API，確認服務是否正常運作。

---

### GET `/api/machine/summary`

回傳整體設備資料摘要，例如：

- 總資料筆數
- 故障率
- 平均空氣溫度
- 平均製程溫度
- 平均溫差
- 平均轉速
- 平均扭矩
- 平均工具磨耗
- 產品類型分布

---

### GET `/api/machine/anomaly`

根據規則式風險分數找出高風險設備紀錄。

支援 query parameters：

- `min_score`：最低風險分數，預設為 70
- `limit`：最多回傳筆數，預設為 10

目前使用的風險規則包含：

- High torque：`torque > 55`
- High tool wear：`tool_wear > 180`
- High temperature gap：`process_temperature - air_temperature > 11`
- Low rotational speed：`rotational_speed < 1400`

---

### GET `/api/machine/failure-modes`

統計不同故障模式的發生次數：

- TWF：Tool Wear Failure
- HDF：Heat Dissipation Failure
- PWF：Power Failure
- OSF：Overstrain Failure
- RNF：Random Failure

---

### GET `/api/machine/by-type`

依產品類型進行分群分析，回傳不同 type 的：

- 資料筆數
- 故障率
- 平均空氣溫度
- 平均製程溫度
- 平均溫差
- 平均轉速
- 平均扭矩
- 平均工具磨耗

---

### POST `/api/machine/predict`

接收一筆新的設備資料，回傳：

- temperature gap
- risk score
- risk level
- risk reasons

範例 request：

```json
{
  "air_temperature": 301.2,
  "process_temperature": 312.9,
  "rotational_speed": 1250,
  "torque": 65.4,
  "tool_wear": 210
}


### 專案流程

AI4I 2020 Dataset
        ↓
pandas Data Processing
        ↓
KPI / Failure Mode / Risk Scoring
        ↓
FastAPI Endpoints
        ↓
JSON Response
        ↓
Dashboard / Internal System