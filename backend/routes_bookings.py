from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import secrets

from database import get_db
from models import Booking, Master, Service, Customer
from schemas import BookingCreate, BookingUpdate, BookingResponse
from auth import get_current_master
from email_service import EmailService

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Create a booking (for master)"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    # Verify service belongs to master
    service = db.query(Service).filter(
        Service.id == booking_data.service_id,
        Service.master_id == master.id
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Generate confirmation code
    confirmation_code = secrets.token_urlsafe(8)
    
    # Create booking
    booking = Booking(
        master_id=master.id,
        customer_name=booking_data.customer_name,
        customer_phone=booking_data.customer_phone,
        customer_email=booking_data.customer_email,
        service_id=booking_data.service_id,
        scheduled_at=booking_data.scheduled_at,
        confirmation_code=confirmation_code,
        status="confirmed"
    )
    db.add(booking)
    db.flush()
    
    # Update or create customer
    customer = db.query(Customer).filter(
        Customer.master_id == master.id,
        Customer.phone == booking_data.customer_phone
    ).first()
    
    if customer:
        customer.total_visits += 1
        customer.total_spent += service.price
        customer.last_visit_at = booking_data.scheduled_at
    else:
        customer = Customer(
            master_id=master.id,
            phone=booking_data.customer_phone,
            name=booking_data.customer_name,
            email=booking_data.customer_email,
            total_visits=1,
            total_spent=service.price,
            last_visit_at=booking_data.scheduled_at
        )
        db.add(customer)
    
    db.commit()
    db.refresh(booking)
    
    # Send confirmation email
    if booking_data.customer_email:
        await EmailService.send_booking_confirmation(
            email=booking_data.customer_email,
            customer_name=booking_data.customer_name,
            service_name=service.name,
            scheduled_at=booking_data.scheduled_at.isoformat(),
            master_name=master.business_name,
            confirmation_code=confirmation_code
        )
    
    return booking


@router.get("", response_model=List[BookingResponse])
async def list_bookings(
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """List all bookings for master"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    bookings = db.query(Booking).filter(Booking.master_id == master.id).order_by(Booking.scheduled_at).all()
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Get booking by ID"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.master_id == master.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    return booking


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    booking_data: BookingUpdate,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Update booking"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.master_id == master.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Update fields
    for field, value in booking_data.dict(exclude_unset=True).items():
        setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: int,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Cancel booking"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.master_id == master.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    booking.status = "cancelled"
    db.commit()
