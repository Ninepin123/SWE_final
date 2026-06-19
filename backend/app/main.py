"""FastAPI 進入點（組長維護）。

這個檔案只做三件事：建立 app、掛 CORS、include 各子系統的 router。
各子系統的功能一律寫在 app/modules/<子系統>/ 裡，不要寫在這裡，
避免多人同時修改本檔造成衝突。
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.aas.monitoring import metrics
from app.modules.aas.router import router as aas_router
from app.modules.sms.router import router as sms_router
from app.modules.sas.router import router as sas_router
from app.modules.trs.router import router as trs_router
from app.modules.ras.router import router as ras_router
from app.modules.ncs.router import router as ncs_router

app = FastAPI(
    title="NUKSAMS API",
    description="高雄大學獎(助)學金申請與管理系統 後端 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def collect_metrics(request: Request, call_next):
    """AAS015-016：收集請求量與伺服器錯誤數供維運監控。"""
    try:
        response = await call_next(request)
    except Exception:
        metrics.record_request(500)
        raise
    metrics.record_request(response.status_code)
    return response


app.include_router(aas_router)
app.include_router(sms_router)
app.include_router(sas_router)
app.include_router(trs_router)
app.include_router(ras_router)
app.include_router(ncs_router)


@app.get("/api/health", tags=["system"])
def health_check():
    return {"status": "ok"}
