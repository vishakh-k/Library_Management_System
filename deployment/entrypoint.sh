#!/bin/sh
set -e

echo "🐳 Starting entrypoint script..."

# Run database migrations/initialization
echo "🛠️ Initializing database..."
python database/init_db.py

# Execute the main container command
echo "🚀 Starting application..."
exec "$@"
