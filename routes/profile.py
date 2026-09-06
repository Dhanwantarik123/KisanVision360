# ============================================================
# KISANVISION360+
# routes/profile.py
# USER + FARM PROFILE MANAGEMENT
# PostgreSQL / Supabase Compatible
# ============================================================

from __future__ import annotations

import logging
import re
from functools import wraps
from typing import Any, Optional

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database.db import get_db_connection


# ============================================================
# BLUEPRINT
# ============================================================

profile_bp = Blueprint("profile", __name__)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
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

RTL_LANGUAGES = {"ur", "ks", "sd"}

VALID_ROLES = {
    "farmer",
    "consumer",
    "admin",
}


# ============================================================
# AUTHENTICATION
# ============================================================

def login_required(view):
    """Require an authenticated user."""

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("user_id"):

            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "message": "Please login first."
                }), 401

            return redirect(
                url_for("auth.login")
            )

        return view(*args, **kwargs)

    return wrapped


# ============================================================
# BASIC HELPERS
# ============================================================

def get_user_id() -> Optional[int]:
    """Return current logged-in user id."""

    value = session.get("user_id")

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_role() -> str:
    """Return current user role."""

    role = str(
        session.get(
            "role",
            "farmer"
        )
    ).lower().strip()

    if role not in VALID_ROLES:
        return "farmer"

    return role


def get_language() -> str:
    """Return global application language."""

    language = str(
        session.get(
            "language",
            "en"
        )
    ).lower().strip()

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    return language


def clean_text(
    value: Any,
    max_length: int = 255
) -> str:
    """Clean user-provided text."""

    if value is None:
        return ""

    value = str(value)

    value = value.replace(
        "\x00",
        " "
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value[:max_length]


def clean_email(value: Any) -> str:
    """Normalize email."""

    return clean_text(
        value,
        255
    ).lower()


def clean_mobile(value: Any) -> str:
    """Keep safe mobile characters."""

    value = clean_text(
        value,
        30
    )

    return re.sub(
        r"[^0-9+\-\s()]",
        "",
        value
    ).strip()


def get_direction(language: str) -> str:

    return (
        "rtl"
        if language in RTL_LANGUAGES
        else "ltr"
    )


# ============================================================
# DATABASE HELPERS
# ============================================================

def column_exists(
    cursor,
    table_name: str,
    column_name: str
) -> bool:
    """Check whether a PostgreSQL column exists."""

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
            (
                table_name,
                column_name,
            )
        )

        row = cursor.fetchone()

        if isinstance(row, dict):
            return bool(
                list(row.values())[0]
            )

        return bool(row[0])

    except Exception:

        return False


def table_exists(
    cursor,
    table_name: str
) -> bool:
    """Check whether a PostgreSQL table exists."""

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

        row = cursor.fetchone()

        if isinstance(row, dict):
            return bool(
                list(row.values())[0]
            )

        return bool(row[0])

    except Exception:

        return False


# ============================================================
# FARM PROFILE TABLE
# ============================================================

