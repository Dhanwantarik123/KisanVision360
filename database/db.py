# ============================================================
# KISANVISION360+
# database/db.py
# PostgreSQL / Supabase Database
# ============================================================

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(override=True)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = {
    "en",
    "hi",
    "mr",
    "kn",
    "te",
    "ta",
    "ml",
    "gu",
    "pa",
    "bn",
    "as",
    "or",
    "ur",
    "ne",
    "sa",
    "kok",
    "mai",
    "ks",
    "sd",
    "mni",
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    """
    Create and return a PostgreSQL connection.
    """

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is missing.\n"
            "Add your Supabase PostgreSQL connection string to .env"
        )

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor,
        connect_timeout=15,
    )


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def get_db():
    """
    Backward-compatible database connection.
    """

    return get_db_connection()


# ============================================================
# CONTEXT MANAGER
# ============================================================

@contextmanager
def database_connection():
    """
    Safe database connection manager.
    """

    connection = None

    try:
        connection = get_db_connection()

        yield connection

        connection.commit()

    except Exception:

        if connection:
            connection.rollback()

        raise

    finally:

        if connection:
            connection.close()


# ============================================================
# EXECUTE QUERY
# ============================================================

def execute_query(
    query,
    params=None,
    fetch=False,
    fetchone=False,
):
    """
    Execute PostgreSQL query.
    """

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(query, params or ())

        if fetchone:

            result = cursor.fetchone()

        elif fetch:

            result = cursor.fetchall()

        else:

            result = None

        connection.commit()

        return result

    except Exception:

        if connection:
            connection.rollback()

        raise

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# TABLE EXISTS
# ============================================================

def table_exists(cursor, table_name):
    """
    Check whether a public PostgreSQL table exists.
    """

    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = %s
        ) AS exists
        """,
        (table_name,),
    )

    result = cursor.fetchone()

    return bool(result["exists"])


# ============================================================
# COLUMN EXISTS
# ============================================================

def column_exists(
    cursor,
    table_name,
    column_name,
):
    """
    Check whether a column exists.
    """

    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
        ) AS exists
        """,
        (
            table_name,
            column_name,
        ),
    )

    result = cursor.fetchone()

    return bool(result["exists"])


# ============================================================
# ADD COLUMN IF MISSING
# ============================================================

