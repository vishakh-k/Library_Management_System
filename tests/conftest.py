"""
Shared fixtures and helper functions for Library Management System tests.

This module provides:
  - A Flask application fixture configured for testing.
  - A test client fixture for making HTTP requests.
  - A CLI runner fixture for testing CLI commands.
  - Helper functions for login/logout flows.
"""

import pytest
import sys
import os

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that ``from app import …`` works
# regardless of how pytest is invoked.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402


# ---------------------------------------------------------------------------
# Application & client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """Create and configure a new Flask app instance for each test."""
    app = create_app("testing")
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "MYSQL_DB": "library_test_db",
        }
    )
    yield app


@pytest.fixture
def client(app):
    """A Flask test client.  Tests that need to make HTTP requests should
    use this fixture."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A Flask test CLI runner for testing management commands."""
    return app.test_cli_runner()


# ---------------------------------------------------------------------------
# Auth helpers (importable by test modules)
# ---------------------------------------------------------------------------

def login(client, username="admin", password="admin123"):
    """Perform a login via POST and follow redirects.

    The auth blueprint is mounted at ``/auth``, so login lives at
    ``/auth/login``.

    Returns the response object so callers can make assertions on it.
    """
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def logout(client):
    """Perform a logout via GET and follow redirects."""
    return client.get("/auth/logout", follow_redirects=True)


@pytest.fixture(autouse=True)
def clean_db(app):
    """Clean and seed database before each test."""
    from extensions import mysql
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        cur.execute("TRUNCATE TABLE issued_books")
        cur.execute("TRUNCATE TABLE books")
        cur.execute("TRUNCATE TABLE students")
        cur.execute("TRUNCATE TABLE users")
        cur.execute("TRUNCATE TABLE activity_logs")
        cur.execute("TRUNCATE TABLE categories")
        cur.execute("TRUNCATE TABLE purchases")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        mysql.connection.commit()
        
        from database.init_db import seed_admin, seed_categories
        seed_admin(cur)
        seed_categories(cur)
        mysql.connection.commit()
        cur.close()
