# ============================================================
# KISANVISION360+ — HELP & SUPPORT ROUTES
# File: routes/help.py
# ============================================================

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
)
from functools import wraps
from datetime import datetime
import os

from database.db import get_db_connection


# ============================================================
# BLUEPRINT
# ============================================================

help_bp = Blueprint("help", __name__)


# ============================================================
# CONSTANTS
# ============================================================

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "kn": "Kannada",
    "te": "Telugu",
    "ta": "Tamil",
    "ml": "Malayalam",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "bn": "Bengali",
    "as": "Assamese",
    "or": "Odia",
    "ur": "Urdu",
    "ne": "Nepali",
    "sa": "Sanskrit",
    "kok": "Konkani",
    "mai": "Maithili",
    "ks": "Kashmiri",
    "sd": "Sindhi",
    "mni": "Manipuri",
}

RTL_LANGUAGES = {"ur", "ks", "sd"}


# ============================================================
# LOGIN DECORATOR
# ============================================================

def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "message": "Login required"
                }), 401

            return jsonify({
                "success": False,
                "message": "Please login first"
            }), 401

        return view_function(*args, **kwargs)

    return wrapped_view


# ============================================================
# HELP DATA
# ============================================================

FAQ_DATA = [

    {
        "id": 1,
        "category": "account",
        "question": "How can I create an account?",
        "answer": (
            "Open the Signup page, enter your name, mobile number, "
            "email, password and select your role. Then submit the form."
        ),
        "keywords": ["signup", "register", "account", "create account"]
    },

    {
        "id": 2,
        "category": "account",
        "question": "How can I change my password?",
        "answer": (
            "Open Settings or Change Password and enter your current "
            "password and the new password."
        ),
        "keywords": ["password", "change password", "security"]
    },

    {
        "id": 3,
        "category": "language",
        "question": "How can I change the application language?",
        "answer": (
            "Language is a global application setting. Change it from "
            "the Language Selection page or Settings. The selected "
            "language is used throughout the application."
        ),
        "keywords": ["language", "marathi", "hindi", "translation"]
    },

    {
        "id": 4,
        "category": "farmer",
        "question": "How does Crop Advisor work?",
        "answer": (
            "Crop Advisor evaluates factors such as soil type, season, "
            "temperature, water availability, budget and farming goal "
            "to rank suitable crops."
        ),
        "keywords": ["crop advisor", "crop recommendation", "crop"]
    },

    {
        "id": 5,
        "category": "farmer",
        "question": "How does Disease Detection work?",
        "answer": (
            "Upload a clear crop or leaf image. The trained CNN model "
            "analyses the image and returns the predicted disease class, "
            "confidence and recommended precautions."
        ),
        "keywords": ["disease", "cnn", "image", "plant disease"]
    },

    {
        "id": 6,
        "category": "farmer",
        "question": "How does Smart Irrigation work?",
        "answer": (
            "Smart Irrigation uses crop, farm area, irrigation method "
            "and available weather information to estimate water "
            "requirements and provide irrigation guidance."
        ),
        "keywords": ["irrigation", "water", "smart irrigation"]
    },

    {
        "id": 7,
        "category": "farmer",
        "question": "Where can I see market prices?",
        "answer": (
            "Open the Market or Mandi section to view available crop "
            "market information and price data."
        ),
        "keywords": ["market", "mandi", "price", "market price"]
    },

    {
        "id": 8,
        "category": "farmer",
        "question": "How can I sell my farm products?",
        "answer": (
            "Farmers can add products through the Marketplace section "
            "with product name, category, price, quantity and other "
            "available information."
        ),
        "keywords": ["sell", "product", "marketplace", "farmer marketplace"]
    },

    {
        "id": 9,
        "category": "consumer",
        "question": "How can I buy a product?",
        "answer": (
            "Open Marketplace, search for a product, check its details "
            "and add it to your cart or use Buy Now."
        ),
        "keywords": ["buy", "consumer", "purchase", "cart"]
    },

    {
        "id": 10,
        "category": "consumer",
        "question": "Where can I see my orders?",
        "answer": (
            "Open the Orders section from the consumer dashboard to "
            "view your order information."
        ),
        "keywords": ["order", "orders", "purchase history"]
    },

    {
        "id": 11,
        "category": "finance",
        "question": "What is Farm Finance?",
        "answer": (
            "Farm Finance helps farmers track income and expenses and "
            "calculate useful financial indicators such as profit, "
            "ROI and financial summaries."
        ),
        "keywords": ["finance", "income", "expense", "profit", "roi"]
    },

    {
        "id": 12,
        "category": "schemes",
        "question": "Where can I find government schemes?",
        "answer": (
            "Open Government Schemes to explore schemes and their "
            "available information. Always verify eligibility and "
            "application details on the official government source."
        ),
        "keywords": ["scheme", "government", "subsidy", "yojana"]
    },

    {
        "id": 13,
        "category": "weather",
        "question": "Where can I check weather information?",
        "answer": (
            "Open Weather to view current weather and available "
            "forecast information for the selected location."
        ),
        "keywords": ["weather", "rain", "temperature", "forecast"]
    },

    {
        "id": 14,
        "category": "profile",
        "question": "How can I update my farm profile?",
        "answer": (
            "Open Profile and update farm location, land area, soil, "
            "irrigation type, crop and other available farm details."
        ),
        "keywords": ["profile", "farm profile", "land", "soil"]
    },

    {
        "id": 15,
        "category": "notifications",
        "question": "What are smart notifications?",
        "answer": (
            "Notifications can provide useful application alerts such "
            "as weather-related information, market updates, disease "
            "alerts and government scheme reminders."
        ),
        "keywords": ["notification", "alert", "alerts"]
    },

    {
        "id": 16,
        "category": "chatbot",
        "question": "What can the AI Assistant do?",
        "answer": (
            "The KisanVision360+ AI Assistant provides role-based "
            "guidance for farming, weather, crops, irrigation, disease, "
            "marketplace, finance, schemes and other application features."
        ),
        "keywords": ["chatbot", "ai assistant", "assistant", "help"]
    },

    {
        "id": 17,
        "category": "technical",
        "question": "Why is my image not uploading?",
        "answer": (
            "Use a JPG, JPEG, PNG or WEBP image and keep the file size "
            "within the application's upload limit. A clear crop or "
            "leaf image gives better disease-detection results."
        ),
        "keywords": ["upload", "image upload", "photo", "file"]
    },

    {
        "id": 18,
        "category": "technical",
        "question": "What should I do if a page shows an error?",
        "answer": (
            "Refresh the page and try again. If the problem continues, "
            "check your internet connection and report the page name "
            "and error message through Support."
        ),
        "keywords": ["error", "problem", "bug", "page error"]
    },

]


