// J&J Detailing - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                    showError(field, 'This field is required');
                } else {
                    field.classList.remove('error');
                    clearError(field);
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
    
    // Real-time form validation
    const inputs = document.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
    
    // Service recommendation system
    const vehicleTypeSelect = document.getElementById('vehicle-type');
    const conditionSelect = document.getElementById('vehicle-condition');
    const recommendationDiv = document.getElementById('service-recommendations');
    
    if (vehicleTypeSelect && conditionSelect && recommendationDiv) {
        const updateRecommendations = async () => {
            const vehicleType = vehicleTypeSelect.value;
            const condition = conditionSelect.value;
            
            if (vehicleType && condition) {
                try {
                    const response = await fetch('/api/recommendations', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `vehicle_type=${vehicleType}&condition=${condition}`
                    });
                    
                    const data = await response.json();
                    displayRecommendations(data.recommendations);
                } catch (error) {
                    console.error('Error fetching recommendations:', error);
                }
            }
        };
        
        vehicleTypeSelect.addEventListener('change', updateRecommendations);
        conditionSelect.addEventListener('change', updateRecommendations);
    }
    
    // Gallery lightbox
    const galleryItems = document.querySelectorAll('.gallery-item');
    galleryItems.forEach(item => {
        item.addEventListener('click', function() {
            const img = this.querySelector('img');
            openLightbox(img.src, img.alt);
        });
    });
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Date and time picker enhancements
    const dateInput = document.querySelector('input[type="date"]');
    const timeInput = document.querySelector('input[type="time"]');
    
    if (dateInput) {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('min', today);
        
        // Disable Sundays
        dateInput.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            if (selectedDate.getDay() === 0) { // Sunday
                alert('We are closed on Sundays. Please select another day.');
                this.value = '';
            }
        });
    }
    
    if (timeInput) {
        // Set business hours (8 AM - 6 PM)
        timeInput.setAttribute('min', '08:00');
        timeInput.setAttribute('max', '18:00');
        timeInput.setAttribute('step', '1800'); // 30-minute intervals
    }
    
    // Star rating system for reviews
    const starRatings = document.querySelectorAll('.star-rating');
    starRatings.forEach(rating => {
        const stars = rating.querySelectorAll('.star');
        stars.forEach((star, index) => {
            star.addEventListener('click', function() {
                const ratingValue = index + 1;
                rating.setAttribute('data-rating', ratingValue);
                updateStarDisplay(rating, ratingValue);
                
                // Update hidden input if exists
                const hiddenInput = rating.querySelector('input[type="hidden"]');
                if (hiddenInput) {
                    hiddenInput.value = ratingValue;
                }
            });
            
            star.addEventListener('mouseenter', function() {
                updateStarDisplay(rating, index + 1);
            });
        });
        
        rating.addEventListener('mouseleave', function() {
            const currentRating = parseInt(rating.getAttribute('data-rating')) || 0;
            updateStarDisplay(rating, currentRating);
        });
    });
    
    // Admin dashboard charts (if Chart.js is loaded)
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
});

// Helper functions
function showError(field, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    
    const existingError = field.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    field.parentElement.appendChild(errorDiv);
}

function clearError(field) {
    const errorDiv = field.parentElement.querySelector('.field-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function validateField(field) {
    const type = field.type;
    const value = field.value.trim();
    
    if (field.hasAttribute('required') && !value) {
        field.classList.add('error');
        showError(field, 'This field is required');
        return false;
    }
    
    if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            field.classList.add('error');
            showError(field, 'Please enter a valid email address');
            return false;
        }
    }
    
    if (type === 'tel' && value) {
        const phoneRegex = /^[\d\s\-\+\(\)]+$/;
        if (!phoneRegex.test(value) || value.replace(/\D/g, '').length < 10) {
            field.classList.add('error');
            showError(field, 'Please enter a valid phone number');
            return false;
        }
    }
    
    field.classList.remove('error');
    clearError(field);
    return true;
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('service-recommendations');
    if (!container) return;
    
    container.innerHTML = '<h3>Recommended Services:</h3>';
    
    recommendations.forEach(rec => {
        const recDiv = document.createElement('div');
        recDiv.className = 'recommendation-card';
        recDiv.innerHTML = `
            <h4>${rec.category}</h4>
            <p>${rec.service}</p>
            <div class="rec-details">
                <span class="price">${rec.price_range}</span>
                <span class="duration">${rec.duration}</span>
                <span class="confidence">Confidence: ${rec.confidence}%</span>
            </div>
            <ul class="benefits">
                ${rec.benefits.map(benefit => `<li>${benefit}</li>`).join('')}
            </ul>
        `;
        container.appendChild(recDiv);
    });
}

function openLightbox(src, alt) {
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.innerHTML = `
        <div class="lightbox-content">
            <span class="close">&times;</span>
            <img src="${src}" alt="${alt}">
            <div class="caption">${alt}</div>
        </div>
    `;
    
    document.body.appendChild(lightbox);
    
    // Add click handlers
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox || e.target.className === 'close') {
            lightbox.remove();
        }
    });
    
    // Add escape key handler
    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') {
            lightbox.remove();
            document.removeEventListener('keydown', escHandler);
        }
    });
}

function updateStarDisplay(rating, value) {
    const stars = rating.querySelectorAll('.star');
    stars.forEach((star, index) => {
        if (index < value) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

function initializeCharts() {
    // Bookings chart
    const bookingsCtx = document.getElementById('bookingsChart');
    if (bookingsCtx) {
        new Chart(bookingsCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                datasets: [{
                    label: 'Bookings',
                    data: [12, 19, 15, 25, 22, 30],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Services chart
    const servicesCtx = document.getElementById('servicesChart');
    if (servicesCtx) {
        new Chart(servicesCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Express Detail', 'Standard Detail', 'Premium Detail', 'Paint Correction', 'Ceramic Coating'],
                datasets: [{
                    data: [30, 25, 20, 15, 10],
                    backgroundColor: [
                        '#3498db',
                        '#2ecc71',
                        '#f39c12',
                        '#e74c3c',
                        '#9b59b6'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Service worker for PWA support
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('SW registered:', registration))
            .catch(error => console.log('SW registration failed:', error));
    });
}