# ============================================================
# KISANVISION360+
# routes/weather.py
# Live Weather + Forecast + Farm Weather Intelligence
# ============================================================

import os
import requests

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    url_for,
    flash,
)

from database.db import get_db_connection


# ============================================================
# BLUEPRINT
# ============================================================

weather_bp = Blueprint("weather", __name__)


# ============================================================
# CONFIGURATION
# ============================================================

CITY = os.getenv("DEFAULT_CITY", "Nagpur")

OPENWEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY",
    ""
).strip()

OPENWEATHER_BASE_URL = (
    "https://api.openweathermap.org/data/2.5"
)


# ============================================================
# ACCESS CHECK
# ============================================================

def farmer_or_consumer_required():

    if not session.get("user_id"):

        flash(
            "Please login to view weather information.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    role = str(
        session.get("role", "")
    ).strip().lower()

    if role not in {
        "farmer",
        "consumer",
        "admin",
    }:

        flash(
            "You are not authorized to access weather.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    return None


# ============================================================
# DATABASE LOCATION
# ============================================================

def fetch_user_location():

    conn = None
    cursor = None

    try:

        user_id = session.get("user_id")

        if not user_id:
            return None

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT location
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,),
        )

        row = cursor.fetchone()

        if not row:
            return None

        if isinstance(row, dict):
            return row.get("location")

        return row[0]

    except Exception as exc:

        print(
            "Weather location DB error:",
            exc
        )

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


# ============================================================
# GET USER LOCATION
# ============================================================

def get_user_location():

    # 1. SESSION LOCATION
    location = session.get("location")

    if location:

        location = str(
            location
        ).strip()

        if location:
            return location

    # 2. DATABASE LOCATION
    location = fetch_user_location()

    if location:

        location = str(
            location
        ).strip()

        if location:

            session["location"] = location

            return location

    # 3. DEFAULT CITY
    return CITY


# ============================================================
# GET REQUESTED CITY
# ============================================================

def get_weather_city():

    """
    Priority:

    1. ?city=Pune
    2. session["location"]
    3. users.location
    4. DEFAULT_CITY
    """

    city = request.args.get(
        "city",
        ""
    ).strip()

    if city:
        return city

    city = get_user_location()

    city = str(
        city or CITY
    ).strip()

    if not city:
        city = CITY

    return city


# ============================================================
# WEATHER ICON
# ============================================================

def weather_icon(icon_code):

    if not icon_code:
        return "ðŸŒ¤ï¸"

    icons = {

        "01d": "â˜€ï¸",
        "01n": "ðŸŒ™",

        "02d": "ðŸŒ¤ï¸",
        "02n": "â˜ï¸",

        "03d": "â˜ï¸",
        "03n": "â˜ï¸",

        "04d": "â˜ï¸",
        "04n": "â˜ï¸",

        "09d": "ðŸŒ§ï¸",
        "09n": "ðŸŒ§ï¸",

        "10d": "ðŸŒ¦ï¸",
        "10n": "ðŸŒ§ï¸",

        "11d": "â›ˆï¸",
        "11n": "â›ˆï¸",

        "13d": "â„ï¸",
        "13n": "â„ï¸",

        "50d": "ðŸŒ«ï¸",
        "50n": "ðŸŒ«ï¸",
    }

    return icons.get(
        icon_code,
        "ðŸŒ¤ï¸"
    )


# ============================================================
# WEATHER RISK
# ============================================================

