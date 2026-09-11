# ============================================================
# KISANVISION360+
# app.py
# Main Flask Application
# PostgreSQL / Supabase
# Blueprint Based Architecture
# ============================================================

import os
import traceback

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify,
    url_for,
    flash,
    send_from_directory,
)

from dotenv import load_dotenv


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

ENV_FILE = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(
    ENV_FILE,
    override=True
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)


# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = os.getenv(
    "SECRET_KEY",
    "kisanvision360-development-secret-key-change-this"
)


# ============================================================
# SESSION CONFIGURATION
# ============================================================

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

if os.getenv("FLASK_ENV", "").lower() == "production":
    app.config["SESSION_COOKIE_SECURE"] = True
else:
    app.config["SESSION_COOKIE_SECURE"] = False


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app.config["APP_NAME"] = "KisanVision360+"
app.config["APP_VERSION"] = "2.0.0"

app.config["MAX_CONTENT_LENGTH"] = (
    10 * 1024 * 1024
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

app.config["DATABASE_URL"] = os.getenv(
    "DATABASE_URL",
    ""
)


# ============================================================
# WEATHER CONFIGURATION
# ============================================================

app.config["OPENWEATHER_API_KEY"] = os.getenv(
    "OPENWEATHER_API_KEY",
    ""
)

app.config["DEFAULT_CITY"] = os.getenv(
    "DEFAULT_CITY",
    "Nagpur"
)

from routes.tools import tools_bp

app.register_blueprint(tools_bp)
# ============================================================
# MAIL CONFIGURATION
# ============================================================

app.config["MAIL_SERVER"] = os.getenv(
    "MAIL_SERVER",
    "smtp.gmail.com"
)

try:

    app.config["MAIL_PORT"] = int(
        os.getenv(
            "MAIL_PORT",
            "587"
        )
    )

except Exception:

    app.config["MAIL_PORT"] = 587


app.config["MAIL_USE_TLS"] = (
    os.getenv(
        "MAIL_USE_TLS",
        "true"
    ).lower() == "true"
)

app.config["MAIL_USERNAME"] = os.getenv(
    "MAIL_USERNAME",
    ""
)

app.config["MAIL_PASSWORD"] = os.getenv(
    "MAIL_PASSWORD",
    ""
)


# ============================================================
# UPLOAD DIRECTORIES
# ============================================================

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

PRODUCT_UPLOAD_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "products"
)

DISEASE_UPLOAD_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "disease"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    PRODUCT_UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    DISEASE_UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PRODUCT_UPLOAD_FOLDER"] = PRODUCT_UPLOAD_FOLDER
app.config["DISEASE_UPLOAD_FOLDER"] = DISEASE_UPLOAD_FOLDER


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = {
    "en",
    "hi",
    "mr",
    "kn",
    "te",
    "ta",
    "ml",
    "gu",
    "pa",
    "bn",
    "as",
    "or",
    "ur",
    "ne",
    "sa",
    "kok",
    "mai",
    "ks",
    "sd",
    "mni",
}


RTL_LANGUAGES = {
    "ur",
    "ks",
    "sd",
}


# ============================================================
# LANGUAGE NAMES
# ============================================================

