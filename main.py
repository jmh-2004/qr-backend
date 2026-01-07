from fastapi import FastAPI
from login import router as login_router
from dashboard import router as dashboard_router
from myqr import router as myqr_router
from mymoneyqr import router as moneyqr_router
from db import init_db

app = FastAPI(title="QR Monetization Backend (v1)")
init_db()

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(login_router, prefix="/auth", tags=["auth"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(myqr_router, prefix="/qr", tags=["qr"])
app.include_router(moneyqr_router, prefix="/moneyqr", tags=["moneyqr"])

