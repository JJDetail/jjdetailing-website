# Your main.py code here

from fastapi import FastAPI, Request, Form, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from typing import Optional
import logging

# Import our modules
from app.admin import router as admin_router, get_current_user
from app.ai_tools import analyze_customer_inquiry, generate_service_recommendations
from app.database import init_db, get_db, Booking, Contact, Review, Service
from app.email_service import send_booking_confirmation, send_contact_notification

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="J&J Detailing", version="1.0.0")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key-here"))

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include admin router
app.include_router(admin_router, prefix="/admin", tags=["admin"])

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "J&J Detailing - Premium Car Detailing Services"
    })

# About page
@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {
        "request": request,
        "title": "About J&J Detailing"
    })

# Services page
@app.get("/services", response_class=HTMLResponse)
async def services(request: Request, db=Depends(get_db)):
    services = db.query(Service).filter(Service.is_active == True).all()
    return templates.TemplateResponse("services.html", {
        "request": request,
        "title": "Our Services",
        "services": services
    })

# Booking page
@app.get("/booking", response_class=HTMLResponse)
async def booking_form(request: Request, db=Depends(get_db)):
    services = db.query(Service).filter(Service.is_active == True).all()
    return templates.TemplateResponse("booking.html", {
        "request": request,
        "title": "Book Your Detailing",
        "services": services
    })

# Handle booking submission
@app.post("/booking")
async def submit_booking(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    service_id: int = Form(...),
    vehicle_make: str = Form(...),
    vehicle_model: str = Form(...),
    vehicle_year: str = Form(...),
    preferred_date: str = Form(...),
    preferred_time: str = Form(...),
    notes: Optional[str] = Form(None),
    db=Depends(get_db)
):
    try:
        # Create booking
        booking = Booking(
            name=name,
            email=email,
            phone=phone,
            service_id=service_id,
            vehicle_info=f"{vehicle_year} {vehicle_make} {vehicle_model}",
            preferred_datetime=datetime.strptime(f"{preferred_date} {preferred_time}", "%Y-%m-%d %H:%M"),
            notes=notes,
            status="pending"
        )
        db.add(booking)
        db.commit()
        
        # Send confirmation email
        await send_booking_confirmation(booking)
        
        # Use AI to analyze the inquiry
        ai_response = await analyze_customer_inquiry(notes or "")
        
        return templates.TemplateResponse("booking_success.html", {
            "request": request,
            "title": "Booking Confirmed",
            "booking": booking,
            "ai_insights": ai_response
        })
    except Exception as e:
        logger.error(f"Booking error: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Booking Error",
            "error": "There was an error processing your booking. Please try again."
        })

# Contact page
@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {
        "request": request,
        "title": "Contact Us"
    })

# Handle contact form submission
@app.post("/contact")
async def submit_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    subject: str = Form(...),
    message: str = Form(...),
    db=Depends(get_db)
):
    try:
        # Create contact entry
        contact = Contact(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        db.add(contact)
        db.commit()
        
        # Send notification
        await send_contact_notification(contact)
        
        # Use AI to generate response suggestions
        ai_suggestions = await generate_service_recommendations(message)
        
        return templates.TemplateResponse("contact_success.html", {
            "request": request,
            "title": "Message Sent",
            "suggestions": ai_suggestions
        })
    except Exception as e:
        logger.error(f"Contact error: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Contact Error",
            "error": "There was an error sending your message. Please try again."
        })

# Gallery page
@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    return templates.TemplateResponse("gallery.html", {
        "request": request,
        "title": "Our Work Gallery"
    })

# Reviews page
@app.get("/reviews", response_class=HTMLResponse)
async def reviews(request: Request, db=Depends(get_db)):
    reviews = db.query(Review).filter(Review.is_approved == True).order_by(Review.created_at.desc()).all()
    return templates.TemplateResponse("reviews.html", {
        "request": request,
        "title": "Customer Reviews",
        "reviews": reviews
    })

# FAQ page
@app.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    return templates.TemplateResponse("faq.html", {
        "request": request,
        "title": "Frequently Asked Questions"
    })

# Legal/Privacy page
@app.get("/legal", response_class=HTMLResponse)
async def legal(request: Request):
    return templates.TemplateResponse("legal.html", {
        "request": request,
        "title": "Legal & Privacy Policy"
    })

# API endpoint for service recommendations
@app.post("/api/recommendations")
async def get_recommendations(
    vehicle_type: str = Form(...),
    condition: str = Form(...),
    budget: Optional[str] = Form(None)
):
    recommendations = await generate_service_recommendations(
        f"Vehicle: {vehicle_type}, Condition: {condition}, Budget: {budget}"
    )
    return {"recommendations": recommendations}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {
        "request": request,
        "title": "Page Not Found"
    }, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return templates.TemplateResponse("500.html", {
        "request": request,
        "title": "Internal Server Error"
    }, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
