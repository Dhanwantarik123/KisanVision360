import os
import requests
import numpy as np

from flask import Flask, render_template, request, redirect, session, jsonify

from db import db, cursor
from utils.crop_price import get_crop_prices
from utils.mandi_price import get_market_price
from utils.schemes import get_schemes

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from flask import url_for
from werkzeug.utils import secure_filename
import os
app = Flask(__name__)

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


@app.route("/disease")
def disease():
    return render_template("disease.html")


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

    if session.get("role","").lower() != "farmer":
        return redirect("/dashboard")

    user_id = session["user_id"]

    # Total Income
    cursor.execute("""
        SELECT IFNULL(SUM(amount),0)
        FROM transactions
        WHERE farmer_id=%s
        AND type='Income'
    """,(user_id,))

    income = cursor.fetchone()[0]

    # Total Expense
    cursor.execute("""
        SELECT IFNULL(SUM(amount),0)
        FROM transactions
        WHERE farmer_id=%s
        AND type='Expense'
    """,(user_id,))

    expenses = cursor.fetchone()[0]

    profit = income - expenses

    # Recent Transactions
    cursor.execute("""
        SELECT description,
               amount,
               type
        FROM transactions
        WHERE farmer_id=%s
        ORDER BY id DESC
        LIMIT 10
    """,(user_id,))

    transactions = cursor.fetchall()

    return render_template(

        "finance.html",

        name=session["name"],

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
@app.route("/expense", methods=["GET","POST"])
def expense():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    if request.method == "POST":

        description = request.form["description"]
        amount = request.form["amount"]

        cursor.execute("""
            INSERT INTO transactions
            (farmer_id,description,amount,type)
            VALUES(%s,%s,%s,'Expense')
        """,(user_id,description,amount))

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
    """,(user_id,))

    expense_list = cursor.fetchall()

    return render_template(
        "expense.html",
        name=session["name"],
        expense_list=expense_list
    )

@app.route("/predict_disease", methods=["POST"])
def predict_disease():

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

    upload_folder = app.config["UPLOAD_FOLDER"]

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    image_name = file.filename

    upload_path = os.path.join(
        upload_folder,
        image_name
    )

    file.save(upload_path)

    try:

        # Load image
        image = Image.open(upload_path).convert("RGB")

        # Resize according to model input
        image = image.resize((224, 224))

        # Convert image to array
        image_array = np.array(image)

        # Normalize
        image_array = image_array / 255.0

        # Add batch dimension
        image_array = np.expand_dims(
            image_array,
            axis=0
        )

        # Prediction
        prediction = disease_model.predict(
            image_array,
            verbose=0
        )

        # Get highest probability
        predicted_index = np.argmax(prediction[0])

        confidence = float(
            prediction[0][predicted_index]
        ) * 100

        disease_name = DISEASE_CLASSES[
            predicted_index
        ]

        # Disease information
        disease_info = {

            "Healthy": {
                "status": "No Disease Detected",
                "symptoms": "Leaves appear healthy with normal green color.",
                "treatment": "No treatment required.",
                "prevention": "Maintain proper irrigation, nutrition and regular crop monitoring."
            },

            "Early Blight": {
                "status": "Disease Detected",
                "symptoms": "Brown spots appear on leaves and yellowing occurs.",
                "treatment": "Spray Mancozeb every 7 days as recommended for the crop.",
                "prevention": "Avoid overwatering and remove infected leaves."
            },

            "Late Blight": {
                "status": "Disease Detected",
                "symptoms": "Dark brown or black patches appear on leaves and stems.",
                "treatment": "Use an appropriate fungicide recommended for late blight.",
                "prevention": "Avoid excess moisture and improve air circulation."
            },

            "Leaf Spot": {
                "status": "Disease Detected",
                "symptoms": "Small brown or dark spots appear on the leaves.",
                "treatment": "Remove affected leaves and apply a suitable fungicide.",
                "prevention": "Avoid overhead watering and maintain proper spacing."
            }
        }

        info = disease_info.get(
            disease_name,
            {
                "status": "Disease Detected",
                "symptoms": "Symptoms information is not available.",
                "treatment": "Consult an agricultural expert.",
                "prevention": "Monitor the crop regularly."
            }
        )

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

    except Exception as e:

        return render_template(
            "disease.html",
            error="Unable to process image: " + str(e)
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


from flask import request, jsonify

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

    if "user_id" not in session:
        return redirect("/login")


    prices = get_crop_prices()


    cursor.execute("""
        SELECT *
        FROM marketplace_products
        ORDER BY id DESC
    """)


    products = cursor.fetchall()


    weather = get_weather_data()



    return render_template(
        "marketplace.html",
        name=session["name"],
        prices=prices,
        products=products,
        weather=weather
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
@app.route("/notifications")
def notifications():

    if "user_id" not in session:
        return redirect("/login")

    weather = get_weather_data()

    notifications = [

        {
            "title": "🌧 Heavy Rain Alert",
            "message": "Heavy rainfall expected within the next 24 hours. Delay irrigation.",
            "time": "10 Minutes Ago",
            "type": "warning"
        },

        {
            "title": "🌾 Crop Price Updated",
            "message": "Soybean price increased by ₹150 per Quintal today.",
            "time": "30 Minutes Ago",
            "type": "market"
        },

        {
            "title": "🤖 AI Recommendation",
            "message": "Weather is suitable for fertilizer application after 6 PM.",
            "time": "1 Hour Ago",
            "type": "ai"
        },

        {
            "title": "💬 New Consumer Message",
            "message": "A consumer is interested in purchasing your crop.",
            "time": "2 Hours Ago",
            "type": "chat"
        }

    ]

    return render_template(
        "notifications.html",
        name=session["name"],
        weather=weather,
        notifications=notifications
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
    

if __name__ == "__main__":
    app.run(debug=True)
