
# ============================================================
# KISANVISION360+ FARM FINANCE ROUTES
# File: routes/finance.py
# ============================================================

from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from database.db import get_db_connection


# ============================================================
# BLUEPRINT
# ============================================================

finance_bp = Blueprint("finance", __name__)


# ============================================================
# AUTHENTICATION
# ============================================================

def farmer_only():
    """
    Check whether current user is logged-in farmer.
    """
    user_id = session.get("user_id")
    role = str(session.get("role", "")).lower().strip()

    if not user_id:
        return False

    if role != "farmer":
        return False

    return True


def login_redirect():
    """
    Redirect unauthenticated users to login page.
    """
    try:
        return redirect(url_for("auth.login"))
    except Exception:
        return redirect("/login")


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert DB values to float.
    """
    try:
        if value is None:
            return default

        if isinstance(value, Decimal):
            return float(value)

        return float(value)

    except (TypeError, ValueError, InvalidOperation):
        return default


def safe_amount(value):
    """
    Convert form amount to Decimal.
    """
    try:
        value = str(value).strip()

        if not value:
            return None

        amount = Decimal(value)

        if amount <= 0:
            return None

        return amount

    except (InvalidOperation, ValueError, TypeError):
        return None


def get_user_id():
    return session.get("user_id")


# ============================================================
# DATABASE HELPERS
# ============================================================

def table_exists(conn, table_name):
    """
    Check whether PostgreSQL table exists.
    """
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = %s
            ) AS exists
            """,
            (table_name,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            return bool(row.get("exists"))

        return bool(row[0])

    finally:
        cur.close()


def column_exists(conn, table_name, column_name):
    """
    Check whether a column exists.
    """
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                  AND column_name = %s
            ) AS exists
            """,
            (table_name, column_name)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            return bool(row.get("exists"))

        return bool(row[0])

    finally:
        cur.close()


# ============================================================
# FINANCE DATABASE INITIALIZATION
# ============================================================

def create_finance_tables():
    """
    Create finance tables if they don't exist.
    """

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # ----------------------------------------------------
        # FARM EXPENSES
        # ----------------------------------------------------

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS farm_expenses (
                id SERIAL PRIMARY KEY,
                farmer_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount NUMERIC(12,2) NOT NULL DEFAULT 0,
                category VARCHAR(100),
                expense_date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # FARM INCOME
        # ----------------------------------------------------

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS farm_income (
                id SERIAL PRIMARY KEY,
                farmer_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount NUMERIC(12,2) NOT NULL DEFAULT 0,
                category VARCHAR(100),
                income_date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # FINANCIAL GOALS
        # ----------------------------------------------------

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS financial_goals (
                id SERIAL PRIMARY KEY,
                farmer_id INTEGER NOT NULL,
                goal_name VARCHAR(200) NOT NULL,
                target_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
                current_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
                target_date DATE,
                status VARCHAR(30) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # INDEXES
        # ----------------------------------------------------

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_farm_expenses_farmer
            ON farm_expenses(farmer_id)
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_farm_income_farmer
            ON farm_income(farmer_id)
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_financial_goals_farmer
            ON financial_goals(farmer_id)
            """
        )

        conn.commit()

        print("[FINANCE] Finance tables initialized successfully.")

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Database initialization error:",
            repr(error)
        )

    finally:

        cur.close()
        conn.close()


def initialize_finance_service():
    """
    Called by app.py if required.
    """
    try:

        create_finance_tables()

        print("[FINANCE] Finance service initialized.")

        return True

    except Exception as error:

        print(
            "[FINANCE] Finance service initialization failed:",
            repr(error)
        )

        return False


# ============================================================
# MAIN FINANCE DASHBOARD
# ============================================================

