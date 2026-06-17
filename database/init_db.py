"""
Database initialisation script.

Reads schema.sql, creates tables, and seeds the database with a default
admin user and starter categories.

Usage:
    python database/init_db.py
"""

import os
import sys
import time

import MySQLdb
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Ensure the project root is on sys.path so dotenv finds .env
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


def get_connection():
    """Create a raw MySQL connection using environment variables with retries."""
    retries = 15
    for attempt in range(1, retries + 1):
        try:
            return MySQLdb.connect(
                host=os.environ.get('MYSQL_HOST', 'localhost'),
                user=os.environ.get('MYSQL_USER', 'root'),
                passwd=os.environ.get('MYSQL_PASSWORD', 'password'),
                port=int(os.environ.get('MYSQL_PORT', 3306)),
                charset='utf8mb4',
            )
        except MySQLdb.OperationalError as exc:
            if attempt == retries:
                print(f"[error] Failed to connect to MySQL after {retries} attempts: {exc}")
                raise
            print(f"[init] MySQL not ready yet (attempt {attempt}/{retries}). Waiting 2s...")
            time.sleep(2)


def execute_schema(cursor, schema_path):
    """Read and execute every statement in schema.sql."""
    with open(schema_path, 'r', encoding='utf-8') as fh:
        sql = fh.read()

    # Split on semicolons and execute each statement individually
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    for statement in statements:
        cursor.execute(statement)


def seed_admin(cursor):
    """Insert a default admin user if one does not already exist."""
    cursor.execute("SELECT id FROM users WHERE username = %s", ('admin',))
    if cursor.fetchone():
        print("[seed] Admin user already exists – skipping.")
        return

    password_hash = generate_password_hash('admin123')
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, role) "
        "VALUES (%s, %s, %s, %s)",
        ('admin', 'admin@library.com', password_hash, 'admin'),
    )
    print("[seed] Default admin user created (username=admin, password=admin123).")


def seed_categories(cursor):
    """Insert default book categories if the table is empty."""
    cursor.execute("SELECT COUNT(*) AS cnt FROM categories")
    row = cursor.fetchone()
    count = row['cnt'] if isinstance(row, dict) else row[0]

    if count > 0:
        print("[seed] Categories already seeded – skipping.")
        return

    default_categories = [
        ('Fiction', 'Fictional works including novels and short stories'),
        ('Non-Fiction', 'Non-fictional works including essays and biographies'),
        ('Science', 'Books on physics, chemistry, biology and other sciences'),
        ('Technology', 'Books on computing, engineering and technology'),
        ('History', 'Historical texts and analyses'),
        ('Mathematics', 'Mathematics textbooks and references'),
        ('Literature', 'Classic and modern literary works'),
        ('Reference', 'Dictionaries, encyclopedias and reference material'),
    ]

    cursor.executemany(
        "INSERT INTO categories (name, description) VALUES (%s, %s)",
        default_categories,
    )
    print(f"[seed] Inserted {len(default_categories)} default categories.")


def init_db():
    """Main initialisation routine."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')

    if not os.path.exists(schema_path):
        print(f"[error] Schema file not found: {schema_path}")
        sys.exit(1)

    conn = get_connection()
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)

        # Ensure we create and use the right database
        db_name = os.environ.get('MYSQL_DB', 'library_db')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")

        print("[init] Executing schema.sql …")
        execute_schema(cursor, schema_path)
        conn.commit()

        print("[init] Seeding default data …")
        seed_admin(cursor)
        seed_categories(cursor)
        conn.commit()

        print("[init] Database initialisation complete [OK]")
    except MySQLdb.Error as exc:
        conn.rollback()
        print(f"[error] MySQL error: {exc}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
