import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from typing import Optional
from dotenv import load_dotenv
import httpx

load_dotenv()

# Initialize logging
logger = logging.getLogger(__name__)

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@jjdetailing.com")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@jjdetailing.com")

# Email templates
BOOKING_CONFIRMATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
        .content { background-color: #f4f4f4; padding: 20px; margin-top: 20px; }
        .details { background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
        .button { background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>J&J Detailing</h1>
            <p>Booking Confirmation</p>
        </div>
        <div class="content">
            <h2>Thank you for your booking, {name}!</h2>
            <p>We've received your booking request and will contact you shortly to confirm the appointment.</p>
            
            <div class="details">
                <h3>Booking Details:</h3>
                <p><strong>Service:</strong> {service}</p>
                <p><strong>Vehicle:</strong> {vehicle}</p>
                <p><strong>Preferred Date:</strong> {date}</p>
                <p><strong>Preferred Time:</strong> {time}</p>
                {notes_section}
            </div>
            
            <p><strong>What's Next?</strong></p>
            <ul>
                <li>We'll review your booking and confirm availability within 24 hours</li>
                <li>You'll receive a confirmation call or text at {phone}</li>
                <li>Payment is due upon completion of service</li>
            </ul>
            
            <p>If you need to make any changes, please contact us:</p>
            <p>📞 Phone: (555) 123-4567<br>
            📧 Email: info@jjdetailing.com</p>
        </div>
        <div class="footer">
            <p>© 2024 J&J Detailing. All rights reserved.</p>
            <p>123 Main Street, City, State 12345</p>
        </div>
    </div>
</body>
</html>
"""

CONTACT_NOTIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #e74c3c; color: white; padding: 20px; text-align: center; }
        .content { background-color: #f4f4f4; padding: 20px; margin-top: 20px; }
        .message { background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Contact Message</h1>
        </div>
        <div class="content">
            <h2>You have a new message from the website</h2>
            
            <div class="message">
                <p><strong>From:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Phone:</strong> {phone}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Message:</strong></p>
                <p style="background-color: #ecf0f1; padding: 10px; border-radius: 5px;">{message}</p>
                <p><strong>Received:</strong> {timestamp}</p>
            </div>
            
            <p>Please respond to this inquiry promptly. You can reply directly to {email}.</p>
        </div>
        <div class="footer">
            <p>This is an automated message from J&J Detailing website.</p>
        </div>
    </div>
</body>
</html>
"""

CUSTOMER_CONTACT_REPLY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
        .content { background-color: #f4f4f4; padding: 20px; margin-top: 20px; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>J&J Detailing</h1>
            <p>Thank You for Contacting Us</p>
        </div>
        <div class="content">
            <h2>Hello {name},</h2>
            <p>Thank you for reaching out to J&J Detailing. We've received your message and will get back to you within 24 hours.</p>
            
            <p>In the meantime, here are some quick links that might help:</p>
            <ul>
                <li><a href="#">View Our Services</a></li>
                <li><a href="#">Check Pricing</a></li>
                <li><a href="#">Book Online</a></li>
                <li><a href="#">Read FAQs</a></li>
            </ul>
            
            <p>If your inquiry is urgent, please call us at (555) 123-4567.</p>
            
            <p>Best regards,<br>
            The J&J Detailing Team</p>
        </div>
        <div class="footer">
            <p>© 2024 J&J Detailing. All rights reserved.</p>
            <p>123 Main Street, City, State 12345</p>
        </div>
    </div>
</body>
</html>
"""

async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """Send an email using SMTP or fallback to console logging"""
    try:
        if SMTP_USER and SMTP_PASSWORD:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = FROM_EMAIL
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            # Fallback: Log email content
            logger.info(f"Email (not sent - no SMTP config):")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Content preview: {text_content[:200] if text_content else 'HTML email'}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

async def send_booking_confirmation(booking) -> bool:
    """Send booking confirmation email to customer"""
    try:
        # Format the booking details
        service_name = booking.service.name if booking.service else "Service"
        date = booking.preferred_datetime.strftime("%B %d, %Y")
        time = booking.preferred_datetime.strftime("%I:%M %p")
        
        notes_section = ""
        if booking.notes:
            notes_section = f"<p><strong>Additional Notes:</strong> {booking.notes}</p>"
        
        # Fill in the template
        html_content = BOOKING_CONFIRMATION_TEMPLATE.format(
            name=booking.name,
            service=service_name,
            vehicle=booking.vehicle_info,
            date=date,
            time=time,
            phone=booking.phone,
            notes_section=notes_section
        )
        
        # Send email
        subject = f"Booking Confirmation - J&J Detailing"
        await send_email(booking.email, subject, html_content)
        
        # Also send notification to admin
        admin_subject = f"New Booking: {booking.name} - {service_name}"
        await send_email(ADMIN_EMAIL, admin_subject, html_content)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {str(e)}")
        return False

async def send_contact_notification(contact) -> bool:
    """Send contact form notification to admin and auto-reply to customer"""
    try:
        # Send notification to admin
        timestamp = contact.created_at.strftime("%B %d, %Y at %I:%M %p")
        
        admin_html = CONTACT_NOTIFICATION_TEMPLATE.format(
            name=contact.name,
            email=contact.email,
            phone=contact.phone or "Not provided",
            subject=contact.subject,
            message=contact.message,
            timestamp=timestamp
        )
        
        admin_subject = f"New Contact: {contact.subject}"
        await send_email(ADMIN_EMAIL, admin_subject, admin_html)
        
        # Send auto-reply to customer
        customer_html = CUSTOMER_CONTACT_REPLY_TEMPLATE.format(
            name=contact.name
        )
        
        customer_subject = "Thank you for contacting J&J Detailing"
        await send_email(contact.email, customer_subject, customer_html)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send contact notification: {str(e)}")
        return False

async def send_appointment_reminder(booking) -> bool:
    """Send appointment reminder email"""
    try:
        # Format reminder details
        service_name = booking.service.name if booking.service else "Service"
        date = booking.preferred_datetime.strftime("%B %d, %Y")
        time = booking.preferred_datetime.strftime("%I:%M %p")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Appointment Reminder</h2>
                <p>Hi {booking.name},</p>
                <p>This is a friendly reminder about your upcoming appointment:</p>
                <div style="background-color: #f4f4f4; padding: 15px; margin: 15px 0;">
                    <p><strong>Service:</strong> {service_name}</p>
                    <p><strong>Date:</strong> {date}</p>
                    <p><strong>Time:</strong> {time}</p>
                    <p><strong>Vehicle:</strong> {booking.vehicle_info}</p>
                </div>
                <p>Please let us know if you need to reschedule.</p>
                <p>We look forward to seeing you!</p>
                <p>Best regards,<br>J&J Detailing Team</p>
            </div>
        </body>
        </html>
        """
        
        subject = f"Appointment Reminder - {date} at {time}"
        return await send_email(booking.email, subject, html_content)
        
    except Exception as e:
        logger.error(f"Failed to send appointment reminder: {str(e)}")
        return False

async def send_review_request(booking) -> bool:
    """Send review request email after service completion"""
    try:
        service_name = booking.service.name if booking.service else "our service"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>How was your experience?</h2>
                <p>Hi {booking.name},</p>
                <p>Thank you for choosing J&J Detailing for {service_name}. We hope you're enjoying your freshly detailed vehicle!</p>
                <p>We'd love to hear about your experience. Your feedback helps us improve and helps other customers make informed decisions.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Leave a Review</a>
                </div>
                <p>Thank you for your business!</p>
                <p>Best regards,<br>J&J Detailing Team</p>
            </div>
        </body>
        </html>
        """
        
        subject = "How was your experience with J&J Detailing?"
        return await send_email(booking.email, subject, html_content)
        
    except Exception as e:
        logger.error(f"Failed to send review request: {str(e)}")
        return False

# Webhook integration for n8n
async def trigger_n8n_workflow(workflow_name: str, data: dict) -> bool:
    """Trigger an n8n workflow via webhook"""
    try:
        n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
        if not n8n_webhook_url:
            logger.warning("N8N webhook URL not configured")
            return False
        
        webhook_url = f"{n8n_webhook_url}/{workflow_name}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=data)
            response.raise_for_status()
            
        logger.info(f"Successfully triggered n8n workflow: {workflow_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to trigger n8n workflow: {str(e)}")
        return False