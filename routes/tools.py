# ============================================================
# KISANVISION360+ - FARMER TOOLS ROUTE
# ============================================================
# Farmer Utility Tools
#
# Features:
# - Tools dashboard
# - Crop profit calculator
# - Seed calculator
# - Fertilizer calculator
# - Water requirement calculator
# - Land-area conversion
# - Yield calculator
# - Break-even calculator
# - ROI calculator
# - Tool history
# - PostgreSQL / Supabase compatible
# ============================================================

from flask import (
    Blueprint,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    session,
)

from database.db import get_db_connection

from datetime import datetime


# ============================================================
# BLUEPRINT
# ============================================================

tools_bp = Blueprint("tools", __name__)


# ============================================================
# CONSTANTS
# ============================================================

ACRE_TO_SQFT = 43560.0
HECTARE_TO_ACRE = 2.47105
SQM_TO_SQFT = 10.7639
SQFT_TO_SQM = 0.092903


# ============================================================
# AUTH
# ============================================================

def is_logged_in():
    return bool(session.get("user_id"))


def is_farmer():
    return (
        str(
            session.get("role", "")
        ).strip().lower()
        == "farmer"
    )


def current_user_id():
    return session.get("user_id")


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default

        return int(value)

    except (TypeError, ValueError):
        return default


def positive(value):
    return max(0.0, safe_float(value))


def round2(value):
    return round(
        safe_float(value),
        2,
    )


def table_exists(cursor, table_name):
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


def get_columns(cursor, table_name):
    try:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            """,
            (table_name,),
        )

        rows = cursor.fetchall()

        result = set()

        for row in rows:
            if isinstance(row, dict):
                result.add(row["column_name"])
            else:
                result.add(row[0])

        return result

    except Exception:
        return set()


def safe_close(cursor=None, conn=None):

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
# HISTORY TABLE
# ============================================================

def ensure_tool_history_table():
    """
    Creates tool_history if it does not already exist.
    """

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_history (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                tool_name VARCHAR(100) NOT NULL,
                input_data JSONB,
                result_data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_tool_history_user
            ON tool_history(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_tool_history_created
            ON tool_history(created_at DESC)
            """
        )

        conn.commit()

        return True

    except Exception as exc:

        if conn:
            conn.rollback()

        print(
            "Tool history table error:",
            exc,
        )

        return False

    finally:
        safe_close(
            cursor,
            conn,
        )


# ============================================================
# SAVE TOOL HISTORY
# ============================================================

def save_tool_history(
    tool_name,
    input_data,
    result_data,
):
    """
    Save calculation history.
    """

    if not current_user_id():
        return False

    conn = None
    cursor = None

    try:

        ensure_tool_history_table()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tool_history (
                user_id,
                tool_name,
                input_data,
                result_data
            )
            VALUES (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                current_user_id(),
                tool_name,
                __import__("json").dumps(
                    input_data
                ),
                __import__("json").dumps(
                    result_data
                ),
            ),
        )

        conn.commit()

        return True

    except Exception as exc:

        if conn:
            conn.rollback()

        print(
            "Tool history save error:",
            exc,
        )

        return False

    finally:
        safe_close(
            cursor,
            conn,
        )


# ============================================================
# AREA CONVERTER
# ============================================================

