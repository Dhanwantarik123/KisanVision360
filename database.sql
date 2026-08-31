PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    username TEXT UNIQUE,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'Farmer',
    location TEXT,
    profile_pic TEXT
);

CREATE TABLE IF NOT EXISTS crops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    crop_name TEXT,
    crop_type TEXT,
    sowing_date TEXT,
    soil_type TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    city TEXT,
    temperature REAL,
    humidity REAL,
    rainfall REAL,
    description TEXT,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS disease (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    image TEXT,
    disease_name TEXT,
    confidence REAL,
    symptoms TEXT,
    treatment TEXT,
    prevention TEXT,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS irrigation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    crop_name TEXT,
    soil_moisture REAL,
    irrigation_required TEXT,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_name TEXT NOT NULL,
    category TEXT,
    quantity REAL NOT NULL DEFAULT 0,
    unit TEXT DEFAULT 'kg',
    price REAL NOT NULL DEFAULT 0,
    description TEXT,
    image TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS consumer_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    crop TEXT NOT NULL,
    quantity REAL NOT NULL,
    budget REAL NOT NULL,
    location TEXT,
    requirement TEXT,
    status TEXT DEFAULT 'Open',
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    product_name TEXT,
    quantity REAL,
    price REAL,
    total REAL,
    status TEXT DEFAULT 'Processing',
    payment_status TEXT DEFAULT 'Pending',
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    report_type TEXT,
    report_data TEXT,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    message TEXT,
    is_read INTEGER DEFAULT 0,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS finance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    amount REAL,
    description TEXT,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS government (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_name TEXT,
    description TEXT,
    eligibility TEXT,
    benefits TEXT,
    link TEXT
);

CREATE TABLE IF NOT EXISTS chatbot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    question TEXT,
    answer TEXT,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    message TEXT,
    date TEXT,
    is_read INTEGER DEFAULT 0,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);