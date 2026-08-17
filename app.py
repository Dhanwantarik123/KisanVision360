import os
import sqlite3
import requests
import numpy as np
import tensorflow as tf

from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify,
    url_for,
    flash
)
from utils.mandi_price import get_market_price
from werkzeug.utils import secure_filename

from PIL import Image

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

from db import db, cursor

from utils.crop_price import get_crop_prices
from utils.mandi_price import get_market_price
from utils.schemes import get_schemes

app = Flask(__name__)
# =========================================================
# AI DISEASE MODEL
# =========================================================

MODEL_PATH = os.path.join(
    app.root_path,
    "ai_models",
    "disease_model.keras"
)


disease_model = tf.keras.models.load_model(
    MODEL_PATH
)


# =========================================================
# LOAD DISEASE CLASS NAMES
# =========================================================

CLASS_FILE = os.path.join(
    app.root_path,
    "ai_models",
    "disease_classes.txt"
)


with open(CLASS_FILE, "r") as file:

    DISEASE_CLASSES = [
        line.strip()
        for line in file
        if line.strip()
    ]


print("Disease classes:")

for i, name in enumerate(DISEASE_CLASSES):

    print(i, "=", name)
app.config["UPLOAD_FOLDER"] = "static/uploads"

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)
app.secret_key = "kisanvision360_secret_key"
WEATHER_API_KEY = "a03114f8eb4b0276cd6efa27c6f4613d"   # Replace with your OpenWeather API Key
CITY = "Nagpur"
@app.route("/")


@app.route("/language")
def language():
    return render_template("language.html")

@app.route("/set-language", methods=["POST"])
def set_language():

    if "user_id" not in session:
        return redirect("/login")

    session["language"] = request.form["language"]

    return redirect("/settings")
import tensorflow as tf

disease_model = tf.keras.models.load_model(
    "ai_models/disease_model.keras"
)


DISEASE_CLASSES = [

    "Healthy",

    "Early Blight",

    "Late Blight",

    "Leaf Spot"

]
@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:

        if session["role"] == "Farmer":
            return redirect("/farmer")
        elif session["role"] == "Consumer":
            return redirect("/consumer")
        else:
            return redirect("/admin")

    if request.method == "POST":

        login = request.form.get("login", "").strip()
        password = request.form.get("password", "").strip()

        sql = """
        SELECT id, fullname, mobile, email, password, role
        FROM users
        WHERE (mobile=%s OR email=%s) AND password=%s
        """

        cursor.execute(sql, (login, login, password))
        user = cursor.fetchone()

        print("User:", user)

        if user:

            session["user_id"] = user[0]
            session["name"] = user[1]
            session["role"] = user[5]

            role = user[5].strip().lower()

            if role == "farmer":
                return redirect("/farmer")
            elif role == "consumer":
                return redirect("/consumer")
            else:
                return redirect("/admin")

        return render_template(
            "login.html",
            error="Invalid Mobile/Email or Password"
        )

    return render_template("login.html")



@app.route("/orders")
def orders():

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute("""
        SELECT
            id,
            user_id,
            product_id,
            quantity,
            total_price,
            status,
            date
        FROM orders
        WHERE user_id=%s
        ORDER BY id DESC
    """, (session["user_id"],))

    orders = cursor.fetchall()

    return render_template(
        "orders.html",
        orders=orders,
        name=session["name"]
    )

