# ============================================================
# KISANVISION360+
# CONSUMER ROUTES
# PostgreSQL / Supabase
#
# Separate Consumer Notification System
# ============================================================

from datetime import datetime
import traceback

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
)

from database.db import get_db_connection


# ============================================================
# BLUEPRINT
# ============================================================

consumer_bp = Blueprint(
    "consumer",
    __name__
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    return get_db_connection()


def row_to_dict(row):
    if row is None:
        return None

    if isinstance(row, dict):
        return dict(row)

    try:
        return dict(row)
    except Exception:
        return row


def rows_to_dict(rows):
    return [
        row_to_dict(row)
        for row in rows
    ]


def execute_fetchone(conn, query, params=()):
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def execute_fetchall(conn, query, params=()):
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


# ============================================================
# AUTH HELPERS
# ============================================================

def logged_in():
    return "user_id" in session


def current_role():
    return str(
        session.get("role", "")
    ).strip().lower()


def consumer_only():
    return (
        logged_in()
        and current_role() == "consumer"
    )


def login_redirect():
    return redirect(
        url_for("auth.login")
    )


# ============================================================
# CONSUMER NOTIFICATION TABLE
#
# This is intentionally separate from farmer notifications.
# ============================================================

def create_consumer_notification_table():

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS consumer_notifications (

                    id BIGSERIAL PRIMARY KEY,

                    consumer_id BIGINT NOT NULL,

                    title VARCHAR(255) NOT NULL,

                    message TEXT NOT NULL,

                    notification_type VARCHAR(50)
                        DEFAULT 'general',

                    is_read BOOLEAN
                        DEFAULT FALSE,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_consumer_notifications_consumer
                ON consumer_notifications(consumer_id)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_consumer_notifications_read
                ON consumer_notifications(
                    consumer_id,
                    is_read
                )
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_consumer_notifications_type
                ON consumer_notifications(
                    consumer_id,
                    notification_type
                )
                """
            )

        conn.commit()

        print(
            "[OK] Consumer notification table ready."
        )

        return True

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            "[ERROR] Consumer notification table:",
            repr(error)
        )

        return False

    finally:

        if conn:
            conn.close()


# ============================================================
# INITIALIZE TABLE
#
# Safe to call when blueprint is imported.
# ============================================================

try:
    create_consumer_notification_table()
except Exception as error:
    print(
        "[WARNING] Consumer notification initialization:",
        repr(error)
    )


# ============================================================
# CONSUMER NOTIFICATION CREATOR
#
# Other modules such as marketplace.py can import this:
#
# from routes.consumer import create_consumer_notification
#
# Example:
#
# create_consumer_notification(
#     consumer_id=12,
#     title="Order Confirmed",
#     message="Your order #25 has been confirmed.",
#     notification_type="order"
# )
# ============================================================

def create_consumer_notification(
    consumer_id,
    title,
    message,
    notification_type="general"
):

    conn = None

    try:

        if not consumer_id:
            return False

        title = str(
            title or "KisanVision360+"
        ).strip()

        message = str(
            message or ""
        ).strip()

        notification_type = str(
            notification_type or "general"
        ).strip().lower()

        if not title:
            title = "KisanVision360+"

        if not message:
            return False

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO consumer_notifications
                (
                    consumer_id,
                    title,
                    message,
                    notification_type,
                    is_read,
                    created_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    consumer_id,
                    title,
                    message,
                    notification_type
                )
            )

        conn.commit()

        return True

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            "[CONSUMER NOTIFICATION CREATE ERROR]",
            repr(error)
        )

        return False

    finally:

        if conn:
            conn.close()


# ============================================================
# CONSUMER NOTIFICATION COUNT
# ============================================================

def get_consumer_notification_count(
    consumer_id
):

    conn = None

    try:

        conn = get_db()

        row = execute_fetchone(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM consumer_notifications
            WHERE consumer_id = %s
              AND is_read = FALSE
            """,
            (consumer_id,)
        )

        if not row:
            return 0

        data = row_to_dict(row)

        return int(
            data.get("count", 0) or 0
        )

    except Exception as error:

        print(
            "[CONSUMER NOTIFICATION COUNT ERROR]",
            repr(error)
        )

        return 0

    finally:

        if conn:
            conn.close()


# ============================================================
# GET CONSUMER NOTIFICATIONS
# ============================================================

def get_consumer_notifications(
    consumer_id,
    limit=100
):

    conn = None

    try:

        conn = get_db()

        rows = execute_fetchall(
            conn,
            """
            SELECT
                id,
                consumer_id,
                title,
                message,
                notification_type,
                is_read,
                created_at
            FROM consumer_notifications
            WHERE consumer_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            (
                consumer_id,
                limit
            )
        )

        return rows_to_dict(rows)

    except Exception as error:

        print(
            "[CONSUMER NOTIFICATIONS ERROR]",
            repr(error)
        )

        return []

    finally:

        if conn:
            conn.close()


# ============================================================
# WEATHER
# ============================================================

def get_consumer_location():

    location = (
        session.get("city")
        or session.get("location")
        or "Nagpur"
    )

    return str(location).strip()


def get_consumer_weather():

    """
    Uses the existing KisanVision360 weather service.

    Expected existing function:
        routes.weather.get_current_weather(city)

    If unavailable, the dashboard still works.
    """

    city = get_consumer_location()

    try:

        from routes.weather import (
            get_current_weather
        )

        data = get_current_weather(city)

        if not data:
            return {}

        weather = row_to_dict(data)

        if not weather:
            return {}

        # ----------------------------------------------------
        # Normalize different possible weather field names
        # ----------------------------------------------------

        weather["city"] = (
            weather.get("city")
            or weather.get("name")
            or city
        )

        weather["country"] = (
            weather.get("country")
            or "IN"
        )

        weather["temperature"] = (
            weather.get("temperature")
            if weather.get("temperature") is not None
            else weather.get("temp", "N/A")
        )

        weather["feels_like"] = (
            weather.get("feels_like")
            if weather.get("feels_like") is not None
            else weather.get("feels_like_temp", "N/A")
        )

        weather["humidity"] = (
            weather.get("humidity", "N/A")
        )

        weather["wind"] = (
            weather.get("wind")
            if weather.get("wind") is not None
            else weather.get("wind_speed", "N/A")
        )

        weather["clouds"] = (
            weather.get("clouds")
            if weather.get("clouds") is not None
            else weather.get("cloud", 0)
        )

        weather["description"] = (
            weather.get("description")
            or weather.get("condition")
            or "Weather information"
        )

        weather["icon"] = (
            weather.get("icon", "")
        )

        return weather

    except Exception as error:

        print(
            "[CONSUMER WEATHER ERROR]",
            repr(error)
        )

        return {
            "city": city,
            "country": "IN",
            "temperature": "N/A",
            "feels_like": "N/A",
            "humidity": "N/A",
            "wind": "N/A",
            "clouds": 0,
            "description": "Weather unavailable",
            "icon": ""
        }


# ============================================================
# CONSUMER DASHBOARD
# ============================================================

@consumer_bp.route(
    "/consumer"
)
def consumer():

    if not consumer_only():
        return login_redirect()

    user_id = session["user_id"]

    conn = None

    try:

        conn = get_db()

        # ----------------------------------------------------
        # USER
        # ----------------------------------------------------

        user = execute_fetchone(
            conn,
            """
            SELECT *
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = row_to_dict(user)

        if not user:

            session.clear()

            return redirect(
                url_for("auth.login")
            )

        # ----------------------------------------------------
        # CONSUMER PROFILE
        # ----------------------------------------------------

        consumer_profile = None

        try:

            consumer_profile = execute_fetchone(
                conn,
                """
                SELECT *
                FROM consumer_profiles
                WHERE user_id = %s
                LIMIT 1
                """,
                (user_id,)
            )

            consumer_profile = row_to_dict(
                consumer_profile
            )

        except Exception as error:

            print(
                "[CONSUMER PROFILE WARNING]",
                repr(error)
            )

        # ----------------------------------------------------
        # PRODUCTS
        # ----------------------------------------------------

        products = []

        try:

            products = execute_fetchall(
                conn,
                """
                SELECT
                    p.*,
                    u.name AS farmer_name
                FROM products p
                LEFT JOIN users u
                    ON p.farmer_id = u.id
                WHERE LOWER(
                    COALESCE(
                        p.status,
                        'active'
                    )
                ) = 'active'
                AND COALESCE(
                    p.quantity,
                    0
                ) > 0
                ORDER BY
                    p.created_at DESC,
                    p.id DESC
                LIMIT 12
                """
            )

            products = rows_to_dict(
                products
            )

        except Exception as error:

            print(
                "[CONSUMER PRODUCTS WARNING]",
                repr(error)
            )

            products = []

        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        orders = []

        try:

            orders = execute_fetchall(
                conn,
                """
                SELECT
                    o.*,
                    u.name AS farmer_name
                FROM orders o
                LEFT JOIN users u
                    ON o.farmer_id = u.id
                WHERE o.consumer_id = %s
                ORDER BY
                    o.id DESC
                LIMIT 10
                """,
                (user_id,)
            )

            orders = rows_to_dict(
                orders
            )

        except Exception as error:

            print(
                "[CONSUMER ORDERS WARNING]",
                repr(error)
            )

            orders = []

        # ----------------------------------------------------
        # CART
        # ----------------------------------------------------

        cart_count = 0

        try:

            row = execute_fetchone(
                conn,
                """
                SELECT
                    COUNT(*) AS count
                FROM cart
                WHERE consumer_id = %s
                """,
                (user_id,)
            )

            if row:

                cart_data = row_to_dict(row)

                cart_count = int(
                    cart_data.get("count", 0) or 0
                )

        except Exception as error:

            print(
                "[CONSUMER CART WARNING]",
                repr(error)
            )

        # ----------------------------------------------------
        # WISHLIST
        # ----------------------------------------------------

        wishlist_count = 0

        try:

            row = execute_fetchone(
                conn,
                """
                SELECT
                    COUNT(*) AS count
                FROM wishlist
                WHERE consumer_id = %s
                """,
                (user_id,)
            )

            if row:

                wishlist_data = row_to_dict(
                    row
                )

                wishlist_count = int(
                    wishlist_data.get(
                        "count",
                        0
                    ) or 0
                )

        except Exception as error:

            print(
                "[CONSUMER WISHLIST WARNING]",
                repr(error)
            )

        # ----------------------------------------------------
        # NOTIFICATION COUNT
        # ----------------------------------------------------

        notification_count = (
            get_consumer_notification_count(
                user_id
            )
        )

        # ----------------------------------------------------
        # NOTIFICATIONS
        # ----------------------------------------------------

        notifications = (
            get_consumer_notifications(
                user_id,
                10
            )
        )

        # ----------------------------------------------------
        # MARKET / MANDI
        # ----------------------------------------------------

        prices = []

        try:

            prices = execute_fetchall(
                conn,
                """
                SELECT *
                FROM market_prices
                ORDER BY
                    created_at DESC
                LIMIT 10
                """
            )

            prices = rows_to_dict(
                prices
            )

        except Exception as error:

            print(
                "[CONSUMER MARKET WARNING]",
                repr(error)
            )

            prices = []

        # ----------------------------------------------------
        # WEATHER
        # ----------------------------------------------------

        weather = get_consumer_weather()

        # ----------------------------------------------------
        # DASHBOARD STATISTICS
        # ----------------------------------------------------

        total_orders = len(orders)

        delivered_orders = 0

        pending_orders = 0

        try:

            for order in orders:

                status = str(
                    order.get(
                        "status",
                        ""
                    )
                ).lower().strip()

                if status in [
                    "delivered",
                    "completed"
                ]:

                    delivered_orders += 1

                elif status in [
                    "pending",
                    "confirmed",
                    "processing",
                    "shipped",
                    "out for delivery"
                ]:

                    pending_orders += 1

        except Exception as error:

            print(
                "[CONSUMER ORDER STATUS WARNING]",
                repr(error)
            )

        # ----------------------------------------------------
        # ACTIVITY SCORE
        # ----------------------------------------------------

        activity_score = min(
            100,
            (
                total_orders * 10
                + cart_count * 5
                + wishlist_count * 3
                + 20
            )
        )

        if activity_score >= 75:

            activity_status = "Highly Active"

        elif activity_score >= 45:

            activity_status = "Active"

        else:

            activity_status = "Getting Started"

        # ----------------------------------------------------
        # RENDER
        # ----------------------------------------------------

        return render_template(
            "consumer.html",

            name=(
                user.get("name")
                or session.get(
                    "name",
                    "Consumer"
                )
            ),

            user=user,

            consumer_profile=(
                consumer_profile
                or {}
            ),

            products=products,

            orders=orders,

            notifications=notifications,

            notification_count=notification_count,

            prices=prices,

            weather=weather,

            cart_count=cart_count,

            wishlist_count=wishlist_count,

            total_orders=total_orders,

            delivered_orders=delivered_orders,

            pending_orders=pending_orders,

            activity_score=activity_score,

            activity_status=activity_status
        )

    except Exception as error:

        print(
            "[CONSUMER DASHBOARD ERROR]",
            repr(error)
        )

        traceback.print_exc()

        if conn:
            conn.rollback()

        return render_template(
            "consumer.html",

            name=session.get(
                "name",
                "Consumer"
            ),

            user={},

            consumer_profile={},

            products=[],

            orders=[],

            notifications=[],

            notification_count=0,

            prices=[],

            weather=get_consumer_weather(),

            cart_count=0,

            wishlist_count=0,

            total_orders=0,

            delivered_orders=0,

            pending_orders=0,

            activity_score=20,

            activity_status="Getting Started"
        )

    finally:

        if conn:
            conn.close()


# ============================================================
# CONSUMER NOTIFICATION CENTER
# ============================================================

@consumer_bp.route(
    "/consumer/notifications"
)
def consumer_notifications():

    if not consumer_only():
        return login_redirect()

    user_id = session["user_id"]

    notifications = (
        get_consumer_notifications(
            user_id,
            200
        )
    )

    notification_count = (
        get_consumer_notification_count(
            user_id
        )
    )

    weather = get_consumer_weather()

    return render_template(
        "consumer_notifications.html",

        name=session.get(
            "name",
            "Consumer"
        ),

        notifications=notifications,

        notification_count=notification_count,

        weather=weather
    )


# ============================================================
# MARK ONE CONSUMER NOTIFICATION AS READ
# ============================================================

@consumer_bp.route(
    "/consumer/notifications/read/<int:notification_id>"
)
def consumer_mark_one_read(
    notification_id
):

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE consumer_notifications
                SET is_read = TRUE
                WHERE id = %s
                  AND consumer_id = %s
                """,
                (
                    notification_id,
                    session["user_id"]
                )
            )

        conn.commit()

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            "[CONSUMER MARK READ ERROR]",
            repr(error)
        )

    finally:

        if conn:
            conn.close()

    return redirect(
        url_for(
            "consumer.consumer_notifications"
        )
    )


# ============================================================
# MARK ALL CONSUMER NOTIFICATIONS AS READ
# ============================================================

@consumer_bp.route(
    "/consumer/notifications/read-all"
)
def consumer_mark_all_read():

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE consumer_notifications
                SET is_read = TRUE
                WHERE consumer_id = %s
                  AND is_read = FALSE
                """,
                (
                    session["user_id"],
                )
            )

        conn.commit()

        flash(
            "All consumer notifications marked as read.",
            "success"
        )

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            "[CONSUMER MARK ALL READ ERROR]",
            repr(error)
        )

        flash(
            "Unable to mark notifications as read.",
            "error"
        )

    finally:

        if conn:
            conn.close()

    return redirect(
        url_for(
            "consumer.consumer_notifications"
        )
    )


