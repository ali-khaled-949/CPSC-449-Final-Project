from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import session maker, declarative_base, relationship
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get the DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Please check your environment variables.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI Application
app = FastAPI()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Models
class PlanCreate(BaseModel):
    name: str
    description: Optional[str]
    api_permissions: List[str]
    usage_limit: int

class PlanUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    api_permissions: Optional[List[str]]
    usage_limit: Optional[int]

class UpdateSubscription(BaseModel):
    plan_id: int


# Database Models
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    api_permissions = Column(String(1024), nullable=False)
    usage_limit = Column(Integer, nullable=False)
    subscriptions = relationship("UserSubscription", back_populates="plan")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")


Base.metadata.create_all(bind=engine)


# Admin: Create a Subscription Plan
@app.post("/plans")
async def create_plan(plan: PlanCreate, db: SessionLocal = Depends(get_db)):
    existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == plan.name).first()
    if existing_plan:
        raise HTTPException(status_code=400, detail="Plan with this name already exists")

    new_plan = SubscriptionPlan(
        name=plan.name,
        description=plan.description,
        api_permissions=",".join(plan.api_permissions),
        usage_limit=plan.usage_limit,
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return {"message": "Plan created successfully", "plan_id": new_plan.id}


@app.put("/subscriptions/{user_id}")
async def update_subscription(user_id: str, update: UpdateSubscription, db: Session = Depends(get_db)):
    subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription.plan_id = update.plan_id  # Update plan_id
    db.commit()
    return {"message": f"Subscription for user {user_id} updated to plan {update.plan_id}"}


    
    # Query for the user's subscription
    subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Update the plan_id
    subscription.plan_id = update.plan_id
    db.commit()
    db.refresh(subscription)
    return {"message": f"Subscription for user {user_id} updated to plan {update.plan_id}"}


# User: Get Subscription Details
@app.get("/subscriptions/{user_id}")
async def get_subscription(user_id: str, db: SessionLocal = Depends(get_db)):
    subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    plan = subscription.plan
    return {
        "user_id": subscription.user_id,
        "plan": {
            "name": plan.name,
            "description": plan.description,
            "api_permissions": plan.api_permissions.split(","),
            "usage_limit": plan.usage_limit,
        },
        "usage_count": subscription.usage_count,
    }


# User: Check Access to an API Request
@app.get("/access/{user_id}/{api_request}")
async def check_access(user_id: str, api_request: str, db: SessionLocal = Depends(get_db)):
    subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    plan = subscription.plan
    if api_request not in plan.api_permissions.split(","):
        raise HTTPException(status_code=403, detail="Access denied: API not allowed in plan.")
    if subscription.usage_count >= plan.usage_limit:
        raise HTTPException(status_code=403, detail="Access denied: Usage limit exceeded.")

    subscription.usage_count += 1
    db.commit()
    return {"message": "Access granted"}


# Sample APIs
@app.get("/api/service1")
async def service1():
    return {"message": "Service 1 is active"}

@app.get("/api/service2")
async def service2():
    return {"message": "Service 2 is active"}

@app.get("/api/service3")
async def service3():
    return {"message": "Service 3 is active"}

@app.get("/api/service4")
async def service4():
    return {"message": "Service 4 is active"}

@app.get("/api/service5")
async def service5():
    return {"message": "Service 5 is active"}

@app.get("/api/service6")
async def service6():
    return {"message": "Service 6 is active"}
