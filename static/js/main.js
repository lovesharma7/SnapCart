// Main JavaScript file for common functionality

document.addEventListener('DOMContentLoaded', function() {
    updateCartBadge();

    // Virtual basket chips
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', function() {
            const basketInput = document.getElementById('basket-input');
            if (basketInput) {
                basketInput.value = this.textContent.trim();
            }
        });
    });

    // Theme toggle
    handleThemeToggle();

    // Hero slideshow (UPDATED)
    handleHeroSlideshow();
});


// ===========================
// Theme Toggle
// ===========================
function handleThemeToggle() {
    const toggleInput = document.getElementById('theme-toggle');
    const docElement = document.documentElement;

    function setToggleState() {
        const currentTheme = docElement.getAttribute('data-theme');
        toggleInput.checked = currentTheme === 'dark';
    }

    setToggleState();

    toggleInput.addEventListener('change', () => {
        if (toggleInput.checked) {
            docElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            docElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });
}


// ===========================
// HERO IMAGE SLIDESHOW (UPDATED)
// ===========================
function handleHeroSlideshow() {
    const slideshow = document.querySelector('.hero-slideshow');

    if (!slideshow) return;

    const slides = slideshow.querySelectorAll('.slide');

    if (slides.length <= 1) {
        if (slides.length === 1) slides[0].classList.add('active');
        return;
    }

    let index = 0;
    slides[index].classList.add('active');

    setInterval(() => {
        slides[index].classList.remove('active');
        index = (index + 1) % slides.length;
        slides[index].classList.add('active');
    }, 5000); // every 5 seconds
}


// ===========================
// Cart Badge
// ===========================
function updateCartBadge() {
    fetch('/api/cart/count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('cart-badge');
            if (!badge) return;

            badge.textContent = data.count || 0;
            badge.style.display = data.count > 0 ? 'inline-block' : 'none';
        })
        .catch(error => console.error('Error updating cart badge:', error));
}


// ===========================
// Notification
// ===========================
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
        animation: slideIn 0.3s ease-out;
    `;

    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to   { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to   { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}


// ===========================
// Helpers
// ===========================
function formatPrice(price) {
    return '₹' + parseFloat(price).toFixed(2);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}

// -----------------------------
// SEARCH BAR FUNCTIONALITY
// -----------------------------
document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.querySelector(".search-input");
    const searchBtn = document.querySelector(".search-btn");

    if (!searchInput || !searchBtn) return;

    function performSearch() {
        const query = searchInput.value.trim();
        if (query.length === 0) return;

        // Redirect to products with search query
        window.location.href = `/products?search=${encodeURIComponent(query)}`;
    }

    // Click event
    searchBtn.addEventListener("click", performSearch);

    // Press Enter key
    searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            performSearch();
        }
    });
});
