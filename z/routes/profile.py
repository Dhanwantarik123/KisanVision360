
# ============================================================
# KISANVISION360+ - PROFILE ROUTES
# ============================================================

import os
import re
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash,
    current_app,
)

from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from database.db import get_db_connection

load_dotenv(override=True)


# ============================================================
# BLUEPRINT
# ============================================================

profile_bp = Blueprint("profile", __name__)


# ============================================================
# LOGIN REQUIRED
# ============================================================

def login_required(view_func):
    """
    Simple login protection.
    """

    from functools import wraps

    @wraps(view_func)
    def wrapper(*args, **kwargs):

        user_id = session.get("user_id")

        if not user_id:
            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "message": "Login required."
                }), 401

            return redirect(url_for("login"))

        return view_func(*args, **kwargs)

    return wrapper


# ============================================================
# BASIC HELPERS
# ============================================================

def get_user_id():
    """
    Get logged-in user ID from session.
    """

    user_id = session.get("user_id")

    if user_id is None:
        return None

    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def get_role():
    """
    Get current user's role.
    """

    role = session.get("role", "farmer")

    return str(role).strip().lower()


def get_language():
    """
    Get current user's language.
    """

    language = (
        session.get("language")
        or session.get("preferred_language")
        or "en"
    )

    return str(language).strip().lower()


def clean_text(value, max_length=150):
    """
    Clean normal text input.
    """

    if value is None:
        return ""

    value = str(value).strip()

    value = re.sub(r"\s+", " ", value)

    return value[:max_length]


def clean_email(value):
    """
    Clean and validate email.
    """

    if value is None:
        return ""

    value = str(value).strip().lower()

    if not value:
        return ""

    if len(value) > 150:
        return ""

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.match(pattern, value):
        return ""

    return value


def clean_mobile(value):
    """
    Clean mobile number.
    """

    if value is None:
        return ""

    value = str(value).strip()

    value = re.sub(r"[^0-9+]", "", value)

    return value[:20]


def language_direction(language):
    """
    Return text direction.
    """

    rtl_languages = {
        "ur",
        "ar",
        "fa",
    }

    return "rtl" if language in rtl_languages else "ltr"


# ============================================================
# DATABASE HELPERS
# ============================================================

def table_exists(conn, table_name):
    """
    Check whether a PostgreSQL table exists.
    """

    cursor = conn.cursor()

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
            (table_name,)
        )

        result = cursor.fetchone()

        if isinstance(result, dict):
            return bool(result.get("exists"))

        return bool(result[0]) if result else False

    finally:
        cursor.close()


