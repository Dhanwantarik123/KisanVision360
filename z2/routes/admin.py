# ============================================================
# KISANVISION360+
# routes/admin.py
# Admin Dashboard & Administration Routes
# ============================================================

from flask import (
    Blueprint,
    render_template,
    redirect,
    session,
    url_for,
    flash,
    jsonify,
    request,
)

from database.db import get_db_connection


# ============================================================
# BLUEPRINT
# ============================================================

admin_bp = Blueprint("admin", __name__)


# ============================================================
# ADMIN ACCESS
# ============================================================

def admin_required():

    if not session.get("user_id"):
        flash("Please login to continue.", "warning")
        return redirect(url_for("login"))

    role = str(
        session.get("role", "")
    ).strip().lower()

    if role != "admin":

        flash("Admin access required.", "danger")

        if role == "farmer":
            return redirect(url_for("farmer"))

        if role == "consumer":
            return redirect(url_for("consumer"))

        return redirect(url_for("login"))

    return None


# ============================================================
# DATABASE HELPERS
# ============================================================

def fetch_one(query, params=None):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            query,
            params or ()
        )

        return cursor.fetchone()

    except Exception as exc:

        print("Admin DB Error:", exc)
        return None

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


def fetch_all(query, params=None):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            query,
            params or ()
        )

        return cursor.fetchall() or []

    except Exception as exc:

        print("Admin DB Error:", exc)
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
# ADMIN DASHBOARD
# ============================================================

