"""Book issue / return routes.

Blueprint: ``issues_bp``  (url_prefix ``/issues``)
"""

from datetime import date, timedelta

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort,
)
from flask_login import login_required, current_user

from extensions import mysql

issues_bp = Blueprint('issues', __name__, url_prefix='/issues')

@issues_bp.before_request
@login_required
def limit_to_admin():
    if current_user.role != 'admin':
        abort(403)

# Fine rate: Rs per day overdue
FINE_PER_DAY = 2.00
# Default loan period in days
LOAN_PERIOD_DAYS = 14


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
        pass


# ------------------------------------------------------------------
# List issued books
# ------------------------------------------------------------------
@issues_bp.route('/', endpoint='list_issues')
@login_required
def index():
    """List all issued books with optional status filter."""
    status = request.args.get('status', '').strip()

    try:
        cur = mysql.connection.cursor()

        query = (
            "SELECT ib.*, b.title AS book_title, b.author AS book_author, "
            "       s.name AS student_name, s.enrollment_no "
            "FROM issued_books ib "
            "JOIN books b ON ib.book_id = b.id "
            "JOIN students s ON ib.student_id = s.id "
        )
        params = []

        if status:
            query += "WHERE ib.status = %s "
            params.append(status)

        query += "ORDER BY ib.issue_date DESC"

        cur.execute(query, tuple(params))
        issues = list(cur.fetchall())

        for issue in issues:
            issue['book'] = {'title': issue['book_title'], 'author': issue['book_author']}
            issue['student'] = {'name': issue['student_name']}

        cur.close()

        return render_template(
            'issues/list.html', issues=issues, status=status,
        )
    except Exception as e:
        flash(f'Error loading issues: {e}', 'error')
        return render_template(
            'issues/list.html', issues=[], status=status,
        )


# ------------------------------------------------------------------
# Issue a book
# ------------------------------------------------------------------
@issues_bp.route('/new', methods=['GET', 'POST'], endpoint='issue_book')
@issues_bp.route('/add', methods=['GET', 'POST'], endpoint='issue_book_alias')
@login_required
def new():
    """Show the issue form (GET) or create a new issue record (POST)."""
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT id, title, author, available FROM books "
            "WHERE available > 0 ORDER BY title"
        )
        books = cur.fetchall()
        cur.execute("SELECT id, name, enrollment_no FROM students ORDER BY name")
        students = cur.fetchall()
        cur.close()
    except Exception:
        books, students = [], []

    if request.method == 'POST':
        book_id = request.form.get('book_id', type=int)
        student_id = request.form.get('student_id', type=int)

        if not book_id or not student_id:
            flash('Please select both a book and a student.', 'error')
            return render_template(
                'issues/issue.html', books=books, students=students,
            )

        try:
            cur = mysql.connection.cursor()

            # Verify book availability
            cur.execute(
                "SELECT id, title, available FROM books WHERE id = %s",
                (book_id,),
            )
            book = cur.fetchone()

            if not book:
                flash('Book not found.', 'error')
                return redirect(url_for('issues.issue_book'))

            if book['available'] <= 0:
                flash('This book is not available for issue.', 'error')
                return redirect(url_for('issues.issue_book'))

            # Verify student exists
            cur.execute(
                "SELECT id, name FROM students WHERE id = %s",
                (student_id,),
            )
            student = cur.fetchone()

            if not student:
                flash('Student not found.', 'error')
                return redirect(url_for('issues.issue_book'))

            issue_date = date.today()
            due_date = issue_date + timedelta(days=LOAN_PERIOD_DAYS)

            # Create issue record
            cur.execute(
                "INSERT INTO issued_books "
                "(book_id, student_id, issue_date, due_date, status, issued_by) "
                "VALUES (%s, %s, %s, %s, 'issued', %s)",
                (book_id, student_id, issue_date, due_date, current_user.id),
            )

            # Decrement available count
            cur.execute(
                "UPDATE books SET available = available - 1 WHERE id = %s",
                (book_id,),
            )

            mysql.connection.commit()
            issue_id = cur.lastrowid
            cur.close()

            _log_activity(
                'ISSUE', 'issued_book', issue_id,
                f"Issued '{book['title']}' to {student['name']}",
            )
            flash(
                f"Book '{book['title']}' issued to {student['name']}. "
                f"Due date: {due_date.strftime('%d-%b-%Y')}.",
                'success',
            )
            return redirect(url_for('issues.list_issues'))

        except Exception as e:
            flash(f'Error issuing book: {e}', 'error')
            return render_template(
                'issues/issue.html', books=books, students=students,
            )

    # GET
    return render_template(
        'issues/issue.html', books=books, students=students,
    )


# ------------------------------------------------------------------
# Return a book
# ------------------------------------------------------------------
@issues_bp.route('/return/<int:id>', methods=['GET', 'POST'], endpoint='return_book')
@login_required
def return_book(id):
    """Process a book return and calculate any fine."""
    try:
        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT ib.*, b.title AS book_title, s.name AS student_name "
            "FROM issued_books ib "
            "JOIN books b ON ib.book_id = b.id "
            "JOIN students s ON ib.student_id = s.id "
            "WHERE ib.id = %s",
            (id,),
        )
        issue = cur.fetchone()

        if not issue:
            flash('Issue record not found.', 'error')
            return redirect(url_for('issues.list_issues'))

        if issue['status'] == 'returned':
            flash('This book has already been returned.', 'warning')
            return redirect(url_for('issues.list_issues'))

        return_date = date.today()
        fine = 0.00

        # Calculate fine if overdue
        if return_date > issue['due_date']:
            overdue_days = (return_date - issue['due_date']).days
            fine = round(overdue_days * FINE_PER_DAY, 2)

        # Update issue record
        cur.execute(
            "UPDATE issued_books SET return_date = %s, fine = %s, "
            "status = 'returned' WHERE id = %s",
            (return_date, fine, id),
        )

        # Increment available count
        cur.execute(
            "UPDATE books SET available = available + 1 WHERE id = %s",
            (issue['book_id'],),
        )

        mysql.connection.commit()
        cur.close()

        _log_activity(
            'RETURN', 'issued_book', id,
            f"Returned '{issue['book_title']}' from {issue['student_name']}. "
            f"Fine: Rs {fine}",
        )

        if fine > 0:
            flash(
                f"Book returned. Fine of Rs {fine:.2f} applied "
                f"({(return_date - issue['due_date']).days} days overdue).",
                'warning',
            )
        else:
            flash('Book returned successfully. No fine.', 'success')

    except Exception as e:
        flash(f'Error returning book: {e}', 'error')

    return redirect(url_for('issues.list_issues'))
