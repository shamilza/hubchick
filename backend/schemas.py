from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, time


# ============= Auth Schemas =============
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    business_name: str = Field(..., min_length=1)
    specialization: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ============= Master Schemas =============
class MasterProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    specialization: Optional[str] = None
    avatar_url: Optional[str] = None


class MasterProfileResponse(BaseModel):
    id: int
    slug: str
    business_name: str
    specialization: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


# ============= Service Schemas =============
class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=1)
    duration_minutes: int = Field(..., ge=15, le=480)
    price: float = Field(..., gt=0)


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: int
    name: str
    duration_minutes: int
    price: float
    is_active: bool

    class Config:
        from_attributes = True


# ============= Schedule Schemas =============
class ScheduleCreate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    is_working_day: bool = True


class ScheduleUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    is_working_day: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: int
    day_of_week: int
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    is_working_day: bool

    class Config:
        from_attributes = True


# ============= Booking Schemas =============
class BookingCreate(BaseModel):
    customer_name: str = Field(..., min_length=1)
    customer_phone: str = Field(..., min_length=10)
    service_id: int
    scheduled_at: datetime


class BookingUpdate(BaseModel):
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class BookingResponse(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    service_id: int
    scheduled_at: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Customer Schemas =============
class CustomerResponse(BaseModel):
    id: int
    phone: str
    name: str
    notes: Optional[str] = None
    is_blacklisted: bool
    total_visits: int
    total_spent: float
    last_visit_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============= Public Booking Schemas =============
class PublicSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    available: bool


class PublicBookingRequest(BaseModel):
    customer_name: str = Field(..., min_length=1)
    customer_phone: str = Field(..., min_length=10)
    customer_email: Optional[EmailStr] = None
    service_id: int
    scheduled_at: datetime


class PublicBookingResponse(BaseModel):
    id: int
    confirmation_code: str
    scheduled_at: datetime
    service_name: str
    master_name: str


# ============= Finance Schemas =============
class FinanceDashboard(BaseModel):
    today_earnings: float
    week_earnings: float
    month_earnings: float
    total_bookings_month: int


class TransactionResponse(BaseModel):
    id: int
    date: datetime
    description: str
    amount: float
    type: str  # income, expense
    booking_id: Optional[int] = None

    class Config:
        from_attributes = True