# ============================================================
# DELETE ONE CONSUMER NOTIFICATION
# ============================================================

@consumer_bp.route(
    "/consumer/notifications/delete/<int:notification_id>"
)
def consumer_delete_notification(
    notification_id
):

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM consumer_notifications
                WHERE id = %s
                  AND consumer_id = %s
                """,
                (
                    notification_id,
                    session["user_id"]
                )
            )

        conn.commit()

        flash(
            "Notification deleted.",
            "success"
        )

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            "[CONSUMER DELETE NOTIFICATION ERROR]",
            repr(error)
        )

        flash(
            "Unable to delete notification.",
            "error"
        )

    finally:

        if conn:
            conn.close()

    return redirect(
        url_for(
            "consumer.consumer_notifications"
        )
    )


# ============================================================
# DELETE ALL READ CONSUMER NOTIFICATIONS
# ============================================================

@consumer_bp.route(
    "/consumer/notifications/delete-read"
)
def consumer_delete_read_notifications():

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM consumer_notifications
                WHERE consumer_id = %s
                  AND is_read = TRUE
                """,
                (
                    session["user_id"],
                )
            )

        conn.commit()

        flash(
            "Read notifications cleared.",
            "success"
        )

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            "[CONSUMER DELETE READ ERROR]",
            repr(error)
        )

        flash(
            "Unable to clear notifications.",
            "error"
        )

    finally:

        if conn:
            conn.close()

    return redirect(
        url_for(
            "consumer.consumer_notifications"
        )
    )


