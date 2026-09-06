# ============================================================
# KISANVISION360+
# AI-POWERED SMART FARMING PLATFORM
# ============================================================
#
# Main Flask Application
#
# Architecture:
#   Flask
#   PostgreSQL / Supabase
#   Modular Blueprints
#   Global Multilingual System
#   AI Disease Detection
#   Weather Intelligence
#   Crop Recommendation
#   Smart Irrigation
#   Mandi Intelligence
#   Marketplace
#   Finance
#   Government Schemes
#   Notifications
#   AI Chatbot
#
# ============================================================

import os
from pathlib import Path
from datetime import datetime

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    session,
    request,
    jsonify,
    flash,
)
from werkzeug.utils import secure_filename


# ============================================================
# APPLICATION PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# ENVIRONMENT
# ============================================================

try:
    from dotenv import load_dotenv

    load_dotenv(
        BASE_DIR / ".env"
    )

except Exception as e:
    print(
        "DOTENV WARNING:",
        e
    )


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)


# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = os.getenv(
    "SECRET_KEY",
    "CHANGE_THIS_KISANVISION360_SECRET_KEY"
)


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app.config["MAX_CONTENT_LENGTH"] = (
    10 * 1024 * 1024
)

app.config["JSON_SORT_KEYS"] = False

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

if os.getenv(
    "FLASK_ENV",
    "development"
).lower() == "production":

    app.config[
        "SESSION_COOKIE_SECURE"
    ] = True

else:

    app.config[
        "SESSION_COOKIE_SECURE"
    ] = False


# ============================================================
# APPLICATION INFORMATION
# ============================================================

APP_NAME = "KisanVision360+"

APP_VERSION = "2.0.0"

APP_DESCRIPTION = (
    "AI-Powered Smart Farming Platform"
)


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = {

    "en": "English",

    "hi": "Hindi",

    "mr": "Marathi",

    "kn": "Kannada",

    "te": "Telugu",

    "ta": "Tamil",

    "ml": "Malayalam",

    "gu": "Gujarati",

    "pa": "Punjabi",

    "bn": "Bengali",

    "as": "Assamese",

    "or": "Odia",

    "ur": "Urdu",

    "ne": "Nepali",

    "sa": "Sanskrit",

    "kok": "Konkani",

    "mai": "Maithili",

    "ks": "Kashmiri",

    "sd": "Sindhi",

    "mni": "Manipuri",
}


RTL_LANGUAGES = {
    "ur",
    "ks",
    "sd",
}


# ============================================================
# UPLOAD DIRECTORIES
# ============================================================

UPLOAD_FOLDER = (
    BASE_DIR
    / "static"
    / "uploads"
)

PRODUCT_UPLOAD_FOLDER = (
    UPLOAD_FOLDER
    / "products"
)

DISEASE_UPLOAD_FOLDER = (
    UPLOAD_FOLDER
    / "disease"
)

PROFILE_UPLOAD_FOLDER = (
    UPLOAD_FOLDER
    / "profiles"
)


for folder in [

    UPLOAD_FOLDER,

    PRODUCT_UPLOAD_FOLDER,

    DISEASE_UPLOAD_FOLDER,

    PROFILE_UPLOAD_FOLDER,

]:

    folder.mkdir(
        parents=True,
        exist_ok=True
    )


app.config[
    "UPLOAD_FOLDER"
] = str(UPLOAD_FOLDER)

app.config[
    "PRODUCT_UPLOAD_FOLDER"
] = str(
    PRODUCT_UPLOAD_FOLDER
)

app.config[
    "DISEASE_UPLOAD_FOLDER"
] = str(
    DISEASE_UPLOAD_FOLDER
)

app.config[
    "PROFILE_UPLOAD_FOLDER"
] = str(
    PROFILE_UPLOAD_FOLDER
)


# ============================================================
# MAIL
# ============================================================

