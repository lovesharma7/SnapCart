// Cart functionality

// Add to cart function
function addToCart(productId, quantity = 1) {
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            product_id: parseInt(productId), 
            quantity: parseInt(quantity) 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Product added to cart!', 'success');
            updateCartBadge();
        } else if (data.error) {
            if (data.error === 'Please login first') {
                showNotification('Please login to add items to cart', 'warning');
                setTimeout(() => {
                    window.location.href = '/auth';
                }, 1500);
            } else {
                showNotification(data.error, 'error');
            }
        }
    })
    .catch(error => {
        console.error('Error adding to cart:', error);
        showNotification('Failed to add item to cart', 'error');
    });
}

// Add event listeners for "Add to Cart" buttons
document.addEventListener('DOMContentLoaded', function() {
    // Handle add to cart buttons on product cards
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation(); // Prevent navigation to product detail
            const productId = this.dataset.productId;
            addToCart(productId, 1);
        });
    });
});

// Update cart badge (defined in main.js but can be called from here)
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

// Show notification function (if not already defined in main.js)
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert--${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 16px;
        z-index: 1001;
        max-width: 400px;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        animation: slideIn 0.3s ease-out;
    `;
    
    // Add animation styles if not already present
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
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
            .alert--success {
                background: rgba(33, 128, 141, 0.1);
                border: 1px solid rgba(33, 128, 141, 0.3);
            }
            .alert--error {
                background: rgba(192, 21, 47, 0.1);
                border: 1px solid rgba(192, 21, 47, 0.3);
            }
            .alert--warning {
                background: rgba(168, 75, 47, 0.1);
                border: 1px solid rgba(168, 75, 47, 0.3);
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}