def ensure_farmer_profile_table():
    """
    Create/upgrade farmer profile table.

    This function is intentionally safe to execute multiple times.
    """

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS farmer_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,

                farm_name VARCHAR(255),
                farm_location VARCHAR(255),

                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,

                land_area DOUBLE PRECISION DEFAULT 0,
                land_unit VARCHAR(30) DEFAULT 'acre',

                soil_type VARCHAR(100),
                irrigation_type VARCHAR(100),

                main_crop VARCHAR(150),
                farming_type VARCHAR(100),

                water_availability VARCHAR(100),
                budget DOUBLE PRECISION DEFAULT 0,

                farming_goal VARCHAR(255),

                village VARCHAR(150),
                district VARCHAR(150),
                state VARCHAR(150),
                pincode VARCHAR(20),

                preferred_language VARCHAR(20) DEFAULT 'en',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Add columns for older installations.

        required_columns = {
            "farm_name": "VARCHAR(255)",
            "farm_location": "VARCHAR(255)",
            "latitude": "DOUBLE PRECISION",
            "longitude": "DOUBLE PRECISION",
            "land_area": "DOUBLE PRECISION DEFAULT 0",
            "land_unit": "VARCHAR(30) DEFAULT 'acre'",
            "soil_type": "VARCHAR(100)",
            "irrigation_type": "VARCHAR(100)",
            "main_crop": "VARCHAR(150)",
            "farming_type": "VARCHAR(100)",
            "water_availability": "VARCHAR(100)",
            "budget": "DOUBLE PRECISION DEFAULT 0",
            "farming_goal": "VARCHAR(255)",
            "village": "VARCHAR(150)",
            "district": "VARCHAR(150)",
            "state": "VARCHAR(150)",
            "pincode": "VARCHAR(20)",
            "preferred_language": "VARCHAR(20) DEFAULT 'en'",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }

        for column_name, definition in required_columns.items():

            if not column_exists(
                cur,
                "farmer_profiles",
                column_name
            ):

                cur.execute(
                    f"""
                    ALTER TABLE farmer_profiles
                    ADD COLUMN {column_name} {definition}
                    """
                )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_farmer_profiles_user
            ON farmer_profiles(user_id)
            """
        )

        conn.commit()

        return True

    except Exception as exc:

        logger.exception(
            "Farmer profile table setup failed: %s",
            exc
        )

        if conn:

            try:
                conn.rollback()
            except Exception:
                pass

        return False

    finally:

        if cur:

            try:
                cur.close()
            except Exception:
                pass

        if conn:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# CONSUMER PROFILE TABLE
# ============================================================

def ensure_consumer_profile_table():

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS consumer_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,

                address TEXT,
                city VARCHAR(150),
                district VARCHAR(150),
                state VARCHAR(150),
                pincode VARCHAR(20),

                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,

                preferred_language VARCHAR(20) DEFAULT 'en',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        required_columns = {
            "address": "TEXT",
            "city": "VARCHAR(150)",
            "district": "VARCHAR(150)",
            "state": "VARCHAR(150)",
            "pincode": "VARCHAR(20)",
            "latitude": "DOUBLE PRECISION",
            "longitude": "DOUBLE PRECISION",
            "preferred_language": "VARCHAR(20) DEFAULT 'en'",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }

        for column_name, definition in required_columns.items():

            if not column_exists(
                cur,
                "consumer_profiles",
                column_name
            ):

                cur.execute(
                    f"""
                    ALTER TABLE consumer_profiles
                    ADD COLUMN {column_name} {definition}
                    """
                )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_consumer_profiles_user
            ON consumer_profiles(user_id)
            """
        )

        conn.commit()

        return True

    except Exception as exc:

        logger.exception(
            "Consumer profile table setup failed: %s",
            exc
        )

        if conn:

            try:
                conn.rollback()
            except Exception:
                pass

        return False

    finally:

        if cur:

            try:
                cur.close()
            except Exception:
                pass

        if conn:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# USER PROFILE FETCH
# ============================================================

