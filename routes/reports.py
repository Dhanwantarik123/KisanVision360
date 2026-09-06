# ============================================================
# KISANVISION360+ - REPORTS ROUTE
# ============================================================
# Farmer Reports & Analytics
#
# Features:
# - Farmer report dashboard
# - Farm overview
# - Crop summary
# - Finance summary
# - Marketplace summary
# - Orders summary
# - Monthly analytics
# - Crop performance
# - Expense/income analysis
# - Report API
# - JSON export-ready API
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

reports_bp = Blueprint("reports", __name__)


# ============================================================
# AUTHENTICATION
# ============================================================

def is_logged_in():
    return bool(session.get("user_id"))


def is_farmer():
    role = str(
        session.get("role", "")
    ).strip().lower()

    return role == "farmer"


def current_user_id():
    return session.get("user_id")


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_connection():
    return get_db_connection()


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


def get_columns(cursor, table_name):
    """
    Return available columns of a PostgreSQL table.
    """

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

        columns = set()

        for row in rows:
            if isinstance(row, dict):
                columns.add(row["column_name"])
            else:
                columns.add(row[0])

        return columns

    except Exception:
        return set()


def row_to_dict(cursor, row):
    """
    Convert tuple or dict database result into dict.
    """

    if row is None:
        return {}

    if isinstance(row, dict):
        return dict(row)

    columns = [
        description[0]
        for description in cursor.description
    ]

    return dict(zip(columns, row))