@app.route("/place_order/<int:product_id>", methods=["POST"])
def place_order(product_id):

    if "user_id" not in session:
        return redirect("/login")

    qty = int(request.form.get("quantity", 1))

    cursor.execute(
        "SELECT name, price FROM products WHERE id=%s",
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        return "Product not found"

    name = product[0]
    price = float(product[1])

    total = price * qty

    cursor.execute("""
        INSERT INTO orders
        (user_id, product_name, quantity, price, total)
        VALUES(%s,%s,%s,%s,%s)
    """,
    (
        session["user_id"],
        name,
        qty,
        price,
        total
    ))

    db.commit()

    return redirect("/orders")

@app.route("/finance")
def finance():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role", "").lower() != "farmer":
        return redirect("/dashboard")

    farmer_id = session["user_id"]

    # =========================
    # TOTAL INCOME
    # =========================

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE farmer_id = ?
        AND type = 'Income'
    """, (farmer_id,))

    income = cursor.fetchone()[0] or 0


    # =========================
    # TOTAL EXPENSE
    # =========================

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE farmer_id = ?
        AND type = 'Expense'
    """, (farmer_id,))

    expenses = cursor.fetchone()[0] or 0


    # =========================
    # NET PROFIT
    # =========================

    profit = income - expenses


    # =========================
    # RECENT TRANSACTIONS
    # =========================

    cursor.execute("""
        SELECT
            description,
            amount,
            type,
            date
        FROM transactions
        WHERE farmer_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (farmer_id,))

    transactions = cursor.fetchall()


    # =========================
    # FINANCE PAGE
    # =========================

    return render_template(
        "finance.html",

        name=session.get("name", "Farmer"),

        income=income,

        expenses=expenses,

        profit=profit,

        transactions=transactions
    )

@app.route("/income", methods=["GET", "POST"])
def income():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    if request.method == "POST":

        description = request.form["description"]
        amount = request.form["amount"]

        cursor.execute("""
            INSERT INTO transactions
            (farmer_id, description, amount, type)
            VALUES(%s,%s,%s,'Income')
        """, (user_id, description, amount))

        db.commit()

        return redirect("/income")

    cursor.execute("""
        SELECT
            DATE(created_at),
            description,
            amount
        FROM transactions
        WHERE farmer_id=%s
        AND type='Income'
        ORDER BY id DESC
    """, (user_id,))

    income_list = cursor.fetchall()

    return render_template(
        "income.html",
        name=session["name"],
        income_list=income_list
    )


@app.route("/expense", methods=["GET", "POST"])
def expense():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    if request.method == "POST":

        description = request.form["description"]
        amount = request.form["amount"]

        cursor.execute("""
            INSERT INTO transactions
            (farmer_id, description, amount, type)
            VALUES(%s,%s,%s,'Expense')
        """, (user_id, description, amount))

        db.commit()

        return redirect("/expense")

    cursor.execute("""
        SELECT
            DATE(created_at),
            description,
            amount
        FROM transactions
        WHERE farmer_id=%s
        AND type='Expense'
        ORDER BY id DESC
    """, (user_id,))

    expense_list = cursor.fetchall()

    return render_template(
        "expense.html",
        name=session["name"],
        expense_list=expense_list
    )
# =========================================================
# DISEASE PAGE
# =========================================================

@app.route("/disease")
def disease():

    return render_template(
        "disease.html"
    )


# =========================================================
# AI DISEASE PREDICTION
# =========================================================

@app.route(
    "/predict_disease",
    methods=["POST"]
)
def predict_disease():

    # -----------------------------------------------------
    # CHECK IMAGE
    # -----------------------------------------------------

    if "image" not in request.files:

        return render_template(
            "disease.html",
            error="Please select an image."
        )


    file = request.files["image"]


    if file.filename == "":

        return render_template(
            "disease.html",
            error="Please select an image."
        )


    # -----------------------------------------------------
    # UPLOAD FOLDER
    # -----------------------------------------------------

    upload_folder = app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(
            app.static_folder,
            "uploads"
        )
    )


    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    # -----------------------------------------------------
    # SAFE FILE NAME
    # -----------------------------------------------------

    image_name = secure_filename(
        file.filename
    )


    upload_path = os.path.join(
        upload_folder,
        image_name
    )


    file.save(
        upload_path
    )


    # -----------------------------------------------------
    # DISEASE INFORMATION
    # -----------------------------------------------------

    disease_info = {

        "bacterial_blight": {

            "status": "Disease Detected",

            "symptoms":
            "Water-soaked or brown lesions may appear on leaves.",

            "treatment":
            "Remove severely affected plant material and follow crop-specific disease management recommendations.",

            "prevention":
            "Use healthy planting material and avoid unnecessary leaf wetness."
        },


        "brown_spot": {

            "status": "Disease Detected",

            "symptoms":
            "Brown spots or lesions can appear on the leaves.",

            "treatment":
            "Remove affected material and use an appropriate crop-specific treatment.",

            "prevention":
            "Maintain proper spacing and avoid excessive moisture."
        },


        "crestamento": {

            "status": "Disease Detected",

            "symptoms":
            "Leaf discoloration and disease-related damage may be visible.",

            "treatment":
            "Consult an agricultural expert for crop-specific treatment.",

            "prevention":
            "Monitor crops regularly and maintain good field sanitation."
        },


        "ferrugen": {

            "status": "Disease Detected",

            "symptoms":
            "Rust-like spots or lesions may appear on leaves.",

            "treatment":
            "Use a suitable crop-specific fungicide according to the product label.",

            "prevention":
            "Improve air circulation and avoid prolonged leaf wetness."
        },


        "Mosaic Virus": {

            "status": "Disease Detected",

            "symptoms":
            "Mosaic-like light and dark green patterns may appear on leaves.",

            "treatment":
            "Remove severely infected plants and control disease vectors where applicable.",

            "prevention":
            "Use healthy planting material and monitor for insect vectors."
        },


        "powdery_mildew": {

            "status": "Disease Detected",

            "symptoms":
            "White powder-like growth may appear on leaf surfaces.",

            "treatment":
            "Use a suitable crop-specific fungicide according to the product label.",

            "prevention":
            "Improve air circulation and avoid excessive humidity."
        },


        "septoria": {

            "status": "Disease Detected",

            "symptoms":
            "Small dark spots may develop on leaves and may enlarge over time.",

            "treatment":
            "Remove affected leaves and follow crop-specific disease management recommendations.",

            "prevention":
            "Avoid overhead watering and maintain good field sanitation."
        },


        "Southern blight": {

            "status": "Disease Detected",

            "symptoms":
            "Wilting and brown lesions may develop near the base of the plant.",

            "treatment":
            "Remove affected plants and follow appropriate crop-specific management practices.",

            "prevention":
            "Maintain good drainage and avoid excessive soil moisture."
        },


        "Sudden Death Syndrome": {

            "status": "Disease Detected",

            "symptoms":
            "Plants may show yellowing, wilting and premature leaf loss.",

            "treatment":
            "Consult an agricultural expert for crop-specific management.",

            "prevention":
            "Use healthy planting material and maintain proper field management."
        },


        "Yellow Mosaic": {

            "status": "Disease Detected",

            "symptoms":
            "Yellow and green mosaic patterns may appear on the leaves.",

            "treatment":
            "Remove severely infected plants and manage insect vectors where applicable.",

            "prevention":
            "Use healthy planting material and regularly monitor for vector insects."
        }

    }


    # -----------------------------------------------------
    # PREDICTION
    # -----------------------------------------------------

    try:

        # Open image

        image = Image.open(
            upload_path
        ).convert("RGB")


        # Resize

        image = image.resize(
            (224, 224)
        )


        # Convert to NumPy

        image_array = np.array(
            image,
            dtype=np.float32
        )


        # IMPORTANT:
        # Do NOT divide by 255 here.
        #
        # The trained model already contains:
        #
        # Rescaling(1.0 / 255)


        # Add batch dimension

        image_array = np.expand_dims(
            image_array,
            axis=0
        )


        # -------------------------------------------------
        # AI PREDICTION
        # -------------------------------------------------

        prediction = disease_model.predict(
            image_array,
            verbose=0
        )


        # Highest probability

        predicted_index = int(
            np.argmax(
                prediction[0]
            )
        )


        # Confidence

        confidence = float(
            prediction[0][predicted_index]
        ) * 100


        # Disease name

        disease_name = DISEASE_CLASSES[
            predicted_index
        ]


        # -------------------------------------------------
        # GET DISEASE INFORMATION
        # -------------------------------------------------

        info = disease_info.get(
            disease_name
        )


        # Generic information if class name
        # doesn't exactly match

        if info is None:

            info = {

                "status":
                "Disease Detected",

                "symptoms":
                "Symptoms information is not available.",

                "treatment":
                "Consult an agricultural expert for suitable treatment.",

                "prevention":
                "Monitor the crop regularly and maintain good field sanitation."
            }


        # -------------------------------------------------
        # RETURN RESULT
        # -------------------------------------------------

        return render_template(

            "disease.html",

            image=image_name,

            prediction=disease_name,

            status=info["status"],

            confidence=round(
                confidence,
                2
            ),

            symptoms=info["symptoms"],

            treatment=info["treatment"],

            prevention=info["prevention"]

        )


    # -----------------------------------------------------
    # ERROR
    # -----------------------------------------------------

    except Exception as e:

        print(
            "Disease Detection Error:",
            e
        )


        return render_template(

            "disease.html",

            error=
            "Unable to process image: "
            + str(e)

        )
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        fullname = request.form.get("fullname", "").strip()
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "Farmer").strip()

        if not fullname or not mobile or not email or not password:
            return render_template(
                "signup.html",
                error="Please fill all required fields."
            )

        cursor.execute(
            "SELECT * FROM users WHERE mobile=%s OR email=%s",
            (mobile, email)
        )

        user = cursor.fetchone()

        if user:
            return render_template(
                "signup.html",
                error="Mobile Number or Email already exists."
            )

        sql = """
        INSERT INTO users
        (fullname, mobile, email, password, role)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            fullname,
            mobile,
            email,
            password,
            role
        )

        cursor.execute(sql, values)
        db.commit()

        return redirect("/login")

    return render_template("signup.html")



