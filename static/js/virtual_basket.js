// Virtual Basket functionality

document.addEventListener('DOMContentLoaded', function() {
    const parseButton = document.getElementById('parse-basket-btn');
    const basketInput = document.getElementById('basket-input');
    const loadingState = document.getElementById('loading-state');
    const resultsSection = document.getElementById('results-section');
    const emptyState = document.getElementById('empty-state');

    if (parseButton) {
        parseButton.addEventListener('click', function() {
            const inputText = basketInput.value.trim();
            
            if (!inputText) {
                showNotification('Please enter what you\'re looking for', 'warning');
                return;
            }
            
            // Show loading state
            loadingState.style.display = 'block';
            resultsSection.style.display = 'none';
            emptyState.style.display = 'none';
            
            // Call API
            fetch('/api/virtual-basket/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: inputText })
            })
            .then(response => response.json())
            .then(data => {
                loadingState.style.display = 'none';
                
                if (data.error) {
                    showNotification(data.error, 'error');
                    emptyState.style.display = 'block';
                    return;
                }
                
                // Display results
                displayResults(data);
                resultsSection.style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                loadingState.style.display = 'none';
                showNotification('Failed to process your request', 'error');
                emptyState.style.display = 'block';
            });
        });
    }
});

function displayResults(data) {
    // Display parsed items
    const parsedItemsContainer = document.getElementById('parsed-items');
    parsedItemsContainer.innerHTML = '';
    
    if (data.parsed_items && data.parsed_items.length > 0) {
        data.parsed_items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'parsed-item';
            itemDiv.innerHTML = `
                <strong>${item.quantity}x</strong> 
                ${item.color ? '<span style="color: var(--color-primary);">' + item.color + '</span> ' : ''}${item.type}
            `;
            parsedItemsContainer.appendChild(itemDiv);
        });
    } else {
        parsedItemsContainer.innerHTML = '<p style="color: var(--color-text-secondary);">No items could be parsed from your input.</p>';
    }
    
    // Display suggested combos FIRST (most important)
    const combosContainer = document.getElementById('suggested-combos');
    combosContainer.innerHTML = '';
    
    if (data.combos && data.combos.length > 0) {
        data.combos.forEach((combo, index) => {
            const comboCard = document.createElement('div');
            comboCard.className = 'combo-card';
            comboCard.style.background = index === 0 ? 'linear-gradient(135deg, rgba(33, 128, 141, 0.05) 0%, rgba(26, 104, 115, 0.02) 100%)' : 'var(--color-surface)';
            
            let comboHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-16);">
                    <h3 style="margin: 0;">${combo.name}</h3>
                    ${index === 0 ? '<span class="status status--success">Best Match</span>' : ''}
                </div>
                <p style="color: var(--color-text-secondary); margin-bottom: var(--space-16);">${combo.description}</p>
                <div class="combo-items-grid">
            `;
            
            combo.items.forEach(product => {
                comboHTML += `
                    <div class="combo-item">
                        <a href="/product/${product.id}" style="text-decoration: none; color: inherit;">
                            <img src="${product.image_url}" alt="${product.name}">
                            <h4 style="font-size: var(--font-size-base); margin-bottom: var(--space-4);">${product.name}</h4>
                            ${product.color ? `<p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-4);">Color: ${product.color}</p>` : ''}
                            <p class="product-price" style="margin: 0;">₹${parseFloat(product.price).toFixed(2)}</p>
                        </a>
                    </div>
                `;
            });
            
            comboHTML += `
                </div>
                <div class="combo-total" style="display: flex; justify-content: space-between; align-items: center; margin-top: var(--space-20); padding-top: var(--space-16); border-top: 2px solid var(--color-border);">
                    <span style="font-size: var(--font-size-lg);">Total Price:</span>
                    <span style="font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); color: var(--color-primary);">₹${combo.total_price.toFixed(2)}</span>
                </div>
                <button class="btn btn--primary btn--full-width" style="margin-top: var(--space-16);" onclick="addComboToCart(${JSON.stringify(combo.items.map(p => p.id))})">
                    Add Entire Combo to Cart
                </button>
            `;
            
            comboCard.innerHTML = comboHTML;
            combosContainer.appendChild(comboCard);
        });
    } else {
        combosContainer.innerHTML = `
            <div class="card">
                <div class="card__body">
                    <p style="text-align: center; color: var(--color-text-secondary);">
                        ${data.suggestions && data.suggestions.length > 0 ? 
                          'Could not find matching products for all items. Check individual suggestions below.' : 
                          'No combo suggestions available. Try different items or colors!'}
                    </p>
                </div>
            </div>
        `;
    }
    
    // Display individual product suggestions (SECONDARY)
    const suggestionsContainer = document.getElementById('product-suggestions');
    suggestionsContainer.innerHTML = '';
    
    if (data.suggestions && data.suggestions.length > 0) {
        data.suggestions.forEach(suggestion => {
            const sectionDiv = document.createElement('div');
            sectionDiv.style.marginBottom = 'var(--space-32)';
            
            const item = suggestion.item;
            const itemTitle = `${item.quantity}x ${item.color ? item.color + ' ' : ''}${item.type}`;
            
            sectionDiv.innerHTML = `
                <h3 style="margin-bottom: var(--space-16); color: var(--color-text);">
                    Matching products for: <span style="color: var(--color-primary);">${itemTitle}</span>
                </h3>
            `;
            
            const productsGrid = document.createElement('div');
            productsGrid.className = 'products-grid';
            
            if (suggestion.products && suggestion.products.length > 0) {
                suggestion.products.forEach(product => {
                    const productCard = createProductCard(product);
                    productsGrid.appendChild(productCard);
                });
            } else {
                productsGrid.innerHTML = '<p style="color: var(--color-text-secondary);">No matching products found for this item.</p>';
            }
            
            sectionDiv.appendChild(productsGrid);
            suggestionsContainer.appendChild(sectionDiv);
        });
    } else {
        suggestionsContainer.innerHTML = `
            <div class="card">
                <div class="card__body">
                    <p style="text-align: center; color: var(--color-text-secondary);">
                        No individual product suggestions available.
                    </p>
                </div>
            </div>
        `;
    }
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    
    card.innerHTML = `
        <a href="/product/${product.id}">
            <div class="product-image">
                <img src="${product.image_url}" alt="${product.name}">
                ${product.color ? `<span class="product-badge">${product.color}</span>` : ''}
            </div>
            <div class="product-info">
                <h3 class="product-name">${product.name}</h3>
                <p class="product-description">${product.description ? product.description.substring(0, 60) + '...' : ''}</p>
                <p class="product-price">₹${parseFloat(product.price).toFixed(2)}</p>
                ${product.stock > 0 ? 
                    '<span class="status status--success">In Stock</span>' : 
                    '<span class="status status--error">Out of Stock</span>'}
            </div>
        </a>
        ${product.stock > 0 ? `
            <button class="btn btn--primary btn--full-width add-to-cart-btn-vb" 
                    data-product-id="${product.id}">
                Add to Cart
            </button>
        ` : ''}
    `;
    
    // Add event listener for add to cart button
    const addButton = card.querySelector('.add-to-cart-btn-vb');
    if (addButton) {
        addButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const productId = this.dataset.productId;
            addToCart(productId, 1);
        });
    }
    
    return card;
}

// Function to add entire combo to cart
function addComboToCart(productIds) {
    if (!productIds || productIds.length === 0) return;
    
    let addedCount = 0;
    const totalItems = productIds.length;
    
    productIds.forEach((productId, index) => {
        fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                product_id: parseInt(productId), 
                quantity: 1
            })
        })
        .then(response => response.json())
        .then(data => {
            addedCount++;
            if (addedCount === totalItems) {
                if (data.success || addedCount > 0) {
                    showNotification(`Added ${addedCount} items to cart!`, 'success');
                    updateCartBadge();
                } else {
                    showNotification('Failed to add some items', 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
}

// Helper function for notifications (should match cart.js)
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
    
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
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
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add to cart function (should match cart.js)
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