def convert_area(
    value,
    from_unit,
):
    """
    Convert area into acres, hectares,
    square feet and square metres.
    """

    value = positive(value)

    unit = str(
        from_unit or "acre"
    ).strip().lower()

    acres = 0.0

    if unit in {
        "acre",
        "acres",
    }:
        acres = value

    elif unit in {
        "hectare",
        "hectares",
        "ha",
    }:
        acres = (
            value
            * HECTARE_TO_ACRE
        )

    elif unit in {
        "sqft",
        "square_feet",
        "square feet",
    }:
        acres = (
            value
            / ACRE_TO_SQFT
        )

    elif unit in {
        "sqm",
        "square_metre",
        "square_meter",
        "square metres",
        "square meters",
    }:
        acres = (
            value
            * SQM_TO_SQFT
            / ACRE_TO_SQFT
        )

    elif unit in {
        "guntha",
        "guntha",
    }:
        # Common Maharashtra conversion:
        # 40 guntha = 1 acre
        acres = value / 40.0

    elif unit in {
        "bigha",
        "bigha",
    }:
        # Bigha differs by region.
        # Use approximate configurable value.
        acres = value * 0.625

    else:
        acres = value

    return {
        "acres": round2(acres),
        "hectares": round2(
            acres / HECTARE_TO_ACRE
        ),
        "square_feet": round2(
            acres * ACRE_TO_SQFT
        ),
        "square_metres": round2(
            acres * ACRE_TO_SQFT
            * SQFT_TO_SQM
        ),
        "guntha": round2(
            acres * 40
        ),
    }


# ============================================================
# PROFIT CALCULATOR
# ============================================================

def calculate_profit(data):

    expected_yield = positive(
        data.get("expected_yield")
    )

    yield_unit_price = positive(
        data.get("selling_price")
    )

    seed_cost = positive(
        data.get("seed_cost")
    )

    fertilizer_cost = positive(
        data.get("fertilizer_cost")
    )

    pesticide_cost = positive(
        data.get("pesticide_cost")
    )

    irrigation_cost = positive(
        data.get("irrigation_cost")
    )

    labor_cost = positive(
        data.get("labor_cost")
    )

    machinery_cost = positive(
        data.get("machinery_cost")
    )

    other_cost = positive(
        data.get("other_cost")
    )

    total_cost = (
        seed_cost
        + fertilizer_cost
        + pesticide_cost
        + irrigation_cost
        + labor_cost
        + machinery_cost
        + other_cost
    )

    revenue = (
        expected_yield
        * yield_unit_price
    )

    profit = revenue - total_cost

    roi = (
        (profit / total_cost) * 100
        if total_cost > 0
        else 0
    )

    break_even_quantity = (
        total_cost / yield_unit_price
        if yield_unit_price > 0
        else 0
    )

    return {
        "expected_yield": round2(
            expected_yield
        ),
        "selling_price": round2(
            yield_unit_price
        ),
        "total_cost": round2(
            total_cost
        ),
        "revenue": round2(
            revenue
        ),
        "profit": round2(
            profit
        ),
        "roi_percent": round2(
            roi
        ),
        "break_even_quantity": round2(
            break_even_quantity
        ),
        "status": (
            "Profitable"
            if profit > 0
            else
            "Break-even"
            if profit == 0
            else
            "Loss"
        ),
    }


# ============================================================
# SEED CALCULATOR
# ============================================================

def calculate_seed(data):

    area_acres = positive(
        data.get("area_acres")
    )

    seed_rate = positive(
        data.get("seed_rate")
    )

    germination = positive(
        data.get(
            "germination",
            100,
        )
    )

    purity = positive(
        data.get(
            "purity",
            100,
        )
    )

    if germination <= 0:
        germination = 100

    if purity <= 0:
        purity = 100

    base_seed = (
        area_acres
        * seed_rate
    )

    adjusted_seed = (
        base_seed
        * (100 / germination)
        * (100 / purity)
    )

    return {
        "area_acres": round2(
            area_acres
        ),
        "seed_rate": round2(
            seed_rate
        ),
        "germination": round2(
            germination
        ),
        "purity": round2(
            purity
        ),
        "base_seed_kg": round2(
            base_seed
        ),
        "recommended_seed_kg": round2(
            adjusted_seed
        ),
    }


# ============================================================
# FERTILIZER CALCULATOR
# ============================================================