@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")


    role = session.get("role")


    if role == "Farmer":

        return redirect("/farmer")


    elif role == "Consumer":

        return redirect("/consumer")


    elif role == "Admin":

        return redirect("/admin")


    else:

        return redirect("/login")

@app.route("/farmer")
def farmer():

    if "user_id" not in session:
        return redirect("/login")


    # Role check
    if session.get("role", "").strip().lower() != "farmer":
        return redirect("/dashboard")


    user_id = session["user_id"]


    # Farmer details
    cursor.execute("""
        SELECT id, fullname, mobile, email, role
        FROM users
        WHERE id=%s
    """, (user_id,))


    farmer = cursor.fetchone()


    if not farmer:
        session.clear()
        return redirect("/login")


    # Live weather API
    weather = get_weather_data()


    return render_template(
        "farmer.html",
        name=session["name"],
        farmer=farmer,
        weather=weather
    )







# ==============================
# Weather API Function
# ==============================


def get_weather_data():

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY}&appid={WEATHER_API_KEY}&units=metric"
    )

    try:

        response = requests.get(url, timeout=10)

        response.raise_for_status()

        data = response.json()

        weather = {

            "city": data["name"],

            "country": data["sys"]["country"],

            "temperature": data["main"]["temp"],

            "feels_like": data["main"]["feels_like"],

            "humidity": data["main"]["humidity"],

            "pressure": data["main"]["pressure"],

            "wind": data["wind"]["speed"],

            "condition": data["weather"][0]["main"],

            "description": data["weather"][0]["description"],

            "icon": data["weather"][0]["icon"],

            "visibility": data.get("visibility", 0) / 1000,

            "clouds": data["clouds"]["all"],

            "sunrise": data["sys"]["sunrise"],

            "sunset": data["sys"]["sunset"]

        }

        if "rain" in data:

            weather["rainfall"] = data["rain"].get("1h", 0)

        else:

            weather["rainfall"] = 0

        return weather

    except requests.exceptions.RequestException:

        return {

            "city": CITY,

            "country": "",

            "temperature": "N/A",

            "feels_like": "N/A",

            "humidity": "N/A",

            "pressure": "N/A",

            "wind": "N/A",

            "condition": "Unavailable",

            "description": "Unable to fetch weather data",

            "icon": "",

            "visibility": "N/A",

            "clouds": "N/A",

            "sunrise": "",

            "sunset": "",

            "rainfall": "N/A"

        }

