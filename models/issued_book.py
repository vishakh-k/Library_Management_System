"""IssuedBook model – tracks book borrow / return transactions."""

from datetime import date, timedelta


class IssuedBook:
    """Encapsulates all issued-book-related database operations."""

    FINE_PER_DAY = 1.00  # fine amount per overdue day

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_all(mysql, status=None):
        """Return all issue records, optionally filtered by *status*.

        Each row includes book title/author and student name via JOINs.
        """
        cur = mysql.connection.cursor()
        query = (
            "SELECT ib.*, b.title AS book_title, b.author AS book_author, "
            "s.name AS student_name, s.enrollment_no, "
            "u.username AS issued_by_name "
            "FROM issued_books ib "
            "JOIN books b ON ib.book_id = b.id "
            "JOIN students s ON ib.student_id = s.id "
            "LEFT JOIN users u ON ib.issued_by = u.id "
        )
        params = []

        if status:
            query += "WHERE ib.status = %s "
            params.append(status)

        query += "ORDER BY ib.created_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_by_id(mysql, issue_id):
        """Return a single issue record with JOINed data, or ``None``."""
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT ib.*, b.title AS book_title, b.author AS book_author, "
            "b.isbn AS book_isbn, "
            "s.name AS student_name, s.enrollment_no, s.email AS student_email, "
            "u.username AS issued_by_name "
            "FROM issued_books ib "
            "JOIN books b ON ib.book_id = b.id "
            "JOIN students s ON ib.student_id = s.id "
            "LEFT JOIN users u ON ib.issued_by = u.id "
            "WHERE ib.id = %s",
            (issue_id,),
        )
        row = cur.fetchone()
        cur.close()
        return row

    # ------------------------------------------------------------------
    # Issue / Return
    # ------------------------------------------------------------------

    @staticmethod
    def issue_book(mysql, book_id, student_id, user_id, due_days=14):
        """Issue a book to a student.

        * Sets issue_date to today and due_date to today + *due_days*.
        * Decrements the book's ``available`` count.
        * Returns the new issue record id.
        """
        today = date.today()
        due = today + timedelta(days=due_days)

        cur = mysql.connection.cursor()

        # Insert the issue record
        cur.execute(
            "INSERT INTO issued_books "
            "(book_id, student_id, issue_date, due_date, status, issued_by) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (book_id, student_id, today, due, 'issued', user_id),
        )
        new_id = cur.lastrowid

        # Decrement availability
        cur.execute(
            "UPDATE books SET available = available - 1 WHERE id = %s",
            (book_id,),
        )

        mysql.connection.commit()
        cur.close()
        return new_id

    @staticmethod
    def return_book(mysql, issue_id):
        """Process the return of an issued book.

        * Sets ``return_date`` to today.
        * Calculates and stores any overdue fine.
        * Updates status to ``'returned'``.
        * Increments the book's ``available`` count.
        * Returns the calculated fine amount.
        """
        cur = mysql.connection.cursor()

        # Fetch the issue record
        cur.execute(
            "SELECT * FROM issued_books WHERE id = %s",
            (issue_id,),
        )
        record = cur.fetchone()
        if record is None:
            cur.close()
            return None

        today = date.today()
        due_date = record['due_date']
        fine = IssuedBook.calculate_fine(due_date, today)

        # Update the issue record
        cur.execute(
            "UPDATE issued_books "
            "SET return_date = %s, fine = %s, status = %s "
            "WHERE id = %s",
            (today, fine, 'returned', issue_id),
        )

        # Increment book availability
        cur.execute(
            "UPDATE books SET available = available + 1 WHERE id = %s",
            (record['book_id'],),
        )

        mysql.connection.commit()
        cur.close()
        return fine

    @staticmethod
    def calculate_fine(due_date, return_date):
        """Calculate the fine based on the number of overdue days.

        Returns ``0.00`` if the book is returned on time.
        """
        if isinstance(due_date, str):
            due_date = date.fromisoformat(due_date)
        if isinstance(return_date, str):
            return_date = date.fromisoformat(return_date)

        if return_date <= due_date:
            return 0.00

        overdue_days = (return_date - due_date).days
        return round(overdue_days * IssuedBook.FINE_PER_DAY, 2)

    # ------------------------------------------------------------------
    # Overdue detection
    # ------------------------------------------------------------------

    @staticmethod
    def get_overdue(mysql):
        """Return all issue records that are past their due date and still
        have status ``'issued'``.
        """
        cur = mysql.connection.cursor()
        today = date.today()
        cur.execute(
            "SELECT ib.*, b.title AS book_title, b.author AS book_author, "
            "s.name AS student_name, s.enrollment_no "
            "FROM issued_books ib "
            "JOIN books b ON ib.book_id = b.id "
            "JOIN students s ON ib.student_id = s.id "
            "WHERE ib.due_date < %s AND ib.status = 'issued' "
            "ORDER BY ib.due_date",
            (today,),
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    # ------------------------------------------------------------------
    # Aggregate counts
    # ------------------------------------------------------------------

    @staticmethod
    def get_issued_count(mysql):
        """Return the number of books currently issued (not yet returned)."""
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM issued_books WHERE status = 'issued'"
        )
        row = cur.fetchone()
        cur.close()
        return row['cnt']

    @staticmethod
    def get_returned_count(mysql):
        """Return the number of books that have been returned."""
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM issued_books WHERE status = 'returned'"
        )
        row = cur.fetchone()
        cur.close()
        return row['cnt']

    @staticmethod
    def get_total_fines(mysql):
        """Return the sum of all fines collected."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT COALESCE(SUM(fine), 0) AS total FROM issued_books")
        row = cur.fetchone()
        cur.close()
        return float(row['total'])

    def __repr__(self):
        return "<IssuedBook>"
