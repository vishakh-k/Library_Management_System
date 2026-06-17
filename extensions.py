"""Shared Flask extensions — imported by app.py and route modules.

Instantiate extensions here (without an app) to avoid circular imports.
In app.py call ``mysql.init_app(app)`` and ``login_manager.init_app(app)``.
"""

from flask_mysqldb import MySQL
from flask_login import LoginManager

mysql = MySQL()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'
