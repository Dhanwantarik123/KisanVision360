# ============================================================
# KISANVISION360+ — NOTIFICATIONS ROUTE
# File: routes/notifications.py
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

from services.notification_service import create_smart_notification, ensure_notification_schema


# ============================================================
# BLUEPRINT
# ============================================================

notifications_bp = Blueprint("notifications", __name__)

logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================

def get_user_id():
    """
    Get logged-in user ID safely.
    Supports both user_id and id session keys.
    """

    user_id = (
        session.get("user_id")
        or session.get("id")
    )

    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def get_role():
    """
    Get current logged-in role.
    """

    return str(
        session.get("role", "")
    ).strip().lower()


def login_required():
    """
    Check whether a valid user ID exists.
    """

    return bool(get_user_id())


# ============================================================
# DATABASE SETUP
# ============================================================

def ensure_notifications_table():
    """
    Ensure the notifications table exists and contains
    all columns required by this module.

    PostgreSQL / Supabase compatible.
    """

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        # ----------------------------------------------------
        # Create table if it does not exist
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                notification_type VARCHAR(80)
                    DEFAULT 'general',
                is_read BOOLEAN
                    DEFAULT FALSE,
                date TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,
                farmer_id BIGINT
            )
            """
        )

        # ----------------------------------------------------
        # Existing installations may have an older schema.
        # Add missing columns safely.
        # ----------------------------------------------------

        cursor.execute(
            """
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS user_id BIGINT
            """
        )

        cursor.execute(
            """
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS title VARCHAR(255)
            """
        )

        cursor.execute(
            """
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS message TEXT
            """
        )

        cursor.execute(
            """
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS notification_type
            VARCHAR(80) DEFAULT 'general'
            """
        )

        cursor.execute(
            """
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS is_read
            BOOLEAN DEFAULT FALSE
            """
        )

        cursor.execute(
            """
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS date
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
        )

        cursor.execute(
            """
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
        )

        cursor.execute(
            """
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS farmer_id BIGINT
            """
        )

        # ----------------------------------------------------
        # Fix NULL defaults in old records
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE notifications
            SET is_read = FALSE
            WHERE is_read IS NULL
            """
        )

        cursor.execute(
            """
            UPDATE notifications
            SET notification_type = 'general'
            WHERE notification_type IS NULL
            """
        )

        cursor.execute(
            """
            UPDATE notifications
            SET date = COALESCE(date, created_at, CURRENT_TIMESTAMP)
            WHERE date IS NULL
            """
        )

        cursor.execute(
            """
            UPDATE notifications
            SET created_at = COALESCE(
                created_at,
                date,
                CURRENT_TIMESTAMP
            )
            WHERE created_at IS NULL
            """
        )

        # ----------------------------------------------------
        # Indexes
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_notifications_user
            ON notifications(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_notifications_read
            ON notifications(user_id, is_read)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_notifications_date
            ON notifications(date DESC)
            """
        )

        conn.commit()
        # Add advanced notification fields/indexes without breaking older installs.
        ensure_notification_schema()

    except Exception as exc:

        if conn:
            conn.rollback()

        logger.exception(
            "Notification table setup failed: %s",
            exc,
        )

        raise

    finally:

        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# CURSOR / ROW HELPERS
# ============================================================

NOTIFICATION_COLUMNS = [
    "id",
    "user_id",
    "title",
    "message",
    "notification_type",
    "category",
    "priority",
    "is_read",
    "is_archived",
    "action_url",
    "related_id",
    "event_id",
    "date",
    "created_at",
    "expires_at",
    "farmer_id",
]


def row_to_dict(row, columns):
    """
    Convert PostgreSQL tuple rows or dictionary rows
    into a normal dictionary.
    """

    if row is None:
        return None

    if isinstance(row, dict):
        return dict(row)

    return dict(
        zip(columns, row)
    )


def serialize_notification(row):
    """
    Convert PostgreSQL datetime values to JSON-safe strings.
    """

    item = row_to_dict(
        row,
        NOTIFICATION_COLUMNS,
    )

    if not item:
        return None

    for field in (
        "date",
        "created_at",
    ):

        value = item.get(field)

        if isinstance(
            value,
            datetime,
        ):
            item[field] = value.isoformat()

    item["is_read"] = bool(
        item.get(
            "is_read",
            False,
        )
    )

    return item


# ============================================================
# FETCH NOTIFICATIONS
# ============================================================

def fetch_notifications(
    user_id,
    limit=100,
    unread_only=False,
):
    """
    Fetch notifications for the logged-in user.

    Supports both:
        user_id
        farmer_id

    This keeps compatibility with older records.
    """

    conn = None
    cursor = None

    try:

        ensure_notifications_table()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            limit = int(limit)
        except (
            TypeError,
            ValueError,
        ):
            limit = 100

        limit = max(
            1,
            min(limit, 200),
        )

        # ----------------------------------------------------
        # Unread only
        # ----------------------------------------------------

        if unread_only:

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    title,
                    message,
                    notification_type,
                    category,
                    priority,
                    is_read,
                    is_archived,
                    action_url,
                    related_id,
                    event_id,
                    date,
                    created_at,
                    expires_at,
                    farmer_id
                FROM notifications
                WHERE
                    (
                        user_id = %s
                        OR farmer_id = %s
                    )
                    AND COALESCE(
                        is_read,
                        FALSE
                    ) = FALSE
                ORDER BY
                    COALESCE(
                        date,
                        created_at
                    ) DESC
                LIMIT %s
                """,
                (
                    user_id,
                    user_id,
                    limit,
                ),
            )

        # ----------------------------------------------------
        # All notifications
        # ----------------------------------------------------

        else:

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    title,
                    message,
                    notification_type,
                    category,
                    priority,
                    is_read,
                    is_archived,
                    action_url,
                    related_id,
                    event_id,
                    date,
                    created_at,
                    expires_at,
                    farmer_id
                FROM notifications
                WHERE
                    user_id = %s
                    OR farmer_id = %s
                ORDER BY
                    COALESCE(
                        date,
                        created_at
                    ) DESC
                LIMIT %s
                """,
                (
                    user_id,
                    user_id,
                    limit,
                ),
            )

        rows = cursor.fetchall()

        return [
            serialize_notification(row)
            for row in rows
        ]

    except Exception as exc:

        logger.exception(
            "Unable to fetch notifications: %s",
            exc,
        )

        return []

    finally:

        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# MAIN NOTIFICATIONS PAGE
# ============================================================

@notifications_bp.route(
    "/notifications",
    methods=["GET"],
)
def notifications():

    if not login_required():

        flash(
            "Please login to view notifications.",
            "warning",
        )

        return redirect(
            url_for("auth.login")
        )

    try:

        user_id = get_user_id()

        notification_list = fetch_notifications(
            user_id=user_id,
            limit=100,
        )

        unread_count = sum(
            1
            for notification in notification_list
            if not notification.get(
                "is_read",
                False,
            )
        )

        return render_template(
            "notifications.html",
            notifications=notification_list,
            unread_count=unread_count,
            role=get_role(),
            language=session.get(
                "language",
                "en",
            ),
        )

    except Exception as exc:

        logger.exception(
            "Notifications page error: %s",
            exc,
        )

        return render_template(
            "notifications.html",
            notifications=[],
            unread_count=0,
            role=get_role(),
            language=session.get(
                "language",
                "en",
            ),
            error=(
                "Unable to load notifications "
                "right now."
            ),
        )


# ============================================================
# API — GET NOTIFICATIONS
# ============================================================

@notifications_bp.route(
    "/api/notifications",
    methods=["GET"],
)
def api_notifications():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required.",
        }), 401

    try:

        user_id = get_user_id()

        limit = request.args.get(
            "limit",
            100,
        )

        try:
            limit = int(limit)
        except (
            TypeError,
            ValueError,
        ):
            limit = 100

        unread_only = (
            str(
                request.args.get(
                    "unread_only",
                    "false",
                )
            ).lower()
            in {
                "true",
                "1",
                "yes",
            }
        )

        notification_list = fetch_notifications(
            user_id=user_id,
            limit=limit,
            unread_only=unread_only,
        )

        unread_count = sum(
            1
            for item in notification_list
            if not item.get(
                "is_read",
                False,
            )
        )

        return jsonify({
            "success": True,
            "notifications": notification_list,
            "count": len(notification_list),
            "unread_count": unread_count,
        })

    except Exception as exc:

        logger.exception(
            "Notification API error: %s",
            exc,
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to load notifications."
            ),
            "notifications": [],
            "count": 0,
            "unread_count": 0,
        }), 500


# ============================================================
# API — UNREAD COUNT
# ============================================================

@notifications_bp.route(
    "/api/notifications/count",
    methods=["GET"],
)
def notification_count():

    if not login_required():

        return jsonify({
            "success": False,
            "count": 0,
            "unread_count": 0,
        }), 401

    conn = None
    cursor = None

    try:

        ensure_notifications_table()

        user_id = get_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM notifications
            WHERE
                (
                    user_id = %s
                    OR farmer_id = %s
                )
                AND COALESCE(
                    is_read,
                    FALSE
                ) = FALSE
            """,
            (
                user_id,
                user_id,
            ),
        )

        row = cursor.fetchone()

        if isinstance(row, dict):

            count = next(
                iter(row.values()),
                0,
            )

        else:

            count = row[0] if row else 0

        count = int(
            count or 0
        )

        return jsonify({
            "success": True,
            "count": count,
            "unread_count": count,
        })

    except Exception as exc:

        logger.exception(
            "Notification count error: %s",
            exc,
        )

        return jsonify({
            "success": False,
            "count": 0,
            "unread_count": 0,
        }), 500

    finally:

        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# API — MARK ONE AS READ
