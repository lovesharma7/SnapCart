from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from config import Config
import re
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Database connection helper
def get_db_connection():
    connection = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )
    return connection

# Helper function to check if user is logged in
def is_logged_in():
    return 'user_id' in session

# ==================== HOME PAGE ====================
@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all categories
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    
    # Get featured products (latest 8 products)
    cursor.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        ORDER BY p.created_at DESC 
        LIMIT 8
    """)
    featured_products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('home.html', 
                         categories=categories, 
                         featured_products=featured_products,
                         is_logged_in=is_logged_in())

# ==================== PRODUCTS PAGE ====================
@app.route('/products')
def products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    search_query = request.args.get('search', '')
    
    # Build query
    query = """
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        WHERE 1=1
    """
    params = []
    
    if category_id:
        query += " AND p.category_id = %s"
        params.append(category_id)
    
    if search_query:
        query += " AND (p.name LIKE %s OR p.description LIKE %s)"
        search_param = f"%{search_query}%"
        params.extend([search_param, search_param])
    
    query += " ORDER BY p.created_at DESC"
    
    cursor.execute(query, params)
    products_list = cursor.fetchall()
    
    # Get all categories for filter
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('products.html', 
                         products=products_list, 
                         categories=categories,
                         selected_category=category_id,
                         search_query=search_query,
                         is_logged_in=is_logged_in())

# ==================== PRODUCT DETAIL PAGE ====================
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get product details
    cursor.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        WHERE p.id = %s
    """, (product_id,))
    product = cursor.fetchone()
    
    if not product:
        cursor.close()
        conn.close()
        return "Product not found", 404
    
    # Get related products (same category)
    cursor.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        WHERE p.category_id = %s AND p.id != %s 
        LIMIT 4
    """, (product['category_id'], product_id))
    related_products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('product_detail.html', 
                         product=product, 
                         related_products=related_products,
                         is_logged_in=is_logged_in())

# ==================== VIRTUAL BASKET PAGE ====================
@app.route('/virtual-basket')
def virtual_basket():
    return render_template('virtual_basket.html', is_logged_in=is_logged_in())

@app.route('/api/virtual-basket/parse', methods=['POST'])
def parse_virtual_basket():
    data = request.get_json()
    text_input = data.get('text', '').lower()
    
    if not text_input:
        return jsonify({'error': 'No input provided'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Define comprehensive patterns for ALL items in database
    # CRITICAL: Order from MOST SPECIFIC to LEAST SPECIFIC to prevent overlaps
    patterns = [
        {
            'key': 'laptop_bag',
            'pattern': r'(\d+)?\s*(laptop|computer)\s+(bags?|backpacks?)',
            'search_terms': ['Laptop', 'laptop'],
            'priority': 1
        },
        {
            'key': 'formal_shoes',
            'pattern': r'(\d+)?\s*(?:pairs?\s+of\s+)?(\w+)?\s*(formal\s*shoes?|loafers?)',
            'search_terms': ['Formal', 'formal', 'Loafer', 'loafer'],
            'priority': 2
        },
        {
            'key': 'usb_hub',
            'pattern': r'(\d+)?\s*(usb|usb-c|type-c)?\s*(hub|adapter)',
            'search_terms': ['USB', 'Hub', 'hub'],
            'priority': 3
        },
        {
            'key': 'bluetooth_speaker',
            'pattern': r'(\d+)?\s*(bluetooth|wireless)\s+speakers?',
            'search_terms': ['Bluetooth', 'Speaker', 'speaker'],
            'priority': 4
        },
        {
            'key': 'wireless_earbuds',
            'pattern': r'(\d+)?\s*(wireless|bluetooth)\s+(earbuds?|headphones?)',
            'search_terms': ['Wireless', 'Earbuds', 'earbuds', 'Bluetooth'],
            'priority': 5
        },
        {
            'key': 'smart_watch',
            'pattern': r'(\d+)?\s*smart\s*watches?',
            'search_terms': ['Smart', 'Watch', 'watch'],
            'priority': 6
        },
        {
            'key': 'leather_jacket',
            'pattern': r'(\d+)?\s*leather\s+jackets?',
            'search_terms': ['Leather', 'Jacket', 'jacket'],
            'priority': 7
        },
        {
            'key': 'denim_jacket',
            'pattern': r'(\d+)?\s*denim\s+jackets?',
            'search_terms': ['Denim', 'Jacket', 'jacket'],
            'priority': 8
        },
        {
            'key': 'leather_belt',
            'pattern': r'(\d+)?\s*leather\s+belts?',
            'search_terms': ['Leather', 'Belt', 'belt'],
            'priority': 9
        },
        {
            'key': 'shirt',
            'pattern': r'(\d+)?\s*(white|black|blue|red|grey|gray|navy|light\s*blue|dark\s*blue|green|yellow|orange|purple|pink)?\s*(shirts?|tshirts?|t-shirts?)',
            'search_terms': ['shirt', 'Shirt'],
            'priority': 10
        },
        {
            'key': 'pant',
            'pattern': r'(\d+)?\s*(black|blue|grey|gray|brown|khaki|white|navy|dark\s*blue|light\s*blue|beige)?\s*(pants?|trousers?|jeans?|chinos?)',
            'search_terms': ['pant', 'Pant', 'jean', 'Jean', 'trouser', 'Trouser', 'chino', 'Chino'],
            'priority': 11
        },
        {
            'key': 'sneaker',
            'pattern': r'(\d+)?\s*(?:pairs?\s+of\s+)?(\w+)?\s*(sneakers?)',
            'search_terms': ['sneaker', 'Sneaker', 'Canvas'],
            'priority': 12
        },
        {
            'key': 'shoes',
            'pattern': r'(\d+)?\s*(?:pairs?\s+of\s+)?(\w+)?\s*(shoes?)',
            'search_terms': ['shoe', 'Shoe'],
            'priority': 13
        },
        {
            'key': 'jacket',
            'pattern': r'(\d+)?\s*(black|blue|grey|gray|brown|red|green)?\s*(jackets?|blazers?)',
            'search_terms': ['jacket', 'Jacket', 'blazer', 'Blazer'],
            'priority': 14
        },
        {
            'key': 'belt',
            'pattern': r'(\d+)?\s*(black|brown|white|grey|gray)?\s*belts?',
            'search_terms': ['belt', 'Belt'],
            'priority': 15
        },
        {
            'key': 'bag',
            'pattern': r'(\d+)?\s*(black|brown|blue|grey|gray|leather|canvas|white)?\s*(bags?|backpacks?|handbags?)',
            'search_terms': ['bag', 'Bag', 'backpack', 'Backpack'],
            'priority': 16
        },
        {
            'key': 'watch',
            'pattern': r'(\d+)?\s*(silver|gold|black|brown|leather|metal)?\s*(watch|watches)',
            'search_terms': ['watch', 'Watch'],
            'priority': 17
        },
        {
            'key': 'sunglasses',
            'pattern': r'(\d+)?\s*(black|brown|blue|aviator|wayfarer)?\s*(sunglasses?|shades?)',
            'search_terms': ['sunglasses', 'Sunglasses'],
            'priority': 18
        },
        {
            'key': 'wallet',
            'pattern': r'(\d+)?\s*(black|brown|leather|grey|gray)?\s*wallets?',
            'search_terms': ['wallet', 'Wallet'],
            'priority': 19
        },
        {
            'key': 'earbuds',
            'pattern': r'(\d+)?\s*(black|white)?\s*(earbuds?|headphones?)',
            'search_terms': ['Earbuds', 'earbuds', 'headphone'],
            'priority': 20
        },
        {
            'key': 'speaker',
            'pattern': r'(\d+)?\s*(portable|black|blue)?\s*speakers?',
            'search_terms': ['Speaker', 'speaker'],
            'priority': 21
        }
    ]
    
    # Sort patterns by priority (most specific first)
    patterns.sort(key=lambda x: x['priority'])
    
    # Track matched positions to prevent overlaps
    matched_items = []
    matched_positions = []
    
    # Parse the input text for each pattern (in priority order)
    for pattern_config in patterns:
        pattern = pattern_config['pattern']
        matches = re.finditer(pattern, text_input, re.IGNORECASE)
        
        for match in matches:
            start_pos = match.start()
            end_pos = match.end()
            
            # Check if this position overlaps with any already matched position
            overlaps = False
            for matched_start, matched_end in matched_positions:
                if not (end_pos <= matched_start or start_pos >= matched_end):
                    overlaps = True
                    break
            
            if overlaps:
                continue
            
            # Record this match position
            matched_positions.append((start_pos, end_pos))
            
            # Extract quantity and color
            quantity_str = match.group(1)
            color = match.group(2) if len(match.groups()) > 1 else None
            
            # Clean up color
            if color:
                color = color.strip().lower().replace(' ', '')
                if color in ['gray', 'grey']:
                    color = 'grey'
                elif 'lightblue' in color or color == 'light':
                    color = 'blue'
                elif 'darkblue' in color or color == 'navy':
                    color = 'navy'
                elif color == 'beige':
                    color = 'brown'
                elif color in ['laptop', 'computer', 'formal', 'usb', 'bluetooth', 'wireless', 
                              'smart', 'leather', 'denim', 'portable']:
                    color = None
            
            quantity = int(quantity_str) if quantity_str else 1
            
            matched_items.append({
                'type': pattern_config['key'],
                'quantity': quantity,
                'color': color,
                'search_terms': pattern_config['search_terms'],
                'priority': pattern_config['priority']
            })
    
    # Additional cleanup: Remove exact duplicates by (type, color)
    unique_items = []
    seen = set()
    for item in matched_items:
        key = (item['type'], item.get('color'))
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    
    parsed_items = unique_items
    
    if not parsed_items:
        cursor.close()
        conn.close()
        return jsonify({
            'parsed_items': [],
            'suggestions': [],
            'combos': [],
            'message': 'Could not understand your input. Try: "1 white shirt, 1 black pant, 1 pair of sneakers, 1 backpack"'
        })
    
    # Fetch matching products from database for each parsed item
    suggestions = []
    all_matched_products = []
    
    for item in parsed_items:
        # Build query to find matching products
        query = "SELECT * FROM products WHERE ("
        params = []
        
        # Build OR conditions for search terms
        search_conditions = []
        for term in item['search_terms']:
            search_conditions.append("name LIKE %s")
            params.append(f"%{term}%")
        
        query += " OR ".join(search_conditions)
        query += ")"
        
        # Match by color if specified
        if item['color']:
            query += " AND LOWER(REPLACE(color, ' ', '')) = %s"
            params.append(item['color'])
        
        # Only in-stock items
        query += " AND stock > 0"
        
        # Order by price (ascending)
        query += " ORDER BY price ASC LIMIT 8"
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        if products:
            suggestions.append({
                'item': item,
                'products': products
            })
            all_matched_products.append({
                'item': item,
                'product': products[0]
            })
    
    # Generate combo suggestions if we have matches for all items
    combos = []
    
    if len(all_matched_products) == len(parsed_items) and len(parsed_items) > 0:
        # Count how many items have multiple product options
        items_with_multiple_options = sum(1 for s in suggestions if len(s['products']) > 1)
        items_with_3plus_options = sum(1 for s in suggestions if len(s['products']) >= 3)
        items_with_4plus_options = sum(1 for s in suggestions if len(s['products']) >= 4)
        
        # COMBO 1: Budget Combo (cheapest options) - ALWAYS CREATE
        combo_items = []
        total_price = 0
        combo_description = "Perfect match! "
        
        for matched in all_matched_products:
            product = matched['product']
            item = matched['item']
            combo_items.append(product)
            total_price += float(product['price']) * item['quantity']
            
            color_name = product['color'].title() if product['color'] else ""
            combo_description += f"{color_name} {product['name']}, "
        
        combo_description = combo_description.rstrip(', ') + " - Great combination!"
        
        combos.append({
            'name': f'💰 Budget Combo ({len(combo_items)} items)',
            'items': combo_items,
            'total_price': total_price,
            'description': combo_description,
            'item_count': len(combo_items),
            'badge': 'Best Value'
        })
        
        # COMBO 2: Alternative Combo - Create if AT LEAST ONE item has 2+ options
        if items_with_multiple_options >= 1:
            alt_combo_items = []
            alt_total_price = 0
            
            for suggestion in suggestions:
                if len(suggestion['products']) > 1:
                    product = suggestion['products'][1]
                else:
                    product = suggestion['products'][0]
                
                alt_combo_items.append(product)
                alt_total_price += float(product['price']) * suggestion['item']['quantity']
            
            if alt_total_price != total_price:
                combos.append({
                    'name': f'⭐ Alternative Combo ({len(alt_combo_items)} items)',
                    'items': alt_combo_items,
                    'total_price': alt_total_price,
                    'description': 'Another great option with different items where available',
                    'item_count': len(alt_combo_items),
                    'badge': 'Popular Choice'
                })
        
        # COMBO 3: Premium Combo - Create if AT LEAST ONE item has 3+ options
        if items_with_3plus_options >= 1:
            premium_combo_items = []
            premium_total_price = 0
            
            for suggestion in suggestions:
                if len(suggestion['products']) >= 3:
                    product = suggestion['products'][2]
                elif len(suggestion['products']) >= 2:
                    product = suggestion['products'][1]
                else:
                    product = suggestion['products'][0]
                
                premium_combo_items.append(product)
                premium_total_price += float(product['price']) * suggestion['item']['quantity']
            
            existing_prices = [c['total_price'] for c in combos]
            if premium_total_price not in existing_prices:
                combos.append({
                    'name': f'👑 Premium Combo ({len(premium_combo_items)} items)',
                    'items': premium_combo_items,
                    'total_price': premium_total_price,
                    'description': 'Higher-end options for a premium look',
                    'item_count': len(premium_combo_items),
                    'badge': 'Premium'
                })
        
        # COMBO 4: Variety Combo - Create if AT LEAST ONE item has 4+ options
        if items_with_4plus_options >= 1:
            variety_combo_items = []
            variety_total_price = 0
            
            for i, suggestion in enumerate(suggestions):
                num_products = len(suggestion['products'])
                if num_products >= 4:
                    idx = (i % 4)
                    product = suggestion['products'][idx]
                elif num_products >= 3:
                    idx = (i % 3)
                    product = suggestion['products'][idx]
                elif num_products >= 2:
                    idx = (i % 2)
                    product = suggestion['products'][idx]
                else:
                    product = suggestion['products'][0]
                
                variety_combo_items.append(product)
                variety_total_price += float(product['price']) * suggestion['item']['quantity']
            
            existing_prices = [c['total_price'] for c in combos]
            if variety_total_price not in existing_prices:
                combos.append({
                    'name': f'🎨 Variety Combo ({len(variety_combo_items)} items)',
                    'items': variety_combo_items,
                    'total_price': variety_total_price,
                    'description': 'Balanced mix rotating through available options',
                    'item_count': len(variety_combo_items),
                    'badge': 'Balanced'
                })
        
        # COMBO 5: Mid-Range Combo - Create if we have 2+ combos and items with options
        if len(combos) >= 2 and items_with_multiple_options >= 1:
            mid_combo_items = []
            mid_total_price = 0
            
            for suggestion in suggestions:
                num_products = len(suggestion['products'])
                if num_products >= 5:
                    product = suggestion['products'][2]
                elif num_products >= 3:
                    product = suggestion['products'][1]
                elif num_products >= 2:
                    product = suggestion['products'][1]
                else:
                    product = suggestion['products'][0]
                
                mid_combo_items.append(product)
                mid_total_price += float(product['price']) * suggestion['item']['quantity']
            
            existing_prices = [c['total_price'] for c in combos]
            if mid_total_price not in existing_prices:
                combos.append({
                    'name': f'💎 Mid-Range Combo ({len(mid_combo_items)} items)',
                    'items': mid_combo_items,
                    'total_price': mid_total_price,
                    'description': 'Balanced combination of mid-priced options',
                    'item_count': len(mid_combo_items),
                    'badge': 'Balanced'
                })
    
    # Sort combos by price (ascending)
    combos.sort(key=lambda x: x['total_price'])
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'parsed_items': parsed_items,
        'suggestions': suggestions,
        'combos': combos,
        'total_items_requested': len(parsed_items),
        'total_items_found': len(all_matched_products)
    })

# ==================== CART PAGE ====================
@app.route('/cart')
def cart():
    if not is_logged_in():
        flash('Please login to view your cart', 'warning')
        return redirect(url_for('auth'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT c.*, p.name, p.price, p.image_url, p.stock,
               (c.quantity * p.price) as subtotal
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (session['user_id'],))
    cart_items = cursor.fetchall()
    
    total = sum(float(item['subtotal']) for item in cart_items)
    
    cursor.close()
    conn.close()
    
    return render_template('cart.html', 
                         cart_items=cart_items, 
                         total=total,
                         is_logged_in=is_logged_in())

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    if not is_logged_in():
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    
    if product['stock'] < quantity:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Insufficient stock'}), 400
    
    cursor.execute("""
        SELECT * FROM cart 
        WHERE user_id = %s AND product_id = %s
    """, (session['user_id'], product_id))
    existing_item = cursor.fetchone()
    
    if existing_item:
        new_quantity = existing_item['quantity'] + quantity
        cursor.execute("""
            UPDATE cart 
            SET quantity = %s 
            WHERE user_id = %s AND product_id = %s
        """, (new_quantity, session['user_id'], product_id))
    else:
        cursor.execute("""
            INSERT INTO cart (user_id, product_id, quantity) 
            VALUES (%s, %s, %s)
        """, (session['user_id'], product_id, quantity))
    
    conn.commit()
    
    cursor.execute("SELECT SUM(quantity) as count FROM cart WHERE user_id = %s", (session['user_id'],))
    result = cursor.fetchone()
    cart_count = result['count'] if result['count'] else 0
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'success': True, 
        'message': 'Added to cart',
        'cart_count': cart_count
    })

@app.route('/api/cart/update', methods=['POST'])
def update_cart():
    if not is_logged_in():
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id or quantity < 1:
        return jsonify({'error': 'Invalid data'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        UPDATE cart 
        SET quantity = %s 
        WHERE user_id = %s AND product_id = %s
    """, (quantity, session['user_id'], product_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    if not is_logged_in():
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        DELETE FROM cart 
        WHERE user_id = %s AND product_id = %s
    """, (session['user_id'], product_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/cart/count')
def cart_count():
    if not is_logged_in():
        return jsonify({'count': 0})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT SUM(quantity) as count FROM cart WHERE user_id = %s", (session['user_id'],))
    result = cursor.fetchone()
    count = result['count'] if result['count'] else 0
    
    cursor.close()
    conn.close()
    
    return jsonify({'count': count})

# ==================== AUTHENTICATION ====================
@app.route('/auth')
def auth():
    if is_logged_in():
        return redirect(url_for('home'))
    return render_template('auth.html', is_logged_in=False)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'All fields required'}), 400
    
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 400
    
    hashed_password = generate_password_hash(password)
    cursor.execute("""
        INSERT INTO users (username, email, password) 
        VALUES (%s, %s, %s)
    """, (username, email, hashed_password))
    
    conn.commit()
    user_id = cursor.lastrowid
    
    cursor.close()
    conn.close()
    
    session['user_id'] = user_id
    session['username'] = username
    
    return jsonify({'success': True, 'message': 'Registration successful'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'All fields required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, username))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    session['user_id'] = user['id']
    session['username'] = user['username']
    
    return jsonify({'success': True, 'message': 'Login successful'})

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

# ==================== RUN APPLICATION ====================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
