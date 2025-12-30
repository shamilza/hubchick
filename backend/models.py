from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Time
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # master / customer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Master(Base):
    __tablename__ = "masters"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    slug = Column(String, unique=True, index=True)
    business_name = Column(String)
    specialization = Column(String)
    avatar_url = Column(String, nullable=True)

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"))
    name = Column(String)
    duration_minutes = Column(Integer)
    price = Column(Float)
    is_active = Column(Boolean, default=True)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"))
    customer_phone = Column(String)
    customer_name = Column(String)
    service_id = Column(Integer, ForeignKey("services.id"))
    scheduled_at = Column(DateTime)
    status = Column(String) # pending / confirmed / completed / cancelled / no_show
    created_at = Column(DateTime, default=datetime.utcnow)

class Schedule(Base):
    __tablename__ = "schedule"
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"))
    day_of_week = Column(Integer) # 0-6
    start_time = Column(Time)
    end_time = Column(Time)
    break_start = Column(Time, nullable=True)
    break_end = Column(Time, nullable=True)
    is_working_day = Column(Boolean, default=True)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"))
    phone = Column(String)
    name = Column(String)
    notes = Column(String, nullable=True)
    is_blacklisted = Column(Boolean, default=False)
    total_visits = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    last_visit_at = Column(DateTime, nullable=True)
