from datetime import datetime, date, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # 'student' or 'admin'
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationship to items reported by this user
    items = db.relationship("Item", backref="reporter", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str):
        """Hash password using industry-standard scrypt / pbkdf2 algorithm."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify hashed password for secure login."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        """Check if user has administrative privileges."""
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_type = db.Column(db.String(10), nullable=False)  # 'lost' or 'found'
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)   # 'Electronics', 'ID Cards', etc.
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False)  # e.g., 'Library 2nd Floor'
    item_date = db.Column(db.Date, nullable=False, default=date.today)
    image_url = db.Column(db.String(500), nullable=True)  # AWS S3 public URL or local path
    status = db.Column(db.String(20), nullable=False, default="Lost")  # 'Lost', 'Found', 'Returned'
    contact_info = db.Column(db.String(150), nullable=False)
    storage_provider = db.Column(db.String(50), default="Local Storage") # 'AWS S3' or 'Local'
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<Item #{self.id} {self.title} [{self.status}]>"
