from transformers import pipeline
import logging
from typing import List, Dict, Any
import re
from datetime import datetime

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize AI pipelines
try:
    sentiment_analyzer = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
    summarizer = pipeline('summarization', model='facebook/bart-large-cnn')
    classifier = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')
except Exception as e:
    logger.warning(f"Failed to load AI models: {str(e)}. Using fallback methods.")
    sentiment_analyzer = None
    summarizer = None
    classifier = None

# Service categories for classification
SERVICE_CATEGORIES = [
    "exterior detailing",
    "interior detailing",
    "paint correction",
    "ceramic coating",
    "window tinting",
    "headlight restoration",
    "engine bay cleaning",
    "wheel and tire care",
    "odor removal",
    "leather conditioning"
]

# Predefined service recommendations
SERVICE_RECOMMENDATIONS = {
    "exterior detailing": {
        "basic": "Express Wash & Wax - Perfect for regular maintenance",
        "premium": "Full Exterior Detail - Complete paint decontamination and protection",
        "luxury": "Ceramic Coating Package - Ultimate long-term protection"
    },
    "interior detailing": {
        "basic": "Interior Vacuum & Wipe - Quick refresh for your cabin",
        "premium": "Deep Interior Clean - Steam cleaning and conditioning",
        "luxury": "Complete Interior Restoration - Like-new interior transformation"
    },
    "paint correction": {
        "basic": "Single Stage Polish - Remove light swirls",
        "premium": "Two-Stage Correction - Remove most defects",
        "luxury": "Multi-Stage Correction - Show car finish"
    }
}

async def analyze_customer_inquiry(inquiry: str) -> Dict[str, Any]:
    """Analyze customer inquiry for sentiment and intent"""
    try:
        result = {
            "sentiment": "neutral",
            "confidence": 0.5,
            "key_concerns": [],
            "urgency": "normal",
            "recommended_response_tone": "professional"
        }
        
        if not inquiry:
            return result
        
        # Sentiment analysis
        if sentiment_analyzer:
            try:
                sentiment_result = sentiment_analyzer(inquiry)[0]
                result["sentiment"] = sentiment_result["label"].lower()
                result["confidence"] = sentiment_result["score"]
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {str(e)}")
        
        # Extract key concerns using regex patterns
        concern_patterns = {
            "scratches": r"\b(scratch|scratches|scuff|marks?)\b",
            "dirt": r"\b(dirt|dirty|filth|mud|dusty?)\b",
            "stains": r"\b(stain|stains|spot|spots)\b",
            "odor": r"\b(smell|odor|stink|scent)\b",
            "damage": r"\b(damage|damaged|broken|crack)\b",
            "urgent": r"\b(urgent|asap|immediately|emergency|today|tomorrow)\b",
            "premium": r"\b(best|premium|luxury|high-end|expensive)\b",
            "budget": r"\b(cheap|budget|affordable|economical|value)\b"
        }
        
        inquiry_lower = inquiry.lower()
        for concern, pattern in concern_patterns.items():
            if re.search(pattern, inquiry_lower):
                result["key_concerns"].append(concern)
        
        # Determine urgency
        if "urgent" in result["key_concerns"]:
            result["urgency"] = "high"
        elif any(word in inquiry_lower for word in ["soon", "week", "quickly"]):
            result["urgency"] = "medium"
        
        # Determine response tone
        if result["sentiment"] == "negative":
            result["recommended_response_tone"] = "empathetic and solution-focused"
        elif "premium" in result["key_concerns"]:
            result["recommended_response_tone"] = "premium and detailed"
        elif "budget" in result["key_concerns"]:
            result["recommended_response_tone"] = "value-focused and helpful"
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing customer inquiry: {str(e)}")
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "key_concerns": [],
            "urgency": "normal",
            "recommended_response_tone": "professional"
        }

