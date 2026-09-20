# KisanVision360+ Advanced Notification & SOS Upgrade

## Main focus
Farmer + Consumer notifications, weather-aware irrigation alerts, disease-risk monitoring alerts, and critical SOS notifications.

## Weather rules
1. Rain expected -> Delay irrigation.
2. Heavy rain expected -> Avoid unnecessary irrigation.
3. High temperature + low expected rainfall -> Review/increase irrigation.
4. Suitable conditions -> Irrigation recommended.
5. Strong wind -> Review planned farm activity.
6. Warm + humid + wet conditions -> Crop monitoring alert (not a diagnosis).
7. SOS -> Critical emergency notification.

## Integration
Use `services.smart_notification_engine.build_weather_alerts(...)` from the existing weather/irrigation service and persist each generated alert in the existing notifications table.

Example:
```python
from services.smart_notification_engine import build_weather_alerts

alerts = build_weather_alerts(
    rain_probability=70,
    rain_mm=12,
    temperature=28,
    humidity=82,
    wind_speed=15,
    crop="Tomato",
)
```

For SOS:
```python
from services.smart_notification_engine import sos_notification
alert = sos_notification("ACKNOWLEDGED", "Farm Accident")
```

## Important
- The weather engine is advisory; it should not claim a medical/agricultural diagnosis.
- Existing notification preferences, authentication and PostgreSQL persistence should be used by the app's existing routes.
- Existing UI should connect each notification's action to Weather, Irrigation, Disease or SOS.
