from services.smart_notification_engine import (
    weather_irrigation_alert, disease_risk_alert, sos_notification
)

def test_rain_delay():
    a = weather_irrigation_alert(rain_probability=60, rain_mm=4, temperature=28, humidity=70)
    assert a["type"] == "rain_expected"

def test_heavy_rain():
    a = weather_irrigation_alert(rain_probability=80, rain_mm=25, temperature=28, humidity=80)
    assert a["type"] == "heavy_rain"

def test_heat_low_rain():
    a = weather_irrigation_alert(rain_probability=10, rain_mm=0, temperature=38, humidity=40)
    assert a["type"] == "heat_low_rain"

def test_wind():
    a = weather_irrigation_alert(rain_probability=0, rain_mm=0, temperature=28, humidity=50, wind_speed=40)
    assert a["type"] == "strong_wind"

def test_disease_risk():
    a = disease_risk_alert(humidity=90, temperature=25, rain_probability=70, rain_mm=10)
    assert a["type"] == "disease_risk"

def test_sos():
    a = sos_notification("ACKNOWLEDGED", "Farm Accident")
    assert a["priority"] == "CRITICAL"
