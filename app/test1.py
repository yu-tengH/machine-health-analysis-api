# fastapi:做api, query:網址輸入參數進行查詢
# BaseModel:post, pandas:資料處理, HTTPException：資料檔不存在時回傳錯誤
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import pandas as pd
import logging

# logging設定: 記錄程式運行狀態，方便除錯
# logging有幾種等級: DEBUG, INFO, WARNING, ERROR, CRITICAL（嚴重出錯）
# logging.basicConfig(level=logging.INFO)為顯示INFO等級以上的訊息，包含INFO, WARNING, ERROR, CRITICAL
# logging.getLogger(__name__) :__name__是當前模組名稱，這樣可以在多個模組中使用不同的logger
# basicConfig()是設定logging的基本配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fun = FastAPI(
    title="Machine Health Analysis API",
    description="A FastAPI demo for predictive maintenance and machine health analysis using AI4I 2020 dataset.",
    version="1.0.0"
)

DATA_PATH = "data/ai4i2020.csv"


class MachineInput(BaseModel):
    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float


def load_data():
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Data file not found. Please check data/ai4i2020.csv."
        )

    # 把原始欄位名稱改成比較好寫的 snake_case
    df = df.rename(columns={
        "UDI": "udi",
        "UID": "uid",
        "Product ID": "product_id",
        "Type": "type",
        "Air temperature [K]": "air_temperature",
        "Process temperature [K]": "process_temperature",
        "Rotational speed [rpm]": "rotational_speed",
        "Torque [Nm]": "torque",
        "Tool wear [min]": "tool_wear",
        "Machine failure": "machine_failure",
        "TWF": "twf",
        "HDF": "hdf",
        "PWF": "pwf",
        "OSF": "osf",
        "RNF": "rnf"
    })
    
    # 報錯：「資料有讀到，但欄位不符合預期」。
    required_columns = [
        "type",
        "air_temperature",
        "process_temperature",
        "rotational_speed",
        "torque",
        "tool_wear",
        "machine_failure",
        "twf",
        "hdf",
        "pwf",
        "osf",
        "rnf"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Required columns are missing.",
                "missing_columns": missing_columns,
                "available_columns": df.columns.tolist()
            }
    )

    # 衍生欄位：製程溫度與空氣溫度的差距
    df["temperature_gap"] = df["process_temperature"] - df["air_temperature"]

    return df


def calculate_risk_score(row):
    risk_score = 0
    risk_reasons = []

    if row["torque"] > 55:
        risk_score += 30
        risk_reasons.append("High torque")

    if row["tool_wear"] > 180:
        risk_score += 30
        risk_reasons.append("High tool wear")

    if row["temperature_gap"] > 11:
        risk_score += 20
        risk_reasons.append("High temperature gap")

    if row["rotational_speed"] < 1400:
        risk_score += 20
        risk_reasons.append("Low rotational speed")

    return risk_score, risk_reasons


@fun.get("/")
def root():
    return {
        "message": "Machine Health Analysis API is running",
        "dataset": "AI4I 2020 Predictive Maintenance Dataset",
        "docs": "/docs"
    }


@fun.get("/api/machine/summary")
def get_machine_summary():
    df = load_data()

    failure_rate = df["machine_failure"].mean()

    type_distribution = (
        df["type"]
        .value_counts()
        .to_dict()
    )

    return {
        "total_records": int(len(df)),
        "failure_rate": round(float(failure_rate), 4),
        "avg_air_temperature": round(float(df["air_temperature"].mean()), 2),
        "avg_process_temperature": round(float(df["process_temperature"].mean()), 2),
        "avg_temperature_gap": round(float(df["temperature_gap"].mean()), 2),
        "avg_rotational_speed": round(float(df["rotational_speed"].mean()), 2),
        "avg_torque": round(float(df["torque"].mean()), 2),
        "avg_tool_wear": round(float(df["tool_wear"].mean()), 2),
        "type_distribution": type_distribution
    }

