from fastapi import FastAPI
import pandas as pd

from pydantic import BaseModel # Post要用的，定義前端送來的資料

# 建立 FastAPI 物件，可以用「docs」打開: uvicorn app.main:func --reload
# http://127.0.0.1:8000/docs
func = FastAPI(
    title="My FastAPI test",
    description="This is a test FastAPI application.",
    version="0.1.0"
)

data_path = "data/machine_data.csv"

# (Post)如果有人要呼叫 /api/machine/predict，他必須送這五個欄位進來。
class MachineInput(BaseModel):
    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float
    
    
def load():
    df = pd.read_csv(data_path)
    return df

@func.get("/")
def root():
    return{
        "message": "Hello, API is running!"
    }
    
@func.get("/api/machine/summary")
def get_machine_summary():
    df = load()
    total_records = len(df)
    machine_count = df["machine_id"].nunique()
    avg_air_temperature = df["air_temperature"].mean()
    avg_process_temperature = df["process_temperature"].mean()
    avg_torque = df["torque"].mean()
    avg_tool_wear = df["tool_wear"].mean()
    failure_rate = df["machine_failure"].mean()
    return{
        "total_records": total_records,
        "machine_count": machine_count,
        "failure_rate": avg_air_temperature,
        "avg_temperature": avg_process_temperature,
        "avg_torque": avg_torque,
        "avg_tool_wear": avg_tool_wear,
        "failure_rate": failure_rate
    }
    
@func.get("/api/machine/anomaly")
def get_machine_anomaly():
    df = load()
    # 新增一個欄位：製程溫度與空氣溫度的差距
    df["temperature_gap"] = df["process_temperature"] - df["air_temperature"]
    # 定義異常規則
    high_torque = df["torque"] > 55
    high_tool_wear = df["tool_wear"] > 150
    high_temperature_gap = df["temperature_gap"] > 11
    low_rotational_speed = df["rotational_speed"] < 1400
    # 只要符合其中一個條件，就視為異常資料
    # 這裡的 | 是「或」。
    anomaly_df = df[high_torque | high_tool_wear | high_temperature_gap |low_rotational_speed
    ].copy()
    def get_anomaly_reason(row):
        reasons = []
        if row["torque"] > 55:
            reasons.append("High torque")
        if row["tool_wear"] > 150:
            reasons.append("High tool wear")
        if row["temperature_gap"] > 11:
            reasons.append("High temperature gap")
        if row["rotational_speed"] < 1400:
            reasons.append("Low rotational speed")
        return ", ".join(reasons)
    # anomaly_df["anomaly_reasons"]: 把每一列算出來的異常原因，存成一個新的欄位，欄位名稱叫 anomaly_reasons
    # axis=1 的意思是：一次處理一列 row（一橫排）
    anomaly_df["anomaly_reasons"] = anomaly_df.apply(get_anomaly_reason, axis=1)
    # 計算簡單 risk score
    # high_torque → +30
    # high_tool_wear → +30
    # high_temperature_gap → +20
    # low_rotational_speed → +20
    def calculate_risk_score(row):
        score = 0

        if row["torque"] > 55:
            score += 30

        if row["tool_wear"] > 150:
            score += 30

        if row["temperature_gap"] > 11:
            score += 20

        if row["rotational_speed"] < 1400:
            score += 20

        return score

    anomaly_df["risk_score"] = anomaly_df.apply(calculate_risk_score, axis=1)
    # 計算簡單 risk score
    def calculate_risk_score(row):
        score = 0

        if row["torque"] > 55:
            score += 30

        if row["tool_wear"] > 150:
            score += 30

        if row["temperature_gap"] > 11:
            score += 20

        if row["rotational_speed"] < 1400:
            score += 20

        return score

    anomaly_df["risk_score"] = anomaly_df.apply(calculate_risk_score, axis=1)
    # 依照風險分數由高到低排序
    anomaly_df = anomaly_df.sort_values("risk_score", ascending=False)

    result = anomaly_df[
        [
            "machine_id",
            "air_temperature",
            "process_temperature",
            "temperature_gap",
            "rotational_speed",
            "torque",
            "tool_wear",
            "machine_failure",
            "risk_score",
            "anomaly_reasons"
        ]
    ].to_dict(orient="records")

    return {
        "anomaly_count": len(result),
        "rules": {
            "high_torque": "torque > 55",
            "high_tool_wear": "tool_wear > 150",
            "high_temperature_gap": "process_temperature - air_temperature > 11",
            "low_rotational_speed": "rotational_speed < 1400"
            },
        "anomalies": result
    }

#(Post)如果有人要呼叫 /api/machine/predict，他必須送這五個欄位進來。
#(Post)測試方式不能跟get一樣，因為get是直接在網址列輸入參數，post是要用body傳送資料。 (或是用postman)
# 使用uvicorn app.main:func --reload
# 並且網址輸入 /docs，找到：POST /api/machine/predict
# 之後點擊「try it out」，進行修改，然後在「Request body」裡面輸入以下的JSON資料：
#{  
#    "air_temperature": 25.0,
#    "process_temperature": 40.0,
#    "rotational_speed": 1500.0,
#    "torque": 60.0,
#    "tool_wear": 160.0
#}     
# 網址要用docs(可以想成fastapi的資料頁)http://127.0.0.1:8000/docs





@func.post("/api/machine/predict")
def predict_machine_failure(data: MachineInput):
    temperature_gap = data.process_temperature - data.air_temperature

    risk_score = 0
    risk_reasons = []

    if data.torque > 55:
        risk_score += 30
        risk_reasons.append("High torque")

    if data.tool_wear > 150:
        risk_score += 30
        risk_reasons.append("High tool wear")

    if temperature_gap > 11:
        risk_score += 20
        risk_reasons.append("High temperature gap")

    if data.rotational_speed < 1400:
        risk_score += 20
        risk_reasons.append("Low rotational speed")

    if risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "temperature_gap": round(temperature_gap, 2),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons
    }