def ask_chatbot():

    user_message = request.json["message"].lower()


    response = agriculture_bot(user_message)


    return jsonify({
        "reply": response
    })



def agriculture_bot(message):


    if "weather" in message:

        return (
            "You can check live weather from the Weather module. "
            "Weather information helps in irrigation and crop planning."
        )


    elif "fertilizer" in message:

        return (
            "Fertilizer selection depends on soil NPK values. "
            "Use soil testing data before fertilizer application."
        )


    elif "irrigation" in message:

        return (
            "Irrigation scheduling depends on crop type, "
            "soil moisture and weather conditions."
        )


    elif "pest" in message or "disease" in message:

        return (
            "For pest detection, upload crop images in Pest & Disease module "
            "for AI analysis."
        )


    elif "crop" in message:

        return (
            "Crop recommendation requires soil nutrients, "
            "temperature, rainfall and humidity data."
        )


    elif "market" in message or "price" in message:

        return (
            "Check Market Prices module for latest crop rates."
        )


    else:

        return (
            "I can help you with crops, weather, fertilizer, "
            "irrigation, pest management and farming guidance."
        )
  
def create_notifications():

    weather = get_weather_data()

    notifications = []

    current_time = datetime.now().strftime("%I:%M %p")


    # Weather notification

    if weather["temperature"] != "N/A":

        notifications.append({

            "type": "weather",

            "title": "Live Weather Update",

            "message":
                f'{weather["city"]}: '
                f'{weather["temperature"]}°C, '
                f'{weather["description"]}. '
                f'Humidity {weather["humidity"]}%.',

            "time": current_time

        })


    # Rain notification

    if weather["rainfall"] != "N/A" and weather["rainfall"] > 0:

        notifications.append({

            "type": "warning",

            "title": "Rain Alert",

            "message":
                f'Rainfall of {weather["rainfall"]} mm '
                f'is reported in {weather["city"]}. '
                'Avoid unnecessary irrigation.',

            "time": current_time

        })


    # High temperature

    if (
        weather["temperature"] != "N/A"
        and weather["temperature"] >= 35
    ):

        notifications.append({

            "type": "warning",

            "title": "High Temperature Alert",

            "message":
                f'Temperature is {weather["temperature"]}°C. '
                'Check soil moisture and provide irrigation '
                'during cooler hours if required.',

            "time": current_time

        })


    # High humidity

    if (
        weather["humidity"] != "N/A"
        and weather["humidity"] >= 80
    ):

        notifications.append({

            "type": "warning",

            "title": "High Humidity Alert",

            "message":
                f'Humidity is {weather["humidity"]}%. '
                'Monitor crops for possible fungal diseases.',

            "time": current_time

        })


    # Strong wind

    if (
        weather["wind"] != "N/A"
        and weather["wind"] >= 8
    ):

        notifications.append({

            "type": "warning",

            "title": "Strong Wind Alert",

            "message":
                f'Wind speed is {weather["wind"]} m/s. '
                'Avoid spraying pesticides during strong winds.',

            "time": current_time

        })


    # Irrigation suggestion

    if (
        weather["temperature"] != "N/A"
        and weather["humidity"] != "N/A"
        and weather["rainfall"] == 0
        and weather["humidity"] < 70
    ):

        notifications.append({

            "type": "ai",

            "title": "Irrigation Suggestion",

            "message":
                "No rainfall is currently reported and humidity "
                f'is {weather["humidity"]}%. Check soil moisture '
                "before irrigation.",

            "time": current_time

        })


    return weather, notifications