@finance_bp.route("/finance")
def finance():

    if not farmer_only():
        return login_redirect()

    farmer_id = get_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # ----------------------------------------------------
        # TOTAL INCOME
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM farm_income
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            income = safe_float(row.get("total"))
        else:
            income = safe_float(row[0])

        # ----------------------------------------------------
        # TOTAL EXPENSES
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM farm_expenses
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            expenses = safe_float(row.get("total"))
        else:
            expenses = safe_float(row[0])

        # ----------------------------------------------------
        # PROFIT
        # ----------------------------------------------------

        profit = income - expenses

        # ----------------------------------------------------
        # RECENT TRANSACTIONS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                description,
                amount,
                'income' AS transaction_type,
                income_date AS transaction_date
            FROM farm_income
            WHERE farmer_id = %s

            UNION ALL

            SELECT
                description,
                amount,
                'expense' AS transaction_type,
                expense_date AS transaction_date
            FROM farm_expenses
            WHERE farmer_id = %s

            ORDER BY transaction_date DESC
            LIMIT 10
            """,
            (farmer_id, farmer_id)
        )

        transactions = []

        for row in cur.fetchall():

            if isinstance(row, dict):

                transactions.append(
                    (
                        row.get("description"),
                        row.get("amount"),
                        row.get("transaction_type"),
                        row.get("transaction_date")
                    )
                )

            else:

                transactions.append(
                    (
                        row[0],
                        row[1],
                        row[2],
                        row[3]
                    )
                )

        # ----------------------------------------------------
        # USER NAME
        # ----------------------------------------------------

        name = session.get("name", "Farmer")

        try:

            cur.execute(
                """
                SELECT name
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (farmer_id,)
            )

            user_row = cur.fetchone()

            if user_row:

                if isinstance(user_row, dict):
                    db_name = user_row.get("name")
                else:
                    db_name = user_row[0]

                if db_name:
                    name = db_name

        except Exception:
            pass

        return render_template(
            "finance.html",
            income=income,
            expenses=expenses,
            profit=profit,
            transactions=transactions,
            name=name
        )

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Dashboard error:",
            repr(error)
        )

        flash(
            "Unable to load finance dashboard.",
            "error"
        )

        return render_template(
            "finance.html",
            income=0,
            expenses=0,
            profit=0,
            transactions=[],
            name=session.get("name", "Farmer")
        )

    finally:

        cur.close()
        conn.close()


# ============================================================
# ADD INCOME
# ============================================================