# ============================================================
# TEST CONSUMER NOTIFICATION
# ============================================================

@consumer_bp.route(
    "/consumer/notifications/test"
)
def consumer_test_notification():

    if not consumer_only():
        return jsonify({
            "success": False,
            "message": "Please login as Consumer."
        }), 401

    success = create_consumer_notification(

        consumer_id=session["user_id"],

        title="Consumer Notification Test",

        message=(
            "Your KisanVision360+ consumer "
            "notification system is working correctly."
        ),

        notification_type="general"
    )

    if success:

        return jsonify({
            "success": True,
            "message": "Consumer test notification created."
        })

    return jsonify({
        "success": False,
        "message": "Unable to create consumer notification."
    }), 500


# ============================================================
# CONSUMER NOTIFICATION API
# ============================================================

@consumer_bp.route(
    "/api/consumer/notifications"
)
def api_consumer_notifications():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    user_id = session["user_id"]

    notifications = (
        get_consumer_notifications(
            user_id,
            200
        )
    )

    unread_count = (
        get_consumer_notification_count(
            user_id
        )
    )

    return jsonify({

        "success": True,

        "count": len(
            notifications
        ),

        "unread_count": unread_count,

        "notifications": notifications
    })


# ============================================================
# CONSUMER NOTIFICATION READ API
# ============================================================