def calculate_weather_risk(
    temperature,
    humidity,
    rainfall,
    wind,
    clouds
):

    risks = []

    try:

        temperature = float(
            temperature or 0
        )

        humidity = float(
            humidity or 0
        )

        rainfall = float(
            rainfall or 0
        )

        wind = float(
            wind or 0
        )

        clouds = float(
            clouds or 0
        )

    except (
        TypeError,
        ValueError
    ):

        return {
            "level": "Unknown",
            "score": 0,
            "risks": [],
        }

    score = 0

    # TEMPERATURE
    if temperature >= 40:

        score += 30

        risks.append(
            "Extreme heat risk"
        )

    elif temperature >= 35:

        score += 20

        risks.append(
            "High temperature"
        )

    # HUMIDITY
    if humidity >= 85:

        score += 20

        risks.append(
            "High humidity"
        )

    # RAINFALL
    if rainfall >= 30:

        score += 25

        risks.append(
            "Heavy rainfall possibility"
        )

    elif rainfall >= 10:

        score += 10

        risks.append(
            "Rainfall detected"
        )

    # WIND
    if wind >= 15:

        score += 20

        risks.append(
            "Strong wind"
        )

    # CLOUDS
    if clouds >= 90:

        score += 5

        risks.append(
            "Very cloudy conditions"
        )

    if score >= 60:

        level = "High"

    elif score >= 30:

        level = "Moderate"

    else:

        level = "Low"

    return {

        "level": level,

        "score": min(
            score,
            100
        ),

        "risks": risks,
    }


# ============================================================
# FARM WEATHER ADVICE
# ============================================================

def generate_farm_advice(
    temperature,
    humidity,
    rainfall,
    wind,
):

    advice = []

    try:

        temperature = float(
            temperature or 0
        )

        humidity = float(
            humidity or 0
        )

        rainfall = float(
            rainfall or 0
        )

        wind = float(
            wind or 0
        )

    except (
        TypeError,
        ValueError
    ):

        return [
            "Weather data is currently unavailable."
        ]

    # WATER
    if rainfall >= 10:

        advice.append(
            "Rainfall is present. "
            "Review irrigation before watering the crop."
        )

    elif temperature >= 35:

        advice.append(
            "High temperature detected. "
            "Monitor soil moisture carefully."
        )

    else:

        advice.append(
            "Check soil moisture before irrigation."
        )

    # DISEASE
    if humidity >= 80:

        advice.append(
            "High humidity can increase disease pressure. "
            "Monitor crops regularly."
        )

    # WIND
    if wind >= 12:

        advice.append(
            "Strong wind is possible. "
            "Avoid unnecessary spraying during windy conditions."
        )

    # EXTREME HEAT
    if temperature >= 40:

        advice.append(
            "Extreme heat detected. "
            "Protect sensitive crops and livestock."
        )

    return advice


# ============================================================
# CURRENT WEATHER
# ============================================================