def fetch_user_profile(
    user_id: int
):

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        if not table_exists(
            cur,
            "users"
        ):
            return None

        cur.execute(
            """
            SELECT *
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        row = cur.fetchone()

        if not row:
            return None

        if isinstance(row, dict):
            return dict(row)

        # Fallback for tuple cursor.
        columns = [
            description[0]
            for description in cur.description
        ]

        return dict(
            zip(
                columns,
                row
            )
        )

    except Exception as exc:

        logger.exception(
            "Fetching user profile failed: %s",
            exc
        )

        return None

    finally:

        if cur:

            try:
                cur.close()
            except Exception:
                pass

        if conn:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# FARM PROFILE FETCH
# ============================================================

def fetch_farmer_profile(
    user_id: int
):

    ensure_farmer_profile_table()

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM farmer_profiles
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        row = cur.fetchone()

        if not row:
            return {}

        if isinstance(row, dict):
            return dict(row)

        columns = [
            description[0]
            for description in cur.description
        ]

        return dict(
            zip(
                columns,
                row
            )
        )

    except Exception as exc:

        logger.exception(
            "Fetching farmer profile failed: %s",
            exc
        )

        return {}

    finally:

        if cur:

            try:
                cur.close()
            except Exception:
                pass

        if conn:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# CONSUMER PROFILE FETCH
# ============================================================

def fetch_consumer_profile(
    user_id: int
):

    ensure_consumer_profile_table()

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM consumer_profiles
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        row = cur.fetchone()

        if not row:
            return {}

        if isinstance(row, dict):
            return dict(row)

        columns = [
            description[0]
            for description in cur.description
        ]

        return dict(
            zip(
                columns,
                row
            )
        )

    except Exception as exc:

        logger.exception(
            "Fetching consumer profile failed: %s",
            exc
        )

        return {}

    finally:

        if cur:

            try:
                cur.close()
            except Exception:
                pass

        if conn:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# PROFILE PAGE
# ============================================================

@profile_bp.route(
    "/profile",
    methods=["GET"]
)
@login_required
def profile():

    user_id = get_user_id()
    role = get_role()
    language = get_language()

    user = fetch_user_profile(
        user_id
    )

    if not user:

        return jsonify({
            "success": False,
            "message": "User profile not found."
        }), 404

    farmer = {}
    consumer = {}

    if role == "farmer":

        farmer = fetch_farmer_profile(
            user_id
        )

    elif role == "consumer":

        consumer = fetch_consumer_profile(
            user_id
        )

    # Keep session information synchronized.

    if user.get("name"):
        session["name"] = user["name"]

    if user.get("role"):
        session["role"] = str(
            user["role"]
        ).lower()

    return render_template(
        "profile.html",
        user=user,
        farmer=farmer,
        consumer=consumer,
        role=role,
        language=language,
        direction=get_direction(
            language
        ),
        supported_languages=SUPPORTED_LANGUAGES,
        rtl_languages=RTL_LANGUAGES,
    )


# ============================================================
# UPDATE BASIC USER PROFILE
# ============================================================

@profile_bp.route(
    "/api/profile",
    methods=["GET", "PUT", "POST"]
)
@login_required
def api_profile():

    user_id = get_user_id()

    if request.method == "GET":

        user = fetch_user_profile(
            user_id
        )

        if not user:

            return jsonify({
                "success": False,
                "message": "Profile not found."
            }), 404

        role = get_role()

        result = {
            "user": user,
            "role": role,
            "language": get_language(),
            "direction": get_direction(
                get_language()
            ),
        }

        if role == "farmer":

            result["farm_profile"] = (
                fetch_farmer_profile(
                    user_id
                )
            )

        elif role == "consumer":

            result["consumer_profile"] = (
                fetch_consumer_profile(
                    user_id
                )
            )

        return jsonify({
            "success": True,
            **result,
        })

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    )

    if not data:

        data = request.form.to_dict()

    name = clean_text(
        data.get("name")
        or data.get("fullname")
        or data.get("full_name"),
        255
    )

    email = clean_email(
        data.get("email")
    )

    mobile = clean_mobile(
        data.get("mobile")
        or data.get("phone")
    )

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        # ----------------------------------------------------
        # Detect available user columns.
        # ----------------------------------------------------

        available = {}

        for column in [
            "name",
            "fullname",
            "email",
            "mobile",
            "phone",
            "location",
            "language",
            "preferred_language",
        ]:

            available[column] = column_exists(
                cur,
                "users",
                column
            )

        updates = []
        values = []

        # Name
        if name:

            if available["name"]:

                updates.append(
                    "name = %s"
                )

                values.append(name)

            elif available["fullname"]:

                updates.append(
                    "fullname = %s"
                )

                values.append(name)

        # Email
        if email and available["email"]:

            updates.append(
                "email = %s"
            )

            values.append(email)

        # Mobile
        if mobile:

            if available["mobile"]:

                updates.append(
                    "mobile = %s"
                )

                values.append(mobile)

            elif available["phone"]:

                updates.append(
                    "phone = %s"
                )

                values.append(mobile)

        # Location
        location = clean_text(
            data.get("location"),
            255
        )

        if location and available["location"]:

            updates.append(
                "location = %s"
            )

            values.append(location)

        # ----------------------------------------------------
        # Execute only if something is available.
        # ----------------------------------------------------

        if updates:

            values.append(
                user_id
            )

            cur.execute(
                f"""
                UPDATE users
                SET {", ".join(updates)}
                WHERE id = %s
                """,
                tuple(values)
            )

        # ----------------------------------------------------
        # Global language
        # ----------------------------------------------------

        language = str(
            data.get(
                "language",
                get_language()
            )
        ).lower().strip()

        if language in SUPPORTED_LANGUAGES:

            session["language"] = language

            if available["language"]:

                cur.execute(
                    """
                    UPDATE users
                    SET language = %s
                    WHERE id = %s
                    """,
                    (
                        language,
                        user_id,
                    )
                )

            elif available["preferred_language"]:

                cur.execute(
                    """
                    UPDATE users
                    SET preferred_language = %s
                    WHERE id = %s
                    """,
                    (
                        language,
                        user_id,
                    )
                )

        # Session name.
        if name:
            session["name"] = name

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Profile updated successfully.",
            "language": get_language(),
            "direction": get_direction(
                get_language()
            ),
        })

    except Exception as exc:

        logger.exception(
            "User profile update failed: %s",
            exc
        )

        if conn:

            try:
                conn.rollback()
            except Exception:
                pass

        return jsonify({
            "success": False,
            "message": "Unable to update profile."
        }), 500

    finally:

        if cur:

            try:
                cur.close()
            except Exception:
                pass

        if conn:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# FARM PROFILE API
# ============================================================

@profile_bp.route(
    "/api/profile/farm",
    methods=["GET", "PUT", "POST"]
)
@login_required
def farm_profile_api():

    user_id = get_user_id()

    ensure_farmer_profile_table()

    if request.method == "GET":

        return jsonify({
            "success": True,
            "profile": fetch_farmer_profile(
                user_id
            ),
        })

    data = request.get_json(
        silent=True
    )

    if not data:
        data = request.form.to_dict()

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    def to_float(
        value,
        default=0.0
    ):

        try:

            if value in (
                None,
                "",
            ):
                return default

            return float(value)

        except (
            TypeError,
            ValueError
        ):

            return default

    land_area = to_float(
        data.get(
            "land_area",
            data.get(
                "area",
                0
            )
        )
    )

    budget = to_float(
        data.get(
            "budget",
            0
        )
    )

    latitude = data.get(
        "latitude"
    )

    longitude = data.get(
        "longitude"
    )

    latitude = (
        to_float(latitude, None)
        if latitude not in (
            None,
            ""
        )
        else None
    )

    longitude = (
        to_float(longitude, None)
        if longitude not in (
            None,
            ""
        )
        else None
    )

    farm_name = clean_text(
        data.get("farm_name"),
        255
    )

    farm_location = clean_text(
        data.get("farm_location")
        or data.get("location"),
        255
    )

    land_unit = clean_text(
        data.get(
            "land_unit",
            "acre"
        ),
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
        data.get("main_crop")
        or data.get("crop"),
        150
    )

    farming_type = clean_text(
        data.get("farming_type"),
        100
    )

    water_availability = clean_text(
        data.get("water_availability"),
        100
    )

    farming_goal = clean_text(
        data.get("farming_goal")
        or data.get("goal"),
        255
    )

    village = clean_text(
        data.get("village"),
        150
    )

    district = clean_text(
        data.get("district"),
        150
    )

    state = clean_text(
        data.get("state"),
        150
    )

    pincode = clean_text(
        data.get("pincode"),
        20
    )

    language = str(
        data.get(
            "language",
            get_language()
        )
    ).lower().strip()

    if language not in SUPPORTED_LANGUAGES:
        language = get_language()

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if land_area < 0:

        return jsonify({
            "success": False,
            "message": "Land area cannot be negative."
        }), 400

    if budget < 0:

        return jsonify({
            "success": False,
            "message": "Budget cannot be negative."
        }), 400

    if latitude is not None:

        if not -90 <= latitude <= 90:

            return jsonify({
                "success": False,
                "message": "Invalid latitude."
            }), 400

    if longitude is not None:

        if not -180 <= longitude <= 180:

            return jsonify({
                "success": False,
                "message": "Invalid longitude."
            }), 400

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO farmer_profiles
                (
                    user_id,
                    farm_name,
                    farm_location,
                    latitude,
                    longitude,
                    land_area,
                    land_unit,
                    soil_type,
                    irrigation_type,
                    main_crop,
                    farming_type,
                    water_availability,
                    budget,
                    farming_goal,
                    village,
                    district,
                    state,
                    pincode,
                    preferred_language,
                    updated_at
                )
            VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    CURRENT_TIMESTAMP
                )
            ON CONFLICT (user_id)
            DO UPDATE SET
                farm_name = EXCLUDED.farm_name,
                farm_location = EXCLUDED.farm_location,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                land_area = EXCLUDED.land_area,
                land_unit = EXCLUDED.land_unit,
                soil_type = EXCLUDED.soil_type,
                irrigation_type = EXCLUDED.irrigation_type,
                main_crop = EXCLUDED.main_crop,
                farming_type = EXCLUDED.farming_type,
                water_availability = EXCLUDED.water_availability,
                budget = EXCLUDED.budget,
                farming_goal = EXCLUDED.farming_goal,
                village = EXCLUDED.village,
                district = EXCLUDED.district,
                state = EXCLUDED.state,
                pincode = EXCLUDED.pincode,
                preferred_language = EXCLUDED.preferred_language,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                farm_name or None,
                farm_location or None,
                latitude,
                longitude,
                land_area,
                land_unit or "acre",
                soil_type or None,
                irrigation_type or None,
                main_crop or None,
                farming_type or None,
                water_availability or None,
                budget,
                farming_goal or None,
                village or None,
                district or None,
                state or None,
                pincode or None,
                language,
            )
        )

        conn.commit()

        # Global language.
        session["language"] = language

        return jsonify({
            "success": True,
            "message": "Farm profile saved successfully.",
            "profile": fetch_farmer_profile(
                user_id
            ),
            "language": language,
            "direction": get_direction(
                language
            ),
        })

    except Exception as exc:

        logger.exception(
            "Farm profile update failed: %s",
            exc
        )

        if conn:

            try:
                conn.rollback()
            except Exception:
                pass

        return jsonify({
            "success": False,
            "message": "Unable to save farm profile."
        }), 500

    finally:

        if cur:

            try:
                cur.close()
            except Exception:
                pass

        if conn:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# LOCATION API
# ============================================================

@profile_bp.route(
    "/api/profile/location",
    methods=["GET", "POST", "PUT"]
)
@login_required
def profile_location():

    user_id = get_user_id()
    role = get_role()

    if request.method == "GET":

        if role == "farmer":

            profile = fetch_farmer_profile(
                user_id
            )

            return jsonify({
                "success": True,
                "latitude": profile.get(
                    "latitude"
                ),
                "longitude": profile.get(
                    "longitude"
                ),
                "location": profile.get(
                    "farm_location"
                ),
                "district": profile.get(
                    "district"
                ),
                "state": profile.get(
                    "state"
                ),
            })

        user = fetch_user_profile(
            user_id
        ) or {}

        return jsonify({
            "success": True,
            "location": user.get(
                "location"
            ),
        })

    data = request.get_json(
        silent=True
    ) or {}

    location = clean_text(
        data.get("location"),
        255
    )

    try:

        latitude = (
            float(data["latitude"])
            if data.get("latitude") not in (
                None,
                ""
            )
            else None
        )

        longitude = (
            float(data["longitude"])
            if data.get("longitude") not in (
                None,
                ""
            )
            else None
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "success": False,
            "message": "Invalid GPS coordinates."
        }), 400

    if latitude is not None and not (
        -90 <= latitude <= 90
    ):

        return jsonify({
            "success": False,
            "message": "Invalid latitude."
        }), 400

    if longitude is not None and not (
        -180 <= longitude <= 180
    ):

        return jsonify({
            "success": False,
            "message": "Invalid longitude."
        }), 400

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        if role == "farmer":

            ensure_farmer_profile_table()

            cur.execute(
                """
                INSERT INTO farmer_profiles
                    (
                        user_id,
                        farm_location,
                        latitude,
                        longitude,
                        updated_at
                    )
                VALUES
                    (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    farm_location = COALESCE(
                        EXCLUDED.farm_location,
                        farmer_profiles.farm_location
                    ),
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    location or None,
                    latitude,
                    longitude,
                )
            )

        else:

            if column_exists(
                cur,
                "users",
                "location"
            ):

                cur.execute(
                    """
                    UPDATE users
                    SET location = %s
                    WHERE id = %s
                    """,
                    (
                        location or None,
                        user_id,
                    )
                )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Location updated successfully.",
            "latitude": latitude,
            "longitude": longitude,
            "location": location,
        })

    except Exception as exc:

        logger.exception(
            "Profile location update failed: %s",
            exc
        )

        if conn:

            try:
                conn.rollback()
            except Exception:
                pass

        return jsonify({
            "success": False,
            "message": "Unable to update location."
        }), 500

    finally:

        if cur:

            try:
                cur.close()
            except Exception:
                pass

        if conn:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# LANGUAGE API