@app.route("/irrigation", methods=["GET","POST"])
def irrigation():

    if "user_id" not in session:
        return redirect("/login")


    result = None


    if request.method == "POST":

        crop = request.form["crop"]

        soil = request.form["soil"]

        rainfall = float(request.form["rainfall"])


        if rainfall > 50:

            result = {
                "status":"No Irrigation Required",
                "reason":"Sufficient rainfall available"
            }


        elif soil == "dry":

            result = {
                "status":"Irrigation Required",
                "reason":"Soil moisture is low"
            }


        else:

            result = {
                "status":"Normal Irrigation",
                "reason":"Maintain regular irrigation schedule"
            }



    return render_template(
        "irrigation.html",
        name=session["name"],
        result=result
    )



@app.route("/ask_chatbot", methods=["POST"])
def ask_chatbot():

    data = request.get_json()

    message = data.get("message", "").lower()

    if "weather" in message:
        reply = "🌦 Today's weather is suitable for farming."

    elif "crop" in message:
        reply = "🌱 Soybean and Cotton are recommended."

    elif "irrigation" in message:
        reply = "💧 Irrigate your field early in the morning."

    elif "market" in message or "price" in message:
        reply = "📈 Soybean: ₹5100/quintal"

    elif "scheme" in message:
        reply = "🏛 PM-KISAN and Crop Insurance are available."

    elif "disease" in message:
        reply = "🐛 Upload a crop image to detect diseases."

    else:
        reply = "🤖 I'm here to help! Ask me about weather, crops, irrigation, diseases, market prices, or government schemes."

    return jsonify({"reply": reply})
@app.route("/schemes")
def schemes():


    if "user_id" not in session:

        return redirect("/login")



    scheme_list=get_schemes()



    return render_template(

        "schemes.html",

        name=session["name"],

        schemes=scheme_list

    )


@app.route("/consumer")
def consumer():

    return render_template("consumer.html")
# Load model only if available

if os.path.exists("models/pest_model.keras"):

    pest_model = load_model(
        "models/pest_model.keras"
    )

else:

    pest_model=None



classes=[

"Healthy Crop",
"Leaf Disease",
"Fungal Infection",
"Pest Attack"

]





@app.route("/pest",methods=["GET","POST"])
def pest():


    if "user_id" not in session:

        return redirect("/login")



    prediction=None

    filename=None



    if request.method=="POST":


        file=request.files["crop_image"]


        if file:


            filename=file.filename


            path=os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )


            file.save(path)



            if pest_model:


                img=image.load_img(
                    path,
                    target_size=(224,224)
                )


                img=image.img_to_array(img)

                img=np.expand_dims(
                    img,
                    axis=0
                )


                result=pest_model.predict(img)


                index=np.argmax(result)


                prediction=classes[index]


            else:


                prediction="AI Model not trained yet"



    return render_template(

        "pest.html",

        name=session["name"],

        prediction=prediction,

        image=filename

    )





@app.route("/market",methods=["GET","POST"])
def market():


    if "user_id" not in session:

        return redirect("/login")



    prices=[]


    crop=None



    if request.method=="POST":


        crop=request.form["crop"]


        prices=get_market_price(crop)



    return render_template(

        "market.html",

        name=session["name"],

        prices=prices,

        crop=crop

    )
def consumer():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "Consumer":
        return redirect("/login")

    weather = get_weather_data()

    prices = get_crop_prices()

    return render_template(
        "consumer.html",
        name=session["name"],
        weather=weather,
        prices=prices
    )
@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "Admin":
        return redirect("/login")

    weather = get_weather_data()

    prices = get_crop_prices()

    return render_template(
        "admin.html",
        name=session["name"],
        weather=weather,
        prices=prices
    )
@app.route("/logout")
def logout():

    session.pop("user_id", None)
    session.pop("name", None)
    session.pop("role", None)

    session.clear()

    return redirect("/login")
    
@app.route("/weather")
def weather():

    if "user_id" not in session:
        return redirect("/login")

    weather = get_weather_data()

    return render_template(
        "weather.html",
        name=session["name"],
        weather=weather
    )

