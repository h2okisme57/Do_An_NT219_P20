import os
import jwt
import datetime
from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi.middleware.cors import CORSMiddleware
import httpx

ORDER_SERVICE_ADDR = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:5000")

app = FastAPI(title="NT219 Auth & Gateway Service")

app.add_middleware(
    CORSMiddleware,
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
    allowed_origins = allowed_origins_env.split(",") if allowed_origins_env != "*" else ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. TỰ ĐỘNG KHỞI TẠO KHÓA
def init_keys():
    if not os.path.exists("private.pem") or not os.path.exists("public.pem"):
        print("🔑 Không tìm thấy khóa. Đang khởi tạo cặp khóa RSA 2048-bit mới...")
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        
        # Lưu Private Key
        with open("private.pem", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Lưu Public Key
        with open("public.pem", "wb") as f:
            f.write(private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        print("Đã tạo xong private.pem và public.pem!")

init_keys()

# Đọc khóa dưới dạng bytes
with open("private.pem", "rb") as f: PRIVATE_KEY = f.read()
with open("public.pem", "rb") as f: PUBLIC_KEY = f.read()

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(data: LoginRequest):
    print(f"➜ Login Attempt: {data.username}")
    
    if data.username == "admin" and data.password == "123456":
        payload = {
            "user_id": "U123",
            "email": "admin@uit.edu.vn",
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }
        
        try: 
            # Thực hiện ký Token
            token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
            if isinstance(token, bytes):
                token = token.decode("utf-8")
                
            return {"access_token": token, "token_type": "bearer"}
            
        except Exception as e:
            print(f"❌ LỖI KÝ TOKEN TẠI SERVER: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"LỖI KÝ TOKEN: {str(e)}")
        
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



@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(request: Request, path_name: str):
    url = f"{ORDER_SERVICE_ADDR}/{path_name}"
    headers = dict(request.headers)
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method, url=url, headers=headers,
                content=body, params=request.query_params, timeout=20.0
            )
            return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Không thể kết nối tới Order Service: {str(e)}")