# ============================================================

@profile_bp.route(
    "/api/profile/language",
    methods=["GET", "POST", "PUT"]
)
@login_required
def profile_language():

    if request.method == "GET":

        language = get_language()

        return jsonify({
            "success": True,
            "language": language,
            "language_name": SUPPORTED_LANGUAGES[
                language
            ],
            "direction": get_direction(
                language
            ),
            "supported_languages": (
                SUPPORTED_LANGUAGES
            ),
        })

    data = request.get_json(
        silent=True
    ) or {}

    language = str(
        data.get(
            "language",
            ""
        )
    ).lower().strip()

    if language not in SUPPORTED_LANGUAGES:

        return jsonify({
            "success": False,
            "message": "Unsupported language."
        }), 400

    user_id = get_user_id()

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        # Update users if supported.

        if column_exists(
            cur,
            "users",
            "language"
        ):

            cur.execute(
                """
                UPDATE users
                SET language = %s
                WHERE id = %s
                """,
                (
                    language,
                    user_id,
                )
            )

        elif column_exists(
            cur,
            "users",
            "preferred_language"
        ):

            cur.execute(
                """
                UPDATE users
                SET preferred_language = %s
                WHERE id = %s
                """,
                (
                    language,
                    user_id,
                )
            )

        # Role-specific profile.

        role = get_role()

        if role == "farmer":

            ensure_farmer_profile_table()

            cur.execute(
                """
                INSERT INTO farmer_profiles
                    (
                        user_id,
                        preferred_language
                    )
                VALUES
                    (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    preferred_language = EXCLUDED.preferred_language,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    language,
                )
            )

        elif role == "consumer":

            ensure_consumer_profile_table()

            cur.execute(
                """
                INSERT INTO consumer_profiles
                    (
                        user_id,
                        preferred_language
                    )
                VALUES
                    (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    preferred_language = EXCLUDED.preferred_language,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    language,
                )
            )

        conn.commit()

        # IMPORTANT:
        # Language is global for the whole application.
        session["language"] = language

        return jsonify({
            "success": True,
            "language": language,
            "language_name": SUPPORTED_LANGUAGES[
                language
            ],
            "direction": get_direction(
                language
            ),
            "message": "Application language updated.",
        })

    except Exception as exc:

        logger.exception(
            "Profile language update failed: %s",
            exc
        )

        if conn:

            try:
                conn.rollback()
            except Exception:
                pass

        return jsonify({
            "success": False,
            "message": "Unable to update language."
        }), 500

    finally:

        if cur:

            try:
                cur.close()
            except Exception:
                pass

        if conn:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# FARM PROFILE SUMMARY
