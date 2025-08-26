import os
import hmac
import base64
from functools import wraps
from flask import Blueprint, request, jsonify, session, current_app

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def _constant_time_eq(a: str, b: str) -> bool:
    a = a or ""
    b = b or ""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))

def _header_password() -> str | None:
    # Optional: header-based auth so power users can script with a header
    # e.g. X-Admin-Password: <password>
    hdr = request.headers.get("X-Admin-Password")
    if hdr:
        return hdr

    # Optional: HTTP Basic "Authorization: Basic base64(admin:PASSWORD)"
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Basic "):
        try:
            userpass = base64.b64decode(auth[len("Basic "):]).decode("utf-8", "ignore")
            # Accept any username, only password matters
            if ":" in userpass:
                return userpass.split(":", 1)[1]
        except Exception:
            pass
    return None

def is_admin_request() -> bool:
    # Session cookie (set by /api/auth/login) or header password
    if session.get("is_admin") is True:
        return True
    pwd_env = os.getenv("ADMIN_PASSWORD") or ""
    hdr_pwd = _header_password()
    if hdr_pwd and _constant_time_eq(hdr_pwd, pwd_env):
        return True
    return False

def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_admin_request():
            # Do NOT touch the DB before returning 401/403
            return jsonify({"status": "error", "message": "Unauthorized (edit mode locked)"}), 401
        return fn(*args, **kwargs)
    return wrapper

@auth_bp.route("/status", methods=["GET"])
def status():
    return jsonify({"is_admin": bool(session.get("is_admin"))})

@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    provided = body.get("password") or _header_password()

    admin_pw = os.getenv("ADMIN_PASSWORD")
    if not admin_pw:
        return jsonify({"status": "error", "message": "Server misconfigured: ADMIN_PASSWORD not set"}), 500

    if provided and _constant_time_eq(provided, admin_pw):
        session["is_admin"] = True
        return jsonify({"status": "success", "message": "Unlocked. Edit mode enabled."})
    return jsonify({"status": "error", "message": "Invalid password"}), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Locked. Edit mode disabled."})
