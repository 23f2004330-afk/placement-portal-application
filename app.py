from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# -----------------------
# Flask-Login Setup
# -----------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------
# Create Database + Admin
# -----------------------
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin = User(
            name="Admin",
            email="admin@portal.com",
            password=generate_password_hash("admin123"),
            role="admin",
            approved=True
        )
        db.session.add(admin)
        db.session.commit()


# -----------------------
# Routes
# -----------------------

@app.route("/")
def home():
    return "Placement Portal Running"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            if user.blacklisted:
                flash("Your account is blacklisted")
                return redirect(url_for("login"))

            if not user.approved and user.role == "company":
                flash("Wait for admin approval")
                return redirect(url_for("login"))

            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():

    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    elif current_user.role == "company":
        return redirect(url_for("company_dashboard"))

    elif current_user.role == "student":
        return redirect(url_for("student_dashboard"))

    return "Unknown Role"





@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return "Access Denied"
    return render_template("admin_dashboard.html")

@app.route("/company/dashboard")
@login_required
def company_dashboard():
    if current_user.role != "company":
        return "Access Denied"
    return "Company Dashboard"

@app.route("/student/dashboard")
@login_required
def student_dashboard():
    if current_user.role != "student":
        return "Access Denied"
    return "Student Dashboard"





@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully")
    return redirect(url_for("login"))


# -----------------------
# Student Registration
# -----------------------

@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for("register_student"))

        new_student = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="student",
            approved=True
        )

        db.session.add(new_student)
        db.session.commit()

        flash("Registration successful. Please login.")
        return redirect(url_for("login"))

    return render_template("register_student.html")


# -----------------------
# Company Registration
# -----------------------

@app.route("/register/company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for("register_company"))

        new_company = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="company",
            approved=False
        )

        db.session.add(new_company)
        db.session.commit()

        flash("Registration submitted. Wait for admin approval.")
        return redirect(url_for("login"))

    return render_template("register_company.html")


if __name__ == "__main__":
    app.run(debug=True)