try:

    from flask_mail import Mail

    app.config[
        "MAIL_SERVER"
    ] = os.getenv(
        "MAIL_SERVER",
        "smtp.gmail.com"
    )

    app.config[
        "MAIL_PORT"
    ] = int(
        os.getenv(
            "MAIL_PORT",
            "587"
        )
    )

    app.config[
        "MAIL_USE_TLS"
    ] = (
        os.getenv(
            "MAIL_USE_TLS",
            "true"
        ).lower()
        == "true"
    )

    app.config[
        "MAIL_USERNAME"
    ] = os.getenv(
        "MAIL_USERNAME",
        ""
    )

    app.config[
        "MAIL_PASSWORD"
    ] = os.getenv(
        "MAIL_PASSWORD",
        ""
    )

    app.config[
        "MAIL_DEFAULT_SENDER"
    ] = os.getenv(
        "MAIL_DEFAULT_SENDER",
        app.config[
            "MAIL_USERNAME"
        ]
    )

    mail = Mail(app)

except Exception as e:

    mail = None

    print(
        "MAIL WARNING:",
        e
    )


# ============================================================
# DATABASE
# ============================================================

try:

    from database.db import (
        get_db_connection,
        init_db,
        test_connection,
        database_health,
    )

    DATABASE_AVAILABLE = True

except Exception as e:

    get_db_connection = None

    init_db = None

    test_connection = None

    database_health = None

    DATABASE_AVAILABLE = False

    print(
        "DATABASE IMPORT ERROR:",
        e
    )


# ============================================================
# BLUEPRINT REGISTRATION HELPER
# ============================================================

REGISTERED_BLUEPRINTS = []


def register_blueprint_safe(
    module_path,
    blueprint_variable,
    display_name
):

    try:

        module_name = module_path

        module = __import__(
            module_name,
            fromlist=[
                blueprint_variable
            ]
        )

        blueprint = getattr(
            module,
            blueprint_variable
        )

        app.register_blueprint(
            blueprint
        )

        REGISTERED_BLUEPRINTS.append(
            display_name
        )

        print(
            f"[OK] {display_name}"
        )

        return True

    except Exception as e:

        print(
            f"[ERROR] {display_name}"
        )

        print(
            "       ",
            repr(e)
        )

        return False


# ============================================================
# AUTHENTICATION
# ============================================================

register_blueprint_safe(
    "routes.auth",
    "auth_bp",
    "Authentication"
)


# ============================================================
# FARMER
# ============================================================

register_blueprint_safe(
    "routes.farmer",
    "farmer_bp",
    "Farmer"
)


# ============================================================
# CONSUMER
# ============================================================

register_blueprint_safe(
    "routes.consumer",
    "consumer_bp",
    "Consumer"
)


# ============================================================
# ADMIN
# ============================================================

register_blueprint_safe(
    "routes.admin",
    "admin_bp",
    "Admin"
)


# ============================================================
# WEATHER
# ============================================================

register_blueprint_safe(
    "routes.weather",
    "weather_bp",
    "Weather"
)


# ============================================================
# CROP
# ============================================================

register_blueprint_safe(
    "routes.crop",
    "crop_bp",
    "Crop"
)


# ============================================================
# CROP RECOMMENDATION
# ============================================================

register_blueprint_safe(
    "routes.recommendation",
    "recommendation_bp",
    "AI Crop Recommendation"
)


# ============================================================
# SMART IRRIGATION
# ============================================================

register_blueprint_safe(
    "routes.irrigation",
    "irrigation_bp",
    "Smart Irrigation"
)


# ============================================================
# DISEASE DETECTION
# ============================================================

register_blueprint_safe(
    "routes.disease",
    "disease_bp",
    "AI Disease Detection"
)


# ============================================================
# MARKET
# ============================================================

register_blueprint_safe(
    "routes.market",
    "market_bp",
    "Mandi Market"
)


# ============================================================
# MARKETPLACE
# ============================================================

register_blueprint_safe(
    "routes.marketplace",
    "marketplace_bp",
    "Marketplace"
)


# ============================================================
# FINANCE
# ============================================================

register_blueprint_safe(
    "routes.finance",
    "finance_bp",
    "Finance"
)


# ============================================================
# GOVERNMENT SCHEMES
# ============================================================

register_blueprint_safe(
    "routes.government",
    "government_bp",
    "Government Schemes"
)


# ============================================================
# NOTIFICATIONS
# ============================================================

register_blueprint_safe(
    "routes.notifications",
    "notifications_bp",
    "Notifications"
)


# ============================================================
# AI CHATBOT
# ============================================================

register_blueprint_safe(
    "routes.chatbot",
    "chatbot_bp",
    "AI Chatbot"
)


# ============================================================
# PROFILE
# ============================================================