@app.route("/recommendation")
def recommendation():

    if "user_id" not in session:
        return redirect("/login")

    weather = get_weather_data()

    return render_template(
        "recommendation.html",
        name=session["name"],
        weather=weather,
        recommendation={
            "crop": "Soybean",
            "confidence": "92%",
            "reason": "Current weather conditions are suitable for soybean cultivation.",
            "fertilizer": "NPK 20:20:0",
            "irrigation": "Irrigate after 6:00 PM",
            "pest_risk": "Low"
        }
    )
@app.route("/marketplace")
def marketplace():

    conn = sqlite3.connect(
        "instance/kisanvision360.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    conn.close()


    # LIVE AGMARKNET DATA

    prices = get_market_price()


    return render_template(
        "marketplace.html",
        products=products,
        prices=prices,
        weather=None,
        notifications_count=0,
        name=session.get(
            "name",
            "Farmer"
        )
    )
@app.route("/tools")
def tools():

    if "user_id" not in session:
        return redirect("/login")


    tools=[


    {
    "name":"🚜 Mahindra Tractor 575 DI",
    "category":"Land Preparation",
    "price":"₹6.7 - ₹7.2 Lakh",
    "image":"https://www.mahindratractor.com/-/media/images/tractor.jpg",
    "buy":"https://www.mahindratractor.com",
    "rent":"Available through local dealers",
    "subsidy":"Eligible under state agriculture schemes"
    },


    {
    "name":"🌾 Combine Harvester",
    "category":"Harvesting",
    "price":"₹8 Lakh+ (Model dependent)",
    "image":"https://www.claas.com/medias/images/harvesting.jpg",
    "buy":"https://tractorkarvan.com/harvester-machine",
    "rent":"Custom Hiring Centres available",
    "subsidy":"Check state farm mechanization scheme"
    },


    {
    "name":"🔄 Fieldking Rotavator",
    "category":"Soil Preparation",
    "price":"₹1.19 Lakh approx",
    "image":"https://fieldking.com/wp-content/uploads/rotavator.jpg",
    "buy":"https://www.fieldking.com",
    "rent":"Available",
    "subsidy":"Agriculture machinery subsidy available"
    },


    {
    "name":"🌿 KisanKraft Power Weeder",
    "category":"Weeding",
    "price":"₹37,000 - ₹85,000",
    "image":"https://www.kisankraft.com/wp-content/uploads/weeder.jpg",
    "buy":"https://www.kisankraft.com",
    "rent":"Available",
    "subsidy":"Depends on government scheme"
    },


    {
    "name":"🛰 Garuda Agriculture Drone",
    "category":"Smart Farming",
    "price":"₹4.5 - ₹6.5 Lakh",
    "image":"https://www.garudaaerospace.com/images/agri-drone.jpg",
    "buy":"https://www.garudaaerospace.com",
    "rent":"Drone service providers available",
    "subsidy":"Drone subsidy available under government programs"
    }


    ]


    return render_template(
        "tools.html",
        tools=tools,
        name=session["name"]
    )
@app.route("/emi")
def emi():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "emi.html",
        name=session["name"]
    )

@app.route("/reports")
def reports():

    return render_template(
        "reports.html",
        name=session["name"]
    )



@app.route("/alerts")
def alerts():

    return render_template(
        "alerts.html",
        name=session["name"]
    )


@app.route("/help")
def help():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "help.html",
        name=session.get("name", "")
    )
@app.route("/consumer-request")
def consumer_request():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "Farmer":
        return redirect("/dashboard")

    weather = get_weather_data()

    prices = get_crop_prices()

    consumer_requests = [

        {
            "id": 1,
            "consumer": "Rahul Sharma",
            "crop": "Tomato",
            "quantity": "500 kg",
            "price": "₹28/kg",
            "location": "Nagpur",
            "status": "Pending"
        },

        {
            "id": 2,
            "consumer": "Priya Patil",
            "crop": "Onion",
            "quantity": "1 Ton",
            "price": "₹22/kg",
            "location": "Wardha",
            "status": "Accepted"
        },

        {
            "id": 3,
            "consumer": "Amit Verma",
            "crop": "Soybean",
            "quantity": "750 kg",
            "price": "₹4700/Quintal",
            "location": "Amravati",
            "status": "Pending"
        }

    ]

    return render_template(
        "consumer_request.html",
        name=session["name"],
        weather=weather,
        prices=prices,
        requests=consumer_requests
    )
@app.route("/chat")
def chat():

    if "user_id" not in session:
        return redirect("/login")

    weather = get_weather_data()

    chats = [

        {
            "sender": "Consumer",
            "message": "Hello, I need 500 kg of Soybean.",
            "time": "10:15 AM"
        },

        {
            "sender": session["name"],
            "message": "Yes, it is available.",
            "time": "10:17 AM"
        },

        {
            "sender": "Consumer",
            "message": "Can you deliver it by tomorrow?",
            "time": "10:20 AM"
        }

    ]

    return render_template(
        "chat.html",
        name=session["name"],
        weather=weather,
        chats=chats
    )
