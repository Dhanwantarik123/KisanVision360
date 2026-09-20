import hashlib
import logging
from datetime import datetime, timezone
from database.db import get_db_connection

logger = logging.getLogger(__name__)

PRIORITIES = {"CRITICAL", "HIGH", "MEDIUM", "NORMAL"}


def ensure_notification_schema():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            notification_type VARCHAR(80) DEFAULT 'general',
            category VARCHAR(80) DEFAULT 'System',
            priority VARCHAR(20) DEFAULT 'NORMAL',
            is_read BOOLEAN DEFAULT FALSE,
            is_archived BOOLEAN DEFAULT FALSE,
            action_url TEXT,
            related_id VARCHAR(120),
            event_id VARCHAR(255),
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            farmer_id BIGINT
        )
        """)
        additions = [
            ("category", "VARCHAR(80) DEFAULT 'System'"),
            ("priority", "VARCHAR(20) DEFAULT 'NORMAL'"),
            ("is_archived", "BOOLEAN DEFAULT FALSE"),
            ("action_url", "TEXT"),
            ("related_id", "VARCHAR(120)"),
            ("event_id", "VARCHAR(255)"),
            ("expires_at", "TIMESTAMP"),
        ]
        for col, typ in additions:
            cur.execute(f"ALTER TABLE notifications ADD COLUMN IF NOT EXISTS {col} {typ}")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_event ON notifications(user_id, event_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_category ON notifications(user_id, category)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(user_id, priority)")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close(); conn.close()


def _event_key(user_id, event_id, notification_type, title):
    raw = f"{user_id}|{event_id or ''}|{notification_type}|{title}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_smart_notification(user_id, title, message, notification_type="general",
                               category=None, priority="NORMAL", action_url=None,
                               related_id=None, event_id=None, expires_at=None):
    if not user_id:
        return None
    priority = str(priority or "NORMAL").upper()
    if priority not in PRIORITIES:
        priority = "NORMAL"
    category = category or notification_type.title()
    ensure_notification_schema()
    conn = get_db_connection(); cur = conn.cursor()
    try:
        key = _event_key(user_id, event_id, notification_type, title) if event_id else None
        if key:
            cur.execute("SELECT id FROM notifications WHERE user_id=%s AND event_id=%s LIMIT 1", (int(user_id), key))
            if cur.fetchone():
                conn.rollback()
                return None
        cur.execute("""
            INSERT INTO notifications
            (user_id,title,message,notification_type,category,priority,is_read,is_archived,
             action_url,related_id,event_id,date,created_at,expires_at,farmer_id)
            VALUES (%s,%s,%s,%s,%s,%s,FALSE,FALSE,%s,%s,%s,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,%s,%s)
            RETURNING id
        """, (int(user_id), str(title)[:255], str(message), str(notification_type)[:80],
              str(category)[:80], priority, action_url, related_id, key, expires_at, int(user_id)))
        row = cur.fetchone(); conn.commit()
        new_id = row["id"] if isinstance(row, dict) else row[0]
        # Keep the existing consumer notification UI working too.
        cur2 = None
        try:
            cur2 = conn.cursor()
            cur2.execute("SELECT 1 FROM information_schema.tables WHERE table_name='consumer_notifications'")
            exists = cur2.fetchone()
            if exists and mirror_consumer:
                cur2.execute("SELECT role FROM users WHERE id=%s", (int(user_id),))
                u = cur2.fetchone()
                role = (u.get("role") if isinstance(u, dict) else (u[0] if u else "")) if u else ""
                if str(role).lower() == "consumer":
                    cur2.execute("""
                        INSERT INTO consumer_notifications (consumer_id,title,message,notification_type,is_read,created_at)
                        VALUES (%s,%s,%s,%s,FALSE,CURRENT_TIMESTAMP)
                    """, (int(user_id), str(title)[:255], str(message), str(notification_type)[:50]))
                    conn.commit()
        except Exception:
            if conn: conn.rollback()
        finally:
            if cur2: cur2.close()
        return new_id
    except Exception:
        conn.rollback(); logger.exception("Notification creation failed")
        return None
    finally:
        cur.close(); conn.close()


def build_weather_alerts(forecast):
    alerts = []
    if not forecast:
        return alerts
    for day in forecast[:5]:
        temp = float(day.get("temperature") or 0)
        rain = float(day.get("rainfall") or day.get("rain") or 0)
        prob = float(day.get("rain_probability") or 0)
        wind = float(day.get("wind") or day.get("wind_speed") or 0)
        humidity = float(day.get("humidity") or 0)
        date_key = day.get("date") or day.get("day") or "forecast"
        if wind >= 35:
            alerts.append(("Strong Wind Alert", "Strong wind is expected. Review planned farm activities and avoid unnecessary spraying.", "weather", "Weather", "HIGH", "/weather", f"weather-wind-{date_key}"))
        if prob >= 70 and rain >= 20:
            alerts.append(("Heavy Rainfall Expected", "Heavy rainfall is expected. Avoid unnecessary irrigation and monitor your farm.", "irrigation", "Irrigation", "HIGH", "/irrigation", f"weather-heavy-rain-{date_key}"))
        elif prob >= 50 or rain >= 5:
            alerts.append(("Rain Expected — Delay Irrigation", "Rain is expected. Consider delaying irrigation to avoid unnecessary water use.", "irrigation", "Irrigation", "MEDIUM", "/irrigation", f"weather-rain-{date_key}"))
        if temp >= 35 and prob < 30 and rain < 2:
            alerts.append(("High Temperature + Low Rain", "High temperature with low expected rainfall. Review your irrigation requirement.", "irrigation", "Irrigation", "HIGH", "/irrigation", f"weather-heat-{date_key}"))
        if 18 <= temp <= 34 and prob < 30 and humidity < 85:
            alerts.append(("Irrigation Conditions Suitable", "Weather conditions are suitable for irrigation. Review your crop and irrigation schedule.", "irrigation", "Irrigation", "NORMAL", "/irrigation", f"weather-irrigation-{date_key}"))
        if humidity >= 80 and 18 <= temp <= 32 and (prob >= 50 or rain >= 5):
            alerts.append(("Crop Monitoring Alert", "Warm, humid and wet conditions may increase crop disease risk. Monitor your crop closely.", "disease", "Disease", "MEDIUM", "/disease", f"weather-disease-{date_key}"))
    return alerts
