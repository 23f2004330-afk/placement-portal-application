from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin / company / student

    approved = db.Column(db.Boolean, default=False)
    blacklisted = db.Column(db.Boolean, default=False)

    contact = db.Column(db.String(30))
    department = db.Column(db.String(120))
    cgpa = db.Column(db.Float)
    grad_year = db.Column(db.Integer)
    resume_filename = db.Column(db.String(255))

    website = db.Column(db.String(255))
    hr_contact = db.Column(db.String(120))

    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    drives = db.relationship(
        "Drive",
        backref="company",
        foreign_keys="Drive.company_id",
        lazy=True,
        cascade="all, delete-orphan",
    )
    applications = db.relationship(
        "Application",
        backref="student",
        foreign_keys="Application.student_id",
        lazy=True,
        cascade="all, delete-orphan",
    )


class Drive(db.Model):
    __tablename__ = "drive"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    eligibility = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(120))
    salary = db.Column(db.String(120))
    deadline = db.Column(db.Date, nullable=False)

    status = db.Column(db.String(20), default="Pending")  # Pending/Approved/Rejected/Closed
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = db.relationship(
        "Application",
        backref="drive",
        lazy=True,
        cascade="all, delete-orphan",
    )


class Application(db.Model):
    __tablename__ = "application"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("drive.id"), nullable=False)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Applied")  # Applied/Shortlisted/Selected/Rejected
    remarks = db.Column(db.String(255))

    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="unique_application"),
    )
