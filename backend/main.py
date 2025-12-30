from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta
import secrets
import uuid

from config import settings
from database import get_db, engine
from models import Base, User, Master
from schemas import (
    UserRegister, UserLogin, TokenResponse, 
    MasterProfileResponse, RefreshTokenRequest
)
from auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, verify_token, get_current_master
)
from email_service import EmailService
from routes_services import router as services_router
from routes_schedule import router as schedule_router
from routes_bookings import router as bookings_router
from routes_public import router as public_router
from routes_calendar import router as calendar_router
from routes_customers import router as customers_router
from routes_finance import router as finance_router

# Create tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create routers
auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
master_router = APIRouter(prefix="/api/v1/master", tags=["master"])


# ============= Auth Endpoints =============

@auth_router.post("/register", response_model=dict)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new master"""
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create verification code
    verification_code = secrets.token_urlsafe(32)
    
    # Create user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        verification_code=verification_code,
        role="master"
    )
    db.add(user)
    db.flush()
    
    # Create master profile
    slug = user_data.business_name.lower().replace(" ", "-") + "-" + str(user.id)
    master = Master(
        user_id=user.id,
        slug=slug,
        business_name=user_data.business_name,
        specialization=user_data.specialization
    )
    db.add(master)
    db.commit()
    
    # Send verification email
    await EmailService.send_verification_email(user_data.email, verification_code)
    
    return {
        "message": "Registration successful. Please check your email to verify your account.",
        "user_id": user.id,
        "email": user.email
    }


@auth_router.post("/verify", response_model=dict)
async def verify_email(code: str, db: Session = Depends(get_db)):
    """Verify email with code"""
    
    user = db.query(User).filter(User.verification_code == code).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    user.is_verified = True
    user.verification_code = None
    db.commit()
    
    return {"message": "Email verified successfully"}


@auth_router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password"""
    
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email."
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "email": user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    
    try:
        payload = verify_token(request.refresh_token)
        user_id = payload.get("sub")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=request.refresh_token
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


# ============= Master Profile Endpoints =============

@master_router.get("/profile", response_model=MasterProfileResponse)
async def get_master_profile(
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Get master profile"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    return master


@master_router.patch("/profile", response_model=MasterProfileResponse)
async def update_master_profile(
    profile_data: dict,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Update master profile"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    # Update fields
    for field, value in profile_data.items():
        if value is not None and hasattr(master, field):
            setattr(master, field, value)
    
    db.commit()
    return master


# ============= Health Check =============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Hubchick API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include routers
app.include_router(auth_router)
app.include_router(master_router)
app.include_router(services_router)
app.include_router(schedule_router)
app.include_router(bookings_router)
app.include_router(public_router)
app.include_router(calendar_router)
app.include_router(customers_router)
app.include_router(finance_router)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