def column_exists(conn, table_name, column_name):
    """
    Check whether a column exists.
    """

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                  AND column_name = %s
            )
            """,
            (table_name, column_name)
        )

        result = cursor.fetchone()

        if isinstance(result, dict):
            return bool(result.get("exists"))

        return bool(result[0]) if result else False

    finally:
        cursor.close()


# ============================================================
# PROFILE TABLES
# ============================================================

def ensure_farmer_profile_table(conn):
    """
    Ensure farmer_profiles table exists.
    """

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS farmer_profiles (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                farm_name VARCHAR(150),
                farm_size NUMERIC(12,2),
                farm_size_unit VARCHAR(30),
                soil_type VARCHAR(100),
                irrigation_type VARCHAR(100),
                main_crop VARCHAR(150),
                experience_years INTEGER,
                district VARCHAR(100),
                state VARCHAR(100),
                village VARCHAR(150),
                pincode VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()


def ensure_consumer_profile_table(conn):
    """
    Ensure consumer_profiles table exists.
    """

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS consumer_profiles (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                address TEXT,
                city VARCHAR(100),
                state VARCHAR(100),
                pincode VARCHAR(20),
                preferred_category VARCHAR(150),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()


# ============================================================
# FETCH USER PROFILE
# ============================================================

def fetch_user_profile(user_id):
    """
    Fetch complete user profile.
    """

    conn = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                mobile,
                email,
                role,
                location,
                preferred_language,
                profile_pic,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        cursor.close()

        if not user:
            return None

        return dict(user)

    except Exception as e:

        print("FETCH USER PROFILE ERROR:", e)

        return None

    finally:

        if conn:
            conn.close()


# ============================================================
# FETCH FARMER PROFILE
# ============================================================

def fetch_farmer_profile(user_id):
    """
    Fetch farmer-specific profile.
    """

    conn = None

    try:

        conn = get_db_connection()

        if not table_exists(conn, "farmer_profiles"):
            return {}

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM farmer_profiles
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        profile = cursor.fetchone()

        cursor.close()

        if not profile:
            return {}

        return dict(profile)

    except Exception as e:

        print("FETCH FARMER PROFILE ERROR:", e)

        return {}

    finally:

        if conn:
            conn.close()


# ============================================================
# FETCH CONSUMER PROFILE
# ============================================================

def fetch_consumer_profile(user_id):
    """
    Fetch consumer-specific profile.
    """

    conn = None

    try:

        conn = get_db_connection()

        if not table_exists(conn, "consumer_profiles"):
            return {}

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM consumer_profiles
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        profile = cursor.fetchone()

        cursor.close()

        if not profile:
            return {}

        return dict(profile)

    except Exception as e:

        print("FETCH CONSUMER PROFILE ERROR:", e)

        return {}

    finally:

        if conn:
            conn.close()


# ============================================================
# PROFILE COMPLETION
# ============================================================

def calculate_profile_completion(user, role_profile=None):
    """
    Calculate profile completion percentage.
    """

    if not user:
        return 0

    total_fields = [
        user.get("name"),
        user.get("mobile"),
        user.get("email"),
        user.get("location"),
    ]

    completed = sum(
        1 for value in total_fields
        if value and str(value).strip()
    )

    base_percentage = int(
        (completed / len(total_fields)) * 80
    )

    # Profile image gives additional completion.
    if user.get("profile_pic"):
        base_percentage += 10

    # Role-specific profile gives additional completion.
    if role_profile:

        important_fields = []

        if get_role() == "farmer":

            important_fields = [
                role_profile.get("farm_name"),
                role_profile.get("farm_size"),
                role_profile.get("main_crop"),
            ]

        else:

            important_fields = [
                role_profile.get("address"),
                role_profile.get("city"),
            ]

        if any(
            value is not None and str(value).strip()
            for value in important_fields
        ):
            base_percentage += 10

    return min(base_percentage, 100)


# ============================================================
# PROFILE PAGE
# ============================================================

@profile_bp.route("/profile", methods=["GET"])
@login_required
def profile():

    user_id = get_user_id()

    user = fetch_user_profile(user_id)

    if not user:
        flash("Profile not found.", "error")

        if get_role() == "farmer":
            return redirect(url_for("farmer.farmer"))

        return redirect(url_for("login"))

    role = get_role()

    if role == "farmer":

        role_profile = fetch_farmer_profile(user_id)

    else:

        role_profile = fetch_consumer_profile(user_id)

    completion = calculate_profile_completion(
        user,
        role_profile
    )

    # Keep session information updated.
    session["name"] = user.get("name") or ""
    session["role"] = user.get("role") or role

    return render_template(
        "profile.html",
        user=user,
        profile=user,
        role_profile=role_profile,
        name=user.get("name") or "User",
        mobile=user.get("mobile") or "",
        email=user.get("email") or "",
        role=user.get("role") or role,
        location=user.get("location") or "",
        preferred_language=user.get("preferred_language") or "en",
        profile_pic=user.get("profile_pic") or "",
        profile_completion=completion,
        completion=completion,
        language=get_language(),
        direction=language_direction(get_language()),
    )


# ============================================================
# EDIT PROFILE
# ============================================================

@profile_bp.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    user_id = get_user_id()

    if not user_id:
        return redirect(url_for("login"))

    conn = None

    try:

        conn = get_db_connection()

        # ----------------------------------------------------
        # POST - SAVE PROFILE
        # ----------------------------------------------------

        if request.method == "POST":

            name = clean_text(
                request.form.get("name"),
                150
            )

            mobile = clean_mobile(
                request.form.get("mobile")
            )

            email = clean_email(
                request.form.get("email")
            )

            location = clean_text(
                request.form.get("location"),
                255
            )

            if not name:

                flash(
                    "Name is required.",
                    "error"
                )

                return redirect(
                    url_for("profile.edit_profile")
                )

            cursor = conn.cursor()

            # ------------------------------------------------
            # CHECK EMAIL DUPLICATE
            # ------------------------------------------------

            if email:

                cursor.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                      AND id <> %s
                    LIMIT 1
                    """,
                    (
                        email,
                        user_id
                    )
                )

                existing_email = cursor.fetchone()

                if existing_email:

                    cursor.close()

                    flash(
                        "This email address is already used by another account.",
                        "error"
                    )

                    return redirect(
                        url_for("profile.edit_profile")
                    )

            # ------------------------------------------------
            # UPDATE USER
            # ------------------------------------------------

            cursor.execute(
                """
                UPDATE users
                SET
                    name = %s,
                    mobile = %s,
                    email = %s,
                    location = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    name,
                    mobile or None,
                    email or None,
                    location or None,
                    user_id
                )
            )

            # ------------------------------------------------
            # PROFILE IMAGE
            # ------------------------------------------------

            profile_file = request.files.get("profile")

            if profile_file and profile_file.filename:

                original_name = profile_file.filename

                extension = (
                    os.path.splitext(original_name)[1]
                    .lower()
                )

                allowed_extensions = {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp",
                }

                if extension not in allowed_extensions:

                    conn.rollback()
                    cursor.close()

                    flash(
                        "Only JPG, JPEG, PNG or WEBP images are allowed.",
                        "error"
                    )

                    return redirect(
                        url_for("profile.edit_profile")
                    )

                # Check file size.
                profile_file.seek(0, os.SEEK_END)

                file_size = profile_file.tell()

                profile_file.seek(0)

                max_size = 5 * 1024 * 1024

                if file_size > max_size:

                    conn.rollback()
                    cursor.close()

                    flash(
                        "Profile image must be smaller than 5 MB.",
                        "error"
                    )

                    return redirect(
                        url_for("profile.edit_profile")
                    )

                filename = secure_filename(
                    profile_file.filename
                )

                timestamp = datetime.now().strftime(
                    "%Y%m%d%H%M%S"
                )

                filename = (
                    f"profile_{user_id}_{timestamp}{extension}"
                )

                upload_folder = os.path.join(
                    current_app.root_path,
                    "static",
                    "uploads",
                    "profiles"
                )

                os.makedirs(
                    upload_folder,
                    exist_ok=True
                )

                file_path = os.path.join(
                    upload_folder,
                    filename
                )

                profile_file.save(file_path)

                profile_url = (
                    f"/static/uploads/profiles/{filename}"
                )

                # Make sure profile_pic column exists.
                if column_exists(
                    conn,
                    "users",
                    "profile_pic"
                ):

                    cursor.execute(
                        """
                        UPDATE users
                        SET
                            profile_pic = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (
                            profile_url,
                            user_id
                        )
                    )

            # ------------------------------------------------
            # COMMIT
            # ------------------------------------------------

            conn.commit()

            cursor.close()

            # Update session name.
            session["name"] = name

            flash(
                "Profile updated successfully.",
                "success"
            )

            return redirect(
                url_for("profile.profile")
            )

        # ----------------------------------------------------
        # GET - SHOW FORM
        # ----------------------------------------------------

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                mobile,
                email,
                role,
                location,
                preferred_language,
                profile_pic,
                is_active
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        cursor.close()

        if not user:

            flash(
                "Profile not found.",
                "error"
            )

            return redirect(
                url_for("profile.profile")
            )

        user = dict(user)

        role = str(
            user.get("role") or get_role()
        ).strip().lower()

        if role == "farmer":

            role_profile = fetch_farmer_profile(
                user_id
            )

        else:

            role_profile = fetch_consumer_profile(
                user_id
            )

        completion = calculate_profile_completion(
            user,
            role_profile
        )

        return render_template(
            "edit-profile.html",
            user=user,
            profile=user,
            role_profile=role_profile,
            name=user.get("name") or "",
            mobile=user.get("mobile") or "",
            email=user.get("email") or "",
            role=user.get("role") or role,
            location=user.get("location") or "",
            profile_pic=user.get("profile_pic") or "",
            profile_completion=completion,
            completion=completion,
            language=get_language(),
            direction=language_direction(
                get_language()
            ),
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "EDIT PROFILE ERROR:",
            repr(e)
        )

        flash(
            "Unable to update profile.",
            "error"
        )

        return redirect(
            url_for("profile.profile")
        )

    finally:

        if conn:
            conn.close()


