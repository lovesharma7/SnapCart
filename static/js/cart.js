document.addEventListener('DOMContentLoaded', () => {
    loadCart();
});

// Load cart items
async function loadCart() {
    const cartContainer = document.getElementById('cart-container');
    
    try {
        const response = await fetch(`${API_URL}/cart`);
        
        if (!response.ok) {
            cartContainer.innerHTML = '<p>Please login to view your cart.</p>';
            return;
        }
        
        const cartItems = await response.json();
        
        if (cartItems.length === 0) {
            cartContainer.innerHTML = '<p>Your cart is empty.</p>';
            updateCartSummary(0, 0);
            return;
        }
        
        cartContainer.innerHTML = cartItems.map(item => `
            <div class="cart-item">
                <div class="cart-item-image">
                    ${item.image_url ? `<img src="${item.image_url}" alt="${item.product_name}" style="width:100%; height:100%; object-fit:cover;">` : 'Image'}
                </div>
                <div class="cart-item-info">
                    <h3>${item.product_name}</h3>
                    <p>Price: $${item.price}</p>
                    <p>${item.color ? `Color: ${item.color}` : ''} ${item.size ? `| Size: ${item.size}` : ''}</p>
                </div>
                <div class="cart-item-controls">
                    <div class="quantity-control">
                        <button onclick="updateQuantity(${item.cart_item_id}, ${item.quantity - 1})">-</button>
                        <input type="number" value="${item.quantity}" readonly>
                        <button onclick="updateQuantity(${item.cart_item_id}, ${item.quantity + 1})">+</button>
                    </div>
                    <p><strong>$${(item.price * item.quantity).toFixed(2)}</strong></p>
                    <button class="btn btn-danger" onclick="removeFromCart(${item.cart_item_id})">Remove</button>
                </div>
            </div>
        `).join('');
        
        // Calculate totals
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        const totalPrice = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        updateCartSummary(totalItems, totalPrice);
        
    } catch (error) {
        console.error('Error loading cart:', error);
        cartContainer.innerHTML = '<p>Error loading cart.</p>';
    }
}

// Update cart summary
function updateCartSummary(totalItems, totalPrice) {
    document.getElementById('total-items').textContent = totalItems;
    document.getElementById('total-price').textContent = totalPrice.toFixed(2);
}

// Update quantity
async function updateQuantity(cartItemId, newQuantity) {
    if (newQuantity < 1) {
        removeFromCart(cartItemId);
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/cart/update`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                cart_item_id: cartItemId,
                quantity: newQuantity
            })
        });
        
        if (response.ok) {
            loadCart();
        }
    } catch (error) {
        console.error('Error updating quantity:', error);
    }
}

// Remove from cart
async function removeFromCart(cartItemId) {
    if (!confirm('Remove this item from cart?')) return;
    
    try {
        const response = await fetch(`${API_URL}/cart/remove/${cartItemId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadCart();
            updateCartCount();
        }
    } catch (error) {
        console.error('Error removing item:', error);
    }
}
