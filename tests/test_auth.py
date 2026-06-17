"""
Tests for authentication routes: login, logout, and access control.

The ``auth`` blueprint is mounted at ``/auth`` (see ``routes/auth.py``).
Flask-Login is configured with ``login_view = 'auth.login'``, so
unauthenticated requests to protected pages redirect to ``/auth/login``.
"""

import pytest
from tests.conftest import login, logout


# ---------------------------------------------------------------------------
# Login page
# ---------------------------------------------------------------------------

class TestLoginPage:
    """Tests related to the login page rendering."""

    def test_login_page_loads(self, client):
        """GET /auth/login should return 200 and render the login form."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"login" in response.data.lower() or b"Login" in response.data

    def test_login_page_contains_form_fields(self, client):
        """The login page should contain username and password fields."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"username" in response.data.lower()
        assert b"password" in response.data.lower()


# ---------------------------------------------------------------------------
# Successful login
# ---------------------------------------------------------------------------

class TestLoginSuccess:
    """Tests for successful authentication."""

    def test_login_success(self, client):
        """POST /auth/login with valid credentials should redirect to the
        dashboard."""
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        # Expect a redirect (302 / 303) toward the dashboard
        assert response.status_code in (302, 303)
        location = response.headers.get("Location", "")
        assert "/dashboard" in location or "/" == location

    def test_login_success_follow_redirect(self, client):
        """After following redirects the user should land on the dashboard
        page."""
        response = login(client)
        assert response.status_code == 200
        # The dashboard page should contain a recognisable keyword
        assert (
            b"dashboard" in response.data.lower()
            or b"Dashboard" in response.data
            or b"welcome" in response.data.lower()
        )


# ---------------------------------------------------------------------------
# Failed login
# ---------------------------------------------------------------------------

class TestLoginFailure:
    """Tests for failed authentication attempts."""

    def test_login_invalid_credentials(self, client):
        """POST /auth/login with wrong password should show an error
        message."""
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": "wrongpassword"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert (
            b"invalid" in response.data.lower()
            or b"incorrect" in response.data.lower()
            or b"error" in response.data.lower()
            or b"failed" in response.data.lower()
        )

    def test_login_invalid_username(self, client):
        """POST /auth/login with a non-existent username should show an
        error."""
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent_user", "password": "admin123"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert (
            b"invalid" in response.data.lower()
            or b"incorrect" in response.data.lower()
            or b"error" in response.data.lower()
            or b"not found" in response.data.lower()
        )

    def test_login_empty_fields(self, client):
        """POST /auth/login with empty username and password should not
        authenticate."""
        response = client.post(
            "/auth/login",
            data={"username": "", "password": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # User should remain on the login page (not the dashboard)
        assert (
            b"login" in response.data.lower()
            or b"required" in response.data.lower()
            or b"error" in response.data.lower()
        )

    def test_login_empty_username(self, client):
        """POST /auth/login with only a password should fail."""
        response = client.post(
            "/auth/login",
            data={"username": "", "password": "admin123"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"dashboard" not in response.data.lower()

    def test_login_empty_password(self, client):
        """POST /auth/login with only a username should fail."""
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"dashboard" not in response.data.lower()


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogout:
    """Tests for the logout flow."""

    def test_logout(self, client):
        """After login, GET /auth/logout should redirect the user to the
        login page."""
        login(client)
        response = client.get("/auth/logout", follow_redirects=False)
        assert response.status_code in (302, 303)
        assert "/login" in response.headers.get("Location", "")

    def test_logout_follow_redirect(self, client):
        """After logout the user should see the login page again."""
        login(client)
        response = logout(client)
        assert response.status_code == 200
        assert b"login" in response.data.lower()

    def test_logout_clears_session(self, client):
        """After logout, accessing a protected route should redirect to
        login."""
        login(client)
        logout(client)

        response = client.get("/dashboard/", follow_redirects=False)
        assert response.status_code in (302, 303)
        location = response.headers.get("Location", "")
        assert "/login" in location


# ---------------------------------------------------------------------------
# Protected routes
# ---------------------------------------------------------------------------

class TestProtectedRoutes:
    """Tests that protected pages redirect unauthenticated users."""

    @pytest.mark.parametrize(
        "route",
        [
            "/dashboard/",
            "/books/",
            "/students/",
            "/issues/",
        ],
    )
    def test_protected_route_redirect(self, client, route):
        """GET <protected route> without login should redirect to
        /auth/login."""
        response = client.get(route, follow_redirects=False)
        assert response.status_code in (302, 303, 401)
        if response.status_code in (302, 303):
            assert "/login" in response.headers.get("Location", "")

    def test_dashboard_accessible_after_login(self, client):
        """GET /dashboard/ after login should return 200."""
        login(client)
        response = client.get("/dashboard/")
        assert response.status_code == 200
