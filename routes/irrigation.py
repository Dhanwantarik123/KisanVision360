# ============================================================
# KISANVISION360+
# routes/irrigation.py
# Smart Irrigation Intelligence
# PostgreSQL / Supabase Ready
# ============================================================

from datetime import datetime

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


# ============================================================
# BLUEPRINT
# ============================================================

irrigation_bp = Blueprint(
    "irrigation",
    __name__
)


# ============================================================
# FARMER ACCESS
# ============================================================

def farmer_required():

    if not session.get("user_id"):

        return redirect(
            url_for("login")
        )

    role = str(
        session.get("role", "")
    ).strip().lower()

    if role != "farmer":

        flash(
            "Only farmers can access Smart Irrigation.",
            "warning"
        )

        return redirect(
            url_for("farmer")
        )

    return None


# ============================================================
# SAFE NUMBER
# ============================================================

def safe_float(
    value,
    default=0.0
):

    try:
        return float(value)
    except (
        TypeError,
        ValueError
    ):
        return default


# ============================================================
# SAFE INTEGER
# ============================================================

def safe_int(
    value,
    default=0
):

    try:
        return int(float(value))
    except (
        TypeError,
        ValueError
    ):
        return default


# ============================================================
# GET FARMER PROFILE
# ============================================================

def get_farmer_profile():

    conn = None
    cursor = None

    try:

        user_id = session.get(
            "user_id"
        )

        if not user_id:
            return {}

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                u.location,
                fp.farm_area,
                fp.soil_type,
                fp.irrigation_method
            FROM users u
            LEFT JOIN farmer_profiles fp
                ON fp.user_id = u.id
            WHERE u.id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        row = cursor.fetchone()

        if not row:
            return {}

        if isinstance(row, dict):
            return dict(row)

        columns = [
            column[0]
            for column in cursor.description
        ]

        return dict(
            zip(columns, row)
        )

    except Exception as exc:

        print(
            "Irrigation profile error:",
            exc
        )

        return {}

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
# GET CURRENT WEATHER
# ============================================================

def get_weather():

    try:

        location = session.get(
            "location"
        )

        if not location:

            profile = get_farmer_profile()

            location = profile.get(
                "location"
            )

        if not location:
            location = "Nagpur"

        from routes.weather import (
            get_current_weather
        )

        result = get_current_weather(
            location
        )

        if isinstance(result, dict):

            if result.get(
                "success",
                False
            ):

                return result

        return {}

    except Exception as exc:

        print(
            "Irrigation weather error:",
            exc
        )

        return {}


# ============================================================
# IRRIGATION CROP REQUIREMENTS
# ============================================================

CROP_WATER_REQUIREMENTS = {

    "rice": {
        "name": "Rice",
        "water_need": "high",
        "daily_mm": 6.0,
        "root_depth": 0.30,
    },

    "wheat": {
        "name": "Wheat",
        "water_need": "medium",
        "daily_mm": 4.0,
        "root_depth": 0.35,
    },

    "cotton": {
        "name": "Cotton",
        "water_need": "medium",
        "daily_mm": 4.5,
        "root_depth": 0.60,
    },

    "soybean": {
        "name": "Soybean",
        "water_need": "medium",
        "daily_mm": 4.0,
        "root_depth": 0.50,
    },

    "maize": {
        "name": "Maize",
        "water_need": "medium",
        "daily_mm": 4.5,
        "root_depth": 0.50,
    },

    "chickpea": {
        "name": "Chickpea",
        "water_need": "low",
        "daily_mm": 3.0,
        "root_depth": 0.45,
    },

    "pigeon_pea": {
        "name": "Pigeon Pea",
        "water_need": "low",
        "daily_mm": 3.0,
        "root_depth": 0.60,
    },

    "tomato": {
        "name": "Tomato",
        "water_need": "medium",
        "daily_mm": 4.5,
        "root_depth": 0.40,
    },

    "onion": {
        "name": "Onion",
        "water_need": "medium",
        "daily_mm": 4.0,
        "root_depth": 0.30,
    },

    "potato": {
        "name": "Potato",
        "water_need": "medium",
        "daily_mm": 4.0,
        "root_depth": 0.35,
    },

    "groundnut": {
        "name": "Groundnut",
        "water_need": "low",
        "daily_mm": 3.5,
        "root_depth": 0.40,
    },

    "sugarcane": {
        "name": "Sugarcane",
        "water_need": "high",
        "daily_mm": 6.5,
        "root_depth": 0.80,
    },

    "millet": {
        "name": "Millet",
        "water_need": "low",
        "daily_mm": 2.5,
        "root_depth": 0.40,
    },

    "mustard": {
        "name": "Mustard",
        "water_need": "low",
        "daily_mm": 3.0,
        "root_depth": 0.40,
    },

    "green_gram": {
        "name": "Green Gram",
        "water_need": "low",
        "daily_mm": 2.8,
        "root_depth": 0.35,
    },
}


