from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Service, Master
from schemas import ServiceCreate, ServiceUpdate, ServiceResponse
from auth import get_current_master

router = APIRouter(prefix="/api/v1/services", tags=["services"])


@router.post("", response_model=ServiceResponse)
async def create_service(
    service_data: ServiceCreate,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Create a new service"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    service = Service(
        master_id=master.id,
        name=service_data.name,
        duration_minutes=service_data.duration_minutes,
        price=service_data.price
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    
    return service


@router.get("", response_model=List[ServiceResponse])
async def list_services(
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """List all services for master"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    services = db.query(Service).filter(Service.master_id == master.id).all()
    return services


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Get service by ID"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.master_id == master.id
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return service


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Update service"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.master_id == master.id
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Update fields
    for field, value in service_data.dict(exclude_unset=True).items():
        setattr(service, field, value)
    
    db.commit()
    db.refresh(service)
    
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Delete service"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found"
        )
    
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.master_id == master.id
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    db.delete(service)
    db.commit()
