from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'love4761'  # Add your MySQL password
app.config['MYSQL_DB'] = 'ecommerce_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ============ ROUTES FOR PAGES ============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def products_page():
    return render_template('products.html')

@app.route('/cart')
def cart_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('cart.html')

@app.route('/virtual-basket')
def virtual_basket_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('virtual_basket.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

# ============ API ENDPOINTS ============

# Get all categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        cursor.close()
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get all products
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        cursor = mysql.connection.cursor()
        category_id = request.args.get('category_id')
        search = request.args.get('search', '')
        
        if category_id:
            query = "SELECT * FROM products WHERE category_id = %s AND product_name LIKE %s"
            cursor.execute(query, (category_id, f'%{search}%'))
        else:
            query = "SELECT * FROM products WHERE product_name LIKE %s"
            cursor.execute(query, (f'%{search}%',))
        
        products = cursor.fetchall()
        cursor.close()
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User Registration
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        hashed_password = generate_password_hash(password)
        
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        mysql.connection.commit()
        user_id = cursor.lastrowid
        
        # Create cart for new user
        cursor.execute("INSERT INTO cart (user_id) VALUES (%s)", (user_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Registration successful', 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 400

# User Login
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session.permanent = True
            return jsonify({'message': 'Login successful', 'success': True, 'username': user['username']})
        else:
            return jsonify({'message': 'Invalid credentials', 'success': False}), 401
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

# User Logout
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully', 'success': True})

# Check Session
@app.route('/api/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False})

# Add to Cart
@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in', 'success': False}), 401
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        user_id = session['user_id']
        
        cursor = mysql.connection.cursor()
        
        # Get user's cart
        cursor.execute("SELECT cart_id FROM cart WHERE user_id = %s", (user_id,))
        cart = cursor.fetchone()
        
        if not cart:
            cursor.execute("INSERT INTO cart (user_id) VALUES (%s)", (user_id,))
            mysql.connection.commit()
            cart_id = cursor.lastrowid
        else:
            cart_id = cart['cart_id']
        
        # Check if product already in cart
        cursor.execute(
            "SELECT * FROM cart_items WHERE cart_id = %s AND product_id = %s",
            (cart_id, product_id)
        )
        existing_item = cursor.fetchone()
        
        if existing_item:
            cursor.execute(
                "UPDATE cart_items SET quantity = quantity + %s WHERE cart_id = %s AND product_id = %s",
                (quantity, cart_id, product_id)
            )
        else:
            cursor.execute(
                "INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (%s, %s, %s)",
                (cart_id, product_id, quantity)
            )
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Added to cart', 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

# Get Cart Items
@app.route('/api/cart', methods=['GET'])
def get_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        user_id = session['user_id']
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT p.*, ci.quantity, ci.cart_item_id
            FROM cart c
            JOIN cart_items ci ON c.cart_id = ci.cart_id
            JOIN products p ON ci.product_id = p.product_id
            WHERE c.user_id = %s
        """
        cursor.execute(query, (user_id,))
        cart_items = cursor.fetchall()
        cursor.close()
        
        return jsonify(cart_items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update Cart Item Quantity
@app.route('/api/cart/update', methods=['PUT'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        cart_item_id = data.get('cart_item_id')
        quantity = data.get('quantity')
        
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE cart_items SET quantity = %s WHERE cart_item_id = %s",
            (quantity, cart_item_id)
        )
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Cart updated', 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Remove from Cart
@app.route('/api/cart/remove/<int:cart_item_id>', methods=['DELETE'])
def remove_from_cart(cart_item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM cart_items WHERE cart_item_id = %s", (cart_item_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Item removed', 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Virtual Basket - Get Recommendations
@app.route('/api/virtual-basket/recommend', methods=['POST'])
def virtual_basket_recommend():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        items = data.get('items', [])  # List of {description, color, category}
        
        cursor = mysql.connection.cursor()
        
        # Save virtual basket
        user_id = session['user_id']
        cursor.execute("INSERT INTO virtual_basket (user_id) VALUES (%s)", (user_id,))
        mysql.connection.commit()
        basket_id = cursor.lastrowid
        
        # Save items
        for item in items:
            cursor.execute(
                "INSERT INTO virtual_basket_items (basket_id, item_description, category_id, color) VALUES (%s, %s, %s, %s)",
                (basket_id, item.get('description'), item.get('category_id'), item.get('color'))
            )
        mysql.connection.commit()
        
        # Find matching products
        recommendations = []
        
        for item in items:
            query = """
                SELECT * FROM products 
                WHERE category_id = %s 
                AND (color = %s OR color IS NULL)
                LIMIT 3
            """
            cursor.execute(query, (item.get('category_id'), item.get('color')))
            matching_products = cursor.fetchall()
            recommendations.extend(matching_products)
        
        # Get pre-defined combinations
        if len(recommendations) >= 3:
            product_ids = [p['product_id'] for p in recommendations[:3]]
            combo_query = """
                SELECT pc.*, 
                       p1.product_name as name1, p1.price as price1, p1.image_url as img1,
                       p2.product_name as name2, p2.price as price2, p2.image_url as img2,
                       p3.product_name as name3, p3.price as price3, p3.image_url as img3
                FROM product_combinations pc
                JOIN products p1 ON pc.product_id_1 = p1.product_id
                JOIN products p2 ON pc.product_id_2 = p2.product_id
                JOIN products p3 ON pc.product_id_3 = p3.product_id
                WHERE pc.product_id_1 IN (%s, %s, %s)
                   OR pc.product_id_2 IN (%s, %s, %s)
                   OR pc.product_id_3 IN (%s, %s, %s)
                ORDER BY pc.compatibility_score DESC
                LIMIT 5
            """
            cursor.execute(combo_query, product_ids * 3)
            combinations = cursor.fetchall()
        else:
            combinations = []
        
        cursor.close()
        
        return jsonify({
            'recommendations': recommendations,
            'combinations': combinations,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

if __name__ == '__main__':
    app.run(debug=True)