# ============================================================

@notifications_bp.route(
    "/api/notifications/<int:notification_id>/read",
    methods=["POST", "PUT"],
)
def mark_notification_read(
    notification_id,
):

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required.",
        }), 401

    conn = None
    cursor = None

    try:

        ensure_notifications_table()

        user_id = get_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE notifications
            SET is_read = TRUE
            WHERE
                id = %s
                AND (
                    user_id = %s
                    OR farmer_id = %s
                )
            """,
            (
                notification_id,
                user_id,
                user_id,
            ),
        )

        updated = cursor.rowcount

        conn.commit()

        if updated == 0:

            return jsonify({
                "success": False,
                "message": (
                    "Notification not found."
                ),
            }), 404

        return jsonify({
            "success": True,
            "message": (
                "Notification marked as read."
            ),
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        logger.exception(
            "Mark notification read error: %s",
            exc,
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to update notification."
            ),
        }), 500

    finally:

        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# API — MARK ALL AS READ
# ============================================================

@notifications_bp.route(
    "/api/notifications/read-all",
    methods=["POST", "PUT"],
)
def mark_all_read():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required.",
        }), 401

    conn = None
    cursor = None

    try:

        ensure_notifications_table()

        user_id = get_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE notifications
            SET is_read = TRUE
            WHERE
                (
                    user_id = %s
                    OR farmer_id = %s
                )
                AND COALESCE(
                    is_read,
                    FALSE
                ) = FALSE
            """,
            (
                user_id,
                user_id,
            ),
        )

        updated = cursor.rowcount

        conn.commit()

        return jsonify({
            "success": True,
            "message": (
                "All notifications marked as read."
            ),
            "updated": updated,
            "unread_count": 0,
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        logger.exception(
            "Mark all notifications read error: %s",
            exc,
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to update notifications."
            ),
        }), 500

    finally:

        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# API — DELETE ONE NOTIFICATION
