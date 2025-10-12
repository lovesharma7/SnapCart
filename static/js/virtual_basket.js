let basketItems = [];

document.addEventListener('DOMContentLoaded', () => {
    loadCategoriesForBasket();
    
    document.getElementById('add-item-btn').addEventListener('click', addItemToBasket);
    document.getElementById('get-recommendations-btn').addEventListener('click', getRecommendations);
});

// Load categories for dropdown
async function loadCategoriesForBasket() {
    try {
        const response = await fetch(`${API_URL}/categories`);
        const categories = await response.json();
        
        const categorySelect = document.getElementById('item-category');
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.category_id;
            option.textContent = category.category_name;
            categorySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Add item to basket
function addItemToBasket() {
    const description = document.getElementById('item-description').value.trim();
    const categoryId = document.getElementById('item-category').value;
    const color = document.getElementById('item-color').value.trim();
    
    if (!description || !categoryId) {
        alert('Please enter item description and select category');
        return;
    }
    
    const item = {
        description: description,
        category_id: parseInt(categoryId),
        color: color || null
    };
    
    basketItems.push(item);
    displayBasketItems();
    
    // Clear inputs
    document.getElementById('item-description').value = '';
    document.getElementById('item-category').value = '';
    document.getElementById('item-color').value = '';
}

// Display basket items
function displayBasketItems() {
    const itemsList = document.getElementById('items-list');
    
    if (basketItems.length === 0) {
        itemsList.innerHTML = '<p>No items added yet.</p>';
        return;
    }
    
    itemsList.innerHTML = basketItems.map((item, index) => `
        <div class="basket-item">
            <span>${item.description} ${item.color ? `(${item.color})` : ''}</span>
            <button class="btn btn-danger" onclick="removeBasketItem(${index})">Remove</button>
        </div>
    `).join('');
}

// Remove item from basket
function removeBasketItem(index) {
    basketItems.splice(index, 1);
    displayBasketItems();
}

// Get recommendations
async function getRecommendations() {
    if (basketItems.length === 0) {
        alert('Please add at least one item to your virtual basket');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/virtual-basket/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                items: basketItems
            })
        });
        
        if (!response.ok) {
            alert('Please login to use virtual basket feature');
            window.location.href = '/login';
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            displayRecommendations(data.recommendations, data.combinations);
        }
    } catch (error) {
        console.error('Error getting recommendations:', error);
        alert('Error getting recommendations');
    }
}

// Display recommendations
function displayRecommendations(recommendations, combinations) {
    const recommendationsSection = document.getElementById('recommendations-section');
    const combinationsContainer = document.getElementById('combinations-container');
    const recommendationsContainer = document.getElementById('recommendations-container');
    
    recommendationsSection.style.display = 'block';
    
    // Display combinations
    if (combinations.length > 0) {
        combinationsContainer.innerHTML = combinations.map(combo => `
            <div class="combination-card">
                <h4>Perfect Combo</h4>
                <div class="combination-items">
                    <div class="combination-item">
                        <strong>${combo.name1}</strong> - $${combo.price1}
                    </div>
                    <div class="combination-item">
                        <strong>${combo.name2}</strong> - $${combo.price2}
                    </div>
                    <div class="combination-item">
                        <strong>${combo.name3}</strong> - $${combo.price3}
                    </div>
                </div>
                <p class="compatibility-score">Compatibility Score: ${combo.compatibility_score}%</p>
                <p><strong>Total: $${(parseFloat(combo.price1) + parseFloat(combo.price2) + parseFloat(combo.price3)).toFixed(2)}</strong></p>
                <button class="btn btn-primary" onclick="addComboToCart([${combo.product_id_1}, ${combo.product_id_2}, ${combo.product_id_3}])">Add Combo to Cart</button>
            </div>
        `).join('');
    } else {
        combinationsContainer.innerHTML = '<p>No pre-made combinations available.</p>';
    }
    
    // Display individual recommendations
    if (recommendations.length > 0) {
        recommendationsContainer.innerHTML = recommendations.map(product => createProductCard(product)).join('');
    } else {
        recommendationsContainer.innerHTML = '<p>No matching products found.</p>';
    }
}

// Add combo to cart
async function addComboToCart(productIds) {
    for (const productId of productIds) {
        await addToCart(productId);
    }
    alert('Combo added to cart!');
}