@finance_bp.route("/finance/income", methods=["GET", "POST"])
@finance_bp.route("/finance/add-income", methods=["GET", "POST"])
def add_income():

    if not farmer_only():
        return login_redirect()

    if request.method == "POST":

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        amount = safe_amount(
            request.form.get("amount")
        )

        income_date = request.form.get(
            "income_date"
        ) or request.form.get("date")

        if not description:

            flash(
                "Please enter income description.",
                "error"
            )

            return redirect(
                url_for("finance.add_income")
            )

        if amount is None:

            flash(
                "Please enter a valid income amount.",
                "error"
            )

            return redirect(
                url_for("finance.add_income")
            )

        if not income_date:
            income_date = date.today()

        conn = get_db_connection()
        cur = conn.cursor()

        try:

            cur.execute(
                """
                INSERT INTO farm_income
                (
                    farmer_id,
                    description,
                    amount,
                    category,
                    income_date
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    get_user_id(),
                    description,
                    amount,
                    category,
                    income_date
                )
            )

            conn.commit()

            flash(
                "Income added successfully.",
                "success"
            )

            return redirect(
                url_for("finance.finance")
            )

        except Exception as error:

            conn.rollback()

            print(
                "[FINANCE] Add income error:",
                repr(error)
            )

            flash(
                "Unable to add income.",
                "error"
            )

            return redirect(
                url_for("finance.add_income")
            )

        finally:

            cur.close()
            conn.close()

    # --------------------------------------------------------
    # GET INCOME PAGE
    # --------------------------------------------------------

    return render_template(
        "income.html",
        today=date.today().isoformat()
    )


# ============================================================
# ADD EXPENSE
# ============================================================

@finance_bp.route("/finance/expense", methods=["GET", "POST"])
@finance_bp.route("/finance/add-expense", methods=["GET", "POST"])
def add_expense():

    if not farmer_only():
        return login_redirect()

    farmer_id = get_user_id()

    # ========================================================
    # POST - ADD EXPENSE
    # ========================================================

    if request.method == "POST":

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        amount = safe_amount(
            request.form.get("amount")
        )

        expense_date = request.form.get(
            "expense_date"
        ) or request.form.get("date")

        # ----------------------------------------------------
        # VALIDATE DESCRIPTION
        # ----------------------------------------------------

        if not description:

            flash(
                "Please enter expense description.",
                "error"
            )

            return redirect(
                url_for("finance.add_expense")
            )

        # ----------------------------------------------------
        # VALIDATE AMOUNT
        # ----------------------------------------------------

        if amount is None:

            flash(
                "Please enter a valid expense amount.",
                "error"
            )

            return redirect(
                url_for("finance.add_expense")
            )

        # ----------------------------------------------------
        # DEFAULT DATE
        # ----------------------------------------------------

        if not expense_date:
            expense_date = date.today()

        conn = get_db_connection()
        cur = conn.cursor()

        try:

            # ------------------------------------------------
            # INSERT EXPENSE
            # ------------------------------------------------

            cur.execute(
                """
                INSERT INTO farm_expenses
                (
                    farmer_id,
                    description,
                    amount,
                    category,
                    expense_date
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    farmer_id,
                    description,
                    amount,
                    category,
                    expense_date
                )
            )

            conn.commit()

            flash(
                "Expense added successfully.",
                "success"
            )

            # ------------------------------------------------
            # IMPORTANT:
            # After POST, redirect to finance dashboard.
            # Do NOT render expense.html here.
            # ------------------------------------------------

            return redirect(
                url_for("finance.finance")
            )

        except Exception as error:

            conn.rollback()

            print(
                "[FINANCE] Add expense error:",
                repr(error)
            )

            flash(
                "Unable to add expense.",
                "error"
            )

            return redirect(
                url_for("finance.add_expense")
            )

        finally:

            cur.close()
            conn.close()

    # ========================================================
    # GET - LOAD EXPENSE PAGE
    # ========================================================

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # ----------------------------------------------------
        # TOTAL EXPENSE
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS expense_total
            FROM farm_expenses
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):

            expense_total = safe_float(
                row.get("expense_total")
            )

        else:

            expense_total = safe_float(
                row[0]
            )

        # ----------------------------------------------------
        # EXPENSE LIST
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                id,
                description,
                amount,
                category,
                expense_date
            FROM farm_expenses
            WHERE farmer_id = %s
            ORDER BY expense_date DESC, id DESC
            """,
            (farmer_id,)
        )

        expense_list = cur.fetchall()

        # ----------------------------------------------------
        # RENDER EXPENSE PAGE
        # ----------------------------------------------------

        return render_template(
            "expense.html",
            today=date.today().isoformat(),
            expense_total={
                "value": expense_total
            },
            expense_list=expense_list,
            name=session.get("name", "Farmer")
        )

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Load expense page error:",
            repr(error)
        )

        flash(
            "Unable to load expense page.",
            "error"
        )

        return redirect(
            url_for("finance.finance")
        )

    finally:

        cur.close()
        conn.close()


# ============================================================
# DELETE INCOME
# ============================================================

@finance_bp.route(
    "/finance/income/delete/<int:income_id>",
    methods=["POST", "GET"]
)
def delete_income(income_id):

    if not farmer_only():
        return login_redirect()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            DELETE FROM farm_income
            WHERE id = %s
              AND farmer_id = %s
            """,
            (
                income_id,
                get_user_id()
            )
        )

        conn.commit()

        flash(
            "Income deleted successfully.",
            "success"
        )

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Delete income error:",
            repr(error)
        )

        flash(
            "Unable to delete income.",
            "error"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for("finance.finance")
    )


# ============================================================
# DELETE EXPENSE
# ============================================================