async def generate_service_recommendations(description: str) -> List[Dict[str, Any]]:
    """Generate service recommendations based on customer needs"""
    try:
        recommendations = []
        
        if not description:
            return recommendations
        
        # Use zero-shot classification if available
        if classifier:
            try:
                result = classifier(
                    description,
                    candidate_labels=SERVICE_CATEGORIES,
                    multi_label=True
                )
                
                # Get top 3 categories
                top_categories = []
                for label, score in zip(result["labels"], result["scores"]):
                    if score > 0.3:  # Confidence threshold
                        top_categories.append((label, score))
                
                top_categories = sorted(top_categories, key=lambda x: x[1], reverse=True)[:3]
                
            except Exception as e:
                logger.error(f"Classification failed: {str(e)}")
                top_categories = []
        else:
            # Fallback: Use keyword matching
            top_categories = []
            description_lower = description.lower()
            
            category_keywords = {
                "exterior detailing": ["exterior", "outside", "paint", "wash", "wax", "shine"],
                "interior detailing": ["interior", "inside", "seats", "carpet", "dashboard"],
                "paint correction": ["swirl", "scratch", "buff", "polish", "paint"],
                "ceramic coating": ["ceramic", "coating", "protection", "nano"],
                "odor removal": ["smell", "odor", "fresh", "scent", "stink"]
            }
            
            for category, keywords in category_keywords.items():
                if any(keyword in description_lower for keyword in keywords):
                    top_categories.append((category, 0.8))
        
        # Determine budget level
        budget_level = "premium"  # default
        if any(word in description.lower() for word in ["budget", "cheap", "affordable"]):
            budget_level = "basic"
        elif any(word in description.lower() for word in ["best", "premium", "luxury"]):
            budget_level = "luxury"
        
        # Generate recommendations for each category
        for category, confidence in top_categories:
            if category in SERVICE_RECOMMENDATIONS:
                service = SERVICE_RECOMMENDATIONS[category].get(budget_level, 
                         SERVICE_RECOMMENDATIONS[category]["premium"])
                
                recommendations.append({
                    "category": category.title(),
                    "service": service,
                    "confidence": round(confidence * 100),
                    "price_range": get_price_range(category, budget_level),
                    "duration": get_service_duration(category, budget_level),
                    "benefits": get_service_benefits(category)
                })
        
        # If no specific recommendations, provide general ones
        if not recommendations:
            recommendations = [
                {
                    "category": "Full Detail Package",
                    "service": "Complete Interior & Exterior Detail",
                    "confidence": 90,
                    "price_range": "$150-$300",
                    "duration": "3-4 hours",
                    "benefits": ["Thorough cleaning", "Paint protection", "Interior conditioning"]
                },
                {
                    "category": "Express Service",
                    "service": "Quick Wash & Interior Vacuum",
                    "confidence": 85,
                    "price_range": "$50-$80",
                    "duration": "45-60 minutes",
                    "benefits": ["Fast service", "Basic protection", "Fresh interior"]
                }
            ]
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return [{
            "category": "Standard Detail",
            "service": "Full Service Car Detail",
            "confidence": 75,
            "price_range": "$100-$200",
            "duration": "2-3 hours",
            "benefits": ["Complete cleaning", "Paint protection", "Interior refresh"]
        }]

def get_price_range(category: str, budget_level: str) -> str:
    """Get price range for a service category and budget level"""
    price_ranges = {
        "exterior detailing": {"basic": "$50-$80", "premium": "$100-$150", "luxury": "$200-$300"},
        "interior detailing": {"basic": "$60-$90", "premium": "$120-$180", "luxury": "$250-$350"},
        "paint correction": {"basic": "$200-$300", "premium": "$400-$600", "luxury": "$800-$1200"},
        "ceramic coating": {"basic": "$500-$700", "premium": "$800-$1200", "luxury": "$1500-$2500"},
        "odor removal": {"basic": "$50-$75", "premium": "$100-$150", "luxury": "$200-$300"}
    }
    
    return price_ranges.get(category, {}).get(budget_level, "$100-$200")

def get_service_duration(category: str, budget_level: str) -> str:
    """Get estimated duration for a service"""
    durations = {
        "exterior detailing": {"basic": "1-2 hours", "premium": "2-3 hours", "luxury": "3-4 hours"},
        "interior detailing": {"basic": "1-2 hours", "premium": "2-3 hours", "luxury": "4-5 hours"},
        "paint correction": {"basic": "3-4 hours", "premium": "5-6 hours", "luxury": "8-10 hours"},
        "ceramic coating": {"basic": "4-5 hours", "premium": "6-8 hours", "luxury": "1-2 days"},
        "odor removal": {"basic": "30-45 min", "premium": "1-2 hours", "luxury": "2-3 hours"}
    }
    
    return durations.get(category, {}).get(budget_level, "2-3 hours")

