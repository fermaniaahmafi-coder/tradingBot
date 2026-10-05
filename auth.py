import hmac
import hashlib
import base64
import json
import time
from functools import wraps
from flask import request, redirect, jsonify
from config import Config

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64url_decode(s: str) -> bytes:
    padding = '=' * (4 - (len(s) % 4)) if len(s) % 4 != 0 else ''
    return base64.urlsafe_b64decode(s + padding)

def create_token(username: str) -> str:
    """Generate HS256 JWT token with expiration."""
    exp = int(time.time()) + (Config.JWT_EXPIRY_HOURS * 3600)
    payload = {
        "sub": username,
        "username": username,
        "iat": int(time.time()),
        "exp": exp
    }

    try:
        import jwt
        return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
    except Exception:
        # Pure-Python standard library HS256 fallback (zero-dependency)
        header = {"alg": "HS256", "typ": "JWT"}
        h_str = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
        p_str = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
        signing_input = f"{h_str}.{p_str}".encode('utf-8')
        sig = hmac.new(Config.JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
        sig_str = _b64url_encode(sig)
        return f"{h_str}.{p_str}.{sig_str}"

def verify_token(token: str):
    """Verify HS256 JWT token and return payload if valid, else None."""
    if not token or not isinstance(token, str):
        return None

    # Strip potential Bearer prefix
    if token.startswith("Bearer "):
        token = token[7:].strip()

    try:
        import jwt
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except Exception:
        pass

    # Pure-Python standard library verification fallback
    try:
        parts = token.strip().split('.')
        if len(parts) != 3:
            return None
        h_str, p_str, sig_str = parts
        signing_input = f"{h_str}.{p_str}".encode('utf-8')
        expected_sig = hmac.new(Config.JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_str)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(p_str).decode('utf-8'))
        if payload.get("exp") and time.time() > payload["exp"]:
            return None
        return payload
    except Exception:
        return None

def login_required(f):
    """Decorator to protect web pages and API endpoints with JWT."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Check Cookie first
        token = request.cookies.get("auth_token")

        # 2. Check Authorization Header fallback
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()

        payload = verify_token(token) if token else None

        if not payload:
            # Check if this is an API call or AJAX request
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({
                    "success": False,
                    "error": "Unauthorized: Akses ditolak. Silakan login terlebih dahulu.",
                    "redirect": "/login"
                }), 401
            # If regular browser page request, redirect to login page
            return redirect(f"/login?next={request.path}")

        request.user = payload
        return f(*args, **kwargs)
    return decorated_function
