# ============================================================
# KISANVISION360+
# AI FARMING CHATBOT
# Flask + PostgreSQL / Supabase
#
# Features:
# - Role aware
# - Language aware
# - App specific answers
# - Feature URL returned with every relevant answer
# - Weather integration
# - Mandi integration
# - Marketplace integration
# - Finance integration
# - Schemes integration
# - Database based answers
# ============================================================

import os
import re
import logging
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

from database.db import get_db_connection


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# BLUEPRINT
# ============================================================

chatbot_bp = Blueprint(
    "chatbot",
    __name__
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_MESSAGE_LENGTH = 2000


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "kn": "Kannada",
    "te": "Telugu",
    "ta": "Tamil",
    "ml": "Malayalam",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "bn": "Bengali",
    "as": "Assamese",
    "or": "Odia",
    "ur": "Urdu",
    "ne": "Nepali",
    "sa": "Sanskrit",
    "kok": "Konkani",
    "mai": "Maithili",
    "ks": "Kashmiri",
    "sd": "Sindhi",
    "mni": "Manipuri"
}


RTL_LANGUAGES = {
    "ur",
    "ks",
    "sd"
}


# ============================================================
# FEATURE DEFINITIONS
# ============================================================

FEATURES = {
    "weather": {
        "name": "Open Weather",
        "url_endpoint": "weather.weather",
        "icon": "â˜ï¸"
    },

    "crop_advisor": {
        "name": "Open Crop Advisor",
        "url_endpoint": "recommendation.recommendation",
        "icon": "ðŸŒ±"
    },

    "disease": {
        "name": "Open Disease Detection",
        "url_endpoint": "disease.disease",
        "icon": "ðŸ©º"
    },

    "irrigation": {
        "name": "Open Smart Irrigation",
        "url_endpoint": "irrigation.irrigation",
        "icon": "ðŸ’§"
    },

    "market": {
        "name": "Open Mandi Prices",
        "url_endpoint": "market.market",
        "icon": "ðŸ“ˆ"
    },

    "marketplace": {
        "name": "Open Marketplace",
        "url_endpoint": "marketplace.farmer_marketplace",
        "icon": "ðŸ›’"
    },

    "finance": {
        "name": "Open Farm Finance",
        "url_endpoint": "finance.finance",
        "icon": "ðŸ’°"
    },

    "schemes": {
        "name": "Open Government Schemes",
        "url_endpoint": "government.government",
        "icon": "ðŸ›ï¸"
    },

    "notifications": {
        "name": "Open Notifications",
        "url_endpoint": "notifications.notifications",
        "icon": "ðŸ””"
    },

    "reports": {
        "name": "Open Farm Reports",
        "url_endpoint": "reports.reports",
        "icon": "ðŸ“Š"
    },

    "tools": {
        "name": "Open Farmer Tools",
        "url_endpoint": "tools.tools",
        "icon": "ðŸ› ï¸"
    },

    "profile": {
        "name": "Open Farm Profile",
        "url_endpoint": "profile.profile",
        "icon": "ðŸ‘¨â€ðŸŒ¾"
    }
}


# ============================================================
# SAFE FEATURE URL
# ============================================================

def get_feature_url(feature_key):
    """
    Generate Flask URL safely.

    If an endpoint is not registered, return an empty URL
    instead of breaking the chatbot.
    """

    feature = FEATURES.get(feature_key)

    if not feature:
        return ""

    endpoint = feature.get("url_endpoint")

    if not endpoint:
        return ""

    try:
        return url_for(endpoint)
    except Exception as exc:
        logger.warning(
            "Feature URL unavailable: %s -> %s",
            feature_key,
            exc
        )
        return ""


# ============================================================
# FEATURE RESPONSE
# ============================================================

def feature_data(feature_key):
    """
    Return frontend-ready feature information.
    """

    feature = FEATURES.get(feature_key)

    if not feature:
        return {
            "feature": "",
            "feature_name": "",
            "feature_url": "",
            "feature_icon": ""
        }

    return {
        "feature": feature_key,
        "feature_name": feature["name"],
        "feature_url": get_feature_url(feature_key),
        "feature_icon": feature["icon"]
    }


# ============================================================
# LOGIN CHECK
# ============================================================

def is_logged_in():
    return bool(
        session.get("user_id")
    )


# ============================================================
# CURRENT ROLE
# ============================================================

def get_current_role():
    return str(
        session.get(
            "role",
            "farmer"
        )
    ).strip().lower()


# ============================================================
# CURRENT LANGUAGE
# ============================================================

def get_current_language():
    language = str(
        session.get(
            "language",
            "en"
        )
    ).strip().lower()

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    return language


