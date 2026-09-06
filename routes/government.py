# ============================================================
# KISANVISION360+ â€” GOVERNMENT SCHEMES ROUTE
# File: routes/government.py
# ============================================================

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash,
)

from database.db import get_db_connection

from datetime import datetime
import logging


# ============================================================
# BLUEPRINT
# ============================================================

government_bp = Blueprint("government", __name__)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_SCHEMES = [
    {
        "name": "PM-KISAN",
        "department": "Ministry of Agriculture & Farmers Welfare",
        "purpose": "Income support for eligible farmer families.",
        "eligibility": "Eligible landholding farmer families as per scheme rules.",
        "link": "https://pmkisan.gov.in/",
        "category": "Income Support",
    },
    {
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "department": "Ministry of Agriculture & Farmers Welfare",
        "purpose": "Crop insurance support against notified crop risks.",
        "eligibility": "Farmers cultivating notified crops in notified areas, subject to scheme rules.",
        "link": "https://pmfby.gov.in/",
        "category": "Crop Insurance",
    },
    {
        "name": "Kisan Credit Card",
        "department": "Government of India / Banking System",
        "purpose": "Agricultural credit support for farming and allied activities.",
        "eligibility": "Eligible farmers and agricultural borrowers as per lending rules.",
        "link": "https://www.myscheme.gov.in/",
        "category": "Credit",
    },
    {
        "name": "PM Krishi Sinchai Yojana",
        "department": "Government of India",
        "purpose": "Support for improved irrigation and water-use efficiency.",
        "eligibility": "Eligibility varies according to the applicable component and state guidelines.",
        "link": "https://pmksy.gov.in/",
        "category": "Irrigation",
    },
    {
        "name": "Soil Health Card",
        "department": "Ministry of Agriculture & Farmers Welfare",
        "purpose": "Soil testing and nutrient-management recommendations.",
        "eligibility": "Farmers can access soil testing and recommendations through applicable government facilities.",
        "link": "https://soilhealth.dac.gov.in/",
        "category": "Soil",
    },
    {
        "name": "e-NAM",
        "department": "Ministry of Agriculture & Farmers Welfare",
        "purpose": "Online agricultural market platform for improved market access.",
        "eligibility": "Participation depends on applicable mandi and platform rules.",
        "link": "https://www.enam.gov.in/",
        "category": "Market",
    },
    {
        "name": "PM-KUSUM",
        "department": "Ministry of New and Renewable Energy",
        "purpose": "Support for solar energy applications in agriculture.",
        "eligibility": "Eligibility depends on the applicable component and state implementation.",
        "link": "https://pmkusum.mnre.gov.in/",
        "category": "Energy",
    },
    {
        "name": "Agriculture Infrastructure Fund",
        "department": "Government of India",
        "purpose": "Financing support for agricultural infrastructure projects.",
        "eligibility": "Eligible beneficiaries and projects according to AIF guidelines.",
        "link": "https://agriinfra.dac.gov.in/",
        "category": "Infrastructure",
    },
]


# ============================================================
# FARMER ACCESS
# ============================================================

def farmer_required():
    """
    Allow only logged-in farmers.
    """

    role = str(session.get("role", "")).strip().lower()

    if role != "farmer":
        return False

    return bool(
        session.get("user_id")
        or session.get("id")
        or session.get("user")
    )


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

        if isinstance(row, dict):
            return bool(row.get("exists"))

        return bool(row[0])

    except Exception:
        return False