@finance_bp.route(
    "/finance/expense/delete/<int:expense_id>",
    methods=["POST", "GET"]
)
def delete_expense(expense_id):

    if not farmer_only():
        return login_redirect()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            DELETE FROM farm_expenses
            WHERE id = %s
              AND farmer_id = %s
            """,
            (
                expense_id,
                get_user_id()
            )
        )

        conn.commit()

        flash(
            "Expense deleted successfully.",
            "success"
        )

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Delete expense error:",
            repr(error)
        )

        flash(
            "Unable to delete expense.",
            "error"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for("finance.finance")
    )


# ============================================================
# PROFIT ANALYSIS
# ============================================================

@finance_bp.route("/finance/profit")
def profit():

    if not farmer_only():
        return login_redirect()

    farmer_id = get_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # ----------------------------------------------------
        # TOTAL INCOME
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM farm_income
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            total_income = safe_float(row.get("total"))
        else:
            total_income = safe_float(row[0])

        # ----------------------------------------------------
        # TOTAL EXPENSE
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM farm_expenses
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            total_expense = safe_float(row.get("total"))
        else:
            total_expense = safe_float(row[0])

        net_profit = total_income - total_expense

        # ----------------------------------------------------
        # MONTHLY ANALYSIS
        # ----------------------------------------------------

        cur.execute(
            """
            WITH income_monthly AS (
                SELECT
                    DATE_TRUNC(
                        'month',
                        income_date
                    ) AS month_date,
                    SUM(amount) AS income
                FROM farm_income
                WHERE farmer_id = %s
                GROUP BY 1
            ),

            expense_monthly AS (
                SELECT
                    DATE_TRUNC(
                        'month',
                        expense_date
                    ) AS month_date,
                    SUM(amount) AS expenses
                FROM farm_expenses
                WHERE farmer_id = %s
                GROUP BY 1
            )

            SELECT
                TO_CHAR(
                    COALESCE(
                        i.month_date,
                        e.month_date
                    ),
                    'YYYY-MM'
                ) AS month,

                COALESCE(i.income, 0) AS income,

                COALESCE(e.expenses, 0) AS expenses,

                (
                    COALESCE(i.income, 0)
                    -
                    COALESCE(e.expenses, 0)
                ) AS profit

            FROM income_monthly i

            FULL OUTER JOIN expense_monthly e
                ON i.month_date = e.month_date

            ORDER BY month DESC
            LIMIT 12
            """,
            (
                farmer_id,
                farmer_id
            )
        )

        monthly_data = cur.fetchall()

        # ----------------------------------------------------
        # INCOME BY CATEGORY
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                COALESCE(
                    NULLIF(category, ''),
                    'Other'
                ) AS category,
                COALESCE(SUM(amount), 0) AS total
            FROM farm_income
            WHERE farmer_id = %s
            GROUP BY category
            ORDER BY total DESC
            """,
            (farmer_id,)
        )

        income_categories = cur.fetchall()

        # ----------------------------------------------------
        # EXPENSE BY CATEGORY
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                COALESCE(
                    NULLIF(category, ''),
                    'Other'
                ) AS category,
                COALESCE(SUM(amount), 0) AS total
            FROM farm_expenses
            WHERE farmer_id = %s
            GROUP BY category
            ORDER BY total DESC
            """,
            (farmer_id,)
        )

        expense_categories = cur.fetchall()

        return render_template(
            "profit.html",
            total_income=total_income,
            total_expense=total_expense,
            net_profit=net_profit,
            monthly_data=monthly_data,
            income_categories=income_categories,
            expense_categories=expense_categories
        )

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Profit analysis error:",
            repr(error)
        )

        flash(
            "Unable to load profit analysis.",
            "error"
        )

        return redirect(
            url_for("finance.finance")
        )

    finally:

        cur.close()
        conn.close()


# ============================================================
# FARM CALCULATOR
# ============================================================

@finance_bp.route(
    "/finance/calculator",
    methods=["GET", "POST"]
)
def calculator():

    if not farmer_only():
        return login_redirect()

    result = None

    if request.method == "POST":

        area = safe_float(
            request.form.get("area"),
            0
        )

        seed_cost = safe_float(
            request.form.get("seed_cost"),
            0
        )

        fertilizer_cost = safe_float(
            request.form.get("fertilizer_cost"),
            0
        )

        pesticide_cost = safe_float(
            request.form.get("pesticide_cost"),
            0
        )

        labour_cost = safe_float(
            request.form.get("labour_cost"),
            0
        )

        irrigation_cost = safe_float(
            request.form.get("irrigation_cost"),
            0
        )

        other_cost = safe_float(
            request.form.get("other_cost"),
            0
        )

        expected_yield = safe_float(
            request.form.get("expected_yield"),
            0
        )

        selling_price = safe_float(
            request.form.get("selling_price"),
            0
        )

        total_cost = (
            seed_cost
            + fertilizer_cost
            + pesticide_cost
            + labour_cost
            + irrigation_cost
            + other_cost
        )

        expected_revenue = (
            expected_yield
            * selling_price
        )

        expected_profit = (
            expected_revenue
            - total_cost
        )

        if expected_revenue > 0:

            profit_margin = (
                expected_profit
                / expected_revenue
            ) * 100

        else:

            profit_margin = 0

        if area > 0:
            cost_per_area = total_cost / area
        else:
            cost_per_area = 0

        result = {
            "area": area,
            "total_cost": total_cost,
            "expected_revenue": expected_revenue,
            "expected_profit": expected_profit,
            "profit_margin": profit_margin,
            "cost_per_area": cost_per_area
        }

    return render_template(
        "calculator.html",
        result=result
    )


# ============================================================
# FINANCE SUMMARY API
# ============================================================

@finance_bp.route("/finance/summary")
def summary():

    if not farmer_only():

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    farmer_id = get_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM farm_income
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            income = safe_float(row.get("total"))
        else:
            income = safe_float(row[0])

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM farm_expenses
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            expenses = safe_float(row.get("total"))
        else:
            expenses = safe_float(row[0])

        return jsonify({
            "success": True,
            "income": income,
            "expenses": expenses,
            "profit": income - expenses
        })

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Summary API error:",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to calculate summary"
        }), 500

    finally:

        cur.close()
        conn.close()


# ============================================================
# MONTHLY FINANCE API
# ============================================================

@finance_bp.route("/finance/monthly")
def monthly():

    if not farmer_only():

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    farmer_id = get_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            WITH income_monthly AS (
                SELECT
                    DATE_TRUNC(
                        'month',
                        income_date
                    ) AS month_date,
                    SUM(amount) AS income
                FROM farm_income
                WHERE farmer_id = %s
                GROUP BY 1
            ),

            expense_monthly AS (
                SELECT
                    DATE_TRUNC(
                        'month',
                        expense_date
                    ) AS month_date,
                    SUM(amount) AS expenses
                FROM farm_expenses
                WHERE farmer_id = %s
                GROUP BY 1
            )

            SELECT
                TO_CHAR(
                    COALESCE(
                        i.month_date,
                        e.month_date
                    ),
                    'YYYY-MM'
                ) AS month,

                COALESCE(i.income, 0) AS income,

                COALESCE(e.expenses, 0) AS expenses,

                (
                    COALESCE(i.income, 0)
                    -
                    COALESCE(e.expenses, 0)
                ) AS profit

            FROM income_monthly i

            FULL OUTER JOIN expense_monthly e
                ON i.month_date = e.month_date

            ORDER BY month ASC
            LIMIT 12
            """,
            (
                farmer_id,
                farmer_id
            )
        )

        rows = cur.fetchall()

        data = []

        for row in rows:

            if isinstance(row, dict):

                data.append({
                    "month": row.get("month"),
                    "income": safe_float(
                        row.get("income")
                    ),
                    "expenses": safe_float(
                        row.get("expenses")
                    ),
                    "profit": safe_float(
                        row.get("profit")
                    )
                })

            else:

                data.append({
                    "month": row[0],
                    "income": safe_float(row[1]),
                    "expenses": safe_float(row[2]),
                    "profit": safe_float(row[3])
                })

        return jsonify({
            "success": True,
            "data": data
        })

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Monthly API error:",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to load monthly data"
        }), 500

    finally:

        cur.close()
        conn.close()


