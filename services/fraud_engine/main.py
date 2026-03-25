from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

app = FastAPI()

print("Training AI chống gian lận...")
# Dữ liệu mẫu
data = {
    'amount': [50000, 2000000, 15000000, 50000, 8000000, 20000000],
    'failed_attempts': [0, 1, 3, 0, 2, 4],
    'is_fraud': [0, 0, 1, 0, 1, 1]
}
df = pd.DataFrame(data)
model = RandomForestClassifier(random_state=42)
# Training AI học từ data
model.fit(df[['amount', 'failed_attempts']], df['is_fraud'])
print("AI ready")

# Tạo API để Laravel gọi
class Transaction(BaseModel):
    amount: float
    failed_attempts: int

@app.post("/api/fraud/score")
def score_fraud(tx: Transaction):
    # TẦNG 1: RULE-BASED ENGINE
    # Ví dụ: Giao dịch > 100 triệu là drop
    if tx.amount > 100000000:
        return {"action": "block", "score": 99, "reason": "Rule: Số tiền vượt ngưỡng an toàn"}

    # TẦNG 2: ML ENGINE
    # Tính xác suất lừa đảo (từ 0.0 -> 1.0)
    prob = model.predict_proba([[tx.amount, tx.failed_attempts]])[0][1]
    score = int(prob * 100)

    # MA TRẬN QUYẾT ĐỊNH
    if score >= 70:
        action = "block"        # Nguy hiểm -> Chặn luôn
    elif score >= 30:
        action = "force_3ds"    # Khả nghi -> Ép xác thực OTP (SCA)
    else:
        action = "allow"        # An toàn -> Cho qua bình thường

    return {
        "action": action, 
        "score": score, 
        "reason": f"ML Model Predict (Probability: {prob:.2f})"
    }