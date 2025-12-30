from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Time, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="master")  # master / customer
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    master = relationship("Master", back_populates="user", uselist=False)
    
    __table_args__ = (
        Index('idx_email', 'email'),
    )


class Master(Base):
    __tablename__ = "masters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    business_name = Column(String, nullable=False)
    specialization = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="master")
    services = relationship("Service", back_populates="master", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="master", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="master", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="master", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_slug', 'slug'),
        Index('idx_user_id', 'user_id'),
    )


class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    master = relationship("Master", back_populates="services")
    bookings = relationship("Booking", back_populates="service")
    
    __table_args__ = (
        Index('idx_master_id', 'master_id'),
    )


class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # pending, confirmed, completed, cancelled, no_show
    confirmation_code = Column(String, unique=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    master = relationship("Master", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    
    __table_args__ = (
        Index('idx_master_id', 'master_id'),
        Index('idx_scheduled_at', 'scheduled_at'),
        Index('idx_status', 'status'),
    )


class Schedule(Base):
    __tablename__ = "schedule"
    
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday-Sunday)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_start = Column(Time, nullable=True)
    break_end = Column(Time, nullable=True)
    is_working_day = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    master = relationship("Master", back_populates="schedules")
    
    __table_args__ = (
        Index('idx_master_id', 'master_id'),
        UniqueConstraint('master_id', 'day_of_week', name='uq_master_day'),
    )


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False)
    phone = Column(String, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    is_blacklisted = Column(Boolean, default=False)
    total_visits = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    last_visit_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    master = relationship("Master", back_populates="customers")
    
    __table_args__ = (
        Index('idx_master_id', 'master_id'),
        Index('idx_phone', 'phone'),
        UniqueConstraint('master_id', 'phone', name='uq_master_phone'),
    )


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # income, expense
    description = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_master_id', 'master_id'),
        Index('idx_date', 'date'),
    )


class CalendarIntegration(Base):
    __tablename__ = "calendar_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False)
    provider = Column(String, nullable=False)  # google, yandex
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    calendar_id = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_master_id', 'master_id'),
        UniqueConstraint('master_id', 'provider', name='uq_master_provider'),
    )
