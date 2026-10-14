# KisanVision360+ — complete project bundle

This bundle combines the complete source tree from the uploaded project with the SOS and smart-weather/irrigation changes. Existing pages, static assets, routes, database modules, and model-training scripts are retained.

## Requirements
- Python 3.11 recommended for compatibility with TensorFlow 2.15.x.
- PostgreSQL database (the app uses `DATABASE_URL`).
- OpenWeather API key for live weather/forecast data.

## Setup (Windows PowerShell)
1. Extract the ZIP. Open a terminal in the `z2` folder.
2. Create a virtual environment: `py -3.11 -m venv .venv`
3. Activate it: `.venv\Scripts\Activate.ps1`
4. Install base dependencies: `python -m pip install --upgrade pip` then `pip install -r requirements.txt`.
5. TensorFlow is needed for disease-model inference. On Python 3.11, install a compatible TensorFlow release, e.g. `pip install tensorflow==2.15.1` if supported by your machine.
6. Copy `.env.example` to `.env`; set `SECRET_KEY`, `DATABASE_URL`, and `OPENWEATHER_API_KEY`. Never use the example database URL as a real connection.
7. Ensure the PostgreSQL database and the application's expected tables are available. Run the project's database setup scripts only after reviewing them for your environment.
8. Start the app: `python app.py`. Use the host/port printed by Flask.

## SOS behavior
- SOS requests are recorded in `sos_requests`; admin notifications are attempted using the existing notification service.
- `SOS_EMERGENCY_NUMBER` defaults to `112` (India). Verify this before use.
- A `tel:` link opens the device's phone app; browsers cannot silently call or guarantee that emergency services received a request.
- Treat SOS as a demo until a staffed recipient, alert delivery, access control, and end-to-end tests are configured.

## Weather and irrigation alerts
- Live forecasts require a valid OpenWeather API key and network access.
- Forecast rules provide recommendations, not automated watering: expected/heavy rain advises delaying irrigation; dry-spell logic asks the farmer to check soil moisture and crop needs.
- Background/scheduled execution must be configured separately if alerts should be generated while nobody has the app open.

## Verification performed
- Python files were syntax-compiled during packaging.
- The project has not been end-to-end tested against your PostgreSQL instance, API keys, mail provider, Android device, or production host. Configure those services and test with non-emergency test scenarios before real use.
