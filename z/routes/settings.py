# ============================================================
# KISANVISION360+ - SETTINGS ROUTE
# ============================================================

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
)

from database.db import get_db_connection


# ============================================================
# BLUEPRINT
# ============================================================

settings_bp = Blueprint("settings", __name__)


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "mr": "मराठी",
    "kn": "ಕನ್ನಡ",
    "te": "తెలుగు",
    "ta": "தமிழ்",
    "ml": "മലയാളം",
    "gu": "ગુજરાતી",
    "pa": "ਪੰਜਾਬੀ",
    "bn": "বাংলা",
    "as": "অসমীয়া",
    "or": "ଓଡ଼ିଆ",
    "ur": "اردو",
    "ne": "नेपाली",
    "sa": "संस्कृतम्",
    "kok": "कोंकणी",
    "mai": "मैथिली",
    "ks": "कॉशुर",
    "sd": "سنڌي",
    "mni": "মৈতৈলোন্",
}


# ============================================================
# RTL LANGUAGES
# ============================================================

RTL_LANGUAGES = {
    "ur",
    "ks",
    "sd",
}


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_SETTINGS = {
    "preferred_language": "en",
    "theme": "system",
    "notifications_enabled": True,
    "weather_alerts_enabled": True,
    "market_alerts_enabled": True,
    "disease_alerts_enabled": True,
    "scheme_alerts_enabled": True,
    "dark_mode": False,
}


# ============================================================
# ALLOWED SETTING COLUMNS
# ============================================================

ALLOWED_SETTING_COLUMNS = {
    "preferred_language",
    "theme",
    "notifications_enabled",
    "weather_alerts_enabled",
    "market_alerts_enabled",
    "disease_alerts_enabled",
    "scheme_alerts_enabled",
    "dark_mode",
}


# ============================================================
# HELPERS
# ============================================================

def login_required():
    """
    Check whether user is logged in.
    """

    return bool(session.get("user_id"))


def current_user_id():
    """
    Return logged-in user's ID.
    """

    return session.get("user_id")


def get_user_language():
    """
    Get language from session.
    """

    language = str(
        session.get(
            "language",
            "en"
        )
    ).strip().lower()

    if language not in SUPPORTED_LANGUAGES:

        language = "en"

        session["language"] = "en"

    return language


def language_direction(language=None):
    """
    Return rtl/ltr according to language.
    """

    language = language or get_user_language()

    language = str(
        language
    ).strip().lower()

    if language in RTL_LANGUAGES:
        return "rtl"

    return "ltr"


def normalize_boolean(value, default=False):
    """
    Convert different boolean values into Python bool.
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value != 0

    if isinstance(value, str):

        value = value.strip().lower()

        if value in {
            "true",
            "1",
            "yes",
            "on",
            "enabled",
        }:
            return True

        if value in {
            "false",
            "0",
            "no",
            "off",
            "disabled",
        }:
            return False

    return bool(value)


# ============================================================
# DATABASE HELPERS
# ============================================================

def table_exists(cursor, table_name):
    """
    Check whether a PostgreSQL table exists.
    """

    try:

        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            )
            """,
            (table_name,),
        )

        row = cursor.fetchone()

        if row is None:
            return False

        if isinstance(row, dict):

            return bool(
                row.get("exists")
            )

        return bool(row[0])

    except Exception as exc:

        print(
            "Table check error:",
            exc
        )

        return False


def get_columns(cursor, table_name):
    """
    Get all columns from a PostgreSQL table.
    """

    try:

        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )

        rows = cursor.fetchall()

        columns = set()

        for row in rows:

            if isinstance(row, dict):

                column = row.get(
                    "column_name"
                )

            else:

                column = row[0]

            if column:
                columns.add(column)

        return columns

    except Exception as exc:

        print(
            "Get columns error:",
            exc
        )

        return set()


# ============================================================
# ENSURE SETTINGS COLUMNS
# ============================================================