def get_service_benefits(category: str) -> List[str]:
    """Get key benefits for a service category"""
    benefits = {
        "exterior detailing": ["Enhanced shine", "Paint protection", "Improved resale value"],
        "interior detailing": ["Fresh interior", "Stain removal", "Leather/fabric protection"],
        "paint correction": ["Swirl removal", "Scratch repair", "Mirror finish"],
        "ceramic coating": ["Long-term protection", "Easy maintenance", "UV resistance"],
        "odor removal": ["Fresh scent", "Bacteria elimination", "Allergen reduction"]
    }
    
    return benefits.get(category, ["Professional cleaning", "Enhanced appearance", "Protection"])

async def analyze_booking_patterns(bookings_data: List[Dict]) -> Dict[str, Any]:
    """Analyze booking patterns for insights"""
    try:
        if not bookings_data:
            return {"status": "No data available"}
        
        # Basic analytics
        total_bookings = len(bookings_data)
        
        # Service popularity
        service_counts = {}
        for booking in bookings_data:
            service = booking.get("service_name", "Unknown")
            service_counts[service] = service_counts.get(service, 0) + 1
        
        # Peak booking times
        time_counts = {}
        for booking in bookings_data:
            if booking.get("preferred_time"):
                hour = int(booking["preferred_time"].split(":")[0])
                time_period = "Morning" if hour < 12 else "Afternoon" if hour < 17 else "Evening"
                time_counts[time_period] = time_counts.get(time_period, 0) + 1
        
        # Generate insights
        most_popular_service = max(service_counts.items(), key=lambda x: x[1])[0] if service_counts else "N/A"
        peak_time = max(time_counts.items(), key=lambda x: x[1])[0] if time_counts else "N/A"
        
        return {
            "total_bookings": total_bookings,
            "most_popular_service": most_popular_service,
            "peak_booking_time": peak_time,
            "service_distribution": service_counts,
            "time_distribution": time_counts,
            "insights": [
                f"Most requested service: {most_popular_service}",
                f"Peak booking time: {peak_time}",
                f"Average bookings per service: {total_bookings / len(service_counts) if service_counts else 0:.1f}"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing booking patterns: {str(e)}")
        return {"status": "Analysis failed", "error": str(e)}

async def generate_review_response(review_text: str, rating: int) -> str:
    """Generate an appropriate response to a customer review"""
    try:
        # Analyze sentiment
        sentiment = "positive" if rating >= 4 else "neutral" if rating == 3 else "negative"
        
        # Templates based on sentiment
        if sentiment == "positive":
            responses = [
                f"Thank you so much for your {rating}-star review! We're thrilled to hear about your positive experience.",
                f"We truly appreciate your feedback and {rating}-star rating! It's wonderful to know we met your expectations.",
                f"Thank you for taking the time to share your experience! Your {rating}-star review means the world to us."
            ]
        elif sentiment == "neutral":
            responses = [
                "Thank you for your honest feedback. We appreciate you taking the time to share your experience.",
                "We value your input and would love to learn how we can improve your experience next time.",
                "Thank you for your review. We're always looking for ways to enhance our services."
            ]
        else:
            responses = [
                "We sincerely apologize that your experience didn't meet expectations. Your feedback is invaluable.",
                "Thank you for bringing this to our attention. We take all feedback seriously and will address your concerns.",
                "We're sorry to hear about your experience. Please contact us directly so we can make this right."
            ]
        
        # Add personalized touch if AI is available
        if summarizer and len(review_text) > 50:
            try:
                summary = summarizer(review_text, max_length=30, min_length=10, do_sample=False)[0]['summary_text']
                return f"{responses[0]} {summary} Please visit us again soon!"
            except:
                pass
        
        return responses[0] + " We hope to serve you again soon!"
        
    except Exception as e:
        logger.error(f"Error generating review response: {str(e)}")
        return "Thank you for your feedback. We appreciate you taking the time to share your experience with us."
