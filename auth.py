import os
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from settings import AUTH_MODE, FIREBASE_SERVICE_ACCOUNT

bearer_scheme = HTTPBearer(auto_error=False)

# Firebase init is lazy (only used if AUTH_MODE=FIREBASE)
_firebase_initialized = False

def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return
    if not FIREBASE_SERVICE_ACCOUNT or not os.path.exists(FIREBASE_SERVICE_ACCOUNT):
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT missing or file not found.")
    import firebase_admin
    from firebase_admin import credentials
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred)
    _firebase_initialized = True

def _verify_firebase_token(token: str) -> Dict[str, Any]:
    _init_firebase()
    from firebase_admin import auth as fb_auth
    try:
        decoded = fb_auth.verify_id_token(token)
        return decoded
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
        )

def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_debug_uid: Optional[str] = Header(default=None, alias="X-Debug-Uid"),
) -> Dict[str, Any]:
    """
    DEV mode:
      - Send header: X-Debug-Uid: user123
    FIREBASE mode:
      - Send header: Authorization: Bearer <idToken>
    """
    if AUTH_MODE == "DEV":
        if not x_debug_uid:
            raise HTTPException(401, "DEV mode requires X-Debug-Uid header")
        return {"uid": x_debug_uid, "mode": "DEV"}

    if AUTH_MODE == "FIREBASE":
        if creds is None or not creds.credentials:
            raise HTTPException(401, "Missing Authorization Bearer token")
        decoded = _verify_firebase_token(creds.credentials)
        # Normalize
        return {
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
            "name": decoded.get("name"),
            "role": decoded.get("role"),
            "plan": decoded.get("plan"),
            "mode": "FIREBASE",
            "raw": decoded,
        }

    raise HTTPException(500, f"Unknown AUTH_MODE={AUTH_MODE}")