# ============================================================

@notifications_bp.route(
    "/api/notifications/<int:notification_id>",
    methods=["DELETE"],
)
def delete_notification(
    notification_id,
):

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required.",
        }), 401

    conn = None
    cursor = None

    try:

        ensure_notifications_table()

        user_id = get_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM notifications
            WHERE
                id = %s
                AND (
                    user_id = %s
                    OR farmer_id = %s
                )
            """,
            (
                notification_id,
                user_id,
                user_id,
            ),
        )

        deleted = cursor.rowcount

        conn.commit()

        if deleted == 0:

            return jsonify({
                "success": False,
                "message": (
                    "Notification not found."
                ),
            }), 404

        return jsonify({
            "success": True,
            "message": (
                "Notification deleted."
            ),
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        logger.exception(
            "Delete notification error: %s",
            exc,
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to delete notification."
            ),
        }), 500

    finally:

        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# API — DELETE ALL READ NOTIFICATIONS
# ============================================================

@notifications_bp.route(
    "/api/notifications/clear-read",
    methods=["DELETE", "POST"],
)
def clear_read_notifications():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required.",
        }), 401

    conn = None
    cursor = None

    try:

        ensure_notifications_table()

        user_id = get_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM notifications
            WHERE
                (
                    user_id = %s
                    OR farmer_id = %s
                )
                AND COALESCE(
                    is_read,
                    FALSE
                ) = TRUE
            """,
            (
                user_id,
                user_id,
            ),
        )

        deleted = cursor.rowcount

        conn.commit()

        return jsonify({
            "success": True,
            "message": (
                "Read notifications cleared."
            ),
            "deleted": deleted,
        })

    except Exception as exc:

        if conn:
            conn.rollback()

        logger.exception(
            "Clear notifications error: %s",
            exc,
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to clear notifications."
            ),
        }), 500

    finally:

        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# INTERNAL FUNCTION — CREATE NOTIFICATION
