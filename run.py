import os
from app import create_app

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
