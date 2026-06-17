"""Book management routes — CRUD and QR-code generation.

Blueprint: ``books_bp``  (url_prefix ``/books``)
"""

import io
import base64

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort,
)
from flask_login import login_required, current_user

from extensions import mysql

books_bp = Blueprint('books', __name__, url_prefix='/books')

@books_bp.before_request
@login_required
def limit_to_admin():
    if current_user.role != 'admin':
        abort(403)


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------
def _log_activity(action, entity_type, entity_id, details=None):
    """Insert a row into activity_logs for audit purposes."""
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO activity_logs "
            "(user_id, action, entity_type, entity_id, details, ip_address) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                current_user.id, action, entity_type,
                entity_id, details, request.remote_addr,
            ),
        )
        mysql.connection.commit()
        cur.close()
    except Exception:
        pass  # logging should never break the main flow


# ------------------------------------------------------------------
# List books
# ------------------------------------------------------------------
@books_bp.route('/', endpoint='list_books')
@login_required
def index():
    """List all books with optional search and category filter."""
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '', type=str)

    try:
        cur = mysql.connection.cursor()

        # Build dynamic query
        query = (
            "SELECT b.*, c.name AS category_name "
            "FROM books b "
            "LEFT JOIN categories c ON b.category_id = c.id "
            "WHERE 1=1 "
        )
        params = []

        if search:
            query += "AND (b.title LIKE %s OR b.author LIKE %s OR b.isbn LIKE %s) "
            like = f'%{search}%'
            params.extend([like, like, like])

        if category_id:
            query += "AND b.category_id = %s "
            params.append(category_id)

        query += "ORDER BY b.title ASC"

        cur.execute(query, tuple(params))
        books = list(cur.fetchall())

        for book in books:
            if book.get('category_name'):
                book['category'] = {'name': book['category_name']}
            else:
                book['category'] = None

        # Categories for filter dropdown
        cur.execute("SELECT * FROM categories ORDER BY name")
        categories = cur.fetchall()

        cur.close()

        return render_template(
            'books/list.html',
            books=books,
            categories=categories,
            search=search,
            category_id=category_id,
        )
    except Exception as e:
        flash(f'Error loading books: {e}', 'error')
        return render_template(
            'books/list.html', books=[], categories=[],
            search=search, category_id=category_id,
        )


# ------------------------------------------------------------------
# Add a book
# ------------------------------------------------------------------
@books_bp.route('/add', methods=['GET', 'POST'], endpoint='add_book')
@login_required
def add():
    """Render the add-book form (GET) or create a new book (POST)."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categories ORDER BY name")
        categories = cur.fetchall()
        cur.close()
    except Exception:
        categories = []

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        isbn = request.form.get('isbn', '').strip() or None
        publisher = request.form.get('publisher', '').strip() or None
        category_id = request.form.get('category_id') or None
        quantity = request.form.get('quantity', 1, type=int)
        shelf_location = request.form.get('shelf_location', '').strip() or None

        # Validation
        if not title or not author:
            flash('Title and Author are required.', 'error')
            return render_template(
                'books/add.html', categories=categories,
                book=request.form,
            )

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO books "
                "(title, author, isbn, publisher, category_id, "
                " quantity, available, shelf_location) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (title, author, isbn, publisher, category_id,
                 quantity, quantity, shelf_location),
            )
            mysql.connection.commit()
            book_id = cur.lastrowid
            cur.close()

            _log_activity('CREATE', 'book', book_id,
                          f'Added book: {title}')
            flash('Book added successfully!', 'success')
            return redirect(url_for('books.list_books'))
        except Exception as e:
            flash(f'Error adding book: {e}', 'error')
            return render_template(
                'books/add.html', categories=categories,
                book=request.form,
            )

    # GET
    return render_template('books/add.html', categories=categories, book=None)


# ------------------------------------------------------------------
# Edit a book
# ------------------------------------------------------------------
@books_bp.route('/edit/<int:id>', methods=['GET', 'POST'], endpoint='edit_book')
@login_required
def edit(id):
    """Render the edit form (GET) or update the book (POST)."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categories ORDER BY name")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM books WHERE id = %s", (id,))
        book = cur.fetchone()
        cur.close()

    except Exception as e:
        flash(f'Error loading book: {e}', 'error')
        return redirect(url_for('books.list_books'))

    if not book:
        abort(404)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        isbn = request.form.get('isbn', '').strip() or None
        publisher = request.form.get('publisher', '').strip() or None
        category_id = request.form.get('category_id') or None
        quantity = request.form.get('quantity', 1, type=int)
        shelf_location = request.form.get('shelf_location', '').strip() or None

        if not title or not author:
            flash('Title and Author are required.', 'error')
            return render_template(
                'books/add.html', categories=categories, book=book,
            )

        try:
            # Adjust available count proportionally
            issued = book['quantity'] - book['available']
            new_available = max(quantity - issued, 0)

            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE books SET title=%s, author=%s, isbn=%s, "
                "publisher=%s, category_id=%s, quantity=%s, "
                "available=%s, shelf_location=%s WHERE id=%s",
                (title, author, isbn, publisher, category_id,
                 quantity, new_available, shelf_location, id),
            )
            mysql.connection.commit()
            cur.close()

            _log_activity('UPDATE', 'book', id,
                          f'Updated book: {title}')
            flash('Book updated successfully!', 'success')
            return redirect(url_for('books.list_books'))
        except Exception as e:
            flash(f'Error updating book: {e}', 'error')
            return render_template(
                'books/add.html', categories=categories, book=book,
            )

    # GET
    return render_template('books/add.html', categories=categories, book=book)


# ------------------------------------------------------------------
# Delete a book
# ------------------------------------------------------------------
@books_bp.route('/delete/<int:id>', methods=['POST'], endpoint='delete_book')
@login_required
def delete(id):
    """Delete a book by ID."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT title FROM books WHERE id = %s", (id,))
        book = cur.fetchone()

        if not book:
            flash('Book not found.', 'error')
            return redirect(url_for('books.list_books'))

        cur.execute("DELETE FROM books WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()

        _log_activity('DELETE', 'book', id,
                      f"Deleted book: {book['title']}")
        flash('Book deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting book: {e}', 'error')

    return redirect(url_for('books.list_books'))


# ------------------------------------------------------------------
# QR Code
# ------------------------------------------------------------------
@books_bp.route('/qr/<int:id>', endpoint='book_qr')
@login_required
def qr_code(id):
    """Generate and display a QR code for a book."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM books WHERE id = %s", (id,))
        book = cur.fetchone()
        cur.close()

        if not book:
            flash('Book not found.', 'error')
            return redirect(url_for('books.list_books'))

        import qrcode

        qr_data = (
            f"Book: {book['title']}\n"
            f"Author: {book['author']}\n"
            f"ISBN: {book.get('isbn', 'N/A')}\n"
            f"ID: {book['id']}"
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        return render_template(
            'books/qr.html', book=book, qr_code=qr_base64,
        )
    except Exception as e:
        flash(f'Error generating QR code: {e}', 'error')
        return redirect(url_for('books.list_books'))
