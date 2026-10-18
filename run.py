import os
import sys
import types
import importlib.util

# Explicitly add current directory to Python module search path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Check if 'app' directory exists
app_dir = os.path.join(BASE_DIR, "app")
if os.path.isdir(app_dir):
    from app import create_app
else:
    # Handle flat repository upload on GitHub (where files are in root)
    if "app" not in sys.modules:
        app_pkg = types.ModuleType("app")
        app_pkg.__path__ = [BASE_DIR]
        app_pkg.__file__ = os.path.join(BASE_DIR, "__init__.py")
        sys.modules["app"] = app_pkg

        init_path = os.path.join(BASE_DIR, "__init__.py")
        if os.path.isfile(init_path):
            spec = importlib.util.spec_from_file_location("app", init_path)
            spec.loader.exec_module(app_pkg)

    from app import create_app

# Application instance for Gunicorn WSGI server and Flask CLI
app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development").lower() == "development"
    
    print("============================================================")
    print(f"[*] Campus Lost & Found System starting on http://{host}:{port}")
    print("============================================================")
    
    app.run(host=host, port=port, debug=debug)
