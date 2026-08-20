
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

import os
import json
import requests

from dotenv import load_dotenv


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


def login_required():
    return "user_id" in session


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


# =========================================================
# OPENROUTER HELPER
# =========================================================

def ask_ai(prompt):

    if not OPENROUTER_API_KEY:

        return None, "OpenRouter API key is not configured."


    headers = {

        "Authorization":
            f"Bearer {OPENROUTER_API_KEY}",

        "Content-Type":
            "application/json",

        "X-Title":
            "NEXORA AI"

    }


    payload = {

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


    }


    try:

        response = requests.post(

            "https://openrouter.ai/api/v1/chat/completions",

            headers=headers,

            json=payload,

            timeout=60

        )


        data = response.json()


        if response.status_code != 200:

            error_message = (
                data
                .get("error", {})
                .get(
                    "message",
                    "OpenRouter request failed."
                )
            )

            return None, error_message


        choices = data.get(
            "choices",
            []
        )


        if not choices:

            return None, "AI returned no response."


        content = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )


        if not content:

            return None, "AI returned an empty response."


        return content.strip(), None


    except requests.exceptions.Timeout:

        return None, "AI request timed out."


    except requests.exceptions.RequestException:

        return None, "Could not connect to OpenRouter."


    except Exception:

        app.logger.exception(
            "OpenRouter error"
        )

        return None, "Unexpected AI error."


# =========================================================
# AI CAPTION GENERATOR
# =========================================================


# =========================================================
# AI SCRIPT GENERATOR
# =========================================================

@app.route(
    "/api/generate-script",
    methods=["POST"]
)
def generate_script():

    if not login_required():
        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    platform = str(
        data.get("platform", "YouTube")
    ).strip()

    topic = str(
        data.get("topic", "")
    ).strip()

    duration = str(
        data.get("duration", "60 seconds")
    ).strip()

    style = str(
        data.get("style", "Engaging")
    ).strip()

    audience = str(
        data.get("audience", "General")
    ).strip()

    if not topic:
        return jsonify({
            "success": False,
            "message": "Please enter a topic."
        }), 400

    prompt = f"""
You are the NEXORA AI Script Writer.

Create an original video script.

Platform: {platform}
Topic: {topic}
Duration: {duration}
Style: {style}
Target Audience: {audience}

Create a clear, engaging script with:

1. HOOK
2. INTRO
3. MAIN CONTENT
4. ENDING
5. CALL TO ACTION

Requirements:
- Match the requested platform.
- Match the requested duration.
- Make the script natural and easy to speak.
- Keep the audience engaged.
- Do not mention AI.
- Do not add unnecessary explanations.
- Return only the finished script.
"""

    script, error = ask_ai(prompt)

    if error:
        return jsonify({
            "success": False,
            "message": error
        }), 500

    return jsonify({
        "success": True,
        "script": script
    })
@app.route(
    "/api/generate-caption",
    methods=["POST"]
)
def generate_caption():

    if not login_required():

        return jsonify({

            "success": False,

            "message":
                "Login required"

        }), 401


    data = request.get_json(
        silent=True
    ) or {}


    platform = str(
        data.get(
            "platform",
            "Instagram"
        )
    ).strip()


    topic = str(
        data.get(
            "topic",
            ""
        )
    ).strip()


    style = str(
        data.get(
            "style",
            "Trendy"
        )
    ).strip()


    length = str(
        data.get(
            "length",
            "Medium"
        )
    ).strip()


    if not topic:

        return jsonify({

            "success": False,

            "message":
                "Please enter a topic."

        }), 400


    prompt = f"""
You are the NEXORA AI Creator Assistant.

Create one original social-media caption.

Platform: {platform}

Topic:
{topic}

Style:
{style}

Length:
{length}

Rules:
- Make it original.
- Make it natural and engaging.
- Match the platform.
- Match the requested style.
- Use emojis naturally.
- Do not mention AI.
- Do not add hashtags.
- Return only the caption.
"""


    caption, error = ask_ai(
        prompt
    )


    if error:

        return jsonify({

            "success": False,

            "message":
                error

        }), 500


    return jsonify({

        "success": True,

        "caption":
            caption

    })


# =========================================================
# AI TITLE GENERATOR
# =========================================================

@app.route(
    "/api/generate-title",
    methods=["POST"]
)
def generate_title():

    if not login_required():
        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    platform = str(
        data.get("platform", "YouTube")
    ).strip()

    topic = str(
        data.get("topic", "")
    ).strip()

    style = str(
        data.get("style", "Clickable")
    ).strip()

    count = int(
        data.get("count", 10)
    )

    if not topic:
        return jsonify({
            "success": False,
            "message": "Please enter a topic."
        }), 400

    count = max(
        1,
        min(count, 20)
    )

    prompt = f"""
You are the NEXORA AI Title Generator.

Generate {count} original video titles.

Platform: {platform}
Topic: {topic}
Style: {style}

Requirements:
- Make every title different.
- Make them interesting and natural.
- Match the platform.
- Avoid fake or misleading claims.
- Avoid unnecessary clickbait.
- Keep titles concise.
- Number each title from 1 to {count}.
- Return only the numbered titles.
"""

    titles, error = ask_ai(prompt)

    if error:
        return jsonify({
            "success": False,
            "message": error
        }), 500

    return jsonify({
        "success": True,
        "titles": titles
    })

