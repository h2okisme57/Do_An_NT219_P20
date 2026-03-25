from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pkcs11
import base64

app = FastAPI()
# Chỉ đường dẫn vào thư viện lõi của SoftHSM
lib = pkcs11.lib('/usr/lib/softhsm/libsofthsm2.so')

class SignRequest(BaseModel):
    payload: str # Chuỗi biên lai mày gửi sang từ Laravel

@app.post("/api/sign")
def sign_data(req: SignRequest):
    try:
        # Mở két sắt bằng mã PIN
        token = lib.get_token(token_label='NT219_Token')
        with token.open(user_pin='1234') as session:
            # Lấy chìa khóa RSA đã tạo
            priv_key = session.get_key(object_class=pkcs11.ObjectClass.PRIVATE_KEY, label='my_sign_key')
            
            # Ký số payload
            data_bytes = req.payload.encode('utf-8')
            signature = priv_key.sign(data_bytes, mechanism=pkcs11.Mechanism.RSA_PKCS)
            
            # Trả về chữ ký dạng Base64 cho Laravel
            return {"signature": base64.b64encode(signature).decode('utf-8')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))