"""Tests for public storefront, registration, and purchase features."""

import pytest
from extensions import mysql
from tests.conftest import login, logout

def register_customer(client, username="customer", email="customer@example.com", password="customer123"):
    return client.post(
        "/auth/register",
        data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password
        },
        follow_redirects=True
    )

def test_registration_flow(client, app):
    """Test user registration page and user creation."""
    # 1. Page loads
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert b"sign up" in response.data.lower() or b"register" in response.data.lower()

    # 2. Successful registration
    response = register_customer(client)
    assert response.status_code == 200
    assert b"successful" in response.data.lower() or b"login" in response.data.lower()

    # 3. Verify user exists in DB and has role = 'user'
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = 'customer'")
        user = cur.fetchone()
        cur.close()
        assert user is not None
        assert user['role'] == 'user'

def test_registration_password_mismatch(client):
    """Test registration failure when passwords don't match."""
    response = client.post(
        "/auth/register",
        data={
            "username": "mismatch",
            "email": "mismatch@example.com",
            "password": "password123",
            "confirm_password": "different_password"
        },
        follow_redirects=True
    )
    assert b"do not match" in response.data.lower()

def test_login_redirection_by_role(client):
    """Test role-based login redirects."""
    # 1. Admin login redirects to dashboard
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False
    )
    assert response.status_code in (302, 303)
    assert "/dashboard" in response.headers.get("Location", "")

    # 2. Customer login redirects to store
    register_customer(client, username="customer2", email="customer2@example.com")
    response = client.post(
        "/auth/login",
        data={"username": "customer2", "password": "customer123"},
        follow_redirects=False
    )
    assert response.status_code in (302, 303)
    assert "/store" in response.headers.get("Location", "")

def test_unauthorized_user_access_to_admin_pages(client):
    """Verify that a customer user gets a 403 on admin routes."""
    # Register and login as customer
    register_customer(client)
    login(client, username="customer", password="customer123")

    # Try admin routes
    for route in ["/dashboard/", "/books/", "/students/", "/issues/", "/reports/", "/categories/"]:
        response = client.get(route)
        assert response.status_code == 403

def test_store_catalog_listing(client, app):
    """Test store page displaying books."""
    # Seed a book
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM categories LIMIT 1")
        cat_id = cur.fetchone()['id']
        cur.execute(
            "INSERT INTO books (title, author, isbn, category_id, quantity, available, price) "
            "VALUES ('Test Novel', 'John Doe', '1234567890123', %s, 10, 8, 299.00)",
            (cat_id,)
        )
        mysql.connection.commit()
        cur.close()

    # Login as customer
    register_customer(client)
    login(client, username="customer", password="customer123")

    # Access catalog
    response = client.get("/store/")
    assert response.status_code == 200
    assert b"Test Novel" in response.data
    assert b"John Doe" in response.data
    assert b"299.00" in response.data

def test_purchase_flow(client, app):
    """Test checking out a book and verifying quantity changes & transaction logs."""
    # Seed a book
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM categories LIMIT 1")
        cat_id = cur.fetchone()['id']
        cur.execute(
            "INSERT INTO books (title, author, isbn, category_id, quantity, available, price) "
            "VALUES ('Buyable Book', 'Jane Smith', '9876543210123', %s, 5, 5, 500.00)",
            (cat_id,)
        )
        mysql.connection.commit()
        book_id = cur.lastrowid
        cur.close()

    # Login as customer
    register_customer(client)
    login(client, username="customer", password="customer123")

    # 1. View buy page
    response = client.get(f"/store/buy/{book_id}")
    assert response.status_code == 200
    assert b"Buyable Book" in response.data

    # 2. Checkout 2 copies
    response = client.post(
        f"/store/checkout/{book_id}",
        data={"quantity": "2"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"successfully" in response.data.lower()

    # 3. Verify book quantity reduced by 2
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT available FROM books WHERE id = %s", (book_id,))
        available = cur.fetchone()['available']
        
        # Verify purchase was recorded
        cur.execute("SELECT * FROM purchases WHERE book_id = %s", (book_id,))
        purchase = cur.fetchone()
        cur.close()
        
        assert available == 3
        assert purchase is not None
        assert purchase['quantity'] == 2
        assert float(purchase['price_paid']) == 1000.00

    # 4. Access my purchases page
    response = client.get("/store/my-purchases")
    assert response.status_code == 200
    assert b"Buyable Book" in response.data
    assert b"1000.00" in response.data

def test_purchase_insufficient_stock(client, app):
    """Test purchase failure when stock is insufficient."""
    # Seed a book
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM categories LIMIT 1")
        cat_id = cur.fetchone()['id']
        cur.execute(
            "INSERT INTO books (title, author, isbn, category_id, quantity, available, price) "
            "VALUES ('Limited Book', 'Author', '9876543210999', %s, 1, 1, 100.00)",
            (cat_id,)
        )
        mysql.connection.commit()
        book_id = cur.lastrowid
        cur.close()

    # Login as customer
    register_customer(client)
    login(client, username="customer", password="customer123")

    # Checkout 2 copies (only 1 available)
    response = client.post(
        f"/store/checkout/{book_id}",
        data={"quantity": "2"},
        follow_redirects=True
    )
    assert b"not enough stock" in response.data.lower()