def calculate_fertilizer(data):

    area_acres = positive(
        data.get("area_acres")
    )

    nitrogen = positive(
        data.get("nitrogen")
    )

    phosphorus = positive(
        data.get("phosphorus")
    )

    potassium = positive(
        data.get("potassium")
    )

    # Approximate nutrient-to-fertilizer conversion.
    # These are generic planning estimates.
    urea = nitrogen / 0.46
    dap = phosphorus / 0.46
    mop = potassium / 0.60

    return {
        "area_acres": round2(
            area_acres
        ),

        "nitrogen_kg": round2(
            nitrogen
            * area_acres
        ),

        "phosphorus_kg": round2(
            phosphorus
            * area_acres
        ),

        "potassium_kg": round2(
            potassium
            * area_acres
        ),

        "estimated_urea_kg": round2(
            urea
            * area_acres
        ),

        "estimated_dap_kg": round2(
            dap
            * area_acres
        ),

        "estimated_mop_kg": round2(
            mop
            * area_acres
        ),

        "note": (
            "Planning estimate only. "
            "Use soil-test recommendations "
            "before final fertilizer application."
        ),
    }


# ============================================================
# WATER CALCULATOR
# ============================================================

def calculate_water(data):

    area_acres = positive(
        data.get("area_acres")
    )

    water_mm = positive(
        data.get("water_mm")
    )

    efficiency = positive(
        data.get(
            "efficiency",
            70,
        )
    )

    if efficiency <= 0:
        efficiency = 70

    if efficiency > 100:
        efficiency = 100

    # 1 mm over 1 acre â‰ˆ 4046.86 litres.
    base_litres = (
        area_acres
        * water_mm
        * 4046.86
    )

    required_litres = (
        base_litres
        / (efficiency / 100)
    )

    return {
        "area_acres": round2(
            area_acres
        ),
        "water_depth_mm": round2(
            water_mm
        ),
        "efficiency_percent": round2(
            efficiency
        ),
        "base_water_litres": round2(
            base_litres
        ),
        "estimated_water_litres": round2(
            required_litres
        ),
        "estimated_water_cubic_metre": round2(
            required_litres / 1000
        ),
    }


# ============================================================
# YIELD CALCULATOR
# ============================================================

def calculate_yield(data):

    area_acres = positive(
        data.get("area_acres")
    )

    yield_per_acre = positive(
        data.get("yield_per_acre")
    )

    total_yield = (
        area_acres
        * yield_per_acre
    )

    return {
        "area_acres": round2(
            area_acres
        ),
        "yield_per_acre": round2(
            yield_per_acre
        ),
        "estimated_total_yield": round2(
            total_yield
        ),
    }


# ============================================================
# ROI CALCULATOR
# ============================================================

def calculate_roi(data):

    investment = positive(
        data.get("investment")
    )

    return_value = positive(
        data.get("return_value")
    )

    profit = (
        return_value
        - investment
    )

    roi = (
        profit
        / investment
        * 100
        if investment > 0
        else 0
    )

    return {
        "investment": round2(
            investment
        ),
        "return_value": round2(
            return_value
        ),
        "profit": round2(
            profit
        ),
        "roi_percent": round2(
            roi
        ),
    }


# ============================================================
# BREAK EVEN CALCULATOR
# ============================================================

def calculate_break_even(data):

    fixed_cost = positive(
        data.get("fixed_cost")
    )

    variable_cost = positive(
        data.get("variable_cost")
    )

    selling_price = positive(
        data.get("selling_price")
    )

    contribution = (
        selling_price
        - variable_cost
    )

    break_even_quantity = (
        fixed_cost / contribution
        if contribution > 0
        else 0
    )

    return {
        "fixed_cost": round2(
            fixed_cost
        ),
        "variable_cost_per_unit": round2(
            variable_cost
        ),
        "selling_price_per_unit": round2(
            selling_price
        ),
        "contribution_per_unit": round2(
            contribution
        ),
        "break_even_quantity": round2(
            break_even_quantity
        ),
        "status": (
            "Calculable"
            if contribution > 0
            else
            "Selling price must exceed variable cost"
        ),
    }


