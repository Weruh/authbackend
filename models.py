"""Database models and explicit public representations."""
from datetime import datetime

from extensions import bcrypt, db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    _password_hash = db.Column("password_hash", db.String(128), nullable=False)
    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    @property
    def password_hash(self):
        raise AttributeError("Password hashes are private.")

    @password_hash.setter
    def password_hash(self, password):
        # Bcrypt uses at most 72 bytes; reject longer input rather than truncate it.
        if not isinstance(password, str) or not 8 <= len(password.encode("utf-8")) <= 72:
            raise ValueError("Password must contain between 8 and 72 UTF-8 bytes.")
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        return (
            isinstance(password, str)
            and 8 <= len(password.encode("utf-8")) <= 72
            and bcrypt.check_password_hash(self._password_hash, password)
        )

    def to_dict(self):
        return {"id": self.id, "username": self.username}


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user = db.relationship("User", back_populates="notes")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }
