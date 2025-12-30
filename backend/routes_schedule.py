from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Schedule, Master
from schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from auth import get_current_master

router = APIRouter(prefix="/api/v1/schedule", tags=["schedule"])


@router.post("", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Create schedule for a day"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    # Check if schedule already exists for this day
    existing = db.query(Schedule).filter(
        Schedule.master_id == master.id,
        Schedule.day_of_week == schedule_data.day_of_week
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule already exists for this day"
        )
    
    schedule = Schedule(
        master_id=master.id,
        day_of_week=schedule_data.day_of_week,
        start_time=schedule_data.start_time,
        end_time=schedule_data.end_time,
        break_start=schedule_data.break_start,
        break_end=schedule_data.break_end,
        is_working_day=schedule_data.is_working_day
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    return schedule


@router.get("", response_model=List[ScheduleResponse])
async def get_schedule(
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Get master's schedule"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    schedules = db.query(Schedule).filter(Schedule.master_id == master.id).order_by(Schedule.day_of_week).all()
    return schedules


@router.get("/{day_of_week}", response_model=ScheduleResponse)
async def get_schedule_for_day(
    day_of_week: int,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Get schedule for specific day"""
    
    if day_of_week < 0 or day_of_week > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Day of week must be 0-6"
        )
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    schedule = db.query(Schedule).filter(
        Schedule.master_id == master.id,
        Schedule.day_of_week == day_of_week
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found for this day"
        )
    
    return schedule


@router.patch("/{day_of_week}", response_model=ScheduleResponse)
async def update_schedule(
    day_of_week: int,
    schedule_data: ScheduleUpdate,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Update schedule for a day"""
    
    if day_of_week < 0 or day_of_week > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Day of week must be 0-6"
        )
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    schedule = db.query(Schedule).filter(
        Schedule.master_id == master.id,
        Schedule.day_of_week == day_of_week
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found for this day"
        )
    
    # Update fields
    for field, value in schedule_data.dict(exclude_unset=True).items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    
    return schedule


@router.delete("/{day_of_week}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    day_of_week: int,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Delete schedule for a day"""
    
    if day_of_week < 0 or day_of_week > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Day of week must be 0-6"
        )
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    schedule = db.query(Schedule).filter(
        Schedule.master_id == master.id,
        Schedule.day_of_week == day_of_week
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found for this day"
        )
    
    db.delete(schedule)
    db.commit()