@consumer_bp.route(
    "/api/consumer/notifications/read/<int:notification_id>",
    methods=["POST"]
)
def api_consumer_mark_read(
    notification_id
):

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE consumer_notifications
                SET is_read = TRUE
                WHERE id = %s
                  AND consumer_id = %s
                """,
                (
                    notification_id,
                    session["user_id"]
                )
            )

            updated = cur.rowcount

        conn.commit()

        return jsonify({

            "success": True,

            "updated": updated,

            "unread_count":
                get_consumer_notification_count(
                    session["user_id"]
                )
        })

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            "[CONSUMER READ API ERROR]",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to update notification."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# CONSUMER MARK ALL READ API
# ============================================================

@consumer_bp.route(
    "/api/consumer/notifications/read-all",
    methods=["POST"]
)
def api_consumer_mark_all_read():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None

    try:

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE consumer_notifications
                SET is_read = TRUE
                WHERE consumer_id = %s
                  AND is_read = FALSE
                """,
                (
                    session["user_id"],
                )
            )

            updated = cur.rowcount

        conn.commit()

        return jsonify({

            "success": True,

            "updated": updated,

            "unread_count": 0
        })

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            "[CONSUMER READ ALL API ERROR]",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to mark notifications."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# CONSUMER SUMMARY API
# ============================================================

