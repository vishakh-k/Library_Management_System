"""
Library Management System – Flask Application Factory
======================================================

Entry point for the application.  Run directly with::

    python app.py

or via a WSGI server such as Gunicorn::

    gunicorn "app:create_app()"
"""

import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from flask_mysqldb import MySQL

from config import config
from models.user import User

# ---------------------------------------------------------------------------
# Extension instances (created at module level, initialised inside the factory)
# ---------------------------------------------------------------------------
mysql = MySQL()
login_manager = LoginManager()


def create_app(config_name=None):
    """Application factory.

    Parameters
    ----------
    config_name : str, optional
        One of ``'development'``, ``'production'``, ``'testing'``.
        Defaults to the ``FLASK_ENV`` environment variable, falling back
        to ``'development'``.
    """
    load_dotenv()

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config[config_name])

    # ------------------------------------------------------------------
    # Initialise extensions
    # ------------------------------------------------------------------
    mysql.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # ------------------------------------------------------------------
    # Flask-Login user loader
    # ------------------------------------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        """Callback used by Flask-Login to reload a user from the session."""
        return User.get_by_id(mysql, int(user_id))

    # ------------------------------------------------------------------
    # Register blueprints
    # ------------------------------------------------------------------
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.books import books_bp
    from routes.students import students_bp
    from routes.issues import issues_bp
    from routes.reports import reports_bp
    from routes.categories import categories_bp
    from routes.store import store_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(store_bp)

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------
    @app.errorhandler(404)
    def page_not_found(error):
        """Handle 404 errors."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 errors."""
        return render_template('errors/500.html'), 500

    # ------------------------------------------------------------------
    # Root redirect
    # ------------------------------------------------------------------
    @app.route('/')
    def index():
        """Render the landing page when not logged in, or redirect based on role."""
        from flask import redirect, url_for, request
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('store.list_books'))
        
        search = request.args.get('search', '').strip()
        books = []
        arrivals = []
        stats = {
            'total_books': 0,
            'available_books': 0,
            'total_categories': 0,
            'total_students': 0
        }

        try:
            cur = mysql.connection.cursor()
            
            # 1. Fetch library stats
            cur.execute("SELECT IFNULL(SUM(quantity), 0) AS total_books, IFNULL(SUM(available), 0) AS available_books FROM books")
            book_stats = cur.fetchone()
            if book_stats:
                stats['total_books'] = book_stats['total_books']
                stats['available_books'] = book_stats['available_books']
                
            cur.execute("SELECT COUNT(*) AS total_categories FROM categories")
            cat_stats = cur.fetchone()
            if cat_stats:
                stats['total_categories'] = cat_stats['total_categories']
                
            cur.execute("SELECT COUNT(*) AS total_students FROM students")
            student_stats = cur.fetchone()
            if student_stats:
                stats['total_students'] = student_stats['total_students']
                
            # 2. Fetch new arrivals (latest 4 books)
            cur.execute(
                "SELECT b.*, c.name AS category_name "
                "FROM books b "
                "LEFT JOIN categories c ON b.category_id = c.id "
                "ORDER BY b.id DESC "
                "LIMIT 4"
            )
            arrivals = cur.fetchall()
            
            # 3. Handle book search
            if search:
                search_param = f"%{search}%"
                cur.execute(
                    "SELECT b.*, c.name AS category_name "
                    "FROM books b "
                    "LEFT JOIN categories c ON b.category_id = c.id "
                    "WHERE b.title LIKE %s OR b.author LIKE %s OR b.isbn LIKE %s "
                    "ORDER BY b.title ASC",
                    (search_param, search_param, search_param)
                )
                books = cur.fetchall()
                
            cur.close()
        except Exception as e:
            app.logger.error(f"Error loading landing page data: {str(e)}")
            
        return render_template(
            'landing.html',
            stats=stats,
            arrivals=arrivals,
            books=books,
            search=search
        )

    return app


# ---------------------------------------------------------------------------
# Direct invocation
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