# query parameters: min_score, limit
# 使用Query來定義 查詢參數，並提供預設值和描述
# ex: 網址用：/api/machine/anomaly?min_score=90&limit=5，可以透過設定參數輸出特定分數以及限制數量
# 上述是指只回傳 risk_score 大於等於 90 的資料，而且最多回傳 5 筆。
@fun.get("/api/machine/anomaly")
def get_machine_anomaly(
    min_score: int = Query(default=70, description="Minimum risk score for anomaly records"),
    limit: int = Query(default=10, description="Maximum number of anomaly records to return")
):
    df = load_data()

    risk_results = df.apply(calculate_risk_score, axis=1)

    # lambda: 對 risk_results 裡面的每一筆結果，都取出第 0 個值，也就是 risk_score。
    df["risk_score"] = risk_results.apply(lambda x: x[0])
    df["risk_reasons"] = risk_results.apply(lambda x: x[1])

    anomaly_df = df[df["risk_score"] >= min_score].copy()
    anomaly_df = anomaly_df.sort_values("risk_score", ascending=False).head(limit)

    result = anomaly_df[
        [
            "udi",
            "product_id",
            "type",
            "air_temperature",
            "process_temperature",
            "temperature_gap",
            "rotational_speed",
            "torque",
            "tool_wear",
            "machine_failure",
            "risk_score",
            "risk_reasons"
        ]
    ].to_dict(orient="records")

    return {
        "min_score": min_score,
        "limit": limit,
        "anomaly_count": int(len(result)),
        "rules": {
            "high_torque": "torque > 55",
            "high_tool_wear": "tool_wear > 180",
            "high_temperature_gap": "process_temperature - air_temperature > 11",
            "low_rotational_speed": "rotational_speed < 1400"
        },
        "anomalies": result
    }


@fun.get("/api/machine/failure-modes")
def get_failure_modes():
    df = load_data()

    failure_modes = {
        "tool_wear_failure_twf": int(df["twf"].sum()),
        "heat_dissipation_failure_hdf": int(df["hdf"].sum()),
        "power_failure_pwf": int(df["pwf"].sum()),
        "overstrain_failure_osf": int(df["osf"].sum()),
        "random_failure_rnf": int(df["rnf"].sum()),
        "machine_failure_total": int(df["machine_failure"].sum())
    }

    return {
        "failure_modes": failure_modes,
        "note": "These are labels provided by the AI4I 2020 dataset."
    }


@fun.post("/api/machine/predict")
def predict_machine_failure(data: MachineInput):
    temperature_gap = data.process_temperature - data.air_temperature
    logger.info(f"Prediction request received: {data}")
    logger.info(f"Prediction result: risk_score={risk_score}, risk_level={risk_level}")

    row = {
        "air_temperature": data.air_temperature,
        "process_temperature": data.process_temperature,
        "temperature_gap": temperature_gap,
        "rotational_speed": data.rotational_speed,
        "torque": data.torque,
        "tool_wear": data.tool_wear
    }

    risk_score, risk_reasons = calculate_risk_score(row)

    if risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "temperature_gap": round(float(temperature_gap), 2),
        "risk_score": int(risk_score),
        "risk_level": risk_level,
        "risk_reasons": risk_reasons
    }

#
@fun.get("/api/machine/by-type")
def get_machine_summary_by_type():
    df = load_data()

    summary_by_type = (
        # .groupby("type")是用來分類的
        df.groupby("type")
        # .agg(...)是用來計算每個分類的統計數據
        .agg(
            record_count=("type", "count"),
            failure_rate=("machine_failure", "mean"),
            avg_air_temperature=("air_temperature", "mean"),
            avg_process_temperature=("process_temperature", "mean"),
            avg_temperature_gap=("temperature_gap", "mean"),
            avg_rotational_speed=("rotational_speed", "mean"),
            avg_torque=("torque", "mean"),
            avg_tool_wear=("tool_wear", "mean")
        )
        .round(4)
        # groupby 完後，type 會變成 index。
        # 可以把 index 想成表格左邊的分類標籤。
        # 但我們要回傳 JSON，通常希望 type 也是一般欄位
        .reset_index()
        
    )

    return {
        "group_by": "type",
        # summary_by_type 原本是 pandas DataFrame，像表格一樣
        # 但 API 要回傳 JSON，不能直接回傳 DataFrame。
        # to_dict(orient="records") 是把表格轉成 JSON 格式的 list of dicts
        "summary": summary_by_type.to_dict(orient="records")
    }