# ============================================================
# IRRIGATION EFFICIENCY
# ============================================================

IRRIGATION_EFFICIENCY = {

    "drip": 0.90,

    "sprinkler": 0.75,

    "furrow": 0.60,

    "flood": 0.50,

    "manual": 0.55,

    "rainfed": 0.40,

}


# ============================================================
# NORMALIZE CROP
# ============================================================

def normalize_crop(
    crop
):

    crop = str(
        crop or ""
    ).strip().lower()

    aliases = {

        "paddy": "rice",

        "chana": "chickpea",

        "gram": "chickpea",

        "tur": "pigeon_pea",

        "arhar": "pigeon_pea",

        "mung": "green_gram",

        "moong": "green_gram",

        "bajra": "millet",

    }

    return aliases.get(
        crop,
        crop
    )


# ============================================================
# CALCULATE IRRIGATION
# ============================================================

def calculate_irrigation(
    crop,
    area_acres,
    irrigation_method="drip",
    rainfall_mm=0,
    temperature=25,
    humidity=60,
    soil_moisture=None,
):

    crop_key = normalize_crop(
        crop
    )

    crop_data = CROP_WATER_REQUIREMENTS.get(
        crop_key
    )

    if not crop_data:

        crop_data = {
            "name": str(crop).title(),
            "water_need": "medium",
            "daily_mm": 4.0,
            "root_depth": 0.40,
        }

    area_acres = max(
        safe_float(area_acres, 1),
        0.01
    )

    rainfall_mm = max(
        safe_float(rainfall_mm),
        0
    )

    temperature = safe_float(
        temperature,
        25
    )

    humidity = safe_float(
        humidity,
        60
    )

    method = str(
        irrigation_method or "drip"
    ).strip().lower()

    efficiency = IRRIGATION_EFFICIENCY.get(
        method,
        0.60
    )

    # --------------------------------------------------------
    # Base crop demand
    # --------------------------------------------------------

    daily_need_mm = crop_data[
        "daily_mm"
    ]

    # --------------------------------------------------------
    # Temperature adjustment
    # --------------------------------------------------------

    if temperature >= 35:

        daily_need_mm *= 1.20

    elif temperature >= 30:

        daily_need_mm *= 1.10

    elif temperature <= 15:

        daily_need_mm *= 0.85

    # --------------------------------------------------------
    # Humidity adjustment
    # --------------------------------------------------------

    if humidity >= 80:

        daily_need_mm *= 0.85

    elif humidity <= 35:

        daily_need_mm *= 1.10

    # --------------------------------------------------------
    # Rainfall deduction
    # --------------------------------------------------------

    effective_rainfall = rainfall_mm * 0.70

    net_need_mm = max(
        daily_need_mm
        - effective_rainfall,
        0
    )

    # --------------------------------------------------------
    # Irrigation efficiency adjustment
    # --------------------------------------------------------

    application_need_mm = (
        net_need_mm
        / efficiency
    )

    # --------------------------------------------------------
    # 1 mm water over 1 acre
    # â‰ˆ 4046.86 litres
    # --------------------------------------------------------

    litres_per_mm_per_acre = 4046.86

    daily_litres = (
        application_need_mm
        * area_acres
        * litres_per_mm_per_acre
    )

    weekly_litres = (
        daily_litres
        * 7
    )

    # --------------------------------------------------------
    # Recommended duration
    # --------------------------------------------------------

    if crop_data["water_need"] == "high":

        frequency_days = 1

    elif crop_data["water_need"] == "medium":

        frequency_days = 2

    else:

        frequency_days = 3

    event_litres = (
        daily_litres
        * frequency_days
    )

    # --------------------------------------------------------
    # Soil moisture override
    # --------------------------------------------------------

    moisture_status = (
        "Unknown"
    )

    if soil_moisture is not None:

        moisture = safe_float(
            soil_moisture
        )

        if moisture >= 70:

            moisture_status = "Wet"

            daily_litres *= 0.50

        elif moisture >= 40:

            moisture_status = "Optimal"

            daily_litres *= 0.75

        else:

            moisture_status = "Dry"

    # --------------------------------------------------------
    # Water saving
    # --------------------------------------------------------

    flood_equivalent = (
        net_need_mm
        / IRRIGATION_EFFICIENCY["flood"]
        * area_acres
        * litres_per_mm_per_acre
    )

    water_saved = max(
        flood_equivalent
        - daily_litres,
        0
    )

    if flood_equivalent > 0:

        saving_percent = (
            water_saved
            / flood_equivalent
        ) * 100

    else:

        saving_percent = 0

    # --------------------------------------------------------
    # Irrigation priority
    # --------------------------------------------------------

    if moisture_status == "Wet":

        priority = "Low"

    elif net_need_mm >= 5:

        priority = "High"

    elif net_need_mm >= 2:

        priority = "Medium"

    else:

        priority = "Low"

    return {

        "crop": crop_data["name"],

        "crop_key": crop_key,

        "water_need": crop_data[
            "water_need"
        ],

        "area_acres": round(
            area_acres,
            2
        ),

        "irrigation_method": method,

        "efficiency": round(
            efficiency * 100,
            1
        ),

        "daily_need_mm": round(
            daily_need_mm,
            2
        ),

        "rainfall_mm": round(
            rainfall_mm,
            2
        ),

        "net_need_mm": round(
            net_need_mm,
            2
        ),

        "application_need_mm": round(
            application_need_mm,
            2
        ),

        "daily_litres": round(
            daily_litres,
            0
        ),

        "weekly_litres": round(
            weekly_litres,
            0
        ),

        "event_litres": round(
            event_litres,
            0
        ),

        "frequency_days": frequency_days,

        "water_saved_litres": round(
            water_saved,
            0
        ),

        "water_saving_percent": round(
            saving_percent,
            1
        ),

        "soil_moisture": (
            safe_float(soil_moisture)
            if soil_moisture is not None
            else None
        ),

        "moisture_status": moisture_status,

        "priority": priority,

    }


