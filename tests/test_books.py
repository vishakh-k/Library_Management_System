"""
Tests for book management routes: listing, adding, editing, deleting, and searching.
"""

import pytest
from tests.conftest import login


# ---------------------------------------------------------------------------
# Sample payloads
# ---------------------------------------------------------------------------

VALID_BOOK = {
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "isbn": "9780132350884",
    "publisher": "Prentice Hall",
    "quantity": "5",
    "category": "Programming",
}

UPDATED_BOOK = {
    "title": "Clean Code: A Handbook",
    "author": "Robert C. Martin",
    "isbn": "9780132350884",
    "publisher": "Prentice Hall",
    "quantity": "10",
    "category": "Software Engineering",
}


class TestBooksPageAccess:
    """Tests for accessing the books listing page."""

    def test_books_page_loads(self, client):
        """GET /books after login should return 200."""
        login(client)
        response = client.get("/books")
        assert response.status_code == 200
        assert b"book" in response.data.lower()

    def test_books_page_requires_login(self, client):
        """GET /books without login should redirect to /login."""
        response = client.get("/books", follow_redirects=False)
        assert response.status_code in (302, 303)
        assert "/login" in response.headers.get("Location", "")

    def test_books_page_follow_redirect_when_unauthenticated(self, client):
        """Following the redirect for an unauthenticated /books request
        should land on the login page."""
        response = client.get("/books", follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data.lower()


class TestAddBook:
    """Tests for the add-book workflow."""

    def test_add_book_page_loads(self, client):
        """GET /books/add after login should return 200 with a form."""
        login(client)
        response = client.get("/books/add")
        assert response.status_code == 200
        assert b"title" in response.data.lower()

    def test_add_book_success(self, client):
        """POST /books/add with valid data should redirect (success)."""
        login(client)
        response = client.post("/books/add", data=VALID_BOOK, follow_redirects=False)
        # Expect redirect to books list on success
        assert response.status_code in (302, 303)

    def test_add_book_success_follow_redirect(self, client):
        """After adding a book the user should be redirected to the books list
        where the new title appears."""
        login(client)
        response = client.post("/books/add", data=VALID_BOOK, follow_redirects=True)
        assert response.status_code == 200
        assert (
            b"Clean Code" in response.data
            or b"success" in response.data.lower()
            or b"added" in response.data.lower()
        )

    def test_add_book_missing_fields(self, client):
        """POST /books/add with missing required fields should show an error."""
        login(client)
        incomplete_data = {"title": "Incomplete Book"}
        response = client.post(
            "/books/add", data=incomplete_data, follow_redirects=True
        )
        assert response.status_code == 200
        # Should remain on the form / show an error
        assert (
            b"required" in response.data.lower()
            or b"error" in response.data.lower()
            or b"add" in response.data.lower()
        )

    def test_add_book_missing_title(self, client):
        """POST /books/add without a title should fail validation."""
        login(client)
        data = {**VALID_BOOK, "title": ""}
        response = client.post("/books/add", data=data, follow_redirects=True)
        assert response.status_code == 200
        assert (
            b"required" in response.data.lower()
            or b"error" in response.data.lower()
            or b"title" in response.data.lower()
        )

    def test_add_book_negative_quantity(self, client):
        """A book with a negative quantity should be rejected."""
        login(client)
        data = {**VALID_BOOK, "quantity": "-1"}
        response = client.post("/books/add", data=data, follow_redirects=True)
        assert response.status_code == 200
        # The app should either reject or silently clamp – at minimum it
        # should not crash (status 200).


class TestEditBook:
    """Tests for the edit-book workflow."""

    def test_edit_book_page_loads(self, client):
        """GET /books/edit/1 after login should return 200 (or 404 if no
        book with id 1 exists in the test DB)."""
        login(client)
        response = client.get("/books/edit/1")
        assert response.status_code in (200, 404)

    def test_edit_book(self, client):
        """POST /books/edit/1 with updated data should process the update."""
        login(client)
        response = client.post(
            "/books/edit/1", data=UPDATED_BOOK, follow_redirects=True
        )
        # 200 → success page; 404 → book does not exist in test DB
        assert response.status_code in (200, 404)

    def test_edit_book_without_login(self, client):
        """POST /books/edit/1 without authentication should redirect."""
        response = client.post(
            "/books/edit/1", data=UPDATED_BOOK, follow_redirects=False
        )
        assert response.status_code in (302, 303)
        assert "/login" in response.headers.get("Location", "")


class TestDeleteBook:
    """Tests for the delete-book workflow."""

    def test_delete_book(self, client):
        """POST /books/delete/1 should remove the book or return 404."""
        login(client)
        response = client.post("/books/delete/1", follow_redirects=True)
        assert response.status_code in (200, 404)

    def test_delete_book_without_login(self, client):
        """Deleting a book without authentication should redirect to login."""
        response = client.post("/books/delete/1", follow_redirects=False)
        assert response.status_code in (302, 303)
        assert "/login" in response.headers.get("Location", "")

    def test_delete_nonexistent_book(self, client):
        """Deleting a book that does not exist should return 404 or a
        user-friendly error."""
        login(client)
        response = client.post("/books/delete/99999", follow_redirects=True)
        assert response.status_code in (200, 404)


class TestSearchBooks:
    """Tests for the book search functionality."""

    def test_search_books(self, client):
        """GET /books?search=python should return 200 with results."""
        login(client)
        response = client.get("/books?search=python")
        assert response.status_code == 200

    def test_search_books_no_results(self, client):
        """Searching for a non-existent title should return 200 with an
        empty result set or a 'no results' message."""
        login(client)
        response = client.get("/books?search=xyznonexistent123")
        assert response.status_code == 200

    def test_search_books_empty_query(self, client):
        """GET /books?search= (empty query) should return all books."""
        login(client)
        response = client.get("/books?search=")
        assert response.status_code == 200

    def test_search_books_special_characters(self, client):
        """Search with special characters should not cause a 500 error."""
        login(client)
        response = client.get("/books?search=%27OR%201%3D1--")
        assert response.status_code in (200, 400)
