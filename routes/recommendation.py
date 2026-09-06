# routes/recommendation.py

import os
import logging
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify

from database.db import get_db_connection

try:
    from routes.weather import get_current_weather
except Exception:
    get_current_weather = None


# =========================================================
# BLUEPRINT
# =========================================================

recommendation_bp = Blueprint(
    "recommendation",
    __name__,
    url_prefix="/recommendation"
)

logger = logging.getLogger(__name__)

DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Nagpur")


# =========================================================
# LOGIN CHECK
# =========================================================

def farmer_required():
    """
    Allow only logged-in farmers.
    """

    user_id = session.get("user_id")
    role = str(session.get("role", "")).strip().lower()

    if not user_id:
        return False

    if role not in ("farmer", "admin"):
        return False

    return True


# =========================================================
# USER LOCATION
# =========================================================

def get_user_location():
    """
    Priority:
    1. session location
    2. database location
    3. Nagpur
    """

    location = str(session.get("location", "")).strip()

    if location:
        return location

    user_id = session.get("user_id")

    if not user_id:
        return DEFAULT_CITY

    conn = None

    try:
        conn = get_db_connection()

        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT location
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,)
            )
        except Exception:
            # Some DB layers may still use SQLite-style placeholders
            try:
                cursor.execute(
                    """
                    SELECT location
                    FROM users
                    WHERE id = ?
                    LIMIT 1
                    """,
                    (user_id,)
                )
            except Exception:
                return DEFAULT_CITY

        row = cursor.fetchone()

        if row:

            if isinstance(row, dict):
                location = row.get("location")

            else:
                try:
                    location = row[0]
                except Exception:
                    location = None

            if location:
                location = str(location).strip()

                if location:
                    session["location"] = location
                    return location

    except Exception as exc:
        logger.warning(
            "Unable to read user location: %s",
            exc
        )

    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass

    return DEFAULT_CITY


# =========================================================
# WEATHER
# =========================================================

def get_recommendation_weather():
    """
    Fetch current weather for crop recommendation.
    """

    city = get_user_location()

    default_weather = {
        "success": False,
        "city": city,
        "temperature": None,
        "feels_like": None,
        "humidity": None,
        "wind": None,
        "description": "Weather information unavailable",
        "icon": "01d"
    }

    if get_current_weather is None:
        return default_weather

    try:

        result = get_current_weather(city)

        if not isinstance(result, dict):
            return default_weather

        if isinstance(result.get("weather"), dict):
            weather = dict(result["weather"])
        else:
            weather = dict(result)

        for key, value in default_weather.items():

            if key not in weather:
                weather[key] = value

        if not weather.get("city"):
            weather["city"] = city

        session["location"] = weather.get(
            "city",
            city
        )

        return weather

    except Exception as exc:

        logger.warning(
            "Recommendation weather error: %s",
            exc
        )

        return default_weather


# =========================================================
# CROP DATABASE
# =========================================================

