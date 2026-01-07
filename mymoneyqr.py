import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, HttpUrl

from auth import get_current_user
from db import get_conn
from settings import BASE_URL, PAYOUT_PER_VALID_SCAN_USD

router = APIRouter(prefix="/qr")

class CreateMoneyQR(BaseModel):
    dest_url: HttpUrl

class UpdateMoneyQR(BaseModel):
    dest_url: HttpUrl

def new_code():
    return secrets.token_urlsafe(6).replace("-", "").replace("_", "")

@router.post("", summary="Create money QR")
def create_money_qr(payload: CreateMoneyQR, user=Depends(get_current_user)):
    code = new_code()
    with get_conn() as con:
        con.execute(
            "INSERT INTO money_qr_links(code, owner_uid, dest_url) VALUES (%s,%s,%s)",
            (code, user["uid"], str(payload.dest_url))
        )
        con.commit()
    return {
        "code": code,
        "dest_url": str(payload.dest_url),
        "qr_url": f"/qr/m/{code}",
        "qr_url_full": f"{BASE_URL}/qr/m/{code}",
    }

@router.patch("/{code}", summary="Update destination (owner only)")
def update_money_qr(code: str, payload: UpdateMoneyQR, user=Depends(get_current_user)):
    with get_conn() as con:
        row = con.execute("SELECT owner_uid FROM money_qr_links WHERE code=%s", (code,)).fetchone()
        if not row:
            raise HTTPException(404, "Money QR not found")
        if row["owner_uid"] != user["uid"]:
            raise HTTPException(403, "Not your Money QR")

        con.execute(
            "UPDATE money_qr_links SET dest_url=%s, updated_at=now() WHERE code=%s",
            (str(payload.dest_url), code)
        )
        con.commit()
    return {"ok": True, "code": code, "dest_url": str(payload.dest_url)}

@router.get("/qr/m/{code}", include_in_schema=False)
def money_entry(code: str, request: Request):
    with get_conn() as con:
        row = con.execute("SELECT active FROM money_qr_links WHERE code=%s", (code,)).fetchone()
        if not row or row["active"] is False:
            raise HTTPException(404, "Money QR not found")

        # Create session, expires in 2 minutes
        expires_at = con.execute("SELECT now() + interval '2 minutes' AS exp").fetchone()["exp"]
        sid = con.execute(
            "INSERT INTO money_sessions(code, expires_at) VALUES (%s,%s) RETURNING sid",
            (code, expires_at)
        ).fetchone()["sid"]
        con.commit()

    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Continue</title>
      <style>
        body {{ font-family: Arial, sans-serif; padding: 18px; }}
        .box {{ max-width: 520px; margin: 0 auto; }}
        .ad {{ border: 1px solid #ddd; padding: 14px; border-radius: 10px; margin: 14px 0; }}
        button {{ padding: 12px 16px; font-size: 16px; width: 100%; }}
      </style>
    </head>
    <body>
      <div class="box">
        <h2>Sponsored</h2>
        <div class="ad">
          <b>Ad placeholder</b><br/>
          (Later: real ad network interstitial goes here.)
        </div>

        <button id="btn" disabled>Continue (3)</button>
        <p style="font-size:12px;color:#666">Session expires in 2 minutes.</p>
      </div>

      <script>
        let t = 3;
        const btn = document.getElementById("btn");
        const tick = () => {{
          if (t <= 0) {{
            btn.disabled = false;
            btn.textContent = "Continue";
            return;
          }}
          btn.textContent = "Continue (" + t + ")";
          t -= 1;
          setTimeout(tick, 1000);
        }};
        tick();
        btn.addEventListener("click", () => {{
          window.location.href = "/m/{code}/go?sid={sid}";
        }});
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@router.get("/m/{code}/go", include_in_schema=False)
def money_go(code: str, sid: str):
    with get_conn() as con:
        # Lock session to prevent double-credit
        sess = con.execute(
            """
            SELECT sid, expires_at, used
            FROM money_sessions
            WHERE sid=%s AND code=%s
            FOR UPDATE
            """,
            (sid, code)
        ).fetchone()
        if not sess:
            raise HTTPException(400, "Invalid session")
        if sess["used"] is True:
            raise HTTPException(400, "Session already used")
        expired = con.execute("SELECT (now() > %s) AS expired", (sess["expires_at"],)).fetchone()["expired"]
        if expired:
            raise HTTPException(400, "Session expired")

        qr = con.execute(
            "SELECT dest_url, owner_uid, active FROM money_qr_links WHERE code=%s",
            (code,)
        ).fetchone()
        if not qr or qr["active"] is False:
            raise HTTPException(404, "Money QR not found")

        # Mark used + credit owner
        con.execute("UPDATE money_sessions SET used=TRUE WHERE sid=%s", (sid,))
        con.execute(
            "INSERT INTO earnings(owner_uid, code, amount_usd) VALUES (%s,%s,%s)",
            (qr["owner_uid"], code, PAYOUT_PER_VALID_SCAN_USD)
        )
        con.commit()

    return RedirectResponse(url=qr["dest_url"], status_code=307)