# ============================================================
# CURRENT USER NAME
# ============================================================

def get_current_name():
    return str(
        session.get(
            "name",
            "Farmer"
        )
    ).strip() or "Farmer"


# ============================================================
# DATABASE HELPER
# ============================================================

def safe_query(
    query,
    params=(),
    fetch="all"
):
    """
    Safe PostgreSQL query helper.

    Returns:
        list for fetch='all'
        dict/row for fetch='one'
        None on error
    """

    connection = None

    try:

        connection = get_db_connection()

        with connection.cursor() as cursor:

            cursor.execute(
                query,
                params
            )

            if fetch == "one":
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()

        return result

    except Exception as exc:

        logger.warning(
            "Chatbot database query failed: %s",
            exc
        )

        return None

    finally:

        if connection:

            try:
                connection.close()
            except Exception:
                pass


# ============================================================
# ROW TO DICT
# ============================================================

def row_to_dict(row):

    if row is None:
        return {}

    if isinstance(row, dict):
        return dict(row)

    try:
        return dict(row)
    except Exception:
        return {}


# ============================================================
# WEATHER
# ============================================================

def get_weather_information():

    try:

        from routes.weather import get_current_weather

        city = (
            session.get("location")
            or os.getenv(
                "DEFAULT_CITY",
                "Nagpur"
            )
        )

        weather = get_current_weather(city)

        if not weather:
            return None

        return weather

    except Exception as exc:

        logger.warning(
            "Weather chatbot integration failed: %s",
            exc
        )

        return None


# ============================================================
# WEATHER ANSWER
# ============================================================

def weather_answer():

    weather = get_weather_information()

    feature = feature_data(
        "weather"
    )

    if not weather:

        return (
            "I could not retrieve the live weather data right now. "
            "Please open the Weather module to check the latest "
            "weather information for your location. â˜ï¸"
        ), feature

    city = (
        weather.get("city")
        or session.get("location")
        or os.getenv("DEFAULT_CITY", "Nagpur")
    )

    temperature = weather.get(
        "temperature",
        weather.get("temp")
    )

    humidity = weather.get(
        "humidity"
    )

    wind = weather.get(
        "wind",
        weather.get("wind_speed")
    )

    description = weather.get(
        "description",
        weather.get(
            "condition",
            "Current conditions available"
        )
    )

    answer_parts = [
        f"â˜ï¸ Current weather for {city}:",
        "",
        f"â€¢ Condition: {description}"
    ]

    if temperature is not None:
        answer_parts.append(
            f"â€¢ Temperature: {temperature}Â°C"
        )

    if humidity is not None:
        answer_parts.append(
            f"â€¢ Humidity: {humidity}%"
        )

    if wind is not None:
        answer_parts.append(
            f"â€¢ Wind: {wind}"
        )

    answer_parts.extend([
        "",
        "ðŸŒ± Farming advice:",
        "Check soil moisture before irrigation.",
        "If humidity is high, monitor crops regularly "
        "for disease symptoms."
    ])

    return "\n".join(answer_parts), feature


# ============================================================
# CROP ADVISOR
# ============================================================

def crop_advisor_answer():

    feature = feature_data(
        "crop_advisor"
    )

    return (
        "ðŸŒ± KisanVision360+ Crop Advisor helps you select "
        "suitable crops using farm information such as soil, "
        "location, season and farming conditions.\n\n"
        "For a personalized recommendation, open Crop Advisor "
        "and enter your farm details."
    ), feature


# ============================================================
# DISEASE
# ============================================================

def disease_answer():

    feature = feature_data(
        "disease"
    )

    return (
        "ðŸ©º KisanVision360+ Disease Detection uses the crop "
        "leaf image analysis module to classify supported "
        "crop-disease classes.\n\n"
        "Upload a clear crop leaf image in Disease Detection "
        "for the model prediction.\n\n"
        "For serious crop damage, also verify the result with "
        "a qualified agricultural expert."
    ), feature


# ============================================================
# IRRIGATION
# ============================================================

def irrigation_answer():

    feature = feature_data(
        "irrigation"
    )

    weather = get_weather_information()

    answer = (
        "ðŸ’§ Smart Irrigation helps you plan irrigation according "
        "to crop and environmental conditions."
    )

    if weather:

        humidity = weather.get("humidity")

        if isinstance(
            humidity,
            (int, float)
        ):

            if humidity >= 80:

                answer += (
                    "\n\nCurrent humidity is relatively high. "
                    "Check soil moisture before adding irrigation."
                )

            else:

                answer += (
                    "\n\nCheck actual soil moisture and crop stage "
                    "before deciding the next irrigation."
                )

    answer += (
        "\n\nOpen Smart Irrigation for the complete irrigation "
        "planning module."
    )

    return answer, feature