register_blueprint_safe(
    "routes.profile",
    "profile_bp",
    "Profile"
)


# ============================================================
# SETTINGS
# ============================================================

register_blueprint_safe(
    "routes.settings",
    "settings_bp",
    "Settings"
)


# ============================================================
# REPORTS
# ============================================================

register_blueprint_safe(
    "routes.reports",
    "reports_bp",
    "Reports"
)


# ============================================================
# TOOLS
# ============================================================

register_blueprint_safe(
    "routes.tools",
    "tools_bp",
    "Farmer Tools"
)


# ============================================================
# HELP
# ============================================================

register_blueprint_safe(
    "routes.help",
    "help_bp",
    "Help & Support"
)


# ============================================================
# GLOBAL TEMPLATE DATA
# ============================================================

@app.context_processor
def global_template_data():

    language = session.get(
        "language",
        "en"
    )

    if language not in SUPPORTED_LANGUAGES:

        language = "en"

    role = str(
        session.get(
            "role",
            ""
        )
        or ""
    ).strip().lower()

    return {

        "app_name":
            APP_NAME,

        "app_version":
            APP_VERSION,

        "app_description":
            APP_DESCRIPTION,

        "current_language":
            language,

        "current_language_name":
            SUPPORTED_LANGUAGES.get(
                language,
                "English"
            ),

        "supported_languages":
            SUPPORTED_LANGUAGES,

        "rtl":
            language in RTL_LANGUAGES,

        "is_rtl":
            language in RTL_LANGUAGES,

        "current_role":
            role,

        "current_user_id":
            session.get(
                "user_id"
            ),

        "current_user_name":
            session.get(
                "name",
                "User"
            ),

    }


# ============================================================
# LANGUAGE FILTER
# ============================================================

@app.template_filter(
    "language_name"
)
def language_name(code):

    return SUPPORTED_LANGUAGES.get(
        code,
        "English"
    )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    return redirect(
        url_for(
            "auth.language"
        )
    )


# ============================================================
# DASHBOARD COMPATIBILITY ROUTE
# ============================================================

@app.route(
    "/dashboard"
)
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    role = str(
        session.get(
            "role",
            ""
        )
        or ""
    ).lower().strip()

    if role == "farmer":

        return redirect(
            url_for(
                "farmer.farmer"
            )
        )

    if role == "consumer":

        return redirect(
            url_for(
                "consumer.consumer"
            )
        )

    if role == "admin":

        return redirect(
            url_for(
                "admin.admin"
            )
        )

    session.clear()

    return redirect(
        url_for(
            "auth.login"
        )
    )


# ============================================================
# PROFILE IMAGE COMPATIBILITY
# ============================================================

