from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
import sqlite3
import os

crop_bp = Blueprint("crop", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(
    BASE_DIR,
    "instance",
    "kisanvision360.db"
)


# =========================================================
# DATABASE
# =========================================================

def get_crop_db():

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# CREATE / FIX CROP TABLE
# =========================================================

def init_crop_table():

    conn = get_crop_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER,
            crop_name TEXT NOT NULL,
            sowing_date TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            soil_type TEXT,
            irrigation_method TEXT,
            farm_area REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Fix old crops table if columns are missing
    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(crops)"
        ).fetchall()
    ]

    if "farmer_id" not in columns:
        conn.execute(
            "ALTER TABLE crops ADD COLUMN farmer_id INTEGER"
        )

    if "duration_days" not in columns:
        conn.execute(
            "ALTER TABLE crops ADD COLUMN duration_days INTEGER DEFAULT 0"
        )

    if "soil_type" not in columns:
        conn.execute(
            "ALTER TABLE crops ADD COLUMN soil_type TEXT"
        )

    if "irrigation_method" not in columns:
        conn.execute(
            "ALTER TABLE crops ADD COLUMN irrigation_method TEXT"
        )

    if "farm_area" not in columns:
        conn.execute(
            "ALTER TABLE crops ADD COLUMN farm_area REAL DEFAULT 0"
        )

    conn.commit()
    conn.close()


# =========================================================
# GROWTH STAGE
# =========================================================

def get_growth_stage(age, duration):

    if duration <= 0:
        return "Unknown"

    percentage = (age / duration) * 100

    if percentage <= 10:
        return "Germination"

    elif percentage <= 25:
        return "Seedling"

    elif percentage <= 55:
        return "Vegetative Growth"

    elif percentage <= 75:
        return "Flowering"

    elif percentage <= 90:
        return "Fruit / Grain Development"

    elif percentage < 100:
        return "Maturity"

    return "Harvest Ready"


# =========================================================
# CROP DETAILS
# =========================================================

@crop_bp.route("/crop-details", methods=["GET", "POST"])
def crop_details():

    init_crop_table()

    farmer_id = session.get("user_id")

    # =====================================================
    # SAVE CROP
    # =====================================================

    if request.method == "POST":

        crop_name = request.form.get(
            "crop_name", ""
        ).strip()

        sowing_date = request.form.get(
            "sowing_date", ""
        )

        duration_days = request.form.get(
            "duration_days", ""
        )

        soil_type = request.form.get(
            "soil_type", ""
        )

        irrigation_method = request.form.get(
            "irrigation_method", ""
        )

        farm_area = request.form.get(
            "farm_area", "0"
        )

        if not crop_name or not sowing_date or not duration_days:

            flash(
                "Please enter all required details.",
                "danger"
            )

            return redirect(
                url_for("crop.crop_details")
            )

        try:

            duration_days = int(duration_days)
            farm_area = float(farm_area or 0)

            datetime.strptime(
                sowing_date,
                "%Y-%m-%d"
            )

        except ValueError:

            flash(
                "Invalid crop details.",
                "danger"
            )

            return redirect(
                url_for("crop.crop_details")
            )

        conn = get_crop_db()

        conn.execute(
            """
            INSERT INTO crops
            (
                farmer_id,
                crop_name,
                sowing_date,
                duration_days,
                soil_type,
                irrigation_method,
                farm_area
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                farmer_id,
                crop_name,
                sowing_date,
                duration_days,
                soil_type,
                irrigation_method,
                farm_area
            )
        )

        conn.commit()
        conn.close()

        flash(
            "Crop saved successfully!",
            "success"
        )

        return redirect(
            url_for("crop.crop_details")
        )

    # =====================================================
    # GET CROPS
    # =====================================================

    conn = get_crop_db()

    if farmer_id:

        crops = conn.execute(
            """
            SELECT *
            FROM crops
            WHERE farmer_id = ?
            ORDER BY id DESC
            """,
            (farmer_id,)
        ).fetchall()

    else:

        crops = []

    conn.close()

    # =====================================================
    # CROP CALCULATION
    # =====================================================

    crop_data = []

    today = datetime.now().date()

    for crop in crops:

        try:

            sowing = datetime.strptime(
                crop["sowing_date"],
                "%Y-%m-%d"
            ).date()

        except (ValueError, TypeError):

            continue

        age = max(
            0,
            (today - sowing).days
        )

        duration = int(
            crop["duration_days"] or 0
        )

        harvest = sowing + timedelta(
            days=duration
        )

        remaining = max(
            0,
            (harvest - today).days
        )

        progress = (
            int((age / duration) * 100)
            if duration > 0
            else 0
        )

        progress = min(
            100,
            progress
        )

        crop_data.append({

            "id": crop["id"],

            "crop_name": crop["crop_name"],

            "sowing_date": crop["sowing_date"],

            "duration_days": duration,

            "soil_type": crop["soil_type"],

            "irrigation_method":
                crop["irrigation_method"],

            "farm_area":
                crop["farm_area"],

            "age": age,

            "remaining": remaining,

            "progress": progress,

            "stage": get_growth_stage(
                age,
                duration
            ),

            "harvest_date":
                harvest.strftime("%d %b %Y")
        })

    # =====================================================
    # PAGE
    # =====================================================

    return render_template(
        "crop_details.html",
        crops=crop_data,
        name=session.get(
            "name",
            "Farmer"
        )
    )