# Bind to all interfaces on port 8000
bind = "0.0.0.0:8000"

# Calculate the number of workers based on available CPU cores
workers = 1

# Use Uvicorn's worker class for ASGI applications
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout (in seconds) for worker processes before they're killed and restarted
timeout = 30

# Logging settings:
loglevel = "info"
accesslog = "-"  # Logs access messages to stdout
errorlog = "-"  # Logs error messages to stderr
