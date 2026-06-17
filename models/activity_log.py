"""ActivityLog model – audit trail for user actions."""


class ActivityLog:
    """Encapsulates all activity-log-related database operations."""

    @staticmethod
    def log(mysql, user_id, action, entity_type=None, entity_id=None,
            details=None, ip_address=None):
        """Insert an activity log entry.

        Parameters
        ----------
        mysql : Flask-MySQLdb extension instance
        user_id : int or None
        action : str – short verb, e.g. ``'create_book'``, ``'login'``
        entity_type : str or None – e.g. ``'book'``, ``'student'``
        entity_id : int or None
        details : str or None – free-form description
        ip_address : str or None
        """
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO activity_logs "
            "(user_id, action, entity_type, entity_id, details, ip_address) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, action, entity_type, entity_id, details, ip_address),
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_recent(mysql, limit=20):
        """Return the most recent *limit* log entries, with the username
        of the acting user.
        """
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT al.*, u.username "
            "FROM activity_logs al "
            "LEFT JOIN users u ON al.user_id = u.id "
            "ORDER BY al.created_at DESC "
            "LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def get_all(mysql, page=1, per_page=50):
        """Return a paginated list of log entries.

        Returns a dict with keys ``items``, ``page``, ``per_page``,
        ``total``, and ``pages``.
        """
        cur = mysql.connection.cursor()

        # Total count
        cur.execute("SELECT COUNT(*) AS cnt FROM activity_logs")
        total = cur.fetchone()['cnt']

        # Calculate offset
        offset = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page  # ceiling division

        cur.execute(
            "SELECT al.*, u.username "
            "FROM activity_logs al "
            "LEFT JOIN users u ON al.user_id = u.id "
            "ORDER BY al.created_at DESC "
            "LIMIT %s OFFSET %s",
            (per_page, offset),
        )
        items = cur.fetchall()
        cur.close()

        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
        }

    def __repr__(self):
        return "<ActivityLog>"
