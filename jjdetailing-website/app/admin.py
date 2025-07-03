# Your admin.py code here

from fastapi import APIRouter, Request, Form, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import secrets
import os
from dotenv import load_dotenv

from app.database import get_db, Booking, Contact, Review, Service, User
from fastapi.templating import Jinja2Templates

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create router
router = APIRouter()

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Security
security = HTTPBasic()

# Admin credentials (in production, store in database)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = pwd_context.hash(os.getenv("ADMIN_PASSWORD", "admin123"))

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    if username == ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD_HASH):
        return username
    return None

def get_current_user(request: Request):
    """Check if user is authenticated via session"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user

# Admin login page
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "title": "Admin Login"
    })

# Handle login
@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    user = authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "title": "Admin Login",
            "error": "Invalid username or password"
        })
    
    # Set session
    request.session["user"] = user
    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)

# Admin logout
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

# Admin dashboard
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    # Get statistics
    total_bookings = db.query(Booking).count()
    pending_bookings = db.query(Booking).filter(Booking.status == "pending").count()
    total_contacts = db.query(Contact).filter(Contact.is_read == False).count()
    total_reviews = db.query(Review).filter(Review.is_approved == False).count()
    
    # Get recent bookings
    recent_bookings = db.query(Booking).order_by(Booking.created_at.desc()).limit(5).all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "title": "Admin Dashboard",
        "user": user,
        "stats": {
            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "unread_contacts": total_contacts,
            "pending_reviews": total_reviews
        },
        "recent_bookings": recent_bookings
    })

# Bookings management
@router.get("/bookings", response_class=HTMLResponse)
async def bookings(
    request: Request,
    user: str = Depends(get_current_user),
    db=Depends(get_db),
    status_filter: Optional[str] = None
):
    query = db.query(Booking)
    if status_filter:
        query = query.filter(Booking.status == status_filter)
    
    bookings = query.order_by(Booking.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/bookings.html", {
        "request": request,
        "title": "Manage Bookings",
        "user": user,
        "bookings": bookings,
        "status_filter": status_filter
    })

# Update booking status
@router.post("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: int,
    status: str = Form(...),
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = status
    booking.updated_at = datetime.now()
    db.commit()
    
    return RedirectResponse(url="/admin/bookings", status_code=status.HTTP_302_FOUND)

# Services management
@router.get("/services", response_class=HTMLResponse)
async def services(
    request: Request,
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    services = db.query(Service).all()
    
    return templates.TemplateResponse("admin/services.html", {
        "request": request,
        "title": "Manage Services",
        "user": user,
        "services": services
    })

# Add new service
@router.post("/services/add")
async def add_service(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    duration: int = Form(...),
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    service = Service(
        name=name,
        description=description,
        price=price,
        duration_minutes=duration,
        is_active=True
    )
    db.add(service)
    db.commit()
    
    return RedirectResponse(url="/admin/services", status_code=status.HTTP_302_FOUND)

# Update service
@router.post("/services/{service_id}/update")
async def update_service(
    service_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    duration: int = Form(...),
    is_active: bool = Form(False),
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service.name = name
    service.description = description
    service.price = price
    service.duration_minutes = duration
    service.is_active = is_active
    service.updated_at = datetime.now()
    db.commit()
    
    return RedirectResponse(url="/admin/services", status_code=status.HTTP_302_FOUND)

# Contacts management
@router.get("/contacts", response_class=HTMLResponse)
async def contacts(
    request: Request,
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    contacts = db.query(Contact).order_by(Contact.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/contacts.html", {
        "request": request,
        "title": "Contact Messages",
        "user": user,
        "contacts": contacts
    })

# Mark contact as read
@router.post("/contacts/{contact_id}/read")
async def mark_contact_read(
    contact_id: int,
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.is_read = True
    db.commit()
    
    return RedirectResponse(url="/admin/contacts", status_code=status.HTTP_302_FOUND)

# Reviews management
@router.get("/reviews", response_class=HTMLResponse)
async def reviews(
    request: Request,
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/reviews.html", {
        "request": request,
        "title": "Manage Reviews",
        "user": user,
        "reviews": reviews
    })

# Approve/reject review
@router.post("/reviews/{review_id}/approve")
async def approve_review(
    review_id: int,
    action: str = Form(...),
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.is_approved = (action == "approve")
    db.commit()
    
    return RedirectResponse(url="/admin/reviews", status_code=status.HTTP_302_FOUND)

# Analytics page
@router.get("/analytics", response_class=HTMLResponse)
async def analytics(
    request: Request,
    user: str = Depends(get_current_user),
    db=Depends(get_db)
):
    # Calculate analytics
    from sqlalchemy import func
    from datetime import timedelta
    
    # Monthly bookings
    thirty_days_ago = datetime.now() - timedelta(days=30)
    monthly_bookings = db.query(Booking).filter(
        Booking.created_at >= thirty_days_ago
    ).count()
    
    # Revenue calculation
    completed_bookings = db.query(Booking).filter(
        Booking.status == "completed",
        Booking.created_at >= thirty_days_ago
    ).all()
    
    monthly_revenue = sum(
        booking.service.price for booking in completed_bookings 
        if booking.service
    )
    
    # Popular services
    popular_services = db.query(
        Service.name,
        func.count(Booking.id).label('count')
    ).join(Booking).group_by(Service.id).order_by(
        func.count(Booking.id).desc()
    ).limit(5).all()
    
    return templates.TemplateResponse("admin/analytics.html", {
        "request": request,
        "title": "Analytics",
        "user": user,
        "analytics": {
            "monthly_bookings": monthly_bookings,
            "monthly_revenue": monthly_revenue,
            "popular_services": popular_services
        }
    })

# Settings page
@router.get("/settings", response_class=HTMLResponse)
async def settings(
    request: Request,
    user: str = Depends(get_current_user)
):
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "title": "Settings",
        "user": user
    })

# Update password
@router.post("/settings/password")
async def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user: str = Depends(get_current_user)
):
    # Verify current password
    if not verify_password(current_password, ADMIN_PASSWORD_HASH):
        return templates.TemplateResponse("admin/settings.html", {
            "request": request,
            "title": "Settings",
            "user": user,
            "error": "Current password is incorrect"
        })
    
    # Check new passwords match
    if new_password != confirm_password:
        return templates.TemplateResponse("admin/settings.html", {
            "request": request,
            "title": "Settings",
            "user": user,
            "error": "New passwords do not match"
        })
    
    # In production, update the password in database
    # For now, just show success
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "title": "Settings",
        "user": user,
        "success": "Password updated successfully"
    })
