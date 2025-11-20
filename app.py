from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from config import Config
import re
from datetime import datetime
import json

import re
from collections import defaultdict

# --- Normalization helpers ---
def normalize_text(s):
    if not s:
        return ""
    s = s.lower()
    # remove punctuation except spaces
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# synonyms for product types -> normalized type key
TYPE_SYNONYMS = {
    'jacket': ['jacket', 'leather jacket', 'denim jacket', 'blazer'],
    'shirt': ['shirt', 'tshirt', 'tee', 'white shirt', 'formal shirt', 'casual shirt'],
    'pant': ['pant','pants','jeans','trouser','trousers','chinos'],
    'shoe': ['shoe','shoes','sneakers','formal shoes','canvas shoes','loafers','running shoes'],
    'belt': ['belt'],
    'accessory': ['wallet','watch','sunglasses','backpack','bag','belt'],
    'electronics': ['earbuds','smart watch','speaker','laptop bag','usb','headphones'],
}

# invert synonyms for quick lookup (word -> canonical type)
TYPE_MAP = {}
for canon, words in TYPE_SYNONYMS.items():
    for w in words:
        TYPE_MAP[normalize_text(w)] = canon

# colors mapping / fuzzy groups
COLOR_MAP = {
    'black': ['black', 'jet black', 'charcoal', 'ebony'],
    'white': ['white', 'off white', 'ivory', 'cream'],
    'blue': ['blue', 'navy', 'royal blue', 'azure', 'sky'],
    'brown': ['brown','tan','camel'],
    'grey': ['grey','gray','slate'],
    'silver': ['silver','steel'],
    'red': ['red','maroon','burgundy'],
    'green': ['green','olive'],
}

# invert color map
COLOR_KEY = {}
for k,v in COLOR_MAP.items():
    for w in v:
        COLOR_KEY[normalize_text(w)] = k

def canonical_type_from_phrase(phrase):
    # try to match canonical type using substring matching
    phrase = normalize_text(phrase)
    # check multi-word synonyms first
    for key in sorted(TYPE_MAP.keys(), key=lambda x: -len(x)):
        if key in phrase:
            return TYPE_MAP[key]
    # fallback: check tokens
    for token in phrase.split():
        if token in TYPE_MAP:
            return TYPE_MAP[token]
    return None

def canonical_color_from_phrase(phrase):
    phrase = normalize_text(phrase)
    for key in sorted(COLOR_KEY.keys(), key=lambda x: -len(x)):
        if key in phrase:
            return COLOR_KEY[key]
    for token in phrase.split():
        if token in COLOR_KEY:
            return COLOR_KEY[token]
    return None

# match product record to a requested item (phrase)
def score_product_against_request(product, req_type, req_color):
    # product is dict-like with fields: id, name, category_name or category_id, color, stock
    score = 0
    name = normalize_text(product.get('name') or '')
    color = normalize_text(product.get('color') or '')
    category = normalize_text(product.get('category_name') or str(product.get('category_id') or ''))

    # Type match: check product name or category for canonical type
    prod_type = None
    # try to infer product type from name using our TYPE_MAP
    for key in TYPE_MAP:
        if key in name:
            prod_type = TYPE_MAP[key]
            break
    # also check category name
    for key in TYPE_MAP:
        if key in category:
            prod_type = TYPE_MAP[key]
            break

    if prod_type == req_type:
        score += 3
    # allow partial matches: e.g. 'jeans' matched as pant
    else:
        # check if request type word appears in product name
        if req_type and req_type in name:
            score += 2

    # Color match
    if req_color:
        if req_color == color:
            score += 2
        else:
            # try fuzzy via COLOR_KEY mapping in name & color
            prod_color_canon = COLOR_KEY.get(color)
            if prod_color_canon == req_color:
                score += 2
            else:
                # check name for color words
                for cword, canon in COLOR_KEY.items():
                    if cword in name and canon == req_color:
                        score += 1

    # prefer in-stock
    try:
        if int(product.get('stock', 0)) > 0:
            score += 1
    except:
        pass

    return score

