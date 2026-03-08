import os
from datetime import date, datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import Application, Drive, User, db

app = Flask(__name__)
app.config.from_object(Config)
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "resumes")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
ALLOWED_RESUME_EXTENSIONS = {"pdf", "doc", "docx"}

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def role_required(role_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if current_user.role != role_name:
                flash("Access denied.")
                return redirect(url_for("dashboard"))
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def is_allowed_resume(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_RESUME_EXTENSIONS


@app.before_request
def enforce_blacklist():
    if (
        current_user.is_authenticated
        and current_user.blacklisted
        and request.endpoint not in {"logout", "login", "static"}
    ):
        logout_user()
        flash("Your account has been deactivated by admin.")
        return redirect(url_for("login"))
    return None


with app.app_context():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.create_all()

    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin = User(
            name="Admin",
            email="admin@portal.com",
            password=generate_password_hash("admin123"),
            role="admin",
            approved=True,
        )
        db.session.add(admin)
        db.session.commit()


@app.route("/")
def home():
    return render_template("base.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid credentials.")
            return redirect(url_for("login"))

        if user.blacklisted:
            flash("Your account is deactivated by admin.")
            return redirect(url_for("login"))

        if user.role == "company" and not user.approved:
            flash("Company account pending admin approval.")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    if current_user.role == "company":
        return redirect(url_for("company_dashboard"))
    if current_user.role == "student":
        return redirect(url_for("student_dashboard"))
    flash("Unknown role.")
    return redirect(url_for("login"))


@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        contact = request.form.get("contact", "").strip()
        department = request.form.get("department", "").strip()
        cgpa = request.form.get("cgpa", "").strip()
        grad_year = request.form.get("grad_year", "").strip()

        if User.query.filter_by(email=email).first():
            flash("Email already exists.")
            return redirect(url_for("register_student"))

        student = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="student",
            approved=True,
            contact=contact or None,
            department=department or None,
            cgpa=float(cgpa) if cgpa else None,
            grad_year=int(grad_year) if grad_year else None,
        )
        db.session.add(student)
        db.session.commit()
        flash("Student registration successful. Please login.")
        return redirect(url_for("login"))

    return render_template("register_student.html")


@app.route("/register/company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        website = request.form.get("website", "").strip()
        hr_contact = request.form.get("hr_contact", "").strip()
        contact = request.form.get("contact", "").strip()

        if User.query.filter_by(email=email).first():
            flash("Email already exists.")
            return redirect(url_for("register_company"))

        company = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="company",
            approved=False,
            website=website or None,
            hr_contact=hr_contact or None,
            contact=contact or None,
        )
        db.session.add(company)
        db.session.commit()
        flash("Company registration submitted. Wait for admin approval.")
        return redirect(url_for("login"))

    return render_template("register_company.html")


@app.route("/admin/dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    student_q = request.args.get("student_q", "").strip()
    company_q = request.args.get("company_q", "").strip()

    students_query = User.query.filter_by(role="student")
    companies_query = User.query.filter_by(role="company")

    if student_q:
        student_filters = [
            User.name.ilike(f"%{student_q}%"),
            User.email.ilike(f"%{student_q}%"),
            User.contact.ilike(f"%{student_q}%"),
        ]
        if student_q.isdigit():
            student_filters.append(User.id == int(student_q))
        students_query = students_query.filter(or_(*student_filters))

    if company_q:
        company_filters = [User.name.ilike(f"%{company_q}%"), User.email.ilike(f"%{company_q}%")]
        if company_q.isdigit():
            company_filters.append(User.id == int(company_q))
        companies_query = companies_query.filter(or_(*company_filters))

    students = students_query.order_by(User.id.desc()).all()
    companies = companies_query.order_by(User.id.desc()).all()
    pending_companies = User.query.filter_by(role="company", approved=False).order_by(User.id.desc()).all()
    drives = Drive.query.order_by(Drive.created_on.desc()).all()
    pending_drives = Drive.query.filter_by(status="Pending").order_by(Drive.created_on.desc()).all()
    applications = Application.query.order_by(Application.applied_on.desc()).all()

    return render_template(
        "admin_dashboard.html",
        students=students,
        companies=companies,
        pending_companies=pending_companies,
        drives=drives,
        pending_drives=pending_drives,
        applications=applications,
        total_students=User.query.filter_by(role="student").count(),
        total_companies=User.query.filter_by(role="company").count(),
        total_drives=Drive.query.count(),
        total_applications=Application.query.count(),
        student_q=student_q,
        company_q=company_q,
    )


@app.route("/admin/company/<int:company_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def approve_company(company_id):
    company = User.query.get_or_404(company_id)
    if company.role != "company":
        flash("Invalid company.")
        return redirect(url_for("admin_dashboard"))

    company.approved = True
    db.session.commit()
    flash("Company approved.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/company/<int:company_id>/reject", methods=["POST"])
@login_required
@role_required("admin")
def reject_company(company_id):
    company = User.query.get_or_404(company_id)
    if company.role != "company":
        flash("Invalid company.")
        return redirect(url_for("admin_dashboard"))

    db.session.delete(company)
    db.session.commit()
    flash("Company rejected and removed.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/drive/<int:drive_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def approve_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    drive.status = "Approved"
    db.session.commit()
    flash("Drive approved.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/drive/<int:drive_id>/reject", methods=["POST"])
@login_required
@role_required("admin")
def reject_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    drive.status = "Rejected"
    db.session.commit()
    flash("Drive rejected.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/drive/<int:drive_id>/close", methods=["POST"])
@login_required
@role_required("admin")
def close_drive_by_admin(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    drive.status = "Closed"
    db.session.commit()
    flash("Drive closed.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>/blacklist", methods=["POST"])
@login_required
@role_required("admin")
def toggle_blacklist(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Admin cannot be blacklisted.")
        return redirect(url_for("admin_dashboard"))

    user.blacklisted = not user.blacklisted
    db.session.commit()
    flash(f"{user.name} status updated.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Admin profile edit is restricted here.")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        user.name = request.form.get("name", user.name).strip()
        user.contact = request.form.get("contact", "").strip() or None
        user.email = request.form.get("email", user.email).strip().lower()

        if user.role == "student":
            user.department = request.form.get("department", "").strip() or None
            cgpa_value = request.form.get("cgpa", "").strip()
            grad_value = request.form.get("grad_year", "").strip()
            user.cgpa = float(cgpa_value) if cgpa_value else None
            user.grad_year = int(grad_value) if grad_value else None
        else:
            user.website = request.form.get("website", "").strip() or None
            user.hr_contact = request.form.get("hr_contact", "").strip() or None
            user.approved = request.form.get("approved") == "on"

        db.session.commit()
        flash("User updated.")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_edit_user.html", user=user)


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Admin cannot be deleted.")
        return redirect(url_for("admin_dashboard"))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted.")
    return redirect(url_for("admin_dashboard"))


@app.route("/drive/<int:drive_id>")
@login_required
@role_required("admin")
def drive_details(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    return render_template("drive_details.html", drive=drive)


@app.route("/application/<int:app_id>")
@login_required
@role_required("admin")
def application_details(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template("application_details.html", application=application)


@app.route("/company/dashboard")
@login_required
@role_required("company")
def company_dashboard():
    drives = Drive.query.filter_by(company_id=current_user.id).order_by(Drive.created_on.desc()).all()
    applicants_by_drive = {drive.id: Application.query.filter_by(drive_id=drive.id).count() for drive in drives}
    return render_template(
        "company_dashboard.html",
        drives=drives,
        applicants_by_drive=applicants_by_drive,
    )


@app.route("/company/profile", methods=["GET", "POST"])
@login_required
@role_required("company")
def company_profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.contact = request.form.get("contact", "").strip() or None
        current_user.website = request.form.get("website", "").strip() or None
        current_user.hr_contact = request.form.get("hr_contact", "").strip() or None
        db.session.commit()
        flash("Company profile updated.")
        return redirect(url_for("company_dashboard"))

    return render_template("company_profile.html")


@app.route("/company/create_drive", methods=["GET", "POST"])
@login_required
@role_required("company")
def create_drive():
    if not current_user.approved:
        flash("Wait for admin approval before creating drives.")
        return redirect(url_for("company_dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        eligibility = request.form.get("eligibility", "").strip()
        deadline_raw = request.form.get("deadline", "").strip()
        location = request.form.get("location", "").strip()
        salary = request.form.get("salary", "").strip()

        try:
            deadline_date = datetime.strptime(deadline_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid deadline date.")
            return redirect(url_for("create_drive"))

        drive = Drive(
            company_id=current_user.id,
            title=title,
            description=description,
            eligibility=eligibility,
            deadline=deadline_date,
            location=location or None,
            salary=salary or None,
            status="Pending",
        )
        db.session.add(drive)
        db.session.commit()
        flash("Drive created and sent for admin approval.")
        return redirect(url_for("company_dashboard"))

    return render_template("create_drive.html")


@app.route("/company/drive/<int:drive_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("company")
def edit_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        flash("Unauthorized.")
        return redirect(url_for("company_dashboard"))

    if request.method == "POST":
        drive.title = request.form.get("title", drive.title).strip()
        drive.description = request.form.get("description", drive.description).strip()
        drive.eligibility = request.form.get("eligibility", drive.eligibility).strip()
        drive.location = request.form.get("location", "").strip() or None
        drive.salary = request.form.get("salary", "").strip() or None
        deadline_raw = request.form.get("deadline", "").strip()

        try:
            drive.deadline = datetime.strptime(deadline_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid deadline date.")
            return redirect(url_for("edit_drive", drive_id=drive.id))

        if drive.status in {"Approved", "Rejected"}:
            drive.status = "Pending"

        db.session.commit()
        flash("Drive updated.")
        return redirect(url_for("company_dashboard"))

    return render_template("edit_drive.html", drive=drive)


@app.route("/company/drive/<int:drive_id>/close", methods=["POST"])
@login_required
@role_required("company")
def close_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        flash("Unauthorized.")
        return redirect(url_for("company_dashboard"))

    drive.status = "Closed"
    db.session.commit()
    flash("Drive closed.")
    return redirect(url_for("company_dashboard"))


@app.route("/company/drive/<int:drive_id>/delete", methods=["POST"])
@login_required
@role_required("company")
def delete_drive(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        flash("Unauthorized.")
        return redirect(url_for("company_dashboard"))

    db.session.delete(drive)
    db.session.commit()
    flash("Drive deleted.")
    return redirect(url_for("company_dashboard"))


@app.route("/company/applicants/<int:drive_id>")
@login_required
@role_required("company")
def view_applicants(drive_id):
    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        flash("Unauthorized.")
        return redirect(url_for("company_dashboard"))

    applications = Application.query.filter_by(drive_id=drive_id).order_by(Application.applied_on.desc()).all()
    return render_template("company_applicants.html", drive=drive, applications=applications)


@app.route("/company/application/<int:app_id>/status", methods=["POST"])
@login_required
@role_required("company")
def update_application_status(app_id):
    application = Application.query.get_or_404(app_id)
    if application.drive.company_id != current_user.id:
        flash("Unauthorized.")
        return redirect(url_for("company_dashboard"))

    new_status = request.form.get("status", "")
    if new_status not in {"Shortlisted", "Selected", "Rejected"}:
        flash("Invalid status.")
        return redirect(url_for("view_applicants", drive_id=application.drive_id))

    application.status = new_status
    application.remarks = request.form.get("remarks", "").strip() or None
    db.session.commit()
    flash("Application status updated.")
    return redirect(url_for("view_applicants", drive_id=application.drive_id))


@app.route("/student/dashboard")
@login_required
@role_required("student")
def student_dashboard():
    drives = (
        Drive.query.filter_by(status="Approved")
        .filter(Drive.deadline >= date.today())
        .order_by(Drive.deadline.asc())
        .all()
    )
    student_applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.applied_on.desc()).all()
    return render_template(
        "student_dashboard.html",
        drives=drives,
        student_applications=student_applications,
    )


@app.route("/student/profile", methods=["GET", "POST"])
@login_required
@role_required("student")
def student_profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.contact = request.form.get("contact", "").strip() or None
        current_user.department = request.form.get("department", "").strip() or None
        cgpa_value = request.form.get("cgpa", "").strip()
        grad_value = request.form.get("grad_year", "").strip()
        current_user.cgpa = float(cgpa_value) if cgpa_value else None
        current_user.grad_year = int(grad_value) if grad_value else None

        resume = request.files.get("resume")
        if resume and resume.filename:
            if not is_allowed_resume(resume.filename):
                flash("Resume must be PDF/DOC/DOCX.")
                return redirect(url_for("student_profile"))

            filename = secure_filename(f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{resume.filename}")
            resume.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            current_user.resume_filename = filename

        db.session.commit()
        flash("Student profile updated.")
        return redirect(url_for("student_dashboard"))

    return render_template("student_profile.html")


@app.route("/student/resume/<path:filename>")
@login_required
def download_resume(filename):
    if current_user.role not in {"admin", "company", "student"}:
        flash("Unauthorized.")
        return redirect(url_for("dashboard"))
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/student/drive/<int:drive_id>")
@login_required
@role_required("student")
def student_drive_details(drive_id):
    drive = Drive.query.filter_by(id=drive_id, status="Approved").first_or_404()
    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive_id).first()
    return render_template("student_drive_details.html", drive=drive, existing=existing)


@app.route("/apply/<int:drive_id>", methods=["POST"])
@login_required
@role_required("student")
def apply_drive(drive_id):
    drive = Drive.query.filter_by(id=drive_id, status="Approved").first_or_404()

    if drive.deadline < date.today():
        flash("Application deadline has passed.")
        return redirect(url_for("student_dashboard"))

    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive_id).first()
    if existing:
        flash("You have already applied for this drive.")
        return redirect(url_for("student_dashboard"))

    application = Application(student_id=current_user.id, drive_id=drive_id, status="Applied")
    db.session.add(application)
    db.session.commit()
    flash("Application submitted.")
    return redirect(url_for("student_dashboard"))


@app.route("/student/history")
@login_required
@role_required("student")
def student_history():
    applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.applied_on.desc()).all()
    return render_template("student_history.html", applications=applications)


if __name__ == "__main__":
    app.run(debug=True)