def clean_value(value):
    """
    Convert PostgreSQL values into JSON-safe values.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.isoformat()

    try:
        # Decimal
        if hasattr(value, "as_tuple"):
            return float(value)
    except Exception:
        pass

    return value


def clean_dict(data):
    return {
        key: clean_value(value)
        for key, value in data.items()
    }


# ============================================================
# FARMER PROFILE
# ============================================================

def get_farmer_profile(user_id):
    """
    Get farmer profile from users + farmer_profiles.
    """

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        user_data = {}

        if table_exists(cursor, "users"):

            user_columns = get_columns(
                cursor,
                "users",
            )

            columns = [
                c
                for c in [
                    "id",
                    "name",
                    "email",
                    "mobile",
                    "location",
                    "role",
                    "preferred_language",
                ]
                if c in user_columns
            ]

            if "id" in columns:

                cursor.execute(
                    f"""
                    SELECT {", ".join(columns)}
                    FROM users
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )

                row = cursor.fetchone()

                if row:
                    user_data = row_to_dict(
                        cursor,
                        row,
                    )

        profile_data = {}

        if table_exists(
            cursor,
            "farmer_profiles",
        ):

            profile_columns = get_columns(
                cursor,
                "farmer_profiles",
            )

            possible_columns = [
                "user_id",
                "farm_name",
                "farm_location",
                "latitude",
                "longitude",
                "land_area",
                "land_unit",
                "soil_type",
                "irrigation_type",
                "main_crop",
                "farming_type",
                "water_availability",
                "budget",
                "farming_goal",
                "village",
                "district",
                "state",
                "pincode",
            ]

            columns = [
                c
                for c in possible_columns
                if c in profile_columns
            ]

            if "user_id" in columns:

                cursor.execute(
                    f"""
                    SELECT {", ".join(columns)}
                    FROM farmer_profiles
                    WHERE user_id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )

                row = cursor.fetchone()

                if row:
                    profile_data = row_to_dict(
                        cursor,
                        row,
                    )

        result = {
            **user_data,
            **profile_data,
        }

        return clean_dict(result)

    except Exception as exc:

        print(
            "Reports farmer profile error:",
            exc,
        )

        return {}

    finally:
        safe_close(
            cursor,
            conn,
        )


# ============================================================
# CROP REPORT
# ============================================================

def get_crop_report(user_id):
    """
    Crop statistics for current farmer.
    """

    conn = None
    cursor = None

    result = {
        "total_crops": 0,
        "active_crops": 0,
        "harvested_crops": 0,
        "planned_crops": 0,
        "total_area": 0,
        "crops": [],
    }

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if not table_exists(cursor, "crops"):
            return result

        columns = get_columns(
            cursor,
            "crops",
        )

        if "user_id" not in columns:
            return result

        select_columns = [
            c
            for c in [
                "id",
                "user_id",
                "crop_name",
                "name",
                "crop",
                "area",
                "land_area",
                "area_acres",
                "soil_type",
                "sowing_date",
                "planting_date",
                "harvest_date",
                "expected_harvest",
                "status",
                "growth_stage",
                "progress",
                "expected_yield",
                "yield_quantity",
                "quantity",
                "created_at",
            ]
            if c in columns
        ]

        if not select_columns:
            return result

        cursor.execute(
            f"""
            SELECT {", ".join(select_columns)}
            FROM crops
            WHERE user_id = %s
            ORDER BY created_at DESC NULLS LAST
            """,
            (user_id,),
        )

        rows = cursor.fetchall()

        for row in rows:

            crop = row_to_dict(
                cursor,
                row,
            )

            crop = clean_dict(crop)

            result["crops"].append(crop)

        result["total_crops"] = len(
            result["crops"]
        )

        for crop in result["crops"]:

            status = str(
                crop.get("status", "")
            ).lower()

            if status in {
                "active",
                "growing",
                "cultivating",
                "cultivation",
            }:
                result["active_crops"] += 1

            elif status in {
                "harvested",
                "completed",
                "complete",
            }:
                result["harvested_crops"] += 1

            elif status in {
                "planned",
                "upcoming",
            }:
                result["planned_crops"] += 1

            area = (
                crop.get("area")
                or crop.get("land_area")
                or crop.get("area_acres")
                or 0
            )

            try:
                result["total_area"] += float(area)
            except Exception:
                pass

    except Exception as exc:

        print(
            "Reports crop error:",
            exc,
        )

    finally:
        safe_close(
            cursor,
            conn,
        )

    return result


# ============================================================
# FINANCE REPORT
# ============================================================

def get_finance_report(user_id):
    """
    Income and expense summary.
    """

    result = {
        "total_income": 0.0,
        "total_expense": 0.0,
        "profit": 0.0,
        "income_count": 0,
        "expense_count": 0,
        "income_categories": {},
        "expense_categories": {},
        "monthly": [],
    }

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # ----------------------------------------------------
        # INCOME
        # ----------------------------------------------------

        if table_exists(
            cursor,
            "farm_income",
        ):

            columns = get_columns(
                cursor,
                "farm_income",
            )

            if "user_id" in columns:

                amount_column = None

                for candidate in [
                    "amount",
                    "income",
                    "value",
                    "total",
                ]:
                    if candidate in columns:
                        amount_column = candidate
                        break

                category_column = (
                    "category"
                    if "category" in columns
                    else None
                )

                date_column = None

                for candidate in [
                    "income_date",
                    "date",
                    "created_at",
                ]:
                    if candidate in columns:
                        date_column = candidate
                        break

                if amount_column:

                    select_parts = [
                        f"{amount_column} AS amount"
                    ]

                    if category_column:
                        select_parts.append(
                            f"{category_column} AS category"
                        )

                    if date_column:
                        select_parts.append(
                            f"{date_column} AS record_date"
                        )

                    cursor.execute(
                        f"""
                        SELECT {", ".join(select_parts)}
                        FROM farm_income
                        WHERE user_id = %s
                        """,
                        (user_id,),
                    )

                    rows = cursor.fetchall()

                    for row in rows:

                        data = row_to_dict(
                            cursor,
                            row,
                        )

                        try:
                            amount = float(
                                data.get(
                                    "amount",
                                    0,
                                )
                                or 0
                            )
                        except Exception:
                            amount = 0

                        result[
                            "total_income"
                        ] += amount

                        result[
                            "income_count"
                        ] += 1

                        category = str(
                            data.get(
                                "category",
                                "Other",
                            )
                            or "Other"
                        )

                        result[
                            "income_categories"
                        ][category] = (
                            result[
                                "income_categories"
                            ].get(category, 0)
                            + amount
                        )

        # ----------------------------------------------------
        # EXPENSE
        # ----------------------------------------------------

        if table_exists(
            cursor,
            "farm_expenses",
        ):

            columns = get_columns(
                cursor,
                "farm_expenses",
            )

            if "user_id" in columns:

                amount_column = None

                for candidate in [
                    "amount",
                    "expense",
                    "value",
                    "total",
                ]:
                    if candidate in columns:
                        amount_column = candidate
                        break

                category_column = (
                    "category"
                    if "category" in columns
                    else None
                )

                if amount_column:

                    select_parts = [
                        f"{amount_column} AS amount"
                    ]

                    if category_column:
                        select_parts.append(
                            f"{category_column} AS category"
                        )

                    cursor.execute(
                        f"""
                        SELECT {", ".join(select_parts)}
                        FROM farm_expenses
                        WHERE user_id = %s
                        """,
                        (user_id,),
                    )

                    rows = cursor.fetchall()

                    for row in rows:

                        data = row_to_dict(
                            cursor,
                            row,
                        )

                        try:
                            amount = float(
                                data.get(
                                    "amount",
                                    0,
                                )
                                or 0
                            )
                        except Exception:
                            amount = 0

                        result[
                            "total_expense"
                        ] += amount

                        result[
                            "expense_count"
                        ] += 1

                        category = str(
                            data.get(
                                "category",
                                "Other",
                            )
                            or "Other"
                        )

                        result[
                            "expense_categories"
                        ][category] = (
                            result[
                                "expense_categories"
                            ].get(category, 0)
                            + amount
                        )

        result["profit"] = (
            result["total_income"]
            - result["total_expense"]
        )

        result["total_income"] = round(
            result["total_income"],
            2,
        )

        result["total_expense"] = round(
            result["total_expense"],
            2,
        )

        result["profit"] = round(
            result["profit"],
            2,
        )

    except Exception as exc:

        print(
            "Reports finance error:",
            exc,
        )

    finally:
        safe_close(
            cursor,
            conn,
        )

    return result


# ============================================================
# MARKETPLACE REPORT
# ============================================================

def get_marketplace_report(user_id):
    """
    Farmer marketplace inventory and order statistics.
    """

    result = {
        "products": 0,
        "active_products": 0,
        "stock_quantity": 0.0,
        "inventory_value": 0.0,
        "orders": 0,
        "completed_orders": 0,
        "pending_orders": 0,
    }

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # ----------------------------------------------------
        # PRODUCTS
        # ----------------------------------------------------

        product_table = None

        if table_exists(
            cursor,
            "marketplace_products",
        ):
            product_table = (
                "marketplace_products"
            )

        elif table_exists(
            cursor,
            "products",
        ):
            product_table = "products"

        if product_table:

            columns = get_columns(
                cursor,
                product_table,
            )

            owner_column = None

            for candidate in [
                "farmer_id",
                "user_id",
                "seller_id",
            ]:
                if candidate in columns:
                    owner_column = candidate
                    break

            if owner_column:

                quantity_column = None

                for candidate in [
                    "quantity",
                    "stock",
                    "available_quantity",
                ]:
                    if candidate in columns:
                        quantity_column = candidate
                        break

                price_column = None

                for candidate in [
                    "price",
                    "selling_price",
                    "unit_price",
                ]:
                    if candidate in columns:
                        price_column = candidate
                        break

                status_column = (
                    "status"
                    if "status" in columns
                    else None
                )

                if quantity_column:

                    query = f"""
                        SELECT
                            {quantity_column} AS quantity
                    """

                    if price_column:
                        query += f"""
                            ,
                            {price_column} AS price
                        """

                    if status_column:
                        query += f"""
                            ,
                            {status_column} AS status
                        """

                    query += f"""
                        FROM {product_table}
                        WHERE {owner_column} = %s
                    """

                    cursor.execute(
                        query,
                        (user_id,),
                    )

                    rows = cursor.fetchall()

                    result["products"] = len(rows)

                    for row in rows:

                        item = row_to_dict(
                            cursor,
                            row,
                        )

                        try:
                            quantity = float(
                                item.get(
                                    "quantity",
                                    0,
                                )
                                or 0
                            )
                        except Exception:
                            quantity = 0

                        result[
                            "stock_quantity"
                        ] += quantity

                        if price_column:

                            try:
                                price = float(
                                    item.get(
                                        "price",
                                        0,
                                    )
                                    or 0
                                )
                            except Exception:
                                price = 0

                            result[
                                "inventory_value"
                            ] += (
                                quantity
                                * price
                            )

                        status = str(
                            item.get(
                                "status",
                                "active",
                            )
                            or "active"
                        ).lower()

                        if status in {
                            "active",
                            "available",
                            "listed",
                        }:
                            result[
                                "active_products"
                            ] += 1

        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        if table_exists(
            cursor,
            "orders",
        ):

            columns = get_columns(
                cursor,
                "orders",
            )

            owner_column = None

            for candidate in [
                "farmer_id",
                "seller_id",
            ]:
                if candidate in columns:
                    owner_column = candidate
                    break

            if owner_column:

                status_column = (
                    "status"
                    if "status" in columns
                    else None
                )

                query = "SELECT "

                if status_column:
                    query += (
                        f"{status_column}"
                        " AS status"
                    )
                else:
                    query += (
                        "'pending' AS status"
                    )

                query += """
                    FROM orders
                    WHERE
                """

                query += (
                    f"{owner_column} = %s"
                )

                cursor.execute(
                    query,
                    (user_id,),
                )

                rows = cursor.fetchall()

                result["orders"] = len(rows)

                for row in rows:

                    data = row_to_dict(
                        cursor,
                        row,
                    )

                    status = str(
                        data.get(
                            "status",
                            "pending",
                        )
                        or "pending"
                    ).lower()

                    if status in {
                        "completed",
                        "delivered",
                        "complete",
                    }:
                        result[
                            "completed_orders"
                        ] += 1

                    elif status in {
                        "pending",
                        "processing",
                        "confirmed",
                    }:
                        result[
                            "pending_orders"
                        ] += 1

        result[
            "stock_quantity"
        ] = round(
            result["stock_quantity"],
            2,
        )

        result[
            "inventory_value"
        ] = round(
            result["inventory_value"],
            2,
        )

    except Exception as exc:

        print(
            "Reports marketplace error:",
            exc,
        )

    finally:
        safe_close(
            cursor,
            conn,
        )

    return result


# ============================================================
# NOTIFICATION REPORT
# ============================================================

def get_notification_report(user_id):
    """
    Notification statistics.
    """

    result = {
        "total": 0,
        "unread": 0,
        "read": 0,
    }

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if not table_exists(
            cursor,
            "notifications",
        ):
            return result

        columns = get_columns(
            cursor,
            "notifications",
        )

        owner_column = None

        for candidate in [
            "user_id",
            "farmer_id",
        ]:
            if candidate in columns:
                owner_column = candidate
                break

        if not owner_column:
            return result

        read_column = (
            "is_read"
            if "is_read" in columns
            else None
        )

        if read_column:

            cursor.execute(
                f"""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE {read_column} = FALSE
                    ) AS unread,
                    COUNT(*) FILTER (
                        WHERE {read_column} = TRUE
                    ) AS read
                FROM notifications
                WHERE {owner_column} = %s
                """,
                (user_id,),
            )

        else:

            cursor.execute(
                f"""
                SELECT
                    COUNT(*) AS total
                FROM notifications
                WHERE {owner_column} = %s
                """,
                (user_id,),
            )

        row = cursor.fetchone()

        if row:

            data = row_to_dict(
                cursor,
                row,
            )

            result["total"] = int(
                data.get(
                    "total",
                    0,
                )
                or 0
            )

            result["unread"] = int(
                data.get(
                    "unread",
                    0,
                )
                or 0
            )

            result["read"] = int(
                data.get(
                    "read",
                    0,
                )
                or 0
            )

    except Exception as exc:

        print(
            "Reports notification error:",
            exc,
        )

    finally:
        safe_close(
            cursor,
            conn,
        )

    return result


# ============================================================
# COMPLETE REPORT
# ============================================================

def build_report(user_id):
    """
    Build complete farmer analytics report.
    """

    profile = get_farmer_profile(
        user_id
    )

    crops = get_crop_report(
        user_id
    )

    finance = get_finance_report(
        user_id
    )

    marketplace = get_marketplace_report(
        user_id
    )

    notifications = get_notification_report(
        user_id
    )

    # --------------------------------------------------------
    # PROFIT MARGIN
    # --------------------------------------------------------

    income = finance[
        "total_income"
    ]

    expense = finance[
        "total_expense"
    ]

    profit = finance[
        "profit"
    ]

    if income > 0:
        profit_margin = (
            profit / income
        ) * 100
    else:
        profit_margin = 0

    # --------------------------------------------------------
    # FARM SCORE
    # --------------------------------------------------------

    score = 0

    if crops["total_crops"] > 0:
        score += 25

    if finance["total_income"] > 0:
        score += 20

    if marketplace["products"] > 0:
        score += 20

    if marketplace["active_products"] > 0:
        score += 15

    if notifications["unread"] == 0:
        score += 10

    if finance["profit"] >= 0:
        score += 10

    score = min(
        100,
        max(0, score),
    )

    if score >= 80:
        health = "Excellent"
    elif score >= 60:
        health = "Good"
    elif score >= 40:
        health = "Moderate"
    else:
        health = "Needs Attention"

    return {
        "generated_at": datetime.now().isoformat(),

        "farmer": profile,

        "crops": crops,

        "finance": finance,

        "marketplace": marketplace,

        "notifications": notifications,

        "analytics": {
            "profit_margin": round(
                profit_margin,
                2,
            ),
            "farm_score": score,
            "farm_health": health,
        },

        "insights": generate_insights(
            crops,
            finance,
            marketplace,
            notifications,
        ),
    }


# ============================================================
# SMART INSIGHTS
# ============================================================

def generate_insights(
    crops,
    finance,
    marketplace,
    notifications,
):
    """
    Generate explainable rule-based insights.
    """

    insights = []

    # Crop insight
    if crops["total_crops"] == 0:

        insights.append({
            "type": "crop",
            "priority": "high",
            "title": "Add your crops",
            "message": (
                "Add your current crops "
                "to unlock better farm analytics."
            ),
        })

    elif crops["active_crops"] > 0:

        insights.append({
            "type": "crop",
            "priority": "normal",
            "title": "Active cultivation",
            "message": (
                f"You currently have "
                f"{crops['active_crops']} active crop(s)."
            ),
        })

    # Finance insight
    if finance["total_expense"] > finance["total_income"]:

        insights.append({
            "type": "finance",
            "priority": "high",
            "title": "Expense alert",
            "message": (
                "Your recorded expenses are "
                "higher than your recorded income."
            ),
        })

    elif finance["profit"] > 0:

        insights.append({
            "type": "finance",
            "priority": "normal",
            "title": "Positive balance",
            "message": (
                "Your recorded farm income "
                "is currently above expenses."
            ),
        })

    # Marketplace
    if marketplace["products"] == 0:

        insights.append({
            "type": "marketplace",
            "priority": "normal",
            "title": "Marketplace opportunity",
            "message": (
                "Add farm products to your "
                "marketplace inventory."
            ),
        })

    elif marketplace["active_products"] < marketplace["products"]:

        insights.append({
            "type": "marketplace",
            "priority": "normal",
            "title": "Review product listings",
            "message": (
                "Some products may not currently "
                "be active in the marketplace."
            ),
        })

    # Notifications
    if notifications["unread"] > 0:

        insights.append({
            "type": "notification",
            "priority": "normal",
            "title": "Unread notifications",
            "message": (
                f"You have "
                f"{notifications['unread']} unread "
                f"notification(s)."
            ),
        })

    if not insights:

        insights.append({
            "type": "general",
            "priority": "normal",
            "title": "Farm data looks good",
            "message": (
                "Continue updating your farm, "
                "crop and finance records."
            ),
        })

    return insights


# ============================================================
# REPORT PAGE
# ============================================================

@reports_bp.route(
    "/reports",
    methods=["GET"],
)
def reports():
    """
    Main farmer reports page.
    """

    if not is_logged_in():
        return redirect(
            url_for("auth.login")
        )

    if not is_farmer():
        return redirect(
            url_for("farmer.farmer")
        )

    report = build_report(
        current_user_id()
    )

    return render_template(
        "reports.html",
        report=report,

        # Backward-compatible variables
        farmer=report.get(
            "farmer",
            {},
        ),

        crops=report.get(
            "crops",
            {},
        ),

        finance=report.get(
            "finance",
            {},
        ),

        marketplace=report.get(
            "marketplace",
            {},
        ),

        notifications=report.get(
            "notifications",
            {},
        ),

        insights=report.get(
            "insights",
            [],
        ),

        language=session.get(
            "language",
            "en",
        ),
    )


# ============================================================
# REPORT API
# ============================================================

@reports_bp.route(
    "/api/reports",
    methods=["GET"],
)
def reports_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    if not is_farmer():
        return jsonify({
            "success": False,
            "message": "Farmer access required",
        }), 403

    report = build_report(
        current_user_id()
    )

    return jsonify({
        "success": True,
        "report": report,
    })


# ============================================================
# FARM SUMMARY API
# ============================================================

@reports_bp.route(
    "/api/reports/summary",
    methods=["GET"],
)
def reports_summary():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    if not is_farmer():
        return jsonify({
            "success": False,
            "message": "Farmer access required",
        }), 403

    report = build_report(
        current_user_id()
    )

    return jsonify({
        "success": True,

        "summary": {
            "total_crops": report[
                "crops"
            ]["total_crops"],

            "active_crops": report[
                "crops"
            ]["active_crops"],

            "total_area": report[
                "crops"
            ]["total_area"],

            "income": report[
                "finance"
            ]["total_income"],

            "expense": report[
                "finance"
            ]["total_expense"],

            "profit": report[
                "finance"
            ]["profit"],

            "products": report[
                "marketplace"
            ]["products"],

            "orders": report[
                "marketplace"
            ]["orders"],

            "unread_notifications": report[
                "notifications"
            ]["unread"],

            "farm_score": report[
                "analytics"
            ]["farm_score"],

            "farm_health": report[
                "analytics"
            ]["farm_health"],
        },
    })


# ============================================================
# CROP REPORT API
# ============================================================

@reports_bp.route(
    "/api/reports/crops",
    methods=["GET"],
)
def crop_report_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    if not is_farmer():
        return jsonify({
            "success": False,
            "message": "Farmer access required",
        }), 403

    return jsonify({
        "success": True,
        "data": get_crop_report(
            current_user_id()
        ),
    })


# ============================================================
# FINANCE REPORT API
# ============================================================

@reports_bp.route(
    "/api/reports/finance",
    methods=["GET"],
)
def finance_report_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    if not is_farmer():
        return jsonify({
            "success": False,
            "message": "Farmer access required",
        }), 403

    return jsonify({
        "success": True,
        "data": get_finance_report(
            current_user_id()
        ),
    })


# ============================================================
# MARKETPLACE REPORT API
# ============================================================

@reports_bp.route(
    "/api/reports/marketplace",
    methods=["GET"],
)
def marketplace_report_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    if not is_farmer():
        return jsonify({
            "success": False,
            "message": "Farmer access required",
        }), 403

    return jsonify({
        "success": True,
        "data": get_marketplace_report(
            current_user_id()
        ),
    })


# ============================================================
# SMART INSIGHTS API
# ============================================================

@reports_bp.route(
    "/api/reports/insights",
    methods=["GET"],
)
def insights_api():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    if not is_farmer():
        return jsonify({
            "success": False,
            "message": "Farmer access required",
        }), 403

    report = build_report(
        current_user_id()
    )

    return jsonify({
        "success": True,
        "insights": report[
            "insights"
        ],
    })


# ============================================================
# REPORT FILTER
# ============================================================

@reports_bp.route(
    "/api/reports/filter",
    methods=["POST"],
)
def filter_report():

    if not is_logged_in():
        return jsonify({
            "success": False,
            "message": "Login required",
        }), 401

    if not is_farmer():
        return jsonify({
            "success": False,
            "message": "Farmer access required",
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    report = build_report(
        current_user_id()
    )

    # Current report is user-level.
    # Date filtering can be expanded when all
    # financial/crop records have consistent dates.

    return jsonify({
        "success": True,
        "filter": {
            "from": data.get("from"),
            "to": data.get("to"),
            "crop": data.get("crop"),
        },
        "report": report,
    })


# ============================================================
# REPORT HEALTH
# ============================================================

@reports_bp.route(
    "/api/reports/health",
    methods=["GET"],
)
def reports_health():

    database_ok = False
    error = None

    conn = None
    cursor = None

    try:
        conn = get_connection()
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
        "service": "reports",
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

def initialize_reports_service(app=None):
    """
    Optional initialization hook.
    """

    if app:
        app.logger.info(
            "KisanVision360+ Reports service initialized."
        )

    return True