# ============================================================
# CATEGORY API
# ============================================================

@finance_bp.route("/finance/categories")
def categories():

    if not farmer_only():

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    farmer_id = get_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # ----------------------------------------------------
        # INCOME CATEGORIES
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                COALESCE(
                    NULLIF(category, ''),
                    'Other'
                ) AS category,
                COALESCE(SUM(amount), 0) AS total
            FROM farm_income
            WHERE farmer_id = %s
            GROUP BY category
            ORDER BY total DESC
            """,
            (farmer_id,)
        )

        income_rows = cur.fetchall()

        # ----------------------------------------------------
        # EXPENSE CATEGORIES
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                COALESCE(
                    NULLIF(category, ''),
                    'Other'
                ) AS category,
                COALESCE(SUM(amount), 0) AS total
            FROM farm_expenses
            WHERE farmer_id = %s
            GROUP BY category
            ORDER BY total DESC
            """,
            (farmer_id,)
        )

        expense_rows = cur.fetchall()

        income = []
        expenses = []

        for row in income_rows:

            if isinstance(row, dict):

                income.append({
                    "category": row.get("category"),
                    "total": safe_float(
                        row.get("total")
                    )
                })

            else:

                income.append({
                    "category": row[0],
                    "total": safe_float(row[1])
                })

        for row in expense_rows:

            if isinstance(row, dict):

                expenses.append({
                    "category": row.get("category"),
                    "total": safe_float(
                        row.get("total")
                    )
                })

            else:

                expenses.append({
                    "category": row[0],
                    "total": safe_float(row[1])
                })

        return jsonify({
            "success": True,
            "income": income,
            "expenses": expenses
        })

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Category API error:",
            repr(error)
        )

        return jsonify({
            "success": False
        }), 500

    finally:

        cur.close()
        conn.close()


