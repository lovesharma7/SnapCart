from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, render_template, current_app
import mysql.connector
from datetime import datetime

wishlist_bp = Blueprint('wishlist', __name__)

def get_db_connection():
    app = current_app._get_current_object()
    return mysql.connector.connect(
        host=app.config.get('MYSQL_HOST'),
        user=app.config.get('MYSQL_USER'),
        password=app.config.get('MYSQL_PASSWORD'),
        database=app.config.get('MYSQL_DB')
    )

# --------------------------
# Helper: Get wishlist count
# --------------------------
def get_wishlist_count(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM wishlists WHERE user_id=%s", (user_id,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


# --------------------------
# ADD TO WISHLIST
# --------------------------
@wishlist_bp.route('/wishlist/add', methods=['POST'])
def add_to_wishlist():
    if 'user_id' not in session:
        return jsonify({'error': 'login_required'}), 401

    user_id = session['user_id']
    product_id = request.json.get('product_id')

    if not product_id:
        return jsonify({'error': 'missing_product_id'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT IGNORE INTO wishlists (user_id, product_id) VALUES (%s, %s)",
            (user_id, product_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    # Return updated wishlist count
    count = get_wishlist_count(user_id)
    return jsonify({'ok': True, 'count': count}), 200


# --------------------------
# REMOVE FROM WISHLIST
# --------------------------
@wishlist_bp.route('/wishlist/remove', methods=['POST'])
def remove_from_wishlist():
    if 'user_id' not in session:
        return jsonify({'error': 'login_required'}), 401

    user_id = session['user_id']
    product_id = request.json.get('product_id')

    if not product_id:
        return jsonify({'error': 'missing_product_id'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM wishlists WHERE user_id=%s AND product_id=%s",
            (user_id, product_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    # Return updated wishlist count
    count = get_wishlist_count(user_id)
    return jsonify({'ok': True, 'count': count}), 200


# --------------------------
# WISHLIST PAGE
# --------------------------
@wishlist_bp.route('/wishlist')
def list_wishlist():
    if 'user_id' not in session:
        flash('Please login to view your wishlist', 'warning')
        return redirect(url_for('auth'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT p.*, w.created_at AS saved_at
        FROM wishlists w
        JOIN products p ON p.id = w.product_id
        WHERE w.user_id = %s
        ORDER BY w.created_at DESC
        """,
        (user_id,)
    )
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('wishlist.html', items=items, is_logged_in=True)


# --------------------------
# COUNT API
# --------------------------
@wishlist_bp.route('/wishlist/count')
def wishlist_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})

    user_id = session['user_id']
    count = get_wishlist_count(user_id)
    return jsonify({'count': count})


# --------------------------
# IDS API
# --------------------------
@wishlist_bp.route('/wishlist/ids')
def wishlist_ids():
    if 'user_id' not in session:
        return jsonify({'ids': []})

    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_id FROM wishlists WHERE user_id=%s", (user_id,))
    rows = cur.fetchall()

    ids = [r[0] for r in rows]

    cur.close()
    conn.close()

    return jsonify({'ids': ids})
