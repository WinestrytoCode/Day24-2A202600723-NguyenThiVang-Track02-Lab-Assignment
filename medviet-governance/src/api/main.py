# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """Trả về 10 records raw đầu tiên. Chỉ admin được phép."""
    df = pd.read_csv("data/raw/patients_raw.csv").head(10)
    return JSONResponse(content=df.to_dict(orient="records"))

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """Trả về anonymized data. admin và ml_engineer được phép."""
    df = pd.read_csv("data/raw/patients_raw.csv").head(10)
    df_anon = anonymizer.anonymize_dataframe(df)
    return JSONResponse(content=df_anon.to_dict(orient="records"))

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """Trả về số bệnh nhân theo loại bệnh. data_analyst, ml_engineer, admin được phép."""
    df = pd.read_csv("data/raw/patients_raw.csv")
    metrics = df.groupby("benh").size().reset_index(name="so_luong")
    return JSONResponse(content=metrics.to_dict(orient="records"))

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Xóa bệnh nhân theo patient_id. Chỉ admin được phép."""
    return JSONResponse(content={"message": f"Patient {patient_id} deleted", "deleted_by": current_user["username"]})

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
