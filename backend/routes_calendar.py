from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import CalendarIntegration, Master
from auth import get_current_master
from calendar_service import GoogleCalendarService, YandexCalendarService

router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])


@router.get("/google/auth-url")
async def get_google_auth_url():
    """Get Google OAuth authorization URL"""
    try:
        auth_url, state = GoogleCalendarService.get_auth_url()
        return {
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Google auth URL"
        )


@router.post("/google/callback")
async def handle_google_callback(
    code: str = Query(...),
    state: str = Query(...),
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    
    try:
        # Get tokens from Google
        tokens = GoogleCalendarService.handle_callback(code, state)
        
        # Get master
        master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
        if not master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Master not found"
            )
        
        # Check if integration already exists
        existing = db.query(CalendarIntegration).filter(
            CalendarIntegration.master_id == master.id,
            CalendarIntegration.provider == 'google'
        ).first()
        
        if existing:
            existing.access_token = tokens['access_token']
            existing.refresh_token = tokens['refresh_token']
            existing.is_active = True
        else:
            # Create new integration
            integration = CalendarIntegration(
                master_id=master.id,
                provider='google',
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                calendar_id='primary',  # Use primary calendar
                is_active=True
            )
            db.add(integration)
        
        db.commit()
        
        return {
            "message": "Google Calendar connected successfully",
            "provider": "google"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect Google Calendar: {str(e)}"
        )


@router.get("/yandex/auth-url")
async def get_yandex_auth_url():
    """Get Yandex OAuth authorization URL"""
    try:
        auth_url = YandexCalendarService.get_auth_url()
        return {
            "auth_url": auth_url
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Yandex auth URL"
        )


@router.post("/yandex/callback")
async def handle_yandex_callback(
    code: str = Query(...),
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Handle Yandex OAuth callback"""
    
    try:
        # Get tokens from Yandex
        tokens = YandexCalendarService.handle_callback(code)
        
        # Get master
        master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
        if not master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Master not found"
            )
        
        # Check if integration already exists
        existing = db.query(CalendarIntegration).filter(
            CalendarIntegration.master_id == master.id,
            CalendarIntegration.provider == 'yandex'
        ).first()
        
        if existing:
            existing.access_token = tokens['access_token']
            existing.refresh_token = tokens['refresh_token']
            existing.is_active = True
        else:
            # Create new integration
            integration = CalendarIntegration(
                master_id=master.id,
                provider='yandex',
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                calendar_id='default',
                is_active=True
            )
            db.add(integration)
        
        db.commit()
        
        return {
            "message": "Yandex Calendar connected successfully",
            "provider": "yandex"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect Yandex Calendar: {str(e)}"
        )


@router.get("/integrations")
async def list_integrations(
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """List all calendar integrations for master"""
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found"
        )
    
    integrations = db.query(CalendarIntegration).filter(
        CalendarIntegration.master_id == master.id
    ).all()
    
    return [
        {
            "id": i.id,
            "provider": i.provider,
            "is_active": i.is_active,
            "calendar_id": i.calendar_id,
            "created_at": i.created_at.isoformat()
        }
        for i in integrations
    ]


@router.delete("/integrations/{provider}")
async def disconnect_calendar(
    provider: str,
    current_user: dict = Depends(get_current_master),
    db: Session = Depends(get_db)
):
    """Disconnect calendar integration"""
    
    if provider not in ['google', 'yandex']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider"
        )
    
    master = db.query(Master).filter(Master.user_id == current_user["user_id"]).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found"
        )
    
    integration = db.query(CalendarIntegration).filter(
        CalendarIntegration.master_id == master.id,
        CalendarIntegration.provider == provider
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    db.delete(integration)
    db.commit()
    
    return {
        "message": f"{provider.capitalize()} Calendar disconnected"
    }
