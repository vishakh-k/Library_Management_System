"""Student management routes — CRUD and profile view.

Blueprint: ``students_bp``  (url_prefix ``/students``)
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort,
)
from flask_login import login_required, current_user

from extensions import mysql

students_bp = Blueprint('students', __name__, url_prefix='/students')

@students_bp.before_request
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
        pass


# ------------------------------------------------------------------
# List students
# ------------------------------------------------------------------
@students_bp.route('/', endpoint='list_students')
@login_required
def index():
    """List all students with optional search."""
    search = request.args.get('search', '').strip()

    try:
        cur = mysql.connection.cursor()

        if search:
            like = f'%{search}%'
            cur.execute(
                "SELECT * FROM students "
                "WHERE name LIKE %s OR email LIKE %s "
                "OR enrollment_no LIKE %s OR department LIKE %s "
                "ORDER BY name ASC",
                (like, like, like, like),
            )
        else:
            cur.execute("SELECT * FROM students ORDER BY name ASC")

        students = cur.fetchall()
        cur.close()

        return render_template(
            'students/list.html', students=students, search=search,
        )
    except Exception as e:
        flash(f'Error loading students: {e}', 'error')
        return render_template(
            'students/list.html', students=[], search=search,
        )


# ------------------------------------------------------------------
# Add a student
# ------------------------------------------------------------------
@students_bp.route('/add', methods=['GET', 'POST'], endpoint='add_student')
@login_required
def add():
    """Render the add-student form (GET) or create a new student (POST)."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip() or None
        enrollment_no = request.form.get('enrollment_no', '').strip()
        department = request.form.get('department', '').strip() or None
        semester = request.form.get('semester', '').strip() or None
        address = request.form.get('address', '').strip() or None

        # Validation
        if not name or not email or not enrollment_no:
            flash('Name, Email, and Enrollment No are required.', 'error')
            return render_template(
                'students/add.html', student=request.form,
            )

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO students "
                "(name, email, phone, enrollment_no, department, "
                " semester, address) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (name, email, phone, enrollment_no,
                 department, semester, address),
            )
            mysql.connection.commit()
            student_id = cur.lastrowid
            cur.close()

            _log_activity('CREATE', 'student', student_id,
                          f'Added student: {name}')
            flash('Student added successfully!', 'success')
            return redirect(url_for('students.list_students'))
        except Exception as e:
            flash(f'Error adding student: {e}', 'error')
            return render_template(
                'students/add.html', student=request.form,
            )

    # GET
    return render_template('students/add.html', student=None)


# ------------------------------------------------------------------
# Edit a student
# ------------------------------------------------------------------
@students_bp.route('/edit/<int:id>', methods=['GET', 'POST'], endpoint='edit_student')
@login_required
def edit(id):
    """Render the edit form (GET) or update the student (POST)."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE id = %s", (id,))
        student = cur.fetchone()
        cur.close()

    except Exception as e:
        flash(f'Error loading student: {e}', 'error')
        return redirect(url_for('students.list_students'))

    if not student:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip() or None
        enrollment_no = request.form.get('enrollment_no', '').strip()
        department = request.form.get('department', '').strip() or None
        semester = request.form.get('semester', '').strip() or None
        address = request.form.get('address', '').strip() or None

        if not name or not email or not enrollment_no:
            flash('Name, Email, and Enrollment No are required.', 'error')
            return render_template(
                'students/add.html', student=student,
            )

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE students SET name=%s, email=%s, phone=%s, "
                "enrollment_no=%s, department=%s, semester=%s, "
                "address=%s WHERE id=%s",
                (name, email, phone, enrollment_no,
                 department, semester, address, id),
            )
            mysql.connection.commit()
            cur.close()

            _log_activity('UPDATE', 'student', id,
                          f'Updated student: {name}')
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students.list_students'))
        except Exception as e:
            flash(f'Error updating student: {e}', 'error')
            return render_template(
                'students/add.html', student=student,
            )

    # GET
    return render_template('students/add.html', student=student)


# ------------------------------------------------------------------
# Delete a student
# ------------------------------------------------------------------
@students_bp.route('/delete/<int:id>', methods=['POST'], endpoint='delete_student')
@login_required
def delete(id):
    """Delete a student by ID."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT name FROM students WHERE id = %s", (id,))
        student = cur.fetchone()

        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('students.list_students'))

        cur.execute("DELETE FROM students WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()

        _log_activity('DELETE', 'student', id,
                      f"Deleted student: {student['name']}")
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting student: {e}', 'error')

    return redirect(url_for('students.list_students'))


# ------------------------------------------------------------------
# Student profile
# ------------------------------------------------------------------
@students_bp.route('/profile/<int:id>', endpoint='student_profile')
@students_bp.route('/<int:id>', endpoint='student_profile_short')
@login_required
def profile(id):
    """Show a student's profile with their book issue history."""
    try:
        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM students WHERE id = %s", (id,))
        student = cur.fetchone()

        if student:
            # Books currently or previously issued to this student
            cur.execute(
                "SELECT ib.*, b.title AS book_title, b.author AS book_author "
                "FROM issued_books ib "
                "JOIN books b ON ib.book_id = b.id "
                "WHERE ib.student_id = %s "
                "ORDER BY ib.issue_date DESC",
                (id,),
            )
            issued_books = list(cur.fetchall())

            for ib in issued_books:
                ib['book'] = {'title': ib['book_title'], 'author': ib['book_author']}
        else:
            issued_books = []

        cur.close()
    except Exception as e:
        flash(f'Error loading student profile: {e}', 'error')
        return redirect(url_for('students.list_students'))

    if not student:
        abort(404)

    return render_template(
        'students/profile.html',
        student=student,
        issued_books=issued_books,
    )
