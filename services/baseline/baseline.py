from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class BaselineRequest(BaseModel):
    model_id: str
    metric_name: str
    value: float
    timestamp: int
    feature_name: Optional[str] = None  # For domain violations or drift
    baseline_min: Optional[float] = None
    baseline_max: Optional[float] = None

    class Config:
        protected_namespaces = ()

@app.post("/baseline")
async def receive_baseline_metric(request: BaselineRequest):
    print(f"[Baseline] Received {request.metric_name} for model {request.model_id} at {request.timestamp}")
    
    # Optional domain check logic
    if request.feature_name and request.baseline_min is not None and request.baseline_max is not None:
        if request.value < request.baseline_min or request.value > request.baseline_max:
            print(f"[Baseline] Domain violation detected on {request.feature_name}: {request.value}")
            return {"status": "violation", "feature": request.feature_name, "value": request.value}

    return {"status": "ok", "metric": request.metric_name, "value": request.value}
