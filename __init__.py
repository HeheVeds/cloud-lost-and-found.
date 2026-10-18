import os
from flask import Flask, send_file, send_from_directory
from flask_login import LoginManager
from app.config import Config
from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message = "Please sign in to access this page."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_app(config_class=Config):
    # Dynamically detect template and static directories (supports both flat and nested GitHub layouts)
    base = os.path.dirname(os.path.abspath(__file__))
    tmpl_dir = os.path.join(base, "templates")
    if not os.path.isdir(tmpl_dir):
        tmpl_dir = base
        
    static_dir = os.path.join(base, "static")
    if not os.path.isdir(static_dir):
        static_dir = base

    app = Flask(__name__, template_folder=tmpl_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # Static file fallback routes for flat repository uploads
    @app.route("/static/css/style.css")
    def _serve_css():
        nested = os.path.join(app.static_folder, "css", "style.css")
        if os.path.isfile(nested):
            return send_file(nested)
        return send_from_directory(app.static_folder, "style.css")

    @app.route("/static/js/main.js")
    def _serve_js():
        nested = os.path.join(app.static_folder, "js", "main.js")
        if os.path.isfile(nested):
            return send_file(nested)
        return send_from_directory(app.static_folder, "main.js")

    # Ensure upload folder exists for local storage fallback
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Auto-create tables and default admin if needed
    with app.app_context():
        try:
            db_engine = app.config.get("DB_ENGINE_TYPE", "SQLite")
            print(f"\n" + "="*50)
            print(f" ACTIVE DATABASE: {db_engine}")
            if "postgres" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
                print(f" CLOUD STATUS   : CONNECTED TO CLOUD DATABASE (AWS NEON)")
            print("="*50 + "\n")
            db.create_all()
            # Seed default admin if no admin exists
            admin_user = User.query.filter_by(role="admin").first()
            if not admin_user:
                default_admin = User(
                    name="Campus Administrator",
                    email="admin@campus.edu",
                    role="admin"
                )
                default_admin.set_password("admin123")
                db.session.add(default_admin)
                db.session.commit()
                print("[SYSTEM INIT] Created default admin account: admin@campus.edu / admin123")
        except Exception as e:
            print(f"[DB INIT ERROR] Could not initialize tables: {e}")

    return app
