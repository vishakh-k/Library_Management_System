"""Category management routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import mysql
from models.category import Category

categories_bp = Blueprint('categories', __name__, url_prefix='/categories')

@categories_bp.before_request
@login_required
def limit_to_admin():
    if current_user.role != 'admin':
        abort(403)

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

@categories_bp.route('/', endpoint='list_categories')
@login_required
def index():
    """List all categories."""
    try:
        categories = Category.get_all(mysql)
        return render_template('categories/list.html', categories=categories)
    except Exception as e:
        flash(f"Error loading categories: {e}", "danger")
        return render_template('categories/list.html', categories=[])

@categories_bp.route('/add', methods=['GET', 'POST'], endpoint='add_category')
@login_required
def add():
    """Add a category."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip() or None

        if not name:
            flash("Category name is required.", "danger")
            return render_template('categories/add.html', category=request.form)

        try:
            category_id = Category.create(mysql, name, description)
            _log_activity('CREATE', 'category', category_id, f"Added category: {name}")
            flash("Category added successfully!", "success")
            return redirect(url_for('categories.list_categories'))
        except Exception as e:
            flash(f"Error creating category: {e}", "danger")
            return render_template('categories/add.html', category=request.form)

    return render_template('categories/add.html', category=None)

@categories_bp.route('/edit/<int:id>', methods=['GET', 'POST'], endpoint='edit_category')
@login_required
def edit(id):
    """Edit a category."""
    try:
        category = Category.get_by_id(mysql, id)
        if not category:
            flash("Category not found.", "danger")
            return redirect(url_for('categories.list_categories'))
    except Exception as e:
        flash(f"Error loading category: {e}", "danger")
        return redirect(url_for('categories.list_categories'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip() or None

        if not name:
            flash("Category name is required.", "danger")
            return render_template('categories/add.html', category=category)

        try:
            Category.update(mysql, id, name, description)
            _log_activity('UPDATE', 'category', id, f"Updated category: {name}")
            flash("Category updated successfully!", "success")
            return redirect(url_for('categories.list_categories'))
        except Exception as e:
            flash(f"Error updating category: {e}", "danger")
            return render_template('categories/add.html', category=category)

    return render_template('categories/add.html', category=category)

@categories_bp.route('/delete/<int:id>', methods=['POST'], endpoint='delete_category')
@login_required
def delete(id):
    """Delete a category."""
    try:
        category = Category.get_by_id(mysql, id)
        if not category:
            flash("Category not found.", "danger")
            return redirect(url_for('categories.list_categories'))

        Category.delete(mysql, id)
        _log_activity('DELETE', 'category', id, f"Deleted category: {category['name']}")
        flash("Category deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting category: {e}", "danger")

    return redirect(url_for('categories.list_categories'))