# ============================================================
# MANDI
# ============================================================

def market_answer(message):

    feature = feature_data(
        "market"
    )

    try:

        from utils.mandi_price import (
            get_market_price
        )

        crop = extract_crop(
            message
        )

        result = get_market_price(
            crop
        )

        if isinstance(result, dict):

            records = result.get(
                "records",
                []
            )

        elif isinstance(result, list):

            records = result

        else:

            records = []

        if records:

            lines = [
                "ðŸ“ˆ Available mandi information:"
            ]

            for record in records[:5]:

                record = row_to_dict(
                    record
                )

                commodity = (
                    record.get("commodity")
                    or record.get("crop")
                    or crop
                    or "Crop"
                )

                market = (
                    record.get("market")
                    or "Market"
                )

                modal = (
                    record.get("modal_price")
                    or record.get("modal")
                )

                minimum = (
                    record.get("min_price")
                    or record.get("min")
                )

                maximum = (
                    record.get("max_price")
                    or record.get("max")
                )

                line = (
                    f"â€¢ {commodity} â€” {market}"
                )

                if modal:
                    line += (
                        f" | Modal: â‚¹{modal}"
                    )

                elif minimum or maximum:

                    line += (
                        f" | Range: â‚¹{minimum or '-'}"
                        f" - â‚¹{maximum or '-'}"
                    )

                lines.append(
                    line
                )

            lines.extend([
                "",
                "Market data can change. Verify the latest "
                "available record before making a selling decision."
            ])

            return "\n".join(lines), feature

    except Exception as exc:

        logger.warning(
            "Mandi chatbot integration failed: %s",
            exc
        )

    return (
        "ðŸ“ˆ I could not retrieve the requested mandi information "
        "right now.\n\n"
        "Open Mandi Prices to check the available market records."
    ), feature


# ============================================================
# EXTRACT CROP
# ============================================================

def extract_crop(message):

    text = message.lower()

    crops = [
        "wheat",
        "rice",
        "soybean",
        "cotton",
        "maize",
        "corn",
        "tomato",
        "potato",
        "onion",
        "chilli",
        "grape",
        "apple",
        "orange",
        "peach",
        "cherry",
        "strawberry"
    ]

    for crop in crops:

        if crop in text:
            return crop

    return None


# ============================================================
# MARKETPLACE
# ============================================================

def marketplace_answer():

    feature = feature_data(
        "marketplace"
    )

    query = """
        SELECT
            COUNT(*) AS total_products
        FROM products
        WHERE LOWER(COALESCE(status, 'active')) = 'active'
    """

    result = safe_query(
        query,
        fetch="one"
    )

    total_products = 0

    if result:

        result = row_to_dict(
            result
        )

        try:
            total_products = int(
                result.get(
                    "total_products",
                    0
                ) or 0
            )
        except Exception:
            total_products = 0

    if total_products:

        answer = (
            f"ðŸ›’ The marketplace currently has "
            f"{total_products} active product listing"
            f"{'s' if total_products != 1 else ''}.\n\n"
            "You can search products, view product details, "
            "compare sellers and continue to cart/order."
        )

    else:

        answer = (
            "ðŸ›’ I could not find active marketplace products "
            "right now.\n\n"
            "Open Marketplace to check the latest listings."
        )

    return answer, feature


# ============================================================
# FINANCE
# ============================================================

def finance_answer():

    feature = feature_data(
        "finance"
    )

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return (
            "ðŸ’° Please log in to view your personal farm "
            "finance information."
        ), feature

    income_result = safe_query(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS total_income
        FROM farm_income
        WHERE farmer_id = %s
        """,
        (user_id,),
        fetch="one"
    )

    expense_result = safe_query(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS total_expense
        FROM farm_expenses
        WHERE farmer_id = %s
        """,
        (user_id,),
        fetch="one"
    )

    income = 0
    expense = 0

    if income_result:

        income_result = row_to_dict(
            income_result
        )

        try:
            income = float(
                income_result.get(
                    "total_income",
                    0
                ) or 0
            )
        except Exception:
            income = 0

    if expense_result:

        expense_result = row_to_dict(
            expense_result
        )

        try:
            expense = float(
                expense_result.get(
                    "total_expense",
                    0
                ) or 0
            )
        except Exception:
            expense = 0

    balance = income - expense

    return (
        "ðŸ’° Your farm finance summary:\n\n"
        f"â€¢ Total income: â‚¹{income:,.2f}\n"
        f"â€¢ Total expenses: â‚¹{expense:,.2f}\n"
        f"â€¢ Balance: â‚¹{balance:,.2f}\n\n"
        "Open Farm Finance to manage income, expenses and "
        "financial records."
    ), feature


