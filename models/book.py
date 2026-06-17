"""Book model with CRUD, search, availability management, and QR generation."""

import base64
import io

import qrcode


class Book:
    """Encapsulates all book-related database operations."""

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_all(mysql, search=None, category_id=None):
        """Return all books, optionally filtered by *search* term or
        *category_id*.

        Each row includes the category name via a LEFT JOIN.
        """
        cur = mysql.connection.cursor()
        query = (
            "SELECT b.*, c.name AS category_name "
            "FROM books b "
            "LEFT JOIN categories c ON b.category_id = c.id "
        )
        params = []
        conditions = []

        if search:
            conditions.append(
                "(b.title LIKE %s OR b.author LIKE %s OR b.isbn LIKE %s)"
            )
            like = f"%{search}%"
            params.extend([like, like, like])

        if category_id:
            conditions.append("b.category_id = %s")
            params.append(category_id)

        if conditions:
            query += "WHERE " + " AND ".join(conditions) + " "

        query += "ORDER BY b.created_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_by_id(mysql, book_id):
        """Return a single book dict (with category name), or ``None``."""
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT b.*, c.name AS category_name "
            "FROM books b "
            "LEFT JOIN categories c ON b.category_id = c.id "
            "WHERE b.id = %s",
            (book_id,),
        )
        row = cur.fetchone()
        cur.close()
        return row

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    @staticmethod
    def create(mysql, data):
        """Insert a new book from a dictionary of column values.

        Expected keys: title, author, isbn, publisher, category_id,
        quantity, shelf_location.

        Returns the new row id.
        """
        cur = mysql.connection.cursor()
        quantity = int(data.get('quantity', 1))
        cur.execute(
            "INSERT INTO books "
            "(title, author, isbn, publisher, category_id, quantity, "
            "available, shelf_location) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                data['title'],
                data['author'],
                data.get('isbn'),
                data.get('publisher'),
                data.get('category_id') or None,
                quantity,
                quantity,  # available defaults to the full quantity
                data.get('shelf_location'),
            ),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
        return new_id

    @staticmethod
    def update(mysql, book_id, data):
        """Update an existing book identified by *book_id*."""
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE books SET title=%s, author=%s, isbn=%s, publisher=%s, "
            "category_id=%s, quantity=%s, shelf_location=%s "
            "WHERE id=%s",
            (
                data['title'],
                data['author'],
                data.get('isbn'),
                data.get('publisher'),
                data.get('category_id') or None,
                data.get('quantity', 1),
                data.get('shelf_location'),
                book_id,
            ),
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def delete(mysql, book_id):
        """Delete a book by its *book_id*."""
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
        mysql.connection.commit()
        cur.close()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    @staticmethod
    def search(mysql, query):
        """Search books by title, author, or ISBN."""
        cur = mysql.connection.cursor()
        like = f"%{query}%"
        cur.execute(
            "SELECT b.*, c.name AS category_name "
            "FROM books b "
            "LEFT JOIN categories c ON b.category_id = c.id "
            "WHERE b.title LIKE %s OR b.author LIKE %s OR b.isbn LIKE %s "
            "ORDER BY b.title",
            (like, like, like),
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    # ------------------------------------------------------------------
    # Availability helpers
    # ------------------------------------------------------------------

    @staticmethod
    def update_availability(mysql, book_id, change):
        """Increment (positive *change*) or decrement (negative) the
        ``available`` count for a book.
        """
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE books SET available = available + %s WHERE id = %s",
            (change, book_id),
        )
        mysql.connection.commit()
        cur.close()

    # ------------------------------------------------------------------
    # Aggregate counts
    # ------------------------------------------------------------------

    @staticmethod
    def get_total_count(mysql):
        """Return the total number of books in the catalogue."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM books")
        row = cur.fetchone()
        cur.close()
        return row['cnt']

    @staticmethod
    def get_available_count(mysql):
        """Return the total number of books currently available."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT SUM(available) AS cnt FROM books")
        row = cur.fetchone()
        cur.close()
        return row['cnt'] or 0

    # ------------------------------------------------------------------
    # QR code generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_qr(mysql, book_id):
        """Generate a QR code for *book_id*, store it as a base64-encoded
        PNG in the ``qr_code`` column, and return the base64 string.
        """
        book = Book.get_by_id(mysql, book_id)
        if book is None:
            return None

        # QR payload: basic book metadata
        qr_data = (
            f"Book ID: {book['id']}\n"
            f"Title: {book['title']}\n"
            f"Author: {book['author']}\n"
            f"ISBN: {book.get('isbn', 'N/A')}"
        )

        img = qrcode.make(qr_data)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE books SET qr_code = %s WHERE id = %s",
            (b64, book_id),
        )
        mysql.connection.commit()
        cur.close()
        return b64

    def __repr__(self):
        return "<Book>"