@admin_bp.route("/admin")
def admin():

    access = admin_required()

    if access:
        return access

    # --------------------------------------------------------
    # USER STATISTICS
    # --------------------------------------------------------

    total_users = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM users
        """
    )

    total_farmers = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE LOWER(role) = 'farmer'
        """
    )

    total_consumers = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE LOWER(role) = 'consumer'
        """
    )

    total_admins = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE LOWER(role) = 'admin'
        """
    )

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    total_products = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM marketplace_products
        """
    )

    available_products = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM marketplace_products
        WHERE status = 'Available'
          AND quantity > 0
        """
    )

    # --------------------------------------------------------
    # ORDERS
    # --------------------------------------------------------

    total_orders = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM orders
        """
    )

    pending_orders = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM orders
        WHERE LOWER(COALESCE(status, '')) IN
        ('pending', 'placed', 'processing')
        """
    )

    completed_orders = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM orders
        WHERE LOWER(COALESCE(status, '')) IN
        ('completed', 'delivered')
        """
    )

    # --------------------------------------------------------
    # MARKETPLACE VALUE
    # --------------------------------------------------------

    trading_value = fetch_one(
        """
        SELECT COALESCE(
            SUM(
                COALESCE(price, 0) *
                COALESCE(quantity, 0)
            ),
            0
        ) AS value
        FROM marketplace_products
        """
    )

    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    notification_count = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM notifications
        """
    )

    unread_notifications = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM notifications
        WHERE COALESCE(is_read, FALSE) = FALSE
        """
    )

    # --------------------------------------------------------
    # RECENT USERS
    # --------------------------------------------------------

    recent_users = fetch_all(
        """
        SELECT
            id,
            name,
            mobile,
            email,
            role,
            location
        FROM users
        ORDER BY id DESC
        LIMIT 10
        """
    )

    # --------------------------------------------------------
    # RECENT PRODUCTS
    # --------------------------------------------------------

    recent_products = fetch_all(
        """
        SELECT *
        FROM marketplace_products
        ORDER BY created_at DESC
        LIMIT 10
        """
    )

    # --------------------------------------------------------
    # RECENT ORDERS
    # --------------------------------------------------------

    recent_orders = fetch_all(
        """
        SELECT *
        FROM orders
        ORDER BY created_at DESC
        LIMIT 10
        """
    )

    # --------------------------------------------------------
    # SAFE VALUES
    # --------------------------------------------------------

    def count_value(row):

        if isinstance(row, dict):
            return int(row.get("count", 0) or 0)

        if row:
            try:
                return int(row[0] or 0)
            except Exception:
                return 0

        return 0

    def numeric_value(row):

        if isinstance(row, dict):
            value = (
                row.get("value", 0)
                or 0
            )
        elif row:
            value = row[0] or 0
        else:
            value = 0

        try:
            return float(value)
        except Exception:
            return 0.0

    total_users_value = count_value(total_users)
    farmers_value = count_value(total_farmers)
    consumers_value = count_value(total_consumers)
    admins_value = count_value(total_admins)

    products_value = count_value(total_products)
    available_products_value = count_value(
        available_products
    )

    orders_value = count_value(total_orders)
    pending_orders_value = count_value(
        pending_orders
    )
    completed_orders_value = count_value(
        completed_orders
    )

    trading_value_value = numeric_value(
        trading_value
    )

    notification_value = count_value(
        notification_count
    )

    unread_notification_value = count_value(
        unread_notifications
    )

    # --------------------------------------------------------
    # ADMIN INSIGHT
    # --------------------------------------------------------

    if pending_orders_value > 10:

        admin_insight = (
            "High order activity detected. "
            "Review pending orders."
        )

    elif unread_notification_value > 10:

        admin_insight = (
            "There are several unread notifications "
            "requiring attention."
        )

    elif available_products_value == 0:

        admin_insight = (
            "No marketplace stock is currently available."
        )

    elif farmers_value == 0:

        admin_insight = (
            "No farmer accounts are currently registered."
        )

    else:

        admin_insight = (
            "Platform operations are running normally."
        )

    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    return render_template(
        "admin.html",

        name=session.get(
            "name",
            "Administrator"
        ),

        # User statistics
        total_users=total_users_value,
        total_farmers=farmers_value,
        total_consumers=consumers_value,
        total_admins=admins_value,

        # Marketplace
        total_products=products_value,
        available_products=available_products_value,

        # Orders
        total_orders=orders_value,
        pending_orders=pending_orders_value,
        completed_orders=completed_orders_value,

        # Finance
        trading_value=trading_value_value,

        # Notifications
        notification_count=unread_notification_value,
        total_notifications=notification_value,

        # Data
        recent_users=recent_users,
        recent_products=recent_products,
        recent_orders=recent_orders,

        # Intelligence
        admin_insight=admin_insight,

        language=session.get(
            "language",
            "en"
        ),

        role="admin",
    )


# ============================================================
# ADMIN STATISTICS API
# ============================================================

@admin_bp.route("/api/admin/statistics")
def admin_statistics():

    access = admin_required()

    if access:
        return jsonify({
            "success": False,
            "message": "Admin authentication required."
        }), 401

    def get_count(query):

        row = fetch_one(query)

        if isinstance(row, dict):
            return int(
                row.get("count", 0) or 0
            )

        if row:
            try:
                return int(row[0] or 0)
            except Exception:
                pass

        return 0

    users = get_count(
        """
        SELECT COUNT(*)
        FROM users
        """
    )

    farmers = get_count(
        """
        SELECT COUNT(*)
        FROM users
        WHERE LOWER(role) = 'farmer'
        """
    )

    consumers = get_count(
        """
        SELECT COUNT(*)
        FROM users
        WHERE LOWER(role) = 'consumer'
        """
    )

    products = get_count(
        """
        SELECT COUNT(*)
        FROM marketplace_products
        """
    )

    orders = get_count(
        """
        SELECT COUNT(*)
        FROM orders
        """
    )

    notifications = get_count(
        """
        SELECT COUNT(*)
        FROM notifications
        WHERE COALESCE(is_read, FALSE) = FALSE
        """
    )

    return jsonify({

        "success": True,

        "statistics": {
            "users": users,
            "farmers": farmers,
            "consumers": consumers,
            "products": products,
            "orders": orders,
            "unread_notifications": notifications,
        }
    })


# ============================================================
# ADMIN USERS API
# ============================================================

@admin_bp.route("/api/admin/users")
def admin_users():

    access = admin_required()

    if access:
        return jsonify({
            "success": False,
            "message": "Admin authentication required."
        }), 401

    search = request.args.get(
        "q",
        ""
    ).strip()

    role = request.args.get(
        "role",
        ""
    ).strip().lower()

    params = []

    query = """
        SELECT
            id,
            name,
            mobile,
            email,
            role,
            location
        FROM users
        WHERE 1 = 1
    """

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        query += """
            AND (
                LOWER(name) LIKE LOWER(%s)
                OR LOWER(email) LIKE LOWER(%s)
                OR mobile LIKE %s
                OR LOWER(location) LIKE LOWER(%s)
            )
        """

        keyword = f"%{search}%"

        params.extend([
            keyword,
            keyword,
            keyword,
            keyword,
        ])

    # --------------------------------------------------------
    # ROLE FILTER
    # --------------------------------------------------------

    if role in {
        "farmer",
        "consumer",
        "admin",
    }:

        query += """
            AND LOWER(role) = LOWER(%s)
        """

        params.append(role)

    query += """
        ORDER BY id DESC
        LIMIT 100
    """

    users = fetch_all(
        query,
        tuple(params)
    )

    return jsonify({
        "success": True,
        "count": len(users),
        "users": users,
    })


# ============================================================
# ADMIN PRODUCTS API
# ============================================================

@admin_bp.route("/api/admin/products")
def admin_products():

    access = admin_required()

    if access:
        return jsonify({
            "success": False,
            "message": "Admin authentication required."
        }), 401

    products = fetch_all(
        """
        SELECT *
        FROM marketplace_products
        ORDER BY created_at DESC
        LIMIT 100
        """
    )

    return jsonify({
        "success": True,
        "count": len(products),
        "products": products,
    })


# ============================================================
# ADMIN ORDERS API
# ============================================================

@admin_bp.route("/api/admin/orders")
def admin_orders():

    access = admin_required()

    if access:
        return jsonify({
            "success": False,
            "message": "Admin authentication required."
        }), 401

    status = request.args.get(
        "status",
        ""
    ).strip().lower()

    if status:

        orders = fetch_all(
            """
            SELECT *
            FROM orders
            WHERE LOWER(COALESCE(status, '')) = LOWER(%s)
            ORDER BY created_at DESC
            LIMIT 100
            """,
            (status,),
        )

    else:

        orders = fetch_all(
            """
            SELECT *
            FROM orders
            ORDER BY created_at DESC
            LIMIT 100
            """
        )

    return jsonify({
        "success": True,
        "count": len(orders),
        "orders": orders,
    })


# ============================================================
# ADMIN NOTIFICATIONS API
# ============================================================

@admin_bp.route("/api/admin/notifications")
def admin_notifications():

    access = admin_required()

    if access:
        return jsonify({
            "success": False,
            "message": "Admin authentication required."
        }), 401

    notifications = fetch_all(
        """
        SELECT *
        FROM notifications
        ORDER BY created_at DESC
        LIMIT 100
        """
    )

    return jsonify({
        "success": True,
        "count": len(notifications),
        "notifications": notifications,
    })


# ============================================================
# ADMIN LANGUAGE API
# ============================================================

@admin_bp.route("/api/admin/language")
def admin_language():

    access = admin_required()

    if access:
        return jsonify({
            "success": False
        }), 401

    language = session.get(
        "language",
        "en"
    )

    rtl_languages = {
        "ur",
        "ks",
        "sd"
    }

    return jsonify({
        "success": True,
        "language": language,
        "direction": (
            "rtl"
            if language in rtl_languages
            else "ltr"
        )
    })


# ============================================================
# ADMIN HEALTH
# ============================================================

@admin_bp.route("/api/admin/health")
def admin_health():

    return jsonify({
        "success": True,
        "module": "admin",
        "status": "online",
        "application": "KisanVision360+",
    })