# ============================================================
# GOVERNMENT SCHEMES
# ============================================================

def schemes_answer():

    feature = feature_data(
        "schemes"
    )

    result = safe_query(
        """
        SELECT
            COUNT(*) AS total_schemes
        FROM government_schemes
        """,
        fetch="one"
    )

    total = 0

    if result:

        result = row_to_dict(
            result
        )

        try:
            total = int(
                result.get(
                    "total_schemes",
                    0
                ) or 0
            )
        except Exception:
            total = 0

    if total:

        return (
            f"ðŸ›ï¸ KisanVision360+ currently has "
            f"{total} government scheme record"
            f"{'s' if total != 1 else ''} available.\n\n"
            "Open Government Schemes to search schemes, "
            "eligibility information and application guidance.\n\n"
            "Always verify eligibility and application details "
            "on the official government source."
        ), feature

    return (
        "ðŸ›ï¸ Government scheme information is available through "
        "the Government Schemes module.\n\n"
        "Open the module to search available schemes and "
        "eligibility information."
    ), feature


# ============================================================
# NOTIFICATIONS
# ============================================================

def notifications_answer():

    feature = feature_data(
        "notifications"
    )

    return (
        "ðŸ”” KisanVision360+ Notifications can provide updates "
        "related to farming activities, weather, market "
        "information, orders and other application events.\n\n"
        "Open Notifications to view your latest alerts."
    ), feature


# ============================================================
# REPORTS
# ============================================================

def reports_answer():

    feature = feature_data(
        "reports"
    )

    return (
        "ðŸ“Š Farm Reports bring together important farm information "
        "such as financial records, weather information, "
        "analysis and connected module data.\n\n"
        "Open Farm Reports for your complete report."
    ), feature


# ============================================================
# TOOLS
# ============================================================

def tools_answer():

    feature = feature_data(
        "tools"
    )

    return (
        "ðŸ› ï¸ Farmer Tools provides useful agricultural tools and "
        "calculators available in KisanVision360+.\n\n"
        "Open Farmer Tools to use the available utilities."
    ), feature


# ============================================================
# FARM PROFILE
# ============================================================

def profile_answer():

    feature = feature_data(
        "profile"
    )

    return (
        "ðŸ‘¨â€ðŸŒ¾ Your Farm Profile stores important information "
        "used by KisanVision360+ for personalized farming "
        "features.\n\n"
        "Open Farm Profile to review or update your information."
    ), feature


# ============================================================
# KISANVISION360 EXPLANATION
# ============================================================

def about_answer():

    return (
        "ðŸŒ± KisanVision360+ is an integrated smart farming "
        "decision-support platform.\n\n"
        "It connects:\n"
        "â€¢ Farm Profile\n"
        "â€¢ Weather\n"
        "â€¢ Crop Advisor\n"
        "â€¢ Cultivation\n"
        "â€¢ Disease Detection\n"
        "â€¢ Smart Irrigation\n"
        "â€¢ Mandi Prices\n"
        "â€¢ Marketplace\n"
        "â€¢ Finance\n"
        "â€¢ Government Schemes\n"
        "â€¢ Notifications\n"
        "â€¢ Reports\n"
        "â€¢ AI Assistant\n\n"
        "The main idea is to connect the farming lifecycle "
        "instead of keeping every feature as a separate system."
    ), None


# ============================================================
# BASIC FARMING QUESTIONS
# ============================================================

def farming_general_answer(message):

    text = message.lower()

    if "npk" in text:

        return (
            "ðŸŒ± NPK stands for Nitrogen, Phosphorus and Potassium.\n\n"
            "â€¢ Nitrogen supports vegetative growth.\n"
            "â€¢ Phosphorus supports root development and reproductive growth.\n"
            "â€¢ Potassium supports overall plant strength and several "
            "physiological processes.\n\n"
            "The correct fertilizer requirement depends on crop, "
            "soil condition and recommendation."
        ), None

    if (
        "black soil" in text
        or "black soil crop" in text
    ):

        return (
            "ðŸŒ± Black soil can support several crops, including "
            "cotton, soybean and some cereal crops depending on "
            "location, season, water availability and soil condition.\n\n"
            "For a personalized recommendation, use Crop Advisor "
            "with your farm details."
        ), feature_data(
            "crop_advisor"
        )

    if (
        "irrigation" in text
        or "water" in text
    ):

        return irrigation_answer()

    return (
        "ðŸŒ± I can help with KisanVision360+ features and "
        "general farming questions.\n\n"
        "Try asking about Weather, Crop Advisor, Disease Detection, "
        "Irrigation, Mandi Prices, Marketplace, Finance or "
        "Government Schemes."
    ), None