# ============================================================

def create_notification(
    user_id,
    title,
    message,
    notification_type="general",
    category=None,
    priority="NORMAL",
    action_url=None,
    related_id=None,
    event_id=None,
    expires_at=None,
):
    """Central notification creator used by the whole application."""
    return bool(create_smart_notification(
        user_id=user_id, title=title, message=message,
        notification_type=notification_type, category=category,
        priority=priority, action_url=action_url, related_id=related_id,
        event_id=event_id, expires_at=expires_at
    ))


# ============================================================
# API — CREATE NOTIFICATION
# ============================================================

@notifications_bp.route(
    "/api/notifications/create",
    methods=["POST"],
)
def api_create_notification():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required.",
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    title = str(
        data.get(
            "title",
            "",
        )
    ).strip()

    message = str(
        data.get(
            "message",
            "",
        )
    ).strip()

    notification_type = str(
        data.get(
            "notification_type",
            "general",
        )
    ).strip()

    if not title or not message:

        return jsonify({
            "success": False,
            "message": (
                "Title and message are required."
            ),
        }), 400

    success = create_notification(
        user_id=get_user_id(),
        title=title,
        message=message,
        notification_type=notification_type,
    )

    if not success:

        return jsonify({
            "success": False,
            "message": (
                "Unable to create notification."
            ),
        }), 500

    return jsonify({
        "success": True,
        "message": (
            "Notification created successfully."
        ),
    }), 201


# ============================================================
# API — TEST NOTIFICATION
# ============================================================

@notifications_bp.route(
    "/api/notifications/test",
    methods=["POST"],
)
def test_notification():
    """
    Create a test notification for the
    currently logged-in user.

    Used by the Test Notification button
    on notifications.html.
    """

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required.",
        }), 401

    user_id = get_user_id()

    success = create_notification(
        user_id=user_id,
        title="KisanVision360+ Test Notification",
        message=(
            "Your notification system is "
            "working correctly."
        ),
        notification_type="system",
    )

    if not success:

        return jsonify({
            "success": False,
            "message": (
                "Unable to create test notification."
            ),
        }), 500

    return jsonify({
        "success": True,
        "message": (
            "Test notification created "
            "successfully."
        ),
    }), 201


@notifications_bp.route("/api/notifications/advanced", methods=["GET"])
def advanced_notifications():
    if not login_required():
        return jsonify(success=False, message="Login required."), 401
    try:
        ensure_notification_schema()
        user_id=get_user_id(); conn=get_db_connection(); cur=conn.cursor()
        category=request.args.get("category", "").strip()
        priority=request.args.get("priority", "").strip().upper()
        search=request.args.get("search", "").strip()
        unread=request.args.get("unread", "").lower() in {"1","true","yes"}
        where=["user_id=%s", "COALESCE(is_archived,FALSE)=FALSE"]; params=[user_id]
        if category: where.append("LOWER(category)=LOWER(%s)"); params.append(category)
        if priority: where.append("priority=%s"); params.append(priority)
        if search: where.append("(title ILIKE %s OR message ILIKE %s OR category ILIKE %s OR notification_type ILIKE %s)"); q=f"%{search}%"; params += [q,q,q,q]
        if unread: where.append("COALESCE(is_read,FALSE)=FALSE")
        cur.execute("SELECT id,title,message,notification_type,category,priority,is_read,is_archived,action_url,related_id,event_id,created_at,expires_at FROM notifications WHERE " + " AND ".join(where) + " ORDER BY created_at DESC LIMIT 200", tuple(params))
        rows=cur.fetchall(); cur.close(); conn.close()
        return jsonify(success=True, notifications=[dict(r) for r in rows], count=len(rows))
    except Exception as e:
        return jsonify(success=False,message=str(e)),500