# ============================================================
# GENERATE SMART ADVICE
# ============================================================

def generate_advice(
    result,
    weather
):

    advice = []

    method = result[
        "irrigation_method"
    ]

    priority = result[
        "priority"
    ]

    rainfall = result[
        "rainfall_mm"
    ]

    moisture = result[
        "moisture_status"
    ]

    saving = result[
        "water_saving_percent"
    ]

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    if priority == "High":

        advice.append(
            "Irrigation priority is high. Check the field and irrigate according to crop requirement."
        )

    elif priority == "Medium":

        advice.append(
            "Moderate irrigation is recommended. Avoid unnecessary extra watering."
        )

    else:

        advice.append(
            "Irrigation requirement is currently low."
        )

    # --------------------------------------------------------
    # Rain
    # --------------------------------------------------------

    if rainfall >= 5:

        advice.append(
            "Recent rainfall can reduce irrigation demand."
        )

    # --------------------------------------------------------
    # Soil moisture
    # --------------------------------------------------------

    if moisture == "Wet":

        advice.append(
            "Soil moisture is high. Avoid over-irrigation."
        )

    elif moisture == "Dry":

        advice.append(
            "Soil moisture is low. Field inspection is recommended."
        )

    elif moisture == "Optimal":

        advice.append(
            "Soil moisture is in an acceptable range."
        )

    # --------------------------------------------------------
    # Irrigation method
    # --------------------------------------------------------

    if method == "drip":

        advice.append(
            "Drip irrigation provides efficient water delivery near the root zone."
        )

    elif method == "sprinkler":

        advice.append(
            "Sprinkler irrigation can provide better uniformity than flood irrigation."
        )

    elif method in (
        "flood",
        "manual"
    ):

        advice.append(
            "Consider drip or sprinkler irrigation where economically suitable to reduce water loss."
        )

    # --------------------------------------------------------
    # Water saving
    # --------------------------------------------------------

    if saving >= 25:

        advice.append(
            f"Estimated water saving versus flood irrigation is about {saving:.0f}%."
        )

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    if weather:

        description = str(
            weather.get(
                "description",
                ""
            )
        ).lower()

        if any(
            word in description
            for word in (
                "rain",
                "drizzle",
                "storm"
            )
        ):

            advice.append(
                "Rain-related weather is present. Recheck irrigation before watering."
            )

    return advice


