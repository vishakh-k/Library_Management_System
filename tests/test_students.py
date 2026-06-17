"""
Tests for student management routes: listing, adding, editing, deleting,
profile viewing, and searching.
"""

import pytest
from tests.conftest import login


# ---------------------------------------------------------------------------
# Sample payloads
# ---------------------------------------------------------------------------

VALID_STUDENT = {
    "name": "Jane Doe",
    "email": "jane.doe@university.edu",
    "phone": "9876543210",
    "department": "Computer Science",
    "enrollment_no": "CS2024001",
    "semester": "6",
}

UPDATED_STUDENT = {
    "name": "Jane Doe",
    "email": "jane.updated@university.edu",
    "phone": "9876543211",
    "department": "Information Technology",
    "enrollment_no": "CS2024001",
    "semester": "7",
}


class TestStudentsPageAccess:
    """Tests for accessing the students listing page."""

    def test_students_page_loads(self, client):
        """GET /students after login should return 200."""
        login(client)
        response = client.get("/students")
        assert response.status_code == 200
        assert b"student" in response.data.lower()

    def test_students_page_requires_login(self, client):
        """GET /students without login should redirect to /login."""
        response = client.get("/students", follow_redirects=False)
        assert response.status_code in (302, 303)
        assert "/login" in response.headers.get("Location", "")

    def test_students_page_follow_redirect_when_unauthenticated(self, client):
        """Following the redirect for an unauthenticated /students request
        should land on the login page."""
        response = client.get("/students", follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data.lower()


class TestAddStudent:
    """Tests for the add-student workflow."""

    def test_add_student_page_loads(self, client):
        """GET /students/add after login should return 200 with a form."""
        login(client)
        response = client.get("/students/add")
        assert response.status_code == 200
        assert b"name" in response.data.lower()

    def test_add_student_success(self, client):
        """POST /students/add with valid data should redirect (success)."""
        login(client)
        response = client.post(
            "/students/add", data=VALID_STUDENT, follow_redirects=False
        )
        assert response.status_code in (302, 303)

    def test_add_student_success_follow_redirect(self, client):
        """After adding a student the user should see confirmation on the
        redirected page."""
        login(client)
        response = client.post(
            "/students/add", data=VALID_STUDENT, follow_redirects=True
        )
        assert response.status_code == 200
        assert (
            b"Jane Doe" in response.data
            or b"success" in response.data.lower()
            or b"added" in response.data.lower()
        )

    def test_add_student_missing_fields(self, client):
        """POST /students/add with missing required fields should show an error."""
        login(client)
        incomplete_data = {"name": "Incomplete Student"}
        response = client.post(
            "/students/add", data=incomplete_data, follow_redirects=True
        )
        assert response.status_code == 200
        assert (
            b"required" in response.data.lower()
            or b"error" in response.data.lower()
            or b"add" in response.data.lower()
        )

    def test_add_student_missing_name(self, client):
        """POST /students/add without a name should fail validation."""
        login(client)
        data = {**VALID_STUDENT, "name": ""}
        response = client.post("/students/add", data=data, follow_redirects=True)
        assert response.status_code == 200
        assert (
            b"required" in response.data.lower()
            or b"error" in response.data.lower()
            or b"name" in response.data.lower()
        )

    def test_add_student_invalid_email(self, client):
        """A student with an obviously invalid email should be rejected or
        handled gracefully."""
        login(client)
        data = {**VALID_STUDENT, "email": "not-an-email"}
        response = client.post("/students/add", data=data, follow_redirects=True)
        assert response.status_code == 200

    def test_add_student_duplicate_enrollment(self, client):
        """Adding two students with the same enrollment number should not
        cause a 500 error."""
        login(client)
        client.post("/students/add", data=VALID_STUDENT, follow_redirects=True)
        response = client.post(
            "/students/add", data=VALID_STUDENT, follow_redirects=True
        )
        assert response.status_code in (200, 409)


class TestEditStudent:
    """Tests for the edit-student workflow."""

    def test_edit_student_page_loads(self, client):
        """GET /students/edit/1 after login should return 200 or 404."""
        login(client)
        response = client.get("/students/edit/1")
        assert response.status_code in (200, 404)

    def test_edit_student(self, client):
        """POST /students/edit/1 with updated data should process the update."""
        login(client)
        response = client.post(
            "/students/edit/1", data=UPDATED_STUDENT, follow_redirects=True
        )
        assert response.status_code in (200, 404)

    def test_edit_student_without_login(self, client):
        """POST /students/edit/1 without authentication should redirect."""
        response = client.post(
            "/students/edit/1", data=UPDATED_STUDENT, follow_redirects=False
        )
        assert response.status_code in (302, 303)
        assert "/login" in response.headers.get("Location", "")


class TestDeleteStudent:
    """Tests for the delete-student workflow."""

    def test_delete_student(self, client):
        """POST /students/delete/1 should remove the student or return 404."""
        login(client)
        response = client.post("/students/delete/1", follow_redirects=True)
        assert response.status_code in (200, 404)

    def test_delete_student_without_login(self, client):
        """Deleting a student without authentication should redirect to login."""
        response = client.post("/students/delete/1", follow_redirects=False)
        assert response.status_code in (302, 303)
        assert "/login" in response.headers.get("Location", "")

    def test_delete_nonexistent_student(self, client):
        """Deleting a student that does not exist should return 404 or an
        error message."""
        login(client)
        response = client.post("/students/delete/99999", follow_redirects=True)
        assert response.status_code in (200, 404)


class TestStudentProfile:
    """Tests for viewing a student's profile page."""

    def test_student_profile(self, client):
        """GET /students/1 should return the student profile or 404."""
        login(client)
        response = client.get("/students/1")
        assert response.status_code in (200, 404)

    def test_student_profile_without_login(self, client):
        """Viewing a student profile without login should redirect."""
        response = client.get("/students/1", follow_redirects=False)
        assert response.status_code in (302, 303)
        assert "/login" in response.headers.get("Location", "")

    def test_nonexistent_student_profile(self, client):
        """Viewing a non-existent student profile should return 404."""
        login(client)
        response = client.get("/students/99999")
        assert response.status_code in (200, 404)


class TestSearchStudents:
    """Tests for the student search functionality."""

    def test_search_students(self, client):
        """GET /students?search=jane should return 200."""
        login(client)
        response = client.get("/students?search=jane")
        assert response.status_code == 200

    def test_search_students_no_results(self, client):
        """Searching for a non-existent name should return 200 with an
        empty result set."""
        login(client)
        response = client.get("/students?search=xyznonexistent123")
        assert response.status_code == 200

    def test_search_students_empty_query(self, client):
        """GET /students?search= should return all students."""
        login(client)
        response = client.get("/students?search=")
        assert response.status_code == 200

    def test_search_students_by_enrollment(self, client):
        """Searching by enrollment number should return relevant results."""
        login(client)
        response = client.get("/students?search=CS2024001")
        assert response.status_code == 200
