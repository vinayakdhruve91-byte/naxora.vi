from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_sqlalchemy import SQLAlchemy

from dotenv import load_dotenv

import os
import requests




# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

ADMIN_EMAIL = os.getenv(
    "ADMIN_EMAIL"
)


# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "nexora-development-key"
)

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "sqlite:///nexora.db"

app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False


db = SQLAlchemy(app)


# =====================================================
# USER DATABASE
# =====================================================

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )
    study_streak = db.Column(
    db.Integer,
    default=0
    )

    study_minutes = db.Column(
    db.Integer,
    default=0
    )

    mcqs_practiced = db.Column(
    db.Integer,
    default=0
    )

    weekly_progress = db.Column(
    db.Integer,
    default=0
    )
  




# =====================================================
# USER ACTIVITY
# =====================================================

class Activity(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        nullable=False
    )

    action = db.Column(
        db.String(200),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.now()
    )

# =====================================================
# FEEDBACK DATABASE
# =====================================================

class Feedback(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        nullable=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Pending"
    )


# =====================================================
# CREATE DATABASE
# =====================================================

with app.app_context():

    db.create_all()

    # -------------------------------------------------
    # SAFE SQLITE MIGRATION FOR EXISTING USERS
    # -------------------------------------------------
    # db.create_all() creates missing tables, but it does
    # not add new columns to an existing SQLite table.
    # These checks add the four new dashboard-stat columns
    # without deleting existing users or passwords.
    existing_columns = {
        row[1]
        for row in db.session.execute(
            db.text("PRAGMA table_info(user)")
        ).fetchall()
    }

    new_columns = {
        "study_streak": "INTEGER NOT NULL DEFAULT 0",
        "study_minutes": "INTEGER NOT NULL DEFAULT 0",
        "mcqs_practiced": "INTEGER NOT NULL DEFAULT 0",
        "weekly_progress": "INTEGER NOT NULL DEFAULT 0",
    }

    for column_name, column_definition in new_columns.items():
        if column_name not in existing_columns:
            db.session.execute(
                db.text(
                    f"ALTER TABLE user ADD COLUMN {column_name} {column_definition}"
                )
            )

    db.session.commit()


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =====================================================
# LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        user = User.query.filter_by(
            email=email
        ).first()


        if (
            user
            and check_password_hash(
                user.password,
                password
            )
        ):

            session["user_id"] = user.id

            session["user_name"] = user.name

            session["user_email"] = user.email


            return redirect(
                url_for("dashboard")
            )


        return "Invalid email or password"


    return render_template(
        "login.html"
    )


# =====================================================
# SIGNUP
# =====================================================

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        if not name or not email or not password:

            return "Please fill all fields."


        existing_user = User.query.filter_by(
            email=email
        ).first()


        if existing_user:

            return "Email already registered"


        hashed_password = generate_password_hash(
            password
        )


        new_user = User(

            name=name,

            email=email,

            password=hashed_password

        )


        db.session.add(
            new_user
        )

        db.session.commit()


        return redirect(
            url_for("login")
        )


    return render_template(
        "signup.html"
    )


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=user.name,
        study_streak=user.study_streak or 0,
        study_minutes=user.study_minutes or 0,
        mcqs_practiced=user.mcqs_practiced or 0,
        weekly_progress=user.weekly_progress or 0
    )