# ============================================================
# MAIN IRRIGATION PAGE
# ============================================================

@irrigation_bp.route(
    "/irrigation",
    methods=["GET", "POST"]
)
def irrigation():

    access = farmer_required()

    if access:
        return access

    profile = get_farmer_profile()

    weather = get_weather()

    if request.method == "POST":

        crop = request.form.get(
            "crop",
            "maize"
        )

        area = request.form.get(
            "area",
            profile.get(
                "farm_area",
                1
            )
        )

        method = request.form.get(
            "irrigation_method",
            profile.get(
                "irrigation_method",
                "drip"
            )
        )

        soil_moisture = request.form.get(
            "soil_moisture"
        )

    else:

        crop = "maize"

        area = profile.get(
            "farm_area",
            1
        )

        method = profile.get(
            "irrigation_method",
            "drip"
        )

        soil_moisture = None

    rainfall = weather.get(
        "rainfall",
        0
    )

    temperature = weather.get(
        "temperature",
        25
    )

    humidity = weather.get(
        "humidity",
        60
    )

    result = calculate_irrigation(

        crop=crop,

        area_acres=area,

        irrigation_method=method,

        rainfall_mm=rainfall,

        temperature=temperature,

        humidity=humidity,

        soil_moisture=soil_moisture,

    )

    advice = generate_advice(
        result,
        weather
    )

    return render_template(

        "irrigation.html",

        result=result,

        advice=advice,

        weather=weather,

        profile=profile,

        crop=crop,

        area=area,

        irrigation_method=method,

        soil_moisture=soil_moisture,

        crops=CROP_WATER_REQUIREMENTS,

        name=session.get(
            "name",
            "Farmer"
        ),

        language=session.get(
            "language",
            "en"
        ),

        role=session.get(
            "role",
            "farmer"
        ),

    )


# ============================================================
# SMART IRRIGATION API
# ============================================================

@irrigation_bp.route(
    "/api/irrigation",
    methods=["GET", "POST"]
)
def irrigation_api():

    access = farmer_required()

    if access:

        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    if request.method == "POST":

        data = (
            request.get_json(
                silent=True
            )
            or request.form.to_dict()
        )

    else:

        data = request.args.to_dict()

    profile = get_farmer_profile()

    weather = get_weather()

    crop = data.get(
        "crop",
        "maize"
    )

    area = data.get(
        "area",
        profile.get(
            "farm_area",
            1
        )
    )

    method = data.get(
        "irrigation_method",
        profile.get(
            "irrigation_method",
            "drip"
        )
    )

    soil_moisture = data.get(
        "soil_moisture"
    )

    rainfall = data.get(
        "rainfall",
        weather.get(
            "rainfall",
            0
        )
    )

    temperature = data.get(
        "temperature",
        weather.get(
            "temperature",
            25
        )
    )

    humidity = data.get(
        "humidity",
        weather.get(
            "humidity",
            60
        )
    )

    result = calculate_irrigation(

        crop=crop,

        area_acres=area,

        irrigation_method=method,

        rainfall_mm=rainfall,

        temperature=temperature,

        humidity=humidity,

        soil_moisture=soil_moisture,

    )

    advice = generate_advice(
        result,
        weather
    )

    return jsonify({

        "success": True,

        "application": "KisanVision360+",

        "module": "Smart Irrigation",

        "result": result,

        "advice": advice,

        "weather": {

            "city": weather.get(
                "city"
            ),

            "temperature": weather.get(
                "temperature"
            ),

            "humidity": weather.get(
                "humidity"
            ),

            "rainfall": weather.get(
                "rainfall",
                0
            ),

            "description": weather.get(
                "description"
            ),

        },

    })


# ============================================================
# IRRIGATION RECOMMENDATION API
# ============================================================

