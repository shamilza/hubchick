from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

from models import CalendarIntegration, Master, Booking, Service
from config import settings


class GoogleCalendarService:
    """Service for Google Calendar integration"""
    
    @staticmethod
    def get_auth_url():
        """Get Google OAuth authorization URL"""
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        flow.redirect_uri = settings.google_redirect_uri
        auth_url, state = flow.authorization_url(access_type='offline', prompt='consent')
        return auth_url, state
    
    @staticmethod
    def handle_callback(code: str, state: str):
        """Handle Google OAuth callback"""
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        flow.redirect_uri = settings.google_redirect_uri
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    @staticmethod
    def sync_booking_to_calendar(
        master_id: int,
        booking_id: int,
        db: Session
    ):
        """Sync a booking to Google Calendar"""
        
        # Get calendar integration
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.master_id == master_id,
            CalendarIntegration.provider == 'google',
            CalendarIntegration.is_active == True
        ).first()
        
        if not integration:
            return None
        
        # Get booking details
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return None
        
        service_obj = db.query(Service).filter(Service.id == booking.service_id).first()
        if not service_obj:
            return None
        
        # Create credentials
        credentials = Credentials(token=integration.access_token)
        
        # Build calendar service
        calendar_service = build('calendar', 'v3', credentials=credentials)
        
        # Create event
        event = {
            'summary': f"{booking.customer_name} - {service_obj.name}",
            'description': f"Phone: {booking.customer_phone}\nEmail: {booking.customer_email}",
            'start': {
                'dateTime': booking.scheduled_at.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': (booking.scheduled_at + timedelta(minutes=service_obj.duration_minutes)).isoformat(),
                'timeZone': 'UTC'
            },
            'attendees': [
                {'email': booking.customer_email} if booking.customer_email else {}
            ]
        }
        
        # Remove empty attendees
        event['attendees'] = [a for a in event['attendees'] if a]
        
        # Insert event
        try:
            result = calendar_service.events().insert(
                calendarId=integration.calendar_id,
                body=event,
                sendNotifications=True
            ).execute()
            
            return result.get('id')
        except Exception as e:
            print(f"Error syncing to Google Calendar: {e}")
            return None
    
    @staticmethod
    def remove_booking_from_calendar(
        master_id: int,
        event_id: str,
        db: Session
    ):
        """Remove a booking from Google Calendar"""
        
        # Get calendar integration
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.master_id == master_id,
            CalendarIntegration.provider == 'google',
            CalendarIntegration.is_active == True
        ).first()
        
        if not integration:
            return False
        
        # Create credentials
        credentials = Credentials(token=integration.access_token)
        
        # Build calendar service
        calendar_service = build('calendar', 'v3', credentials=credentials)
        
        try:
            calendar_service.events().delete(
                calendarId=integration.calendar_id,
                eventId=event_id
            ).execute()
            return True
        except Exception as e:
            print(f"Error removing from Google Calendar: {e}")
            return False


class YandexCalendarService:
    """Service for Yandex Calendar integration"""
    
    @staticmethod
    def get_auth_url():
        """Get Yandex OAuth authorization URL"""
        # Yandex OAuth implementation
        # This is a placeholder - implement according to Yandex OAuth docs
        auth_url = f"https://oauth.yandex.com/authorize?client_id={settings.yandex_client_id}&response_type=code&redirect_uri={settings.yandex_redirect_uri}"
        return auth_url
    
    @staticmethod
    def handle_callback(code: str):
        """Handle Yandex OAuth callback"""
        # Exchange code for token
        # This is a placeholder - implement according to Yandex OAuth docs
        return {
            'access_token': 'yandex_token',
            'refresh_token': 'yandex_refresh_token'
        }
    
    @staticmethod
    def sync_booking_to_calendar(
        master_id: int,
        booking_id: int,
        db: Session
    ):
        """Sync a booking to Yandex Calendar"""
        
        # Get calendar integration
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.master_id == master_id,
            CalendarIntegration.provider == 'yandex',
            CalendarIntegration.is_active == True
        ).first()
        
        if not integration:
            return None
        
        # Get booking details
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return None
        
        service_obj = db.query(Service).filter(Service.id == booking.service_id).first()
        if not service_obj:
            return None
        
        # TODO: Implement Yandex Calendar API call
        # This is a placeholder
        
        return None
    
    @staticmethod
    def remove_booking_from_calendar(
        master_id: int,
        event_id: str,
        db: Session
    ):
        """Remove a booking from Yandex Calendar"""
        
        # TODO: Implement Yandex Calendar API call
        return False


class CalendarSyncService:
    """Service for synchronizing bookings with external calendars"""
    
    @staticmethod
    def sync_booking(
        master_id: int,
        booking_id: int,
        db: Session
    ):
        """Sync booking to all connected calendars"""
        
        # Get all active calendar integrations
        integrations = db.query(CalendarIntegration).filter(
            CalendarIntegration.master_id == master_id,
            CalendarIntegration.is_active == True
        ).all()
        
        results = {}
        for integration in integrations:
            if integration.provider == 'google':
                event_id = GoogleCalendarService.sync_booking_to_calendar(
                    master_id, booking_id, db
                )
                results['google'] = event_id
            elif integration.provider == 'yandex':
                event_id = YandexCalendarService.sync_booking_to_calendar(
                    master_id, booking_id, db
                )
                results['yandex'] = event_id
        
        return results
    
    @staticmethod
    def remove_booking(
        master_id: int,
        booking_id: int,
        db: Session
    ):
        """Remove booking from all connected calendars"""
        
        # TODO: Implement removal from all calendars
        pass