def find_best_products_for_requests(db_conn, requested_phrases, products_cache=None):
    """
    requested_phrases: list of strings like "1 white shirt", "1 black pant"
    returns: list of matched product dicts (best per request)
    """

    # Parse each phrase into (req_type, req_color)
    requests = []
    for phrase in requested_phrases:
        norm = normalize_text(phrase)
        color = canonical_color_from_phrase(norm)
        rtype = canonical_type_from_phrase(norm)
        # if no explicit type but phrase contains 'shirt' in plural etc, try tokens
        if not rtype:
            for token in norm.split():
                if token in TYPE_MAP:
                    rtype = TYPE_MAP[token]
                    break
        requests.append({'phrase': phrase, 'type': rtype, 'color': color})

    # Load products once (if not provided)
    products = []
    if products_cache:
        products = products_cache
    else:
        cur = db_conn.cursor(dictionary=True)
        cur.execute("SELECT p.id, p.name, p.description, p.price, p.category_id, c.name as category_name, p.image_url, p.stock, p.color FROM products p LEFT JOIN categories c ON p.category_id = c.id")
        products = cur.fetchall()
        cur.close()

    # For each request, pick best-scoring product
    results = []
    used_product_ids = set()
    for req in requests:
        best = None
        best_score = -999
        for prod in products:
            # skip product if already used for another requested item (optional)
            # We may still allow reuse if you want variants; keep skipping to avoid duplicates
            if prod['id'] in used_product_ids:
                continue
            s = score_product_against_request(prod, req.get('type'), req.get('color'))
            if s > best_score:
                best_score = s
                best = prod
        # Only accept if we at least matched the type (score threshold)
        if best and best_score >= 3:
            results.append({'request': req, 'product': best, 'score': best_score})
            used_product_ids.add(best['id'])
        else:
            # fallback: if no strong match, try permissive match (type or color)
            # choose highest score even if <3, but prefer type
            permissive_best = None
            permissive_score = -999
            for prod in products:
                if prod['id'] in used_product_ids:
                    continue
                s = score_product_against_request(prod, req.get('type'), req.get('color'))
                if s > permissive_score:
                    permissive_score = s
                    permissive_best = prod
            if permissive_best and permissive_score >= 1:
                results.append({'request': req, 'product': permissive_best, 'score': permissive_score})
                used_product_ids.add(permissive_best['id'])
            else:
                # no match found; append None so UI can show missing item
                results.append({'request': req, 'product': None, 'score': 0})

    return results


app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------
# Register wishlist blueprint
# ---------------------------
# If your blueprint file is named `wishlist.py` (as you showed), use this:
from wishlist import wishlist_bp
# If your blueprint file is named wishlist_module.py, use:
# from wishlist_module import wishlist_bp

app.register_blueprint(wishlist_bp)
# ---------------------------

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

# Helper: get wishlist product ids for a user (list of ints)
def get_user_wishlist_ids(user_id):
    if not user_id:
        return []
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT product_id FROM wishlist WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall() or []
        ids = [int(r['product_id']) for r in rows]
    except Exception:
        ids = []
    finally:
        cursor.close()
        conn.close()
    return ids

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

    wishlist_ids = []
    if is_logged_in():
        wishlist_ids = get_user_wishlist_ids(session.get('user_id'))
    
    return render_template('home.html', 
                         categories=categories, 
                         featured_products=featured_products,
                         is_logged_in=is_logged_in(),
                         wishlist_ids=wishlist_ids)

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

    wishlist_ids = []
    if is_logged_in():
        wishlist_ids = get_user_wishlist_ids(session.get('user_id'))
    
    return render_template('products.html', 
                         products=products_list, 
                         categories=categories,
                         selected_category=category_id,
                         search_query=search_query,
                         is_logged_in=is_logged_in(),
                         wishlist_ids=wishlist_ids)

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

    wishlist_ids = []
    if is_logged_in():
        wishlist_ids = get_user_wishlist_ids(session.get('user_id'))
    
    return render_template('product_detail.html', 
                         product=product, 
                         related_products=related_products,
                         is_logged_in=is_logged_in(),
                         wishlist_ids=wishlist_ids)

# ==================== VIRTUAL BASKET PAGE ====================
@app.route('/virtual-basket')
def virtual_basket():
    wishlist_ids = []
    if is_logged_in():
        wishlist_ids = get_user_wishlist_ids(session.get('user_id'))
    return render_template('virtual_basket.html', is_logged_in=is_logged_in(), wishlist_ids=wishlist_ids)