CROP_DATA = {

    "rice": {
        "soils": ["clay", "clayey", "loamy", "alluvial"],
        "seasons": ["kharif", "monsoon"],
        "irrigation": ["high", "medium"],
        "water": "High",
        "fertilizer": "NPK + nitrogen-rich fertilizer",
        "pest_risk": "Medium",
        "yield": "3.5â€“5.0 tonnes/hectare"
    },

    "wheat": {
        "soils": ["loamy", "clay", "alluvial"],
        "seasons": ["rabi", "winter"],
        "irrigation": ["medium", "high"],
        "water": "Medium",
        "fertilizer": "NPK + nitrogen fertilizer",
        "pest_risk": "Low to Medium",
        "yield": "3.0â€“4.5 tonnes/hectare"
    },

    "cotton": {
        "soils": ["black", "black soil", "loamy"],
        "seasons": ["kharif", "monsoon"],
        "irrigation": ["medium", "low"],
        "water": "Medium",
        "fertilizer": "NPK + micronutrients",
        "pest_risk": "High",
        "yield": "1.5â€“2.5 tonnes/hectare"
    },

    "soybean": {
        "soils": ["black", "black soil", "loamy"],
        "seasons": ["kharif", "monsoon"],
        "irrigation": ["low", "medium"],
        "water": "Low to Medium",
        "fertilizer": "NPK + phosphorus",
        "pest_risk": "Medium",
        "yield": "1.5â€“2.5 tonnes/hectare"
    },

    "maize": {
        "soils": ["loamy", "sandy loam", "alluvial"],
        "seasons": ["kharif", "rabi", "summer"],
        "irrigation": ["medium", "high"],
        "water": "Medium",
        "fertilizer": "NPK + nitrogen",
        "pest_risk": "Medium",
        "yield": "4.0â€“6.0 tonnes/hectare"
    },

    "chickpea": {
        "soils": ["black", "black soil", "loamy"],
        "seasons": ["rabi", "winter"],
        "irrigation": ["low", "medium"],
        "water": "Low",
        "fertilizer": "Phosphorus-rich fertilizer",
        "pest_risk": "Low to Medium",
        "yield": "1.2â€“2.0 tonnes/hectare"
    },

    "sugarcane": {
        "soils": ["loamy", "clay", "alluvial"],
        "seasons": ["kharif", "summer", "monsoon"],
        "irrigation": ["high"],
        "water": "Very High",
        "fertilizer": "NPK + organic manure",
        "pest_risk": "Medium",
        "yield": "70â€“100 tonnes/hectare"
    },

    "tomato": {
        "soils": ["loamy", "sandy loam", "alluvial"],
        "seasons": ["rabi", "summer", "kharif"],
        "irrigation": ["medium", "high"],
        "water": "Medium",
        "fertilizer": "Balanced NPK + micronutrients",
        "pest_risk": "High",
        "yield": "20â€“40 tonnes/hectare"
    },

    "onion": {
        "soils": ["loamy", "sandy loam", "alluvial"],
        "seasons": ["rabi", "kharif", "summer"],
        "irrigation": ["medium"],
        "water": "Medium",
        "fertilizer": "NPK + sulphur",
        "pest_risk": "Medium",
        "yield": "15â€“25 tonnes/hectare"
    },

    "millet": {
        "soils": ["sandy", "sandy loam", "black"],
        "seasons": ["kharif", "summer"],
        "irrigation": ["low"],
        "water": "Low",
        "fertilizer": "Balanced NPK",
        "pest_risk": "Low",
        "yield": "1.5â€“2.5 tonnes/hectare"
    }
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(value):

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


# =========================================================
# WEATHER SCORE
# =========================================================

def weather_adjustment(crop, weather):

    score = 0

    if not weather:
        return score

    temperature = weather.get("temperature")
    humidity = weather.get("humidity")

    try:
        temperature = float(temperature)
    except Exception:
        temperature = None

    try:
        humidity = float(humidity)
    except Exception:
        humidity = None

    # Rice likes warm + humid conditions
    if crop == "rice":

        if temperature is not None:
            if 22 <= temperature <= 32:
                score += 10
            elif 18 <= temperature <= 35:
                score += 5

        if humidity is not None and humidity >= 60:
            score += 5

    # Wheat prefers cooler conditions
    elif crop == "wheat":

        if temperature is not None:
            if 12 <= temperature <= 25:
                score += 10
            elif 8 <= temperature <= 30:
                score += 5

    # Cotton
    elif crop == "cotton":

        if temperature is not None:
            if 21 <= temperature <= 35:
                score += 10

    # Soybean
    elif crop == "soybean":

        if temperature is not None:
            if 20 <= temperature <= 30:
                score += 10

    # Maize
    elif crop == "maize":

        if temperature is not None:
            if 18 <= temperature <= 32:
                score += 8

    # Chickpea
    elif crop == "chickpea":

        if temperature is not None:
            if 15 <= temperature <= 28:
                score += 10

    # Sugarcane
    elif crop == "sugarcane":

        if temperature is not None:
            if 20 <= temperature <= 35:
                score += 8

    # Tomato
    elif crop == "tomato":

        if temperature is not None:
            if 18 <= temperature <= 30:
                score += 8

    # Onion
    elif crop == "onion":

        if temperature is not None:
            if 13 <= temperature <= 28:
                score += 8

    # Millet
    elif crop == "millet":

        if temperature is not None:
            if 20 <= temperature <= 35:
                score += 10

    return score


# =========================================================
# CROP SCORING
# =========================================================

def calculate_crop_score(
    crop,
    soil,
    season,
    irrigation,
    weather
):

    data = CROP_DATA[crop]

    score = 0

    soil = normalize(soil)
    season = normalize(season)
    irrigation = normalize(irrigation)

    # Soil
    if soil:

        if soil in [
            normalize(x)
            for x in data["soils"]
        ]:
            score += 35

        elif any(
            soil in normalize(x)
            for x in data["soils"]
        ):
            score += 20

    # Season
    if season:

        if season in [
            normalize(x)
            for x in data["seasons"]
        ]:
            score += 30

    # Irrigation
    if irrigation:

        if irrigation in [
            normalize(x)
            for x in data["irrigation"]
        ]:
            score += 20

    # Weather
    score += weather_adjustment(
        crop,
        weather
    )

    return min(score, 100)


# =========================================================
# REASON GENERATOR
# =========================================================

def generate_reason(
    crop,
    soil,
    season,
    irrigation,
    weather,
    score
):

    data = CROP_DATA[crop]

    reasons = []

    if soil:
        if soil in [
            normalize(x)
            for x in data["soils"]
        ]:
            reasons.append(
                f"{crop.title()} is suitable for the selected soil."
            )

    if season:
        if season in [
            normalize(x)
            for x in data["seasons"]
        ]:
            reasons.append(
                f"The selected {season} season is suitable."
            )

    if irrigation:
        if irrigation in [
            normalize(x)
            for x in data["irrigation"]
        ]:
            reasons.append(
                f"The selected irrigation level matches the crop."
            )

    temperature = weather.get("temperature")

    if temperature is not None:
        reasons.append(
            f"Current weather temperature is approximately "
            f"{temperature}Â°C."
        )

    if not reasons:
        reasons.append(
            "This crop is selected using the available "
            "farm and seasonal information."
        )

    if score >= 80:
        level = "Excellent"
    elif score >= 65:
        level = "Good"
    elif score >= 50:
        level = "Moderate"
    else:
        level = "Low"

    return (
        f"{level} suitability. "
        + " ".join(reasons)
    )


# =========================================================
# GET RECOMMENDATION
# =========================================================

def generate_recommendation(
    soil,
    area,
    season,
    irrigation,
    weather
):

    results = []

    for crop in CROP_DATA:

        score = calculate_crop_score(
            crop,
            soil,
            season,
            irrigation,
            weather
        )

        data = CROP_DATA[crop]

        result = {
            "crop": crop.title(),

            "reason": generate_reason(
                crop,
                soil,
                season,
                irrigation,
                weather,
                score
            ),

            "confidence": f"{score}%",

            "score": score,

            "irrigation": data["water"],

            "fertilizer": data["fertilizer"],

            "pest_risk": data["pest_risk"],

            "yield": data["yield"],

            "area": area
        }

        results.append(result)

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[0]


# =========================================================
# MAIN PAGE
# =========================================================

@recommendation_bp.route(
    "/",
    methods=["GET", "POST"]
)
def recommendation():

    if not farmer_required():
        return redirect(
            url_for("auth.login")
        )

    weather = get_recommendation_weather()

    recommendation_result = None

    soil = ""
    area = ""
    season = ""
    irrigation = ""

    if request.method == "POST":

        soil = request.form.get(
            "soil",
            ""
        ).strip()

        area = request.form.get(
            "area",
            ""
        ).strip()

        season = request.form.get(
            "season",
            ""
        ).strip()

        irrigation = request.form.get(
            "irrigation",
            ""
        ).strip()

        try:

            if area:

                area_value = float(area)

                if area_value <= 0:
                    area = ""

        except ValueError:
            area = ""

        recommendation_result = generate_recommendation(
            soil=soil,
            area=area,
            season=season,
            irrigation=irrigation,
            weather=weather
        )

        session["last_recommendation"] = (
            recommendation_result
        )

    return render_template(
        "recommendation.html",

        recommendation=recommendation_result,

        weather=weather,

        soil=soil,

        area=area,

        season=season,

        irrigation=irrigation,

        city=weather.get(
            "city",
            get_user_location()
        ),

        language=session.get(
            "language",
            "en"
        ),

        role=session.get(
            "role",
            "farmer"
        ),

        name=session.get(
            "name",
            "Farmer"
        ),

        notification_count=session.get(
            "notification_count",
            0
        )
    )


# =========================================================
# API
# =========================================================

@recommendation_bp.route(
    "/api",
    methods=["POST"]
)
def recommendation_api():

    if not farmer_required():
        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    soil = data.get(
        "soil",
        ""
    )

    area = data.get(
        "area",
        ""
    )

    season = data.get(
        "season",
        ""
    )

    irrigation = data.get(
        "irrigation",
        ""
    )

    weather = get_recommendation_weather()

    result = generate_recommendation(
        soil=soil,
        area=area,
        season=season,
        irrigation=irrigation,
        weather=weather
    )

    return jsonify({
        "success": True,
        "recommendation": result,
        "weather": weather
    })


# =========================================================
# HEALTH CHECK
# =========================================================

@recommendation_bp.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "success": True,
        "service": "crop-recommendation",
        "status": "running"
    })


# =========================================================
# LAST RECOMMENDATION
# =========================================================

@recommendation_bp.route(
    "/api/last",
    methods=["GET"]
)
def last_recommendation():

    if not farmer_required():
        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    result = session.get(
        "last_recommendation"
    )

    return jsonify({
        "success": True,
        "recommendation": result
    })