# ============================================================
# NOTIFICATION SYSTEM
# ============================================================

def get_live_notifications():

    city = "Nagpur"
    country = "IN"

    api_key = os.getenv("OPENWEATHER_API_KEY")

    notifications = []
    weather = None

    current_time = datetime.now().strftime("%I:%M %p")

    if not api_key:

        notifications.append({
            "type": "warning",
            "title": "Weather Service",
            "message": "OpenWeather API key is not configured.",
            "time": current_time
        })

        return weather, notifications


    try:

        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "q": f"{city},{country}",
            "appid": api_key,
            "units": "metric"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )


        if response.status_code != 200:

            print("Weather API Error:", response.text)

            notifications.append({
                "type": "warning",
                "title": "Weather Service Error",
                "message": "Live weather information is currently unavailable.",
                "time": current_time
            })

            return weather, notifications


        data = response.json()


        # ====================================================
        # LIVE WEATHER DATA
        # ====================================================

        temperature = data["main"]["temp"]

        feels_like = data["main"]["feels_like"]

        humidity = data["main"]["humidity"]

        wind_speed = data["wind"]["speed"]

        cloud = data["clouds"]["all"]

        condition = data["weather"][0]["main"]

        description = data["weather"][0]["description"]

        weather_city = data["name"]


        weather = {

            "city": weather_city,

            "temperature": round(
                temperature,
                1
            ),

            "feels_like": round(
                feels_like,
                1
            ),

            "humidity": humidity,

            "wind": round(
                wind_speed,
                1
            ),

            "cloud": cloud,

            "condition": condition,

            "description": description

        }


        # ====================================================
        # 1. LIVE WEATHER UPDATE
        # ====================================================

        notifications.append({

            "type": "weather",

            "title": "Live Weather Update",

            "message":
                f"{weather_city}: "
                f"{temperature:.1f}°C, "
                f"{description}, "
                f"humidity {humidity}% "
                f"and wind {wind_speed:.1f} m/s.",

            "time": current_time

        })


        # ====================================================
        # 2. RAIN ALERT
        # ====================================================

        if condition in [
            "Rain",
            "Drizzle",
            "Thunderstorm"
        ]:

            notifications.append({

                "type": "warning",

                "title": "Rain Alert",

                "message":
                    f"{description.capitalize()} is currently "
                    f"reported in {weather_city}. "
                    "Avoid unnecessary irrigation and protect "
                    "harvested crops from rain.",

                "time": current_time

            })


        # ====================================================
        # 3. HIGH HUMIDITY ALERT
        # ====================================================

        if humidity >= 80:

            notifications.append({

                "type": "warning",

                "title": "High Humidity Alert",

                "message":
                    f"Humidity is currently {humidity}%. "
                    "High humidity can increase the risk of "
                    "fungal diseases in crops.",

                "time": current_time

            })


        # ====================================================
        # 4. HIGH TEMPERATURE ALERT
        # ====================================================

        if temperature >= 35:

            notifications.append({

                "type": "warning",

                "title": "High Temperature Alert",

                "message":
                    f"Temperature is {temperature:.1f}°C. "
                    "Consider checking soil moisture and "
                    "irrigating during cooler hours.",

                "time": current_time

            })


        # ====================================================
        # 5. STRONG WIND ALERT
        # ====================================================

        if wind_speed >= 8:

            notifications.append({

                "type": "warning",

                "title": "Strong Wind Alert",

                "message":
                    f"Wind speed is {wind_speed:.1f} m/s. "
                    "Avoid spraying pesticides during strong winds.",

                "time": current_time

            })


        # ====================================================
        # 6. IRRIGATION RECOMMENDATION
        # ====================================================

        if (
            condition not in
            ["Rain", "Drizzle", "Thunderstorm"]
            and humidity < 70
        ):

            notifications.append({

                "type": "ai",

                "title": "Irrigation Suggestion",

                "message":
                    f"Humidity is {humidity}% and no rain "
                    "is currently detected. Check soil moisture "
                    "before irrigation.",

                "time": current_time

            })


        # ====================================================
        # 7. NORMAL FARM STATUS
        # ====================================================

        if (
            condition not in
            ["Rain", "Drizzle", "Thunderstorm"]
            and temperature < 35
            and humidity < 80
            and wind_speed < 8
        ):

            notifications.append({

                "type": "ai",

                "title": "Farm Weather Status",

                "message":
                    "Current weather conditions look normal. "
                    "Continue regular crop monitoring.",

                "time": current_time

            })


    except Exception as e:

        print("Notification Weather Error:", e)

        notifications.append({

            "type": "warning",

            "title": "Weather Connection Error",

            "message":
                "Unable to connect to the live weather service.",

            "time": current_time

        })


    return weather, notifications