def add_column_if_missing(
    cursor,
    table_name,
    column_name,
    definition,
):
    """
    Add a column only when it does not already exist.

    IMPORTANT:
    This is used for upgrading older database tables.
    """

    if not table_exists(cursor, table_name):
        return

    if not column_exists(
        cursor,
        table_name,
        column_name,
    ):

        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {definition}
            """
        )


# ============================================================
# USERS MIGRATION
# ============================================================

def migrate_users_table(cursor):
    """
    Upgrade an older users table.
    """

    if not table_exists(cursor, "users"):
        return

    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------

    has_password = column_exists(
        cursor,
        "users",
        "password",
    )

    has_password_hash = column_exists(
        cursor,
        "users",
        "password_hash",
    )

    if has_password and not has_password_hash:

        cursor.execute(
            """
            ALTER TABLE users
            RENAME COLUMN password TO password_hash
            """
        )

    elif not has_password_hash:

        add_column_if_missing(
            cursor,
            "users",
            "password_hash",
            "TEXT",
        )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    has_language = column_exists(
        cursor,
        "users",
        "language",
    )

    has_preferred_language = column_exists(
        cursor,
        "users",
        "preferred_language",
    )

    if has_language and not has_preferred_language:

        cursor.execute(
            """
            ALTER TABLE users
            RENAME COLUMN language TO preferred_language
            """
        )

    elif not has_preferred_language:

        add_column_if_missing(
            cursor,
            "users",
            "preferred_language",
            "VARCHAR(10) DEFAULT 'en'",
        )

    # --------------------------------------------------------
    # PROFILE IMAGE
    # --------------------------------------------------------

    has_profile_image = column_exists(
        cursor,
        "users",
        "profile_image",
    )

    has_profile_pic = column_exists(
        cursor,
        "users",
        "profile_pic",
    )

    if has_profile_image and not has_profile_pic:

        cursor.execute(
            """
            ALTER TABLE users
            RENAME COLUMN profile_image TO profile_pic
            """
        )

    elif not has_profile_pic:

        add_column_if_missing(
            cursor,
            "users",
            "profile_pic",
            "VARCHAR(255)",
        )

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    add_column_if_missing(
        cursor,
        "users",
        "name",
        "VARCHAR(150)",
    )

    # --------------------------------------------------------
    # MOBILE
    # --------------------------------------------------------

    add_column_if_missing(
        cursor,
        "users",
        "mobile",
        "VARCHAR(20)",
    )

    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    add_column_if_missing(
        cursor,
        "users",
        "email",
        "VARCHAR(255)",
    )

    # --------------------------------------------------------
    # ROLE
    # --------------------------------------------------------

    add_column_if_missing(
        cursor,
        "users",
        "role",
        "VARCHAR(30) DEFAULT 'farmer'",
    )

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    add_column_if_missing(
        cursor,
        "users",
        "location",
        "VARCHAR(200)",
    )

    # --------------------------------------------------------
    # ACTIVE
    # --------------------------------------------------------

    add_column_if_missing(
        cursor,
        "users",
        "is_active",
        "BOOLEAN DEFAULT TRUE",
    )

    # --------------------------------------------------------
    # CREATED
    # --------------------------------------------------------

    add_column_if_missing(
        cursor,
        "users",
        "created_at",
        "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    )

    # --------------------------------------------------------
    # UPDATED
    # --------------------------------------------------------

    add_column_if_missing(
        cursor,
        "users",
        "updated_at",
        "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    )

    # --------------------------------------------------------
    # DEFAULTS
    # --------------------------------------------------------

    if column_exists(
        cursor,
        "users",
        "role",
    ):

        cursor.execute(
            """
            ALTER TABLE users
            ALTER COLUMN role
            SET DEFAULT 'farmer'
            """
        )

        cursor.execute(
            """
            UPDATE users
            SET role = LOWER(TRIM(role))
            WHERE role IS NOT NULL
            """
        )

    if column_exists(
        cursor,
        "users",
        "preferred_language",
    ):

        cursor.execute(
            """
            ALTER TABLE users
            ALTER COLUMN preferred_language
            SET DEFAULT 'en'
            """
        )

        cursor.execute(
            """
            UPDATE users
            SET preferred_language = 'en'
            WHERE preferred_language IS NULL
               OR preferred_language = ''
            """
        )

    # --------------------------------------------------------
    # UNIQUE INDEXES
    # --------------------------------------------------------

    if column_exists(cursor, "users", "mobile"):

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            uq_users_mobile
            ON users(mobile)
            WHERE mobile IS NOT NULL
            """
        )

    if column_exists(cursor, "users", "email"):

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            uq_users_email
            ON users(email)
            WHERE email IS NOT NULL
            """
        )


# ============================================================
# CHATBOT MIGRATION
# ============================================================

def migrate_chatbot_tables(cursor):
    """
    Upgrade all existing chatbot tables.

    IMPORTANT:
    CREATE TABLE IF NOT EXISTS does NOT modify an existing
    table.

    Therefore this function explicitly checks every required
    chatbot column before indexes/views are created.
    """

    print("Checking chatbot database schema...")

    # ========================================================
    # CHAT SESSIONS
    # ========================================================

    if not table_exists(
        cursor,
        "chat_sessions",
    ):

        cursor.execute(
            """
            CREATE TABLE chat_sessions (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT,

                language VARCHAR(10)
                    DEFAULT 'en',

                title VARCHAR(150)
                    DEFAULT
                    'KisanVision360+ Farming Assistant',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    else:

        add_column_if_missing(
            cursor,
            "chat_sessions",
            "user_id",
            "BIGINT",
        )

        add_column_if_missing(
            cursor,
            "chat_sessions",
            "language",
            "VARCHAR(10) DEFAULT 'en'",
        )

        add_column_if_missing(
            cursor,
            "chat_sessions",
            "title",
            "VARCHAR(150) DEFAULT 'KisanVision360+ Farming Assistant'",
        )

        add_column_if_missing(
            cursor,
            "chat_sessions",
            "created_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

        add_column_if_missing(
            cursor,
            "chat_sessions",
            "updated_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

    # ========================================================
    # CHAT MESSAGES
    # ========================================================

    if not table_exists(
        cursor,
        "chat_messages",
    ):

        cursor.execute(
            """
            CREATE TABLE chat_messages (
                id BIGSERIAL PRIMARY KEY,

                session_id BIGINT,

                user_id BIGINT,

                message TEXT,

                response TEXT,

                intent VARCHAR(80),

                language VARCHAR(10)
                    DEFAULT 'en',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    else:

        add_column_if_missing(
            cursor,
            "chat_messages",
            "session_id",
            "BIGINT",
        )

        add_column_if_missing(
            cursor,
            "chat_messages",
            "user_id",
            "BIGINT",
        )

        add_column_if_missing(
            cursor,
            "chat_messages",
            "message",
            "TEXT",
        )

        add_column_if_missing(
            cursor,
            "chat_messages",
            "response",
            "TEXT",
        )

        add_column_if_missing(
            cursor,
            "chat_messages",
            "intent",
            "VARCHAR(80)",
        )

        add_column_if_missing(
            cursor,
            "chat_messages",
            "language",
            "VARCHAR(10) DEFAULT 'en'",
        )

        add_column_if_missing(
            cursor,
            "chat_messages",
            "created_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

    # ========================================================
    # CHAT FEEDBACK
    # ========================================================

    if not table_exists(
        cursor,
        "chat_feedback",
    ):

        cursor.execute(
            """
            CREATE TABLE chat_feedback (
                id BIGSERIAL PRIMARY KEY,

                message_id BIGINT,

                user_id BIGINT,

                rating SMALLINT,

                feedback TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    else:

        add_column_if_missing(
            cursor,
            "chat_feedback",
            "message_id",
            "BIGINT",
        )

        add_column_if_missing(
            cursor,
            "chat_feedback",
            "user_id",
            "BIGINT",
        )

        add_column_if_missing(
            cursor,
            "chat_feedback",
            "rating",
            "SMALLINT",
        )

        add_column_if_missing(
            cursor,
            "chat_feedback",
            "feedback",
            "TEXT",
        )

        add_column_if_missing(
            cursor,
            "chat_feedback",
            "created_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

    # ========================================================
    # CHAT CONTEXT
    # ========================================================

    if not table_exists(
        cursor,
        "chat_context",
    ):

        cursor.execute(
            """
            CREATE TABLE chat_context (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT,

                session_id BIGINT,

                context_type VARCHAR(80),

                context_key VARCHAR(100),

                context_value TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    else:

        add_column_if_missing(
            cursor,
            "chat_context",
            "user_id",
            "BIGINT",
        )

        add_column_if_missing(
            cursor,
            "chat_context",
            "session_id",
            "BIGINT",
        )

        add_column_if_missing(
            cursor,
            "chat_context",
            "context_type",
            "VARCHAR(80)",
        )

        add_column_if_missing(
            cursor,
            "chat_context",
            "context_key",
            "VARCHAR(100)",
        )

        add_column_if_missing(
            cursor,
            "chat_context",
            "context_value",
            "TEXT",
        )

        add_column_if_missing(
            cursor,
            "chat_context",
            "created_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

        add_column_if_missing(
            cursor,
            "chat_context",
            "updated_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

    print("Chatbot schema migration: OK")


# ============================================================
# INIT DATABASE
# ============================================================

def init_db():
    """
    Create and upgrade the complete KisanVision360+
    PostgreSQL/Supabase database.

    Safe to execute repeatedly.
    """

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        print()
        print("=" * 65)
        print("KISANVISION360+ DATABASE INITIALIZATION")
        print("=" * 65)

        # ====================================================
        # USERS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,

                name VARCHAR(150) NOT NULL,

                mobile VARCHAR(20),

                email VARCHAR(255),

                password_hash TEXT,

                role VARCHAR(30)
                    DEFAULT 'farmer',

                location VARCHAR(200),

                preferred_language VARCHAR(10)
                    DEFAULT 'en',

                profile_pic VARCHAR(255),

                is_active BOOLEAN
                    DEFAULT TRUE,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        migrate_users_table(cursor)

        # ====================================================
        # FARMER PROFILES
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS farmer_profiles (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT UNIQUE,

                farm_name VARCHAR(150),

                farm_area NUMERIC(12,2),

                area_unit VARCHAR(20)
                    DEFAULT 'acre',

                soil_type VARCHAR(100),

                irrigation_method VARCHAR(100),

                village VARCHAR(150),

                district VARCHAR(150),

                state VARCHAR(100),

                latitude NUMERIC(10,7),

                longitude NUMERIC(10,7),

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # CONSUMER PROFILES
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS consumer_profiles (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT UNIQUE,

                address TEXT,

                city VARCHAR(100),

                state VARCHAR(100),

                pincode VARCHAR(10),

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # CROPS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS crops (
                id BIGSERIAL PRIMARY KEY,

                farmer_id BIGINT,

                crop_name VARCHAR(150),

                sowing_date DATE,

                duration_days INTEGER,

                soil_type VARCHAR(100),

                irrigation_method VARCHAR(100),

                farm_area NUMERIC(12,2),

                expected_harvest_date DATE,

                status VARCHAR(50)
                    DEFAULT 'Active',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # MARKETPLACE PRODUCTS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS marketplace_products (
                id BIGSERIAL PRIMARY KEY,

                farmer_id BIGINT,

                product_name VARCHAR(150),

                category VARCHAR(100),

                description TEXT,

                price NUMERIC(12,2)
                    DEFAULT 0,

                quantity NUMERIC(12,2)
                    DEFAULT 0,

                unit VARCHAR(20)
                    DEFAULT 'Kg',

                image VARCHAR(255)
                    DEFAULT 'no-image.png',

                location VARCHAR(150),

                phone VARCHAR(20),

                status VARCHAR(30)
                    DEFAULT 'Available',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # MARKET PRICES
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_prices (
                id BIGSERIAL PRIMARY KEY,

                commodity VARCHAR(150),

                market VARCHAR(150),

                district VARCHAR(150),

                state VARCHAR(100)
                    DEFAULT 'Maharashtra',

                min_price NUMERIC(12,2),

                max_price NUMERIC(12,2),

                modal_price NUMERIC(12,2),

                arrival_date DATE,

                source VARCHAR(150),

                is_live BOOLEAN
                    DEFAULT TRUE,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # ORDERS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id BIGSERIAL PRIMARY KEY,

                buyer_id BIGINT,

                farmer_id BIGINT,

                product_id BIGINT,

                quantity NUMERIC(12,2)
                    DEFAULT 1,

                price NUMERIC(12,2)
                    DEFAULT 0,

                total_amount NUMERIC(12,2)
                    DEFAULT 0,

                delivery_address TEXT,

                city VARCHAR(100),

                pincode VARCHAR(10),

                payment_method VARCHAR(50)
                    DEFAULT 'COD',

                payment_status VARCHAR(50)
                    DEFAULT 'Pending',

                delivery_status VARCHAR(50)
                    DEFAULT 'Order Placed',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # ORDER ITEMS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id BIGSERIAL PRIMARY KEY,

                order_id BIGINT,

                product_id BIGINT,

                farmer_id BIGINT,

                product_name VARCHAR(150),

                quantity NUMERIC(12,2)
                    DEFAULT 1,

                price NUMERIC(12,2)
                    DEFAULT 0,

                total_amount NUMERIC(12,2)
                    DEFAULT 0,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # CART
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cart (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT,

                product_id BIGINT,

                quantity NUMERIC(12,2)
                    DEFAULT 1,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, product_id)
            )
            """
        )

        # ====================================================
        # CART ITEMS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cart_items (
                id BIGSERIAL PRIMARY KEY,

                cart_id BIGINT,

                user_id BIGINT,

                product_id BIGINT,

                quantity NUMERIC(12,2)
                    DEFAULT 1,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # WISHLIST
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS wishlist (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT,

                product_id BIGINT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, product_id)
            )
            """
        )

        # ====================================================
        # NOTIFICATIONS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT,

                notification_type VARCHAR(50)
                    DEFAULT 'general',

                title VARCHAR(200),

                message TEXT,

                is_read BOOLEAN
                    DEFAULT FALSE,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # FARM EXPENSES
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS farm_expenses (
                id BIGSERIAL PRIMARY KEY,

                farmer_id BIGINT,

                description VARCHAR(255),

                amount NUMERIC(12,2)
                    DEFAULT 0,

                category VARCHAR(100),

                expense_date DATE
                    DEFAULT CURRENT_DATE,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # FARM INCOME
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS farm_income (
                id BIGSERIAL PRIMARY KEY,

                farmer_id BIGINT,

                description VARCHAR(255),

                amount NUMERIC(12,2)
                    DEFAULT 0,

                category VARCHAR(100),

                income_date DATE
                    DEFAULT CURRENT_DATE,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # TRANSACTIONS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT,

                transaction_type VARCHAR(50),

                amount NUMERIC(12,2)
                    DEFAULT 0,

                description TEXT,

                reference_id VARCHAR(100),

                status VARCHAR(50)
                    DEFAULT 'Completed',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # CHATBOT
        # ====================================================
        #
        # IMPORTANT:
        # We deliberately call the migration function here
        # instead of relying only on CREATE TABLE IF NOT EXISTS.
        #
        # This fixes old Supabase tables.
        # ====================================================

        migrate_chatbot_tables(cursor)

        # ====================================================
        # CHATBOT INDEXES
        # ====================================================

        chatbot_indexes = [

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_sessions_user
            ON chat_sessions(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_sessions_updated
            ON chat_sessions(updated_at DESC)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_messages_session
            ON chat_messages(session_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_messages_user
            ON chat_messages(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_messages_created
            ON chat_messages(created_at DESC)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_messages_intent
            ON chat_messages(intent)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_feedback_message
            ON chat_feedback(message_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_feedback_user
            ON chat_feedback(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_context_user
            ON chat_context(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_context_session
            ON chat_context(session_id)
            """,
        ]

        for query in chatbot_indexes:

            cursor.execute(query)

        # ====================================================
        # GENERAL INDEXES
        # ====================================================

        general_indexes = [

            """
            CREATE INDEX IF NOT EXISTS
            idx_users_role
            ON users(role)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_users_language
            ON users(preferred_language)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_farmer_profiles_user
            ON farmer_profiles(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_consumer_profiles_user
            ON consumer_profiles(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_crops_farmer
            ON crops(farmer_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_crops_status
            ON crops(status)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_marketplace_farmer
            ON marketplace_products(farmer_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_marketplace_category
            ON marketplace_products(category)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_marketplace_status
            ON marketplace_products(status)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_market_prices_commodity
            ON market_prices(commodity)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_market_prices_market
            ON market_prices(market)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_market_prices_state
            ON market_prices(state)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_market_prices_date
            ON market_prices(arrival_date DESC)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_buyer
            ON orders(buyer_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_farmer
            ON orders(farmer_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_product
            ON orders(product_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_status
            ON orders(delivery_status)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_order_items_order
            ON order_items(order_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_order_items_product
            ON order_items(product_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_cart_user
            ON cart(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_cart_product
            ON cart(product_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_wishlist_user
            ON wishlist(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_wishlist_product
            ON wishlist(product_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_notifications_user
            ON notifications(user_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_notifications_read
            ON notifications(is_read)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_notifications_created
            ON notifications(created_at DESC)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_expenses_farmer
            ON farm_expenses(farmer_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_income_farmer
            ON farm_income(farmer_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_transactions_user
            ON transactions(user_id)
            """,
        ]

        for query in general_indexes:

            cursor.execute(query)

        # ====================================================
        # CHATBOT VIEWS
        # ====================================================

        cursor.execute(
            """
            CREATE OR REPLACE VIEW chatbot_statistics AS
            SELECT
                COUNT(*) AS total_messages,
                COUNT(DISTINCT user_id) AS total_users,
                COUNT(DISTINCT session_id) AS total_sessions,
                COUNT(DISTINCT intent) AS total_intents
            FROM chat_messages
            """
        )

        cursor.execute(
            """
            CREATE OR REPLACE VIEW chatbot_user_summary AS
            SELECT
                user_id,
                COUNT(*) AS total_messages,
                COUNT(DISTINCT session_id) AS total_sessions,
                MAX(created_at) AS last_message_at
            FROM chat_messages
            GROUP BY user_id
            """
        )

        # ====================================================
        # COMMIT
        # ====================================================

        connection.commit()

        print()
        print("=" * 65)
        print("KISANVISION360+ DATABASE INITIALIZED")
        print("=" * 65)
        print("Database : PostgreSQL / Supabase")
        print("Users    : password_hash / preferred_language")
        print("Chatbot  : sessions / messages / feedback / context")
        print("Status   : READY")
        print("=" * 65)
        print()

        return True

    except Exception as error:

        if connection:

            connection.rollback()

        print()
        print("=" * 65)
        print("DATABASE INITIALIZATION ERROR")
        print("=" * 65)
        print(error)
        print("=" * 65)
        print()

        return False

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CONNECTION TEST
# ============================================================

def test_connection():
    """
    Test PostgreSQL/Supabase connection.
    """

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                current_database() AS database_name,
                current_user AS database_user,
                version() AS postgres_version
            """
        )

        result = cursor.fetchone()

        return {
            "success": True,
            "database": result["database_name"],
            "user": result["database_user"],
            "version": result["postgres_version"],
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error),
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# DATABASE HEALTH
# ============================================================

def database_health():
    """
    Return database health.
    """

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                1 AS status,
                current_database() AS database_name
            """
        )

        result = cursor.fetchone()

        return {
            "status": "healthy",
            "database": "PostgreSQL",
            "database_name": result["database_name"],
            "connected": result["status"] == 1,
        }

    except Exception as error:

        return {
            "status": "unhealthy",
            "database": "PostgreSQL",
            "connected": False,
            "error": str(error),
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# GET TABLE COLUMNS
# ============================================================

def get_table_columns(table_name):
    """
    Return table column information.
    """

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )

        return cursor.fetchall()

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# APPLICATION TABLES
# ============================================================

def get_application_tables():
    """
    Return all public application tables.
    """

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )

        rows = cursor.fetchall()

        return [
            row["table_name"]
            for row in rows
        ]

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print("KisanVision360+ Database Test")
    print("=" * 65)

    # --------------------------------------------------------
    # CONNECTION TEST
    # --------------------------------------------------------

    result = test_connection()

    if not result["success"]:

        print()
        print("DATABASE CONNECTION: FAILED")
        print("ERROR:", result["error"])
        print()

        raise SystemExit(1)

    print()
    print("Database connection : SUCCESS")
    print("Database            :", result["database"])
    print("User                :", result["user"])

    # --------------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------------

    print()
    print("Creating/upgrading database tables...")

    success = init_db()

    if not success:

        print()
        print("DATABASE SETUP: FAILED")
        raise SystemExit(1)

    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------

    health = database_health()

    print()
    print("Database health:")
    print(health)

    # --------------------------------------------------------
    # TABLES
    # --------------------------------------------------------

    print()
    print("Application tables:")

    try:

        tables = get_application_tables()

        for table in tables:
            print("  -", table)

    except Exception as error:

        print(
            "Could not read tables:",
            error,
        )

    print()
    print("=" * 65)
    print("DATABASE SETUP COMPLETED")
    print("=" * 65)
    print()
