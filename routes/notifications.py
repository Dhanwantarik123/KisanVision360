from flask import Blueprint, render_template, session, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime


notification_bp = Blueprint(
    "notifications",
    __name__
)


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DB_PATH = os.path.join(
    BASE_DIR,
    "instance",
    "kisanvision360.db"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    os.makedirs(
        os.path.dirname(DB_PATH),
        exist_ok=True
    )

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# CREATE TABLE
# =========================================================

def init_notification_table():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            farmer_id INTEGER,

            crop_id INTEGER,

            title TEXT NOT NULL,

            message TEXT NOT NULL,

            notification_type TEXT DEFAULT 'general',

            is_read INTEGER DEFAULT 0,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()

    conn.close()


# =========================================================
# CREATE NOTIFICATION
# =========================================================

def create_notification(
    farmer_id,
    title,
    message,
    notification_type="general",
    crop_id=None
):

    init_notification_table()

    conn = get_db()

    conn.execute(
        """
        INSERT INTO notifications
        (
            farmer_id,
            crop_id,
            title,
            message,
            notification_type
        )

        VALUES (?, ?, ?, ?, ?)
        """,

        (
            farmer_id,
            crop_id,
            title,
            message,
            notification_type
        )
    )

    conn.commit()

    conn.close()


# =========================================================
# NOTIFICATION PAGE
# =========================================================

@notification_bp.route("/notifications")
def notifications():

    init_notification_table()

    farmer_id = (
        session.get("user_id")
        or session.get("farmer_id")
    )

    conn = get_db()

    if farmer_id:

        data = conn.execute(
            """
            SELECT *
            FROM notifications

            WHERE farmer_id = ?

            ORDER BY id DESC
            """,
            (farmer_id,)
        ).fetchall()

    else:

        data = conn.execute(
            """
            SELECT *
            FROM notifications

            ORDER BY id DESC
            """
        ).fetchall()

    # Count unread
    if farmer_id:

        unread_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM notifications

            WHERE farmer_id = ?
            AND is_read = 0
            """,
            (farmer_id,)
        ).fetchone()[0]

    else:

        unread_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM notifications

            WHERE is_read = 0
            """
        ).fetchone()[0]

    conn.close()

    return render_template(
        "notifications.html",

        notifications=data,

        notification_count=unread_count,

        name=session.get(
            "name",
            "Farmer"
        )
    )


# =========================================================
# MARK ALL AS READ
# =========================================================

@notification_bp.route(
    "/notifications/read-all"
)
def mark_all_read():

    farmer_id = (
        session.get("user_id")
        or session.get("farmer_id")
    )

    if not farmer_id:

        return redirect(
            url_for("notifications.notifications")
        )

    conn = get_db()

    conn.execute(
        """
        UPDATE notifications

        SET is_read = 1

        WHERE farmer_id = ?
        """,
        (farmer_id,)
    )

    conn.commit()

    conn.close()

    return redirect(
        url_for("notifications.notifications")
    )


# =========================================================
# MARK ONE NOTIFICATION READ
# =========================================================

@notification_bp.route(
    "/notifications/read/<int:notification_id>"
)
def mark_one_read(notification_id):

    farmer_id = (
        session.get("user_id")
        or session.get("farmer_id")
    )

    conn = get_db()

    conn.execute(
        """
        UPDATE notifications

        SET is_read = 1

        WHERE id = ?

        AND farmer_id = ?
        """,
        (
            notification_id,
            farmer_id
        )
    )

    conn.commit()

    conn.close()

    return redirect(
        url_for("notifications.notifications")
    )


# =========================================================
# DELETE ONE NOTIFICATION
# =========================================================

@notification_bp.route(
    "/notifications/delete/<int:notification_id>"
)
def delete_notification(notification_id):

    farmer_id = (
        session.get("user_id")
        or session.get("farmer_id")
    )

    conn = get_db()

    conn.execute(
        """
        DELETE FROM notifications

        WHERE id = ?

        AND farmer_id = ?
        """,
        (
            notification_id,
            farmer_id
        )
    )

    conn.commit()

    conn.close()

    return redirect(
        url_for("notifications.notifications")
    )


# =========================================================
# TEST NOTIFICATION FROM FLASK
# =========================================================

@notification_bp.route(
    "/notifications/test"
)
def test_notification():

    farmer_id = (
        session.get("user_id")
        or session.get("farmer_id")
    )

    if farmer_id:

        create_notification(
            farmer_id=farmer_id,

            title="🌾 KisanVision360",

            message=(
                "Weather and farming notifications "
                "are working successfully."
            ),

            notification_type="success"
        )

    return redirect(
        url_for("notifications.notifications")
    )