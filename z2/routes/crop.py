# ============================================================
# KISANVISION360+
# routes/crop.py
# Crop Details + Growth Tracking + Harvest Intelligence
# PostgreSQL / Supabase Ready
# ============================================================

from datetime import datetime, date

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


# ============================================================
# BLUEPRINT
# ============================================================

crop_bp = Blueprint("crop", __name__)


# ============================================================
# CROP TABLE
# ============================================================

CROP_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS crops (
    id BIGSERIAL PRIMARY KEY,
    farmer_id BIGINT NOT NULL,
    crop_name VARCHAR(150) NOT NULL,
    sowing_date DATE NOT NULL,
    duration_days INTEGER NOT NULL DEFAULT 120,
    soil_type VARCHAR(100),
    irrigation_method VARCHAR(100),
    farm_area NUMERIC(12,2),
    expected_harvest_date DATE,
    status VARCHAR(30) NOT NULL DEFAULT 'Growing',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


# ============================================================
# DATABASE HELPERS
# ============================================================

def ensure_crop_table():

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(CROP_TABLE_SQL)

        conn.commit()

        # ----------------------------------------------------
        # Add missing columns to older installations
        # ----------------------------------------------------

        columns = [
            (
                "expected_harvest_date",
                """
                ALTER TABLE crops
                ADD COLUMN expected_harvest_date DATE
                """
            ),
            (
                "status",
                """
                ALTER TABLE crops
                ADD COLUMN status VARCHAR(30)
                DEFAULT 'Growing'
                """
            ),
            (
                "updated_at",
                """
                ALTER TABLE crops
                ADD COLUMN updated_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
                """
            ),
        ]

        for column_name, alter_sql in columns:

            try:

                cursor.execute(
                    f"""
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'crops'
                    AND column_name = %s
                    """,
                    (column_name,),
                )

                exists = cursor.fetchone()

                if not exists:

                    cursor.execute(
                        alter_sql
                    )

            except Exception as exc:

                print(
                    f"Crop column check error "
                    f"({column_name}):",
                    exc
                )

        conn.commit()

    except Exception as exc:

        if conn:
            conn.rollback()

        print(
            "Crop table initialization error:",
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


# ============================================================
# CURSOR ROW HELPER
# ============================================================

def row_to_dict(cursor, row):

    if row is None:
        return None

    if isinstance(row, dict):
        return dict(row)

    columns = []

    try:
        columns = [
            column[0]
            for column in cursor.description
        ]
    except Exception:
        pass

    return dict(
        zip(columns, row)
    )


# ============================================================
# FARMER ACCESS
# ============================================================

def farmer_required():

    if not session.get("user_id"):

        return redirect(
            url_for("login")
        )

    role = str(
        session.get(
            "role",
            ""
        )
    ).strip().lower()

    if role != "farmer":

        flash(
            "Only farmers can manage crop details.",
            "warning"
        )

        return redirect(
            url_for("farmer")
        )

    return None


# ============================================================
# DATE PARSER
# ============================================================

def parse_date(value):

    if not value:
        return None

    try:

        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()

    except (
        ValueError,
        TypeError
    ):

        return None


# ============================================================
# GROWTH STAGE
# ============================================================

def get_growth_stage(
    age_days,
    duration_days
):

    try:

        age_days = max(
            int(age_days),
            0
        )

        duration_days = max(
            int(duration_days),
            1
        )

    except (
        ValueError,
        TypeError
    ):

        return "Germination"

    progress = (
        age_days / duration_days
    ) * 100

    if progress < 10:

        return "Germination"

    elif progress < 25:

        return "Seedling"

    elif progress < 50:

        return "Vegetative Growth"

    elif progress < 70:

        return "Flowering"

    elif progress < 90:

        return "Fruit/Grain Development"

    elif progress < 100:

        return "Maturity"

    return "Harvest Ready"


# ============================================================
# CROP STATUS
# ============================================================

def get_crop_status(
    age_days,
    duration_days
):

    try:

        age_days = int(age_days)
        duration_days = max(
            int(duration_days),
            1
        )

    except (
        ValueError,
        TypeError
    ):

        return "Growing"

    if age_days < 0:

        return "Planned"

    if age_days >= duration_days:

        return "Harvest Ready"

    return "Growing"


# ============================================================
# PROGRESS
# ============================================================

def calculate_progress(
    age_days,
    duration_days
):

    try:

        age_days = max(
            int(age_days),
            0
        )

        duration_days = max(
            int(duration_days),
            1
        )

        progress = (
            age_days /
            duration_days
        ) * 100

        return round(
            min(progress, 100),
            1
        )

    except (
        ValueError,
        TypeError
    ):

        return 0


# ============================================================
# CROP INTELLIGENCE
# ============================================================

def crop_intelligence(
    crop,
    age_days,
    duration_days,
    progress
):

    stage = get_growth_stage(
        age_days,
        duration_days
    )

    status = get_crop_status(
        age_days,
        duration_days
    )

    insights = []

    actions = []

    # --------------------------------------------------------
    # PLANNED
    # --------------------------------------------------------

    if age_days < 0:

        insights.append(
            "Sowing date is in the future."
        )

        actions.append(
            "Prepare seed, soil and irrigation plan."
        )

    # --------------------------------------------------------
    # GERMINATION
    # --------------------------------------------------------

    elif stage == "Germination":

        insights.append(
            "Early crop establishment stage."
        )

        actions.append(
            "Maintain suitable soil moisture."
        )

    # --------------------------------------------------------
    # SEEDLING
    # --------------------------------------------------------

    elif stage == "Seedling":

        insights.append(
            "Seedlings are developing."
        )

        actions.append(
            "Monitor weeds, pests and soil moisture."
        )

    # --------------------------------------------------------
    # VEGETATIVE
    # --------------------------------------------------------

    elif stage == "Vegetative Growth":

        insights.append(
            "Vegetative growth is active."
        )

        actions.append(
            "Monitor nutrition and irrigation requirements."
        )

    # --------------------------------------------------------
    # FLOWERING
    # --------------------------------------------------------

    elif stage == "Flowering":

        insights.append(
            "Crop is entering the flowering stage."
        )

        actions.append(
            "Monitor weather and crop stress closely."
        )

    # --------------------------------------------------------
    # FRUIT / GRAIN
    # --------------------------------------------------------

    elif stage == "Fruit/Grain Development":

        insights.append(
            "Fruit or grain development is underway."
        )

        actions.append(
            "Monitor crop health and water availability."
        )

    # --------------------------------------------------------
    # MATURITY
    # --------------------------------------------------------

    elif stage == "Maturity":

        insights.append(
            "Crop is approaching harvest."
        )

        actions.append(
            "Start harvest and market planning."
        )

    # --------------------------------------------------------
    # HARVEST
    # --------------------------------------------------------

    elif stage == "Harvest Ready":

        insights.append(
            "Expected crop duration has been reached."
        )

        actions.append(
            "Check crop maturity before harvesting."
        )

    # --------------------------------------------------------
    # GENERAL
    # --------------------------------------------------------

    if progress >= 80:

        actions.append(
            "Review current Mandi prices before harvest."
        )

    if progress >= 90:

        actions.append(
            "Prepare storage and marketplace plans."
        )

    return {

        "stage": stage,

        "status": status,

        "progress": progress,

        "insights": insights,

        "actions": actions,
    }


# ============================================================
# ENRICH CROP
# ============================================================

def enrich_crop(crop):

    if not crop:
        return None

    today = date.today()

    sowing_date = crop.get(
        "sowing_date"
    )

    duration_days = crop.get(
        "duration_days"
    ) or 1

    if isinstance(
        sowing_date,
        datetime
    ):

        sowing_date = (
            sowing_date.date()
        )

    elif isinstance(
        sowing_date,
        str
    ):

        sowing_date = parse_date(
            sowing_date
        )

    try:

        duration_days = int(
            duration_days
        )

    except (
        ValueError,
        TypeError
    ):

        duration_days = 1

    if sowing_date:

        age_days = (
            today - sowing_date
        ).days

        expected_harvest = (
            sowing_date
            + __import__(
                "datetime"
            ).timedelta(
                days=duration_days
            )
        )

    else:

        age_days = 0
        expected_harvest = None

    progress = calculate_progress(
        age_days,
        duration_days
    )

    intelligence = crop_intelligence(
        crop,
        age_days,
        duration_days,
        progress
    )

    crop["age_days"] = age_days

    crop["duration_days"] = duration_days

    crop["progress"] = progress

    crop["growth_stage"] = intelligence[
        "stage"
    ]

    crop["status"] = intelligence[
        "status"
    ]

    crop["expected_harvest_date"] = (
        expected_harvest
    )

    crop["remaining_days"] = max(
        duration_days - max(age_days, 0),
        0
    )

    crop["insights"] = intelligence[
        "insights"
    ]

    crop["actions"] = intelligence[
        "actions"
    ]

    return crop


# ============================================================
# FETCH FARMER CROPS
# ============================================================

def fetch_farmer_crops(
    farmer_id
):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                farmer_id,
                crop_name,
                sowing_date,
                duration_days,
                soil_type,
                irrigation_method,
                farm_area,
                expected_harvest_date,
                status,
                created_at,
                updated_at
            FROM crops
            WHERE farmer_id = %s
            ORDER BY
                CASE
                    WHEN status = 'Growing'
                    THEN 0
                    WHEN status = 'Planned'
                    THEN 1
                    ELSE 2
                END,
                sowing_date DESC
            """,
            (farmer_id,),
        )

        rows = cursor.fetchall()

        crops = []

        for row in rows:

            crop = row_to_dict(
                cursor,
                row
            )

            crop = enrich_crop(
                crop
            )

            crops.append(
                crop
            )

        return crops

    except Exception as exc:

        print(
            "Fetch crops error:",
            exc
        )

        return []

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
# CROP DETAILS PAGE
# ============================================================

@crop_bp.route(
    "/crop-details",
    methods=["GET", "POST"]
)
def crop_details():

    access = farmer_required()

    if access:
        return access

    ensure_crop_table()

    farmer_id = session.get(
        "user_id"
    )

    if request.method == "POST":

        crop_name = str(
            request.form.get(
                "crop_name",
                ""
            )
        ).strip()

        sowing_date = parse_date(
            request.form.get(
                "sowing_date"
            )
        )

        duration_raw = request.form.get(
            "duration_days",
            "120"
        )

        soil_type = str(
            request.form.get(
                "soil_type",
                ""
            )
        ).strip()

        irrigation_method = str(
            request.form.get(
                "irrigation_method",
                ""
            )
        ).strip()

        farm_area_raw = request.form.get(
            "farm_area",
            ""
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not crop_name:

            flash(
                "Please enter crop name.",
                "danger"
            )

            return redirect(
                url_for(
                    "crop.crop_details"
                )
            )

        if not sowing_date:

            flash(
                "Please enter a valid sowing date.",
                "danger"
            )

            return redirect(
                url_for(
                    "crop.crop_details"
                )
            )

        try:

            duration_days = int(
                duration_raw
            )

            if duration_days <= 0:
                raise ValueError

            if duration_days > 1000:
                raise ValueError

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Crop duration must be between 1 and 1000 days.",
                "danger"
            )

            return redirect(
                url_for(
                    "crop.crop_details"
                )
            )

        farm_area = None

        if farm_area_raw:

            try:

                farm_area = float(
                    farm_area_raw
                )

                if farm_area < 0:
                    raise ValueError

            except (
                ValueError,
                TypeError
            ):

                flash(
                    "Please enter a valid farm area.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "crop.crop_details"
                    )
                )

        expected_harvest = (
            sowing_date
            + __import__(
                "datetime"
            ).timedelta(
                days=duration_days
            )
        )

        today = date.today()

        age_days = (
            today - sowing_date
        ).days

        status = get_crop_status(
            age_days,
            duration_days
        )

        conn = None
        cursor = None

        try:

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO crops (
                    farmer_id,
                    crop_name,
                    sowing_date,
                    duration_days,
                    soil_type,
                    irrigation_method,
                    farm_area,
                    expected_harvest_date,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                RETURNING id
                """,
                (
                    farmer_id,
                    crop_name,
                    sowing_date,
                    duration_days,
                    soil_type or None,
                    irrigation_method or None,
                    farm_area,
                    expected_harvest,
                    status,
                ),
            )

            new_crop = cursor.fetchone()

            conn.commit()

            crop_id = (
                new_crop[0]
                if new_crop
                else None
            )

            flash(
                "Crop details saved successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "crop.crop_details"
                )
            )

        except Exception as exc:

            if conn:
                conn.rollback()

            print(
                "Crop save error:",
                exc
            )

            flash(
                "Unable to save crop details.",
                "danger"
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

    crops = fetch_farmer_crops(
        farmer_id
    )

    return render_template(
        "crop_details.html",

        crops=crops,

        name=session.get(
            "name",
            "Farmer"
        ),

        language=session.get(
            "language",
            "en"
        ),

        role=session.get(
            "role",
            "farmer"
        ),
    )


# ============================================================
# CROP LIST API
# ============================================================

@crop_bp.route(
    "/api/crops"
)
def crops_api():

    access = farmer_required()

    if access:

        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    ensure_crop_table()

    crops = fetch_farmer_crops(
        session.get("user_id")
    )

    return jsonify({

        "success": True,

        "count": len(crops),

        "crops": crops,
    })


# ============================================================
# SINGLE CROP API
# ============================================================

@crop_bp.route(
    "/api/crops/<int:crop_id>"
)
def crop_api(crop_id):

    access = farmer_required()

    if access:

        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    ensure_crop_table()

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                farmer_id,
                crop_name,
                sowing_date,
                duration_days,
                soil_type,
                irrigation_method,
                farm_area,
                expected_harvest_date,
                status,
                created_at,
                updated_at
            FROM crops
            WHERE id = %s
            AND farmer_id = %s
            LIMIT 1
            """,
            (
                crop_id,
                session.get("user_id"),
            ),
        )

        row = cursor.fetchone()

        if not row:

            return jsonify({
                "success": False,
                "message": "Crop not found."
            }), 404

        crop = row_to_dict(
            cursor,
            row
        )

        crop = enrich_crop(
            crop
        )

        return jsonify({

            "success": True,

            "crop": crop,
        })

    except Exception as exc:

        print(
            "Single crop API error:",
            exc
        )

        return jsonify({
            "success": False,
            "message": "Unable to load crop."
        }), 500

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
# UPDATE CROP
# ============================================================

@crop_bp.route(
    "/api/crops/<int:crop_id>",
    methods=["PUT", "POST"]
)
def update_crop(crop_id):

    access = farmer_required()

    if access:

        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    # Allow form-data too
    if not data:

        data = request.form.to_dict()

    crop_name = str(
        data.get(
            "crop_name",
            ""
        )
    ).strip()

    sowing_date = parse_date(
        data.get(
            "sowing_date"
        )
    )

    duration_raw = data.get(
        "duration_days"
    )

    soil_type = str(
        data.get(
            "soil_type",
            ""
        )
    ).strip()

    irrigation_method = str(
        data.get(
            "irrigation_method",
            ""
        )
    ).strip()

    farm_area_raw = data.get(
        "farm_area"
    )

    if not crop_name:

        return jsonify({
            "success": False,
            "message": "Crop name is required."
        }), 400

    if not sowing_date:

        return jsonify({
            "success": False,
            "message": "Valid sowing date is required."
        }), 400

    try:

        duration_days = int(
            duration_raw
        )

        if not 1 <= duration_days <= 1000:

            raise ValueError

    except (
        ValueError,
        TypeError
    ):

        return jsonify({
            "success": False,
            "message": "Invalid crop duration."
        }), 400

    farm_area = None

    if farm_area_raw not in (
        None,
        ""
    ):

        try:

            farm_area = float(
                farm_area_raw
            )

            if farm_area < 0:
                raise ValueError

        except (
            ValueError,
            TypeError
        ):

            return jsonify({
                "success": False,
                "message": "Invalid farm area."
            }), 400

    expected_harvest = (
        sowing_date
        + __import__(
            "datetime"
        ).timedelta(
            days=duration_days
        )
    )

    age_days = (
        date.today()
        - sowing_date
    ).days

    status = get_crop_status(
        age_days,
        duration_days
    )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE crops
            SET
                crop_name = %s,
                sowing_date = %s,
                duration_days = %s,
                soil_type = %s,
                irrigation_method = %s,
                farm_area = %s,
                expected_harvest_date = %s,
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            AND farmer_id = %s
            """,
            (
                crop_name,
                sowing_date,
                duration_days,
                soil_type or None,
                irrigation_method or None,
                farm_area,
                expected_harvest,
                status,
                crop_id,
                session.get("user_id"),
            ),
        )

        if cursor.rowcount == 0:

            conn.rollback()

            return jsonify({
                "success": False,
                "message": "Crop not found."
            }), 404

        conn.commit()

        return jsonify({

            "success": True,

            "message": "Crop updated successfully.",
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        print(
            "Crop update error:",
            exc
        )

        return jsonify({
            "success": False,
            "message": "Unable to update crop."
        }), 500

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
# DELETE CROP
# ============================================================

@crop_bp.route(
    "/api/crops/<int:crop_id>",
    methods=["DELETE"]
)
def delete_crop(crop_id):

    access = farmer_required()

    if access:

        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM crops
            WHERE id = %s
            AND farmer_id = %s
            """,
            (
                crop_id,
                session.get("user_id"),
            ),
        )

        if cursor.rowcount == 0:

            conn.rollback()

            return jsonify({
                "success": False,
                "message": "Crop not found."
            }), 404

        conn.commit()

        return jsonify({

            "success": True,

            "message": "Crop deleted successfully.",
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        print(
            "Crop delete error:",
            exc
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete crop."
        }), 500

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
# CROP INTELLIGENCE API
# ============================================================

@crop_bp.route(
    "/api/crops/<int:crop_id>/intelligence"
)
def crop_intelligence_api(crop_id):

    access = farmer_required()

    if access:

        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    ensure_crop_table()

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                farmer_id,
                crop_name,
                sowing_date,
                duration_days,
                soil_type,
                irrigation_method,
                farm_area,
                expected_harvest_date,
                status,
                created_at,
                updated_at
            FROM crops
            WHERE id = %s
            AND farmer_id = %s
            LIMIT 1
            """,
            (
                crop_id,
                session.get("user_id"),
            ),
        )

        row = cursor.fetchone()

        if not row:

            return jsonify({
                "success": False,
                "message": "Crop not found."
            }), 404

        crop = row_to_dict(
            cursor,
            row
        )

        crop = enrich_crop(
            crop
        )

        return jsonify({

            "success": True,

            "crop_id": crop_id,

            "crop_name": crop.get(
                "crop_name"
            ),

            "growth_stage": crop.get(
                "growth_stage"
            ),

            "progress": crop.get(
                "progress"
            ),

            "age_days": crop.get(
                "age_days"
            ),

            "remaining_days": crop.get(
                "remaining_days"
            ),

            "expected_harvest_date": (
                crop.get(
                    "expected_harvest_date"
                )
            ),

            "status": crop.get(
                "status"
            ),

            "insights": crop.get(
                "insights",
                []
            ),

            "actions": crop.get(
                "actions",
                []
            ),

            "connected_modules": {

                "weather": True,

                "crop_advisor": True,

                "irrigation": True,

                "disease_detection": True,

                "market": True,

                "notifications": True,
            },
        })

    except Exception as exc:

        print(
            "Crop intelligence error:",
            exc
        )

        return jsonify({
            "success": False,
            "message": "Unable to generate crop intelligence."
        }), 500

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
# CROP MODULE HEALTH
# ============================================================

@crop_bp.route(
    "/api/crops/health"
)
def crop_health():

    return jsonify({

        "success": True,

        "module": "crop",

        "status": "ready",

        "database": "PostgreSQL",

        "application": "KisanVision360+",

        "features": [

            "Crop registration",

            "Growth stage tracking",

            "Harvest estimation",

            "Progress calculation",

            "Crop intelligence",

            "Farmer-specific crop isolation",

            "Weather integration ready",

            "Irrigation integration ready",

            "Disease integration ready",

            "Market integration ready",

            "Notification integration ready",
        ],
    })
