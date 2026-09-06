# ============================================================
# KISANVISION360+ | FARMER DASHBOARD
# ============================================================
import os
import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash

logger = logging.getLogger(__name__)
farmer_bp = Blueprint("farmer", __name__)

def _db():
    try:
        from database.db import get_db_connection
        return get_db_connection()
    except Exception:
        return None

def _scalar(cur, query, params=()):
    try:
        cur.execute(query, params)
        row = cur.fetchone()
        if not row:
            return 0
        value = list(row.values())[0] if hasattr(row, "values") else row[0]
        return value or 0
    except Exception:
        return 0

def _weather():
    """Small dashboard weather helper; failure never breaks the dashboard."""
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    city = os.getenv("DEFAULT_CITY", "Nagpur").strip() or "Nagpur"
    if not key:
        return {"city": city, "country": "India", "description": "Weather service unavailable"}
    try:
        import requests
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": key, "units": "metric"},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        main, wind, clouds = data.get("main", {}), data.get("wind", {}), data.get("clouds", {})
        return {
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", "IN"),
            "temperature": round(main.get("temp", 0), 1),
            "feels_like": round(main.get("feels_like", 0), 1),
            "humidity": main.get("humidity", "--"),
            "wind": round(wind.get("speed", 0), 1),
            "clouds": clouds.get("all", "--"),
            "description": (data.get("weather") or [{}])[0].get("description", "Clear"),
            "icon": (data.get("weather") or [{}])[0].get("icon", "01d"),
        }
    except Exception as exc:
        logger.warning("Dashboard weather unavailable: %s", exc)
        return {"city": city, "country": "India", "description": "Weather information unavailable"}

@farmer_bp.route("/farmer")
def farmer():
    if not session.get("user_id") or str(session.get("role", "")).lower() != "farmer":
        return redirect(url_for("auth.login"))

    name = session.get("name", "Farmer")
    notification_count = 0
    stats = {"products": 0, "orders": 0, "crops": 0}

    conn = _db()
    if conn:
        try:
            cur = conn.cursor()
            uid = session.get("user_id")
            for table, key in [
                ("products", "products"), ("orders", "orders"), ("crops", "crops")
            ]:
                # Try common owner columns without making the dashboard dependent on one schema.
                for col in ("farmer_id", "user_id", "seller_id"):
                    try:
                        value = _scalar(cur, f"SELECT COUNT(*) AS count FROM {table} WHERE {col} = %s", (uid,))
                        if value:
                            stats[key] = int(value)
                            break
                    except Exception:
                        continue
            try:
                notification_count = int(_scalar(
                    cur,
                    "SELECT COUNT(*) AS count FROM notifications WHERE user_id = %s AND COALESCE(is_read, FALSE) = FALSE",
                    (uid,),
                ))
            except Exception:
                pass
        except Exception as exc:
            logger.warning("Farmer dashboard DB stats unavailable: %s", exc)
        finally:
            try: conn.close()
            except Exception: pass

    return render_template(
        "farmer.html",
        name=name,
        notification_count=notification_count,
        weather_data=_weather(),
        **stats,
    )

# Compatibility aliases used by older links.
@farmer_bp.route("/farmer/dashboard")
def farmer_dashboard():
    return farmer()