@notifications_bp.route("/api/notifications/<int:notification_id>/unread", methods=["POST"])
def mark_notification_unread(notification_id):
    if not login_required(): return jsonify(success=False,message="Login required."),401
    conn=get_db_connection(); cur=conn.cursor()
    cur.execute("UPDATE notifications SET is_read=FALSE WHERE id=%s AND user_id=%s",(notification_id,get_user_id())); updated=cur.rowcount; conn.commit(); cur.close(); conn.close()
    return jsonify(success=updated>0, updated=updated)

@notifications_bp.route("/api/notifications/<int:notification_id>/archive", methods=["POST"])
def archive_notification(notification_id):
    if not login_required(): return jsonify(success=False,message="Login required."),401
    conn=get_db_connection(); cur=conn.cursor(); cur.execute("UPDATE notifications SET is_archived=TRUE WHERE id=%s AND user_id=%s",(notification_id,get_user_id())); updated=cur.rowcount; conn.commit(); cur.close(); conn.close()
    return jsonify(success=updated>0, updated=updated)

@notifications_bp.route("/api/notifications/preferences", methods=["GET","PUT"])
def notification_preferences():
    if not login_required(): return jsonify(success=False,message="Login required."),401
    uid=get_user_id(); conn=get_db_connection(); cur=conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS notification_preferences(
        user_id BIGINT PRIMARY KEY, weather_enabled BOOLEAN DEFAULT TRUE, crop_enabled BOOLEAN DEFAULT TRUE,
        disease_enabled BOOLEAN DEFAULT TRUE, irrigation_enabled BOOLEAN DEFAULT TRUE, market_enabled BOOLEAN DEFAULT TRUE,
        marketplace_enabled BOOLEAN DEFAULT TRUE, finance_enabled BOOLEAN DEFAULT TRUE, scheme_enabled BOOLEAN DEFAULT TRUE,
        ai_enabled BOOLEAN DEFAULT TRUE, sos_enabled BOOLEAN DEFAULT TRUE, system_enabled BOOLEAN DEFAULT TRUE,
        quiet_hours_enabled BOOLEAN DEFAULT FALSE, quiet_start TIME, quiet_end TIME)""")
    if request.method=="PUT":
        data=request.get_json(silent=True) or {}
        cols=["weather_enabled","crop_enabled","disease_enabled","irrigation_enabled","market_enabled","marketplace_enabled","finance_enabled","scheme_enabled","ai_enabled","sos_enabled","system_enabled","quiet_hours_enabled"]
        vals=[bool(data.get(c,True)) for c in cols]
        cur.execute("INSERT INTO notification_preferences(user_id,"+",".join(cols)+") VALUES(%s,"+",".join(["%s"]*len(cols))+ ") ON CONFLICT(user_id) DO UPDATE SET "+",".join([f"{c}=EXCLUDED.{c}" for c in cols]),[uid]+vals); conn.commit()
    cur.execute("SELECT * FROM notification_preferences WHERE user_id=%s",(uid,)); row=cur.fetchone(); conn.commit(); cur.close(); conn.close()
    return jsonify(success=True, preferences=dict(row) if row else {})


# ============================================================
# HEALTH CHECK
# ============================================================

@notifications_bp.route(
    "/api/notifications/health",
    methods=["GET"],
)
def notifications_health():

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1"
        )

        cursor.fetchone()

        return jsonify({
            "success": True,
            "service": "notifications",
            "database": "connected",
            "status": "healthy",
            "timestamp": (
                datetime.utcnow().isoformat()
            ),
        })

    except Exception as exc:

        logger.exception(
            "Notification health check failed: %s",
            exc,
        )

        return jsonify({
            "success": False,
            "service": "notifications",
            "database": "disconnected",
            "status": "error",
            "error": str(exc),
        }), 500

    finally:

        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "notifications_bp",
    "create_notification",
    "test_notification",
]