LANGUAGE_NAMES = {

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


# ============================================================
# GLOBAL TEMPLATE CONTEXT
# ============================================================

@app.context_processor
def inject_global_context():

    language = session.get(
        "language",
        "en"
    )

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    direction = (
        "rtl"
        if language in RTL_LANGUAGES
        else "ltr"
    )

    return {

        "app_name":
            app.config["APP_NAME"],

        "app_version":
            app.config["APP_VERSION"],

        "current_language":
            language,

        "current_direction":
            direction,

        "supported_languages":
            SUPPORTED_LANGUAGES,

        "language_names":
            LANGUAGE_NAMES,

        "rtl_languages":
            RTL_LANGUAGES,

        "current_user_id":
            session.get("user_id"),

        "current_user_name":
            session.get(
                "name",
                "User"
            ),

        "current_role":
            str(
                session.get(
                    "role",
                    ""
                )
            ).lower().strip(),

        "is_logged_in":
            bool(
                session.get(
                    "user_id"
                )
            ),

    }


# ============================================================
# GLOBAL LANGUAGE BEFORE REQUEST
# ============================================================

@app.before_request
def set_global_language():

    language = session.get(
        "language",
        "en"
    )

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    session["language"] = language

    session["direction"] = (
        "rtl"
        if language in RTL_LANGUAGES
        else "ltr"
    )


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def initialize_database():

    try:

        from database.db import init_db

        result = init_db()

        print(
            "[DATABASE] INITIALIZATION:",
            result
        )

        return bool(result)

    except Exception as error:

        print()
        print("=" * 70)
        print(
            "[DATABASE] INITIALIZATION ERROR"
        )
        print("=" * 70)

        print(
            repr(error)
        )

        traceback.print_exc()

        print("=" * 70)

        return False


def test_database():

    try:

        from database.db import test_connection

        result = test_connection()

        if isinstance(
            result,
            dict
        ):

            return bool(
                result.get(
                    "success",
                    False
                )
            )

        return bool(result)

    except Exception as error:

        print(
            "[DATABASE] TEST ERROR:",
            repr(error)
        )

        return False


# ============================================================
# FINANCE SERVICE INITIALIZATION
# ============================================================

def initialize_finance_service_safe():

    try:

        from routes.finance import (
            initialize_finance_service
        )

        result = initialize_finance_service()

        print(
            "[OK] Finance service initialized:",
            result
        )

        return True

    except ImportError as error:

        print(
            "[WARNING] Finance initializer not found:",
            repr(error)
        )

        return False

    except Exception as error:

        print(
            "[ERROR] Finance service initialization failed:",
            repr(error)
        )

        traceback.print_exc()

        return False


# ============================================================
# BLUEPRINT REGISTRATION
# ============================================================

def register_blueprint_safe(
    blueprint,
    name
):

    try:

        if blueprint.name in app.blueprints:

            print(
                f"[SKIP] Blueprint already registered: {name}"
            )

            return True

        app.register_blueprint(
            blueprint
        )

        print(
            f"[OK] Blueprint registered: {name}"
        )

        return True

    except Exception as error:

        print(
            f"[ERROR] Blueprint failed: {name}"
        )

        print(
            repr(error)
        )

        traceback.print_exc()

        return False


# ============================================================
# REGISTER ALL BLUEPRINTS
# ============================================================

def register_all_blueprints():

    print()
    print("=" * 70)
    print(
        "KISANVISION360+ BLUEPRINT REGISTRATION"
    )
    print("=" * 70)


    # ========================================================
    # AUTH
    # ========================================================

    try:

        from routes.auth import auth_bp

        register_blueprint_safe(
            auth_bp,
            "auth"
        )

    except Exception as error:

        print(
            "[ERROR] auth blueprint:",
            repr(error)
        )


    # ========================================================
    # FARMER
    # ========================================================

    try:

        from routes.farmer import farmer_bp

        register_blueprint_safe(
            farmer_bp,
            "farmer"
        )

    except Exception as error:

        print(
            "[ERROR] farmer blueprint:",
            repr(error)
        )


    # ========================================================
    # CONSUMER
    # ========================================================

    try:

        from routes.consumer import consumer_bp

        register_blueprint_safe(
            consumer_bp,
            "consumer"
        )

    except Exception as error:

        print(
            "[ERROR] consumer blueprint:",
            repr(error)
        )


    # ========================================================
    # ADMIN
    # ========================================================

    try:

        from routes.admin import admin_bp

        register_blueprint_safe(
            admin_bp,
            "admin"
        )

    except Exception as error:

        print(
            "[ERROR] admin blueprint:",
            repr(error)
        )


    # ========================================================
    # WEATHER
    # ========================================================

    try:

        from routes.weather import weather_bp

        register_blueprint_safe(
            weather_bp,
            "weather"
        )

    except Exception as error:

        print(
            "[ERROR] weather blueprint:",
            repr(error)
        )


    # ========================================================
    # CROP
    # ========================================================

    try:

        from routes.crop import crop_bp

        register_blueprint_safe(
            crop_bp,
            "crop"
        )

    except Exception as error:

        print(
            "[ERROR] crop blueprint:",
            repr(error)
        )


    # ========================================================
    # RECOMMENDATION
    # ========================================================

    try:

        from routes.recommendation import recommendation_bp

        register_blueprint_safe(
            recommendation_bp,
            "recommendation"
        )

    except Exception as error:

        print(
            "[ERROR] recommendation blueprint:",
            repr(error)
        )


    # ========================================================
    # IRRIGATION
    # ========================================================

    try:

        from routes.irrigation import irrigation_bp

        register_blueprint_safe(
            irrigation_bp,
            "irrigation"
        )

    except Exception as error:

        print(
            "[ERROR] irrigation blueprint:",
            repr(error)
        )


    # ========================================================
    # DISEASE
    # ========================================================

    try:

        from routes.disease import disease_bp

        register_blueprint_safe(
            disease_bp,
            "disease"
        )

    except Exception as error:

        print(
            "[ERROR] disease blueprint:",
            repr(error)
        )


    # ========================================================
    # MARKET / MANDI
    # ========================================================

    try:

        from routes.market import market_bp

        register_blueprint_safe(
            market_bp,
            "market"
        )

    except Exception as error:

        print(
            "[ERROR] market blueprint:",
            repr(error)
        )


    # ========================================================
    # MARKETPLACE
    # ========================================================

    try:

        from routes.marketplace import marketplace_bp

        register_blueprint_safe(
            marketplace_bp,
            "marketplace"
        )

    except Exception as error:

        print(
            "[ERROR] marketplace blueprint:",
            repr(error)
        )


    # ========================================================
    # FINANCE
    # ========================================================

    try:

        from routes.finance import finance_bp

        register_blueprint_safe(
            finance_bp,
            "finance"
        )

    except Exception as error:

        print(
            "[ERROR] finance blueprint:",
            repr(error)
        )


    # ========================================================
    # GOVERNMENT
    # ========================================================

    try:

        from routes.government import government_bp

        register_blueprint_safe(
            government_bp,
            "government"
        )

    except Exception as error:

        print(
            "[ERROR] government blueprint:",
            repr(error)
        )


    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    try:

        from routes.notifications import notifications_bp

        register_blueprint_safe(
            notifications_bp,
            "notifications"
        )

    except Exception as error:

        print(
            "[ERROR] notifications blueprint:",
            repr(error)
        )

        # Compatibility with older blueprint name
        try:

            from routes.notifications import notification_bp

            register_blueprint_safe(
                notification_bp,
                "notifications"
            )

        except Exception as second_error:

            print(
                "[ERROR] notification compatibility:",
                repr(second_error)
            )


    # ========================================================
    # CHATBOT
    # ========================================================

    try:

        from routes.chatbot import chatbot_bp

        register_blueprint_safe(
            chatbot_bp,
            "chatbot"
        )

    except Exception as error:

        print(
            "[ERROR] chatbot blueprint:",
            repr(error)
        )


    # ========================================================
    # PROFILE
    # ========================================================

    try:

        from routes.profile import profile_bp

        register_blueprint_safe(
            profile_bp,
            "profile"
        )

    except Exception as error:

        print(
            "[ERROR] profile blueprint:",
            repr(error)
        )


    # ========================================================
    # SETTINGS
    # ========================================================

    try:

        from routes.settings import settings_bp

        register_blueprint_safe(
            settings_bp,
            "settings"
        )

    except Exception as error:

        print(
            "[ERROR] settings blueprint:",
            repr(error)
        )


    # ========================================================
    # REPORTS
    # ========================================================

    try:

        from routes.reports import reports_bp

        register_blueprint_safe(
            reports_bp,
            "reports"
        )

    except Exception as error:

        print(
            "[ERROR] reports blueprint:",
            repr(error)
        )


    # ========================================================
    # TOOLS
    # ========================================================

    try:

        from routes.tools import tools_bp

        register_blueprint_safe(
            tools_bp,
            "tools"
        )

    except Exception as error:

        print(
            "[ERROR] tools blueprint:",
            repr(error)
        )


    # ========================================================
    # HELP
    # ========================================================

    try:

        from routes.help import help_bp

        register_blueprint_safe(
            help_bp,
            "help"
        )

    except Exception as error:

        print(
            "[ERROR] help blueprint:",
            repr(error)
        )


    # ========================================================
    # PRINT REGISTERED BLUEPRINTS
    # ========================================================

    print()
    print(
        "REGISTERED BLUEPRINTS:"
    )

    print(
        list(
            app.blueprints.keys()
        )
    )

    print("=" * 70)
    print()


# ============================================================
# ROOT ROUTE
# ============================================================

@app.route("/")
def index():

    # ========================================================
    # LOGGED-IN USER
    # ========================================================

    if session.get("user_id"):

        role = str(
            session.get(
                "role",
                ""
            )
        ).lower().strip()


        # ----------------------------------------------------
        # FARMER
        # ----------------------------------------------------

        if role == "farmer":

            try:

                return redirect(
                    url_for(
                        "farmer.farmer"
                    )
                )

            except Exception:

                pass


        # ----------------------------------------------------
        # CONSUMER
        # ----------------------------------------------------

        elif role == "consumer":

            try:

                return redirect(
                    url_for(
                        "consumer.consumer"
                    )
                )

            except Exception:

                pass


        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        elif role == "admin":

            try:

                return redirect(
                    url_for(
                        "admin.admin"
                    )
                )

            except Exception:

                pass


    # ========================================================
    # GUEST
    # ========================================================

    try:

        return render_template(
            "splash.html"
        )

    except Exception as error:

        print(
            "[ROOT] splash.html error:",
            repr(error)
        )


    try:

        return render_template(
            "welcome.html"
        )

    except Exception as error:

        print(
            "[ROOT] welcome.html error:",
            repr(error)
        )


    try:

        return redirect(
            url_for(
                "auth.language"
            )
        )

    except Exception:

        return redirect(
            url_for(
                "auth.login"
            )
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    database_status = test_database()

    return jsonify({

        "success": True,

        "application":
            app.config["APP_NAME"],

        "version":
            app.config["APP_VERSION"],

        "database":
            database_status,

        "database_type":
            "PostgreSQL / Supabase",

        "status":
            (
                "healthy"
                if database_status
                else "degraded"
            ),

        "language":
            session.get(
                "language",
                "en"
            ),

        "logged_in":
            bool(
                session.get(
                    "user_id"
                )
            ),

    })


# ============================================================
# API HEALTH
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def api_health():

    database_status = test_database()

    return jsonify({

        "success":
            bool(database_status),

        "database":
            "PostgreSQL / Supabase",

        "connected":
            bool(database_status),

        "status":
            (
                "healthy"
                if database_status
                else "degraded"
            ),

    })


# ============================================================
# APPLICATION INFORMATION
# ============================================================

@app.route(
    "/api/app-info",
    methods=["GET"]
)
def app_info():

    return jsonify({

        "success": True,

        "application":
            app.config["APP_NAME"],

        "version":
            app.config["APP_VERSION"],

        "database":
            "PostgreSQL / Supabase",

        "language":
            session.get(
                "language",
                "en"
            ),

        "direction":
            session.get(
                "direction",
                "ltr"
            ),

        "role":
            session.get(
                "role"
            ),

        "user_id":
            session.get(
                "user_id"
            ),

        "logged_in":
            bool(
                session.get(
                    "user_id"
                )
            ),

        "features": [

            "Authentication",
            "Farmer Dashboard",
            "Consumer Dashboard",
            "Admin Dashboard",
            "Live Weather",
            "Crop Recommendation",
            "Disease Detection",
            "Smart Irrigation",
            "Mandi Market",
            "Marketplace",
            "Finance",
            "Government Schemes",
            "Notifications",
            "AI Chatbot",
            "Reports",
            "Settings",
            "20 Languages",

        ]

    })


# ============================================================
# FAVICON
# ============================================================

@app.route(
    "/favicon.ico"
)
def favicon():

    image_folder = os.path.join(
        BASE_DIR,
        "static",
        "images"
    )

    logo_file = os.path.join(
        image_folder,
        "logo.png"
    )

    if os.path.exists(
        logo_file
    ):

        return send_from_directory(
            image_folder,
            "logo.png"
        )

    return (
        "",
        204
    )


# ============================================================
# COMPATIBILITY: EMI
# ============================================================

@app.route(
    "/emi",
    methods=["GET"]
)
def compatibility_emi():

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

        try:

            return redirect(
                url_for(
                    "farmer.farmer"
                )
            )

        except Exception:

            return redirect(
                url_for(
                    "auth.login"
                )
            )


# ============================================================
# COMPATIBILITY: ALERTS
# ============================================================

@app.route(
    "/alerts",
    methods=["GET"]
)
def compatibility_alerts():

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

        try:

            return redirect(
                url_for(
                    "notifications.notifications"
                )
            )

        except Exception:

            return redirect(
                url_for(
                    "auth.login"
                )
            )


# ============================================================
# COMPATIBILITY: CONSUMER REQUEST
# ============================================================

@app.route(
    "/consumer-request",
    methods=["GET", "POST"]
)
def compatibility_consumer_request():

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
    ).lower().strip()


    if role != "farmer":

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

        return redirect(
            url_for(
                "auth.login"
            )
        )


    try:

        return render_template(
            "consumer_request.html",
            name=session.get(
                "name",
                "Farmer"
            ),
            consumer_requests=[],
            requests=[]
        )

    except Exception:

        return redirect(
            url_for(
                "farmer.farmer"
            )
        )


# ============================================================
# DEBUG ROUTES
# ============================================================

@app.route(
    "/debug/routes",
    methods=["GET"]
)
def debug_routes():

    routes = []

    for rule in app.url_map.iter_rules():

        routes.append({

            "endpoint":
                rule.endpoint,

            "methods":
                sorted(
                    list(
                        rule.methods
                    )
                ),

            "path":
                str(rule),

        })

    routes.sort(
        key=lambda x: x["path"]
    )

    return jsonify({
        "success": True,
        "routes": routes
    })


# ============================================================
# 404 HANDLER
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success": False,

            "error":
                "Endpoint not found",

            "path":
                request.path

        }), 404

    try:

        return render_template(
            "404.html"
        ), 404

    except Exception:

        return (
            "404 - Page Not Found",
            404
        )