def get_current_weather(city):

    if not OPENWEATHER_API_KEY:

        return {

            "success": False,

            "error": (
                "Weather API key is not configured."
            ),

            "city": city,
        }

    try:

        response = requests.get(

            f"{OPENWEATHER_BASE_URL}/weather",

            params={

                "q": city,

                "appid": OPENWEATHER_API_KEY,

                "units": "metric",
            },

            timeout=15,
        )

        if response.status_code != 200:

            try:

                api_data = response.json()

                message = api_data.get(
                    "message",
                    "Weather service unavailable."
                )

            except Exception:

                message = (
                    "Weather service unavailable."
                )

            print(
                "Current weather API error:",
                response.status_code,
                response.text
            )

            return {

                "success": False,

                "error": message,

                "city": city,

                "status_code": response.status_code,
            }

        data = response.json()

        main = data.get(
            "main",
            {}
        )

        wind_data = data.get(
            "wind",
            {}
        )

        clouds_data = data.get(
            "clouds",
            {}
        )

        weather_data = (
            data.get("weather") or [{}]
        )[0]

        rainfall_data = data.get(
            "rain",
            {}
        )

        rainfall = (

            rainfall_data.get(
                "1h",
                0
            )

            or rainfall_data.get(
                "3h",
                0
            )

            or 0
        )

        temperature = main.get(
            "temp"
        )

        feels_like = main.get(
            "feels_like"
        )

        humidity = main.get(
            "humidity"
        )

        wind_speed = wind_data.get(
            "speed",
            0
        )

        clouds = clouds_data.get(
            "all",
            0
        )

        pressure = main.get(
            "pressure"
        )

        visibility = data.get(
            "visibility",
            0
        )

        icon_code = weather_data.get(
            "icon",
            ""
        )

        description = weather_data.get(
            "description",
            "Unavailable"
        )

        risk = calculate_weather_risk(

            temperature,

            humidity,

            rainfall,

            wind_speed,

            clouds,
        )

        advice = generate_farm_advice(

            temperature,

            humidity,

            rainfall,

            wind_speed,
        )

        return {

            "success": True,

            "city": data.get(
                "name",
                city
            ),

            "country": (
                data.get(
                    "sys",
                    {}
                ).get(
                    "country",
                    ""
                )
            ),

            "icon": weather_icon(
                icon_code
            ),

            "icon_code": icon_code,

            "description": description,

            "temperature": temperature,

            "feels_like": feels_like,

            "humidity": humidity,

            "wind": wind_speed,

            "wind_speed": wind_speed,

            "clouds": clouds,

            "visibility": (

                round(
                    float(visibility) / 1000,
                    2
                )

                if visibility

                else 0
            ),

            "rainfall": rainfall,

            "pressure": pressure,

            "risk": risk,

            "advice": advice,

            "latitude": (
                data.get(
                    "coord",
                    {}
                ).get(
                    "lat"
                )
            ),

            "longitude": (
                data.get(
                    "coord",
                    {}
                ).get(
                    "lon"
                )
            ),

            "updated_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    except requests.RequestException as exc:

        print(
            "OpenWeather current weather error:",
            exc
        )

        return {

            "success": False,

            "error": (
                "Unable to connect to "
                "weather service."
            ),

            "city": city,
        }

    except Exception as exc:

        print(
            "Current weather processing error:",
            exc
        )

        return {

            "success": False,

            "error": (
                "Unable to process "
                "weather data."
            ),

            "city": city,
        }


# ============================================================
# FORECAST
# ============================================================

def get_weather_forecast(city):

    """
    OpenWeather 5-day / 3-hour forecast.

    OpenWeather returns approximately 40 forecast
    records. We group them by local calendar date
    and generate daily forecast cards.
    """

    if not OPENWEATHER_API_KEY:

        print(
            "Forecast error: OPENWEATHER_API_KEY missing."
        )

        return []

    try:

        response = requests.get(

            f"{OPENWEATHER_BASE_URL}/forecast",

            params={

                "q": city,

                "appid": OPENWEATHER_API_KEY,

                "units": "metric",
            },

            timeout=15,
        )

        # ====================================================
        # IMPORTANT DEBUG
        # ====================================================

        print(
            "=============================================="
        )

        print(
            "FORECAST CITY:",
            city
        )

        print(
            "FORECAST API STATUS:",
            response.status_code
        )

        # ====================================================
        # API ERROR
        # ====================================================

        if response.status_code != 200:

            try:

                error_data = response.json()

                error_message = error_data.get(
                    "message",
                    "Forecast service unavailable."
                )

            except Exception:

                error_message = (
                    "Forecast service unavailable."
                )

            print(
                "FORECAST API ERROR:",
                error_message
            )

            print(
                "FORECAST RAW RESPONSE:",
                response.text
            )

            print(
                "=============================================="
            )

            return []

        # ====================================================
        # JSON
        # ====================================================

        data = response.json()

        print(
            "FORECAST RESPONSE CODE:",
            data.get("cod")
        )

        print(
            "FORECAST RECORD COUNT:",
            len(
                data.get(
                    "list",
                    []
                )
            )
        )

        forecast_list = data.get(
            "list",
            []
        )

        # ====================================================
        # NO DATA
        # ====================================================

        if not forecast_list:

            print(
                "Forecast API returned no forecast records."
            )

            print(
                "RAW FORECAST RESPONSE:",
                data
            )

            print(
                "=============================================="
            )

            return []

        # ====================================================
        # GROUP BY DATE
        # ====================================================

        grouped = {}

        for item in forecast_list:

            timestamp = item.get(
                "dt"
            )

            if timestamp is None:
                continue

            try:

                timestamp = int(
                    timestamp
                )

                date_obj = datetime.fromtimestamp(
                    timestamp
                )

            except (
                TypeError,
                ValueError,
                OSError,
            ):

                continue

            date_key = date_obj.strftime(
                "%Y-%m-%d"
            )

            if date_key not in grouped:

                grouped[date_key] = []

            grouped[date_key].append(
                item
            )

        # ====================================================
        # NO GROUPED DATA
        # ====================================================

        if not grouped:

            print(
                "Forecast records received but "
                "date grouping failed."
            )

            return []

        # ====================================================
        # DAILY RESULT
        # ====================================================

        result = []

        sorted_dates = sorted(
            grouped.keys()
        )

        # OpenWeather free forecast is about 5 days.
        # We return all available grouped days.
        for date_key in sorted_dates:

            items = grouped.get(
                date_key,
                []
            )

            if not items:
                continue

            temperatures = []

            min_temperatures = []

            max_temperatures = []

            rain_values = []

            humidity_values = []

            wind_values = []

            cloud_values = []

            rain_probabilities = []

            # ------------------------------------------------
            # REPRESENTATIVE WEATHER
            # Prefer midday/central forecast record.
            # ------------------------------------------------

            representative = items[
                len(items) // 2
            ]

            # ------------------------------------------------
            # PROCESS EACH 3-HOUR RECORD
            # ------------------------------------------------

            for item in items:

                main = item.get(
                    "main",
                    {}
                ) or {}

                # TEMPERATURE
                temp = main.get(
                    "temp"
                )

                temp_min = main.get(
                    "temp_min"
                )

                temp_max = main.get(
                    "temp_max"
                )

                humidity = main.get(
                    "humidity"
                )

                if temp is not None:

                    try:

                        temperatures.append(
                            float(temp)
                        )

                    except (
                        TypeError,
                        ValueError
                    ):
                        pass

                if temp_min is not None:

                    try:

                        min_temperatures.append(
                            float(temp_min)
                        )

                    except (
                        TypeError,
                        ValueError
                    ):
                        pass

                if temp_max is not None:

                    try:

                        max_temperatures.append(
                            float(temp_max)
                        )

                    except (
                        TypeError,
                        ValueError
                    ):
                        pass

                # HUMIDITY
                if humidity is not None:

                    try:

                        humidity_values.append(
                            float(humidity)
                        )

                    except (
                        TypeError,
                        ValueError
                    ):
                        pass

                # WIND
                wind_data = item.get(
                    "wind",
                    {}
                ) or {}

                wind_speed = wind_data.get(
                    "speed"
                )

                if wind_speed is not None:

                    try:

                        wind_values.append(
                            float(wind_speed)
                        )

                    except (
                        TypeError,
                        ValueError
                    ):
                        pass

                # CLOUDS
                clouds_data = item.get(
                    "clouds",
                    {}
                ) or {}

                clouds = clouds_data.get(
                    "all"
                )

                if clouds is not None:

                    try:

                        cloud_values.append(
                            float(clouds)
                        )

                    except (
                        TypeError,
                        ValueError
                    ):
                        pass

                # RAIN
                rain_data = item.get(
                    "rain",
                    {}
                ) or {}

                rain_3h = rain_data.get(
                    "3h",
                    0
                )

                try:

                    rain_3h = float(
                        rain_3h or 0
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    rain_3h = 0

                rain_values.append(
                    rain_3h
                )

                # POP = probability of precipitation
                pop = item.get(
                    "pop"
                )

                if pop is not None:

                    try:

                        pop_value = float(
                            pop
                        )

                        # OpenWeather POP is 0.0 - 1.0
                        if pop_value <= 1:

                            pop_value *= 100

                        rain_probabilities.append(
                            pop_value
                        )

                    except (
                        TypeError,
                        ValueError
                    ):
                        pass

            # =================================================
            # TEMPERATURE
            # =================================================

            if temperatures:

                avg_temperature = round(
                    sum(temperatures)
                    / len(temperatures),
                    1
                )

            else:

                avg_temperature = None

            # =================================================
            # MIN TEMPERATURE
            # =================================================

            if min_temperatures:

                min_temperature = round(
                    min(min_temperatures),
                    1
                )

            elif temperatures:

                min_temperature = round(
                    min(temperatures),
                    1
                )

            else:

                min_temperature = None

            # =================================================
            # MAX TEMPERATURE
            # =================================================

            if max_temperatures:

                max_temperature = round(
                    max(max_temperatures),
                    1
                )

            elif temperatures:

                max_temperature = round(
                    max(temperatures),
                    1
                )

            else:

                max_temperature = None

            # =================================================
            # HUMIDITY
            # =================================================

            if humidity_values:

                humidity_value = round(
                    sum(humidity_values)
                    / len(humidity_values)
                )

            else:

                humidity_value = None

            # =================================================
            # WIND
            # =================================================

            if wind_values:

                wind_value = round(
                    sum(wind_values)
                    / len(wind_values),
                    1
                )

            else:

                wind_value = 0

            # =================================================
            # CLOUD
            # =================================================

            if cloud_values:

                cloud_value = round(
                    sum(cloud_values)
                    / len(cloud_values)
                )

            else:

                cloud_value = 0

            # =================================================
            # RAIN
            # =================================================

            rain_value = round(
                sum(rain_values),
                1
            )

            # =================================================
            # RAIN PROBABILITY
            # =================================================

            if rain_probabilities:

                rain_probability = round(
                    max(rain_probabilities)
                )

            else:

                # Fallback estimation if POP is unavailable.
                if rain_value >= 20:

                    rain_probability = 90

                elif rain_value >= 10:

                    rain_probability = 70

                elif rain_value > 0:

                    rain_probability = 40

                else:

                    rain_probability = 0

            rain_probability = max(
                0,
                min(
                    rain_probability,
                    100
                )
            )

            # =================================================
            # WEATHER DESCRIPTION
            # =================================================

            weather_array = representative.get(
                "weather",
                []
            ) or []

            if weather_array:

                weather_item = weather_array[0]

            else:

                weather_item = {}

            icon_code = weather_item.get(
                "icon",
                ""
            )

            description = weather_item.get(
                "description",
                "Unavailable"
            )

            # =================================================
            # DAY NAME
            # =================================================

            try:

                date_object = datetime.strptime(
                    date_key,
                    "%Y-%m-%d"
                )

                day_name = date_object.strftime(
                    "%A"
                )

            except ValueError:

                day_name = date_key

            # =================================================
            # DAILY RISK
            # =================================================

            daily_risk = calculate_weather_risk(

                avg_temperature,

                humidity_value,

                rain_value,

                wind_value,

                cloud_value,
            )

            # =================================================
            # APPEND
            # =================================================

            result.append({

                "date": date_key,

                "day": day_name,

                "icon": weather_icon(
                    icon_code
                ),

                "icon_code": icon_code,

                "description": description,

                "temperature": avg_temperature,

                "temp": avg_temperature,

                "min_temperature": min_temperature,

                "max_temperature": max_temperature,

                "temp_min": min_temperature,

                "temp_max": max_temperature,

                "humidity": humidity_value,

                "wind": wind_value,

                "clouds": cloud_value,

                "rain": rain_value,

                "rainfall": rain_value,

                "rain_probability": rain_probability,

                "pop": rain_probability,

                "risk": daily_risk,

            })

        # ====================================================
        # DEBUG FINAL
        # ====================================================

        print(
            "FORECAST DAYS GENERATED:",
            len(result)
        )

        print(
            "=============================================="
        )

        return result

    except requests.RequestException as exc:

        print(
            "Forecast network error:",
            exc
        )

        return []

    except Exception as exc:

        print(
            "Forecast processing error:",
            repr(exc)
        )

        return []


# ============================================================
# WEATHER PAGE
# ============================================================

@weather_bp.route("/weather")
def weather():

    access = farmer_or_consumer_required()

    if access:
        return access

    city = get_weather_city()

    current_weather = get_current_weather(
        city
    )

    forecast = get_weather_forecast(
        city
    )

    return render_template(

        "weather.html",

        weather=current_weather,

        forecast=forecast,

        city=city,

        language=session.get(
            "language",
            "en"
        ),

        role=session.get(
            "role",
            ""
        ),

        name=session.get(
            "name",
            "Farmer"
        ),

        notification_count=session.get(
            "notification_count",
            0
        ),
    )


# ============================================================
# CURRENT WEATHER API
# ============================================================

@weather_bp.route(
    "/api/weather"
)
def weather_api():

    if not session.get("user_id"):

        return jsonify({

            "success": False,

            "message": (
                "Authentication required."
            ),

        }), 401

    city = get_weather_city()

    weather_data = get_current_weather(
        city
    )

    if not weather_data.get(
        "success",
        False
    ):

        return jsonify(
            weather_data
        ), 503

    return jsonify(
        weather_data
    )


# ============================================================
# FORECAST API
# ============================================================

@weather_bp.route(
    "/api/weather/forecast"
)
def forecast_api():

    if not session.get("user_id"):

        return jsonify({

            "success": False,

            "message": (
                "Authentication required."
            ),

        }), 401

    city = get_weather_city()

    forecast = get_weather_forecast(
        city
    )

    return jsonify({

        "success": True,

        "city": city,

        "forecast": forecast,

        "days": len(
            forecast
        ),

    })


# ============================================================
# WEATHER + FARM INTELLIGENCE
# ============================================================

@weather_bp.route(
    "/api/weather/intelligence"
)
def weather_intelligence():

    if not session.get("user_id"):

        return jsonify({

            "success": False,

            "message": (
                "Authentication required."
            ),

        }), 401

    city = get_weather_city()

    weather_data = get_current_weather(
        city
    )

    if not weather_data.get(
        "success",
        False
    ):

        return jsonify(
            weather_data
        ), 503

    return jsonify({

        "success": True,

        "city": city,

        "weather": weather_data,

        "risk": weather_data.get(
            "risk",
            {}
        ),

        "farm_advice": weather_data.get(
            "advice",
            []
        ),

        "connected_modules": {

            "irrigation": True,

            "crop_advisor": True,

            "disease_detection": True,

            "notifications": True,

            "market": True,
        },

    })


# ============================================================
# UPDATE FARM LOCATION
# ============================================================

@weather_bp.route(
    "/api/weather/location",
    methods=["POST"]
)
def update_weather_location():

    if not session.get("user_id"):

        return jsonify({

            "success": False,

            "message": (
                "Authentication required."
            ),

        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    city = str(
        data.get(
            "city",
            ""
        )
    ).strip()

    if not city:

        return jsonify({

            "success": False,

            "message": "City is required.",

        }), 400

    if len(city) > 100:

        return jsonify({

            "success": False,

            "message": (
                "City name is too long."
            ),

        }), 400

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute(

            """
            UPDATE users
            SET location = %s
            WHERE id = %s
            """,

            (
                city,
                session.get("user_id"),
            ),
        )

        conn.commit()

        session["location"] = city

        return jsonify({

            "success": True,

            "message": (
                "Weather location updated."
            ),

            "city": city,

        })

    except Exception as exc:

        if conn:

            try:

                conn.rollback()

            except Exception:
                pass

        print(
            "Weather location update error:",
            exc
        )

        return jsonify({

            "success": False,

            "message": (
                "Unable to update location."
            ),

        }), 500

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
# WEATHER HEALTH CHECK
# ============================================================

@weather_bp.route(
    "/api/weather/health"
)
def weather_health():

    return jsonify({

        "success": True,

        "module": "weather",

        "status": (

            "configured"

            if OPENWEATHER_API_KEY

            else "api_key_missing"
        ),

        "provider": "OpenWeather",

        "default_city": CITY,

        "application": "KisanVision360+",

    })