# ============================================================
# TOOLS PAGE
# ============================================================

@tools_bp.route(
    "/tools",
    methods=["GET"],
)
def tools():

    if not is_logged_in():
        return redirect(
            url_for("auth.login")
        )

    if not is_farmer():
        return redirect(
            url_for("farmer.farmer")
        )

    return render_template(
        "tools.html",
        language=session.get(
            "language",
            "en",
        ),
        role=session.get(
            "role",
            "farmer",
        ),
    )


# ============================================================
# AREA API
# ============================================================

@tools_bp.route(
    "/api/tools/area",
    methods=["POST"],
)
def area_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    result = convert_area(
        data.get("value"),
        data.get("unit"),
    )

    save_tool_history(
        "area_converter",
        data,
        result,
    )

    return jsonify({
        "success": True,
        "result": result,
    })


# ============================================================
# PROFIT API
# ============================================================

@tools_bp.route(
    "/api/tools/profit",
    methods=["POST"],
)
def profit_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    result = calculate_profit(
        data
    )

    save_tool_history(
        "profit_calculator",
        data,
        result,
    )

    return jsonify({
        "success": True,
        "result": result,
    })


# ============================================================
# SEED API
# ============================================================

@tools_bp.route(
    "/api/tools/seed",
    methods=["POST"],
)
def seed_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    result = calculate_seed(
        data
    )

    save_tool_history(
        "seed_calculator",
        data,
        result,
    )

    return jsonify({
        "success": True,
        "result": result,
    })


# ============================================================
# FERTILIZER API
# ============================================================

@tools_bp.route(
    "/api/tools/fertilizer",
    methods=["POST"],
)
def fertilizer_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    result = calculate_fertilizer(
        data
    )

    save_tool_history(
        "fertilizer_calculator",
        data,
        result,
    )

    return jsonify({
        "success": True,
        "result": result,
    })


# ============================================================
# WATER API
# ============================================================

@tools_bp.route(
    "/api/tools/water",
    methods=["POST"],
)
def water_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    result = calculate_water(
        data
    )

    save_tool_history(
        "water_calculator",
        data,
        result,
    )

    return jsonify({
        "success": True,
        "result": result,
    })


# ============================================================
# YIELD API
# ============================================================

@tools_bp.route(
    "/api/tools/yield",
    methods=["POST"],
)
def yield_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    result = calculate_yield(
        data
    )

    save_tool_history(
        "yield_calculator",
        data,
        result,
    )

    return jsonify({
        "success": True,
        "result": result,
    })


# ============================================================
# ROI API
# ============================================================

@tools_bp.route(
    "/api/tools/roi",
    methods=["POST"],
)
def roi_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    result = calculate_roi(
        data
    )

    save_tool_history(
        "roi_calculator",
        data,
        result,
    )

    return jsonify({
        "success": True,
        "result": result,
    })


# ============================================================
# BREAK EVEN API
# ============================================================

@tools_bp.route(
    "/api/tools/break-even",
    methods=["POST"],
)
def break_even_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    result = calculate_break_even(
        data
    )

    save_tool_history(
        "break_even_calculator",
        data,
        result,
    )

    return jsonify({
        "success": True,
        "result": result,
    })


# ============================================================
# TOOL HISTORY
# ============================================================

