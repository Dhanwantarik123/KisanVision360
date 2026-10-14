"""
KisanVision360+ Smart Notification Engine
Weather-aware notifications for farmers/consumers and SOS critical alerts.

This module is intentionally defensive: it can be imported by an existing Flask app
without requiring a particular ORM. It exposes pure decision functions plus a small
DB-adapter interface that existing routes can connect to.
"""

from datetime import datetime, timezone


def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def weather_irrigation_alert(
    rain_probability=0,
    rain_mm=0,
    temperature=0,
    humidity=0,
    wind_speed=0,
    crop=None,
):
    """
    Returns one actionable weather/farm alert.
    Rules:
      1) Rain expected -> delay irrigation
      2) Heavy rain expected -> avoid unnecessary irrigation
      3) High temp + low rain -> review/increase irrigation
      4) Suitable conditions -> irrigation recommended
      5) Strong wind -> review planned farm activity
    """
    rain_probability = _num(rain_probability)
    rain_mm = _num(rain_mm)
    temperature = _num(temperature)
    humidity = _num(humidity)
    wind_speed = _num(wind_speed)

    # Strong wind gets its own safety/farm-activity alert.
    if wind_speed >= 35:
        return {
            "category": "weather",
            "type": "strong_wind",
            "priority": "HIGH",
            "title": "💨 Strong Wind Alert",
            "message": "Strong winds are expected. Review planned farm activities.",
            "action": "weather",
            "crop": crop,
        }

    # Heavy rain takes precedence over normal rain.
    if rain_probability >= 70 and rain_mm >= 20:
        return {
            "category": "irrigation",
            "type": "heavy_rain",
            "priority": "HIGH",
            "title": "☔ Heavy Rain Expected",
            "message": "Heavy rain is expected. Avoid unnecessary irrigation.",
            "action": "irrigation",
            "crop": crop,
        }

    if rain_probability >= 50 or rain_mm >= 5:
        return {
            "category": "irrigation",
            "type": "rain_expected",
            "priority": "MEDIUM",
            "title": "🌧️ Rain Expected",
            "message": "Rain is expected. Consider delaying irrigation.",
            "action": "irrigation",
            "crop": crop,
        }

    # High heat with little rain: ask farmer to review/increase irrigation.
    if temperature >= 35 and rain_probability < 30 and rain_mm < 2:
        return {
            "category": "irrigation",
            "type": "heat_low_rain",
            "priority": "HIGH",
            "title": "🌡️ Heat & Low Rain Alert",
            "message": "High temperature and low expected rainfall. Review or increase irrigation.",
            "action": "irrigation",
            "crop": crop,
        }

    # Generic suitable-condition recommendation.
    if 18 <= temperature <= 34 and rain_probability < 30 and humidity < 85:
        return {
            "category": "irrigation",
            "type": "irrigation_recommended",
            "priority": "NORMAL",
            "title": "💧 Irrigation Recommended",
            "message": "Current conditions are suitable for reviewing scheduled irrigation.",
            "action": "irrigation",
            "crop": crop,
        }

    return None


def disease_risk_alert(
    humidity=0,
    temperature=0,
    rain_probability=0,
    rain_mm=0,
    crop=None,
):
    """
    Conservative weather-risk notification. It does not diagnose disease.
    It asks the farmer to monitor the crop when warm/humid/wet conditions align.
    """
    humidity = _num(humidity)
    temperature = _num(temperature)
    rain_probability = _num(rain_probability)
    rain_mm = _num(rain_mm)

    risk = (
        humidity >= 80
        and 18 <= temperature <= 32
        and (rain_probability >= 50 or rain_mm >= 5)
    )

    if not risk:
        return None

    return {
        "category": "disease",
        "type": "disease_risk",
        "priority": "MEDIUM",
        "title": "🦠 Crop Monitoring Alert",
        "message": "Warm, humid and wet conditions may increase crop disease risk. Monitor the crop closely.",
        "action": "disease",
        "crop": crop,
    }


def build_weather_alerts(**weather):
    """Return all applicable alerts, including irrigation and disease-risk alerts."""
    alerts = []
    irrigation = weather_irrigation_alert(**weather)
    if irrigation:
        alerts.append(irrigation)

    disease = disease_risk_alert(**weather)
    if disease:
        alerts.append(disease)

    return alerts


def sos_notification(status="SENT", emergency_type="Emergency"):
    """Build a critical SOS notification for farmer/admin/authorized recipient flows."""
    status = str(status or "SENT").upper()
    messages = {
        "SENT": "SOS emergency request has been sent.",
        "ACKNOWLEDGED": "SOS emergency request has been acknowledged.",
        "IN_PROGRESS": "SOS emergency request is in progress.",
        "RESOLVED": "SOS emergency request has been resolved.",
        "CANCELLED": "SOS emergency request has been cancelled.",
    }
    return {
        "category": "sos",
        "type": "sos_status",
        "priority": "CRITICAL",
        "title": "🚨 SOS Emergency Notification",
        "message": f"{messages.get(status, 'SOS emergency status updated')} Type: {emergency_type}.",
        "action": "sos",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