# ============================================================
# 413 HANDLER
# ============================================================

@app.errorhandler(413)
def request_too_large(error):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success": False,

            "error":
                "Uploaded file is too large. "
                "Maximum size is 10 MB."

        }), 413

    flash(
        "Uploaded file is too large. Maximum size is 10 MB.",
        "error"
    )

    return redirect(
        request.referrer
        or url_for("auth.login")
    )


# ============================================================
# 500 HANDLER
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    print()
    print("=" * 70)
    print(
        "INTERNAL SERVER ERROR"
    )
    print("=" * 70)

    print(
        traceback.format_exc()
    )

    print("=" * 70)

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success": False,

            "error":
                "Internal server error"

        }), 500

    try:

        return render_template(
            "500.html"
        ), 500

    except Exception:

        return (
            "500 - Internal Server Error",
            500
        )


# ============================================================
# STARTUP
# ============================================================

def startup():

    print()
    print("=" * 70)
    print(
        "              KISANVISION360+"
    )
    print("=" * 70)

    print(
        "Project:",
        BASE_DIR
    )

    print(
        "Database:",
        "PostgreSQL / Supabase"
    )

    print(
        "Database URL:",
        (
            "CONFIGURED"
            if app.config["DATABASE_URL"]
            else "NOT CONFIGURED"
        )
    )

    print(
        "Default City:",
        app.config["DEFAULT_CITY"]
    )

    print(
        "Supported Languages:",
        len(SUPPORTED_LANGUAGES)
    )

    print(
        "RTL Languages:",
        ", ".join(
            sorted(
                RTL_LANGUAGES
            )
        )
    )

    print("=" * 70)


    # ========================================================
    # DATABASE
    # ========================================================

    database_ok = initialize_database()

    if database_ok:

        print(
            "[OK] Database initialization completed"
        )

    else:

        print(
            "[WARNING] Database initialization failed"
        )


    # ========================================================
    # BLUEPRINTS
    # ========================================================

    register_all_blueprints()


    # ========================================================
    # FINANCE SERVICE
    # ========================================================

    finance_ok = initialize_finance_service_safe()

    if finance_ok:

        print(
            "[OK] Finance database service ready"
        )

    else:

        print(
            "[WARNING] Finance database service not initialized"
        )


    # ========================================================
    # READY
    # ========================================================

    print()
    print("=" * 70)

    print(
        "KISANVISION360+ READY"
    )

    print("=" * 70)

    print(
        "Home:",
        "/"
    )

    print(
        "Login:",
        "/login"
    )

    print(
        "Signup:",
        "/signup"
    )

    print(
        "Language:",
        "/language"
    )

    print(
        "Finance:",
        "/finance"
    )

    print(
        "Mandi:",
        "/market"
    )

    print(
        "Disease:",
        "/disease"
    )

    print(
        "Health:",
        "/health"
    )

    print(
        "API Health:",
        "/api/health"
    )

    print(
        "App Info:",
        "/api/app-info"
    )

    print(
        "Debug Routes:",
        "/debug/routes"
    )

    print(
        "Blueprints:",
        list(
            app.blueprints.keys()
        )
    )

    print(
        "Database:",
        "READY"
        if database_ok
        else "FAILED"
    )

    print(
        "Finance:",
        "READY"
        if finance_ok
        else "FAILED"
    )

    print("=" * 70)
    print()


# ============================================================
# APPLICATION INITIALIZATION
# ============================================================

startup()


# ============================================================
# RUN DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":

    try:

        port = int(
            os.getenv(
                "PORT",
                "5000"
            )
        )

    except Exception:

        port = 5000


    debug = (
        os.getenv(
            "FLASK_DEBUG",
            "true"
        ).lower()
        == "true"
    )


    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )
