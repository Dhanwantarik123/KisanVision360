
# ============================================================
# KISANVISION360+
# routes/reports.py
# Smart Farm Reports
# PostgreSQL / Supabase Finance Integration
# ============================================================

import os
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    jsonify,
    session,
)

from database.db import get_db_connection


# ============================================================
# OPTIONAL DOTENV
# ============================================================

try:
    from dotenv import load_dotenv

    load_dotenv(override=True)

except Exception:
    pass


# ============================================================
# BLUEPRINT
# ============================================================

reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


# ============================================================
# WEATHER IMPORT
# ============================================================

try:

    from routes.weather import get_current_weather

except Exception:

    get_current_weather = None


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_float(value, default=0):
    """Safely convert value to float."""

    try:

        if value is None:
            return default

        return float(value)

    except (ValueError, TypeError):

        return default


def safe_int(value, default=0):
    """Safely convert value to integer."""

    try:

        if value is None:
            return default

        return int(value)

    except (ValueError, TypeError):

        return default


# ============================================================
# GET FARMER ID
# ============================================================

def get_farmer_id():
    """
    Get logged-in farmer ID from session.

    Existing session names are preserved.
    """

    possible_ids = [
        session.get("farmer_id"),
        session.get("user_id"),
        session.get("id"),
        session.get("uid"),
    ]

    for value in possible_ids:

        if value is not None:

            try:
                return int(value)

            except (ValueError, TypeError):
                continue

    return None


# ============================================================
# GET LOGGED USER NAME
# ============================================================

def get_logged_user_name():
    """Get farmer name from session."""

    possible_names = [
        session.get("name"),
        session.get("user_name"),
        session.get("username"),
        session.get("farmer_name"),
    ]

    for name in possible_names:

        if name:

            return str(name)

    return "Farmer"


# ============================================================
# FARMER REPORT DATA
# ============================================================

def get_farmer_report_data(farmer_id):
    """
    Get farmer profile information from PostgreSQL/Supabase.
    """

    farmer = {
        "id": farmer_id,
        "name": get_logged_user_name(),
        "location": "",
        "mobile": "",
        "email": "",
    }

    if not farmer_id:
        return farmer

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # ====================================================
        # USERS
        # ====================================================

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    location,
                    mobile,
                    email
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (farmer_id,)
            )

            row = cursor.fetchone()

            if row:

                farmer["id"] = row["id"]

                if row["name"]:
                    farmer["name"] = row["name"]

                farmer["location"] = row["location"] or ""
                farmer["mobile"] = row["mobile"] or ""
                farmer["email"] = row["email"] or ""

                return farmer

        except Exception as error:

            print(
                "Users report query error:",
                error
            )

            connection.rollback()

        # ====================================================
        # FARMERS FALLBACK
        # ====================================================

        try:

            cursor.execute(
                """
                SELECT *
                FROM farmers
                WHERE id = %s
                LIMIT 1
                """,
                (farmer_id,)
            )

            row = cursor.fetchone()

            if row:

                if row.get("name"):
                    farmer["name"] = row["name"]

                if row.get("location"):
                    farmer["location"] = row["location"]

                if row.get("mobile"):
                    farmer["mobile"] = row["mobile"]

                if row.get("email"):
                    farmer["email"] = row["email"]

        except Exception as error:

            print(
                "Farmers fallback query error:",
                error
            )

            connection.rollback()

        return farmer

    except Exception as error:

        print(
            "FARMER REPORT ERROR:",
            error
        )

        return farmer

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# FINANCE REPORT
# ============================================================

def get_finance_report(farmer_id):
    """
    Get complete finance information from PostgreSQL/Supabase.

    Database source:

        .env
          ↓
        DATABASE_URL
          ↓
        database/db.py
          ↓
        get_db_connection()
          ↓
        farm_income / farm_expenses
    """

    finance = {
        "income": 0,
        "expenses": 0,
        "profit": 0,

        "income_count": 0,
        "expense_count": 0,

        "profit_margin": 0,
        "expense_ratio": 0,

        "financial_score": 0,

        "transactions": [],

        "monthly_data": [],

        "income_categories": [],

        "expense_categories": [],

        "goals": [],
    }

    if not farmer_id:

        print(
            "FINANCE REPORT: farmer_id is missing"
        )

        return finance

    connection = None
    cursor = None

    try:

        # ====================================================
        # DATABASE FROM .ENV
        # ====================================================

        connection = get_db_connection()
        cursor = connection.cursor()

        print()
        print("=" * 65)
        print("KISANVISION360+ FINANCE REPORT")
        print("=" * 65)
        print("Farmer ID:", farmer_id)

        # ====================================================
        # TOTAL INCOME
        # ====================================================

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0) AS total_income,
                COUNT(*) AS income_count
            FROM farm_income
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cursor.fetchone()

        if row:

            finance["income"] = safe_float(
                row["total_income"]
            )

            finance["income_count"] = safe_int(
                row["income_count"]
            )

        # ====================================================
        # TOTAL EXPENSE
        # ====================================================

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0) AS total_expenses,
                COUNT(*) AS expense_count
            FROM farm_expenses
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cursor.fetchone()

        if row:

            finance["expenses"] = safe_float(
                row["total_expenses"]
            )

            finance["expense_count"] = safe_int(
                row["expense_count"]
            )

        # ====================================================
        # PROFIT
        # ====================================================

        finance["profit"] = round(
            finance["income"]
            - finance["expenses"],
            2
        )

        # ====================================================
        # PROFIT MARGIN
        # ====================================================

        if finance["income"] > 0:

            finance["profit_margin"] = round(
                (
                    finance["profit"]
                    / finance["income"]
                ) * 100,
                2
            )

        # ====================================================
        # EXPENSE RATIO
        # ====================================================

        if finance["income"] > 0:

            finance["expense_ratio"] = round(
                (
                    finance["expenses"]
                    / finance["income"]
                ) * 100,
                2
            )

        # ====================================================
        # FINANCIAL SCORE
        # ====================================================

        if finance["income"] <= 0:

            finance["financial_score"] = 0

        elif finance["profit"] <= 0:

            finance["financial_score"] = 20

        else:

            score = (
                50
                + finance["profit_margin"]
            )

            finance["financial_score"] = round(
                max(0, min(100, score)),
                2
            )

        # ====================================================
        # ALL TRANSACTIONS
        # ====================================================

        cursor.execute(
            """
            SELECT
                description,
                amount,
                'Income' AS type,
                income_date AS transaction_date
            FROM farm_income
            WHERE farmer_id = %s

            UNION ALL

            SELECT
                description,
                amount,
                'Expense' AS type,
                expense_date AS transaction_date
            FROM farm_expenses
            WHERE farmer_id = %s

            ORDER BY transaction_date DESC
            """,
            (
                farmer_id,
                farmer_id
            )
        )

        transaction_rows = cursor.fetchall()

        finance["transactions"] = []

        for row in transaction_rows:

            finance["transactions"].append(
                (
                    row["description"] or "Finance Transaction",
                    safe_float(row["amount"]),
                    row["type"],
                    row["transaction_date"],
                )
            )

        # ====================================================
        # INCOME CATEGORIES
        # ====================================================

        cursor.execute(
            """
            SELECT
                COALESCE(category, 'Other') AS category,
                COALESCE(SUM(amount), 0) AS amount
            FROM farm_income
            WHERE farmer_id = %s
            GROUP BY category
            ORDER BY amount DESC
            """,
            (farmer_id,)
        )

        finance["income_categories"] = []

        for row in cursor.fetchall():

            finance["income_categories"].append(
                {
                    "category": row["category"],
                    "amount": safe_float(
                        row["amount"]
                    ),
                }
            )

        # ====================================================
        # EXPENSE CATEGORIES
        # ====================================================

        cursor.execute(
            """
            SELECT
                COALESCE(category, 'Other') AS category,
                COALESCE(SUM(amount), 0) AS amount
            FROM farm_expenses
            WHERE farmer_id = %s
            GROUP BY category
            ORDER BY amount DESC
            """,
            (farmer_id,)
        )

        finance["expense_categories"] = []

        for row in cursor.fetchall():

            finance["expense_categories"].append(
                {
                    "category": row["category"],
                    "amount": safe_float(
                        row["amount"]
                    ),
                }
            )

        # ====================================================
        # MONTHLY FINANCE
        # ====================================================

        cursor.execute(
            """
            SELECT
                month,
                SUM(income) AS income,
                SUM(expenses) AS expenses
            FROM (

                SELECT
                    DATE_TRUNC(
                        'month',
                        income_date
                    ) AS month,

                    SUM(amount) AS income,

                    0::numeric AS expenses

                FROM farm_income

                WHERE farmer_id = %s

                GROUP BY
                    DATE_TRUNC(
                        'month',
                        income_date
                    )

                UNION ALL

                SELECT
                    DATE_TRUNC(
                        'month',
                        expense_date
                    ) AS month,

                    0::numeric AS income,

                    SUM(amount) AS expenses

                FROM farm_expenses

                WHERE farmer_id = %s

                GROUP BY
                    DATE_TRUNC(
                        'month',
                        expense_date
                    )

            ) AS monthly

            GROUP BY month

            ORDER BY month DESC
            """,
            (
                farmer_id,
                farmer_id
            )
        )

        monthly_rows = cursor.fetchall()

        finance["monthly_data"] = []

        for row in monthly_rows:

            monthly_income = safe_float(
                row["income"]
            )

            monthly_expenses = safe_float(
                row["expenses"]
            )

            month_value = row["month"]

            if month_value:

                try:

                    month_value = month_value.strftime(
                        "%Y-%m"
                    )

                except Exception:

                    month_value = str(
                        month_value
                    )

            else:

                month_value = ""

            finance["monthly_data"].append(
                {
                    "month": month_value,

                    "income": monthly_income,

                    "expenses": monthly_expenses,

                    "profit": round(
                        monthly_income
                        - monthly_expenses,
                        2
                    ),
                }
            )

        # ====================================================
        # FINANCIAL GOALS
        # ====================================================

        try:

            cursor.execute(
                """
                SELECT *
                FROM financial_goals
                WHERE farmer_id = %s
                ORDER BY id DESC
                """,
                (farmer_id,)
            )

            finance["goals"] = cursor.fetchall()

        except Exception as goal_error:

            print(
                "Financial goals unavailable:",
                goal_error
            )

            connection.rollback()

            finance["goals"] = []

        # ====================================================
        # DEBUG INFORMATION
        # ====================================================

        print(
            "Income:",
            finance["income"]
        )

        print(
            "Expenses:",
            finance["expenses"]
        )

        print(
            "Profit:",
            finance["profit"]
        )

        print(
            "Income count:",
            finance["income_count"]
        )

        print(
            "Expense count:",
            finance["expense_count"]
        )

        print(
            "Transactions:",
            len(finance["transactions"])
        )

        print(
            "Financial score:",
            finance["financial_score"]
        )

        print("=" * 65)
        print()

        return finance

    except Exception as error:

        print()
        print("=" * 65)
        print("FINANCE REPORT DATABASE ERROR")
        print("=" * 65)
        print(error)
        print("=" * 65)
        print()

        return finance

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# WEATHER REPORT
# ============================================================

def get_report_weather(farmer):
    """
    Get weather information using existing weather module.
    """

    default_weather = {
        "success": False,
        "city": "Nagpur",
        "country": "IN",
        "description": "Weather data unavailable",
        "temperature": 0,
        "feels_like": 0,
        "humidity": 0,
        "rainfall": 0,
        "wind": 0,
        "wind_speed": 0,
        "pressure": 0,
        "clouds": 0,
        "cloud_cover": 0,
        "visibility": 0,
        "uv_index": 0,
        "risk": "Unknown",
        "advice": "",
    }

    if not get_current_weather:

        return default_weather

    try:

        location = (
            farmer.get("location")
            or os.getenv(
                "DEFAULT_CITY",
                "Nagpur"
            )
        )

        weather = get_current_weather(
            location
        )

        if not weather:

            return default_weather

        if isinstance(weather, dict):

            default_weather.update(
                weather
            )

        # ----------------------------------------------------
        # Compatibility values
        # ----------------------------------------------------

        if not default_weather.get("wind"):

            default_weather["wind"] = safe_float(
                default_weather.get(
                    "wind_speed",
                    0
                )
            )

        if not default_weather.get("clouds"):

            default_weather["clouds"] = safe_float(
                default_weather.get(
                    "cloud_cover",
                    0
                )
            )

        return default_weather

    except Exception as error:

        print(
            "REPORT WEATHER ERROR:",
            error
        )

        return default_weather


# ============================================================
# WEATHER SCORE
# ============================================================

def calculate_weather_score(weather):
    """Calculate simple weather score."""

    if not weather:
        return 0

    temperature = safe_float(
        weather.get("temperature")
    )

    humidity = safe_float(
        weather.get("humidity")
    )

    rainfall = safe_float(
        weather.get("rainfall")
    )

    score = 70

    # Temperature
    if 15 <= temperature <= 35:

        score += 10

    elif temperature > 40 or temperature < 10:

        score -= 15

    # Humidity
    if 40 <= humidity <= 80:

        score += 10

    elif humidity > 90 or humidity < 20:

        score -= 10

    # Rainfall
    if rainfall > 50:

        score -= 15

    elif rainfall > 0:

        score += 5

    return round(
        max(0, min(100, score)),
        2
    )


# ============================================================
# FARM SCORE
# ============================================================

def calculate_farm_score(
    financial_score,
    weather_score
):
    """
    Calculate overall farm score.

    Finance = 60%
    Weather = 40%
    """

    financial_score = safe_float(
        financial_score
    )

    weather_score = safe_float(
        weather_score
    )

    if financial_score <= 0 and weather_score <= 0:

        return 0

    if financial_score <= 0:

        return round(
            weather_score,
            2
        )

    if weather_score <= 0:

        return round(
            financial_score,
            2
        )

    score = (
        financial_score * 0.60
        +
        weather_score * 0.40
    )

    return round(
        max(0, min(100, score)),
        2
    )


# ============================================================
# FARM STATUS
# ============================================================

def get_farm_status(score):

    score = safe_float(score)

    if score >= 80:

        return "Excellent"

    if score >= 60:

        return "Good"

    if score >= 40:

        return "Needs Attention"

    return "Critical"


# ============================================================
# GENERATE INSIGHTS
# ============================================================

def generate_insights(
    finance,
    weather
):
    """
    Generate report warnings, positive points
    and solutions.
    """

    warning_points = []
    positive_points = []
    solutions = []

    # ========================================================
    # FINANCE
    # ========================================================

    income = safe_float(
        finance.get("income")
    )

    expenses = safe_float(
        finance.get("expenses")
    )

    profit = safe_float(
        finance.get("profit")
    )

    profit_margin = safe_float(
        finance.get("profit_margin")
    )

    expense_ratio = safe_float(
        finance.get("expense_ratio")
    )

    # --------------------------------------------------------
    # No transactions
    # --------------------------------------------------------

    if (
        finance.get("income_count", 0) == 0
        and
        finance.get("expense_count", 0) == 0
    ):

        warning_points.append(
            "No Finance transactions have been recorded yet."
        )

        solutions.append(
            "Add your farm income and expense transactions "
            "to generate a complete financial report."
        )

    # --------------------------------------------------------
    # Profit
    # --------------------------------------------------------

    elif profit > 0:

        positive_points.append(
            f"Farm is currently showing a profit of ₹{profit:,.2f}."
        )

    else:

        warning_points.append(
            "Farm expenses are currently higher than income."
        )

        solutions.append(
            "Review major expenses and identify areas "
            "where costs can be reduced."
        )

    # --------------------------------------------------------
    # Profit margin
    # --------------------------------------------------------

    if income > 0:

        if profit_margin >= 30:

            positive_points.append(
                "Your profit margin is healthy."
            )

        elif profit_margin < 10:

            warning_points.append(
                "Profit margin is low."
            )

            solutions.append(
                "Consider improving crop yield, "
                "market price realization and expense control."
            )

    # --------------------------------------------------------
    # Expense ratio
    # --------------------------------------------------------

    if expense_ratio > 80:

        warning_points.append(
            "A large portion of farm income is being spent."
        )

        solutions.append(
            "Monitor input costs, labour expenses "
            "and other recurring farm expenses."
        )

    elif expense_ratio < 60 and income > 0:

        positive_points.append(
            "Farm expense ratio is under control."
        )

    # ========================================================
    # WEATHER
    # ========================================================

    temperature = safe_float(
        weather.get("temperature")
    )

    humidity = safe_float(
        weather.get("humidity")
    )

    rainfall = safe_float(
        weather.get("rainfall")
    )

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    if temperature >= 40:

        warning_points.append(
            "High temperature may create heat stress "
            "for crops."
        )

        solutions.append(
            "Monitor irrigation and provide sufficient "
            "water during hot conditions."
        )

    elif 15 <= temperature <= 35:

        positive_points.append(
            "Current temperature is generally suitable "
            "for farming activity."
        )

    # --------------------------------------------------------
    # Humidity
    # --------------------------------------------------------

    if humidity >= 85:

        warning_points.append(
            "High humidity can increase disease risk."
        )

        solutions.append(
            "Monitor crops regularly for fungal "
            "and bacterial symptoms."
        )

    # --------------------------------------------------------
    # Rainfall
    # --------------------------------------------------------

    if rainfall > 50:

        warning_points.append(
            "Heavy rainfall may increase waterlogging risk."
        )

        solutions.append(
            "Check field drainage and avoid unnecessary "
            "irrigation during heavy rainfall."
        )

    elif rainfall > 0:

        positive_points.append(
            "Recent rainfall may support crop water availability."
        )

    return {
        "warning_points": warning_points,
        "positive_points": positive_points,
        "solutions": solutions,
    }


