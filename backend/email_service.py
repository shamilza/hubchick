import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
from jinja2 import Template
import asyncio


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None
    ) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.email_from_name} <{settings.email_from}>"
            msg["To"] = to_email
            
            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send email
            async with aiosmtplib.SMTP(hostname=settings.smtp_host, port=settings.smtp_port) as smtp:
                await smtp.login(settings.smtp_user, settings.smtp_password)
                await smtp.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    @staticmethod
    async def send_verification_email(email: str, verification_code: str) -> bool:
        """Send email verification code"""
        subject = "Verify your Hubchick account"
        html_content = f"""
        <h2>Welcome to Hubchick!</h2>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="http://localhost:3000/verify?code={verification_code}">Verify Email</a></p>
        <p>Or use this code: <strong>{verification_code}</strong></p>
        <p>This link expires in 24 hours.</p>
        """
        
        return await EmailService.send_email(email, subject, html_content)
    
    @staticmethod
    async def send_booking_confirmation(
        email: str,
        customer_name: str,
        service_name: str,
        scheduled_at: str,
        master_name: str,
        confirmation_code: str
    ) -> bool:
        """Send booking confirmation email"""
        subject = f"Booking Confirmation - {service_name}"
        html_content = f"""
        <h2>Booking Confirmed!</h2>
        <p>Hi {customer_name},</p>
        <p>Your booking with <strong>{master_name}</strong> has been confirmed.</p>
        <ul>
            <li><strong>Service:</strong> {service_name}</li>
            <li><strong>Date & Time:</strong> {scheduled_at}</li>
            <li><strong>Confirmation Code:</strong> {confirmation_code}</li>
        </ul>
        <p>Please save your confirmation code for your records.</p>
        """
        
        return await EmailService.send_email(email, subject, html_content)
    
    @staticmethod
    async def send_booking_reminder(
        email: str,
        customer_name: str,
        service_name: str,
        scheduled_at: str,
        master_name: str
    ) -> bool:
        """Send booking reminder email"""
        subject = f"Reminder: Your appointment with {master_name}"
        html_content = f"""
        <h2>Appointment Reminder</h2>
        <p>Hi {customer_name},</p>
        <p>This is a reminder about your upcoming appointment.</p>
        <ul>
            <li><strong>Service:</strong> {service_name}</li>
            <li><strong>Date & Time:</strong> {scheduled_at}</li>
            <li><strong>Master:</strong> {master_name}</li>
        </ul>
        <p>See you soon!</p>
        """
        
        return await EmailService.send_email(email, subject, html_content)
    
    @staticmethod
    async def send_booking_cancellation(
        email: str,
        customer_name: str,
        service_name: str,
        scheduled_at: str,
        master_name: str
    ) -> bool:
        """Send booking cancellation email"""
        subject = f"Booking Cancelled - {service_name}"
        html_content = f"""
        <h2>Booking Cancelled</h2>
        <p>Hi {customer_name},</p>
        <p>Your booking with <strong>{master_name}</strong> has been cancelled.</p>
        <ul>
            <li><strong>Service:</strong> {service_name}</li>
            <li><strong>Date & Time:</strong> {scheduled_at}</li>
        </ul>
        <p>If you have any questions, please contact the master directly.</p>
        """
        
        return await EmailService.send_email(email, subject, html_content)