def ensure_scheme_table():
    """
    Create government_schemes table if it does not exist.

    This makes the module easier to deploy on a fresh PostgreSQL
    database.
    """

    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS government_schemes (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                department VARCHAR(255),
                purpose TEXT,
                eligibility TEXT,
                link TEXT,
                category VARCHAR(100),
                state VARCHAR(100) DEFAULT 'All India',
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_government_schemes_category
            ON government_schemes(category)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_government_schemes_active
            ON government_schemes(active)
            """
        )

        conn.commit()

        cursor.close()

    except Exception as exc:
        if conn:
            conn.rollback()

        logger.warning(
            "Government scheme table initialization failed: %s",
            exc,
        )

    finally:
        if conn:
            conn.close()


# ============================================================
# USER / FARMER PROFILE
# ============================================================

def get_current_user_id():
    """
    Get logged-in user ID from session.
    """

    user_id = (
        session.get("user_id")
        or session.get("id")
        or session.get("user_id")
    )

    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def get_farmer_profile():
    """
    Fetch farmer profile information.

    Uses LEFT JOIN so the route continues working even when
    farmer_profiles has not been completed yet.
    """

    user_id = get_current_user_id()

    if not user_id:
        return {}

    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                u.id,
                u.name,
                u.email,
                u.mobile,
                u.location,

                fp.id AS farmer_profile_id,
                fp.farm_size,
                fp.land_size,
                fp.soil_type,
                fp.irrigation_type,
                fp.primary_crop,
                fp.water_source,
                fp.state,
                fp.district

            FROM users u

            LEFT JOIN farmer_profiles fp
                ON fp.user_id = u.id

            WHERE u.id = %s

            LIMIT 1
            """,
            (user_id,),
        )

        row = cursor.fetchone()

        cursor.close()

        if not row:
            return {}

        if isinstance(row, dict):
            return dict(row)

        columns = [
            "id",
            "name",
            "email",
            "mobile",
            "location",
            "farmer_profile_id",
            "farm_size",
            "land_size",
            "soil_type",
            "irrigation_type",
            "primary_crop",
            "water_source",
            "state",
            "district",
        ]

        return dict(zip(columns, row))

    except Exception as exc:
        logger.warning(
            "Unable to load farmer profile: %s",
            exc,
        )

        return {}

    finally:
        if conn:
            conn.close()


# ============================================================
# SCHEME DATA
# ============================================================

