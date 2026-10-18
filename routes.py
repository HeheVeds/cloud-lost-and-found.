import os
import socket
import platform
from datetime import datetime, date
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Item
from app.s3_storage import save_image_file, test_s3_connection

main_bp = Blueprint("main", __name__)

def admin_required(f):
    """Decorator to restrict access to administrator accounts only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Administrator access required for this action.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# Public & Student Routes
# ==============================================================================

@main_bp.route("/")
def index():
    """Browse and search lost and found items."""
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    item_type = request.args.get("type", "").strip()
    status = request.args.get("status", "").strip()

    items_query = Item.query

    if query:
        items_query = items_query.filter(
            (Item.title.ilike(f"%{query}%")) |
            (Item.description.ilike(f"%{query}%")) |
            (Item.location.ilike(f"%{query}%"))
        )

    if category and category != "all":
        items_query = items_query.filter_by(category=category)

    if item_type and item_type != "all":
        items_query = items_query.filter_by(item_type=item_type)

    if status and status != "all":
        items_query = items_query.filter_by(status=status)

    items = items_query.order_by(Item.created_at.desc()).all()
    
    categories = [
        "Electronics",
        "ID & Documents",
        "Books & Stationery",
        "Keys & Locks",
        "Bags & Bottles",
        "Clothing & Accessories",
        "Other"
    ]

    return render_template(
        "index.html",
        items=items,
        query=query,
        selected_category=category,
        selected_type=item_type,
        selected_status=status,
        categories=categories
    )

@main_bp.route("/item/<int:item_id>")
def item_detail(item_id):
    """View details of a specific lost or found item."""
    item = db.get_or_404(Item, item_id)
    return render_template("item_detail.html", item=item)

@main_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new student or admin account."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        admin_key = request.form.get("admin_key", "").strip()

        if not name or not email or not password:
            flash("All required fields must be filled.", "danger")
            return redirect(url_for("main.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please sign in instead.", "warning")
            return redirect(url_for("main.login"))

        # Verify admin key if role requested is admin
        assigned_role = "student"
        if role == "admin":
            expected_key = current_app.config.get("ADMIN_SECRET_KEY", "ADMIN_CLOUD_2026")
            if admin_key == expected_key:
                assigned_role = "admin"
            else:
                flash("Invalid Admin Secret Key. Created account as Student instead.", "warning")

        new_user = User(name=name, email=email, role=assigned_role)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash(f"Account successfully created as {assigned_role.capitalize()}! Please sign in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate student or administrator."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.index"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("login.html")

@main_bp.route("/logout")
@login_required
def logout():
    """Log out the current user session."""
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("main.index"))

@main_bp.route("/report", methods=["GET", "POST"])
@login_required
def report_item():
    """Report a Lost or Found item with image upload to AWS S3/Local."""
    if request.method == "POST":
        item_type = request.form.get("item_type", "lost")
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "Other")
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        item_date_str = request.form.get("item_date")
        contact_info = request.form.get("contact_info", "").strip()
        image_file = request.files.get("image")

        if not title or not description or not location or not contact_info:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("main.report_item"))

        # Parse date
        try:
            item_date = datetime.strptime(item_date_str, "%Y-%m-%d").date() if item_date_str else date.today()
        except ValueError:
            item_date = date.today()

        # Upload image to AWS S3 or Local fallback
        image_url, storage_provider = save_image_file(image_file)

        # Default initial status
        initial_status = "Lost" if item_type == "lost" else "Found"

        new_item = Item(
            user_id=current_user.id,
            item_type=item_type,
            title=title,
            category=category,
            description=description,
            location=location,
            item_date=item_date,
            image_url=image_url,
            status=initial_status,
            contact_info=contact_info,
            storage_provider=storage_provider
        )

        db.session.add(new_item)
        db.session.commit()

        storage_msg = f" Image stored on {storage_provider}." if image_url else ""
        flash(f"Item report submitted successfully!{storage_msg}", "success")
        return redirect(url_for("main.item_detail", item_id=new_item.id))

    categories = [
        "Electronics",
        "ID & Documents",
        "Books & Stationery",
        "Keys & Locks",
        "Bags & Bottles",
        "Clothing & Accessories",
        "Other"
    ]
    return render_template("report_item.html", categories=categories, today=date.today().isoformat())

@main_bp.route("/my-items")
@login_required
def my_items():
    """View reports submitted by the logged-in student."""
    items = Item.query.filter_by(user_id=current_user.id).order_by(Item.created_at.desc()).all()
    return render_template("my_items.html", items=items)

# ==============================================================================
# Administrator Routes
# ==============================================================================

@main_bp.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Admin dashboard to manage reports, update item statuses, and view metrics."""
    total_items = Item.query.count()
    lost_count = Item.query.filter_by(status="Lost").count()
    found_count = Item.query.filter_by(status="Found").count()
    returned_count = Item.query.filter_by(status="Returned").count()
    s3_items_count = Item.query.filter(Item.storage_provider.ilike("%S3%")).count()

    items = Item.query.order_by(Item.created_at.desc()).all()

    return render_template(
        "admin_dashboard.html",
        total_items=total_items,
        lost_count=lost_count,
        found_count=found_count,
        returned_count=returned_count,
        s3_items_count=s3_items_count,
        items=items
    )

@main_bp.route("/admin/item/<int:item_id>/update-status", methods=["POST"])
@admin_required
def update_status(item_id):
    """Admin updates the status of an item (Lost, Found, Returned)."""
    item = db.get_or_404(Item, item_id)
    new_status = request.form.get("status")

    if new_status in ["Lost", "Found", "Returned"]:
        old_status = item.status
        item.status = new_status
        db.session.commit()
        flash(f"Status for '{item.title}' updated from {old_status} to {new_status}.", "success")
    else:
        flash("Invalid status selected.", "danger")

    return redirect(request.referrer or url_for("main.admin_dashboard"))

@main_bp.route("/admin/item/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_item(item_id):
    """Admin deletes an invalid or spam item report."""
    item = db.get_or_404(Item, item_id)
    title = item.title
    db.session.delete(item)
    db.session.commit()
    flash(f"Report '{title}' has been deleted.", "info")
    return redirect(request.referrer or url_for("main.admin_dashboard"))

# ==============================================================================
# Cloud Diagnostics / Lab Viva Demonstration Route
# ==============================================================================

@main_bp.route("/cloud-info")
def cloud_info():
    """
    Displays real-time cloud diagnostic information to demonstrate
    Virtualization, IaaS, PaaS, SaaS, Docker, RDS, and S3 during practical exams.
    """
    hostname = socket.gethostname()
    
    # Check if running inside Docker container
    is_docker = os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER") == "true"
    
    # S3 connectivity test
    s3_status = test_s3_connection()

    db_type = current_app.config.get("DB_ENGINE_TYPE", "Unknown")
    is_rds = "RDS" in db_type

    cloud_metrics = {
        "hostname": hostname,
        "is_docker": is_docker,
        "os_platform": platform.platform(),
        "python_version": platform.python_version(),
        "database_engine": db_type,
        "database_connected": is_rds or "SQLite" in db_type,
        "s3_status": s3_status,
        "cloud_storage_active": current_app.config.get("USE_S3", False),
        "app_service_model": "SaaS (Software as a Service)",
        "compute_infrastructure": "IaaS (AWS EC2 Virtual Machine)",
        "container_runtime": "Docker Container (Linux)",
    }

    return render_template("cloud_info.html", metrics=cloud_metrics)
