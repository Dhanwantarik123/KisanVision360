import os

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")


conn = psycopg2.connect(
    DATABASE_URL,
    cursor_factory=RealDictCursor
)

cur = conn.cursor()

try:
    print("=" * 60)
    print("KISANVISION360+ CHATBOT DATABASE MIGRATION")
    print("=" * 60)

    # ========================================================
    # CHAT SESSIONS
    # ========================================================

    print("\nUpdating chat_sessions...")

    cur.execute("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS user_id BIGINT
    """)

    cur.execute("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS language VARCHAR(10)
            DEFAULT 'en'
    """)

    cur.execute("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS title VARCHAR(150)
            DEFAULT 'KisanVision360+ Farming Assistant'
    """)

    cur.execute("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
    """)

    cur.execute("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
    """)

    # ========================================================
    # CHAT MESSAGES
    # ========================================================

    print("Updating chat_messages...")

    cur.execute("""
        ALTER TABLE chat_messages
        ADD COLUMN IF NOT EXISTS session_id BIGINT
    """)

    cur.execute("""
        ALTER TABLE chat_messages
        ADD COLUMN IF NOT EXISTS user_id BIGINT
    """)

    cur.execute("""
        ALTER TABLE chat_messages
        ADD COLUMN IF NOT EXISTS message TEXT
    """)

    cur.execute("""
        ALTER TABLE chat_messages
        ADD COLUMN IF NOT EXISTS response TEXT
    """)

    cur.execute("""
        ALTER TABLE chat_messages
        ADD COLUMN IF NOT EXISTS intent VARCHAR(80)
    """)

    cur.execute("""
        ALTER TABLE chat_messages
        ADD COLUMN IF NOT EXISTS language VARCHAR(10)
            DEFAULT 'en'
    """)

    cur.execute("""
        ALTER TABLE chat_messages
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
    """)

    # ========================================================
    # CHAT FEEDBACK
    # ========================================================

    print("Creating chat_feedback...")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_feedback (
            id BIGSERIAL PRIMARY KEY,

            message_id BIGINT NOT NULL,

            user_id BIGINT NOT NULL,

            rating SMALLINT,

            feedback TEXT,

            created_at TIMESTAMP
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT
            chat_feedback_rating_check
            CHECK (
                rating IS NULL
                OR rating BETWEEN 1 AND 5
            )
        )
    """)

    # ========================================================
    # CHAT CONTEXT
    # ========================================================

    print("Creating chat_context...")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_context (
            id BIGSERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,

            session_id BIGINT,

            context_type VARCHAR(80) NOT NULL,

            context_key VARCHAR(100) NOT NULL,

            context_value TEXT,

            created_at TIMESTAMP
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP
                NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ========================================================
    # INDEXES
    # ========================================================

    print("Creating chatbot indexes...")

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_sessions_user
        ON chat_sessions(user_id)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_messages_session
        ON chat_messages(session_id)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_messages_user
        ON chat_messages(user_id)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_messages_created
        ON chat_messages(created_at DESC)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_messages_intent
        ON chat_messages(intent)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_feedback_message
        ON chat_feedback(message_id)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_feedback_user
        ON chat_feedback(user_id)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_context_user
        ON chat_context(user_id)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_context_session
        ON chat_context(session_id)
    """)

    # ========================================================
    # DEFAULT NULL VALUES
    # ========================================================

    cur.execute("""
        UPDATE chat_sessions
        SET language = 'en'
        WHERE language IS NULL
           OR language = ''
    """)

    cur.execute("""
        UPDATE chat_messages
        SET language = 'en'
        WHERE language IS NULL
           OR language = ''
    """)

    # ========================================================
    # COMMIT
    # ========================================================

    conn.commit()

    print()
    print("=" * 60)
    print("CHATBOT DATABASE MIGRATION: SUCCESS")
    print("=" * 60)

except Exception as error:

    conn.rollback()

    print()
    print("=" * 60)
    print("CHATBOT DATABASE MIGRATION: FAILED")
    print("=" * 60)
    print("ERROR:", error)
    print("=" * 60)

    raise

finally:

    cur.close()
    conn.close()