@irrigation_bp.route(
    "/api/irrigation/recommendation"
)
def irrigation_recommendation():

    access = farmer_required()

    if access:

        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    profile = get_farmer_profile()

    weather = get_weather()

    crops = []

    area = safe_float(
        profile.get(
            "farm_area",
            1
        ),
        1
    )

    method = profile.get(
        "irrigation_method",
        "drip"
    )

    for crop_key in CROP_WATER_REQUIREMENTS:

        result = calculate_irrigation(

            crop=crop_key,

            area_acres=area,

            irrigation_method=method,

            rainfall_mm=weather.get(
                "rainfall",
                0
            ),

            temperature=weather.get(
                "temperature",
                25
            ),

            humidity=weather.get(
                "humidity",
                60
            ),

        )

        crops.append(result)

    crops.sort(
        key=lambda item: (
            0 if item["priority"] == "High"
            else 1 if item["priority"] == "Medium"
            else 2,
            item["daily_litres"]
        )
    )

    return jsonify({

        "success": True,

        "recommendations": crops,

        "count": len(crops),

    })


# ============================================================
# WATER SAVING CALCULATOR
# ============================================================

@irrigation_bp.route(
    "/api/irrigation/water-saving",
    methods=["GET", "POST"]
)
def water_saving():

    access = farmer_required()

    if access:

        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    if request.method == "POST":

        data = (
            request.get_json(
                silent=True
            )
            or request.form.to_dict()
        )

    else:

        data = request.args.to_dict()

    area = safe_float(
        data.get(
            "area",
            1
        ),
        1
    )

    daily_need = safe_float(
        data.get(
            "daily_need_mm",
            4
        ),
        4
    )

    current_method = str(
        data.get(
            "current_method",
            "flood"
        )
    ).lower()

    target_method = str(
        data.get(
            "target_method",
            "drip"
        )
    ).lower()

    current_efficiency = (
        IRRIGATION_EFFICIENCY.get(
            current_method,
            0.50
        )
    )

    target_efficiency = (
        IRRIGATION_EFFICIENCY.get(
            target_method,
            0.90
        )
    )

    litres_per_mm_per_acre = 4046.86

    current_water = (
        daily_need
        / current_efficiency
        * area
        * litres_per_mm_per_acre
    )

    target_water = (
        daily_need
        / target_efficiency
        * area
        * litres_per_mm_per_acre
    )

    saving = max(
        current_water
        - target_water,
        0
    )

    percentage = (

        saving
        / current_water
        * 100

        if current_water > 0

        else 0
    )

    return jsonify({

        "success": True,

        "area_acres": round(
            area,
            2
        ),

        "daily_need_mm": round(
            daily_need,
            2
        ),

        "current_method": current_method,

        "target_method": target_method,

        "current_water_litres": round(
            current_water,
            0
        ),

        "target_water_litres": round(
            target_water,
            0
        ),

        "water_saved_litres": round(
            saving,
            0
        ),

        "saving_percent": round(
            percentage,
            1
        ),

    })


# ============================================================
# SUPPORTED CROPS
# ============================================================

@irrigation_bp.route(
    "/api/irrigation/crops"
)
def irrigation_crops():

    return jsonify({

        "success": True,

        "count": len(
            CROP_WATER_REQUIREMENTS
        ),

        "crops": [

            {
                "id": key,

                "name": value[
                    "name"
                ],

                "water_need": value[
                    "water_need"
                ],

                "daily_mm": value[
                    "daily_mm"
                ],

                "root_depth": value[
                    "root_depth"
                ],

            }

            for key, value
            in CROP_WATER_REQUIREMENTS.items()
        ]

    })


# ============================================================
# IRRIGATION METHODS
# ============================================================

@irrigation_bp.route(
    "/api/irrigation/methods"
)
def irrigation_methods():

    return jsonify({

        "success": True,

        "methods": [

            {
                "id": key,

                "efficiency": round(
                    value * 100,
                    1
                ),

            }

            for key, value
            in IRRIGATION_EFFICIENCY.items()
        ]

    })


# ============================================================
# IRRIGATION HEALTH
# ============================================================

@irrigation_bp.route(
    "/api/irrigation/health"
)
def irrigation_health():

    return jsonify({

        "success": True,

        "module": "Smart Irrigation",

        "status": "ready",

        "application": "KisanVision360+",

        "features": [

            "Weather-aware irrigation",

            "Crop water requirement",

            "Rainfall adjustment",

            "Temperature adjustment",

            "Humidity adjustment",

            "Soil moisture support",

            "Water saving calculation",

            "Irrigation method comparison",

            "Drip efficiency analysis",

            "Smart irrigation priority",

            "Farmer profile integration",

            "Crop Advisor integration ready",

            "Notification integration ready",

        ],

        "supported_crops": len(
            CROP_WATER_REQUIREMENTS
        ),

    })
