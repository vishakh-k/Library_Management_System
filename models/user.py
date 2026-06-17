"""User model with Flask-Login integration."""

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin):
    """Represents an application user (admin / librarian).

    Instances are hydrated from database rows and are compatible with
    Flask-Login's ``UserMixin`` interface.
    """

    def __init__(self, id, username, email, password_hash, role='admin',
                 created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at

    # ------------------------------------------------------------------
    # Static query helpers – every method accepts the ``mysql`` connection
    # object provided by Flask-MySQLdb.
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_id(mysql, user_id):
        """Return a ``User`` instance for the given *user_id*, or ``None``."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=row['role'],
            created_at=row.get('created_at'),
        )

    @staticmethod
    def get_by_username(mysql, username):
        """Return a ``User`` for the given *username*, or ``None``."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=row['role'],
            created_at=row.get('created_at'),
        )

    @staticmethod
    def get_by_email(mysql, email):
        """Return a ``User`` for the given *email*, or ``None``."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=row['role'],
            created_at=row.get('created_at'),
        )

    @staticmethod
    def create(mysql, username, email, password):
        """Create a new user with a hashed *password*.

        Returns the auto-generated row id.
        """
        hashed = generate_password_hash(password)
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password_hash, role) "
            "VALUES (%s, %s, %s, %s)",
            (username, email, hashed, 'admin'),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
        return new_id

    @staticmethod
    def verify_password(password_hash, password):
        """Verify a plaintext *password* against the stored hash."""
        return check_password_hash(password_hash, password)

    @staticmethod
    def get_all(mysql):
        """Return a list of all users as ``User`` instances."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cur.fetchall()
        cur.close()
        return [
            User(
                id=r['id'],
                username=r['username'],
                email=r['email'],
                password_hash=r['password_hash'],
                role=r['role'],
                created_at=r.get('created_at'),
            )
            for r in rows
        ]

    def __repr__(self):
        return f"<User {self.username!r}>"
