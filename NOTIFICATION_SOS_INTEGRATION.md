# KisanVision360+ — Notification + SOS Integration

This version integrates the notification engine into the supplied Flask project.

## Main templates
- Farmer notification page: `templates/notifications.html`
- Consumer notification page: `templates/consumer_notifications.html`
- SOS page: `templates/sos.html`
- SOS detail: `templates/sos_detail.html`

## Backend
- `routes/notifications.py` — notification page/API/read/unread/archive/preferences
- `routes/consumer.py` — existing consumer notification system, mirrored to the central notification table
- `routes/weather.py` — forecast is evaluated and relevant smart alerts are created
- `routes/sos.py` — SOS create, status, history and admin list
- `services/notification_service.py` — reusable central notification engine

## Weather rules
- Rain expected → Delay irrigation
- Heavy rain → Avoid unnecessary irrigation
- High temperature + low expected rain → Review irrigation requirement
- Suitable conditions → Irrigation recommended
- Strong wind → Review farm activity
- Warm/humid/wet conditions → Crop monitoring alert

## SOS
Statuses: `SENT`, `ACKNOWLEDGED`, `IN_PROGRESS`, `RESOLVED`, `CANCELLED`.
SOS notifications are `CRITICAL` and are kept separate from normal alert priority.

## PostgreSQL
The service automatically creates/extends:
- `notifications`
- `notification_preferences`
- `sos_requests`

The existing `consumer_notifications` table continues to support the consumer UI.

## Important
The build environment used for packaging does not contain the project's Flask/PostgreSQL Python dependencies, so runtime database/API execution could not be performed here. Python syntax compilation was completed for the changed Python files. Use the project's existing deployment environment/requirements to run it.
