from fastapi import APIRouter, Depends
from auth import get_current_user
from db import get_conn

router = APIRouter()

@router.get("/balance")
def balance(user=Depends(get_current_user)):
    with get_conn() as con:
        row = con.execute(
            "SELECT COALESCE(SUM(amount_usd), 0) AS balance FROM earnings WHERE owner_uid=%s",
            (user["uid"],)
        ).fetchone()
    return {"uid": user["uid"], "balance_usd": float(row["balance"])}

@router.get("/recent")
def recent(user=Depends(get_current_user), limit: int = 20):
    limit = max(1, min(limit, 100))
    with get_conn() as con:
        rows = con.execute(
            """
            SELECT id, code, amount_usd, created_at
            FROM earnings
            WHERE owner_uid=%s
            ORDER BY id DESC
            LIMIT %s
            """,
            (user["uid"], limit)
        ).fetchall()
    return {"uid": user["uid"], "items": rows}

@router.get("/summary")
def summary(user=Depends(get_current_user)):
    with get_conn() as con:
        total = con.execute(
            "SELECT COALESCE(SUM(amount_usd),0) AS total FROM earnings WHERE owner_uid=%s",
            (user["uid"],)
        ).fetchone()["total"]
        count = con.execute(
            "SELECT COUNT(*) AS c FROM earnings WHERE owner_uid=%s",
            (user["uid"],)
        ).fetchone()["c"]
    return {"uid": user["uid"], "total_usd": float(total), "credited_scans": int(count)}
