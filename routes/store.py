"""Public storefront and purchase management routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import mysql

store_bp = Blueprint('store', __name__, url_prefix='/store')

@store_bp.before_request
@login_required
def check_login():
    """Ensure user is logged in for all storefront routes."""
    pass

@store_bp.route('/', endpoint='list_books')
def list_books():
    """Display the list of all books with search and category filter."""
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '').strip()

    try:
        cur = mysql.connection.cursor()
        
        # Base query to get books and their categories
        query = (
            "SELECT b.*, c.name AS category_name "
            "FROM books b "
            "LEFT JOIN categories c ON b.category_id = c.id "
            "WHERE 1=1"
        )
        params = []

        if search:
            query += " AND (b.title LIKE %s OR b.author LIKE %s OR b.isbn LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        if category_id:
            query += " AND b.category_id = %s"
            params.append(category_id)

        query += " ORDER BY b.title ASC"
        cur.execute(query, params)
        books = cur.fetchall()

        # Get all categories for filter dropdown
        cur.execute("SELECT * FROM categories ORDER BY name ASC")
        categories = cur.fetchall()
        
        cur.close()
    except Exception as e:
        flash(f"Error loading products: {str(e)}", "danger")
        books = []
        categories = []

    return render_template(
        'store/list.html',
        books=books,
        categories=categories,
        search=search,
        selected_category=category_id
    )

@store_bp.route('/buy/<int:id>', methods=['GET'])
def buy(id):
    """Checkout confirmation page showing details of a selected book."""
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT b.*, c.name AS category_name "
            "FROM books b "
            "LEFT JOIN categories c ON b.category_id = c.id "
            "WHERE b.id = %s",
            (id,)
        )
        book = cur.fetchone()
        cur.close()
        
        if not book:
            abort(404)

        if book['available'] <= 0:
            flash(f"'{book['title']}' is currently out of stock.", "warning")
            return redirect(url_for('store.list_books'))
            
        return render_template('store/buy.html', book=book)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('store.list_books'))

@store_bp.route('/checkout/<int:id>', methods=['POST'])
def checkout(id):
    """Process book purchase."""
    quantity_raw = request.form.get('quantity', '1')
    try:
        quantity = int(quantity_raw)
        if quantity < 1:
            flash("Quantity must be at least 1.", "danger")
            return redirect(url_for('store.buy', id=id))
    except ValueError:
        flash("Invalid quantity specified.", "danger")
        return redirect(url_for('store.buy', id=id))

    try:
        cur = mysql.connection.cursor()
        # Fetch book with locking to prevent race conditions
        cur.execute("SELECT * FROM books WHERE id = %s FOR UPDATE", (id,))
        book = cur.fetchone()

        if not book:
            cur.close()
            abort(404)

        if book['available'] < quantity:
            cur.close()
            flash(f"Not enough stock available. Only {book['available']} left.", "danger")
            return redirect(url_for('store.buy', id=id))

        # Decrement available quantity
        cur.execute(
            "UPDATE books SET available = available - %s WHERE id = %s",
            (quantity, id)
        )

        # Record purchase
        price_paid = book['price'] * quantity
        cur.execute(
            "INSERT INTO purchases (user_id, book_id, quantity, price_paid, status) "
            "VALUES (%s, %s, %s, %s, 'completed')",
            (current_user.id, id, quantity, price_paid)
        )

        mysql.connection.commit()
        cur.close()
        flash(f"Successfully purchased {quantity} copy/copies of '{book['title']}'!", "success")
        return redirect(url_for('store.my_purchases'))
    except Exception as e:
        flash(f"Purchase failed: {str(e)}", "danger")
        return redirect(url_for('store.buy', id=id))

@store_bp.route('/my-purchases')
def my_purchases():
    """Display the purchase history of the current user."""
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT p.*, b.title, b.author, b.isbn "
            "FROM purchases p "
            "JOIN books b ON p.book_id = b.id "
            "WHERE p.user_id = %s "
            "ORDER BY p.purchase_date DESC",
            (current_user.id,)
        )
        purchases = cur.fetchall()
        cur.close()
    except Exception as e:
        flash(f"Error loading purchase history: {str(e)}", "danger")
        purchases = []

    return render_template('store/my_purchases.html', purchases=purchases)
