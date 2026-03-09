🎓 ApplicationPortal – Placement Management System
📝 Project Overview

ApplicationPortal is a full-stack web application designed to digitize and streamline college placement processes. The platform manages Admins, Students, and Recruitment Drives with secure authentication and role-based access control.

The system allows administrators to create recruitment drives, students to apply for jobs, and administrators to track all applications. It is built using Flask, SQLite, SQLAlchemy, Jinja2, and Bootstrap 5 to provide a clean and responsive web interface.

The goal of this system is to replace manual placement processes with an automated and centralized portal for managing student applications and company recruitment drives.

🚦 Key Features
Admin Features

Secure admin login to manage the entire portal.
Create and manage Recruitment Drives.
View all registered students.
Monitor applications submitted by students.
Delete or manage recruitment drives.
View analytics and placement activity across the system.

Student Features
Secure student registration and login.
View available recruitment drives.
Apply for recruitment drives easily.
Track application status.
Manage personal profile.
View applied drives in the student dashboard.
Recruitment Drive Management

Admin can create recruitment drives with:
Company Name
Job Role
Description
Eligibility criteria
Deadline
Students can apply before the deadline.
Security & Access

Role-Based Access Control (RBAC)
Admin routes protected with custom decorators.
Student routes accessible only to logged-in users.
Password Security
Passwords are securely hashed using Werkzeug Security.
Session Management
Implemented using Flask-Login.

✨ Enhancements & Logic
Application Tracking
Each application is recorded with:
Student ID
Recruitment Drive ID
Application Status
Application Date
This creates a complete history of applications.
Conflict Prevention
Students cannot apply to the same recruitment drive multiple times.
Dashboard Interface
Both admin and student dashboards provide organized card-based layouts and real-time information.

Responsive UI
The frontend uses Bootstrap 5 ensuring:
Mobile-friendly pages
Clean navigation
Structured forms and tables

🛠️ Technologies Used
Backend
Python
Flask
Flask-SQLAlchemy
Flask-Login
Frontend
HTML5
CSS3
Bootstrap 5
Jinja2 Templating Engine
Database
SQLite
SQLAlchemy ORM
Security
Werkzeug Password Hashing
Custom Role-Based Decorators

🏁 Milestones
Milestone 1 – Database Models

Created core database models:
User
Student
RecruitmentDrive
Application
Established relationships between tables using SQLAlchemy.

Milestone 2 – Authentication System
Implemented:
Login
Registration
Logout
Added role-based authentication with Flask-Login.

Milestone 3 – Admin Dashboard
Admin can:
Create recruitment drives
View students
Track applications
Manage placement activities

Milestone 4 – Student Dashboard
Students can:
View available drives
Apply for drives
Track applications
Update profile information

Milestone 5 – Application Tracking
Implemented backend logic to:
Record applications
Prevent duplicate applications
Maintain a history of applied drives

📁 Folder Structure
ApplicationPortal
│
│ README.md
│ requirements.txt
│ app.py
│ config.py
│
├── models
│   └── models.py
│
├── controllers
│   └── routes.py
│
├── instance
│   └── application.db
│
├── templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── student_dashboard.html
│   ├── add_drive.html
│   ├── view_drives.html
│   ├── apply_drive.html
│   ├── student_applications.html
│   └── profile.html
│
└── static
    └── style.css
🔐 Admin Credentials (Default)
Username: admin@portal.com
Password: admin123

(Credentials can be changed in the database)

⚙️ How to Run the Application
1️⃣ Download or Clone the Project
git clone <repository-link>

or download the ZIP file and extract it.

2️⃣ Open the Project in VS Code

Navigate to the project folder.

3️⃣ Install Dependencies

Run the following command in terminal:

pip install Flask Flask-SQLAlchemy Flask-Login werkzeug
4️⃣ Run the Application
python app.py
5️⃣ Open in Browser
http://127.0.0.1:5000/

Register as a student or login as admin to explore the system.

🤖 AI Usage Declaration

Percentage of AI-generated code: 30–35%

AI tools were used for:

HTML and Bootstrap layout suggestions

Debugging Flask route logic

Improving UI structure

Writing project documentation

📽️ Demo Video

Add your demo video link here:

https://drive.google.com/file/d/1MI8iTcM3cvnYbQoK3-6FYDNOwxoxK0V5/view?usp=drive_link