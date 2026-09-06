
# ============================================================
# KISANVISION360+ | FARMER DASHBOARD
# ============================================================

import os
import logging

from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
)

logger = logging.getLogger(__name__)

farmer_bp = Blueprint("farmer", __name__)


# ============================================================
# LOAD .ENV
# ============================================================

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass


# ============================================================
# DATABASE
# ============================================================

def _db():
    """
    Use existing database/db.py.

    DATABASE_URL comes from .env.
    """
    try:
        from database.db import get_db_connection
        return get_db_connection()

    except Exception as exc:
        logger.warning(
            "Database connection unavailable: %s",
            exc
        )
        return None


# ============================================================
# SCALAR DATABASE HELPER
# ============================================================

def _scalar(cur, query, params=()):
    """
    Execute a COUNT/SUM style query safely.
    """

    try:

        cur.execute(
            query,
            params
        )

        row = cur.fetchone()

        if not row:
            return 0

        if hasattr(row, "values"):
            value = list(row.values())[0]
        else:
            value = row[0]

        return value or 0

    except Exception as exc:

        logger.debug(
            "Scalar query failed: %s",
            exc
        )

        return 0


# ============================================================
# WEATHER
# ============================================================

def _weather():
    """
    Get live weather from OpenWeather.

    Configuration is read from .env:

        OPENWEATHER_API_KEY=your_api_key
        DEFAULT_CITY=Nagpur

    Failure never breaks the dashboard.
    """

    city = (
        os.getenv(
            "DEFAULT_CITY",
            "Nagpur"
        ).strip()
        or "Nagpur"
    )

    api_key = (
        os.getenv(
            "OPENWEATHER_API_KEY",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # Default weather response
    # --------------------------------------------------------

    default_weather = {
        "success": False,

        "city": city,

        "country": "IN",

        "temperature": 0,

        "feels_like": 0,

        "humidity": 0,

        "wind": 0,

        "wind_speed": 0,

        "clouds": 0,

        "cloud_cover": 0,

        "pressure": 0,

        "visibility": 0,

        "rainfall": 0,

        "description":
            "Weather service unavailable",

        "icon": "01d",

        "icon_code": "01d",

        "risk": "Unknown",

        "advice": "",
    }

    # --------------------------------------------------------
    # API KEY CHECK
    # --------------------------------------------------------

    if not api_key:

        logger.warning(
            "OPENWEATHER_API_KEY is missing"
        )

        return default_weather

    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    try:

        import requests

        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",

            params={
                "q": city,
                "appid": api_key,
                "units": "metric",
            },

            timeout=8,
        )

        response.raise_for_status()

        data = response.json()

        # ----------------------------------------------------
        # MAIN WEATHER DATA
        # ----------------------------------------------------

        main = data.get(
            "main",
            {}
        )

        wind = data.get(
            "wind",
            {}
        )

        clouds = data.get(
            "clouds",
            {}
        )

        weather_list = data.get(
            "weather",
            []
        )

        weather_item = (
            weather_list[0]
            if weather_list
            else {}
        )

        # ----------------------------------------------------
        # TEMPERATURE
        # ----------------------------------------------------

        temperature = main.get(
            "temp",
            0
        )

        feels_like = main.get(
            "feels_like",
            0
        )

        # ----------------------------------------------------
        # HUMIDITY
        # ----------------------------------------------------

        humidity = main.get(
            "humidity",
            0
        )

        # ----------------------------------------------------
        # WIND
        # ----------------------------------------------------

        wind_speed = wind.get(
            "speed",
            0
        )

        # ----------------------------------------------------
        # CLOUDS
        # ----------------------------------------------------

        cloud_cover = clouds.get(
            "all",
            0
        )

        # ----------------------------------------------------
        # PRESSURE
        # ----------------------------------------------------

        pressure = main.get(
            "pressure",
            0
        )

        # ----------------------------------------------------
        # VISIBILITY
        #
        # OpenWeather returns meters.
        # Convert to kilometres.
        # ----------------------------------------------------

        visibility_m = data.get(
            "visibility",
            0
        )

        visibility_km = round(
            float(visibility_m) / 1000,
            1
        ) if visibility_m else 0

        # ----------------------------------------------------
        # RAINFALL
        #
        # OpenWeather can return:
        # rain.1h
        # rain.3h
        # ----------------------------------------------------

        rain = data.get(
            "rain",
            {}
        )

        rainfall = rain.get(
            "1h",
            0
        )

        if rainfall is None:

            rainfall = rain.get(
                "3h",
                0
            )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        description = (
            weather_item.get(
                "description",
                "Clear"
            )
        )

        # ----------------------------------------------------
        # ICON
        # ----------------------------------------------------

        icon = weather_item.get(
            "icon",
            "01d"
        )

        # ----------------------------------------------------
        # COUNTRY
        # ----------------------------------------------------

        country = (
            data.get(
                "sys",
                {}
            ).get(
                "country",
                "IN"
            )
        )

        # ----------------------------------------------------
        # WEATHER RISK
        # ----------------------------------------------------

        risk = "Low"

        if temperature >= 40:

            risk = "High"

        elif temperature >= 35:

            risk = "Moderate"

        elif humidity >= 90:

            risk = "Moderate"

        elif rainfall >= 20:

            risk = "Moderate"

        # ----------------------------------------------------
        # FARMING ADVICE
        # ----------------------------------------------------

        advice = "Weather conditions are suitable for normal farm activities."

        if temperature >= 40:

            advice = (
                "High temperature detected. "
                "Monitor irrigation and crop heat stress."
            )

        elif humidity >= 90:

            advice = (
                "High humidity detected. "
                "Monitor crops for fungal and bacterial diseases."
            )

        elif rainfall >= 20:

            advice = (
                "Rainfall detected. "
                "Avoid unnecessary irrigation and check field drainage."
            )

        elif temperature < 10:

            advice = (
                "Low temperature detected. "
                "Protect sensitive crops from cold stress."
            )

        # ----------------------------------------------------
        # FINAL WEATHER DATA
        # ----------------------------------------------------

        return {
            "success": True,

            "city": data.get(
                "name",
                city
            ),

            "country": country,

            "temperature": round(
                float(temperature),
                1
            ),

            "feels_like": round(
                float(feels_like),
                1
            ),

            "humidity": humidity,

            "wind": round(
                float(wind_speed),
                1
            ),

            "wind_speed": round(
                float(wind_speed),
                1
            ),

            "clouds": cloud_cover,

            "cloud_cover": cloud_cover,

            "pressure": pressure,

            "visibility": visibility_km,

            "rainfall": round(
                float(rainfall or 0),
                1
            ),

            "description": description,

            "icon": icon,

            "icon_code": icon,

            "risk": risk,

            "advice": advice,
        }

    except Exception as exc:

        logger.warning(
            "Dashboard weather unavailable: %s",
            exc
        )

        return default_weather


# ============================================================
# FARMER DASHBOARD
# ============================================================

@farmer_bp.route("/farmer")
def farmer():

    # ========================================================
    # LOGIN CHECK
    # ========================================================

    if (
        not session.get("user_id")
        or
        str(
            session.get(
                "role",
                ""
            )
        ).lower() != "farmer"
    ):

        return redirect(
            url_for("auth.login")
        )

    # ========================================================
    # USER NAME
    # ========================================================

    name = session.get(
        "name",
        "Farmer"
    )

    # ========================================================
    # DEFAULT VALUES
    # ========================================================

    notification_count = 0

    stats = {
        "products": 0,
        "orders": 0,
        "crops": 0,
    }

    # ========================================================
    # DATABASE
    # ========================================================

    conn = _db()

    if conn:

        try:

            cur = conn.cursor()

            uid = session.get(
                "user_id"
            )

            # =================================================
            # PRODUCTS / ORDERS / CROPS
            # =================================================

            for table, key in [
                ("products", "products"),
                ("orders", "orders"),
                ("crops", "crops"),
            ]:

                for col in (
                    "farmer_id",
                    "user_id",
                    "seller_id",
                ):

                    try:

                        value = _scalar(
                            cur,

                            f"""
                            SELECT COUNT(*) AS count
                            FROM {table}
                            WHERE {col} = %s
                            """,

                            (uid,)
                        )

                        if value:

                            stats[key] = int(
                                value
                            )

                            break

                    except Exception:

                        continue

            # =================================================
            # NOTIFICATIONS
            # =================================================

            try:

                notification_count = int(
                    _scalar(
                        cur,

                        """
                        SELECT COUNT(*) AS count
                        FROM notifications
                        WHERE user_id = %s
                        AND COALESCE(
                            is_read,
                            FALSE
                        ) = FALSE
                        """,

                        (uid,)
                    )
                )

            except Exception:

                notification_count = 0

        except Exception as exc:

            logger.warning(
                "Farmer dashboard DB stats unavailable: %s",
                exc
            )

        finally:

            try:
                conn.close()

            except Exception:
                pass

    # ========================================================
    # LIVE WEATHER
    # ========================================================

    weather_data = _weather()

    # ========================================================
    # RENDER DASHBOARD
    # ========================================================

    return render_template(
        "farmer.html",

        name=name,

        notification_count=notification_count,

        weather_data=weather_data,

        **stats,
    )


# ============================================================
# COMPATIBILITY ROUTE
# ============================================================

@farmer_bp.route("/farmer/dashboard")
def farmer_dashboard():

    return farmer()


# ============================================================
# END OF FILE
# ============================================================

