// Main JavaScript file for common functionality

// Update cart badge count on page load
document.addEventListener('DOMContentLoaded', function() {
    updateCartBadge();
    
    // Add click handlers for example chips in virtual basket
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', function() {
            const basketInput = document.getElementById('basket-input');
            if (basketInput) {
                basketInput.value = this.textContent.trim();
            }
        });
    });
});

// Function to update cart badge
function updateCartBadge() {
    fetch('/api/cart/count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('cart-badge');
            if (badge) {
                badge.textContent = data.count || 0;
                if (data.count > 0) {
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error updating cart badge:', error));
}

// Show notification
function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert--${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 16px;
        z-index: 1001;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Format price in Indian Rupees
function formatPrice(price) {
    return '₹' + parseFloat(price).toFixed(2);
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