@app.route(
    "/upload-profile",
    methods=["POST"]
)
def upload_profile():

    if "user_id" not in session:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    uploaded_file = request.files.get(
        "profile"
    )

    if not uploaded_file:

        flash(
            "Please select a profile image.",
            "warning"
        )

        return redirect(
            url_for(
                "profile.profile"
            )
        )

    if not uploaded_file.filename:

        flash(
            "Please select a valid image.",
            "warning"
        )

        return redirect(
            url_for(
                "profile.profile"
            )
        )

    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }

    filename = secure_filename(
        uploaded_file.filename
    )

    extension = (
        filename.rsplit(
            ".",
            1
        )[-1].lower()
        if "." in filename
        else ""
    )

    if extension not in allowed_extensions:

        flash(
            "Only JPG, JPEG, PNG and WEBP images are allowed.",
            "danger"
        )

        return redirect(
            url_for(
                "profile.profile"
            )
        )

    user_id = session.get(
        "user_id"
    )

    safe_filename = (
        f"user_{user_id}_"
        f"{int(datetime.now().timestamp())}."
        f"{extension}"
    )

    filepath = (
        PROFILE_UPLOAD_FOLDER
        / safe_filename
    )

    try:

        uploaded_file.save(
            str(filepath)
        )

        image_url = (
            "/static/uploads/profiles/"
            + safe_filename
        )

        if get_db_connection:

            conn = None

            try:

                conn = get_db_connection()

                cur = conn.cursor()

                # Check available profile column
                cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                    AND column_name IN
                    ('profile_pic', 'profile_image')
                    """
                )

                columns = [
                    row[0]
                    for row in cur.fetchall()
                ]

                if "profile_pic" in columns:

                    cur.execute(
                        """
                        UPDATE users
                        SET profile_pic = %s
                        WHERE id = %s
                        """,
                        (
                            image_url,
                            user_id
                        )
                    )

                elif "profile_image" in columns:

                    cur.execute(
                        """
                        UPDATE users
                        SET profile_image = %s
                        WHERE id = %s
                        """,
                        (
                            image_url,
                            user_id
                        )
                    )

                conn.commit()

            except Exception as e:

                if conn:

                    conn.rollback()

                print(
                    "PROFILE IMAGE DATABASE ERROR:",
                    e
                )

            finally:

                if conn:

                    conn.close()

        flash(
            "Profile image updated successfully.",
            "success"
        )

    except Exception as e:

        print(
            "PROFILE IMAGE ERROR:",
            e
        )

        flash(
            "Unable to upload profile image.",
            "danger"
        )

    return redirect(
        url_for(
            "profile.profile"
        )
    )


# ============================================================
# CALCULATOR
# ============================================================

@app.route(
    "/calculator",
    methods=["GET", "POST"]
)
def calculator():

    if "user_id" not in session:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    result = None

    if request.method == "POST":

        try:

            value1 = float(
                request.form.get(
                    "value1",
                    "0"
                )
            )

            value2 = float(
                request.form.get(
                    "value2",
                    "0"
                )
            )

            operation = request.form.get(
                "operation",
                "add"
            )

            if operation == "add":

                result = value1 + value2

            elif operation == "subtract":

                result = value1 - value2

            elif operation == "multiply":

                result = value1 * value2

            elif operation == "divide":

                if value2 == 0:

                    result = (
                        "Cannot divide by zero"
                    )

                else:

                    result = (
                        value1 / value2
                    )

            else:

                result = (
                    "Invalid operation"
                )

        except Exception:

            result = (
                "Invalid input"
            )

    return render_template(
        "calculator.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        result=result
    )


# ============================================================
# EMI COMPATIBILITY PAGE
# ============================================================

@app.route(
    "/emi"
)
def emi():

    if "user_id" not in session:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    try:

        return render_template(
            "emi.html",
            name=session.get(
                "name",
                "Farmer"
            )
        )

    except Exception:

        return redirect(
            url_for(
                "finance.finance"
            )
        )


# ============================================================
# ALERTS COMPATIBILITY
# ============================================================

@app.route(
    "/alerts"
)
def alerts():

    if "user_id" not in session:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    try:

        return render_template(
            "alerts.html",
            name=session.get(
                "name",
                "Farmer"
            )
        )

    except Exception:

        return redirect(
            url_for(
                "notifications.notifications"
            )
        )


# ============================================================
# CONSUMER REQUEST
# ============================================================

@app.route(
    "/consumer-request",
    methods=["GET", "POST"]
)
def consumer_request():

    if "user_id" not in session:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    role = str(
        session.get(
            "role",
            ""
        )
        or ""
    ).lower().strip()

    if role != "farmer":

        return redirect(
            url_for(
                "dashboard"
            )
        )

    consumer_requests = []

    return render_template(
        "consumer_request.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        consumer_requests=
            consumer_requests,
        requests=
            consumer_requests,
        prices=[]
    )


# ============================================================
# EDIT PROFILE COMPATIBILITY
# ============================================================

@app.route(
    "/edit-profile",
    methods=["GET", "POST"]
)
def edit_profile():

    if "user_id" not in session:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        user_id = session.get(
            "user_id"
        )

        if get_db_connection:

            conn = None

            try:

                conn = get_db_connection()

                cur = conn.cursor()

                cur.execute(
                    """
                    UPDATE users
                    SET
                        name = COALESCE(%s, name),
                        mobile = %s,
                        email = %s
                    WHERE id = %s
                    """,
                    (
                        name or None,
                        mobile,
                        email,
                        user_id
                    )
                )

                conn.commit()

                session["name"] = name

                session["mobile"] = mobile

                session["email"] = email

                flash(
                    "Profile updated successfully.",
                    "success"
                )

            except Exception as e:

                if conn:

                    conn.rollback()

                print(
                    "EDIT PROFILE ERROR:",
                    e
                )

                flash(
                    "Unable to update profile.",
                    "danger"
                )

            finally:

                if conn:

                    conn.close()

        return redirect(
            url_for(
                "profile.profile"
            )
        )

    return render_template(
        "edit-profile.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        mobile=session.get(
            "mobile",
            ""
        ),
        email=session.get(
            "email",
            ""
        ),
        location=session.get(
            "location",
            "Nagpur"
        )
    )


# ============================================================
# GLOBAL APP INFORMATION
# ============================================================

@app.route(
    "/api/app-info",
    methods=["GET"]
)
def app_info():

    return jsonify({

        "success": True,

        "application":
            APP_NAME,

        "version":
            APP_VERSION,

        "description":
            APP_DESCRIPTION,

        "language_count":
            len(
                SUPPORTED_LANGUAGES
            ),

        "languages":
            SUPPORTED_LANGUAGES,

        "roles": [
            "farmer",
            "consumer",
            "admin"
        ],

        "features": [

            "Global Language System",

            "20 Indian Languages",

            "AI Crop Recommendation",

            "Crop Suitability Score",

            "Weather Intelligence",

            "Weather-aware Planning",

            "Disease Detection",

            "Smart Irrigation",

            "Mandi Market Intelligence",

            "Farmer Marketplace",

            "Finance Management",

            "Government Schemes",

            "Smart Notifications",

            "AI Chatbot",

            "Farm Profile",

            "Reports",

            "Farmer Tools",

        ],

    })


# ============================================================
# APPLICATION HEALTH
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    database_status = (
        "not_configured"
    )

    if test_connection:

        try:

            result = test_connection()

            if isinstance(
                result,
                dict
            ):

                if result.get(
                    "success"
                ):

                    database_status = (
                        "connected"
                    )

                else:

                    database_status = (
                        "error"
                    )

            else:

                database_status = (
                    "connected"
                )

        except Exception as e:

            print(
                "HEALTH DATABASE ERROR:",
                e
            )

            database_status = (
                "error"
            )

    return jsonify({

        "success": True,

        "status": "healthy",

        "application":
            APP_NAME,

        "version":
            APP_VERSION,

        "database":
            database_status,

        "database_url_configured":
            bool(
                os.getenv(
                    "DATABASE_URL"
                )
            ),

        "weather_api_configured":
            bool(
                os.getenv(
                    "OPENWEATHER_API_KEY"
                )
            ),

        "disease_model_exists":
            (
                BASE_DIR
                / "ai_models"
                / "disease_model.keras"
            ).exists(),

        "registered_blueprints":
            REGISTERED_BLUEPRINTS,

    })


# ============================================================
# DATABASE HEALTH
# ============================================================

@app.route(
    "/api/database/health",
    methods=["GET"]
)
def database_health_route():

    try:

        if database_health:

            result = database_health()

            return jsonify(
                result
            )

        if test_connection:

            result = test_connection()

            return jsonify({
                "success": True,
                "database": result
            })

        return jsonify({

            "success": False,

            "message":
                "Database service unavailable"

        }), 503

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                "Database health check failed",

            "error":
                str(e)

        }), 500


# ============================================================
# ROUTE MAP API
# ============================================================

@app.route(
    "/api/routes",
    methods=["GET"]
)
def route_map():

    routes = []

    for rule in app.url_map.iter_rules():

        routes.append({

            "endpoint":
                rule.endpoint,

            "path":
                str(rule),

            "methods":
                sorted(
                    rule.methods
                    or []
                ),

        })

    routes.sort(
        key=lambda item:
            item["path"]
    )

    return jsonify({

        "success": True,

        "count":
            len(routes),

        "routes":
            routes,

    })


# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def not_found(error):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success": False,

            "message":
                "API endpoint not found",

            "path":
                request.path,

        }), 404

    try:

        return render_template(
            "404.html"
        ), 404

    except Exception:

        return (
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>404</title>
            </head>
            <body>
                <h1>404 - Page Not Found</h1>
                <a href="/">Go Home</a>
            </body>
            </html>
            """,
            404
        )


