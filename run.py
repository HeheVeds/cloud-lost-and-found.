import os
import sys

# Explicitly add current directory to Python module search path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from app import create_app
except ModuleNotFoundError:
    # If app directory was uploaded flat or into a different subpath
    if os.path.exists(os.path.join(BASE_DIR, "cloud-lost-and-found", "app")):
        sys.path.insert(0, os.path.join(BASE_DIR, "cloud-lost-and-found"))
        from app import create_app
    else:
        raise

# Application instance for Gunicorn WSGI server and Flask CLI
app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development").lower() == "development"
    
    print("============================================================")
    print(f"[*] Campus Lost & Found System starting on http://{host}:{port}")
    print(f"[*] Access Cloud Diagnostics at: http://{host}:{port}/cloud-info")
    print("============================================================")
    
    app.run(host=host, port=port, debug=debug)
