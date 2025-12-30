from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from database import get_db
from models import Master, Service, Booking, Customer
from schemas import PublicSlot, PublicBookingRequest, PublicBookingResponse
from slots_service import SlotsService
from email_service import EmailService

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.get("/{master_slug}/info")
async def get_master_info(
    master_slug: str,
    db: Session = Depends(get_db)
):
    """Get public master information"""
    
    master = db.query(Master).filter(Master.slug == master_slug).first()
    if not master or not master.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found"
        )
    
    services = db.query(Service).filter(
        Service.master_id == master.id,
        Service.is_active == True
    ).all()
    
    return {
        "id": master.id,
        "slug": master.slug,
        "business_name": master.business_name,
        "specialization": master.specialization,
        "avatar_url": master.avatar_url,
        "description": master.description,
        "phone": master.phone,
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "duration_minutes": s.duration_minutes,
                "price": s.price
            }
            for s in services
        ]
    }


@router.get("/{master_slug}/slots")
async def get_available_slots(
    master_slug: str,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    service_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Get available slots for a specific date and service"""
    
    master = db.query(Master).filter(Master.slug == master_slug).first()
    if not master or not master.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found"
        )
    
    # Verify service belongs to master
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.master_id == master.id,
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Parse date
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Get available slots
    slots = SlotsService.get_available_slots(
        master_id=master.id,
        date=target_date,
        service_duration=service.duration_minutes,
        db=db
    )
    
    return {
        "date": date,
        "service_id": service_id,
        "service_name": service.name,
        "slots": slots
    }


@router.post("/{master_slug}/book", response_model=PublicBookingResponse)
async def create_public_booking(
    master_slug: str,
    booking_data: PublicBookingRequest,
    db: Session = Depends(get_db)
):
    """Create a booking from public page (3-click booking)"""
    
    master = db.query(Master).filter(Master.slug == master_slug).first()
    if not master or not master.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found"
        )
    
    # Verify service
    service = db.query(Service).filter(
        Service.id == booking_data.service_id,
        Service.master_id == master.id,
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Check if slot is available
    slot_end = booking_data.scheduled_at + timedelta(minutes=service.duration_minutes)
    
    if not SlotsService.is_slot_available(
        master_id=master.id,
        slot_start=booking_data.scheduled_at,
        slot_end=slot_end,
        db=db
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot is no longer available. Please select another time."
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
        status="pending"
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
    else:
        customer = Customer(
            master_id=master.id,
            phone=booking_data.customer_phone,
            name=booking_data.customer_name,
            email=booking_data.customer_email,
            total_visits=1,
            total_spent=service.price
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
    
    return PublicBookingResponse(
        id=booking.id,
        confirmation_code=confirmation_code,
        scheduled_at=booking.scheduled_at,
        service_name=service.name,
        master_name=master.business_name
    )


@router.get("/{master_slug}/availability")
async def get_master_availability(
    master_slug: str,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get master availability for next N days"""
    
    master = db.query(Master).filter(Master.slug == master_slug).first()
    if not master or not master.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found"
        )
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    
    availability = SlotsService.get_master_availability(
        master_id=master.id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )
    
    return {
        "master_slug": master_slug,
        "availability": availability
    }
