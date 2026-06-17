"""Category model with basic CRUD operations."""


class Category:
    """Encapsulates all category-related database operations."""

    @staticmethod
    def get_all(mysql):
        """Return all categories ordered by name."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categories ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_by_id(mysql, category_id):
        """Return a single category dict or ``None``."""
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def create(mysql, name, description=None):
        """Insert a new category. Returns the new row id."""
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO categories (name, description) VALUES (%s, %s)",
            (name, description),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
        return new_id

    @staticmethod
    def update(mysql, category_id, name, description=None):
        """Update an existing category."""
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE categories SET name = %s, description = %s WHERE id = %s",
            (name, description, category_id),
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def delete(mysql, category_id):
        """Delete a category by *category_id*."""
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        mysql.connection.commit()
        cur.close()

    def __repr__(self):
        return "<Category>"
