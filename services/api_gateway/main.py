import os
import jwt
import datetime
from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NT219 Auth & Gateway Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_keys():
    if not os.path.exists("private.pem"):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with open("private.pem", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open("public.pem", "wb") as f:
            f.write(private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

init_keys()
with open("private.pem", "r") as f: PRIVATE_KEY = f.read()
with open("public.pem", "r") as f: PUBLIC_KEY = f.read()

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(data: LoginRequest):
    print(f"Login Attempt: {data.username}")
    if data.username == "admin" and data.password == "123456":
        payload = {
            "user_id": "U123",
            "email": "admin@uit.edu.vn",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }
        token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Tài khoản hoặc mật khẩu không chính xác")

@app.middleware("http")
async def verify_jwt(request: Request, call_next):
    if request.url.path in ["/api/login", "/docs", "/openapi.json"] or request.method == "OPTIONS":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response(content='{"detail": "Chưa đăng nhập"}', status_code=401, media_type="application/json")

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        request.scope['headers'].append((b'x-user-id', decoded['user_id'].encode()))
        request.scope['headers'].append((b'x-user-email', decoded['email'].encode()))
    except:
        return Response(content='{"detail": "Token không hợp lệ"}', status_code=401, media_type="application/json")

    return await call_next(request)