# ============================================================
# LOCALIZED COMMON TEXT
# ============================================================

TEXT = {
    "en": {
        "title": "Help & Support",
        "subtitle": "Get help with KisanVision360+ features",
        "welcome": "How can we help you?",
        "search": "Search help topics",
        "faq": "Frequently Asked Questions",
        "contact": "Contact Support",
    },

    "hi": {
        "title": "सहायता और समर्थन",
        "subtitle": "KisanVision360+ सुविधाओं में सहायता प्राप्त करें",
        "welcome": "हम आपकी कैसे सहायता कर सकते हैं?",
        "search": "सहायता विषय खोजें",
        "faq": "अक्सर पूछे जाने वाले प्रश्न",
        "contact": "सहायता से संपर्क करें",
    },

    "mr": {
        "title": "मदत आणि समर्थन",
        "subtitle": "KisanVision360+ सुविधांसाठी मदत मिळवा",
        "welcome": "आम्ही तुमची कशी मदत करू शकतो?",
        "search": "मदत विषय शोधा",
        "faq": "वारंवार विचारले जाणारे प्रश्न",
        "contact": "सपोर्टशी संपर्क करा",
    },

    "kn": {
        "title": "ಸಹಾಯ ಮತ್ತು ಬೆಂಬಲ",
        "subtitle": "KisanVision360+ ವೈಶಿಷ್ಟ್ಯಗಳಿಗೆ ಸಹಾಯ ಪಡೆಯಿರಿ",
        "welcome": "ನಾವು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
        "search": "ಸಹಾಯ ವಿಷಯಗಳನ್ನು ಹುಡುಕಿ",
        "faq": "ಪದೇ ಪದೇ ಕೇಳಲಾಗುವ ಪ್ರಶ್ನೆಗಳು",
        "contact": "ಬೆಂಬಲವನ್ನು ಸಂಪರ್ಕಿಸಿ",
    },

    "te": {
        "title": "సహాయం మరియు మద్దతు",
        "subtitle": "KisanVision360+ ఫీచర్లకు సహాయం పొందండి",
        "welcome": "మేము మీకు ఎలా సహాయం చేయగలం?",
        "search": "సహాయ అంశాలను శోధించండి",
        "faq": "తరచుగా అడిగే ప్రశ్నలు",
        "contact": "మద్దతును సంప్రదించండి",
    },

    "ta": {
        "title": "உதவி மற்றும் ஆதரவு",
        "subtitle": "KisanVision360+ அம்சங்களுக்கு உதவி பெறுங்கள்",
        "welcome": "நாங்கள் உங்களுக்கு எப்படி உதவலாம்?",
        "search": "உதவி தலைப்புகளைத் தேடுங்கள்",
        "faq": "அடிக்கடி கேட்கப்படும் கேள்விகள்",
        "contact": "ஆதரவைத் தொடர்பு கொள்ளுங்கள்",
    },

    "gu": {
        "title": "મદદ અને સપોર્ટ",
        "subtitle": "KisanVision360+ સુવિધાઓ માટે મદદ મેળવો",
        "welcome": "અમે તમારી કેવી રીતે મદદ કરી શકીએ?",
        "search": "મદદના વિષયો શોધો",
        "faq": "વારંવાર પૂછાતા પ્રશ્નો",
        "contact": "સપોર્ટનો સંપર્ક કરો",
    },
}


