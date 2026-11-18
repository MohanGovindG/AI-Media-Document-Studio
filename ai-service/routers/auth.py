from fastapi import APIRouter, HTTPException, Header, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List, Tuple
import hashlib
import hmac
import time
import base64
import json
import uuid

router = APIRouter(prefix="/api/auth", tags=["Authentication & User Management"])

# JWT Secret & Configuration
JWT_SECRET = "ai_studio_super_secret_jwt_key_2026_secure_random"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    if not salt:
        salt = uuid.uuid4().hex[:16]
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hashed, salt

def verify_password(password: str, salt: str, hashed_expected: str) -> bool:
    hashed_computed, _ = hash_password(password, salt)
    return hmac.compare_digest(hashed_computed, hashed_expected)

def create_jwt_token(payload: Dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    
    payload_copy = dict(payload)
    payload_copy["exp"] = int(time.time()) + TOKEN_EXPIRY_SECONDS
    payload_copy["iat"] = int(time.time())
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_copy).encode()).decode().rstrip("=")
    
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{signing_input}.{sig_b64}"

def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64 + "=="[:len(sig_b64) % 4])
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        payload_json = base64.urlsafe_b64decode(payload_b64 + "=="[:len(payload_b64) % 4]).decode()
        payload = json.loads(payload_json)
        
        # Expiry check
        if payload.get("exp") and payload["exp"] < time.time():
            return None
            
        return payload
    except Exception:
        return None

# In-memory User Database with pre-seeded demo creators
_USERS_DB = {}

# Seed default admin user
_admin_pw_hash, _admin_salt = hash_password("password123")
_USERS_DB["admin@studio.ai"] = {
    "id": "usr-admin-1",
    "name": "Mohan Creator",
    "email": "admin@studio.ai",
    "passwordHash": _admin_pw_hash,
    "salt": _admin_salt,
    "role": "ADMIN",
    "plan": "Enterprise Unlimited",
    "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80",
    "createdAt": "2026-01-01T00:00:00Z",
    "usage": {
        "generationsUsed": 142,
        "generationsLimit": 9999,
        "conversionsUsed": 589,
        "conversionsLimit": 9999,
        "storageMbUsed": 450,
        "storageMbLimit": 10000
    }
}

# Seed default creator user
_creator_pw_hash, _creator_salt = hash_password("password123")
_USERS_DB["creator@studio.ai"] = {
    "id": "usr-creator-2",
    "name": "Alex Studio",
    "email": "creator@studio.ai",
    "passwordHash": _creator_pw_hash,
    "salt": _creator_salt,
    "role": "CREATOR",
    "plan": "Pro Creator",
    "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80",
    "createdAt": "2026-02-15T00:00:00Z",
    "usage": {
        "generationsUsed": 34,
        "generationsLimit": 500,
        "conversionsUsed": 86,
        "conversionsLimit": 1000,
        "storageMbUsed": 120,
        "storageMbLimit": 5000
    }
}

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    confirmPassword: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    currentPassword: Optional[str] = None
    newPassword: Optional[str] = None

def get_current_user_from_header(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Bearer token required."
        )
    token = authorization.split(" ")[1]
    payload = decode_jwt_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token. Please log in again."
        )
    email = payload["sub"]
    user = _USERS_DB.get(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account no longer exists."
        )
    return user

@router.post("/register")
async def register_user(req: RegisterRequest):
    # Validation
    name = req.name.strip()
    email = req.email.strip().lower()
    password = req.password

    if not name or len(name) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
    if not email or "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Invalid email address format")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    if req.confirmPassword and req.confirmPassword != password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Duplicate check
    if email in _USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{email}' already exists. Please login instead."
        )

    pw_hash, salt = hash_password(password)
    user_id = f"usr-{uuid.uuid4().hex[:8]}"

    new_user = {
        "id": user_id,
        "name": name,
        "email": email,
        "passwordHash": pw_hash,
        "salt": salt,
        "role": "USER",
        "plan": "Pro Creator Trial",
        "avatar": None,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "usage": {
            "generationsUsed": 0,
            "generationsLimit": 200,
            "conversionsUsed": 0,
            "conversionsLimit": 500,
            "storageMbUsed": 0,
            "storageMbLimit": 2000
        }
    }
    _USERS_DB[email] = new_user

    # Generate JWT
    token = create_jwt_token({
        "sub": email,
        "id": user_id,
        "name": name,
        "role": "USER"
    })

    user_public = {
        "id": user_id,
        "name": name,
        "email": email,
        "role": "USER",
        "plan": "Pro Creator Trial",
        "avatar": None,
        "createdAt": new_user["createdAt"],
        "usage": new_user["usage"]
    }

    return {
        "success": True,
        "message": "User registered successfully",
        "token": token,
        "user": user_public
    }

@router.post("/login")
async def login_user(req: LoginRequest):
    email = req.email.strip().lower()
    password = req.password

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user = _USERS_DB.get(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(password, user["salt"], user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_jwt_token({
        "sub": email,
        "id": user["id"],
        "name": user["name"],
        "role": user["role"]
    })

    user_public = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "plan": user["plan"],
        "avatar": user.get("avatar"),
        "createdAt": user.get("createdAt"),
        "usage": user.get("usage", {})
    }

    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": user_public
    }

@router.get("/me")
async def get_current_user(user: Dict[str, Any] = Depends(get_current_user_from_header)):
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "plan": user["plan"],
            "avatar": user.get("avatar"),
            "createdAt": user.get("createdAt"),
            "usage": user.get("usage", {})
        }
    }

@router.put("/profile")
async def update_profile(req: UpdateProfileRequest, user: Dict[str, Any] = Depends(get_current_user_from_header)):
    email = user["email"]
    user_record = _USERS_DB[email]

    if req.name and len(req.name.strip()) >= 2:
        user_record["name"] = req.name.strip()
    if req.avatar is not None:
        user_record["avatar"] = req.avatar

    if req.newPassword:
        if not req.currentPassword:
            raise HTTPException(status_code=400, detail="Current password is required to change password")
        if not verify_password(req.currentPassword, user_record["salt"], user_record["passwordHash"]):
            raise HTTPException(status_code=400, detail="Incorrect current password")
        if len(req.newPassword) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        pw_hash, salt = hash_password(req.newPassword)
        user_record["passwordHash"] = pw_hash
        user_record["salt"] = salt

    return {
        "success": True,
        "message": "Profile updated successfully",
        "user": {
            "id": user_record["id"],
            "name": user_record["name"],
            "email": user_record["email"],
            "role": user_record["role"],
            "plan": user_record["plan"],
            "avatar": user_record.get("avatar"),
            "createdAt": user_record.get("createdAt"),
            "usage": user_record.get("usage", {})
        }
    }

@router.post("/logout")
async def logout_user():
    return {"success": True, "message": "Successfully logged out"}