@tools_bp.route(
    "/api/tools/history",
    methods=["GET"],
)
def tool_history():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    conn = None
    cursor = None

    try:

        ensure_tool_history_table()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                tool_name,
                input_data,
                result_data,
                created_at
            FROM tool_history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (
                current_user_id(),
            ),
        )

        rows = cursor.fetchall()

        history = []

        for row in rows:

            if isinstance(row, dict):

                item = dict(row)

            else:

                item = {
                    "id": row[0],
                    "tool_name": row[1],
                    "input_data": row[2],
                    "result_data": row[3],
                    "created_at": row[4],
                }

            if isinstance(
                item.get("created_at"),
                datetime,
            ):
                item["created_at"] = (
                    item[
                        "created_at"
                    ].isoformat()
                )

            history.append(item)

        return jsonify({
            "success": True,
            "count": len(history),
            "history": history,
        })

    except Exception as exc:

        print(
            "Tool history read error:",
            exc,
        )

        return jsonify({
            "success": False,
            "message": "Unable to read tool history",
        }), 500

    finally:
        safe_close(
            cursor,
            conn,
        )


# ============================================================
# DELETE HISTORY
# ============================================================

@tools_bp.route(
    "/api/tools/history/<int:history_id>",
    methods=["DELETE"],
)
def delete_history(history_id):

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM tool_history
            WHERE id = %s
              AND user_id = %s
            """,
            (
                history_id,
                current_user_id(),
            ),
        )

        deleted = cursor.rowcount

        conn.commit()

        if deleted == 0:

            return jsonify({
                "success": False,
                "message": "History record not found",
            }), 404

        return jsonify({
            "success": True,
            "message": "History deleted",
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        print(
            "Tool history delete error:",
            exc,
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete history",
        }), 500

    finally:
        safe_close(
            cursor,
            conn,
        )


# ============================================================
# DELETE ALL HISTORY
# ============================================================

@tools_bp.route(
    "/api/tools/history",
    methods=["DELETE"],
)
def delete_all_history():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM tool_history
            WHERE user_id = %s
            """,
            (
                current_user_id(),
            ),
        )

        deleted = cursor.rowcount

        conn.commit()

        return jsonify({
            "success": True,
            "deleted": deleted,
            "message": "Tool history cleared",
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        print(
            "Tool history clear error:",
            exc,
        )

        return jsonify({
            "success": False,
            "message": "Unable to clear history",
        }), 500

    finally:
        safe_close(
            cursor,
            conn,
        )


# ============================================================
# AVAILABLE TOOLS API
# ============================================================

@tools_bp.route(
    "/api/tools",
    methods=["GET"],
)
def available_tools():

    return jsonify({
        "success": True,
        "tools": [
            {
                "id": "profit",
                "name": "Profit Calculator",
                "endpoint": "/api/tools/profit",
            },
            {
                "id": "seed",
                "name": "Seed Calculator",
                "endpoint": "/api/tools/seed",
            },
            {
                "id": "fertilizer",
                "name": "Fertilizer Calculator",
                "endpoint": "/api/tools/fertilizer",
            },
            {
                "id": "water",
                "name": "Water Calculator",
                "endpoint": "/api/tools/water",
            },
            {
                "id": "yield",
                "name": "Yield Calculator",
                "endpoint": "/api/tools/yield",
            },
            {
                "id": "roi",
                "name": "ROI Calculator",
                "endpoint": "/api/tools/roi",
            },
            {
                "id": "break_even",
                "name": "Break-even Calculator",
                "endpoint": "/api/tools/break-even",
            },
            {
                "id": "area",
                "name": "Land Area Converter",
                "endpoint": "/api/tools/area",
            },
        ],
    })


# ============================================================
# HEALTH
# ============================================================

@tools_bp.route(
    "/api/tools/health",
    methods=["GET"],
)
def tools_health():

    database_ok = False
    error = None

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

        error = str(exc)

    finally:

        safe_close(
            cursor,
            conn,
        )

    return jsonify({
        "success": database_ok,
        "service": "farmer_tools",
        "database": database_ok,
        "postgresql": True,
        "supabase_compatible": True,
        "error": error,
    }), (
        200
        if database_ok
        else 503
    )


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_tools_service(app=None):

    if app:
        app.logger.info(
            "KisanVision360+ Farmer Tools service initialized."
        )

    return True
