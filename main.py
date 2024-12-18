from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get the DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Please check your environment variables.")

# Database setup
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

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    subscriptions = relationship("UserSubscription", back_populates="user")

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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    user = relationship("User", back_populates="subscriptions")

Base.metadata.create_all(bind=engine)

# Pydantic Models
class UserCreate(BaseModel):
    name: str
    email: str

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

class SubscriptionAssign(BaseModel):
    user_id: int
    plan_id: int

# Routes for User Management
@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

@app.get("/users", response_model=List[dict])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": user.id, "name": user.name, "email": user.email} for user in users]

# Routes for Subscription Plan Management
@app.post("/plans")
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == plan.name).first()
    if existing_plan:
        raise HTTPException(status_code=400, detail="Plan with this name already exists")
    new_plan = SubscriptionPlan(
        name=plan.name, description=plan.description,
        api_permissions=",".join(plan.api_permissions),
        usage_limit=plan.usage_limit
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return {"message": "Plan created successfully", "plan_id": new_plan.id}

@app.put("/plans/{plan_id}")
def update_plan(plan_id: int, plan: PlanUpdate, db: Session = Depends(get_db)):
    existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not existing_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.name:
        existing_plan.name = plan.name
    if plan.description:
        existing_plan.description = plan.description
    if plan.api_permissions:
        existing_plan.api_permissions = ",".join(plan.api_permissions)
    if plan.usage_limit:
        existing_plan.usage_limit = plan.usage_limit
    db.commit()
    return {"message": "Plan updated successfully"}

@app.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"message": "Plan deleted successfully"}

# Routes for User Subscriptions
@app.post("/subscriptions")
def assign_subscription(subscription: SubscriptionAssign, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == subscription.user_id).first()
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
    if not user or not plan:
        raise HTTPException(status_code=404, detail="User or Plan not found")
    new_subscription = UserSubscription(user_id=subscription.user_id, plan_id=subscription.plan_id)
    db.add(new_subscription)
    db.commit()
    return {"message": f"User {subscription.user_id} subscribed to plan {subscription.plan_id}"}

@app.get("/subscriptions/{user_id}")
def get_subscription(user_id: int, db: Session = Depends(get_db)):
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
        "usage_count": subscription.usage_count
    }

@app.put("/subscriptions/{user_id}")
def update_subscription(user_id: int, plan_id: int, db: Session = Depends(get_db)):
    subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    subscription.plan_id = plan_id
    db.commit()
    return {"message": f"Subscription updated to plan {plan_id}"}

# Access Control
@app.get("/access/{user_id}/{api_request}")
def check_access(user_id: int, api_request: str, db: Session = Depends(get_db)):
    subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    plan = subscription.plan
    if api_request not in plan.api_permissions.split(","):
        raise HTTPException(status_code=403, detail="Access denied")
    if subscription.usage_count >= plan.usage_limit:
        raise HTTPException(status_code=403, detail="Usage limit exceeded")
    subscription.usage_count += 1
    db.commit()
    return {"message": "Access granted"}

from fastapi import Query

# Permissions Table
class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    api_endpoint = Column(String(255), unique=True, nullable=False)

Base.metadata.create_all(bind=engine)

# Add a Permission using Query Parameters
@app.post("/permissions")
def add_permission(
    name: str = Query(..., description="Permission name"), 
    api_endpoint: str = Query(..., description="API endpoint"), 
    description: Optional[str] = Query(None, description="Permission description"), 
    db: Session = Depends(get_db)
):
    existing_permission = db.query(Permission).filter(Permission.name == name).first()
    if existing_permission:
        raise HTTPException(status_code=400, detail="Permission already exists")
    
    new_permission = Permission(name=name, description=description, api_endpoint=api_endpoint)
    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)
    return {"message": "Permission added successfully", "id": new_permission.id}