@app.route('/api/virtual-basket/parse', methods=['POST'])
def parse_virtual_basket():
    data = request.get_json() or {}
    text_input = (data.get('text') or '').lower()
    
    if not text_input:
        return jsonify({'error': 'No input provided'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Define comprehensive patterns for ALL items in database
    patterns = [
        { 'key': 'laptop_bag', 'pattern': r'(\d+)?\s*(laptop|computer)\s+(bags?|backpacks?)',
          'search_terms': ['Laptop', 'laptop'], 'priority': 1 },
        { 'key': 'formal_shoes', 'pattern': r'(\d+)?\s*(?:pairs?\s+of\s+)?(\w+)?\s*(formal\s*shoes?|loafers?)',
          'search_terms': ['Formal', 'formal', 'Loafer', 'loafer'], 'priority': 2 },
        { 'key': 'usb_hub', 'pattern': r'(\d+)?\s*(usb|usb-c|type-c)?\s*(hub|adapter)',
          'search_terms': ['USB', 'Hub', 'hub'], 'priority': 3 },
        { 'key': 'bluetooth_speaker', 'pattern': r'(\d+)?\s*(bluetooth|wireless)\s+speakers?',
          'search_terms': ['Bluetooth', 'Speaker', 'speaker'], 'priority': 4 },
        { 'key': 'wireless_earbuds', 'pattern': r'(\d+)?\s*(wireless|bluetooth)\s+(earbuds?|headphones?)',
          'search_terms': ['Wireless', 'Earbuds', 'earbuds', 'Bluetooth'], 'priority': 5 },
        { 'key': 'smart_watch', 'pattern': r'(\d+)?\s*smart\s*watches?',
          'search_terms': ['Smart', 'Watch', 'watch'], 'priority': 6 },
        { 'key': 'leather_jacket', 'pattern': r'(\d+)?\s*leather\s+jackets?',
          'search_terms': ['Leather', 'Jacket', 'jacket'], 'priority': 7 },
        { 'key': 'denim_jacket', 'pattern': r'(\d+)?\s*denim\s+jackets?',
          'search_terms': ['Denim', 'Jacket', 'jacket'], 'priority': 8 },
        { 'key': 'leather_belt', 'pattern': r'(\d+)?\s*leather\s+belts?',
          'search_terms': ['Leather', 'Belt', 'belt'], 'priority': 9 },
        { 'key': 'shirt', 'pattern': r'(\d+)?\s*(white|black|blue|red|grey|gray|navy|light\s*blue|dark\s*blue|green|yellow|orange|purple|pink)?\s*(shirts?|tshirts?|t-shirts?)',
          'search_terms': ['shirt', 'Shirt'], 'priority': 10 },
        { 'key': 'pant', 'pattern': r'(\d+)?\s*(black|blue|grey|gray|brown|khaki|white|navy|dark\s*blue|light\s*blue|beige)?\s*(pants?|trousers?|jeans?|chinos?)',
          'search_terms': ['pant', 'Pant', 'jean', 'Jean', 'trouser', 'Trouser', 'chino', 'Chino'], 'priority': 11 },
        { 'key': 'sneaker', 'pattern': r'(\d+)?\s*(?:pairs?\s+of\s+)?(\w+)?\s*(sneakers?)',
          'search_terms': ['sneaker', 'Sneaker', 'Canvas'], 'priority': 12 },
        { 'key': 'shoes', 'pattern': r'(\d+)?\s*(?:pairs?\s+of\s+)?(\w+)?\s*(shoes?)',
          'search_terms': ['shoe', 'Shoe'], 'priority': 13 },
        { 'key': 'jacket', 'pattern': r'(\d+)?\s*(black|blue|grey|gray|brown|red|green)?\s*(jackets?|blazers?)',
          'search_terms': ['jacket', 'Jacket', 'blazer', 'Blazer'], 'priority': 14 },
        { 'key': 'belt', 'pattern': r'(\d+)?\s*(black|brown|white|grey|gray)?\s*belts?',
          'search_terms': ['belt', 'Belt'], 'priority': 15 },
        { 'key': 'bag', 'pattern': r'(\d+)?\s*(black|brown|blue|grey|gray|leather|canvas|white)?\s*(bags?|backpacks?|handbags?)',
          'search_terms': ['bag', 'Bag', 'backpack', 'Backpack'], 'priority': 16 },
        { 'key': 'watch', 'pattern': r'(\d+)?\s*(silver|gold|black|brown|leather|metal)?\s*(watch|watches)',
          'search_terms': ['watch', 'Watch'], 'priority': 17 },
        { 'key': 'sunglasses', 'pattern': r'(\d+)?\s*(black|brown|blue|aviator|wayfarer)?\s*(sunglasses?|shades?)',
          'search_terms': ['sunglasses', 'Sunglasses'], 'priority': 18 },
        { 'key': 'wallet', 'pattern': r'(\d+)?\s*(black|brown|leather|grey|gray)?\s*wallets?',
          'search_terms': ['wallet', 'Wallet'], 'priority': 19 },
        { 'key': 'earbuds', 'pattern': r'(\d+)?\s*(black|white)?\s*(earbuds?|headphones?)',
          'search_terms': ['Earbuds', 'earbuds', 'headphone'], 'priority': 20 },
        { 'key': 'speaker', 'pattern': r'(\d+)?\s*(portable|black|blue)?\s*speakers?',
          'search_terms': ['Speaker', 'speaker'], 'priority': 21 }
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
            quantity_str = None
            color = None
            try:
                quantity_str = match.group(1)
                color = match.group(2) if len(match.groups()) >= 2 else None
            except IndexError:
                quantity_str = None
                color = None
            
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
            
            quantity = int(quantity_str) if quantity_str and quantity_str.isdigit() else 1
            
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
            
            color_name = product.get('color', '') or ""
            combo_description += f"{color_name.title()} {product['name']}, "
        
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
    
    total = sum(float(item['subtotal']) for item in cart_items) if cart_items else 0.0
    
    cursor.close()
    conn.close()
    
    return render_template('cart.html', 
                         cart_items=cart_items, 
                         total=total,
                         is_logged_in=is_logged_in())

@app.route('/api/cart/add', methods=['POST'])
@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    # 1. Check Login
    if not session.get('user_id'):  # Changed to check session directly for safety
        return jsonify({'error': 'Please login first', 'redirect': url_for('login')}), 401
    
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 2. Get Product Details
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # 3. Check what is ALREADY in the cart for this user
        cursor.execute("""
            SELECT * FROM cart 
            WHERE user_id = %s AND product_id = %s
        """, (session['user_id'], product_id))
        existing_item = cursor.fetchone()

        # Calculate total requested quantity (Existing + New)
        current_cart_qty = existing_item['quantity'] if existing_item else 0
        total_quantity = current_cart_qty + quantity

        # 4. Validate Stock (Total vs Stock)
        if total_quantity > product['stock']:
            return jsonify({
                'error': f'Insufficient stock. You already have {current_cart_qty} in cart. Only {product["stock"]} available.'
            }), 400
        
        # 5. Update or Insert
        if existing_item:
            cursor.execute("""
                UPDATE cart 
                SET quantity = %s 
                WHERE user_id = %s AND product_id = %s
            """, (total_quantity, session['user_id'], product_id))
        else:
            cursor.execute("""
                INSERT INTO cart (user_id, product_id, quantity) 
                VALUES (%s, %s, %s)
            """, (session['user_id'], product_id, quantity))
        
        conn.commit()
        
        # 6. Get updated total cart count for the navbar badge
        cursor.execute("SELECT SUM(quantity) as count FROM cart WHERE user_id = %s", (session['user_id'],))
        result = cursor.fetchone()
        cart_count = result['count'] if result and result['count'] else 0
        
        return jsonify({
            'success': True, 
            'message': 'Added to cart',
            'cart_count': cart_count
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred'}), 500
        
    finally:
        cursor.close()
        conn.close()

@app.route('/api/cart/update', methods=['POST'])
@app.route('/api/cart/update', methods=['POST'])
def update_cart():
    if not is_logged_in():
        return jsonify({'error': 'Please login first'}), 401

    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    if not product_id or quantity < 1:
        return jsonify({'error': 'Invalid data'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Update quantity
    cursor.execute("""
        UPDATE cart 
        SET quantity = %s 
        WHERE user_id = %s AND product_id = %s
    """, (quantity, session['user_id'], product_id))
    conn.commit()

    # Recalculate totals
    cursor.execute("""
        SELECT SUM(c.quantity * p.price) AS subtotal,
               SUM(c.quantity) AS count
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (session['user_id'],))
    totals = cursor.fetchone() or {}

    subtotal = float(totals.get('subtotal') or 0)
    shipping = 0
    total = subtotal + shipping
    count = totals.get('count') or 0

    cursor.close()
    conn.close()

    return jsonify({
        'success': True,
        'totals': {
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total
        },
        'cart_count': count
    })

@app.route('/api/cart/remove', methods=['POST'])
@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    if not is_logged_in():
        return jsonify({'error': 'Please login first'}), 401

    data = request.get_json() or {}
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Remove item
    cursor.execute("""
        DELETE FROM cart 
        WHERE user_id = %s AND product_id = %s
    """, (session['user_id'], product_id))
    conn.commit()

    # Recalculate totals
    cursor.execute("""
        SELECT SUM(c.quantity * p.price) AS subtotal,
               SUM(c.quantity) AS count
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (session['user_id'],))
    totals = cursor.fetchone() or {}

    subtotal = float(totals.get('subtotal') or 0)
    shipping = 0
    total = subtotal + shipping
    count = totals.get('count') or 0

    cursor.close()
    conn.close()

    return jsonify({
        'success': True,
        'totals': {
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total
        },
        'cart_count': count
    })


@app.route('/api/cart/count')
def cart_count():
    if not is_logged_in():
        return jsonify({'count': 0})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT SUM(quantity) as count FROM cart WHERE user_id = %s", (session['user_id'],))
    result = cursor.fetchone()
    count = result['count'] if result and result['count'] else 0
    
    cursor.close()
    conn.close()
    
    return jsonify({'count': count})

# ==================== WISHLIST STATUS API (ADDED) ====================
@app.route('/api/wishlist/status/<int:product_id>')
def wishlist_status(product_id):
    """
    Returns JSON { in_wishlist: true/false }
    This endpoint helps the frontend show "Added to wishlist" state without reloading.
    """
    if not is_logged_in():
        return jsonify({'in_wishlist': False})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT 1 FROM wishlist WHERE user_id = %s AND product_id = %s LIMIT 1", (session['user_id'], product_id))
    found = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'in_wishlist': bool(found)})

# ==================== AUTHENTICATION ====================
@app.route('/auth')
def auth():
    if is_logged_in():
        return redirect(url_for('home'))
    return render_template('auth.html', is_logged_in=False)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
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
    data = request.get_json() or {}
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

# ==================== CHECKOUT & PAYMENTS (MOCK GATEWAY) ====================
def _fetch_cart_items(user_id, cursor):
    cursor.execute("""
        SELECT c.product_id, c.quantity, p.name, p.price, p.stock, p.image_url
        FROM cart c
        JOIN products p ON p.id = c.product_id
        WHERE c.user_id = %s
    """, (user_id,))
    return cursor.fetchall()

def _compute_cart_total(cart_items):
    return sum(float(it['price']) * int(it['quantity']) for it in cart_items)

@app.route('/checkout', methods=['GET'])
def checkout():
    if not is_logged_in():
        flash('Please login to checkout', 'warning')
        return redirect(url_for('auth'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cart_items = _fetch_cart_items(session['user_id'], cursor)
    total = _compute_cart_total(cart_items) if cart_items else 0.0

    cursor.close()
    conn.close()

    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('products'))

    return render_template('checkout.html',
                           cart_items=cart_items,
                           total=total,
                           is_logged_in=True)

@app.route('/checkout/create-order', methods=['POST'])
def create_order():
    if not is_logged_in():
        return redirect(url_for('auth'))

    full_name = request.form.get('full_name', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    pincode = request.form.get('pincode', '').strip()
    phone = request.form.get('phone', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cart_items = _fetch_cart_items(session['user_id'], cursor)
    if not cart_items:
        cursor.close()
        conn.close()
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart'))

    # Validate stock
    for it in cart_items:
        if it['stock'] < it['quantity']:
            cursor.close()
            conn.close()
            flash(f"Insufficient stock for {it['name']}", 'error')
            return redirect(url_for('cart'))

    total = _compute_cart_total(cart_items)

    # Create order
    cursor.execute("""
        INSERT INTO orders (user_id, total_amount, status, created_at, payment_status)
        VALUES (%s, %s, %s, %s, %s)
    """, (session['user_id'], total, 'created', datetime.now(), 'unpaid'))
    order_id = cursor.lastrowid

    # Create order_items table if you don't have it, or skip this block in production
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    """)
    for it in cart_items:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, it['product_id'], it['quantity'], it['price']))

    conn.commit()
    cursor.close()
    conn.close()

    # Redirect to payment creation (start_payment accepts GET/POST)
    return redirect(url_for('start_payment', order_id=order_id))

@app.route('/payment/create', methods=['GET', 'POST'])
def start_payment():
    if not is_logged_in():
        return redirect(url_for('auth'))

    # Accept order_id from POST form or GET query param
    order_id = None
    if request.method == 'POST':
        order_id = request.form.get('order_id', type=int)
    else:
        order_id = request.args.get('order_id', type=int)

    if not order_id:
        flash('Invalid order', 'error')
        return redirect(url_for('checkout'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch order and validate ownership
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()

    if not order or order['user_id'] != session['user_id']:
        cursor.close()
        conn.close()
        flash('Order not found', 'error')
        return redirect(url_for('checkout'))

    if order.get('payment_status') == 'paid':
        cursor.close()
        conn.close()
        flash('Order already paid', 'info')
        return redirect(url_for('payment_return') + f"?payment_id={order.get('payment_id', 0)}")

    amount = float(order['total_amount'])

    # Create payment
    cursor.execute("""
        INSERT INTO payments (order_id, amount, currency, status)
        VALUES (%s, %s, %s, %s)
    """, (order_id, amount, 'INR', 'created'))
    payment_id = cursor.lastrowid

    # Link order to latest payment
    cursor.execute("UPDATE orders SET payment_id=%s WHERE id=%s", (payment_id, order_id))

    # Optional: log event
    try:
        cursor.execute("""
            INSERT INTO payment_events (payment_id, event_type, payload_json)
            VALUES (%s, %s, %s)
        """, (payment_id, 'payment.created', json.dumps({'order_id': order_id, 'amount': amount})))
    except Exception:
        pass

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('mock_gateway', payment_id=payment_id))

@app.route('/mock-gateway/<int:payment_id>', methods=['GET'])
def mock_gateway(payment_id):
    # Show hosted payment page with amount and merchant branding
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM payments WHERE id=%s", (payment_id,))
    payment = cursor.fetchone()
    if not payment:
        cursor.close()
        conn.close()
        return "Payment not found", 404

    cursor.execute("SELECT * FROM orders WHERE id=%s", (payment['order_id'],))
    order = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('mock_gateway.html',
                           payment=payment,
                           order=order,
                           is_logged_in=is_logged_in())

@app.route('/mock-gateway/process', methods=['POST'])
def mock_gateway_process():
    payment_id = request.form.get('payment_id', type=int)
    method = request.form.get('method', 'card')
    outcome = request.form.get('outcome', 'success')  # success|failed|pending

    # ---- SERVER-SIDE VALIDATION (IMPORTANT) ----
    if not payment_id:
        flash('Invalid payment reference', 'error')
        return redirect(url_for('checkout'))

    errors = []

    if method == 'card':
        card_number = (request.form.get('card_number') or '').strip()
        expiry = (request.form.get('expiry') or '').strip()
        cvv = (request.form.get('cvv') or '').strip()

        if not card_number or not expiry or not cvv:
            errors.append('Please fill all card details (Card Number, Expiry, CVV).')

    elif method == 'upi':
        upi_id = (request.form.get('upi_id') or '').strip()
        if not upi_id:
            errors.append('Please enter your UPI ID.')

    elif method == 'netbanking':
        bank = (request.form.get('bank') or '').strip()
        if not bank:
            errors.append('Please select a bank for Netbanking.')
    else:
        errors.append('Invalid payment method.')

    if errors:
        for msg in errors:
            flash(msg, 'error')
        # Go back to the mock gateway page instead of processing
        return redirect(url_for('mock_gateway', payment_id=payment_id))
    # ---- END VALIDATION ----

    provider_txn_id = f"MOCK-{payment_id}-{int(datetime.now().timestamp())}"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM payments WHERE id=%s", (payment_id,))
    payment = cursor.fetchone()
    if not payment:
        cursor.close()
        conn.close()
        flash('Payment not found', 'error')
        return redirect(url_for('checkout'))

    # Move to processing
    cursor.execute("""
        UPDATE payments SET status=%s, method=%s, provider_txn_id=%s WHERE id=%s
    """, ('processing', method, provider_txn_id, payment_id))

    # Optional event
    try:
        cursor.execute("""
            INSERT INTO payment_events (payment_id, event_type, payload_json)
            VALUES (%s, %s, %s)
        """, (payment_id, 'payment.processing', json.dumps({'outcome_selected': outcome})))
    except Exception:
        pass

    conn.commit()
    cursor.close()
    conn.close()

    # Simulate webhook (server-to-server)
    payload = {
        'payment_id': payment_id,
        'status': outcome,
        'provider_txn_id': provider_txn_id,
        'signature': 'demo-signature'
    }
    with app.test_client() as c:
        c.post('/mock-gateway/webhook', json=payload)

    return redirect(url_for('payment_return') + f"?payment_id={payment_id}")

@app.route('/mock-gateway/webhook', methods=['POST'])
def mock_gateway_webhook():
    data = request.get_json() or {}
    payment_id = data.get('payment_id')
    status = data.get('status')
    provider_txn_id = data.get('provider_txn_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM payments WHERE id=%s", (payment_id,))
    payment = cursor.fetchone()
    if not payment:
        cursor.close()
        conn.close()
        return jsonify({'ok': False, 'error': 'payment not found'}), 404

    # Fetch order
    cursor.execute("SELECT * FROM orders WHERE id=%s", (payment['order_id'],))
    order = cursor.fetchone()
    if not order:
        cursor.close()
        conn.close()
        return jsonify({'ok': False, 'error': 'order not found'}), 404

    if status == 'success':
        cursor.execute("UPDATE payments SET status=%s WHERE id=%s", ('success', payment_id))
        cursor.execute("UPDATE orders SET payment_status='paid', status='confirmed' WHERE id=%s", (order['id'],))

        # Reduce stock now if order_items exist
        cursor.execute("""
            SELECT product_id, quantity FROM order_items WHERE order_id=%s
        """, (order['id'],))
        items = cursor.fetchall() or []
        for it in items:
            cursor.execute("""
                UPDATE products SET stock = GREATEST(stock - %s, 0) WHERE id=%s
            """, (it['quantity'], it['product_id']))
        # Clear cart
        cursor.execute("DELETE FROM cart WHERE user_id=%s", (order['user_id'],))

        try:
            cursor.execute("""
                INSERT INTO payment_events (payment_id, event_type, payload_json)
                VALUES (%s, %s, %s)
            """, (payment_id, 'payment.succeeded', json.dumps(data)))
        except Exception:
            pass

    elif status == 'failed':
        cursor.execute("UPDATE payments SET status=%s WHERE id=%s", ('failed', payment_id))
        cursor.execute("UPDATE orders SET payment_status='failed' WHERE id=%s", (order['id'],))
        try:
            cursor.execute("""
                INSERT INTO payment_events (payment_id, event_type, payload_json)
                VALUES (%s, %s, %s)
            """, (payment_id, 'payment.failed', json.dumps(data)))
        except Exception:
            pass

    elif status == 'pending':
        cursor.execute("UPDATE payments SET status=%s WHERE id=%s", ('pending', payment_id))
        cursor.execute("UPDATE orders SET payment_status='pending' WHERE id=%s", (order['id'],))
        try:
            cursor.execute("""
                INSERT INTO payment_events (payment_id, event_type, payload_json)
                VALUES (%s, %s, %s)
            """, (payment_id, 'payment.pending', json.dumps(data)))
        except Exception:
            pass

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'ok': True})

@app.route('/payment/return', methods=['GET'])
def payment_return():
    payment_id = request.args.get('payment_id', type=int)
    if not payment_id:
        flash('Invalid payment reference', 'error')
        return redirect(url_for('checkout'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM payments WHERE id=%s", (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        cursor.close()
        conn.close()
        return "Payment not found", 404

    cursor.execute("SELECT * FROM orders WHERE id=%s", (payment['order_id'],))
    order = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('payment_result.html',
                           payment=payment,
                           order=order,
                           is_logged_in=is_logged_in())

@app.route('/buy-now/<int:product_id>')
def buy_now(product_id):
    if 'user_id' not in session:
        flash("Please login to continue", "warning")
        return redirect(url_for('auth'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if not product:
        flash("Product not found", "error")
        return redirect(url_for('products'))

    return render_template("buy_now.html", product=product, is_logged_in=True)

# ==================== RUN APPLICATION ====================
if __name__ == '__main__':
    # In development use debug=True. In production, use a proper WSGI server and env config.
    app.run(debug=True, port=5000)