# ============================================================
# NOTIFICATIONS PAGE
# ============================================================

@app.route("/notifications")
def notifications_page():

    name = session.get(
        "name",
        "Farmer"
    )

    weather, notifications = get_live_notifications()

    notification_count = len(
        notifications
    )


    return render_template(

        "notifications.html",

        name=name,

        weather=weather,

        notifications=notifications,

        notification_count=notification_count

    )
@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return "<script>alert('New passwords do not match');window.location='/change-password';</script>"

        cursor.execute(
            "SELECT password FROM users WHERE id=%s",
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if not user:
            return redirect("/login")

        if user[0] != current_password:
            return "<script>alert('Current password is incorrect');window.location='/change-password';</script>"

        cursor.execute(
            "UPDATE users SET password=%s WHERE id=%s",
            (new_password, session["user_id"])
        )

        db.commit()

        return "<script>alert('Password Changed Successfully');window.location='/settings';</script>"

    return render_template("change_password.html")
@app.route("/profile", methods=["GET","POST"])
def profile():

    if "user_id" not in session:
        return redirect("/login")


    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        email = request.form["email"]


        cursor.execute("""
        UPDATE users
        SET fullname=%s, mobile=%s, email=%s
        WHERE id=%s
        """,
        (
            name,
            mobile,
            email,
            session["user_id"]
        ))

        db.commit()

        return redirect("/profile")



    cursor.execute("""
    SELECT fullname,mobile,email,role,profile_pic
    FROM users
    WHERE id=%s
    """,
    (session["user_id"],))


    user = cursor.fetchone()


    weather = get_weather_data()


    return render_template(
        "profile.html",
        name=user[0],
        mobile=user[1],
        email=user[2],
        role=user[3],
        profile_pic=user[4],
        weather=weather
    )
@app.route("/upload-profile", methods=["POST"])
def upload_profile():

    if "user_id" not in session:
        return redirect("/login")


    file = request.files["profile"]


    if file:

        filename = secure_filename(file.filename)

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )


        file.save(filepath)


        db_path = "/" + filepath.replace("\\","/")


        cursor.execute("""
        UPDATE users
        SET profile_pic=%s
        WHERE id=%s
        """,
        (
            db_path,
            session["user_id"]
        ))


        db.commit()


    return redirect("/profile")

@app.route("/settings")
def settings():

    if "user_id" not in session:
        return redirect("/login")


    cursor.execute("""
        SELECT fullname,
               mobile,
               email,
               role
        FROM users
        WHERE id=%s
    """, (session["user_id"],))


    user = cursor.fetchone()


    if not user:
        session.clear()
        return redirect("/login")


    weather = get_weather_data()


    return render_template(
        "settings.html",
        name=user[0],
        mobile=user[1],
        email=user[2],
        role=user[3],
        weather=weather
    )

# =========================================================
# ADD / SELL PRODUCT
# =========================================================

@app.route("/add-product", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":

        product_name = request.form.get(
            "product_name"
        )

        category = request.form.get(
            "category"
        )

        quantity = request.form.get(
            "quantity"
        )

        unit = request.form.get(
            "unit"
        )

        price = request.form.get(
            "price"
        )

        description = request.form.get(
            "description"
        )

        image = request.files.get(
            "image"
        )


        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------

        if not product_name:
            return render_template(
                "add_product.html",
                error="Please enter product name."
            )


        if not category:
            return render_template(
                "add_product.html",
                error="Please select category."
            )


        if not quantity:
            return render_template(
                "add_product.html",
                error="Please enter quantity."
            )


        if not price:
            return render_template(
                "add_product.html",
                error="Please enter price."
            )


        # ---------------------------------------------
        # SAVE IMAGE
        # ---------------------------------------------

        image_name = ""


        if image and image.filename:

            image_name = secure_filename(
                image.filename
            )


            product_upload_folder = os.path.join(
                app.static_folder,
                "uploads",
                "products"
            )


            os.makedirs(
                product_upload_folder,
                exist_ok=True
            )


            image_path = os.path.join(
                product_upload_folder,
                image_name
            )


            image.save(
                image_path
            )


        # ---------------------------------------------
        # SAVE PRODUCT TO DATABASE
        # ---------------------------------------------

        conn = sqlite3.connect(
            "instance/kisanvision360.db"
        )

        cursor = conn.cursor()


        cursor.execute("""
            INSERT INTO products
            (
                product_name,
                category,
                quantity,
                unit,
                price,
                description,
                image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            product_name,

            category,

            quantity,

            unit,

            price,

            description,

            image_name

        ))


        conn.commit()

        conn.close()


        return redirect(
            url_for("marketplace")
        )


    return render_template(
        "add_product.html"
    )
if __name__ == "__main__":
    app.run(debug=True)
