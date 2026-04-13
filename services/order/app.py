from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uuid
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./orders.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    user_id = Column(String)
    email = Column(String)
    item_id = Column(String)
    status = Column(String)

Base.metadata.create_all(bind=engine)
app = FastAPI()

class OrderRequest(BaseModel):
    product_id: str
    quantity: int

@app.post("/api/orders/create")
async def create_order(request: Request, order_req: OrderRequest):
    user_id = request.headers.get("X-User-Id")
    user_email = request.headers.get("X-User-Email")
    
    if not user_id:
        raise HTTPException(status_code=403, detail="Yêu cầu phải đi qua API Gateway")

    order_id = str(uuid.uuid4())
    new_order = Order(
        id=order_id, 
        user_id=user_id, 
        email=user_email, 
        item_id=order_req.product_id, 
        status="success"
    )
    
    db = SessionLocal()
    db.add(new_order)
    db.commit()
    db.close()
    
    return {"status": "success", "order_id": order_id, "client_secret": "pi_mock_secret_123"}