# ============================================================
# BUILD COMPLETE REPORT
# ============================================================

def build_report(
    farmer_id,
    farmer=None,
    finance=None,
    weather=None
):
    """
    Build complete Smart Farm Report.
    """

    if farmer is None:

        farmer = get_farmer_report_data(
            farmer_id
        )

    if finance is None:

        finance = get_finance_report(
            farmer_id
        )

    if weather is None:

        weather = get_report_weather(
            farmer
        )

    # ========================================================
    # WEATHER SCORE
    # ========================================================

    weather_score = calculate_weather_score(
        weather
    )

    # ========================================================
    # FINANCIAL SCORE
    # ========================================================

    financial_score = safe_float(
        finance.get(
            "financial_score",
            0
        )
    )

    # ========================================================
    # FARM SCORE
    # ========================================================

    farm_score = calculate_farm_score(
        financial_score,
        weather_score
    )

    # ========================================================
    # FARM STATUS
    # ========================================================

    farm_status = get_farm_status(
        farm_score
    )

    # ========================================================
    # INSIGHTS
    # ========================================================

    insights = generate_insights(
        finance,
        weather
    )

    # ========================================================
    # COMPLETE REPORT
    # ========================================================

    report = {

        "farmer": farmer,

        "finance": finance,

        "weather": weather,

        "farm_score": farm_score,

        "farm_status": farm_status,

        "financial_score": financial_score,

        "weather_score": weather_score,

        "insights": insights,

        "crops": [],

        "marketplace": [],

        "notifications": [],

        "generated_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }

    return report


# ============================================================
# MAIN REPORT PAGE
# ============================================================

@reports_bp.route("/")
def reports():
    """
    Smart Farm Report page.
    """

    farmer_id = get_farmer_id()

    # ========================================================
    # FARMER
    # ========================================================

    farmer = get_farmer_report_data(
        farmer_id
    )

    # ========================================================
    # FINANCE FROM DATABASE
    # ========================================================

    finance = get_finance_report(
        farmer_id
    )

    # ========================================================
    # WEATHER
    # ========================================================

    weather = get_report_weather(
        farmer
    )

    # ========================================================
    # SCORES
    # ========================================================

    financial_score = safe_float(
        finance.get(
            "financial_score",
            0
        )
    )

    weather_score = calculate_weather_score(
        weather
    )

    farm_score = calculate_farm_score(
        financial_score,
        weather_score
    )

    farm_status = get_farm_status(
        farm_score
    )

    # ========================================================
    # INSIGHTS
    # ========================================================

    insights = generate_insights(
        finance,
        weather
    )

    # ========================================================
    # FLAT VARIABLES
    #
    # IMPORTANT:
    # reports.html expects these variables directly.
    # ========================================================

    name = farmer.get(
        "name",
        get_logged_user_name()
    )

    income = safe_float(
        finance.get("income", 0)
    )

    expenses = safe_float(
        finance.get("expenses", 0)
    )

    profit = safe_float(
        finance.get("profit", 0)
    )

    income_count = safe_int(
        finance.get("income_count", 0)
    )

    expense_count = safe_int(
        finance.get("expense_count", 0)
    )

    profit_margin = safe_float(
        finance.get("profit_margin", 0)
    )

    expense_ratio = safe_float(
        finance.get("expense_ratio", 0)
    )

    transactions = finance.get(
        "transactions",
        []
    )

    warning_points = insights.get(
        "warning_points",
        []
    )

    positive_points = insights.get(
        "positive_points",
        []
    )

    solutions = insights.get(
        "solutions",
        []
    )

    # ========================================================
    # RENDER
    # ========================================================

    return render_template(
        "reports.html",

        # ----------------------------------------------------
        # Complete report
        # ----------------------------------------------------

        report=build_report(
            farmer_id,
            farmer=farmer,
            finance=finance,
            weather=weather
        ),

        reports=build_report(
            farmer_id,
            farmer=farmer,
            finance=finance,
            weather=weather
        ),

        # ----------------------------------------------------
        # Farmer
        # ----------------------------------------------------

        farmer=farmer,

        name=name,

        # ----------------------------------------------------
        # Finance
        # ----------------------------------------------------

        finance=finance,

        income=income,

        expenses=expenses,

        profit=profit,

        income_count=income_count,

        expense_count=expense_count,

        profit_margin=profit_margin,

        expense_ratio=expense_ratio,

        financial_score=financial_score,

        transactions=transactions,

        monthly_data=finance.get(
            "monthly_data",
            []
        ),

        income_categories=finance.get(
            "income_categories",
            []
        ),

        expense_categories=finance.get(
            "expense_categories",
            []
        ),

        goals=finance.get(
            "goals",
            []
        ),

        # ----------------------------------------------------
        # Weather
        # ----------------------------------------------------

        weather=weather,

        weather_score=weather_score,

        # ----------------------------------------------------
        # Farm
        # ----------------------------------------------------

        farm_score=farm_score,

        farm_status=farm_status,

        # ----------------------------------------------------
        # Insights
        # ----------------------------------------------------

        warning_points=warning_points,

        positive_points=positive_points,

        solutions=solutions,

        # ----------------------------------------------------
        # Other modules
        # ----------------------------------------------------

        crops=[],

        marketplace=[],

        notifications=[],

        # ----------------------------------------------------
        # Generated
        # ----------------------------------------------------

        generated_at=datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )


# ============================================================
# API - SUMMARY
# ============================================================

@reports_bp.route("/api/summary")
def report_summary_api():
    """
    Return complete report summary as JSON.
    """

    farmer_id = get_farmer_id()

    farmer = get_farmer_report_data(
        farmer_id
    )

    finance = get_finance_report(
        farmer_id
    )

    weather = get_report_weather(
        farmer
    )

    weather_score = calculate_weather_score(
        weather
    )

    financial_score = safe_float(
        finance.get(
            "financial_score",
            0
        )
    )

    farm_score = calculate_farm_score(
        financial_score,
        weather_score
    )

    farm_status = get_farm_status(
        farm_score
    )

    return jsonify(
        {
            "success": True,

            "farmer": farmer,

            "finance": finance,

            "weather": weather,

            "financial_score": financial_score,

            "weather_score": weather_score,

            "farm_score": farm_score,

            "farm_status": farm_status,

            "generated_at":
                datetime.now().isoformat(),
        }
    )


# ============================================================
# API - WEATHER
# ============================================================

@reports_bp.route("/api/weather")
def report_weather_api():
    """
    Return report weather.
    """

    farmer_id = get_farmer_id()

    farmer = get_farmer_report_data(
        farmer_id
    )

    weather = get_report_weather(
        farmer
    )

    return jsonify(
        {
            "success": True,

            "weather": weather,

            "weather_score":
                calculate_weather_score(
                    weather
                ),
        }
    )


# ============================================================
# API - FINANCE
# ============================================================

@reports_bp.route("/api/finance")
def report_finance_api():
    """
    Return finance data directly from PostgreSQL/Supabase.
    """

    farmer_id = get_farmer_id()

    finance = get_finance_report(
        farmer_id
    )

    return jsonify(
        {
            "success": True,

            "farmer_id": farmer_id,

            "finance": finance,

            "income": finance.get(
                "income",
                0
            ),

            "expenses": finance.get(
                "expenses",
                0
            ),

            "profit": finance.get(
                "profit",
                0
            ),

            "income_count": finance.get(
                "income_count",
                0
            ),

            "expense_count": finance.get(
                "expense_count",
                0
            ),

            "transactions": finance.get(
                "transactions",
                []
            ),
        }
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@reports_bp.route("/health")
def reports_health():
    """
    Reports module health check.
    """

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                current_database()
                AS database_name
            """
        )

        row = cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify(
            {
                "success": True,

                "module": "reports",

                "database": "PostgreSQL / Supabase",

                "database_name":
                    row["database_name"]
                    if row
                    else "",

                "finance_integration": True,

                "status": "healthy",
            }
        )

    except Exception as error:

        return jsonify(
            {
                "success": False,

                "module": "reports",

                "finance_integration": True,

                "status": "unhealthy",

                "error": str(error),
            }
        ), 500


# ============================================================
# END OF FILE
# ============================================================