# ============================================================
# EMI CALCULATOR
# ============================================================

@finance_bp.route(
    "/finance/emi",
    methods=["GET", "POST"]
)
def emi():

    if not farmer_only():
        return login_redirect()

    result = None

    if request.method == "POST":

        principal = safe_float(
            request.form.get("principal"),
            0
        )

        annual_rate = safe_float(
            request.form.get("interest_rate"),
            0
        )

        years = safe_float(
            request.form.get("years"),
            0
        )

        months = years * 12

        monthly_rate = (
            annual_rate / 12 / 100
        )

        if (
            principal > 0
            and months > 0
            and monthly_rate > 0
        ):

            emi_amount = (
                principal
                * monthly_rate
                * (
                    (1 + monthly_rate) ** months
                )
                /
                (
                    ((1 + monthly_rate) ** months)
                    - 1
                )
            )

        elif (
            principal > 0
            and months > 0
        ):

            emi_amount = principal / months

        else:

            emi_amount = 0

        total_payment = (
            emi_amount * months
        )

        total_interest = (
            total_payment - principal
        )

        result = {
            "principal": principal,
            "interest_rate": annual_rate,
            "years": years,
            "months": months,
            "emi": emi_amount,
            "total_payment": total_payment,
            "total_interest": total_interest
        }

    return render_template(
        "emi.html",
        result=result
    )


# ============================================================
# FINANCIAL GOALS
# ============================================================

