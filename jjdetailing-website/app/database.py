from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jjdetailing.db")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Database models
class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, default=120)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    bookings = relationship("Booking", back_populates="service")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"))
    vehicle_info = Column(String(500))
    preferred_datetime = Column(DateTime)
    notes = Column(Text)
    status = Column(String(50), default="pending")  # pending, confirmed, completed, cancelled
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    service = relationship("Service", back_populates="bookings")

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(50))
    subject = Column(String(500))
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(200), nullable=False)
    email = Column(String(200))
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_text = Column(Text)
    service_received = Column(String(200))
    is_approved = Column(Boolean, default=False)
    admin_response = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)

class Gallery(Base):
    __tablename__ = "gallery"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    image_url = Column(String(500), nullable=False)
    category = Column(String(100))  # exterior, interior, paint correction, etc.
    is_featured = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

class FAQ(Base):
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100))  # pricing, services, booking, etc.
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# Database initialization
def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)
    
    # Add default data if tables are empty
    db = SessionLocal()
    try:
        # Add default services if none exist
        if db.query(Service).count() == 0:
            default_services = [
                Service(
                    name="Express Detail",
                    description="Quick exterior wash, interior vacuum, and tire shine",
                    price=59.99,
                    duration_minutes=60
                ),
                Service(
                    name="Standard Detail",
                    description="Full exterior wash, clay bar, wax, interior deep clean",
                    price=149.99,
                    duration_minutes=180
                ),
                Service(
                    name="Premium Detail",
                    description="Complete paint correction, ceramic coating, full interior restoration",
                    price=299.99,
                    duration_minutes=360
                ),
                Service(
                    name="Interior Deep Clean",
                    description="Steam cleaning, leather conditioning, odor removal",
                    price=99.99,
                    duration_minutes=120
                ),
                Service(
                    name="Paint Correction",
                    description="Multi-stage polish to remove swirls and scratches",
                    price=249.99,
                    duration_minutes=300
                ),
                Service(
                    name="Ceramic Coating",
                    description="Professional grade ceramic coating application",
                    price=499.99,
                    duration_minutes=480
                )
            ]
            db.add_all(default_services)
        
        # Add default FAQs if none exist
        if db.query(FAQ).count() == 0:
            default_faqs = [
                FAQ(
                    question="How long does a detail take?",
                    answer="Service times vary: Express Detail (1 hour), Standard Detail (3 hours), Premium Detail (6+ hours). We'll give you an exact timeframe when you book.",
                    category="services",
                    order_index=1
                ),
                FAQ(
                    question="Do I need to book in advance?",
                    answer="We recommend booking 2-3 days in advance, especially for weekend appointments. Same-day service may be available for express details.",
                    category="booking",
                    order_index=2
                ),
                FAQ(
                    question="What payment methods do you accept?",
                    answer="We accept cash, credit/debit cards, and digital payments (Venmo, Zelle, Apple Pay). Payment is due upon completion of service.",
                    category="pricing",
                    order_index=3
                ),
                FAQ(
                    question="Do you offer mobile detailing?",
                    answer="Yes! We offer mobile detailing services within a 15-mile radius. Additional travel fees may apply for longer distances.",
                    category="services",
                    order_index=4
                ),
                FAQ(
                    question="What's included in ceramic coating?",
                    answer="Our ceramic coating package includes paint correction, surface preparation, professional-grade ceramic coating application, and a 2-year warranty.",
                    category="services",
                    order_index=5
                ),
                FAQ(
                    question="How often should I detail my car?",
                    answer="We recommend a full detail every 3-4 months for daily drivers, or every 6 months for garage-kept vehicles. Regular maintenance keeps your car looking its best!",
                    category="services",
                    order_index=6
                )
            ]
            db.add_all(default_faqs)
        
        db.commit()
    finally:
        db.close()

# Dependency to get database session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()