# ============================================================
# TRANSLATION HELPER
# ============================================================

def get_language():
    language = session.get("language", "en")

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    return language


def get_text():
    language = get_language()

    return TEXT.get(
        language,
        TEXT["en"]
    )


# ============================================================
# CATEGORY DATA
# ============================================================

HELP_CATEGORIES = [
    {
        "id": "account",
        "name": "Account & Security",
        "icon": "fa-user-shield",
        "description": "Login, signup and password help"
    },
    {
        "id": "farmer",
        "name": "Farmer Features",
        "icon": "fa-seedling",
        "description": "Crop, disease, irrigation and farm guidance"
    },
    {
        "id": "consumer",
        "name": "Consumer & Shopping",
        "icon": "fa-cart-shopping",
        "description": "Marketplace, cart and orders"
    },
    {
        "id": "weather",
        "name": "Weather",
        "icon": "fa-cloud-sun",
        "description": "Weather and forecast information"
    },
    {
        "id": "finance",
        "name": "Finance",
        "icon": "fa-indian-rupee-sign",
        "description": "Income, expenses and financial tools"
    },
    {
        "id": "schemes",
        "name": "Government Schemes",
        "icon": "fa-landmark",
        "description": "Scheme discovery and information"
    },
    {
        "id": "technical",
        "name": "Technical Support",
        "icon": "fa-screwdriver-wrench",
        "description": "Application errors and technical problems"
    },
    {
        "id": "chatbot",
        "name": "AI Assistant",
        "icon": "fa-robot",
        "description": "Using the KisanVision360+ AI Assistant"
    },
]


# ============================================================
# SUPPORT CONTACT
# ============================================================

def get_support_info():

    return {
        "application": "KisanVision360+",
        "support_type": "Application Support",
        "available": True,
        "response": "Support requests are reviewed by the application team.",
        "email": os.getenv(
            "SUPPORT_EMAIL",
            "support@kisanvision360.com"
        ),
    }


# ============================================================
# HELP HOME
# ============================================================

@help_bp.route("/help")
@login_required
def help_page():

    language = get_language()

    return render_template(
        "help.html",
        language=language,
        language_name=SUPPORTED_LANGUAGES.get(
            language,
            "English"
        ),
        direction="rtl" if language in RTL_LANGUAGES else "ltr",
        text=get_text(),
        faqs=FAQ_DATA,
        categories=HELP_CATEGORIES,
        support=get_support_info(),
        role=session.get("role", ""),
        name=session.get("name", "User"),
    )


# ============================================================
# FAQ API
# ============================================================

@help_bp.route("/api/help/faqs", methods=["GET"])
@login_required
def get_faqs():

    category = (
        request.args.get("category", "")
        .strip()
        .lower()
    )

    search = (
        request.args.get("q", "")
        .strip()
        .lower()
    )

    results = FAQ_DATA

    if category:
        results = [
            item for item in results
            if item["category"].lower() == category
        ]

    if search:

        filtered = []

        for item in results:

            searchable = " ".join([
                item["question"],
                item["answer"],
                item["category"],
                " ".join(item.get("keywords", []))
            ]).lower()

            if search in searchable:
                filtered.append(item)

        results = filtered

    return jsonify({
        "success": True,
        "count": len(results),
        "language": get_language(),
        "faqs": results,
    })


