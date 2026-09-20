-- ============================================================
-- KISANVISION360+
-- AI CHATBOT DATABASE SCHEMA
-- PostgreSQL / Supabase
-- ============================================================

-- ============================================================
-- 1. CHAT SESSIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL,

    language VARCHAR(10) NOT NULL DEFAULT 'en',

    title VARCHAR(150) NOT NULL
        DEFAULT 'KisanVision360+ Farming Assistant',

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. CHAT MESSAGES
-- ============================================================

CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,

    session_id BIGINT NOT NULL,

    user_id BIGINT NOT NULL,

    message TEXT NOT NULL,

    response TEXT NOT NULL,

    intent VARCHAR(80),

    language VARCHAR(10) NOT NULL DEFAULT 'en',

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chat_message_session
        FOREIGN KEY (session_id)
        REFERENCES chat_sessions(id)
        ON DELETE CASCADE
);


-- ============================================================
-- 3. CHAT FEEDBACK
-- ============================================================

CREATE TABLE IF NOT EXISTS chat_feedback (
    id BIGSERIAL PRIMARY KEY,

    message_id BIGINT NOT NULL,

    user_id BIGINT NOT NULL,

    rating SMALLINT,

    feedback TEXT,

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chat_feedback_rating_check
        CHECK (
            rating IS NULL
            OR rating BETWEEN 1 AND 5
        ),

    CONSTRAINT fk_chat_feedback_message
        FOREIGN KEY (message_id)
        REFERENCES chat_messages(id)
        ON DELETE CASCADE
);


-- ============================================================
-- 4. CHAT CONTEXT
-- ============================================================

CREATE TABLE IF NOT EXISTS chat_context (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL,

    session_id BIGINT,

    context_type VARCHAR(80) NOT NULL,

    context_key VARCHAR(100) NOT NULL,

    context_value TEXT,

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chat_context_session
        FOREIGN KEY (session_id)
        REFERENCES chat_sessions(id)
        ON DELETE CASCADE
);


-- ============================================================
-- 5. INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user
ON chat_sessions(user_id);


CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated
ON chat_sessions(updated_at DESC);


CREATE INDEX IF NOT EXISTS idx_chat_messages_session
ON chat_messages(session_id);


CREATE INDEX IF NOT EXISTS idx_chat_messages_user
ON chat_messages(user_id);


CREATE INDEX IF NOT EXISTS idx_chat_messages_created
ON chat_messages(created_at DESC);


CREATE INDEX IF NOT EXISTS idx_chat_messages_intent
ON chat_messages(intent);


CREATE INDEX IF NOT EXISTS idx_chat_feedback_message
ON chat_feedback(message_id);


CREATE INDEX IF NOT EXISTS idx_chat_feedback_user
ON chat_feedback(user_id);


CREATE INDEX IF NOT EXISTS idx_chat_context_user
ON chat_context(user_id);


CREATE INDEX IF NOT EXISTS idx_chat_context_session
ON chat_context(session_id);


CREATE INDEX IF NOT EXISTS idx_chat_context_key
ON chat_context(context_type, context_key);


-- ============================================================
-- 6. AUTO UPDATE TIMESTAMP FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION update_chat_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


-- ============================================================
-- 7. CHAT SESSION UPDATE TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS trg_chat_sessions_updated
ON chat_sessions;

CREATE TRIGGER trg_chat_sessions_updated
BEFORE UPDATE ON chat_sessions
FOR EACH ROW
EXECUTE FUNCTION update_chat_updated_at();


-- ============================================================
-- 8. CHAT CONTEXT UPDATE TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS trg_chat_context_updated
ON chat_context;

CREATE TRIGGER trg_chat_context_updated
BEFORE UPDATE ON chat_context
FOR EACH ROW
EXECUTE FUNCTION update_chat_updated_at();


-- ============================================================
-- 9. SUPPORTED LANGUAGES
-- ============================================================

-- Global application language support:
--
-- en   English
-- hi   Hindi
-- mr   Marathi
-- kn   Kannada
-- te   Telugu
-- ta   Tamil
-- ml   Malayalam
-- gu   Gujarati
-- pa   Punjabi
-- bn   Bengali
-- as   Assamese
-- or   Odia
-- ur   Urdu
-- ne   Nepali
-- sa   Sanskrit
-- kok  Konkani
-- mai  Maithili
-- ks   Kashmiri
-- sd   Sindhi
-- mni  Manipuri
--
-- Language is selected globally in the application.
-- It does NOT need to be selected on every chatbot message.


-- ============================================================
-- 10. CHATBOT STATISTICS VIEW
-- ============================================================

CREATE OR REPLACE VIEW chatbot_statistics AS
SELECT
    COUNT(*) AS total_messages,

    COUNT(DISTINCT user_id) AS total_users,

    COUNT(DISTINCT session_id) AS total_sessions,

    COUNT(DISTINCT intent) AS total_intents

FROM chat_messages;


-- ============================================================
-- 11. USER CHAT SUMMARY VIEW
-- ============================================================

CREATE OR REPLACE VIEW chatbot_user_summary AS
SELECT
    user_id,

    COUNT(*) AS total_messages,

    COUNT(DISTINCT session_id) AS total_sessions,

    MAX(created_at) AS last_message_at

FROM chat_messages

GROUP BY user_id;


-- ============================================================
-- 12. SESSION MESSAGE SUMMARY VIEW
-- ============================================================

CREATE OR REPLACE VIEW chatbot_session_summary AS
SELECT
    cs.id AS session_id,

    cs.user_id,

    cs.title,

    cs.language,

    cs.created_at,

    cs.updated_at,

    COUNT(cm.id) AS total_messages

FROM chat_sessions cs

LEFT JOIN chat_messages cm
    ON cm.session_id = cs.id

GROUP BY
    cs.id,
    cs.user_id,
    cs.title,
    cs.language,
    cs.created_at,
    cs.updated_at;


-- ============================================================
-- 13. TABLE COMMENTS
-- ============================================================

COMMENT ON TABLE chat_sessions IS
'Stores KisanVision360+ AI chatbot conversation sessions.';


COMMENT ON TABLE chat_messages IS
'Stores user questions and AI chatbot responses.';


COMMENT ON TABLE chat_feedback IS
'Stores ratings and feedback for chatbot responses.';


COMMENT ON TABLE chat_context IS
'Stores temporary farming context used by the AI chatbot.';


-- ============================================================
-- 14. VERIFICATION
-- ============================================================

SELECT
    'KisanVision360+ Chatbot Schema Ready'
    AS status;


-- ============================================================
-- 15. VERIFY TABLES
-- ============================================================

SELECT table_name

FROM information_schema.tables

WHERE table_schema = 'public'

AND table_name IN (
    'chat_sessions',
    'chat_messages',
    'chat_feedback',
    'chat_context'
)

ORDER BY table_name;


-- ============================================================
-- COMPLETE
-- ============================================================