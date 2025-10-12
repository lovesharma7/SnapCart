// API Base URL
const API_URL = 'http://127.0.0.1:5000/api';

// Check user session on page load
document.addEventListener('DOMContentLoaded', async () => {
    await checkSession();
    loadCategories();
    loadFeaturedProducts();
});

// Check if user is logged in
async function checkSession() {
    try {
        const response = await fetch(`${API_URL}/check-session`);
        const data = await response.json();
        
        const authLink = document.getElementById('auth-link');
        if (data.logged_in) {
            authLink.textContent = `Logout (${data.username})`;
            authLink.onclick = logout;
            authLink.href = '#';
        } else {
            authLink.textContent = 'Login';
            authLink.href = '/login';
        }
    } catch (error) {
        console.error('Session check error:', error);
    }
}

// Logout function
async function logout(e) {
    e.preventDefault();
    try {
        const response = await fetch(`${API_URL}/logout`, {
            method: 'POST'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Load categories
async function loadCategories() {
    const categoriesGrid = document.getElementById('categories-grid');
    if (!categoriesGrid) return;
    
    try {
        const response = await fetch(`${API_URL}/categories`);
        const categories = await response.json();
        
        categoriesGrid.innerHTML = categories.map(category => `
            <div class="category-card" onclick="filterByCategory(${category.category_id})">
                <h3>${category.category_name}</h3>
                <p>${category.description}</p>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Load featured products (first 8 products)
async function loadFeaturedProducts() {
    const featuredProducts = document.getElementById('featured-products');
    if (!featuredProducts) return;
    
    try {
        const response = await fetch(`${API_URL}/products`);
        const products = await response.json();
        
        featuredProducts.innerHTML = products.slice(0, 8).map(product => createProductCard(product)).join('');
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

// Create product card HTML
function createProductCard(product) {
    return `
        <div class="product-card">
            <div class="product-image">
                ${product.image_url ? `<img src="${product.image_url}" alt="${product.product_name}" style="width:100%; height:100%; object-fit:cover;">` : 'Image Placeholder'}
            </div>
            <div class="product-info">
                <h3>${product.product_name}</h3>
                <p class="product-details">
                    ${product.color ? `Color: ${product.color}` : ''} 
                    ${product.size ? `| Size: ${product.size}` : ''}
                </p>
                <p class="product-price">$${product.price}</p>
                <button class="btn btn-primary" onclick="addToCart(${product.product_id})">Add to Cart</button>
            </div>
        </div>
    `;
}

// Add to cart
async function addToCart(productId) {
    try {
        const response = await fetch(`${API_URL}/cart/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: 1
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Product added to cart!');
            updateCartCount();
        } else {
            alert(data.error || 'Please login to add items to cart');
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error adding to cart:', error);
        alert('Please login to add items to cart');
    }
}

// Update cart count
async function updateCartCount() {
    try {
        const response = await fetch(`${API_URL}/cart`);
        if (response.ok) {
            const cartItems = await response.json();
            const cartCount = document.getElementById('cart-count');
            if (cartCount) {
                cartCount.textContent = cartItems.length;
            }
        }
    } catch (error) {
        console.error('Error updating cart count:', error);
    }
}

// Filter by category (redirect to products page)
function filterByCategory(categoryId) {
    window.location.href = `/products?category=${categoryId}`;
}

// Initialize cart count on load
updateCartCount();