# ============================================================
# 405 ERROR
# ============================================================

@app.errorhandler(405)
def method_not_allowed(error):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success": False,

            "message":
                "HTTP method not allowed",

            "path":
                request.path,

        }), 405

    return (
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>405</title>
        </head>
        <body>
            <h1>405 - Method Not Allowed</h1>
        </body>
        </html>
        """,
        405
    )


# ============================================================
# 413 ERROR
# ============================================================

@app.errorhandler(413)
def request_entity_too_large(error):

    return jsonify({

        "success": False,

        "message":
            "File too large. Maximum allowed size is 10 MB."

    }), 413


# ============================================================
# 500 ERROR
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    print(
        "INTERNAL SERVER ERROR:",
        repr(error)
    )

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success": False,

            "message":
                "Internal server error"

        }), 500

    try:

        return render_template(
            "500.html"
        ), 500

    except Exception:

        return (
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>500</title>
            </head>
            <body>
                <h1>500 - Internal Server Error</h1>
            </body>
            </html>
            """,
            500
        )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    print("")
    print(
        "=" * 70
    )

    print(
        "DATABASE INITIALIZATION"
    )

    print(
        "=" * 70
    )

    if not init_db:

        print(
            "[WARNING] Database module unavailable."
        )

        return

    try:

        init_db()

        print(
            "[OK] PostgreSQL database initialized."
        )

    except Exception as e:

        print(
            "[WARNING] Database initialization failed:"
        )

        print(
            repr(e)
        )

        print(
            "Application will continue."
        )

    print(
        "=" * 70
    )


