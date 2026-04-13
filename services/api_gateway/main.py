import os
from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta

app = FastAPI()

## Cơ chế tự động sinh khóa RSA nếu chưa có, đảm bảo luôn có sẵn private.pem và public.pem để sử dụng
def init_rsa_keys():
    if not os.path.exists("private.pem") or not os.path.exists("public.pem"):
        print("🔑 Không tìm thấy Khóa. Đang tự động sinh khóa RSA 2048-bit mới...")
        
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        with open("private.pem", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption() # Không cài pass
            ))

        with open("public.pem", "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        print("Đã sinh và lưu xong private.pem và public.pem!")

init_rsa_keys()

with open("private.pem", "rb") as f:
    PRIVATE_KEY = f.read()

with open("public.pem", "rb") as f:
    PUBLIC_KEY = f.read()

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(req: LoginRequest):
    if req.username == "admin" and req.password == "123456":
        payload = {
            "user_id": 1,
            "role": "customer",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        # Ký token
        token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Sai tài khoản")

@app.middleware("http")
async def jwt_verification_middleware(request: Request, call_next):
    if request.url.path in ["/login", "/register", "/docs", "/openapi.json"]:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response(content="Thiếu Token", status_code=401)

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        request.scope['headers'].append((b'x-user-id', str(payload.get('user_id')).encode()))
    except Exception:
        return Response(content="Token không hợp lệ hoặc hết hạn", status_code=401)

    return await call_next(request)