def get_schemes_from_database():
    """
    Get active schemes from PostgreSQL.

    If database contains no schemes, return the built-in
    official-reference list.
    """

    ensure_scheme_table()

    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                department,
                purpose,
                eligibility,
                link,
                category,
                state,
                active,
                created_at,
                updated_at
            FROM government_schemes
            WHERE active = TRUE
            ORDER BY name ASC
            """
        )

        rows = cursor.fetchall()

        cursor.close()

        schemes = []

        for row in rows:

            if isinstance(row, dict):
                scheme = dict(row)

            else:
                columns = [
                    "id",
                    "name",
                    "department",
                    "purpose",
                    "eligibility",
                    "link",
                    "category",
                    "state",
                    "active",
                    "created_at",
                    "updated_at",
                ]

                scheme = dict(zip(columns, row))

            schemes.append(scheme)

        if schemes:
            return schemes

    except Exception as exc:
        logger.warning(
            "Unable to read government schemes: %s",
            exc,
        )

    finally:
        if conn:
            conn.close()

    return DEFAULT_SCHEMES.copy()


# ============================================================
# SCHEME MATCHING ENGINE
# ============================================================

def normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def calculate_scheme_match(scheme, profile):
    """
    Explainable rule-based scheme matching.

    This is NOT fake AI. It uses farmer profile attributes
    to calculate a transparent relevance score.
    """

    score = 50

    reasons = []

    category = normalize_text(
        scheme.get("category")
    )

    name = normalize_text(
        scheme.get("name")
    )

    purpose = normalize_text(
        scheme.get("purpose")
    )

    primary_crop = normalize_text(
        profile.get("primary_crop")
    )

    soil_type = normalize_text(
        profile.get("soil_type")
    )

    irrigation = normalize_text(
        profile.get("irrigation_type")
    )

    water_source = normalize_text(
        profile.get("water_source")
    )

    state = normalize_text(
        profile.get("state")
    )

    location = normalize_text(
        profile.get("location")
    )

    # --------------------------------------------------------
    # IRRIGATION
    # --------------------------------------------------------

    if category == "irrigation":
        score += 25
        reasons.append(
            "Useful for irrigation and water-management needs."
        )

    if irrigation:
        if irrigation in {
            "drip",
            "sprinkler",
            "micro irrigation",
            "micro-irrigation",
        }:
            score += 8
            reasons.append(
                "Your irrigation profile may benefit from water-efficiency support."
            )

    # --------------------------------------------------------
    # SOIL
    # --------------------------------------------------------

    if category == "soil":
        score += 25
        reasons.append(
            "Useful for improving soil and nutrient management."
        )

    if soil_type:
        score += 5

    # --------------------------------------------------------
    # CROP INSURANCE
    # --------------------------------------------------------

    if category == "crop insurance":
        score += 20
        reasons.append(
            "Relevant for managing agricultural crop risk."
        )

    if primary_crop:
        score += 8
        reasons.append(
            f"Your primary crop is {profile.get('primary_crop')}."
        )

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    if category == "market":
        score += 18
        reasons.append(
            "Can improve agricultural market access."
        )

    # --------------------------------------------------------
    # CREDIT
    # --------------------------------------------------------

    if category == "credit":
        score += 18
        reasons.append(
            "May be useful for agricultural credit requirements."
        )

    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    if category == "energy":
        score += 15
        reasons.append(
            "May be relevant for agricultural energy requirements."
        )

    # --------------------------------------------------------
    # INFRASTRUCTURE
    # --------------------------------------------------------

    if category == "infrastructure":
        score += 15
        reasons.append(
            "Can be relevant for farm infrastructure development."
        )

    # --------------------------------------------------------
    # INCOME
    # --------------------------------------------------------

    if category == "income support":
        score += 20
        reasons.append(
            "Relevant to farmer income-support programs."
        )

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    if state:
        scheme_state = normalize_text(
            scheme.get("state")
        )

        if scheme_state in {"", "all india", "india"}:
            score += 5

        elif state == scheme_state:
            score += 10
            reasons.append(
                "The scheme location matches your profile."
            )

    elif location:
        score += 2

    # --------------------------------------------------------
    # TEXT MATCHING
    # --------------------------------------------------------

    combined_text = (
        name + " " +
        purpose + " " +
        category
    )

    if primary_crop and primary_crop in combined_text:
        score += 5

    if water_source and (
        water_source in combined_text
        or "water" in combined_text
        or "irrigation" in combined_text
    ):
        score += 4

    score = max(0, min(100, score))

    if score >= 85:
        level = "Highly Relevant"
    elif score >= 70:
        level = "Relevant"
    elif score >= 55:
        level = "Potentially Useful"
    else:
        level = "General Information"

    return {
        "score": score,
        "level": level,
        "reasons": reasons[:4],
    }


# ============================================================
# ENRICH SCHEMES
# ============================================================

def enrich_schemes(schemes, profile):
    result = []

    for scheme in schemes:

        item = dict(scheme)

        match = calculate_scheme_match(
            item,
            profile,
        )

        item["match_score"] = match["score"]
        item["match_level"] = match["level"]
        item["match_reasons"] = match["reasons"]

        result.append(item)

    result.sort(
        key=lambda x: x.get("match_score", 0),
        reverse=True,
    )

    return result


# ============================================================
# MAIN GOVERNMENT SCHEMES PAGE
# ============================================================

@government_bp.route("/government", methods=["GET"])
def government():

    if not farmer_required():
        flash(
            "Please login as a farmer to access government schemes.",
            "warning",
        )

        return redirect(
            url_for("auth.login")
        )

    try:
        profile = get_farmer_profile()

        schemes = get_schemes_from_database()

        schemes = enrich_schemes(
            schemes,
            profile,
        )

        categories = sorted(
            {
                str(s.get("category", "")).strip()
                for s in schemes
                if s.get("category")
            }
        )

        return render_template(
            "government.html",
            schemes=schemes,
            categories=categories,
            profile=profile,
            language=session.get(
                "language",
                "en",
            ),
        )

    except Exception as exc:

        logger.exception(
            "Government schemes page error"
        )

        return render_template(
            "government.html",
            schemes=DEFAULT_SCHEMES,
            categories=[
                "Income Support",
                "Crop Insurance",
                "Credit",
                "Irrigation",
                "Soil",
                "Market",
                "Energy",
                "Infrastructure",
            ],
            profile={},
            language=session.get(
                "language",
                "en",
            ),
            error="Unable to load live scheme data.",
        )


# ============================================================
# API â€” ALL SCHEMES
# ============================================================

@government_bp.route(
    "/api/government/schemes",
    methods=["GET"],
)
def api_government_schemes():

    if not farmer_required():
        return jsonify({
            "success": False,
            "message": "Farmer login required.",
        }), 401

    try:

        profile = get_farmer_profile()

        schemes = get_schemes_from_database()

        schemes = enrich_schemes(
            schemes,
            profile,
        )

        search = normalize_text(
            request.args.get("search")
        )

        category = normalize_text(
            request.args.get("category")
        )

        if search:
            schemes = [
                scheme
                for scheme in schemes
                if (
                    search in normalize_text(
                        scheme.get("name")
                    )
                    or search in normalize_text(
                        scheme.get("purpose")
                    )
                    or search in normalize_text(
                        scheme.get("department")
                    )
                    or search in normalize_text(
                        scheme.get("category")
                    )
                )
            ]

        if category and category != "all":
            schemes = [
                scheme
                for scheme in schemes
                if normalize_text(
                    scheme.get("category")
                ) == category
            ]

        return jsonify({
            "success": True,
            "count": len(schemes),
            "schemes": schemes,
            "generated_at": datetime.utcnow().isoformat(),
        })

    except Exception as exc:

        logger.exception(
            "Government scheme API error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to load government schemes.",
            "error": str(exc),
        }), 500


# ============================================================
# API â€” PERSONALIZED SCHEMES
# ============================================================

@government_bp.route(
    "/api/government/recommendations",
    methods=["GET"],
)
def api_government_recommendations():

    if not farmer_required():
        return jsonify({
            "success": False,
            "message": "Farmer login required.",
        }), 401

    try:

        profile = get_farmer_profile()

        schemes = get_schemes_from_database()

        schemes = enrich_schemes(
            schemes,
            profile,
        )

        limit = request.args.get(
            "limit",
            5,
        )

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 5

        limit = max(
            1,
            min(limit, 20),
        )

        recommendations = schemes[:limit]

        return jsonify({
            "success": True,
            "profile": profile,
            "recommendations": recommendations,
            "count": len(recommendations),
        })

    except Exception as exc:

        logger.exception(
            "Government recommendation error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to generate scheme recommendations.",
            "error": str(exc),
        }), 500


# ============================================================
# API â€” SINGLE SCHEME
# ============================================================

@government_bp.route(
    "/api/government/schemes/<int:scheme_id>",
    methods=["GET"],
)
def api_single_scheme(scheme_id):

    if not farmer_required():
        return jsonify({
            "success": False,
            "message": "Farmer login required.",
        }), 401

    conn = None

    try:

        ensure_scheme_table()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                department,
                purpose,
                eligibility,
                link,
                category,
                state,
                active,
                created_at,
                updated_at
            FROM government_schemes
            WHERE id = %s
              AND active = TRUE
            LIMIT 1
            """,
            (scheme_id,),
        )

        row = cursor.fetchone()

        cursor.close()

        if not row:
            return jsonify({
                "success": False,
                "message": "Scheme not found.",
            }), 404

        if isinstance(row, dict):
            scheme = dict(row)
        else:
            columns = [
                "id",
                "name",
                "department",
                "purpose",
                "eligibility",
                "link",
                "category",
                "state",
                "active",
                "created_at",
                "updated_at",
            ]

            scheme = dict(
                zip(columns, row)
            )

        match = calculate_scheme_match(
            scheme,
            get_farmer_profile(),
        )

        scheme.update({
            "match_score": match["score"],
            "match_level": match["level"],
            "match_reasons": match["reasons"],
        })

        return jsonify({
            "success": True,
            "scheme": scheme,
        })

    except Exception as exc:

        logger.exception(
            "Single scheme API error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to load scheme.",
            "error": str(exc),
        }), 500

    finally:
        if conn:
            conn.close()