@finance_bp.route(
    "/finance/goals",
    methods=["GET", "POST"]
)
def goals():

    if not farmer_only():
        return login_redirect()

    farmer_id = get_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        if request.method == "POST":

            goal_name = request.form.get(
                "goal_name",
                ""
            ).strip()

            target_amount = safe_amount(
                request.form.get("target_amount")
            )

            current_amount = safe_amount(
                request.form.get("current_amount")
            )

            target_date = request.form.get(
                "target_date"
            )

            if current_amount is None:
                current_amount = Decimal("0")

            if (
                not goal_name
                or target_amount is None
            ):

                flash(
                    "Please enter valid goal details.",
                    "error"
                )

                return redirect(
                    url_for("finance.goals")
                )

            cur.execute(
                """
                INSERT INTO financial_goals
                (
                    farmer_id,
                    goal_name,
                    target_amount,
                    current_amount,
                    target_date,
                    status
                )
                VALUES (
                    %s, %s, %s, %s, %s, 'active'
                )
                """,
                (
                    farmer_id,
                    goal_name,
                    target_amount,
                    current_amount,
                    target_date or None
                )
            )

            conn.commit()

            flash(
                "Financial goal created successfully.",
                "success"
            )

            return redirect(
                url_for("finance.goals")
            )

        # ----------------------------------------------------
        # GET GOALS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                id,
                goal_name,
                target_amount,
                current_amount,
                target_date,
                status,
                created_at
            FROM financial_goals
            WHERE farmer_id = %s
            ORDER BY created_at DESC
            """,
            (farmer_id,)
        )

        goals_data = cur.fetchall()

        return render_template(
            "goals.html",
            goals=goals_data
        )

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Goals error:",
            repr(error)
        )

        flash(
            "Unable to load financial goals.",
            "error"
        )

        return redirect(
            url_for("finance.finance")
        )

    finally:

        cur.close()
        conn.close()


# ============================================================
# DELETE GOAL
# ============================================================

@finance_bp.route(
    "/finance/goals/delete/<int:goal_id>",
    methods=["POST", "GET"]
)
def delete_goal(goal_id):

    if not farmer_only():
        return login_redirect()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            DELETE FROM financial_goals
            WHERE id = %s
              AND farmer_id = %s
            """,
            (
                goal_id,
                get_user_id()
            )
        )

        conn.commit()

        flash(
            "Financial goal deleted.",
            "success"
        )

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Delete goal error:",
            repr(error)
        )

        flash(
            "Unable to delete financial goal.",
            "error"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for("finance.goals")
    )


# ============================================================
# FINANCE HEALTH API
# ============================================================

@finance_bp.route("/finance/health")
def finance_health():

    if not farmer_only():

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    farmer_id = get_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # ----------------------------------------------------
        # INCOME
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM farm_income
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            income = safe_float(row.get("total"))
        else:
            income = safe_float(row[0])

        # ----------------------------------------------------
        # EXPENSE
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM farm_expenses
            WHERE farmer_id = %s
            """,
            (farmer_id,)
        )

        row = cur.fetchone()

        if isinstance(row, dict):
            expenses = safe_float(row.get("total"))
        else:
            expenses = safe_float(row[0])

        profit_value = income - expenses

        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        if income <= 0 and expenses <= 0:

            score = 0

        elif income <= 0:

            score = 20

        else:

            ratio = (
                profit_value / income
            ) * 100

            if ratio < 0:
                score = 20

            elif ratio < 10:
                score = 45

            elif ratio < 25:
                score = 70

            else:
                score = 90

        return jsonify({
            "success": True,
            "income": income,
            "expenses": expenses,
            "profit": profit_value,
            "score": score
        })

    except Exception as error:

        conn.rollback()

        print(
            "[FINANCE] Health API error:",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to calculate financial health"
        }), 500

    finally:

        cur.close()
        conn.close()


# ============================================================
# TEST ROUTE
# ============================================================

@finance_bp.route("/finance/test")
def finance_test():

    if not farmer_only():

        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    return jsonify({
        "success": True,
        "message": "Finance module is working",
        "user_id": get_user_id(),
        "role": session.get("role")
    })


# ============================================================
# INITIALIZATION
# ============================================================

# IMPORTANT:
# Do NOT automatically execute database initialization here.
#
# app.py already initializes the database.
#
# If required, app.py can call:
#
# from routes.finance import initialize_finance_service
# initialize_finance_service()
#
# ============================================================

