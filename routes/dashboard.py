"""Dashboard routes – display stats and provide JSON API for Chart.js charts."""

from flask import Blueprint, render_template, jsonify, abort
from flask_login import login_required, current_user
from extensions import mysql
from models.book import Book
from models.student import Student
from models.issued_book import IssuedBook
from models.activity_log import ActivityLog

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.before_request
@login_required
def limit_to_admin():
    if current_user.role != 'admin':
        abort(403)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Display the main dashboard with statistics and recent activity."""
    try:
        total_books = Book.get_total_count(mysql)
        total_students = Student.get_total_count(mysql)
        issued_books = IssuedBook.get_issued_count(mysql)
        returned_books = IssuedBook.get_returned_count(mysql)
        total_fines = IssuedBook.get_total_fines(mysql)
        recent_activity = ActivityLog.get_recent(mysql, limit=10)
    except Exception as e:
        total_books = total_students = issued_books = returned_books = total_fines = 0
        recent_activity = []

    return render_template(
        'dashboard.html',
        total_books=total_books,
        total_students=total_students,
        issued_books=issued_books,
        returned_books=returned_books,
        total_fines=total_fines,
        recent_activity=recent_activity
    )

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def stats_api():
    """API endpoint returning category and monthly trends data for Chart.js."""
    try:
        cur = mysql.connection.cursor()
        
        # 1. Books by category
        cur.execute(
            "SELECT c.name AS category, COUNT(b.id) AS count "
            "FROM categories c "
            "LEFT JOIN books b ON b.category_id = c.id "
            "GROUP BY c.id, c.name "
            "ORDER BY count DESC"
        )
        categories_data = cur.fetchall()

        # 2. Monthly issue/return trends (last 6 months)
        # Use DATE_FORMAT for grouping by Month
        cur.execute(
            "SELECT DATE_FORMAT(issue_date, '%b %Y') AS month_name, "
            "       SUM(CASE WHEN status = 'issued' OR status = 'overdue' THEN 1 ELSE 0 END) AS issued_count, "
            "       SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) AS returned_count, "
            "       MIN(issue_date) as min_date "
            "FROM issued_books "
            "GROUP BY month_name "
            "ORDER BY min_date DESC "
            "LIMIT 6"
        )
        trends_data = cur.fetchall()
        # Reverse to show chronological order
        trends_data = trends_data[::-1]
        
        cur.close()
        
        return jsonify({
            'categories': [row['category'] for row in categories_data],
            'category_counts': [row['count'] for row in categories_data],
            'months': [row['month_name'] for row in trends_data],
            'issued': [int(row['issued_count'] or 0) for row in trends_data],
            'returned': [int(row['returned_count'] or 0) for row in trends_data]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