# ============================================================
# STARTUP INFORMATION
# ============================================================

def print_startup_information():

    print("")
    print(
        "=" * 70
    )

    print(
        "        KISANVISION360+"
    )

    print(
        "        AI-POWERED SMART FARMING PLATFORM"
    )

    print(
        "=" * 70
    )

    print(
        "Version:",
        APP_VERSION
    )

    print(
        "Project:",
        BASE_DIR
    )

    print(
        "Database:",
        (
            "PostgreSQL / Supabase"
            if os.getenv(
                "DATABASE_URL"
            )
            else
            "DATABASE_URL not configured"
        )
    )

    print(
        "Weather API:",
        (
            "Configured"
            if os.getenv(
                "OPENWEATHER_API_KEY"
            )
            else
            "Not configured"
        )
    )

    print(
        "Disease Model:",
        (
            "Found"
            if (
                BASE_DIR
                / "ai_models"
                / "disease_model.keras"
            ).exists()
            else
            "Not found"
        )
    )

    print(
        "Languages:",
        len(
            SUPPORTED_LANGUAGES
        )
    )

    print(
        "Blueprints:",
        len(
            REGISTERED_BLUEPRINTS
        )
    )

    print(
        "=" * 70
    )

    print(
        "MAIN URLS"
    )

    print(
        "Home             : /"
    )

    print(
        "Language         : /language"
    )

    print(
        "Login            : /login"
    )

    print(
        "Signup           : /signup"
    )

    print(
        "Dashboard        : /dashboard"
    )

    print(
        "Farmer           : /farmer"
    )

    print(
        "Consumer         : /consumer"
    )

    print(
        "Admin            : /admin"
    )

    print(
        "Weather          : /weather"
    )

    print(
        "Crop Advisor     : /recommendation"
    )

    print(
        "Disease          : /disease"
    )

    print(
        "Irrigation       : /irrigation"
    )

    print(
        "Market           : /market"
    )

    print(
        "Marketplace      : /marketplace"
    )

    print(
        "Finance          : /finance"
    )

    print(
        "Government       : /government"
    )

    print(
        "Notifications    : /notifications"
    )

    print(
        "Reports          : /reports"
    )

    print(
        "Chatbot          : /chatbot"
    )

    print(
        "Profile          : /profile"
    )

    print(
        "Settings         : /settings"
    )

    print(
        "Tools            : /tools"
    )

    print(
        "Help             : /help"
    )

    print(
        "Health           : /health"
    )

    print(
        "=" * 70
    )

    print("")


# ============================================================
# DATABASE STARTUP
# ============================================================

initialize_database()


# ============================================================
# DEVELOPMENT RUN
# ============================================================

if __name__ == "__main__":

    print_startup_information()

    host = os.getenv(
        "HOST",
        "127.0.0.1"
    )

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    debug = (
        os.getenv(
            "FLASK_DEBUG",
            "false"
        ).lower()
        == "true"
    )

    print(
        f"Starting {APP_NAME}..."
    )

    print(
        f"Open: http://127.0.0.1:{port}"
    )

    print(
        "Debug:",
        debug
    )

    print("")

    app.run(
        host=host,
        port=port,
        debug=debug
    )