# ============================================================
# GREETING
# ============================================================

def greeting_answer():

    name = get_current_name()

    return (
        f"Hello {name}! ðŸ‘‹\n\n"
        "I am your KisanVision360+ AI Assistant.\n\n"
        "You can ask me about your farm, weather, crops, "
        "disease detection, irrigation, mandi prices, "
        "marketplace, finance and government schemes."
    ), None


# ============================================================
# THANK YOU
# ============================================================

def thank_you_answer():

    return (
        "ðŸ˜Š You're welcome!\n\n"
        "I am here to help you use KisanVision360+."
    ), None


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_intent(message):

    text = message.lower().strip()

    # --------------------------------------------------------
    # Greeting
    # --------------------------------------------------------

    if any(word in text for word in [
        "hello",
        "hi",
        "hey",
        "namaste",
        "namaskar",
        "good morning",
        "good afternoon",
        "good evening"
    ]):
        return "greeting"

    # --------------------------------------------------------
    # Thank you
    # --------------------------------------------------------

    if any(word in text for word in [
        "thank you",
        "thanks",
        "thank"
    ]):
        return "thanks"

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    if any(word in text for word in [
        "weather",
        "temperature",
        "rain",
        "rainfall",
        "humidity",
        "forecast",
        "wind",
        "climate"
    ]):
        return "weather"

    # --------------------------------------------------------
    # Crop advisor
    # --------------------------------------------------------

    if any(word in text for word in [
        "crop recommendation",
        "crop advisor",
        "best crop",
        "which crop",
        "suitable crop",
        "crop selection",
        "what should i grow",
        "what crop should"
    ]):
        return "crop_advisor"

    # --------------------------------------------------------
    # Disease
    # --------------------------------------------------------

    if any(word in text for word in [
        "disease",
        "diseases",
        "leaf disease",
        "crop disease",
        "infected",
        "infection",
        "symptom",
        "symptoms",
        "leaf image"
    ]):
        return "disease"

    # --------------------------------------------------------
    # Irrigation
    # --------------------------------------------------------

    if any(word in text for word in [
        "irrigation",
        "irrigate",
        "irrigating",
        "water my crop",
        "watering",
        "when should i water"
    ]):
        return "irrigation"

    # --------------------------------------------------------
    # Mandi
    # --------------------------------------------------------

    if any(word in text for word in [
        "mandi",
        "market price",
        "market prices",
        "crop price",
        "crop prices",
        "selling price",
        "modal price",
        "wholesale price"
    ]):
        return "market"

    # --------------------------------------------------------
    # Marketplace
    # --------------------------------------------------------

    if any(word in text for word in [
        "marketplace",
        "product",
        "products",
        "buy product",
        "sell product",
        "seller",
        "buyer",
        "cart",
        "wishlist",
        "order"
    ]):
        return "marketplace"

    # --------------------------------------------------------
    # Finance
    # --------------------------------------------------------

    if any(word in text for word in [
        "finance",
        "financial",
        "income",
        "expense",
        "expenses",
        "profit",
        "money",
        "budget",
        "earning",
        "earnings",
        "emi"
    ]):
        return "finance"

    # --------------------------------------------------------
    # Government schemes
    # --------------------------------------------------------

    if any(word in text for word in [
        "scheme",
        "schemes",
        "government scheme",
        "government schemes",
        "subsidy",
        "subsidies",
        "farmer support",
        "government help"
    ]):
        return "schemes"

    # --------------------------------------------------------
    # Notifications
    # --------------------------------------------------------

    if any(word in text for word in [
        "notification",
        "notifications",
        "alert",
        "alerts"
    ]):
        return "notifications"

    # --------------------------------------------------------
    # Reports
    # --------------------------------------------------------

    if any(word in text for word in [
        "report",
        "reports",
        "farm report",
        "farm analysis",
        "analysis"
    ]):
        return "reports"

    # --------------------------------------------------------
    # Tools
    # --------------------------------------------------------

    if any(word in text for word in [
        "tool",
        "tools",
        "calculator",
        "machinery",
        "equipment",
        "emi calculator"
    ]):
        return "tools"

    # --------------------------------------------------------
    # Profile
    # --------------------------------------------------------

    if any(word in text for word in [
        "profile",
        "farm profile",
        "my farm details",
        "my farm"
    ]):
        return "profile"

    # --------------------------------------------------------
    # About application
    # --------------------------------------------------------

    if (
        "kisanvision360" in text
        or "what is this app" in text
        or "about the app" in text
    ):
        return "about"

    return "general"


