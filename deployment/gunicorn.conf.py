"""
Gunicorn configuration file – Library Management System.

Usage (standalone):
    gunicorn --config deployment/gunicorn.conf.py 'app:create_app()'

Usage (Docker / systemd):
    Automatically loaded via CMD / ExecStart directives.
"""

import multiprocessing
import os

# =============================================================================
# Server socket
# =============================================================================
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5000")
backlog = 2048

# =============================================================================
# Worker processes
# =============================================================================
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"          # Use 'gevent' or 'eventlet' for async workloads
worker_connections = 1000      # Only relevant for async worker classes
threads = 2                    # Threads per worker (sync class)
max_requests = 1000            # Recycle workers after N requests (prevents leaks)
max_requests_jitter = 50       # Random jitter to avoid thundering-herd restarts

# =============================================================================
# Timeouts
# =============================================================================
timeout = 120                  # Worker silent for >120 s → killed & restarted
graceful_timeout = 30          # Time allowed for a worker to finish after SIGTERM
keepalive = 5                  # Keep-alive duration for client connections (seconds)

# =============================================================================
# Logging
# =============================================================================
accesslog = "-"                # '-' = stdout
errorlog = "-"                 # '-' = stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# =============================================================================
# Process naming
# =============================================================================
proc_name = "library-management-system"

# =============================================================================
# Server mechanics
# =============================================================================
preload_app = True             # Load the app before forking → shares memory
daemon = False                 # Let the supervisor (Docker / systemd) manage the process

# =============================================================================
# Security
# =============================================================================
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# =============================================================================
# Hooks (optional – useful for logging / monitoring)
# =============================================================================
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Gunicorn master starting – Library Management System")


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Gunicorn master forked – new master")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Gunicorn server is ready. Spawning workers…")