# =====================================================
# PROFILE
# =====================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("login"))

    activities = (
        Activity.query
        .filter_by(user_id=user.id)
        .order_by(Activity.id.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "profile.html",
        name=user.name,
        email=user.email,
        study_streak=user.study_streak or 0,
        study_minutes=user.study_minutes or 0,
        mcqs_practiced=user.mcqs_practiced or 0,
        weekly_progress=user.weekly_progress or 0,
        activities=activities
    )



@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not name or not email:
            return render_template(
                "edit-profile.html",
                name=user.name,
                email=user.email,
                error="Please fill both name and email."
            )

        # Check whether another account already uses this email.
        existing_user = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_user:
            return render_template(
                "edit-profile.html",
                name=user.name,
                email=user.email,
                error="This email is already registered."
            )

        old_name = user.name

        user.name = name
        user.email = email

        db.session.add(
            Activity(
                user_id=user.id,
                action="Updated profile"
            )
        )

        db.session.commit()

        # Keep the current login session in sync.
        session["user_name"] = user.name
        session["user_email"] = user.email

        return redirect(url_for("profile"))

    return render_template(
        "edit-profile.html",
        name=user.name,
        email=user.email
    )



# =====================================================
# CHANGE PASSWORD
# =====================================================

@app.route("/profile/password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_password or not new_password or not confirm_password:
            return render_template(
                "change-password.html",
                error="Please fill all password fields."
            )

        if not check_password_hash(user.password, current_password):
            return render_template(
                "change-password.html",
                error="Current password is incorrect."
            )

        if len(new_password) < 8:
            return render_template(
                "change-password.html",
                error="New password must be at least 8 characters."
            )

        if new_password != confirm_password:
            return render_template(
                "change-password.html",
                error="New passwords do not match."
            )

        user.password = generate_password_hash(new_password)

        db.session.add(
            Activity(
                user_id=user.id,
                action="Changed account password"
            )
        )

        db.session.commit()

        return redirect(url_for("profile"))

    return render_template("change-password.html")



# =====================================================
# ACHIEVEMENTS
# =====================================================

@app.route("/achievements")
def achievements():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("login"))

    streak = user.study_streak or 0
    mcqs = user.mcqs_practiced or 0
    minutes = user.study_minutes or 0
    progress = user.weekly_progress or 0

    badges = [
        {
            "icon": "🚀",
            "title": "Welcome Aboard",
            "text": "Create your NEXORA account.",
            "unlocked": True
        },
        {
            "icon": "🔥",
            "title": "3-Day Streak",
            "text": "Reach a 3 day study streak.",
            "unlocked": streak >= 3
        },
        {
            "icon": "🔥",
            "title": "7-Day Streak",
            "text": "Reach a 7 day study streak.",
            "unlocked": streak >= 7
        },
        {
            "icon": "📝",
            "title": "First 10 MCQs",
            "text": "Practice 10 MCQs.",
            "unlocked": mcqs >= 10
        },
        {
            "icon": "🏆",
            "title": "100 MCQs",
            "text": "Practice 100 MCQs.",
            "unlocked": mcqs >= 100
        },
        {
            "icon": "⏱️",
            "title": "Study Starter",
            "text": "Complete 60 minutes of study.",
            "unlocked": minutes >= 60
        },
        {
            "icon": "🎯",
            "title": "Weekly Goal",
            "text": "Reach 100% weekly progress.",
            "unlocked": progress >= 100
        }
    ]

    unlocked_count = sum(1 for badge in badges if badge["unlocked"])

    return render_template(
        "achievements.html",
        name=user.name,
        badges=badges,
        unlocked_count=unlocked_count,
        total_count=len(badges)
    )


# =====================================================
# STUDENT TOOLS
# =====================================================

@app.route("/student-tools")
def student_tools():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "student-tools.html"
    )


# =====================================================
# CREATOR TOOLS
# =====================================================

@app.route("/creator-tools")
def creator_tools():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "creator-tools.html"
    )


# =====================================================
# CREATOR PAGES
# =====================================================

@app.route("/caption-generator")
def caption_generator():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "caption-generator.html"
    )


@app.route("/script-generator")
def script_generator():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "script-generator.html"
    )


@app.route("/title-generator")
def title_generator():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "title-generator.html"
    )


@app.route("/bio-generator")
def bio_generator():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "bio-generator.html"
    )


@app.route("/content-ideas")
def content_ideas():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "content-ideas.html"
    )


@app.route("/hashtag-generator")
def hashtag_generator():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "hashtag-generator.html"
    )


# =====================================================
# STUDENT PAGES
# =====================================================

@app.route("/study-timer")
def study_timer():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "study-timer.html"
    )


@app.route("/exam-countdown")
def exam_countdown():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "exam-countdown.html"
    )


@app.route("/study-planner")
def study_planner():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "study-planner.html"
    )


@app.route("/mcq-generator")
def mcq_generator():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "mcq-generator.html"
    )


@app.route("/percentage")
def percentage():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "percentage.html"
    )


@app.route("/cgpa")
def cgpa():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "cgpa.html"
    )


# =====================================================
# AI — OPENROUTER
# =====================================================

@app.route(
    "/api/ai-test",
    methods=["POST"]
)
def ai_test():

    if "user_id" not in session:

        return jsonify({

            "success": False,

            "message":
                "Login required"

        }), 401


    if not OPENROUTER_API_KEY:

        return jsonify({

            "success": False,

            "message":
                "OpenRouter API key is not configured."

        }), 503


    data = request.get_json(
        silent=True
    ) or {}


    prompt = data.get(
        "prompt",
        ""
    ).strip()


    if not prompt:

        return jsonify({

            "success": False,

            "message":
                "Please provide a prompt."

        }), 400


    try:

        response = requests.post(

            "https://openrouter.ai/api/v1/chat/completions",

            headers={

                "Authorization":
                    f"Bearer {OPENROUTER_API_KEY}",

                "Content-Type":
                    "application/json",

                "X-Title":
                    "NEXORA"

            },

            json={

                "model":
                    "openai/gpt-5",

                "messages": [

                    {

                        "role":
                            "user",

                        "content":
                            prompt

                    }

                ],
                "max_tokens": 4000
            },
            timeout=60
        )

                


        if not response.ok:

            app.logger.error(
                "OpenRouter error: %s",
                response.text
            )


            return jsonify({

                "success": False,

                "message":
                    "AI request failed."

            }), 500


        result = response.json()


        answer = (
            result
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )


        if not answer:

            return jsonify({

                "success": False,

                "message":
                    "AI returned an empty response."

            }), 500


        return jsonify({

            "success": True,

            "response": answer

        })


    except requests.RequestException:

        app.logger.exception(
            "OpenRouter connection failed"
        )


        return jsonify({

            "success": False,

            "message":
                "Could not connect to AI service."

        }), 500


    except Exception:

        app.logger.exception(
            "AI request failed"
        )


        return jsonify({

            "success": False,

            "message":
                "AI request failed."

        }), 500


# =====================================================
# FEEDBACK
# =====================================================

@app.route(
    "/feedback",
    methods=["GET", "POST"]
)
def feedback():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        category = request.form.get(
            "category",
            "General Feedback"
        ).strip()


        message = request.form.get(
            "message",
            ""
        ).strip()


        if not message:

            return render_template(

                "feedback.html",

                error=
                    "Please enter your feedback."

            )


        user = User.query.get(
            session["user_id"]
        )


        if not user:

            session.clear()

            return redirect(
                url_for("login")
            )


        new_feedback = Feedback(

            user_id=user.id,

            name=user.name,

            email=user.email,

            category=category,

            message=message,

            status="Pending"

        )


        db.session.add(
            new_feedback
        )

        db.session.commit()


        return render_template(

            "feedback.html",

            success=
                "Thanks! Your request has been submitted. 💙"

        )


    return render_template(
        "feedback.html"
    )


# =====================================================
# ADMIN FEEDBACK PANEL
# =====================================================

@app.route("/admin/feedback")
def admin_feedback():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    current_email = session.get(
        "user_email",
        ""
    ).lower()


    if not ADMIN_EMAIL:

        return "Admin email is not configured."


    if current_email != ADMIN_EMAIL.lower():

        return "Access denied.", 403


    feedbacks = Feedback.query.order_by(
        Feedback.id.desc()
    ).all()


    return render_template(

        "admin-feedback.html",

        feedbacks=feedbacks

    )


# =====================================================
# UPDATE FEEDBACK STATUS
# =====================================================

@app.route(
    "/admin/feedback/<int:feedback_id>/status",
    methods=["POST"]
)
def update_feedback_status(
    feedback_id
):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    current_email = session.get(
        "user_email",
        ""
    ).lower()


    if (
        not ADMIN_EMAIL
        or current_email != ADMIN_EMAIL.lower()
    ):

        return "Access denied.", 403


    feedback = Feedback.query.get_or_404(
        feedback_id
    )


    new_status = request.form.get(
        "status",
        "Pending"
    )


    allowed_statuses = [

        "Pending",

        "In Progress",

        "Completed"

    ]


    if new_status in allowed_statuses:

        feedback.status = new_status

        db.session.commit()


    return redirect(
        url_for("admin_feedback")
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
