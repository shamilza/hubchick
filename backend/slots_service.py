from datetime import datetime, timedelta, time
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import Schedule, Booking, Service, Master
from database import redis_client
import json


class SlotsService:
    """Service for calculating available time slots"""
    
    @staticmethod
    def get_available_slots(
        master_id: int,
        date: datetime,
        service_duration: int,
        db: Session
    ) -> List[dict]:
        """
        Calculate available slots for a specific date and service duration.
        
        Args:
            master_id: ID of the master
            date: Date to check availability
            service_duration: Duration of service in minutes
            db: Database session
            
        Returns:
            List of available time slots
        """
        
        # Get schedule for the day of week
        day_of_week = date.weekday()
        schedule = db.query(Schedule).filter(
            Schedule.master_id == master_id,
            Schedule.day_of_week == day_of_week
        ).first()
        
        if not schedule or not schedule.is_working_day:
            return []
        
        # Get all bookings for this date
        date_start = datetime.combine(date.date(), time.min)
        date_end = datetime.combine(date.date(), time.max)
        
        bookings = db.query(Booking).filter(
            and_(
                Booking.master_id == master_id,
                Booking.scheduled_at >= date_start,
                Booking.scheduled_at <= date_end,
                Booking.status.in_(["pending", "confirmed"])
            )
        ).all()
        
        # Convert bookings to occupied slots
        occupied_slots = []
        for booking in bookings:
            service = db.query(Service).filter(Service.id == booking.service_id).first()
            if service:
                end_time = booking.scheduled_at + timedelta(minutes=service.duration_minutes)
                occupied_slots.append({
                    "start": booking.scheduled_at,
                    "end": end_time
                })
        
        # Generate available slots
        available_slots = SlotsService._generate_slots(
            schedule, date, service_duration, occupied_slots
        )
        
        return available_slots
    
    @staticmethod
    def _generate_slots(
        schedule: Schedule,
        date: datetime,
        service_duration: int,
        occupied_slots: List[dict]
    ) -> List[dict]:
        """Generate available time slots"""
        
        slots = []
        
        # Convert schedule times to datetime
        work_start = datetime.combine(date.date(), schedule.start_time)
        work_end = datetime.combine(date.date(), schedule.end_time)
        
        # Handle break time
        break_start = None
        break_end = None
        if schedule.break_start and schedule.break_end:
            break_start = datetime.combine(date.date(), schedule.break_start)
            break_end = datetime.combine(date.date(), schedule.break_end)
        
        # Generate 15-minute slots
        current_time = work_start
        while current_time + timedelta(minutes=service_duration) <= work_end:
            slot_end = current_time + timedelta(minutes=service_duration)
            
            # Check if slot overlaps with break
            if break_start and break_end:
                if (current_time < break_end and slot_end > break_start):
                    current_time += timedelta(minutes=15)
                    continue
            
            # Check if slot is occupied
            is_occupied = False
            for occupied in occupied_slots:
                if (current_time < occupied["end"] and slot_end > occupied["start"]):
                    is_occupied = True
                    break
            
            if not is_occupied:
                slots.append({
                    "start_time": current_time.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "available": True
                })
            
            current_time += timedelta(minutes=15)
        
        return slots
    
    @staticmethod
    def reserve_slot(
        master_id: int,
        slot_start: datetime,
        slot_end: datetime,
        ttl: int = 300
    ) -> str:
        """
        Reserve a slot using Redis to prevent double-booking.
        
        Args:
            master_id: ID of the master
            slot_start: Start time of the slot
            slot_end: End time of the slot
            ttl: Time to live in seconds (default 5 minutes)
            
        Returns:
            Reservation ID
        """
        
        reservation_id = f"slot_{master_id}_{slot_start.timestamp()}_{slot_end.timestamp()}"
        
        # Check if slot is already reserved
        if redis_client.exists(reservation_id):
            return None
        
        # Reserve the slot
        redis_client.setex(
            reservation_id,
            ttl,
            json.dumps({
                "master_id": master_id,
                "start": slot_start.isoformat(),
                "end": slot_end.isoformat(),
                "reserved_at": datetime.utcnow().isoformat()
            })
        )
        
        return reservation_id
    
    @staticmethod
    def release_slot(reservation_id: str) -> bool:
        """Release a reserved slot"""
        return bool(redis_client.delete(reservation_id))
    
    @staticmethod
    def is_slot_available(
        master_id: int,
        slot_start: datetime,
        slot_end: datetime,
        db: Session
    ) -> bool:
        """Check if a slot is available (not reserved and not booked)"""
        
        # Check Redis reservation
        reservation_id = f"slot_{master_id}_{slot_start.timestamp()}_{slot_end.timestamp()}"
        if redis_client.exists(reservation_id):
            return False
        
        # Check database bookings
        overlapping_bookings = db.query(Booking).filter(
            and_(
                Booking.master_id == master_id,
                Booking.scheduled_at < slot_end,
                Booking.scheduled_at + timedelta(minutes=0) > slot_start,  # Will be updated with service duration
                Booking.status.in_(["pending", "confirmed"])
            )
        ).first()
        
        return overlapping_bookings is None
    
    @staticmethod
    def get_master_availability(
        master_id: int,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> dict:
        """Get availability for a date range"""
        
        availability = {}
        current_date = start_date
        
        while current_date <= end_date:
            day_key = current_date.strftime("%Y-%m-%d")
            
            # Get schedule for this day
            day_of_week = current_date.weekday()
            schedule = db.query(Schedule).filter(
                Schedule.master_id == master_id,
                Schedule.day_of_week == day_of_week
            ).first()
            
            if schedule and schedule.is_working_day:
                availability[day_key] = {
                    "working": True,
                    "start_time": schedule.start_time.isoformat(),
                    "end_time": schedule.end_time.isoformat(),
                    "break_start": schedule.break_start.isoformat() if schedule.break_start else None,
                    "break_end": schedule.break_end.isoformat() if schedule.break_end else None
                }
            else:
                availability[day_key] = {
                    "working": False
                }
            
            current_date += timedelta(days=1)
        
        return availability