# ============================================================
# FAQ SINGLE ITEM
# ============================================================

@help_bp.route("/api/help/faqs/<int:faq_id>", methods=["GET"])
@login_required
def get_faq(faq_id):

    faq = next(
        (
            item for item in FAQ_DATA
            if item["id"] == faq_id
        ),
        None
    )

    if not faq:
        return jsonify({
            "success": False,
            "message": "FAQ not found"
        }), 404

    return jsonify({
        "success": True,
        "faq": faq,
        "language": get_language(),
    })


# ============================================================
# HELP CATEGORIES
# ============================================================

@help_bp.route("/api/help/categories", methods=["GET"])
@login_required
def get_categories():

    return jsonify({
        "success": True,
        "count": len(HELP_CATEGORIES),
        "categories": HELP_CATEGORIES,
    })


# ============================================================
# SMART HELP SEARCH
# ============================================================

@help_bp.route("/api/help/search", methods=["GET", "POST"])
@login_required
def smart_help_search():

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        query = str(
            data.get("query", "")
        ).strip().lower()
    else:
        query = str(
            request.args.get("q", "")
        ).strip().lower()

    if not query:

        return jsonify({
            "success": True,
            "query": "",
            "count": 0,
            "results": [],
            "message": "Enter a help question."
        })

    words = [
        word
        for word in query.split()
        if len(word) >= 2
    ]

    scored_results = []

    for faq in FAQ_DATA:

        searchable = " ".join([
            faq["question"],
            faq["answer"],
            faq["category"],
            " ".join(faq.get("keywords", []))
        ]).lower()

        score = 0

        if query in faq["question"].lower():
            score += 10

        if query in searchable:
            score += 5

        for word in words:
            if word in searchable:
                score += 1

        if score > 0:
            scored_results.append({
                **faq,
                "score": score
            })

    scored_results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return jsonify({
        "success": True,
        "query": query,
        "count": len(scored_results),
        "results": scored_results[:10],
    })


# ============================================================
# SUPPORT REQUEST TABLE
# ============================================================

def ensure_support_table(connection):

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_requests (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT,
            name VARCHAR(150),
            email VARCHAR(255),
            category VARCHAR(100),
            subject VARCHAR(255),
            message TEXT NOT NULL,
            status VARCHAR(30) DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_support_user
        ON support_requests(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_support_status
        ON support_requests(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_support_created
        ON support_requests(created_at DESC)
    """)

    connection.commit()


# ============================================================
# CREATE SUPPORT REQUEST
# ============================================================

@help_bp.route("/api/help/contact", methods=["POST"])
@login_required
def create_support_request():

    data = request.get_json(silent=True) or request.form.to_dict()

    user_id = session.get("user_id")

    name = str(
        data.get(
            "name",
            session.get("name", "User")
        )
    ).strip()

    email = str(
        data.get("email", "")
    ).strip()

    category = str(
        data.get(
            "category",
            "general"
        )
    ).strip()

    subject = str(
        data.get(
            "subject",
            "KisanVision360+ Support"
        )
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    if not message:

        return jsonify({
            "success": False,
            "message": "Please enter your support message."
        }), 400

    if len(message) > 5000:

        return jsonify({
            "success": False,
            "message": "Support message is too long."
        }), 400

    connection = None

    try:

        connection = get_db_connection()

        ensure_support_table(connection)

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO support_requests
            (
                user_id,
                name,
                email,
                category,
                subject,
                message,
                status,
                created_at,
                updated_at
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'open',
                %s,
                %s
            )
            RETURNING id
        """, (
            user_id,
            name,
            email,
            category,
            subject,
            message,
            datetime.utcnow(),
            datetime.utcnow(),
        ))

        row = cursor.fetchone()

        request_id = (
            row[0]
            if row
            else None
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": (
                "Your support request has been submitted successfully."
            ),
            "request_id": request_id,
            "status": "open",
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "HELP SUPPORT ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to submit support request right now."
            )
        }), 500

    finally:

        if connection:

            try:
                connection.close()
            except Exception:
                pass


