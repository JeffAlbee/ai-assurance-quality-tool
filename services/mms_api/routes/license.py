from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter()

class LicenseStatus(BaseModel):
    status: str
    txid: str
    checked_at: datetime
    expires_at: datetime
    level: str

@router.get("/status", response_model=LicenseStatus)
def get_license_status():
    return LicenseStatus(
        status="active",
        level="premium",
        txid="demo-txid-001",
        checked_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
