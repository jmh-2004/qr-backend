import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

from auth import get_current_user
from db import get_conn
from settings import BASE_URL

router = APIRouter()

class CreateQR(BaseModel):
    dest_url: HttpUrl

class UpdateQR(BaseModel):
    dest_url: HttpUrl

def new_code():
    return secrets.token_urlsafe(6).replace("-", "").replace("_", "")

@router.post("", summary="Create normal QR")
def create_qr(payload: CreateQR, user=Depends(get_current_user)):
    code = new_code()
    with get_conn() as con:
        con.execute(
            "INSERT INTO qr_links(code, owner_uid, dest_url) VALUES (%s,%s,%s)",
            (code, user["uid"], str(payload.dest_url))
        )
        con.commit()
    return {
        "code": code,
        "dest_url": str(payload.dest_url),
        "qr_url": f"/r/{code}",
        "qr_url_full": f"{BASE_URL}/r/{code}",
    }

@router.patch("/{code}", summary="Update destination (owner only)")
def update_qr(code: str, payload: UpdateQR, user=Depends(get_current_user)):
    with get_conn() as con:
        row = con.execute("SELECT owner_uid FROM qr_links WHERE code=%s", (code,)).fetchone()
        if not row:
            raise HTTPException(404, "QR not found")
        if row["owner_uid"] != user["uid"]:
            raise HTTPException(403, "Not your QR")

        con.execute(
            "UPDATE qr_links SET dest_url=%s, updated_at=now() WHERE code=%s",
            (str(payload.dest_url), code)
        )
        con.commit()
    return {"ok": True, "code": code, "dest_url": str(payload.dest_url)}

@router.get("/r/{code}", include_in_schema=False)
def redirect_normal(code: str):
    with get_conn() as con:
        row = con.execute("SELECT dest_url, active FROM qr_links WHERE code=%s", (code,)).fetchone()
        if not row or row["active"] is False:
            raise HTTPException(404, "QR not found")
    return RedirectResponse(url=row["dest_url"], status_code=307)