# ============================================================
# USER SUPPORT HISTORY
# ============================================================

@help_bp.route("/api/help/my-requests", methods=["GET"])
@login_required
def my_support_requests():

    user_id = session.get("user_id")

    connection = None

    try:

        connection = get_db_connection()

        ensure_support_table(connection)

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                category,
                subject,
                message,
                status,
                created_at,
                updated_at
            FROM support_requests
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))

        rows = cursor.fetchall()

        requests_list = []

        for row in rows:

            if hasattr(row, "keys"):

                item = dict(row)

            else:

                item = {
                    "id": row[0],
                    "category": row[1],
                    "subject": row[2],
                    "message": row[3],
                    "status": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                }

            for key in [
                "created_at",
                "updated_at"
            ]:

                if item.get(key):
                    item[key] = item[key].isoformat()

            requests_list.append(item)

        return jsonify({
            "success": True,
            "count": len(requests_list),
            "requests": requests_list,
        })

    except Exception as error:

        print(
            "HELP HISTORY ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to load support history.",
            "requests": []
        }), 500

    finally:

        if connection:

            try:
                connection.close()
            except Exception:
                pass


# ============================================================
# SUPPORT INFORMATION
# ============================================================

@help_bp.route("/api/help/support", methods=["GET"])
@login_required
def support_information():

    return jsonify({
        "success": True,
        "support": get_support_info(),
    })


# ============================================================
# APP GUIDANCE
# ============================================================

@help_bp.route("/api/help/getting-started", methods=["GET"])
@login_required
def getting_started():

    role = (
        session.get("role", "")
        .lower()
        .strip()
    )

    common_steps = [
        {
            "step": 1,
            "title": "Complete your profile",
            "description": (
                "Add your basic profile and location information."
            )
        },
        {
            "step": 2,
            "title": "Set your language",
            "description": (
                "Choose your preferred application language once."
            )
        },
        {
            "step": 3,
            "title": "Explore the dashboard",
            "description": (
                "Use the dashboard to access connected KisanVision360+ modules."
            )
        },
    ]

    farmer_steps = [
        {
            "step": 4,
            "title": "Add farm details",
            "description": (
                "Enter land, soil, irrigation and crop information."
            )
        },
        {
            "step": 5,
            "title": "Use Crop Advisor",
            "description": (
                "Compare suitable crops using farm and weather information."
            )
        },
        {
            "step": 6,
            "title": "Use farm intelligence",
            "description": (
                "Explore weather, disease detection, irrigation, market, "
                "finance and schemes."
            )
        },
    ]

    consumer_steps = [
        {
            "step": 4,
            "title": "Explore Marketplace",
            "description": (
                "Search products available from farmers."
            )
        },
        {
            "step": 5,
            "title": "Use Cart & Wishlist",
            "description": (
                "Save products or add products to your shopping cart."
            )
        },
        {
            "step": 6,
            "title": "Track Orders",
            "description": (
                "View your purchase and order information."
            )
        },
    ]

    admin_steps = [
        {
            "step": 4,
            "title": "Review platform data",
            "description": (
                "Monitor users, products, orders and notifications."
            )
        },
        {
            "step": 5,
            "title": "Manage platform content",
            "description": (
                "Maintain available application information and services."
            )
        },
    ]

    if role == "farmer":
        steps = common_steps + farmer_steps

    elif role == "consumer":
        steps = common_steps + consumer_steps

    elif role == "admin":
        steps = common_steps + admin_steps

    else:
        steps = common_steps

    return jsonify({
        "success": True,
        "role": role,
        "steps": steps,
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@help_bp.route("/api/help/health", methods=["GET"])
def help_health():

    database_status = "unknown"

    connection = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute("SELECT 1")

        cursor.fetchone()

        database_status = "connected"

    except Exception as error:

        database_status = "error"

        print(
            "HELP HEALTH DB ERROR:",
            error
        )

    finally:

        if connection:

            try:
                connection.close()
            except Exception:
                pass

    return jsonify({
        "success": True,
        "service": "help",
        "status": "healthy",
        "database": database_status,
        "language": get_language(),
        "supported_languages": len(
            SUPPORTED_LANGUAGES
        ),
        "faq_count": len(FAQ_DATA),
        "timestamp": datetime.utcnow().isoformat(),
    })


# ============================================================
# BLUEPRINT READY
# ============================================================