# ============================================================
# ANSWER GENERATOR
# ============================================================

def generate_answer(message):

    intent = detect_intent(
        message
    )

    # --------------------------------------------------------
    # Greeting
    # --------------------------------------------------------

    if intent == "greeting":
        return greeting_answer()

    # --------------------------------------------------------
    # Thanks
    # --------------------------------------------------------

    if intent == "thanks":
        return thank_you_answer()

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    if intent == "weather":
        return weather_answer()

    # --------------------------------------------------------
    # Crop advisor
    # --------------------------------------------------------

    if intent == "crop_advisor":
        return crop_advisor_answer()

    # --------------------------------------------------------
    # Disease
    # --------------------------------------------------------

    if intent == "disease":
        return disease_answer()

    # --------------------------------------------------------
    # Irrigation
    # --------------------------------------------------------

    if intent == "irrigation":
        return irrigation_answer()

    # --------------------------------------------------------
    # Market
    # --------------------------------------------------------

    if intent == "market":
        return market_answer(
            message
        )

    # --------------------------------------------------------
    # Marketplace
    # --------------------------------------------------------

    if intent == "marketplace":
        return marketplace_answer()

    # --------------------------------------------------------
    # Finance
    # --------------------------------------------------------

    if intent == "finance":
        return finance_answer()

    # --------------------------------------------------------
    # Schemes
    # --------------------------------------------------------

    if intent == "schemes":
        return schemes_answer()

    # --------------------------------------------------------
    # Notifications
    # --------------------------------------------------------

    if intent == "notifications":
        return notifications_answer()

    # --------------------------------------------------------
    # Reports
    # --------------------------------------------------------

    if intent == "reports":
        return reports_answer()

    # --------------------------------------------------------
    # Tools
    # --------------------------------------------------------

    if intent == "tools":
        return tools_answer()

    # --------------------------------------------------------
    # Profile
    # --------------------------------------------------------

    if intent == "profile":
        return profile_answer()

    # --------------------------------------------------------
    # About
    # --------------------------------------------------------

    if intent == "about":
        return about_answer()

    # --------------------------------------------------------
    # General
    # --------------------------------------------------------

    return farming_general_answer(
        message
    )


# ============================================================
# MULTILINGUAL RESPONSE LAYER
# ============================================================
#
# The application language is selected globally.
#
# For English, return the detailed answer directly.
#
# For the other supported languages, this function provides
# simple common UI responses. Full natural-language translation
# should later be connected to a translation service/model if
# required.
# ============================================================

