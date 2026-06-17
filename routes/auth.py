"""Authentication routes for login and logout."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from extensions import mysql
from models.user import User
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle admin/user login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = True if request.form.get('remember') else False

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')

        try:
            user = User.get_by_username(mysql, username)
            if user and User.verify_password(user.password_hash, password):
                login_user(user, remember=remember)
                flash('Welcome back, ' + user.username + '!', 'success')
                next_page = request.args.get('next')
                if user.role == 'admin':
                    return redirect(next_page or url_for('dashboard.index'))
                else:
                    return redirect(next_page or url_for('store.list_books'))
            else:
                flash('Invalid username or password.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle customer sign up."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not username or not email or not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        try:
            cur = mysql.connection.cursor()
            
            # Check if username or email already exists
            cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            if cur.fetchone():
                flash('Username or email already exists.', 'danger')
                cur.close()
                return render_template('register.html')
            
            # Create user (role = 'user' by default for registration)
            password_hash = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (username, email, password_hash, role) "
                "VALUES (%s, %s, %s, %s)",
                (username, email, password_hash, 'user'),
            )
            mysql.connection.commit()
            cur.close()
            
            flash('Registration successful! Please sign in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('register.html')