# ============================================================
# API â€” FARMER PROFILE FOR SCHEME MATCHING
# ============================================================

@government_bp.route(
    "/api/government/profile",
    methods=["GET"],
)
def api_government_profile():

    if not farmer_required():
        return jsonify({
            "success": False,
            "message": "Farmer login required.",
        }), 401

    try:

        profile = get_farmer_profile()

        return jsonify({
            "success": True,
            "profile": profile,
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": "Unable to load farmer profile.",
            "error": str(exc),
        }), 500


# ============================================================
# API â€” CATEGORIES
# ============================================================

@government_bp.route(
    "/api/government/categories",
    methods=["GET"],
)
def api_government_categories():

    if not farmer_required():
        return jsonify({
            "success": False,
            "message": "Farmer login required.",
        }), 401

    try:

        schemes = get_schemes_from_database()

        categories = sorted(
            {
                str(
                    scheme.get(
                        "category",
                        "",
                    )
                ).strip()
                for scheme in schemes
                if scheme.get("category")
            }
        )

        return jsonify({
            "success": True,
            "categories": categories,
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "message": "Unable to load categories.",
            "error": str(exc),
        }), 500


# ============================================================
# ADMIN â€” ADD SCHEME
# ============================================================

@government_bp.route(
    "/api/government/schemes",
    methods=["POST"],
)
def create_scheme():

    role = str(
        session.get("role", "")
    ).strip().lower()

    if role != "admin":
        return jsonify({
            "success": False,
            "message": "Admin access required.",
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get("name", "")
    ).strip()

    if not name:
        return jsonify({
            "success": False,
            "message": "Scheme name is required.",
        }), 400

    conn = None

    try:

        ensure_scheme_table()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO government_schemes (
                name,
                department,
                purpose,
                eligibility,
                link,
                category,
                state,
                active
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, TRUE
            )
            RETURNING id
            """,
            (
                name,
                data.get("department"),
                data.get("purpose"),
                data.get("eligibility"),
                data.get("link"),
                data.get("category"),
                data.get(
                    "state",
                    "All India",
                ),
            ),
        )

        row = cursor.fetchone()

        conn.commit()

        cursor.close()

        scheme_id = (
            row["id"]
            if isinstance(row, dict)
            else row[0]
        )

        return jsonify({
            "success": True,
            "message": "Government scheme added successfully.",
            "scheme_id": scheme_id,
        }), 201

    except Exception as exc:

        if conn:
            conn.rollback()

        logger.exception(
            "Unable to create scheme"
        )

        return jsonify({
            "success": False,
            "message": "Unable to create scheme.",
            "error": str(exc),
        }), 500

    finally:
        if conn:
            conn.close()


# ============================================================
# ADMIN â€” UPDATE SCHEME
# ============================================================

@government_bp.route(
    "/api/government/schemes/<int:scheme_id>",
    methods=["PUT"],
)
def update_scheme(scheme_id):

    role = str(
        session.get("role", "")
    ).strip().lower()

    if role != "admin":
        return jsonify({
            "success": False,
            "message": "Admin access required.",
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    conn = None

    try:

        ensure_scheme_table()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE government_schemes
            SET
                name = COALESCE(%s, name),
                department = COALESCE(%s, department),
                purpose = COALESCE(%s, purpose),
                eligibility = COALESCE(%s, eligibility),
                link = COALESCE(%s, link),
                category = COALESCE(%s, category),
                state = COALESCE(%s, state),
                active = COALESCE(%s, active),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                data.get("name"),
                data.get("department"),
                data.get("purpose"),
                data.get("eligibility"),
                data.get("link"),
                data.get("category"),
                data.get("state"),
                data.get("active"),
                scheme_id,
            ),
        )

        if cursor.rowcount == 0:
            conn.rollback()

            return jsonify({
                "success": False,
                "message": "Scheme not found.",
            }), 404

        conn.commit()

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Government scheme updated successfully.",
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        logger.exception(
            "Unable to update scheme"
        )

        return jsonify({
            "success": False,
            "message": "Unable to update scheme.",
            "error": str(exc),
        }), 500

    finally:
        if conn:
            conn.close()


# ============================================================
# ADMIN â€” DELETE / DEACTIVATE SCHEME
# ============================================================

@government_bp.route(
    "/api/government/schemes/<int:scheme_id>",
    methods=["DELETE"],
)
def delete_scheme(scheme_id):

    role = str(
        session.get("role", "")
    ).strip().lower()

    if role != "admin":
        return jsonify({
            "success": False,
            "message": "Admin access required.",
        }), 403

    conn = None

    try:

        ensure_scheme_table()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Soft delete keeps historical records safe.
        cursor.execute(
            """
            UPDATE government_schemes
            SET
                active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (scheme_id,),
        )

        if cursor.rowcount == 0:
            conn.rollback()

            return jsonify({
                "success": False,
                "message": "Scheme not found.",
            }), 404

        conn.commit()

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Government scheme removed successfully.",
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        logger.exception(
            "Unable to delete scheme"
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete scheme.",
            "error": str(exc),
        }), 500

    finally:
        if conn:
            conn.close()


# ============================================================
# HEALTH CHECK
# ============================================================

@government_bp.route(
    "/api/government/health",
    methods=["GET"],
)
def government_health():

    conn = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1"
        )

        cursor.fetchone()

        cursor.close()

        return jsonify({
            "success": True,
            "service": "government_schemes",
            "database": "connected",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "service": "government_schemes",
            "database": "disconnected",
            "status": "error",
            "error": str(exc),
        }), 500

    finally:
        if conn:
            conn.close()


# ============================================================
# BLUEPRINT EXPORT
# ============================================================

__all__ = [
    "government_bp",
]
