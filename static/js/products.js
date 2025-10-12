let currentCategory = '';
let currentSearch = '';

document.addEventListener('DOMContentLoaded', () => {
    loadCategoryFilter();
    loadProducts();
    
    // Get category from URL if present
    const urlParams = new URLSearchParams(window.location.search);
    const categoryParam = urlParams.get('category');
    if (categoryParam) {
        currentCategory = categoryParam;
        document.getElementById('category-filter').value = categoryParam;
    }
    
    // Search functionality
    document.getElementById('search-btn').addEventListener('click', searchProducts);
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchProducts();
    });
    
    // Category filter
    document.getElementById('category-filter').addEventListener('change', (e) => {
        currentCategory = e.target.value;
        loadProducts();
    });
});

// Load category filter dropdown
async function loadCategoryFilter() {
    try {
        const response = await fetch(`${API_URL}/categories`);
        const categories = await response.json();
        
        const categoryFilter = document.getElementById('category-filter');
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.category_id;
            option.textContent = category.category_name;
            categoryFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Search products
function searchProducts() {
    currentSearch = document.getElementById('search-input').value;
    loadProducts();
}

// Load products with filters
async function loadProducts() {
    const productsContainer = document.getElementById('products-container');
    
    try {
        let url = `${API_URL}/products?search=${currentSearch}`;
        if (currentCategory) {
            url += `&category_id=${currentCategory}`;
        }
        
        const response = await fetch(url);
        const products = await response.json();
        
        if (products.length === 0) {
            productsContainer.innerHTML = '<p style="text-align:center; padding:2rem;">No products found.</p>';
            return;
        }
        
        productsContainer.innerHTML = products.map(product => createProductCard(product)).join('');
    } catch (error) {
        console.error('Error loading products:', error);
        productsContainer.innerHTML = '<p style="text-align:center; padding:2rem;">Error loading products.</p>';
    }
}