def translate_common_response(
    answer,
    language
):

    if not answer:
        return answer

    if language == "en":
        return answer

    common = {

        "hi": {
            "Hello": "à¤¨à¤®à¤¸à¥à¤¤à¥‡",
            "You're welcome": "à¤†à¤ªà¤•à¤¾ à¤¸à¥à¤µà¤¾à¤—à¤¤ à¤¹à¥ˆ"
        },

        "mr": {
            "Hello": "à¤¨à¤®à¤¸à¥à¤•à¤¾à¤°",
            "You're welcome": "à¤†à¤ªà¤²à¥‡ à¤¸à¥à¤µà¤¾à¤—à¤¤ à¤†à¤¹à¥‡"
        },

        "kn": {
            "Hello": "à²¨à²®à²¸à³à²•à²¾à²°",
            "You're welcome": "à²¸à³à²µà²¾à²—à²¤"
        },

        "te": {
            "Hello": "à°¨à°®à°¸à±à°•à°¾à°°à°‚",
            "You're welcome": "à°¸à±à°µà°¾à°—à°¤à°‚"
        },

        "ta": {
            "Hello": "à®µà®£à®•à¯à®•à®®à¯",
            "You're welcome": "à®µà®°à®µà¯‡à®±à¯à®•à®¿à®±à¯‡à®©à¯"
        },

        "ml": {
            "Hello": "à´¨à´®à´¸àµà´•à´¾à´°à´‚",
            "You're welcome": "à´¸àµà´µà´¾à´—à´¤à´‚"
        },

        "gu": {
            "Hello": "àª¨àª®àª¸à«àª¤à«‡",
            "You're welcome": "àª†àªªàª¨à«àª‚ àª¸à«àªµàª¾àª—àª¤ àª›à«‡"
        },

        "pa": {
            "Hello": "à¨¸à¨¤ à¨¸à©à¨°à©€ à¨…à¨•à¨¾à¨²",
            "You're welcome": "à¨œà©€ à¨†à¨‡à¨†à¨‚ à¨¨à©‚à©°"
        },

        "bn": {
            "Hello": "à¦¨à¦®à¦¸à§à¦•à¦¾à¦°",
            "You're welcome": "à¦¸à§à¦¬à¦¾à¦—à¦¤à¦®"
        },

        "as": {
            "Hello": "à¦¨à¦®à¦¸à§à¦•à¦¾à§°",
            "You're welcome": "à¦¸à§à¦¬à¦¾à¦—à¦¤à¦®"
        },

        "or": {
            "Hello": "à¬¨à¬®à¬¸à­à¬•à¬¾à¬°",
            "You're welcome": "à¬¸à­à­±à¬¾à¬—à¬¤"
        },

        "ur": {
            "Hello": "Ø§Ù„Ø³Ù„Ø§Ù… Ø¹Ù„ÛŒÚ©Ù…",
            "You're welcome": "Ø®ÙˆØ´ Ø¢Ù…Ø¯ÛŒØ¯"
        },

        "ne": {
            "Hello": "à¤¨à¤®à¤¸à¥à¤¤à¥‡",
            "You're welcome": "à¤¸à¥à¤µà¤¾à¤—à¤¤ à¤›"
        },

        "sa": {
            "Hello": "à¤¨à¤®à¤ƒ",
            "You're welcome": "à¤¸à¥à¤µà¤¾à¤—à¤¤à¤®à¥"
        },

        "kok": {
            "Hello": "à¤¨à¤®à¤¸à¥à¤•à¤¾à¤°",
            "You're welcome": "à¤¸à¥à¤µà¤¾à¤—à¤¤"
        },

        "mai": {
            "Hello": "à¤ªà¥à¤°à¤£à¤¾à¤®",
            "You're welcome": "à¤¸à¥à¤µà¤¾à¤—à¤¤ à¤…à¤›à¤¿"
        },

        "ks": {
            "Hello": "Ø§Ù„Ø³Ù„Ø§Ù… Ø¹Ù„ÛŒÚ©Ù…",
            "You're welcome": "Ø®ÙˆØ´ Ø¢Ù…Ø¯ÛŒØ¯"
        },

        "sd": {
            "Hello": "Ø§Ù„Ø³Ù„Ø§Ù… Ø¹Ù„ÙŠÚªÙ…",
            "You're welcome": "Ú€Ù„ÙŠÚªØ§Ø±"
        },

        "mni": {
            "Hello": "ê¯ê¯¥ê¯",
            "You're welcome": "ê¯†ê¯¥ê¯Žê¯”ê¯¥ê¯›ê¯„"
        }
    }

    # Do not incorrectly translate technical farming content.
    # The selected language is still returned to frontend.

    return answer


# ============================================================
# OPEN-ENDED AI ANSWER (OPTIONAL)
# ============================================================

