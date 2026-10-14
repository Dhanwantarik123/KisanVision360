# KisanVision360+ SOS and Smart Irrigation Upgrade

## SOS
- SOS requests are saved to PostgreSQL `sos_requests` and app-admin notifications are attempted.
- SOS page includes a configurable `tel:` emergency-call link.
- Configure `SOS_EMERGENCY_NUMBER` in the server environment before deployment. It defaults to `112` (India emergency number); verify before production.
- A browser cannot silently place a call. The device phone app opens and may ask the user to confirm. This does not dispatch emergency services by itself.

## Weather notifications
- Existing forecast notifications are retained for heavy rain, expected rain, heat/low rain, strong wind, and crop disease risk.
- New rule: if the next three forecast days each have under 2 mm forecast rain and under 30% rain probability, send a dry-spell irrigation review alert. High temperatures raise its priority.
- The advice asks farmers to check soil moisture and crop needs rather than watering automatically.
- Configure `OPENWEATHER_API_KEY` to obtain live weather/forecast data. Without a valid API key, the app cannot claim live forecast-based alerts.

## Validation
- Python syntax compilation passed for the modified SOS and notification service modules.
- Runtime database tests were not run in this environment because `psycopg2` is not installed here.