# ============================================================

@profile_bp.route(
    "/api/profile/summary",
    methods=["GET"]
)
@login_required
def profile_summary():

    user_id = get_user_id()
    role = get_role()

    user = fetch_user_profile(
        user_id
    ) or {}

    result = {
        "name": (
            user.get("name")
            or user.get("fullname")
            or session.get("name")
            or "User"
        ),
        "email": user.get(
            "email"
        ),
        "mobile": (
            user.get("mobile")
            or user.get("phone")
        ),
        "role": role,
        "language": get_language(),
    }

    if role == "farmer":

        farm = fetch_farmer_profile(
            user_id
        )

        result.update({
            "farm_name": farm.get(
                "farm_name"
            ),
            "farm_location": farm.get(
                "farm_location"
            ),
            "land_area": farm.get(
                "land_area",
                0
            ),
            "land_unit": farm.get(
                "land_unit",
                "acre"
            ),
            "soil_type": farm.get(
                "soil_type"
            ),
            "irrigation_type": farm.get(
                "irrigation_type"
            ),
            "main_crop": farm.get(
                "main_crop"
            ),
            "farming_goal": farm.get(
                "farming_goal"
            ),
            "latitude": farm.get(
                "latitude"
            ),
            "longitude": farm.get(
                "longitude"
            ),
        })

    return jsonify({
        "success": True,
        "profile": result,
    })


# ============================================================
# PROFILE HEALTH
# ============================================================

@profile_bp.route(
    "/api/profile/health",
    methods=["GET"]
)
def profile_health():

    database = False

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT 1"
        )

        cur.fetchone()

        database = True

        cur.close()
        conn.close()

    except Exception as exc:

        logger.warning(
            "Profile health database error: %s",
            exc
        )

    return jsonify({
        "success": True,
        "service": "KisanVision360+ Profile",
        "status": (
            "healthy"
            if database
            else "degraded"
        ),
        "database": (
            "connected"
            if database
            else "unavailable"
        ),
        "languages": len(
            SUPPORTED_LANGUAGES
        ),
    })


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_profile_service():
    """
    Initialize profile-related tables.

    Call from app.py during startup if required.
    """

    farmer_ok = ensure_farmer_profile_table()
    consumer_ok = ensure_consumer_profile_table()

    return (
        farmer_ok
        and consumer_ok
    )


# ============================================================
# END OF FILE
# ============================================================
