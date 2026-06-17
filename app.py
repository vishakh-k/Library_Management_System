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
        """Redirect the bare root based on role."""
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('store.list_books'))
        return redirect(url_for('auth.login'))

    return app


# ---------------------------------------------------------------------------
# Direct invocation
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