# ============================================================
# API - GET / UPDATE PROFILE
# ============================================================

@profile_bp.route(
    "/api/profile",
    methods=["GET", "PUT", "POST"]
)
@login_required
def api_profile():

    user_id = get_user_id()

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        user = fetch_user_profile(user_id)

        if not user:

            return jsonify({
                "success": False,
                "message": "Profile not found."
            }), 404

        if get_role() == "farmer":

            role_profile = fetch_farmer_profile(
                user_id
            )

        else:

            role_profile = fetch_consumer_profile(
                user_id
            )

        completion = calculate_profile_completion(
            user,
            role_profile
        )

        return jsonify({
            "success": True,
            "user": user,
            "profile": user,
            "role_profile": role_profile,
            "completion": completion
        })

    # --------------------------------------------------------
    # POST / PUT
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    )

    if not data:

        data = request.form.to_dict()

    name = clean_text(
        data.get("name"),
        150
    )

    mobile = clean_mobile(
        data.get("mobile")
    )

    email = clean_email(
        data.get("email")
    )

    location = clean_text(
        data.get("location"),
        255
    )

    if not name:

        return jsonify({
            "success": False,
            "message": "Name is required."
        }), 400

    conn = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        # Check duplicate email.
        if email:

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(email) = LOWER(%s)
                  AND id <> %s
                LIMIT 1
                """,
                (
                    email,
                    user_id
                )
            )

            duplicate = cursor.fetchone()

            if duplicate:

                cursor.close()

                return jsonify({
                    "success": False,
                    "message": "Email already exists."
                }), 409

        cursor.execute(
            """
            UPDATE users
            SET
                name = %s,
                mobile = %s,
                email = %s,
                location = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                name,
                mobile or None,
                email or None,
                location or None,
                user_id
            )
        )

        conn.commit()

        cursor.close()

        session["name"] = name

        user = fetch_user_profile(
            user_id
        )

        return jsonify({
            "success": True,
            "message": "Profile updated successfully.",
            "user": user
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "API PROFILE UPDATE ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to update profile."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# FARM PROFILE API
# ============================================================

@profile_bp.route(
    "/api/profile/farm",
    methods=["GET", "PUT", "POST"]
)
@login_required
def api_farm_profile():

    user_id = get_user_id()

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    conn = None

    try:

        conn = get_db_connection()

        ensure_farmer_profile_table(conn)

        cursor = conn.cursor()

        # ----------------------------------------------------
        # GET
        # ----------------------------------------------------

        if request.method == "GET":

            cursor.execute(
                """
                SELECT *
                FROM farmer_profiles
                WHERE user_id = %s
                LIMIT 1
                """,
                (user_id,)
            )

            row = cursor.fetchone()

            cursor.close()

            return jsonify({
                "success": True,
                "profile": dict(row) if row else {}
            })

        # ----------------------------------------------------
        # POST / PUT
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        ) or request.form.to_dict()

        farm_name = clean_text(
            data.get("farm_name"),
            150
        )

        farm_size = data.get(
            "farm_size"
        )

        farm_size_unit = clean_text(
            data.get("farm_size_unit"),
            30
        )

        soil_type = clean_text(
            data.get("soil_type"),
            100
        )

        irrigation_type = clean_text(
            data.get("irrigation_type"),
            100
        )

        main_crop = clean_text(
            data.get("main_crop"),
            150
        )

        experience_years = data.get(
            "experience_years"
        )

        district = clean_text(
            data.get("district"),
            100
        )

        state = clean_text(
            data.get("state"),
            100
        )

        village = clean_text(
            data.get("village"),
            150
        )

        pincode = clean_text(
            data.get("pincode"),
            20
        )

        cursor.execute(
            """
            INSERT INTO farmer_profiles (
                user_id,
                farm_name,
                farm_size,
                farm_size_unit,
                soil_type,
                irrigation_type,
                main_crop,
                experience_years,
                district,
                state,
                village,
                pincode
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (user_id)
            DO UPDATE SET
                farm_name = EXCLUDED.farm_name,
                farm_size = EXCLUDED.farm_size,
                farm_size_unit = EXCLUDED.farm_size_unit,
                soil_type = EXCLUDED.soil_type,
                irrigation_type = EXCLUDED.irrigation_type,
                main_crop = EXCLUDED.main_crop,
                experience_years = EXCLUDED.experience_years,
                district = EXCLUDED.district,
                state = EXCLUDED.state,
                village = EXCLUDED.village,
                pincode = EXCLUDED.pincode,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                farm_name or None,
                farm_size or None,
                farm_size_unit or None,
                soil_type or None,
                irrigation_type or None,
                main_crop or None,
                experience_years or None,
                district or None,
                state or None,
                village or None,
                pincode or None,
            )
        )

        conn.commit()

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Farm profile updated successfully.",
            "profile": fetch_farmer_profile(
                user_id
            )
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "FARM PROFILE ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to update farm profile."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# LOCATION API
# ============================================================

@profile_bp.route(
    "/api/profile/location",
    methods=["GET", "POST", "PUT"]
)
@login_required
def api_profile_location():

    user_id = get_user_id()

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    if request.method == "GET":

        user = fetch_user_profile(
            user_id
        )

        return jsonify({
            "success": True,
            "location": (
                user.get("location")
                if user
                else ""
            )
        })

    data = request.get_json(
        silent=True
    ) or request.form.to_dict()

    location = clean_text(
        data.get("location"),
        255
    )

    conn = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET
                location = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                location or None,
                user_id
            )
        )

        conn.commit()

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Location updated successfully.",
            "location": location
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "LOCATION UPDATE ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to update location."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# LANGUAGE API
# ============================================================

@profile_bp.route(
    "/api/profile/language",
    methods=["GET", "POST", "PUT"]
)
@login_required
def api_profile_language():

    user_id = get_user_id()

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    if request.method == "GET":

        user = fetch_user_profile(
            user_id
        )

        language = (
            user.get("preferred_language")
            if user
            else "en"
        ) or "en"

        return jsonify({
            "success": True,
            "language": language
        })

    data = request.get_json(
        silent=True
    ) or request.form.to_dict()

    language = clean_text(
        data.get("language") or "en",
        20
    ).lower()

    conn = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET
                preferred_language = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                language,
                user_id
            )
        )

        conn.commit()

        cursor.close()

        session["language"] = language
        session["preferred_language"] = language

        return jsonify({
            "success": True,
            "message": "Language updated successfully.",
            "language": language
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "LANGUAGE UPDATE ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "message": "Unable to update language."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# PROFILE SUMMARY
# ============================================================

@profile_bp.route(
    "/api/profile/summary",
    methods=["GET"]
)
@login_required
def profile_summary():

    user_id = get_user_id()

    user = fetch_user_profile(
        user_id
    )

    if not user:

        return jsonify({
            "success": False,
            "message": "Profile not found."
        }), 404

    role = str(
        user.get("role") or get_role()
    ).lower()

    if role == "farmer":

        role_profile = fetch_farmer_profile(
            user_id
        )

    else:

        role_profile = fetch_consumer_profile(
            user_id
        )

    completion = calculate_profile_completion(
        user,
        role_profile
    )

    return jsonify({
        "success": True,
        "summary": {
            "name": user.get("name") or "",
            "mobile": user.get("mobile") or "",
            "email": user.get("email") or "",
            "role": role,
            "location": user.get("location") or "",
            "language": (
                user.get("preferred_language")
                or "en"
            ),
            "profile_pic": (
                user.get("profile_pic")
                or ""
            ),
            "completion": completion
        },
        "role_profile": role_profile
    })


# ============================================================
# PROFILE HEALTH
# ============================================================

@profile_bp.route(
    "/api/profile/health",
    methods=["GET"]
)
def profile_health():

    conn = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 AS health"
        )

        result = cursor.fetchone()

        cursor.close()

        return jsonify({
            "success": True,
            "service": "profile",
            "database": bool(result)
        })

    except Exception as e:

        print(
            "PROFILE HEALTH ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "service": "profile",
            "database": False
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# INITIALIZE PROFILE SERVICE
# ============================================================

def initialize_profile_service():

    conn = None

    try:

        conn = get_db_connection()

        ensure_farmer_profile_table(
            conn
        )

        ensure_consumer_profile_table(
            conn
        )

        print(
            "Profile service initialized successfully."
        )

        return True

    except Exception as e:

        print(
            "PROFILE SERVICE INITIALIZATION ERROR:",
            repr(e)
        )

        return False

    finally:

        if conn:
            conn.close()