def ensure_settings_columns(cursor):
    """
    Add missing settings columns to users table.
    """

    if not table_exists(
        cursor,
        "users"
    ):
        return False

    columns = get_columns(
        cursor,
        "users"
    )

    additions = []

    if "preferred_language" not in columns:

        additions.append(
            """
            ADD COLUMN preferred_language
            VARCHAR(10)
            DEFAULT 'en'
            """
        )

    if "theme" not in columns:

        additions.append(
            """
            ADD COLUMN theme
            VARCHAR(20)
            DEFAULT 'system'
            """
        )

    if "notifications_enabled" not in columns:

        additions.append(
            """
            ADD COLUMN notifications_enabled
            BOOLEAN
            DEFAULT TRUE
            """
        )

    if "weather_alerts_enabled" not in columns:

        additions.append(
            """
            ADD COLUMN weather_alerts_enabled
            BOOLEAN
            DEFAULT TRUE
            """
        )

    if "market_alerts_enabled" not in columns:

        additions.append(
            """
            ADD COLUMN market_alerts_enabled
            BOOLEAN
            DEFAULT TRUE
            """
        )

    if "disease_alerts_enabled" not in columns:

        additions.append(
            """
            ADD COLUMN disease_alerts_enabled
            BOOLEAN
            DEFAULT TRUE
            """
        )

    if "scheme_alerts_enabled" not in columns:

        additions.append(
            """
            ADD COLUMN scheme_alerts_enabled
            BOOLEAN
            DEFAULT TRUE
            """
        )

    if "dark_mode" not in columns:

        additions.append(
            """
            ADD COLUMN dark_mode
            BOOLEAN
            DEFAULT FALSE
            """
        )

    for addition in additions:

        try:

            cursor.execute(
                f"""
                ALTER TABLE users
                {addition}
                """
            )

        except Exception as exc:

            print(
                "Column addition warning:",
                exc
            )

            # Continue with other columns.
            try:
                cursor.connection.rollback()
            except Exception:
                pass

    return True


# ============================================================
# FETCH USER SETTINGS
# ============================================================

def fetch_user_settings(user_id):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        # ----------------------------------------------------
        # CHECK USERS TABLE
        # ----------------------------------------------------

        if not table_exists(
            cursor,
            "users"
        ):

            print(
                "Settings error: users table not found"
            )

            return {}

        # ----------------------------------------------------
        # CREATE MISSING SETTINGS COLUMNS
        # ----------------------------------------------------

        ensure_settings_columns(
            cursor
        )

        try:
            conn.commit()
        except Exception:
            pass

        # ----------------------------------------------------
        # GET CURRENT COLUMNS
        # ----------------------------------------------------

        columns = get_columns(
            cursor,
            "users"
        )

        requested_columns = [

            "id",

            "name",

            "email",

            "mobile",

            "role",

            "location",

            "preferred_language",

            "theme",

            "notifications_enabled",

            "weather_alerts_enabled",

            "market_alerts_enabled",

            "disease_alerts_enabled",

            "scheme_alerts_enabled",

            "dark_mode",
        ]

        available = [

            column

            for column
            in requested_columns

            if column in columns
        ]

        if "id" not in available:

            return {}

        # ----------------------------------------------------
        # FETCH USER
        # ----------------------------------------------------

        query = f"""
            SELECT {", ".join(available)}
            FROM users
            WHERE id = %s
            LIMIT 1
        """

        cursor.execute(
            query,
            (user_id,)
        )

        row = cursor.fetchone()

        if not row:

            return {}

        # ----------------------------------------------------
        # DICT CURSOR
        # ----------------------------------------------------

        if isinstance(row, dict):

            return dict(row)

        # ----------------------------------------------------
        # NORMAL CURSOR
        # ----------------------------------------------------

        return dict(
            zip(
                available,
                row
            )
        )

    except Exception as exc:

        print(
            "Settings read error:",
            exc
        )

        return {}

    finally:

        try:

            if cursor:
                cursor.close()

        except Exception:
            pass

        try:

            if conn:
                conn.close()

        except Exception:
            pass


# ============================================================
# UPDATE USER SETTING
# ============================================================