# =========================================================
# AI BIO GENERATOR
# =========================================================

@app.route(
    "/api/generate-bio",
    methods=["POST"]
)
def generate_bio():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    username = str(
        data.get("username", "")
    ).strip()

    niche = str(
        data.get("niche", "")
    ).strip()

    platform = str(
        data.get("platform", "Instagram")
    ).strip()

    style = str(
        data.get("style", "Professional")
    ).strip()

    extra = str(
        data.get("extra", "")
    ).strip()

    if not niche:

        return jsonify({
            "success": False,
            "message": "Please enter your niche."
        }), 400

    prompt = f"""
You are the NEXORA AI Bio Generator.

Create 5 original social-media bios.

Platform: {platform}
Username: {username or "Not provided"}
Niche: {niche}
Style: {style}
Extra information: {extra or "None"}

Requirements:
- Create exactly 5 different bios.
- Keep them concise and natural.
- Match the selected platform.
- Match the requested style.
- Make each bio different.
- Use emojis naturally when appropriate.
- Do not make false claims.
- Number each bio from 1 to 5.
- Return only the five bios.
"""

    bios, error = ask_ai(prompt)

    if error:

        return jsonify({
            "success": False,
            "message": error
        }), 500

    return jsonify({
        "success": True,
        "bios": bios
    })
# =========================================================
# AI CONTENT IDEAS GENERATOR
# =========================================================

@app.route(
    "/api/generate-content-ideas",
    methods=["POST"]
)
def generate_content_ideas():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401


    data = request.get_json(
        silent=True
    ) or {}


    niche = str(
        data.get("niche", "")
    ).strip()


    platform = str(
        data.get(
            "platform",
            "Instagram"
        )
    ).strip()


    content_type = str(
        data.get(
            "content_type",
            "Reels"
        )
    ).strip()


    audience = str(
        data.get(
            "audience",
            "General audience"
        )
    ).strip()


    count = int(
        data.get(
            "count",
            10
        )
    )


    if not niche:

        return jsonify({
            "success": False,
            "message": "Please enter your niche."
        }), 400


    count = max(
        1,
        min(count, 20)
    )


    prompt = f"""
You are the NEXORA AI Content Ideas Assistant.

Generate {count} original content ideas.

Niche:
{niche}

Platform:
{platform}

Content Type:
{content_type}

Target Audience:
{audience}

Requirements:
- Every idea must be different.
- Make ideas practical and creative.
- Match the selected platform.
- Match the content type.
- Consider the target audience.
- Avoid repetitive ideas.
- Do not make false claims.
- Number every idea from 1 to {count}.
- Give only the ideas with a short one-line description.
"""


    ideas, error = ask_ai(
        prompt
    )


    if error:

        return jsonify({
            "success": False,
            "message": error
        }), 500


    return jsonify({
        "success": True,
        "ideas": ideas
    })

# =========================================================
# AI HASHTAG GENERATOR
# =========================================================

@app.route(
    "/api/generate-hashtags",
    methods=["POST"]
)
def generate_hashtags():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    niche = str(
        data.get("niche", "")
    ).strip()

    platform = str(
        data.get(
            "platform",
            "Instagram"
        )
    ).strip()

    topic = str(
        data.get(
            "topic",
            ""
        )
    ).strip()

    count = int(
        data.get(
            "count",
            20
        )
    )

    if not niche:

        return jsonify({
            "success": False,
            "message": "Please enter your niche."
        }), 400

    count = max(
        5,
        min(count, 30)
    )

    prompt = f"""
You are the NEXORA AI Hashtag Assistant.

Generate {count} relevant hashtags.

Niche:
{niche}

Platform:
{platform}

Content Topic:
{topic or "General content in this niche"}

Requirements:
- Every hashtag must be relevant.
- Mix broad, medium, and niche-specific hashtags.
- Do not repeat hashtags.
- Do not use spaces inside hashtags.
- Do not use numbered lists.
- Return only hashtags separated by spaces.
- Include the # symbol.
"""

    hashtags, error = ask_ai(
        prompt
    )

    if error:

        return jsonify({
            "success": False,
            "message": error
        }), 500

    return jsonify({
        "success": True,
        "hashtags": hashtags
    })
# =========================================================
# AI MCQ GENERATOR
# =========================================================

@app.route(
    "/api/generate-mcq",
    methods=["POST"]
)
@app.route(
    "/api/mcq-generator",
    methods=["POST"]
)
def generate_mcq():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401


    data = request.get_json(
        silent=True
    ) or {}


    subject = str(
        data.get("subject", "")
    ).strip()


    topic = str(
        data.get("topic", "")
    ).strip()


    difficulty = str(
        data.get(
            "difficulty",
            "Medium"
        )
    ).strip()
    language = str(
    data.get(
        "language",
        "English"
    )
).strip()


    try:

        count = int(
            data.get(
                "count",
                10
            )
        )

    except (TypeError, ValueError):

        count = 10


    if not subject:

        return jsonify({
            "success": False,
            "message": "Please enter a subject."
        }), 400


    if not topic:

        return jsonify({
            "success": False,
            "message": "Please enter a topic."
        }), 400


    count = max(
        5,
        min(count, 30)
    )


    prompt = f"""
You are the NEXORA AI Exam Assistant.

Create exactly {count} multiple-choice questions.

Subject:
{subject}

Topic:
{topic}

Difficulty:
{difficulty}
Language:
{language}

IMPORTANT:
- Write the question, options, answer and explanation in the selected language.
- If Hindi is selected, use clear Hindi.
- If Hinglish is selected, use Hindi written in Roman script.

For EVERY question provide exactly:

Question
Option A
Option B
Option C
Option D
Correct answer
Explanation

IMPORTANT:
- Every question must be different.
- Every question must have exactly 4 options.
- Only ONE option can be correct.
- The correct answer must be one of A, B, C or D.
- Make questions factually accurate.
- Match the requested difficulty.
- Do not repeat questions.
- Do not use markdown.
- Return ONLY valid JSON.

Use this exact JSON structure:

[
  {{
    "question": "Question text",
    "options": {{
      "A": "Option A",
      "B": "Option B",
      "C": "Option C",
      "D": "Option D"
    }},
    "answer": "A",
    "explanation": "Short explanation"
  }}
]
"""


    result, error = ask_ai(
        prompt
    )


    if error:

        return jsonify({
            "success": False,
            "message": error
        }), 500


    try:

        questions = json.loads(
            result
        )


    except json.JSONDecodeError:

        # Try to extract JSON if model
        # returned extra text.

        start = result.find("[")

        end = result.rfind("]") + 1


        if start == -1 or end <= start:

            return jsonify({
                "success": False,
                "message":
                    "AI returned invalid MCQ data."
            }), 500


        try:

            questions = json.loads(
                result[start:end]
            )

        except json.JSONDecodeError:

            return jsonify({
                "success": False,
                "message":
                    "Could not read AI questions."
            }), 500


    if not isinstance(
        questions,
        list
    ):

        return jsonify({
            "success": False,
            "message":
                "Invalid question format."
        }), 500


    cleaned_questions = []


    for item in questions:

        if not isinstance(
            item,
            dict
        ):

            continue


        question = str(
            item.get(
                "question",
                ""
            )
        ).strip()


        options = item.get(
            "options",
            {}
        )


        answer = str(
            item.get(
                "answer",
                ""
            )
        ).strip().upper()


        explanation = str(
            item.get(
                "explanation",
                ""
            )
        ).strip()


        if not question:

            continue


        if not isinstance(
            options,
            dict
        ):

            continue


        required_options = [
            "A",
            "B",
            "C",
            "D"
        ]


        if not all(
            key in options
            for key in required_options
        ):

            continue


        if answer not in required_options:

            continue


        cleaned_questions.append({

            "question":
                question,

            "options": {

                "A":
                    str(options["A"]),

                "B":
                    str(options["B"]),

                "C":
                    str(options["C"]),

                "D":
                    str(options["D"])

            },

            "answer":
                answer,

            "explanation":
                explanation

        })


    if not cleaned_questions:

        return jsonify({
            "success": False,
            "message":
                "No valid questions were generated."
        }), 500


    user = User.query.get(session["user_id"])
    if user:
        user.mcqs_practiced = (user.mcqs_practiced or 0) + len(cleaned_questions)
        db.session.commit()

    return jsonify({

        "success": True,

        "questions":
            cleaned_questions

    })





# =========================================================
# AI TEST
# =========================================================

@app.route(
    "/api/ai-test",
    methods=["POST"]
)
def ai_test():

    if not login_required():

        return jsonify({

            "success": False,

            "message":
                "Login required"

        }), 401


    data = request.get_json(
        silent=True
    ) or {}


    prompt = str(
        data.get(
            "prompt",
            ""
        )
    ).strip()


    if not prompt:

        return jsonify({

            "success": False,

            "message":
                "Please provide a prompt."

        }), 400


    response, error = ask_ai(
        prompt
    )


    if error:

        return jsonify({

            "success": False,

            "message":
                error

        }), 500


    return jsonify({

        "success": True,

        "response":
            response

    })





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