@consumer_bp.route(
    "/api/consumer/summary"
)
def consumer_summary():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    user_id = session["user_id"]

    conn = None

    try:

        conn = get_db()

        orders_count = 0
        cart_count = 0
        wishlist_count = 0

        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        try:

            row = execute_fetchone(
                conn,
                """
                SELECT COUNT(*) AS count
                FROM orders
                WHERE consumer_id = %s
                """,
                (user_id,)
            )

            if row:

                orders_count = int(
                    row_to_dict(row).get(
                        "count",
                        0
                    ) or 0
                )

        except Exception:
            pass

        # ----------------------------------------------------
        # CART
        # ----------------------------------------------------

        try:

            row = execute_fetchone(
                conn,
                """
                SELECT COUNT(*) AS count
                FROM cart
                WHERE consumer_id = %s
                """,
                (user_id,)
            )

            if row:

                cart_count = int(
                    row_to_dict(row).get(
                        "count",
                        0
                    ) or 0
                )

        except Exception:
            pass

        # ----------------------------------------------------
        # WISHLIST
        # ----------------------------------------------------

        try:

            row = execute_fetchone(
                conn,
                """
                SELECT COUNT(*) AS count
                FROM wishlist
                WHERE consumer_id = %s
                """,
                (user_id,)
            )

            if row:

                wishlist_count = int(
                    row_to_dict(row).get(
                        "count",
                        0
                    ) or 0
                )

        except Exception:
            pass

        return jsonify({

            "success": True,

            "orders": orders_count,

            "cart": cart_count,

            "wishlist": wishlist_count,

            "notifications":
                get_consumer_notification_count(
                    user_id
                )
        })

    except Exception as error:

        print(
            "[CONSUMER SUMMARY ERROR]",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to load summary."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# CONSUMER PRODUCTS API
# ============================================================

@consumer_bp.route(
    "/api/consumer/products"
)
def consumer_products_api():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None

    try:

        conn = get_db()

        rows = execute_fetchall(
            conn,
            """
            SELECT
                p.*,
                u.name AS farmer_name
            FROM products p
            LEFT JOIN users u
                ON p.farmer_id = u.id
            WHERE LOWER(
                COALESCE(
                    p.status,
                    'active'
                )
            ) = 'active'
            AND COALESCE(
                p.quantity,
                0
            ) > 0
            ORDER BY
                p.created_at DESC,
                p.id DESC
            LIMIT 100
            """
        )

        products = rows_to_dict(
            rows
        )

        return jsonify({

            "success": True,

            "count": len(products),

            "products": products
        })

    except Exception as error:

        print(
            "[CONSUMER PRODUCTS API ERROR]",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to load products."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# CONSUMER LOCATION API
# ============================================================

@consumer_bp.route(
    "/api/consumer/location",
    methods=["POST"]
)
def consumer_location():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    city = str(
        data.get("city", "")
    ).strip()

    if not city:

        return jsonify({
            "success": False,
            "message": "City is required."
        }), 400

    session["city"] = city

    return jsonify({

        "success": True,

        "city": city
    })


# ============================================================
# CONSUMER LANGUAGE API
# ============================================================

@consumer_bp.route(
    "/api/consumer/language",
    methods=["POST"]
)
def consumer_language():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    language = str(
        data.get("language", "en")
    ).strip().lower()

    if not language:

        language = "en"

    session["language"] = language

    return jsonify({

        "success": True,

        "language": language
    })


# ============================================================
# CONSUMER HEALTH
# ============================================================

@consumer_bp.route(
    "/api/consumer/health"
)
def consumer_health():

    return jsonify({

        "success": True,

        "module": "consumer",

        "notifications": True,

        "timestamp":
            datetime.utcnow().isoformat()
            + "Z"
    })


# ============================================================
# CONSUMER MANDI PAGE
# ============================================================

@consumer_bp.route(
    "/consumer/mandi"
)
def consumer_mandi():

    if not consumer_only():
        return login_redirect()

    conn = None

    try:

        conn = get_db()

        prices = execute_fetchall(
            conn,
            """
            SELECT *
            FROM market_prices
            ORDER BY
                created_at DESC
            LIMIT 100
            """
        )

        prices = rows_to_dict(
            prices
        )

        return render_template(
            "market.html",

            name=session.get(
                "name",
                "Consumer"
            ),

            prices=prices
        )

    except Exception as error:

        print(
            "[CONSUMER MANDI ERROR]",
            repr(error)
        )

        return render_template(
            "market.html",

            name=session.get(
                "name",
                "Consumer"
            ),

            prices=[]
        )

    finally:

        if conn:
            conn.close()


# ============================================================
# CONSUMER MANDI API
# ============================================================

@consumer_bp.route(
    "/api/consumer/mandi"
)
def consumer_mandi_api():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = None

    try:

        conn = get_db()

        prices = execute_fetchall(
            conn,
            """
            SELECT *
            FROM market_prices
            ORDER BY
                created_at DESC
            LIMIT 200
            """
        )

        prices = rows_to_dict(
            prices
        )

        return jsonify({

            "success": True,

            "count": len(prices),

            "prices": prices
        })

    except Exception as error:

        print(
            "[CONSUMER MANDI API ERROR]",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to load mandi prices."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# CONSUMER MANDI SEARCH
# ============================================================

@consumer_bp.route(
    "/api/consumer/mandi/search"
)
def consumer_mandi_search():

    if not consumer_only():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    search = str(
        request.args.get(
            "q",
            ""
        )
    ).strip().lower()

    conn = None

    try:

        conn = get_db()

        rows = execute_fetchall(
            conn,
            """
            SELECT *
            FROM market_prices
            ORDER BY
                created_at DESC
            LIMIT 500
            """
        )

        prices = rows_to_dict(
            rows
        )

        if search:

            filtered = []

            for price in prices:

                text = " ".join(
                    str(value or "")
                    for value in price.values()
                ).lower()

                if search in text:

                    filtered.append(
                        price
                    )

            prices = filtered

        return jsonify({

            "success": True,

            "count": len(prices),

            "prices": prices
        })

    except Exception as error:

        print(
            "[CONSUMER MANDI SEARCH ERROR]",
            repr(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to search mandi prices."
        }), 500

    finally:

        if conn:
            conn.close()


# ============================================================
# CONSUMER MANDI HEALTH
# ============================================================

@consumer_bp.route(
    "/api/consumer/mandi/health"
)
def consumer_mandi_health():

    return jsonify({

        "success": True,

        "module": "consumer_mandi",

        "status": "active"
    })


# ============================================================
# END
# ============================================================