def update_user_column(
    user_id,
    column_name,
    value
):

    # --------------------------------------------------------
    # VALIDATE COLUMN
    # --------------------------------------------------------

    if column_name not in ALLOWED_SETTING_COLUMNS:

        return (
            False,
            "Invalid setting"
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        # ----------------------------------------------------
        # CHECK TABLE
        # ----------------------------------------------------

        if not table_exists(
            cursor,
            "users"
        ):

            return (
                False,
                "Users table not found"
            )

        # ----------------------------------------------------
        # ENSURE COLUMN
        # ----------------------------------------------------

        ensure_settings_columns(
            cursor
        )

        try:
            conn.commit()
        except Exception:
            pass

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        query = f"""
            UPDATE users
            SET {column_name} = %s
            WHERE id = %s
        """

        cursor.execute(
            query,
            (
                value,
                user_id
            )
        )

        # ----------------------------------------------------
        # CHECK WHETHER USER EXISTS
        # ----------------------------------------------------

        if cursor.rowcount == 0:

            try:
                conn.rollback()
            except Exception:
                pass

            return (
                False,
                "User not found"
            )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        conn.commit()

        return (
            True,
            "Setting updated successfully"
        )

    except Exception as exc:

        if conn:

            try:
                conn.rollback()
            except Exception:
                pass

        print(
            "Settings update error:",
            exc
        )

        return (
            False,
            "Unable to update setting"
        )

    finally:

        try:

            if cursor:
                cursor.close()

        except Exception:
            pass

        try:

            if conn:
                conn.close()

        except Exception:
            pass


# ============================================================
# BUILD SETTINGS RESPONSE
# ============================================================

def build_settings_data(data):

    language = (
        data.get(
            "preferred_language"
        )
        or session.get(
            "language"
        )
        or "en"
    )

    language = str(
        language
    ).strip().lower()

    if language not in SUPPORTED_LANGUAGES:

        language = "en"

    theme = (
        data.get(
            "theme"
        )
        or session.get(
            "theme"
        )
        or "system"
    )

    theme = str(
        theme
    ).strip().lower()

    if theme not in {
        "system",
        "light",
        "dark",
    }:

        theme = "system"

    notifications_enabled = normalize_boolean(
        data.get(
            "notifications_enabled",
            True
        ),
        True
    )

    weather_alerts_enabled = normalize_boolean(
        data.get(
            "weather_alerts_enabled",
            True
        ),
        True
    )

    market_alerts_enabled = normalize_boolean(
        data.get(
            "market_alerts_enabled",
            True
        ),
        True
    )

    disease_alerts_enabled = normalize_boolean(
        data.get(
            "disease_alerts_enabled",
            True
        ),
        True
    )

    scheme_alerts_enabled = normalize_boolean(
        data.get(
            "scheme_alerts_enabled",
            True
        ),
        True
    )

    dark_mode = normalize_boolean(
        data.get(
            "dark_mode",
            False
        ),
        False
    )

    return {

        "language": language,

        "language_name":
            SUPPORTED_LANGUAGES.get(
                language,
                "English"
            ),

        "direction":
            language_direction(
                language
            ),

        "theme": theme,

        "notifications_enabled":
            notifications_enabled,

        "weather_alerts_enabled":
            weather_alerts_enabled,

        "market_alerts_enabled":
            market_alerts_enabled,

        "disease_alerts_enabled":
            disease_alerts_enabled,

        "scheme_alerts_enabled":
            scheme_alerts_enabled,

        "dark_mode":
            dark_mode,
    }


# ============================================================
# SETTINGS PAGE
# ============================================================

@settings_bp.route(
    "/settings",
    methods=["GET"]
)
def settings():

    if not login_required():

        return redirect(
            url_for(
                "auth.login"
            )
        )

    user_id = current_user_id()

    data = fetch_user_settings(
        user_id
    )

    # --------------------------------------------------------
    # If user was not found
    # --------------------------------------------------------

    if not data:

        # Keep session active but use defaults.
        data = {
            "id": user_id,
            "name": session.get(
                "name",
                ""
            ),
            "role": session.get(
                "role",
                ""
            ),
            **DEFAULT_SETTINGS,
        }

    # --------------------------------------------------------
    # Build settings
    # --------------------------------------------------------

    settings_data = build_settings_data(
        data
    )

    # --------------------------------------------------------
    # Synchronize session
    # --------------------------------------------------------

    session["language"] = (
        settings_data["language"]
    )

    session["theme"] = (
        settings_data["theme"]
    )

    session["dark_mode"] = (
        settings_data["dark_mode"]
    )

    if data.get("name"):

        session["name"] = data["name"]

    if data.get("role"):

        session["role"] = str(
            data["role"]
        ).lower().strip()

    # --------------------------------------------------------
    # Render
    # --------------------------------------------------------

    return render_template(
        "settings.html",

        user=data,

        settings=settings_data,

        languages=SUPPORTED_LANGUAGES,

        language=settings_data[
            "language"
        ],

        direction=settings_data[
            "direction"
        ],
    )


# ============================================================
# UPDATE LANGUAGE
# ============================================================

@settings_bp.route(
    "/api/settings/language",
    methods=["POST"]
)
def update_language():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    language = str(
        data.get(
            "language",
            "en"
        )
    ).strip().lower()

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if language not in SUPPORTED_LANGUAGES:

        return jsonify({

            "success": False,

            "message":
                "Unsupported language",

        }), 400

    # --------------------------------------------------------
    # Session
    # --------------------------------------------------------

    session["language"] = language

    session.modified = True

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    success, message = update_user_column(

        current_user_id(),

        "preferred_language",

        language
    )

    return jsonify({

        "success": True,

        "language": language,

        "language_name":
            SUPPORTED_LANGUAGES[
                language
            ],

        "direction":
            language_direction(
                language
            ),

        "database_updated":
            success,

        "message":
            (
                "Language changed globally"
                if success
                else
                "Language changed for this session"
            ),
    })


# ============================================================
# UPDATE THEME
# ============================================================

@settings_bp.route(
    "/api/settings/theme",
    methods=["POST"]
)
def update_theme():

    if not login_required():

        return jsonify({

            "success": False,

            "message":
                "Login required",

        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    theme = str(
        data.get(
            "theme",
            "system"
        )
    ).strip().lower()

    # --------------------------------------------------------
    # Validate theme
    # --------------------------------------------------------

    if theme not in {
        "system",
        "light",
        "dark",
    }:

        return jsonify({

            "success": False,

            "message":
                "Invalid theme",

        }), 400

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    success, message = update_user_column(

        current_user_id(),

        "theme",

        theme
    )

    # --------------------------------------------------------
    # Session
    # --------------------------------------------------------

    session["theme"] = theme

    session.modified = True

    return jsonify({

        "success": True,

        "theme": theme,

        "database_updated":
            success,

        "message":
            message,
    })


# ============================================================
# MASTER NOTIFICATIONS
# ============================================================

@settings_bp.route(
    "/api/settings/notifications",
    methods=["POST"]
)
def update_notifications():

    if not login_required():

        return jsonify({

            "success": False,

            "message":
                "Login required",

        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    enabled = normalize_boolean(
        data.get(
            "enabled"
        ),
        False
    )

    success, message = update_user_column(

        current_user_id(),

        "notifications_enabled",

        enabled
    )

    return jsonify({

        "success": True,

        "enabled": enabled,

        "database_updated":
            success,

        "message":
            message,
    })


# ============================================================
# INDIVIDUAL ALERTS
# ============================================================

@settings_bp.route(
    "/api/settings/alerts",
    methods=["POST"]
)
def update_alerts():

    if not login_required():

        return jsonify({

            "success": False,

            "message":
                "Login required",

        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    mapping = {

        "weather":
            "weather_alerts_enabled",

        "market":
            "market_alerts_enabled",

        "disease":
            "disease_alerts_enabled",

        "schemes":
            "scheme_alerts_enabled",
    }

    updated = {}

    errors = []

    # --------------------------------------------------------
    # Update every supplied alert
    # --------------------------------------------------------

    for key, column in mapping.items():

        if key not in data:
            continue

        value = normalize_boolean(
            data.get(key),
            False
        )

        success, message = update_user_column(

            current_user_id(),

            column,

            value
        )

        if success:

            updated[key] = value

        else:

            errors.append({

                "setting": key,

                "message": message,
            })

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({

        "success":
            len(errors) == 0,

        "updated":
            updated,

        "errors":
            errors,

    })


# ============================================================
# DARK MODE
# ============================================================

@settings_bp.route(
    "/api/settings/dark-mode",
    methods=["POST"]
)
def update_dark_mode():

    if not login_required():

        return jsonify({

            "success": False,

            "message":
                "Login required",

        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    enabled = normalize_boolean(
        data.get(
            "enabled"
        ),
        False
    )

    success, message = update_user_column(

        current_user_id(),

        "dark_mode",

        enabled
    )

    session["dark_mode"] = enabled

    session.modified = True

    return jsonify({

        "success": True,

        "enabled": enabled,

        "database_updated":
            success,

        "message":
            message,
    })


# ============================================================
# COMPLETE SETTINGS API
# ============================================================

@settings_bp.route(
    "/api/settings",
    methods=["GET"]
)
def get_settings():

    if not login_required():

        return jsonify({

            "success": False,

            "message":
                "Login required",

        }), 401

    data = fetch_user_settings(

        current_user_id()

    )

    if not data:

        data = DEFAULT_SETTINGS.copy()

    settings_data = build_settings_data(
        data
    )

    return jsonify({

        "success": True,

        "settings":
            settings_data,

    })


# ============================================================
# RESET SETTINGS
# ============================================================

@settings_bp.route(
    "/api/settings/reset",
    methods=["POST"]
)
def reset_settings():

    if not login_required():

        return jsonify({

            "success": False,

            "message":
                "Login required",

        }), 401

    user_id = current_user_id()

    results = {}

    errors = []

    # --------------------------------------------------------
    # Reset every setting
    # --------------------------------------------------------

    for column, value in DEFAULT_SETTINGS.items():

        success, message = update_user_column(

            user_id,

            column,

            value
        )

        results[column] = success

        if not success:

            errors.append({

                "setting": column,

                "message": message,
            })

    # --------------------------------------------------------
    # Reset session
    # --------------------------------------------------------

    session["language"] = "en"

    session["theme"] = "system"

    session["dark_mode"] = False

    session.modified = True

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({

        "success":
            len(errors) == 0,

        "settings":
            DEFAULT_SETTINGS,

        "database_results":
            results,

        "errors":
            errors,

        "message":
            (
                "Settings reset successfully"
                if not errors
                else
                "Some settings could not be reset"
            ),
    })


# ============================================================
# LANGUAGE LIST
# ============================================================

@settings_bp.route(
    "/api/settings/languages",
    methods=["GET"]
)
def languages():

    return jsonify({

        "success": True,

        "count":
            len(
                SUPPORTED_LANGUAGES
            ),

        "languages": [

            {

                "code":
                    code,

                "name":
                    name,

                "direction":
                    (
                        "rtl"
                        if code
                        in RTL_LANGUAGES
                        else
                        "ltr"
                    ),
            }

            for code, name
            in SUPPORTED_LANGUAGES.items()
        ],
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@settings_bp.route(
    "/api/settings/health",
    methods=["GET"]
)
def settings_health():

    database_ok = False

    database_error = None

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1"
        )

        cursor.fetchone()

        database_ok = True

    except Exception as exc:

        database_error = str(
            exc
        )

        print(
            "Settings health error:",
            exc
        )

    finally:

        try:

            if cursor:
                cursor.close()

        except Exception:
            pass

        try:

            if conn:
                conn.close()

        except Exception:
            pass

    return jsonify({

        "success":
            database_ok,

        "service":
            "settings",

        "database":
            database_ok,

        "database_error":
            database_error,

        "languages":
            len(
                SUPPORTED_LANGUAGES
            ),

        "global_language":
            True,

        "rtl_supported":
            True,

    }), (
        200
        if database_ok
        else 503
    )


# ============================================================
# GOOGLE TRANSLATE / GLOBAL LANGUAGE
# ============================================================

@settings_bp.route(
    "/set-language",
    methods=["POST"]
)
def set_language():

    # --------------------------------------------------------
    # Accept JSON
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    )

    # --------------------------------------------------------
    # Also accept form data
    # --------------------------------------------------------

    if not isinstance(
        data,
        dict
    ):

        data = request.form.to_dict()

    # --------------------------------------------------------
    # Get language
    # --------------------------------------------------------

    language = str(
        data.get(
            "language",
            "en"
        )
    ).strip().lower()

    # --------------------------------------------------------
    # Validate language
    # --------------------------------------------------------

    if language not in SUPPORTED_LANGUAGES:

        return jsonify({

            "success": False,

            "message":
                "Unsupported language",

            "language":
                "en",

        }), 400

    # --------------------------------------------------------
    # Save language in session
    # --------------------------------------------------------

    session["language"] = language

    session.modified = True

    # --------------------------------------------------------
    # Save to database if logged in
    # --------------------------------------------------------

    database_updated = False

    user_id = current_user_id()

    if user_id:

        success, db_message = (
            update_user_column(

                user_id,

                "preferred_language",

                language
            )
        )

        database_updated = success

        if success:

            message = (
                "Global language updated successfully"
            )

        else:

            message = (
                "Language updated for this session"
            )

    else:

        message = (
            "Language saved in session"
        )

    # --------------------------------------------------------
    # Direction
    # --------------------------------------------------------

    direction = language_direction(
        language
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({

        "success": True,

        "language":
            language,

        "language_name":
            SUPPORTED_LANGUAGES[
                language
            ],

        "direction":
            direction,

        "database_updated":
            database_updated,

        "message":
            message,
    })


# ============================================================
# END OF SETTINGS ROUTE
# ============================================================
