from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
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

# Database Models


# Create tables in the database

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

class SubscriptionAssign(BaseModel):
    user_id: str
    plan_id: int

class UpdateSubscription(BaseModel):
    plan_id: int


# Admin: Create a Subscription Plan
@app.post("/plans")
async def create_plan(plan: PlanCreate, db: SessionLocal = Depends(get_db)):
    # Check if a plan with the same name already exists
    existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == plan.name).first()
    if existing_plan:
        raise HTTPException(status_code=400, detail="Plan with this name already exists")

    # If no duplicate, insert the plan
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



# Admin: Update a Subscription Plan
@app.put("/plans/{plan_id}")
async def update_plan(plan_id: int, plan: PlanUpdate, db: SessionLocal = Depends(get_db)):
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

# Admin: Delete a Subscription Plan
@app.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int, db: SessionLocal = Depends(get_db)):
    existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not existing_plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    db.delete(existing_plan)
    db.commit()
    return {"message": "Plan deleted successfully"}

@app.post("/subscriptions")
async def subscribe_to_plan(user_id: str, plan_id: int, db: SessionLocal = Depends(get_db)):
    existing_subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if existing_subscription:
        raise HTTPException(status_code=400, detail="User already has a subscription.")
    new_subscription = UserSubscription(user_id=user_id, plan_id=plan_id)
    db.add(new_subscription)
    db.commit()
    return {"message": f"User {user_id} subscribed to plan {plan_id}"}

@app.get("/api/service1")
async def service1():
    return {"message": "Service 1 is active"}

@app.get("/api/service2")
async def service2():
    return {"message": "Service 2 is active"}

@app.get("/api/service3")
async def service2():
    return {"message": "Service 3 is active"}

@app.get("/api/service4")
async def service2():
    return {"message": "Service 4 is active"}

@app.get("/api/service5")
async def service2():
    return {"message": "Service 5 is active"}

@app.get("/api/service6")
async def service2():
    return {"message": "Service 6 is active"}


# User: Get Subscription Details
@app.get("/subscriptions/{user_id}")
async def get_subscription(user_id: str, db: SessionLocal = Depends(get_db)):
    user_subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not user_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    plan = user_subscription.plan
    return {
        "user_id": user_subscription.user_id,
        "plan": {
            "name": plan.name,
            "description": plan.description,
            "api_permissions": plan.api_permissions.split(","),
            "usage_limit": plan.usage_limit,
        },
        "usage_count": user_subscription.usage_count,
    }


@app.get("/access/{user_id}/{api_request}")
async def check_access(user_id: str, api_request: str, db: SessionLocal = Depends(get_db)):
    user_subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not user_subscription:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found or has no subscription.")

    plan = user_subscription.plan
    if api_request not in plan.api_permissions.split(","):
        raise HTTPException(status_code=403, detail=f"Access denied: API '{api_request}' not allowed in the plan.")

    if user_subscription.usage_count >= plan.usage_limit:
        raise HTTPException(status_code=403, detail="Access denied: Usage limit exceeded.")

    user_subscription.usage_count += 1
    db.commit()
    return {"message": "Access granted"}

@app.get("/subscriptions/{user_id}/usage")
async def get_usage(user_id: str, db: SessionLocal = Depends(get_db)):
    user_subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not user_subscription:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found.")

    plan = user_subscription.plan
    return {
        "user_id": user_id,
        "plan_name": plan.name,
        "usage_count": user_subscription.usage_count,
        "usage_limit": plan.usage_limit,
        "remaining_usage": plan.usage_limit - user_subscription.usage_count
    }


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)  # VARCHAR(255)
    description = Column(String(255), nullable=True)         # VARCHAR(255)
    api_permissions = Column(String(1024), nullable=False)   # VARCHAR(1024)
    usage_limit = Column(Integer, nullable=False)

    # Backref to UserSubscription
    subscriptions = relationship("UserSubscription", back_populates="plan")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)  # VARCHAR(255)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)  # Added column for usage count

    # Relationship with SubscriptionPlan
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)  # VARCHAR(255)
    description = Column(String(255), nullable=True)         # VARCHAR(255)
    api_endpoint = Column(String(255), unique=True, nullable=False)

Base.metadata.create_all(bind=engine)

@app.post("/permissions")
async def add_permission(name: str, api_endpoint: str, description: Optional[str] = None, db: SessionLocal = Depends(get_db)):
    existing_permission = db.query(Permission).filter(Permission.name == name).first()
    if existing_permission:
        raise HTTPException(status_code=400, detail="Permission already exists.")
    new_permission = Permission(name=name, description=description, api_endpoint=api_endpoint)
    db.add(new_permission)
    db.commit()
    return {"message": "Permission added successfully", "id": new_permission.id}


@app.put("/permissions/{permissionId}")
async def modify_permission(permissionId: int, name: Optional[str], api_endpoint: Optional[str], description: Optional[str], db: SessionLocal = Depends(get_db)):
    permission = db.query(Permission).filter(Permission.id == permissionId).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    if name:
        permission.name = name
    if api_endpoint:
        permission.api_endpoint = api_endpoint
    if description:
        permission.description = description
    db.commit()
    return {"message": "Permission updated successfully"}

@app.delete("/permissions/{permissionId}")
async def delete_permission(permissionId: int, db: SessionLocal = Depends(get_db)):
    permission = db.query(Permission).filter(Permission.id == permissionId).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    db.delete(permission)
    db.commit()
    return {"message": "Permission deleted successfully"}

@app.post("/usage/{userId}")
async def track_usage(userId: str, db: SessionLocal = Depends(get_db)):
    user_subscription = db.query(UserSubscription).filter(UserSubscription.user_id == userId).first()
    if not user_subscription:
        raise HTTPException(status_code=404, detail="User subscription not found")
    user_subscription.usage_count += 1
    db.commit()
    return {"message": "API usage tracked", "usage_count": user_subscription.usage_count}



@app.get("/usage/{userId}/limit")
async def check_limit(userId: str, db: SessionLocal = Depends(get_db)):
    user_subscription = db.query(UserSubscription).filter(UserSubscription.user_id == userId).first()
    if not user_subscription:
        raise HTTPException(status_code=404, detail="User subscription not found")
    plan = user_subscription.plan
    remaining = plan.usage_limit - user_subscription.usage_count
    status = "Within limit" if remaining > 0 else "Limit exceeded"
    return {
        "user_id": userId,
        "plan_name": plan.name,
        "usage_count": user_subscription.usage_count,
        "usage_limit": plan.usage_limit,
        "remaining_usage": remaining,
        "status": status
    }
