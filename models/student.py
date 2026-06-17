"""Student model with CRUD, search, and issued-books lookup."""


class Student:
    """Encapsulates all student-related database operations."""

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_all(mysql, search=None):
        """Return all students, optionally filtered by a *search* term."""
        cur = mysql.connection.cursor()

        if search:
            like = f"%{search}%"
            cur.execute(
                "SELECT * FROM students "
                "WHERE name LIKE %s OR email LIKE %s OR enrollment_no LIKE %s "
                "ORDER BY created_at DESC",
                (like, like, like),
            )
        else:
            cur.execute("SELECT * FROM students ORDER BY created_at DESC")

        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_by_id(mysql, student_id):
        """Return a single student dict or ``None``."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        row = cur.fetchone()
        cur.close()
        return row

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    @staticmethod
    def create(mysql, data):
        """Insert a new student from a dictionary of column values.

        Expected keys: name, email, phone, enrollment_no, department,
        semester, address.

        Returns the new row id.
        """
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO students "
            "(name, email, phone, enrollment_no, department, semester, address) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                data['name'],
                data['email'],
                data.get('phone'),
                data['enrollment_no'],
                data.get('department'),
                data.get('semester'),
                data.get('address'),
            ),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
        return new_id

    @staticmethod
    def update(mysql, student_id, data):
        """Update an existing student identified by *student_id*."""
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE students SET name=%s, email=%s, phone=%s, "
            "enrollment_no=%s, department=%s, semester=%s, address=%s "
            "WHERE id=%s",
            (
                data['name'],
                data['email'],
                data.get('phone'),
                data['enrollment_no'],
                data.get('department'),
                data.get('semester'),
                data.get('address'),
                student_id,
            ),
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def delete(mysql, student_id):
        """Delete a student by *student_id*."""
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM students WHERE id = %s", (student_id,))
        mysql.connection.commit()
        cur.close()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    @staticmethod
    def search(mysql, query):
        """Search students by name, email, or enrollment number."""
        cur = mysql.connection.cursor()
        like = f"%{query}%"
        cur.execute(
            "SELECT * FROM students "
            "WHERE name LIKE %s OR email LIKE %s OR enrollment_no LIKE %s "
            "ORDER BY name",
            (like, like, like),
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    @staticmethod
    def get_total_count(mysql):
        """Return the total number of registered students."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM students")
        row = cur.fetchone()
        cur.close()
        return row['cnt']

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    @staticmethod
    def get_issued_books(mysql, student_id):
        """Return all books currently or previously issued to a student,
        including book details via JOIN.
        """
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT ib.*, b.title, b.author, b.isbn "
            "FROM issued_books ib "
            "JOIN books b ON ib.book_id = b.id "
            "WHERE ib.student_id = %s "
            "ORDER BY ib.issue_date DESC",
            (student_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    def __repr__(self):
        return "<Student>"