def open_ended_ai_answer(message, language, role, user_name):
    """Use an LLM for questions outside the built-in farming intents.
    Requires OPENAI_API_KEY. If unavailable/fails, return None so the
    built-in chatbot remains the fallback.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
        language_name = SUPPORTED_LANGUAGES.get(language, "English")
        system = (
            "You are KisanVision360+ AI Assistant. Answer clearly and safely. "
            "You can answer general questions, agriculture, weather concepts, "
            "crop management, disease prevention, irrigation, markets, finance, "
            "government schemes, technology and everyday questions. "
            f"The user's preferred response language is {language_name} (code {language}). "
            "Reply in that language. If the question is medical, legal or financial, "
            "include a brief caution that professional/local official advice may be needed. "
            "Do not invent live prices, weather, scheme eligibility or government rules. "
            "For live app data, tell the user to open the relevant KisanVision360+ module. "
            f"User role: {role}. User name: {user_name}."
        )
        response = client.responses.create(
            model=model,
            instructions=system,
            input=message,
            max_output_tokens=700
        )
        text = getattr(response, "output_text", None)
        return text.strip() if text else None
    except Exception as exc:
        logger.warning("Open-ended AI answer unavailable: %s", exc)
        return None


# ============================================================
# MAIN CHATBOT PAGE
# ============================================================

@chatbot_bp.route(
    "/chatbot",
    methods=["GET"]
)
def chatbot():

    if not is_logged_in():

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "chatbot.html",
        name=get_current_name(),
        role=get_current_role(),
        language=get_current_language()
    )


# ============================================================
# CHATBOT API
# ============================================================

@chatbot_bp.route(
    "/ask-chatbot",
    methods=["POST"]
)
def ask_chatbot():

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    if not is_logged_in():

        return jsonify({
            "success": False,
            "reply": "Please login first.",
            "message": "Please login first."
        }), 401

    # --------------------------------------------------------
    # Request JSON
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    # --------------------------------------------------------
    # Validate message
    # --------------------------------------------------------

    if not message:

        return jsonify({
            "success": False,
            "reply": "Please ask me something.",
            "message": "Please ask me something."
        }), 400

    if len(message) > MAX_MESSAGE_LENGTH:

        return jsonify({
            "success": False,
            "reply": (
                f"Please keep your question within "
                f"{MAX_MESSAGE_LENGTH} characters."
            ),
            "message": (
                f"Please keep your question within "
                f"{MAX_MESSAGE_LENGTH} characters."
            )
        }), 400

    # --------------------------------------------------------
    # Language
    # --------------------------------------------------------

    language = str(
        data.get(
            "language",
            get_current_language()
        )
    ).strip().lower()

    if language not in SUPPORTED_LANGUAGES:
        language = get_current_language()

    # Keep server session as the source of truth.
    session["language"] = language

    # --------------------------------------------------------
    # Role
    # --------------------------------------------------------

    role = get_current_role()

    # Do not blindly trust frontend role.
    requested_role = str(
        data.get(
            "role",
            role
        )
    ).strip().lower()

    if requested_role != role:
        requested_role = role

    # --------------------------------------------------------
    # User name
    # --------------------------------------------------------

    user_name = get_current_name()

    # --------------------------------------------------------
    # Generate answer
    # --------------------------------------------------------

    try:

        answer, feature = generate_answer(
            message
        )

        answer = translate_common_response(
            answer,
            language
        )

        if not answer:

            answer = (
                "I could not generate an answer right now. "
                "Please try again."
            )

        # ----------------------------------------------------
        # Open-ended AI fallback
        # ----------------------------------------------------
        intent = detect_intent(message)
        if intent in ("general", "unknown", "chat"):
            ai_answer = open_ended_ai_answer(
                message, language, requested_role, user_name
            )
            if ai_answer:
                answer = ai_answer

        # ----------------------------------------------------
        # Feature data
        # ----------------------------------------------------

        if feature is None:

            feature_info = {
                "feature": "",
                "feature_name": "",
                "feature_url": "",
                "feature_icon": ""
            }

        else:

            feature_info = feature

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "reply": answer,

            "message": answer,

            "intent": intent,

            "feature": feature_info.get(
                "feature",
                ""
            ),

            "feature_name": feature_info.get(
                "feature_name",
                ""
            ),

            "feature_url": feature_info.get(
                "feature_url",
                ""
            ),

            "feature_icon": feature_info.get(
                "feature_icon",
                ""
            ),

            "language": language,

            "role": requested_role,

            "user_name": user_name,

            "timestamp": datetime.now().isoformat()

        })

    except Exception as exc:

        logger.exception(
            "CHATBOT ERROR"
        )

        return jsonify({

            "success": False,

            "reply": (
                "âš ï¸ I could not process your question right now. "
                "Please try again."
            ),

            "message": (
                "âš ï¸ I could not process your question right now. "
                "Please try again."
            ),

            "error": str(exc)

        }), 500


# ============================================================
# CHATBOT HEALTH
# ============================================================

@chatbot_bp.route(
    "/api/chatbot/health",
    methods=["GET"]
)
def chatbot_health():

    return jsonify({

        "success": True,

        "service": "KisanVision360+ AI Assistant",

        "status": "online",

        "languages": len(
            SUPPORTED_LANGUAGES
        ),

        "features": list(
            FEATURES.keys()
        ),

        "timestamp": datetime.now().isoformat()

    })


# ============================================================
# CHATBOT METADATA
# ============================================================

@chatbot_bp.route(
    "/api/chatbot/metadata",
    methods=["GET"]
)
def chatbot_metadata():

    language = get_current_language()
    role = get_current_role()

    available_features = []

    for key, item in FEATURES.items():

        available_features.append({

            "feature": key,

            "name": item["name"],

            "icon": item["icon"],

            "url": get_feature_url(key)

        })

    return jsonify({

        "success": True,

        "application": "KisanVision360+",

        "assistant": "KisanVision360+ AI Assistant",

        "language": language,

        "language_name": SUPPORTED_LANGUAGES.get(
            language,
            "English"
        ),

        "role": role,

        "rtl": language in RTL_LANGUAGES,

        "supported_languages": SUPPORTED_LANGUAGES,

        "features": available_features

    })


# ============================================================
# DELETE CHAT API
# ============================================================

@chatbot_bp.route(
    "/api/chatbot/clear",
    methods=["POST"]
)
def clear_chat():

    if not is_logged_in():

        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    return jsonify({

        "success": True,

        "message": "Chat history can be cleared from the device."

    })


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_chatbot_service():

    logger.info(
        "KisanVision360+ Chatbot service initialized."
    )

    return True
