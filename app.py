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

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image

from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

from utils.crop_price import get_crop_prices
from utils.mandi_price import get_market_price
from utils.schemes import get_schemes
from db import get_db

# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "kisanvision360_secret_key"
)

serializer = URLSafeTimedSerializer(
    app.secret_key
)


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = app.root_path

DATABASE = os.path.join(
    BASE_DIR,
    "instance",
    "kisanvision360.db"
)

os.makedirs(
    os.path.dirname(DATABASE),
    exist_ok=True
)


def get_db():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# MAIL
# =========================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True

app.config["MAIL_USERNAME"] = os.getenv(
    "MAIL_USERNAME",
    "yourgmail@gmail.com"
)

app.config["MAIL_PASSWORD"] = os.getenv(
    "MAIL_PASSWORD",
    "your-app-password"
)

mail = Mail(app)


# =========================================================
# UPLOAD
# =========================================================

app.config["UPLOAD_FOLDER"] = os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)

PRODUCT_UPLOAD_FOLDER = os.path.join(
    app.config["UPLOAD_FOLDER"],
    "products"
)

os.makedirs(
    PRODUCT_UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# CONFIG
# =========================================================

CITY = "Nagpur"

WEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY",
    "a03114f8eb4b0276cd6efa27c6f4613d"
)

# =========================================================
# KAGGLE DISEASE MODEL
# =========================================================

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ai_models",
    "disease_model.keras"
)

CLASS_FILE = os.path.join(
    BASE_DIR,
    "ai_models",
    "disease_classes.txt"
)

disease_model = None
DISEASE_CLASSES = []


# =========================================================
# LOAD KAGGLE DISEASE MODEL
# =========================================================

try:

    print("\n" + "=" * 60)
    print("KAGGLE DISEASE MODEL")
    print("=" * 60)

    if os.path.exists(MODEL_PATH):

        disease_model = tf.keras.models.load_model(
            MODEL_PATH,
            compile=False
        )

        print("MODEL LOADED SUCCESSFULLY")
        print("Model path:", MODEL_PATH)

        try:
            print(
                "Input shape:",
                disease_model.input_shape
            )

            print(
                "Output shape:",
                disease_model.output_shape
            )

        except Exception:
            pass

    else:

        print("WARNING: Disease model not found")
        print("Expected:")
        print(MODEL_PATH)

except Exception as e:

    disease_model = None

    print("DISEASE MODEL ERROR:")
    print(repr(e))


# =========================================================
# LOAD DISEASE CLASS NAMES
# =========================================================

try:

    print("\n" + "=" * 60)
    print("DISEASE CLASS FILE")
    print("=" * 60)

    if os.path.exists(CLASS_FILE):

        with open(
            CLASS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            DISEASE_CLASSES = [
                line.strip()
                for line in f
                if line.strip()
            ]

        print(
            "Total classes:",
            len(DISEASE_CLASSES)
        )

        for i, disease_class in enumerate(
            DISEASE_CLASSES
        ):

            print(
                f"{i} = {disease_class}"
            )

    else:

        print(
            "WARNING: disease_classes.txt not found"
        )

except Exception as e:

    DISEASE_CLASSES = []

    print(
        "CLASS FILE ERROR:",
        repr(e)
    )


# =========================================================
# VALIDATE MODEL AND CLASS FILE
# =========================================================

def validate_disease_model():

    if disease_model is None:

        return False, "Disease model is not loaded."

    if not DISEASE_CLASSES:

        return False, "Disease class file is empty or missing."

    try:

        model_classes = int(
            disease_model.output_shape[-1]
        )

        class_count = len(
            DISEASE_CLASSES
        )

        print("\n" + "=" * 60)
        print("DISEASE MODEL VALIDATION")
        print("=" * 60)

        print(
            "Model output classes:",
            model_classes
        )

        print(
            "Class file classes:",
            class_count
        )

        if model_classes != class_count:

            print(
                "WARNING: CLASS COUNT DOES NOT MATCH"
            )

            return (
                False,
                "Model classes and class file classes do not match."
            )

        print(
            "MODEL AND CLASS FILE MATCHED"
        )

        return True, "OK"

    except Exception as e:

        print(
            "VALIDATION ERROR:",
            repr(e)
        )

        return False, str(e)


# Run validation when application starts

validate_disease_model()


# =========================================================
# FORMAT DISEASE NAME
# =========================================================

def format_disease_name(name):

    if not name:

        return "Unknown Disease"

    name = str(name)

    name = name.replace(
        "___",
        " - "
    )

    name = name.replace(
        "__",
        " - "
    )

    name = name.replace(
        "_",
        " "
    )

    while "  " in name:

        name = name.replace(
            "  ",
            " "
        )

    return name.strip()


# =========================================================
# HEALTHY CLASS DETECTION
# =========================================================

def is_healthy_disease(name):

    if not name:

        return False

    name_lower = str(
        name
    ).lower().strip()

    healthy_keywords = [

        "healthy",
        "normal",
        "no disease"

    ]

    return any(
        keyword in name_lower
        for keyword in healthy_keywords
    )


# =========================================================
# GET DISEASE INFORMATION
# =========================================================

def get_disease_information(
    disease_name
):

    if not disease_name:

        return {

            "status":
                "Unknown",

            "symptoms":
                "Unable to identify the disease.",

            "treatment":
                "Please upload a clear plant leaf image.",

            "prevention":
                "Use a clear image and maintain regular crop monitoring."

        }

    # -----------------------------------------------------
    # EXACT MATCH
    # -----------------------------------------------------

    if disease_name in DISEASE_INFO:

        return DISEASE_INFO[
            disease_name
        ]

    # -----------------------------------------------------
    # FORMATTED MATCH
    # -----------------------------------------------------

    formatted_name = format_disease_name(
        disease_name
    )

    if formatted_name in DISEASE_INFO:

        return DISEASE_INFO[
            formatted_name
        ]

    # -----------------------------------------------------
    # HEALTHY
    # -----------------------------------------------------

    if is_healthy_disease(
        disease_name
    ):

        return {

            "status":
                "Healthy",

            "symptoms":
                "No major disease symptoms detected.",

            "treatment":
                "No disease treatment is required.",

            "prevention":
                "Continue regular monitoring, proper irrigation and balanced nutrition."

        }

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    return {

        "status":
            "Disease Detected",

        "symptoms":
            "Disease symptoms depend on the identified crop condition.",

        "treatment":
            "Follow crop-specific disease management recommendations and consult an agricultural expert if required.",

        "prevention":
            "Maintain field hygiene, proper irrigation, balanced nutrition and regular crop monitoring."

    }


# =========================================================
# DISEASE PAGE
# =========================================================

@app.route(
    "/disease"
)
def disease():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(

        "disease.html",

        name=session.get(
            "name",
            "Farmer"
        ),

        prediction=None,

        confidence=None,

        image=None,

        status=None,

        symptoms=None,

        treatment=None,

        prevention=None,

        error=None
    )


# =========================================================
# KAGGLE DISEASE PREDICTION
# =========================================================

@app.route(
    "/predict_disease",
    methods=["POST"]
)
def predict_disease():

    # -----------------------------------------------------
    # LOGIN CHECK
    # -----------------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    # -----------------------------------------------------
    # GET UPLOADED IMAGE
    # -----------------------------------------------------

    uploaded_file = request.files.get(
        "image"
    )

    if (
        uploaded_file is None
        or not uploaded_file.filename
    ):

        return render_template(

            "disease.html",

            name=session.get(
                "name",
                "Farmer"
            ),

            prediction=None,
            confidence=None,
            image=None,
            status=None,
            symptoms=None,
            treatment=None,
            prevention=None,

            error="Please select a plant leaf image."

        )

    # -----------------------------------------------------
    # MODEL CHECK
    # -----------------------------------------------------

    if disease_model is None:

        return render_template(

            "disease.html",

            name=session.get(
                "name",
                "Farmer"
            ),

            prediction=None,
            confidence=None,
            image=None,
            status=None,
            symptoms=None,
            treatment=None,
            prevention=None,

            error=(
                "Kaggle disease model is not loaded. "
                "Please check ai_models/disease_model.keras."
            )

        )

    # -----------------------------------------------------
    # CLASS CHECK
    # -----------------------------------------------------

    if not DISEASE_CLASSES:

        return render_template(

            "disease.html",

            name=session.get(
                "name",
                "Farmer"
            ),

            prediction=None,
            confidence=None,
            image=None,
            status=None,
            symptoms=None,
            treatment=None,
            prevention=None,

            error=(
                "Disease class file is missing. "
                "Please check ai_models/disease_classes.txt."
            )

        )

    # -----------------------------------------------------
    # VALIDATE MODEL
    # -----------------------------------------------------

    model_valid, validation_message = (
        validate_disease_model()
    )

    if not model_valid:

        return render_template(

            "disease.html",

            name=session.get(
                "name",
                "Farmer"
            ),

            prediction=None,
            confidence=None,
            image=None,
            status=None,
            symptoms=None,
            treatment=None,
            prevention=None,

            error=validation_message

        )

    # -----------------------------------------------------
    # SAFE FILE NAME
    # -----------------------------------------------------

    filename = secure_filename(
        uploaded_file.filename
    )

    if not filename:

        filename = "plant_leaf.jpg"

    # -----------------------------------------------------
    # CREATE UNIQUE FILE NAME
    # -----------------------------------------------------

    import uuid

    unique_filename = (
        str(uuid.uuid4())
        + "_"
        + filename
    )

    filepath = os.path.join(

        app.config[
            "UPLOAD_FOLDER"
        ],

        unique_filename
    )

    try:

        # =================================================
        # SAVE IMAGE
        # =================================================

        uploaded_file.save(
            filepath
        )

        # =================================================
        # OPEN IMAGE
        # =================================================

        img = Image.open(
            filepath
        ).convert(
            "RGB"
        )

        # =================================================
        # GET MODEL INPUT SIZE
        # =================================================

        try:

            input_shape = (
                disease_model.input_shape
            )

            input_height = int(
                input_shape[1]
            )

            input_width = int(
                input_shape[2]
            )

        except Exception:

            input_height = 224
            input_width = 224

        # =================================================
        # RESIZE IMAGE
        # =================================================

        img = img.resize(

            (
                input_width,
                input_height
            )

        )

        # =================================================
        # IMAGE → NUMPY
        # =================================================

        img_array = np.array(

            img,

            dtype=np.float32

        )

        # =================================================
        # IMPORTANT
        # =================================================
        # DO NOT DIVIDE BY 255
        #
        # Your Kaggle model already contains
        # image rescaling/preprocessing.
        # =================================================

        # =================================================
        # ADD BATCH DIMENSION
        # =================================================

        img_array = np.expand_dims(

            img_array,

            axis=0

        )

        # =================================================
        # MODEL PREDICTION
        # =================================================

        result = disease_model.predict(

            img_array,

            verbose=0

        )

        # =================================================
        # GET PROBABILITIES
        # =================================================

        probabilities = np.asarray(
            result[0]
        )

        # =================================================
        # PREDICTED CLASS
        # =================================================

        predicted_index = int(

            np.argmax(
                probabilities
            )

        )

        # =================================================
        # CONFIDENCE
        # =================================================

        confidence = float(

            probabilities[
                predicted_index
            ] * 100

        )

        # =================================================
        # CLASS NAME
        # =================================================

        if (
            predicted_index
            < len(DISEASE_CLASSES)
        ):

            raw_disease_name = (
                DISEASE_CLASSES[
                    predicted_index
                ]
            )

        else:

            raw_disease_name = (
                "Unknown Disease"
            )

        # =================================================
        # DISPLAY NAME
        # =================================================

        disease_name = (
            format_disease_name(
                raw_disease_name
            )
        )

        # =================================================
        # GET INFORMATION
        # =================================================

        info = get_disease_information(
            raw_disease_name
        )

        # =================================================
        # STATUS
        # =================================================

        if is_healthy_disease(
            raw_disease_name
        ):

            status = "Healthy"

        else:

            status = info.get(
                "status",
                "Disease Detected"
            )

        # =================================================
        # PRINT RESULT
        # =================================================

        print("\n" + "=" * 60)
        print("KAGGLE DISEASE PREDICTION")
        print("=" * 60)

        print(
            "Image:",
            unique_filename
        )

        print(
            "Class Index:",
            predicted_index
        )

        print(
            "Raw Class:",
            raw_disease_name
        )

        print(
            "Display Name:",
            disease_name
        )

        print(
            "Confidence:",
            round(
                confidence,
                2
            ),
            "%"
        )

        print(
            "Status:",
            status
        )

        print("=" * 60)

        # =================================================
        # RETURN RESULT
        # =================================================

        return render_template(

            "disease.html",

            name=session.get(
                "name",
                "Farmer"
            ),

            image=unique_filename,

            prediction=disease_name,

            confidence=round(
                confidence,
                2
            ),

            status=status,

            symptoms=info.get(
                "symptoms"
            ),

            treatment=info.get(
                "treatment"
            ),

            prevention=info.get(
                "prevention"
            ),

            error=None

        )

    # =====================================================
    # ERROR
    # =====================================================

    except Exception as e:

        print("\n" + "=" * 60)

        print(
            "KAGGLE DISEASE PREDICTION ERROR"
        )

        print(
            repr(e)
        )

        print("=" * 60)

        return render_template(

            "disease.html",

            name=session.get(
                "name",
                "Farmer"
            ),

            image=None,

            prediction=None,

            confidence=None,

            status=None,

            symptoms=None,

            treatment=None,

            prevention=None,

            error=(
                "Unable to process image. "
                "Please upload a valid plant leaf image."
            )

        )


# =========================================================
# DISEASE MODEL INFORMATION
# =========================================================

@app.route(
    "/disease_model_info"
)
def disease_model_info():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    model_classes = 0
    input_shape = None

    # -----------------------------------------------------
    # MODEL INFORMATION
    # -----------------------------------------------------

    if disease_model is not None:

        try:

            model_classes = int(
                disease_model.output_shape[-1]
            )

        except Exception:

            model_classes = 0

        try:

            input_shape = (
                disease_model.input_shape
            )

        except Exception:

            input_shape = None

    # -----------------------------------------------------
    # MATCH
    # -----------------------------------------------------

    class_match = (

        model_classes
        == len(DISEASE_CLASSES)

        and model_classes > 0

    )

    # -----------------------------------------------------
    # JSON RESPONSE
    # -----------------------------------------------------

    return jsonify({

        "model_loaded":
            disease_model is not None,

        "model_path":
            MODEL_PATH,

        "class_file":
            CLASS_FILE,

        "input_shape":
            input_shape,

        "model_output_classes":
            model_classes,

        "class_file_classes":
            len(
                DISEASE_CLASSES
            ),

        "classes":
            DISEASE_CLASSES,

        "match":
            class_match

    })
# =========================================================
# DISEASE INFORMATION
# Matches Kaggle Plants Disease Dataset + Cotton Dataset
# =========================================================

DISEASE_INFO = {

    # =====================================================
    # APPLE
    # =====================================================

    "Apple___Apple_scab": {
        "status": "Disease Detected",
        "symptoms": "Olive or dark spots may appear on apple leaves and fruit.",
        "treatment": "Remove infected leaves and follow crop-specific fungicide recommendations.",
        "prevention": "Maintain good orchard sanitation and proper air circulation."
    },

    "Apple___Black_rot": {
        "status": "Disease Detected",
        "symptoms": "Dark brown or black spots can develop on leaves and fruit.",
        "treatment": "Remove infected plant material and use suitable disease management practices.",
        "prevention": "Remove dead wood and maintain good orchard sanitation."
    },

    "Apple___Cedar_apple_rust": {
        "status": "Disease Detected",
        "symptoms": "Yellow-orange spots may appear on apple leaves.",
        "treatment": "Use an appropriate fungicide according to crop recommendations.",
        "prevention": "Remove infected plant material and maintain orchard hygiene."
    },

    "Apple___healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Continue regular monitoring, proper irrigation and balanced nutrition."
    },


    # =====================================================
    # CHERRY
    # =====================================================

    "Cherry_(including_sour)___Powdery_mildew": {
        "status": "Disease Detected",
        "symptoms": "White powder-like growth may appear on leaves.",
        "treatment": "Use a suitable crop-specific fungicide according to the product label.",
        "prevention": "Improve air circulation and avoid excessive humidity."
    },

    "Cherry_(including_sour)___healthy": {
        "status": "Healthy",
        "symptoms": "Leaves appear healthy without major disease symptoms.",
        "treatment": "No disease treatment is required.",
        "prevention": "Maintain proper irrigation, nutrition and regular crop monitoring."
    },


    # =====================================================
    # CORN
    # =====================================================

    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
        "status": "Disease Detected",
        "symptoms": "Gray or brown rectangular lesions may develop on corn leaves.",
        "treatment": "Remove severely affected material and follow crop-specific fungicide recommendations.",
        "prevention": "Use resistant varieties and maintain proper crop rotation."
    },

    "Corn_(maize)___Common_rust_": {
        "status": "Disease Detected",
        "symptoms": "Small reddish-brown rust pustules may appear on leaves.",
        "treatment": "Use suitable fungicide when recommended for the crop.",
        "prevention": "Use resistant varieties and maintain proper field management."
    },

    "Corn_(maize)___Northern_Leaf_Blight": {
        "status": "Disease Detected",
        "symptoms": "Long gray-green or brown lesions may appear on leaves.",
        "treatment": "Follow crop-specific fungicide recommendations.",
        "prevention": "Use resistant varieties and practice crop rotation."
    },

    "Corn_(maize)___healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Maintain proper irrigation, nutrition and regular monitoring."
    },


    # =====================================================
    # GRAPE
    # =====================================================

    "Grape___Black_rot": {
        "status": "Disease Detected",
        "symptoms": "Brown or black lesions may appear on leaves and fruit.",
        "treatment": "Remove infected material and use suitable fungicide recommendations.",
        "prevention": "Maintain vineyard sanitation and good air circulation."
    },

    "Grape___Esca_(Black_Measles)": {
        "status": "Disease Detected",
        "symptoms": "Leaf discoloration and dark spotting may occur.",
        "treatment": "Remove severely affected plant material and consult an agricultural expert.",
        "prevention": "Use healthy planting material and maintain vineyard sanitation."
    },

    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {
        "status": "Disease Detected",
        "symptoms": "Dark spots and blight-like symptoms may develop on leaves.",
        "treatment": "Remove affected leaves and follow crop-specific disease management.",
        "prevention": "Improve air circulation and avoid prolonged leaf wetness."
    },

    "Grape___healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Continue regular vineyard monitoring and proper irrigation."
    },


    # =====================================================
    # ORANGE
    # =====================================================

    "Orange__Healthy_Leaf": {
        "status": "Healthy",
        "symptoms": "Leaf appears healthy without visible disease symptoms.",
        "treatment": "No disease treatment is required.",
        "prevention": "Maintain proper irrigation, nutrition and pest monitoring."
    },

    "Orange___Haunglongbing_(Citrus_greening)": {
        "status": "Disease Detected",
        "symptoms": "Leaves may show uneven yellowing and trees may show reduced growth.",
        "treatment": "Remove severely affected trees where recommended and manage insect vectors.",
        "prevention": "Use healthy planting material and control vector insects."
    },


    # =====================================================
    # PEACH
    # =====================================================

    "Peach___Bacterial_spot": {
        "status": "Disease Detected",
        "symptoms": "Small dark or water-soaked spots may appear on leaves and fruit.",
        "treatment": "Remove severely affected material and follow crop-specific recommendations.",
        "prevention": "Use healthy planting material and avoid unnecessary leaf wetness."
    },

    "Peach___healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Maintain proper irrigation, nutrition and crop monitoring."
    },


    # =====================================================
    # PEPPER
    # =====================================================

    "Pepper,_bell___Bacterial_spot": {
        "status": "Disease Detected",
        "symptoms": "Small dark spots may appear on leaves and fruits.",
        "treatment": "Remove affected plant material and follow crop-specific recommendations.",
        "prevention": "Use healthy seeds and avoid overhead irrigation."
    },

    "Pepper,_bell___healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Maintain proper irrigation and regular crop monitoring."
    },


    # =====================================================
    # POTATO
    # =====================================================

    "Potato___Early_blight": {
        "status": "Disease Detected",
        "symptoms": "Dark circular spots with concentric rings may appear on leaves.",
        "treatment": "Remove affected leaves and use suitable fungicide according to crop recommendations.",
        "prevention": "Maintain field sanitation and avoid prolonged leaf wetness."
    },

    "Potato___Late_blight": {
        "status": "Disease Detected",
        "symptoms": "Dark water-soaked lesions may rapidly develop on leaves.",
        "treatment": "Use appropriate crop-specific fungicide and remove severely infected material.",
        "prevention": "Avoid excessive moisture and maintain good field sanitation."
    },

    "Potato___healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Use healthy seed material and maintain proper irrigation."
    },


    # =====================================================
    # RICE
    # =====================================================

    "Rice__brown_spot": {
        "status": "Disease Detected",
        "symptoms": "Brown circular or oval spots may appear on rice leaves.",
        "treatment": "Maintain balanced crop nutrition and follow suitable crop-specific treatment.",
        "prevention": "Use healthy seed and maintain proper field management."
    },

    "Rice__healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Maintain proper irrigation, nutrition and regular monitoring."
    },

    "Rice__hispa": {
        "status": "Pest Detected",
        "symptoms": "Leaves may show scraping, white streaks or damaged leaf surfaces.",
        "treatment": "Follow recommended pest-management practices for rice hispa.",
        "prevention": "Monitor fields regularly and maintain proper crop management."
    },

    "Rice__leaf_blast": {
        "status": "Disease Detected",
        "symptoms": "Spindle-shaped gray or brown lesions may appear on leaves.",
        "treatment": "Follow crop-specific fungicide and field-management recommendations.",
        "prevention": "Use resistant varieties and avoid excessive nitrogen."
    },

    "Rice__neck_blast": {
        "status": "Disease Detected",
        "symptoms": "Dark lesions may develop around the neck of the rice panicle.",
        "treatment": "Use appropriate crop-specific disease management.",
        "prevention": "Use resistant varieties and maintain balanced crop nutrition."
    },


    # =====================================================
    # SOYBEAN
    # =====================================================

    "Soybean___healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Maintain proper irrigation, nutrition and crop monitoring."
    },

    "Soybean__bacterial_blight": {
        "status": "Disease Detected",
        "symptoms": "Water-soaked or brown lesions may appear on soybean leaves.",
        "treatment": "Remove affected material and follow crop-specific recommendations.",
        "prevention": "Use healthy seed and avoid unnecessary leaf wetness."
    },

    "Soybean__caterpillar": {
        "status": "Pest Detected",
        "symptoms": "Leaves may show chewing damage or missing leaf tissue.",
        "treatment": "Follow recommended integrated pest-management practices.",
        "prevention": "Regularly monitor leaves for caterpillar activity."
    },

    "Soybean__diabrotica_speciosa": {
        "status": "Pest Detected",
        "symptoms": "Leaf feeding damage may appear as holes or damaged leaf tissue.",
        "treatment": "Use recommended pest-management practices.",
        "prevention": "Regular field scouting and proper pest monitoring."
    },

    "Soybean__downy_mildew": {
        "status": "Disease Detected",
        "symptoms": "Pale yellow areas and downy growth may appear on leaves.",
        "treatment": "Use suitable crop-specific disease management.",
        "prevention": "Improve field ventilation and avoid excessive moisture."
    },

    "Soybean__mosaic_virus": {
        "status": "Disease Detected",
        "symptoms": "Mosaic-like light and dark green patterns may appear on leaves.",
        "treatment": "Remove severely infected plants and manage disease vectors.",
        "prevention": "Use healthy planting material and monitor insect vectors."
    },

    "Soybean__powdery_mildew": {
        "status": "Disease Detected",
        "symptoms": "White powder-like growth may appear on leaf surfaces.",
        "treatment": "Use suitable crop-specific fungicide according to the product label.",
        "prevention": "Improve air circulation and avoid excessive humidity."
    },

    "Soybean__rust": {
        "status": "Disease Detected",
        "symptoms": "Small reddish-brown rust-like spots may appear on leaves.",
        "treatment": "Use suitable crop-specific fungicide according to recommendations.",
        "prevention": "Monitor crops regularly and maintain good field sanitation."
    },

    "Soybean__southern_blight": {
        "status": "Disease Detected",
        "symptoms": "Wilting and brown lesions may develop near the plant base.",
        "treatment": "Remove affected plants and follow crop-specific management practices.",
        "prevention": "Maintain good drainage and avoid excessive soil moisture."
    },


    # =====================================================
    # STRAWBERRY
    # =====================================================

    "Strawberry___Leaf_scorch": {
        "status": "Disease Detected",
        "symptoms": "Dark purple or brown spots may develop on strawberry leaves.",
        "treatment": "Remove affected leaves and follow suitable crop-specific disease management.",
        "prevention": "Maintain good field sanitation and proper spacing."
    },

    "Strawberry___healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Maintain proper irrigation, nutrition and regular monitoring."
    },


    # =====================================================
    # TOMATO
    # =====================================================

    "Tomato___Bacterial_spot": {
        "status": "Disease Detected",
        "symptoms": "Small dark spots may appear on tomato leaves and fruits.",
        "treatment": "Remove affected material and follow crop-specific recommendations.",
        "prevention": "Avoid overhead watering and use healthy planting material."
    },

    "Tomato___Early_blight": {
        "status": "Disease Detected",
        "symptoms": "Dark spots with concentric rings may appear on older leaves.",
        "treatment": "Remove affected leaves and use suitable fungicide according to recommendations.",
        "prevention": "Maintain field sanitation and avoid prolonged leaf wetness."
    },

    "Tomato___Late_blight": {
        "status": "Disease Detected",
        "symptoms": "Dark water-soaked lesions may rapidly develop on leaves.",
        "treatment": "Use suitable crop-specific disease management and remove severely affected material.",
        "prevention": "Avoid excessive moisture and maintain good air circulation."
    },

    "Tomato___Leaf_Mold": {
        "status": "Disease Detected",
        "symptoms": "Yellow patches may appear on the upper leaf surface with mold underneath.",
        "treatment": "Improve ventilation and follow suitable fungicide recommendations.",
        "prevention": "Reduce humidity and improve air circulation."
    },

    "Tomato___Septoria_leaf_spot": {
        "status": "Disease Detected",
        "symptoms": "Small circular spots with dark borders may appear on leaves.",
        "treatment": "Remove affected leaves and follow crop-specific recommendations.",
        "prevention": "Avoid overhead watering and maintain field sanitation."
    },

    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "status": "Pest Detected",
        "symptoms": "Fine webbing and small yellow or pale spots may appear on leaves.",
        "treatment": "Use integrated pest-management practices and suitable crop-approved controls.",
        "prevention": "Monitor leaves regularly and maintain proper crop health."
    },

    "Tomato___Target_Spot": {
        "status": "Disease Detected",
        "symptoms": "Circular brown lesions may appear on tomato leaves and fruit.",
        "treatment": "Remove affected material and use suitable crop-specific fungicide.",
        "prevention": "Improve air circulation and avoid prolonged leaf wetness."
    },

    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "status": "Disease Detected",
        "symptoms": "Leaves may curl upward and show yellowing with reduced plant growth.",
        "treatment": "Remove severely infected plants and manage whitefly vectors.",
        "prevention": "Use healthy planting material and monitor whitefly populations."
    },

    "Tomato___Tomato_mosaic_virus": {
        "status": "Disease Detected",
        "symptoms": "Light and dark green mosaic patterns may appear on leaves.",
        "treatment": "Remove severely infected plants and maintain good field sanitation.",
        "prevention": "Use healthy planting material and sanitize tools."
    },

    "Tomato___healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Continue proper irrigation, nutrition and regular crop monitoring."
    },


    # =====================================================
    # COTTON DATASET
    # =====================================================

    "bacterial_blight": {
        "status": "Disease Detected",
        "symptoms": "Water-soaked or dark lesions may appear on cotton leaves.",
        "treatment": "Remove affected plant material and follow crop-specific recommendations.",
        "prevention": "Use healthy seed and avoid unnecessary leaf wetness."
    },

    "curl_virus": {
        "status": "Disease Detected",
        "symptoms": "Cotton leaves may curl, become distorted and show reduced growth.",
        "treatment": "Remove severely affected plants and manage insect vectors.",
        "prevention": "Use healthy planting material and monitor vector insects."
    },

    "fussarium_wilt": {
        "status": "Disease Detected",
        "symptoms": "Leaves may wilt, yellow and show reduced plant growth.",
        "treatment": "Remove severely affected plants and follow crop-specific management practices.",
        "prevention": "Use resistant varieties and maintain good field sanitation."
    },

    "healthy": {
        "status": "Healthy",
        "symptoms": "No major disease symptoms detected.",
        "treatment": "No disease treatment is required.",
        "prevention": "Maintain proper irrigation, nutrition and regular crop monitoring."
    }
}
# =========================================================
# WEATHER
# =========================================================

def get_weather_data():

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
    )

    params = {
        "q": CITY,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return {
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
            "visibility": data.get(
                "visibility",
                0
            ) / 1000,
            "clouds": data["clouds"]["all"],
            "sunrise": data["sys"]["sunrise"],
            "sunset": data["sys"]["sunset"],
            "rainfall": data.get(
                "rain",
                {}
            ).get(
                "1h",
                0
            )
        }

    except Exception as e:

        print(
            "WEATHER ERROR:",
            e
        )

        return {
            "city": CITY,
            "country": "IN",
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


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return redirect(
        url_for("language")
    )


# =========================================================
# LANGUAGE
# =========================================================

@app.route("/language")
def language():

    return render_template(
        "language.html",
        language=session.get(
            "language",
            "en"
        )
    )


@app.route(
    "/set-language",
    methods=["POST"]
)
def set_language():

    language_code = request.form.get(
        "language",
        "en"
    ).strip()

    allowed_languages = [
        "en",
        "hi",
        "mr",
        "kn",
        "te",
        "ta",
        "ml",
        "gu",
        "pa",
        "bn"
    ]

    if language_code not in allowed_languages:

        language_code = "en"

    session["language"] = language_code

    return redirect(
        url_for("login")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if "user_id" in session:

        role = str(
            session.get(
                "role",
                ""
            )
        ).lower()

        if role == "farmer":
            return redirect(
                url_for("farmer")
            )

        if role == "consumer":
            return redirect(
                url_for("consumer")
            )

        if role == "admin":
            return redirect(
                url_for("admin")
            )

    if request.method == "POST":

        login_value = request.form.get(
            "login",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if not login_value or not password:

            return render_template(
                "login.html",
                error="Please enter Mobile/Email and Password"
            )

        try:

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                SELECT
                    id,
                    fullname,
                    mobile,
                    email,
                    password,
                    role
                FROM users
                WHERE mobile = ?
                   OR email = ?
                """,
                (
                    login_value,
                    login_value
                )
            )

            user = cur.fetchone()

            conn.close()

        except Exception as e:

            print(
                "LOGIN ERROR:",
                e
            )

            return render_template(
                "login.html",
                error="Database error."
            )

        if not user:

            return render_template(
                "login.html",
                error="Invalid Mobile/Email or Password"
            )

        stored_password = user["password"]

        password_ok = False

        try:

            password_ok = check_password_hash(
                stored_password,
                password
            )

        except Exception:

            password_ok = (
                stored_password == password
            )

        if not password_ok:

            return render_template(
                "login.html",
                error="Invalid Mobile/Email or Password"
            )

        session["user_id"] = user["id"]
        session["name"] = user["fullname"]
        session["mobile"] = user["mobile"]
        session["email"] = user["email"]
        session["role"] = user["role"]

        role = str(
            user["role"]
        ).strip().lower()

        if role == "farmer":

            return redirect(
                url_for("farmer")
            )

        if role == "consumer":

            return redirect(
                url_for("consumer")
            )

        if role == "admin":

            return redirect(
                url_for("admin")
            )

        session.clear()

        return render_template(
            "login.html",
            error="Invalid user role"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# SIGNUP
# =========================================================

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "POST":

        fullname = request.form.get(
            "fullname",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        role = request.form.get(
            "role",
            "Farmer"
        ).strip()

        if not all([
            fullname,
            mobile,
            email,
            password
        ]):

            return render_template(
                "signup.html",
                error="Please fill all required fields."
            )

        try:

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                SELECT id
                FROM users
                WHERE mobile = ?
                   OR email = ?
                """,
                (
                    mobile,
                    email
                )
            )

            if cur.fetchone():

                conn.close()

                return render_template(
                    "signup.html",
                    error="Mobile Number or Email already exists."
                )

            password_hash = generate_password_hash(
                password
            )

            cur.execute(
                """
                INSERT INTO users
                (
                    fullname,
                    mobile,
                    email,
                    password,
                    role
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    fullname,
                    mobile,
                    email,
                    password_hash,
                    role
                )
            )

            conn.commit()
            conn.close()

            return redirect(
                url_for("login")
            )

        except Exception as e:

            print(
                "SIGNUP ERROR:",
                e
            )

            return render_template(
                "signup.html",
                error="Unable to create account."
            )

    return render_template(
        "signup.html"
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        if not email:

            flash(
                "Please enter your email.",
                "error"
            )

            return redirect(
                url_for("forgot_password")
            )

        try:

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                SELECT id, email
                FROM users
                WHERE email = ?
                """,
                (email,)
            )

            user = cur.fetchone()

            conn.close()

        except Exception as e:

            print(
                "FORGOT PASSWORD DB ERROR:",
                e
            )

            flash(
                "Database error.",
                "error"
            )

            return redirect(
                url_for("forgot_password")
            )

        if not user:

            flash(
                "Email address not found.",
                "error"
            )

            return redirect(
                url_for("forgot_password")
            )

        token = serializer.dumps(
            email,
            salt="password-reset"
        )

        reset_link = url_for(
            "reset_password",
            token=token,
            _external=True
        )

        try:

            msg = Message(
                subject="KisanVision360 - Password Reset",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email]
            )

            msg.body = f"""
Hello,

You requested to reset your KisanVision360 password.

Click the link below:

{reset_link}

This link will expire in 15 minutes.

Regards,
KisanVision360 Team
"""

            mail.send(msg)

            flash(
                "Password reset link has been sent to your email.",
                "success"
            )

        except Exception as e:

            print(
                "MAIL ERROR:",
                e
            )

            flash(
                "Unable to send email. Check your Gmail SMTP settings.",
                "error"
            )

        return redirect(
            url_for("login")
        )

    return render_template(
        "forgot_password.html"
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    try:

        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=900
        )

    except Exception:

        flash(
            "Reset link is invalid or expired.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not password or not confirm_password:

            flash(
                "Please fill all fields.",
                "error"
            )

            return redirect(
                url_for(
                    "reset_password",
                    token=token
                )
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                url_for(
                    "reset_password",
                    token=token
                )
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return redirect(
                url_for(
                    "reset_password",
                    token=token
                )
            )

        password_hash = generate_password_hash(
            password
        )

        try:

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                UPDATE users
                SET password = ?
                WHERE email = ?
                """,
                (
                    password_hash,
                    email
                )
            )

            conn.commit()
            conn.close()

            flash(
                "Password changed successfully. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Exception as e:

            print(
                "RESET PASSWORD ERROR:",
                e
            )

            flash(
                "Unable to change password.",
                "error"
            )

    return render_template(
        "reset_password.html",
        token=token
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    role = str(
        session.get(
            "role",
            ""
        )
    ).lower()

    if role == "farmer":
        return redirect(
            url_for("farmer")
        )

    if role == "consumer":
        return redirect(
            url_for("consumer")
        )

    if role == "admin":
        return redirect(
            url_for("admin")
        )

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# FARMER
# =========================================================

@app.route("/farmer")
def farmer():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if str(
        session.get(
            "role",
            ""
        )
    ).lower() != "farmer":

        return redirect(
            url_for("dashboard")
        )

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                fullname,
                mobile,
                email,
                role
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        )

        farmer_data = cur.fetchone()

        conn.close()

    except Exception as e:

        print(
            "FARMER ERROR:",
            e
        )

        farmer_data = None

    if not farmer_data:

        session.clear()

        return redirect(
            url_for("login")
        )

    return render_template(
        "farmer.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        farmer=farmer_data,
        weather=get_weather_data()
    )


# =========================================================
# CONSUMER
# =========================================================

@app.route("/consumer")
def consumer():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if str(
        session.get(
            "role",
            ""
        )
    ).lower() != "consumer":

        return redirect(
            url_for("dashboard")
        )

    try:

        prices = get_crop_prices()

    except Exception as e:

        print(
            "CROP PRICE ERROR:",
            e
        )

        prices = []

    return render_template(
        "consumer.html",
        name=session.get(
            "name",
            "Consumer"
        ),
        weather=get_weather_data(),
        prices=prices
    )


# =========================================================
# ADMIN
# =========================================================

@app.route("/admin")
def admin():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if str(
        session.get(
            "role",
            ""
        )
    ).lower() != "admin":

        return redirect(
            url_for("dashboard")
        )

    try:

        prices = get_crop_prices()

    except Exception:

        prices = []

    return render_template(
        "admin.html",
        name=session.get(
            "name",
            "Admin"
        ),
        weather=get_weather_data(),
        prices=prices
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# WEATHER PAGE
# =========================================================

@app.route("/weather")
def weather():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "weather.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        weather=get_weather_data()
    )


# =========================================================
# CROP RECOMMENDATION
# =========================================================

@app.route(
    "/recommendation",
    methods=["GET", "POST"]
)
def recommendation():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    recommendation_data = {
        "crop": "Soybean",
        "confidence": "92%",
        "reason": "Select your farm conditions and generate an AI recommendation.",
        "fertilizer": "NPK 20:20:0",
        "irrigation": "Every 3 Days",
        "pest_risk": "Low Risk",
        "yield": "25 Quintal/Acre"
    }

    if request.method == "POST":

        soil = request.form.get(
            "soil",
            "black"
        )

        season = request.form.get(
            "season",
            "kharif"
        )

        irrigation = request.form.get(
            "irrigation",
            "good"
        )

        if season == "kharif":

            crops = {
                "black": "Soybean",
                "red": "Groundnut",
                "alluvial": "Rice",
                "loamy": "Maize",
                "sandy": "Bajra"
            }

        elif season == "rabi":

            crops = {
                "black": "Wheat",
                "red": "Chickpea",
                "alluvial": "Wheat",
                "loamy": "Gram",
                "sandy": "Barley"
            }

        else:

            crops = {
                "black": "Moong",
                "red": "Groundnut",
                "alluvial": "Watermelon",
                "loamy": "Cucumber",
                "sandy": "Watermelon"
            }

        crop = crops.get(
            soil,
            "Soybean"
        )

        irrigation_map = {
            "good": "Every 3 Days",
            "medium": "Every 4–5 Days",
            "low": "Every 6–7 Days"
        }

        irrigation_advice = irrigation_map.get(
            irrigation,
            "Every 3 Days"
        )

        fertilizer_map = {
            "black": "NPK 20:20:0",
            "red": "NPK 10:26:26",
            "alluvial": "NPK 20:20:20",
            "loamy": "NPK 15:15:15",
            "sandy": "Organic Manure + NPK"
        }

        fertilizer = fertilizer_map.get(
            soil,
            "Organic Manure + NPK"
        )

        if irrigation == "low":

            pest_risk = "Medium Risk"

        elif irrigation == "medium":

            pest_risk = "Low-Medium Risk"

        else:

            pest_risk = "Low Risk"

        yield_map = {
            "Soybean": "25 Quintal/Acre",
            "Wheat": "30 Quintal/Acre",
            "Rice": "35 Quintal/Acre",
            "Groundnut": "20 Quintal/Acre",
            "Chickpea": "18 Quintal/Acre",
            "Maize": "28 Quintal/Acre",
            "Moong": "10 Quintal/Acre",
            "Watermelon": "100 Quintal/Acre",
            "Cucumber": "80 Quintal/Acre"
        }

        yield_value = yield_map.get(
            crop,
            "22 Quintal/Acre"
        )

        reason = (
            f"{crop} is suitable for "
            f"{season.capitalize()} season "
            f"with {soil} soil."
        )

        recommendation_data = {
            "crop": crop,
            "confidence": "92%",
            "reason": reason,
            "fertilizer": fertilizer,
            "irrigation": irrigation_advice,
            "pest_risk": pest_risk,
            "yield": yield_value
        }

    return render_template(
        "recommendation.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        weather=get_weather_data(),
        recommendation=recommendation_data
    )


# =========================================================
# IRRIGATION
# =========================================================

@app.route(
    "/irrigation",
    methods=["GET", "POST"]
)
def irrigation():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    result = None

    if request.method == "POST":

        crop = request.form.get(
            "crop",
            ""
        ).strip()

        soil = request.form.get(
            "soil",
            "normal"
        )

        try:

            rainfall = float(
                request.form.get(
                    "rainfall",
                    "0"
                )
            )

        except ValueError:

            rainfall = 0

        if rainfall >= 20:

            result = {
                "status": "Irrigation Not Required",
                "reason": f"Recent rainfall is {rainfall} mm."
            }

        elif soil == "wet":

            result = {
                "status": "Irrigation Not Required",
                "reason": f"The soil is wet. Avoid irrigation for {crop}."
            }

        elif soil == "dry":

            result = {
                "status": "Irrigation Required",
                "reason": f"The soil is dry. Irrigate {crop}."
            }

        else:

            result = {
                "status": "Light Irrigation Recommended",
                "reason": f"Use moderate irrigation for {crop}."
            }

    return render_template(
        "irrigation.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        weather=get_weather_data(),
        result=result
    )


@app.route(
    "/pest",
    methods=["GET", "POST"]
)
def pest():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    prediction = None
    filename = None

    if request.method == "POST":

        uploaded_file = request.files.get(
            "crop_image"
        )

        if uploaded_file and uploaded_file.filename:

            filename = secure_filename(
                uploaded_file.filename
            )

            path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            uploaded_file.save(path)

            if pest_model is None:

                prediction = (
                    "AI Model not trained yet"
                )

            else:

                try:

                    img = Image.open(
                        path
                    ).convert("RGB")

                    img = img.resize(
                        (224, 224)
                    )

                    arr = np.array(
                        img,
                        dtype=np.float32
                    )

                    arr = np.expand_dims(
                        arr,
                        axis=0
                    )

                    result = pest_model.predict(
                        arr,
                        verbose=0
                    )

                    index = int(
                        np.argmax(
                            result[0]
                        )
                    )

                    if index < len(
                        PEST_CLASSES
                    ):

                        prediction = (
                            PEST_CLASSES[index]
                        )

                    else:

                        prediction = "Unknown"

                except Exception as e:

                    print(
                        "PEST ERROR:",
                        e
                    )

                    prediction = (
                        "Unable to process image"
                    )

    return render_template(
        "pest.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        prediction=prediction,
        image=filename
    )
# =========================================================
# REPORTS
# =========================================================

# =========================================================
# REPORTS
# Finance + Live Weather Report
# =========================================================

@app.route("/reports")
def reports():

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    if "user_id" not in session:
        return redirect(url_for("login"))

    farmer_id = session["user_id"]
    farmer_name = session.get("name", "Farmer")

    # -----------------------------------------------------
    # DEFAULT FINANCE VALUES
    # -----------------------------------------------------

    income = 0.0
    expenses = 0.0
    profit = 0.0

    income_count = 0
    expense_count = 0

    transactions = []

    # =====================================================
    # FINANCE DATA
    # =====================================================

    try:

        conn = get_db()
        cur = conn.cursor()

        # TOTAL INCOME
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE farmer_id = ?
            AND LOWER(type) = 'income'
        """, (farmer_id,))

        row = cur.fetchone()

        if row:
            income = float(row[0] or 0)

        # TOTAL EXPENSE
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE farmer_id = ?
            AND LOWER(type) = 'expense'
        """, (farmer_id,))

        row = cur.fetchone()

        if row:
            expenses = float(row[0] or 0)

        # INCOME COUNT
        cur.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE farmer_id = ?
            AND LOWER(type) = 'income'
        """, (farmer_id,))

        row = cur.fetchone()

        if row:
            income_count = int(row[0] or 0)

        # EXPENSE COUNT
        cur.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE farmer_id = ?
            AND LOWER(type) = 'expense'
        """, (farmer_id,))

        row = cur.fetchone()

        if row:
            expense_count = int(row[0] or 0)

        # RECENT TRANSACTIONS
        cur.execute("""
            SELECT description, amount, type, date
            FROM transactions
            WHERE farmer_id = ?
            ORDER BY id DESC
            LIMIT 20
        """, (farmer_id,))

        transactions = cur.fetchall()

        conn.close()

    except Exception as e:

        print("REPORT FINANCE ERROR:", e)

    # -----------------------------------------------------
    # PROFIT
    # -----------------------------------------------------

    profit = income - expenses

    # -----------------------------------------------------
    # PROFIT MARGIN
    # -----------------------------------------------------

    if income > 0:

        profit_margin = round(
            (profit / income) * 100,
            2
        )

    else:

        profit_margin = 0

    # -----------------------------------------------------
    # EXPENSE RATIO
    # -----------------------------------------------------

    if income > 0:

        expense_ratio = round(
            (expenses / income) * 100,
            2
        )

    else:

        expense_ratio = 0

    # =====================================================
    # LIVE WEATHER
    # =====================================================

    try:

        # YOUR FUNCTION DOES NOT NEED CITY
        weather = get_weather_data()

        if not weather:
            raise Exception(
                "Weather data is empty"
            )

    except Exception as e:

        print(
            "REPORT WEATHER ERROR:",
            e
        )

        weather = {
            "city": CITY,
            "country": "IN",
            "temperature": 0,
            "feels_like": 0,
            "humidity": 0,
            "pressure": 0,
            "wind": 0,
            "condition": "Unavailable",
            "description": "Weather unavailable",
            "icon": "",
            "visibility": 0,
            "clouds": 0,
            "sunrise": "",
            "sunset": "",
            "rainfall": 0
        }

    # =====================================================
    # SAFE WEATHER VALUES
    # =====================================================

    def safe_float(value):

        try:

            if value in (
                None,
                "",
                "N/A"
            ):
                return 0.0

            return float(value)

        except:

            return 0.0

    temperature = safe_float(
        weather.get("temperature", 0)
    )

    feels_like = safe_float(
        weather.get("feels_like", 0)
    )

    humidity = safe_float(
        weather.get("humidity", 0)
    )

    pressure = safe_float(
        weather.get("pressure", 0)
    )

    wind = safe_float(
        weather.get("wind", 0)
    )

    rainfall = safe_float(
        weather.get("rainfall", 0)
    )

    visibility = safe_float(
        weather.get("visibility", 0)
    )

    clouds = safe_float(
        weather.get("clouds", 0)
    )

    # =====================================================
    # WEATHER CONDITION
    # =====================================================

    condition = weather.get(
        "condition",
        "Unavailable"
    )

    description = weather.get(
        "description",
        "Weather information unavailable"
    )

    city = weather.get(
        "city",
        CITY
    )

    country = weather.get(
        "country",
        "IN"
    )

    # =====================================================
    # WEATHER SCORE
    # =====================================================

    weather_score = 100

    # High temperature
    if temperature >= 35:
        weather_score -= 15

    if temperature >= 40:
        weather_score -= 15

    # High humidity
    if humidity >= 80:
        weather_score -= 15

    # Heavy rain
    if rainfall >= 10:
        weather_score -= 15

    # Strong wind
    if wind >= 10:
        weather_score -= 10

    # Heavy cloud cover
    if clouds >= 90:
        weather_score -= 5

    weather_score = max(
        0,
        min(100, weather_score)
    )

    # =====================================================
    # FINANCIAL SCORE
    # =====================================================

    financial_score = 50

    if income > 0:
        financial_score += 10

    if profit > 0:
        financial_score += 15

    if profit_margin >= 20:
        financial_score += 10

    if income > 0 and expense_ratio <= 70:
        financial_score += 10

    financial_score = min(
        100,
        financial_score
    )

    # =====================================================
    # OVERALL FARM SCORE
    # =====================================================

    farm_score = round(
        (
            financial_score * 0.60
        ) +
        (
            weather_score * 0.40
        )
    )

    # =====================================================
    # FARM STATUS
    # =====================================================

    if farm_score >= 80:

        farm_status = "Excellent"

    elif farm_score >= 60:

        farm_status = "Good"

    elif farm_score >= 40:

        farm_status = "Needs Attention"

    else:

        farm_status = "Critical"

    # =====================================================
    # FINANCE ANALYSIS
    # =====================================================

    financial_status = ""

    if profit > 0:

        financial_status = (
            "Farm is currently profitable."
        )

    elif profit < 0:

        financial_status = (
            "Farm expenses are higher than income."
        )

    else:

        financial_status = (
            "Income and expense data are currently balanced."
        )

    # =====================================================
    # WEATHER ANALYSIS
    # =====================================================

    weather_status = []

    if temperature >= 40:

        weather_status.append(
            "Very high temperature detected."
        )

    elif temperature >= 35:

        weather_status.append(
            "High temperature detected."
        )

    else:

        weather_status.append(
            "Temperature is within a moderate range."
        )

    if humidity >= 80:

        weather_status.append(
            "High humidity may increase disease risk."
        )

    elif humidity < 30:

        weather_status.append(
            "Low humidity may increase crop water demand."
        )

    else:

        weather_status.append(
            "Humidity is at a moderate level."
        )

    if rainfall >= 10:

        weather_status.append(
            "Recent rainfall is high; check field drainage."
        )

    elif rainfall > 0:

        weather_status.append(
            "Rainfall has been recorded."
        )

    else:

        weather_status.append(
            "No significant rainfall is currently recorded."
        )

    if wind >= 10:

        weather_status.append(
            "Strong wind detected; avoid spraying."
        )

    # =====================================================
    # WARNINGS
    # =====================================================

    warning_points = []

    if income == 0:

        warning_points.append(
            "No income transactions have been recorded."
        )

    if expenses > income:

        warning_points.append(
            "Expenses are higher than income."
        )

    if temperature >= 35:

        warning_points.append(
            "High temperature may increase irrigation requirements."
        )

    if humidity >= 80:

        warning_points.append(
            "High humidity may increase crop disease risk."
        )

    if rainfall >= 10:

        warning_points.append(
            "Heavy rainfall may require drainage management."
        )

    if wind >= 10:

        warning_points.append(
            "High wind speed may affect spraying operations."
        )

    # =====================================================
    # POSITIVE POINTS
    # =====================================================

    positive_points = []

    if income > 0:

        positive_points.append(
            "Income records are available."
        )

    if profit > 0:

        positive_points.append(
            "Farm currently has positive profit."
        )

    if profit_margin >= 20:

        positive_points.append(
            "Profit margin is above 20%."
        )

    if weather_score >= 80:

        positive_points.append(
            "Current weather conditions are generally favorable."
        )

    # =====================================================
    # SMART SOLUTIONS
    # =====================================================

    solutions = []

    if income == 0:

        solutions.append({
            "title": "Add Income",
            "description":
                "No income has been recorded.",
            "action":
                "Add crop sales and other income from the Income page."
        })

    if expenses > income:

        solutions.append({
            "title": "Control Expenses",
            "description":
                "Your expenses are greater than income.",
            "action":
                "Review fertilizer, seed, labour and irrigation expenses."
        })

    if temperature >= 35:

        solutions.append({
            "title": "Heat Management",
            "description":
                "Temperature is high.",
            "action":
                "Schedule irrigation during morning or evening."
        })

    if humidity >= 80:

        solutions.append({
            "title": "Disease Monitoring",
            "description":
                "Humidity is high.",
            "action":
                "Inspect crops regularly for fungal disease symptoms."
        })

    if rainfall >= 10:

        solutions.append({
            "title": "Rain Management",
            "description":
                "Rainfall is relatively high.",
            "action":
                "Check drainage and avoid unnecessary irrigation."
        })

    if wind >= 10:

        solutions.append({
            "title": "Wind Protection",
            "description":
                "Wind speed is high.",
            "action":
                "Avoid spraying pesticides during strong winds."
        })

    if not solutions:

        solutions.append({
            "title": "Farm Condition Good",
            "description":
                "No major issue was detected.",
            "action":
                "Continue monitoring Finance and Weather."
        })

    # =====================================================
    # FINAL REPORT
    # =====================================================

    return render_template(

        "reports.html",

        # USER
        name=farmer_name,

        # FINANCE
        income=round(income, 2),
        expenses=round(expenses, 2),
        profit=round(profit, 2),

        profit_margin=profit_margin,
        expense_ratio=expense_ratio,

        income_count=income_count,
        expense_count=expense_count,

        financial_score=financial_score,
        financial_status=financial_status,

        # WEATHER
        weather=weather,

        city=city,
        country=country,

        temperature=temperature,
        feels_like=feels_like,
        humidity=humidity,
        pressure=pressure,
        wind=wind,
        rainfall=rainfall,
        visibility=visibility,
        clouds=clouds,

        condition=condition,
        description=description,

        weather_score=weather_score,
        weather_status=weather_status,

        # OVERALL
        farm_score=farm_score,
        farm_status=farm_status,

        # ANALYSIS
        warning_points=warning_points,
        positive_points=positive_points,
        solutions=solutions,

        # TRANSACTIONS
        transactions=transactions
    )
# =========================================================
# MARKET
# =========================================================

@app.route(
    "/market",
    methods=["GET", "POST"]
)
def market():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    prices = []
    crop = None

    if request.method == "POST":

        crop = request.form.get(
            "crop",
            ""
        ).strip()

        try:

            prices = get_market_price(
                crop
            )

        except Exception as e:

            print(
                "MARKET ERROR:",
                e
            )

    return render_template(
        "market.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        prices=prices,
        crop=crop
    )


# =========================================================
# GOVERNMENT SCHEMES
# =========================================================

@app.route("/government")
def government():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    try:

        schemes_list = get_schemes()

    except Exception as e:

        print(
            "SCHEME ERROR:",
            e
        )

        schemes_list = []

    return render_template(
        "schemes.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        schemes=schemes_list
    )


@app.route("/schemes")
def schemes():

    return government()


# =========================================================
# MARKETPLACE
# =========================================================

@app.route("/marketplace")
def marketplace():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    products = []

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                product_name,
                category,
                quantity,
                unit,
                price,
                description,
                image
            FROM products
            ORDER BY id DESC
            """
        )

        products = cur.fetchall()

        conn.close()

    except Exception as e:

        print(
            "MARKETPLACE ERROR:",
            e
        )

    try:

        prices = get_market_price()

    except Exception as e:

        print(
            "MARKET PRICE ERROR:",
            e
        )

        prices = []

    return render_template(
        "marketplace.html",
        products=products,
        prices=prices,
        weather=get_weather_data(),
        notifications_count=0,
        name=session.get(
            "name",
            "Farmer"
        )
    )


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route(
    "/add-product",
    methods=["GET", "POST"]
)
def add_product():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        product_name = request.form.get(
            "product_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        quantity = request.form.get(
            "quantity",
            "0"
        ).strip()

        unit = request.form.get(
            "unit",
            "kg"
        ).strip()

        price = request.form.get(
            "price",
            "0"
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        uploaded_image = request.files.get(
            "image"
        )

        if not product_name:

            return render_template(
                "add_product.html",
                error="Please enter product name."
            )

        image_name = ""

        if uploaded_image and uploaded_image.filename:

            image_name = secure_filename(
                uploaded_image.filename
            )

            uploaded_image.save(
                os.path.join(
                    PRODUCT_UPLOAD_FOLDER,
                    image_name
                )
            )

        try:

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
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
                """,
                (
                    product_name,
                    category,
                    quantity,
                    unit,
                    price,
                    description,
                    image_name
                )
            )

            conn.commit()

            conn.close()

        except Exception as e:

            print(
                "ADD PRODUCT ERROR:",
                e
            )

            return render_template(
                "add_product.html",
                error="Unable to save product."
            )

        return redirect(
            url_for("marketplace")
        )

    return render_template(
        "add_product.html"
    )

# =========================================================
# PLACE ORDER
# =========================================================

@app.route("/place_order/<int:product_id>", methods=["POST"])
def place_order(product_id):

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    conn = None

    try:
        # Get quantity
        quantity_text = request.form.get("quantity", "").strip()

        if not quantity_text:
            flash("Please enter quantity.", "warning")
            return redirect(url_for("marketplace"))

        try:
            quantity = float(quantity_text)
        except ValueError:
            flash("Invalid quantity.", "danger")
            return redirect(url_for("marketplace"))

        if quantity <= 0:
            flash("Quantity must be greater than 0.", "warning")
            return redirect(url_for("marketplace"))

        # Database
        conn = get_db()
        cur = conn.cursor()

        # Get product
        cur.execute(
            """
            SELECT
                id,
                product_name,
                quantity,
                unit,
                price
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        )

        product = cur.fetchone()

        if not product:
            flash("Product not found.", "danger")
            return redirect(url_for("marketplace"))

        # Product details
        product_id = product["id"]
        product_name = product["product_name"]

        available_quantity = float(
            product["quantity"] or 0
        )

        unit = product["unit"] or "kg"

        price = float(
            product["price"] or 0
        )

        # Check stock
        if quantity > available_quantity:
            flash(
                f"Only {available_quantity:g} {unit} available.",
                "warning"
            )
            return redirect(url_for("marketplace"))

        # Total
        total = price * quantity

        order_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Insert order
        cur.execute(
            """
            INSERT INTO orders
            (
                user_id,
                product_id,
                product_name,
                quantity,
                price,
                total,
                status,
                date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                product_id,
                product_name,
                quantity,
                price,
                total,
                "Processing",
                order_date
            )
        )

        # Update product stock
        remaining_quantity = (
            available_quantity - quantity
        )

        cur.execute(
            """
            UPDATE products
            SET quantity = ?
            WHERE id = ?
            """,
            (
                remaining_quantity,
                product_id
            )
        )

        # Save
        conn.commit()

        flash(
            f"Order placed successfully for {product_name}!",
            "success"
        )

        return redirect(
            url_for("orders")
        )

    except Exception as e:

        print("=" * 60)
        print("PLACE ORDER ACTUAL ERROR:")
        print(repr(e))
        print("=" * 60)

        if conn:
            conn.rollback()

        # Show actual error temporarily
        flash(
            f"Order Error: {str(e)}",
            "danger"
        )

        return redirect(
            url_for("marketplace")
        )

    finally:

        if conn:
            conn.close()
# =========================================================
# REMOVE ORDER
# =========================================================

@app.route(
    "/remove_order/<int:order_id>",
    methods=["POST"]
)
def remove_order(order_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = None

    try:

        conn = get_db()

        cur = conn.cursor()

        # Check order belongs to current user
        cur.execute(
            """
            SELECT
                id,
                product_id,
                quantity
            FROM orders
            WHERE id = ?
              AND user_id = ?
            """,
            (
                order_id,
                session["user_id"]
            )
        )

        order = cur.fetchone()

        if not order:

            conn.close()

            flash(
                "Order not found.",
                "danger"
            )

            return redirect(
                url_for("orders")
            )

        product_id = order[1]
        order_quantity = float(
            order[2] or 0
        )

        # -----------------------------------------
        # RESTORE PRODUCT QUANTITY
        # -----------------------------------------

        cur.execute(
            """
            UPDATE products
            SET quantity = quantity + ?
            WHERE id = ?
            """,
            (
                order_quantity,
                product_id
            )
        )

        # -----------------------------------------
        # DELETE ORDER
        # -----------------------------------------

        cur.execute(
            """
            DELETE FROM orders
            WHERE id = ?
              AND user_id = ?
            """,
            (
                order_id,
                session["user_id"]
            )
        )

        conn.commit()

        flash(
            "Order removed successfully.",
            "success"
        )

    except Exception as e:

        print(
            "REMOVE ORDER ERROR:",
            repr(e)
        )

        if conn:

            conn.rollback()

        flash(
            f"Unable to remove order: {str(e)}",
            "danger"
        )

    finally:

        if conn:
            conn.close()

    return redirect(
        url_for("orders")
    )
# =========================================================
# ORDERS
# =========================================================
# =========================================================
# ORDERS
# =========================================================

@app.route("/orders")
def orders():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    order_list = []

    conn = None

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                product_name,
                quantity,
                price,
                total,
                status,
                date
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
        """, (
            session["user_id"],
        ))

        order_list = cur.fetchall()

    except Exception as e:

        print(
            "ORDERS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load orders.",
            "danger"
        )

    finally:

        if conn:

            conn.close()

    return render_template(

        "orders.html",

        orders=order_list,

        name=session.get(
            "name",
            "User"
        ),

        role=session.get(
            "role",
            "Consumer"
        )
    )
@app.route("/finance")
def finance():

    if "user_id" not in session:
        return redirect(url_for("login"))

    farmer_id = session["user_id"]

    income = 0
    expenses = 0
    transaction_list = []

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE farmer_id = ?
            AND LOWER(type) = 'income'
        """, (farmer_id,))

        income = float(cur.fetchone()[0] or 0)

        cur.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE farmer_id = ?
            AND LOWER(type) = 'expense'
        """, (farmer_id,))

        expenses = float(cur.fetchone()[0] or 0)

        cur.execute("""
            SELECT description, amount, type, date
            FROM transactions
            WHERE farmer_id = ?
            ORDER BY id DESC
            LIMIT 10
        """, (farmer_id,))

        transaction_list = cur.fetchall()

        conn.close()

    except Exception as e:

        print("FINANCE ERROR:", e)

    return render_template(
        "finance.html",
        name=session.get("name", "Farmer"),
        income=income,
        expenses=expenses,
        profit=income - expenses,
        transactions=transaction_list
    )

# =========================================================
# INCOME
# =========================================================

@app.route(
    "/income",
    methods=["GET", "POST"]
)
def income():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    if request.method == "POST":

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:

            amount = float(
                request.form.get(
                    "amount",
                    "0"
                )
            )

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO transactions
                (
                    farmer_id,
                    description,
                    amount,
                    type,
                    date
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    description,
                    amount,
                    "Income",
                    datetime.now().strftime(
                        "%Y-%m-%d"
                    )
                )
            )

            conn.commit()
            conn.close()

        except Exception as e:

            print(
                "INCOME ERROR:",
                e
            )

        return redirect(
            url_for("income")
        )

    income_list = []

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                date,
                description,
                amount
            FROM transactions
            WHERE farmer_id = ?
              AND LOWER(type) = 'income'
            ORDER BY id DESC
            """,
            (user_id,)
        )

        income_list = cur.fetchall()

        conn.close()

    except Exception as e:

        print(
            "INCOME FETCH ERROR:",
            e
        )

    return render_template(
        "income.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        income_list=income_list
    )


# =========================================================
# EXPENSE
# =========================================================

@app.route(
    "/expense",
    methods=["GET", "POST"]
)
def expense():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    if request.method == "POST":

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:

            amount = float(
                request.form.get(
                    "amount",
                    "0"
                )
            )

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO transactions
                (
                    farmer_id,
                    description,
                    amount,
                    type,
                    date
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    description,
                    amount,
                    "Expense",
                    datetime.now().strftime(
                        "%Y-%m-%d"
                    )
                )
            )

            conn.commit()
            conn.close()

        except Exception as e:

            print(
                "EXPENSE ERROR:",
                e
            )

        return redirect(
            url_for("expense")
        )

    expense_list = []

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                date,
                description,
                amount
            FROM transactions
            WHERE farmer_id = ?
              AND LOWER(type) = 'expense'
            ORDER BY id DESC
            """,
            (user_id,)
        )

        expense_list = cur.fetchall()

        conn.close()

    except Exception as e:

        print(
            "EXPENSE FETCH ERROR:",
            e
        )

    return render_template(
        "expense.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        expense_list=expense_list
    )


# =========================================================
# PROFIT
# =========================================================

@app.route("/profit")
def profit():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    farmer_id = session["user_id"]

    total_income = 0
    total_expense = 0

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN LOWER(type) = 'income'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ),
                COALESCE(
                    SUM(
                        CASE
                            WHEN LOWER(type) = 'expense'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                )
            FROM transactions
            WHERE farmer_id = ?
            """,
            (farmer_id,)
        )

        data = cur.fetchone()

        if data:

            total_income = float(
                data[0] or 0
            )

            total_expense = float(
                data[1] or 0
            )

        conn.close()

    except Exception as e:

        print(
            "PROFIT ERROR:",
            e
        )

    return render_template(
        "profit.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        total_income=total_income,
        total_expense=total_expense,
        profit=(
            total_income -
            total_expense
        )
    )


# =========================================================
# KISANVISION360 AI CHATBOT
# =========================================================

def agriculture_bot(message):

    message = str(message or "").strip()

    if not message:
        return "Please ask me something about KisanVision360 or farming."


    text = message.lower()


    # -----------------------------------------------------
    # GREETING
    # -----------------------------------------------------

    if any(word in text.split() for word in ["hi", "hello", "hey", "namaste"]):

        return (
            "👋 Hello! I am KisanVision360 AI Assistant. 🌱\n\n"
            "You can ask me about:\n"
            "🌦 Weather\n"
            "🌱 Crop Recommendation\n"
            "🩺 Disease Detection\n"
            "💧 Irrigation\n"
            "🧪 Fertilizer / NPK\n"
            "📈 Mandi Prices\n"
            "🏛 Government Schemes\n"
            "🛒 Marketplace\n"
            "📦 Orders\n"
            "💰 Finance\n"
            "👤 Profile\n"
            "🔔 Notifications\n"
            "🌐 Languages\n"
            "or any other KisanVision360 feature."
        )


    # -----------------------------------------------------
    # APP / PROJECT
    # -----------------------------------------------------

    if any(word in text for word in [
        "what is kisanvision",
        "what is kisanvision360",
        "kisanvision360",
        "about app",
        "about this app"
    ]):

        return (
            "🌱 KisanVision360 is an AI-powered smart farming platform.\n\n"
            "It provides:\n"
            "• Live Weather\n"
            "• AI Crop Recommendation\n"
            "• AI Disease Detection\n"
            "• Smart Irrigation guidance\n"
            "• Mandi Market Prices\n"
            "• Government Schemes\n"
            "• Finance Management\n"
            "• Farmer Marketplace\n"
            "• Orders\n"
            "• Notifications\n"
            "• Profile and Settings\n"
            "• AI Chatbot\n\n"
            "The platform is designed to help farmers manage "
            "farming activities from one application."
        )


    # -----------------------------------------------------
    # WEATHER
    # -----------------------------------------------------

    if any(word in text for word in [
        "weather",
        "temperature",
        "rain",
        "rainfall",
        "humidity",
        "climate"
    ]):

        try:

            weather = get_weather_data()

            if weather:

                city = weather.get("city", "Nagpur")
                temperature = weather.get("temperature", "N/A")
                description = (
                    weather.get("description")
                    or weather.get("condition")
                    or "N/A"
                )
                humidity = weather.get("humidity", "N/A")

                return (
                    f"🌦️ Current Weather\n\n"
                    f"📍 City: {city}\n"
                    f"🌡 Temperature: {temperature}°C\n"
                    f"☁ Condition: {description}\n"
                    f"💧 Humidity: {humidity}%\n\n"
                    "You can also open the Weather module "
                    "for more weather information."
                )

        except Exception as e:

            print("CHATBOT WEATHER ERROR:", e)

            return (
                "⚠️ I could not fetch the current weather right now. "
                "Please open the Weather module."
            )


    # -----------------------------------------------------
    # CROP RECOMMENDATION
    # -----------------------------------------------------

    if any(word in text for word in [
        "crop recommendation",
        "crop recommend",
        "which crop",
        "best crop",
        "recommend crop",
        "crop advisor"
    ]):

        return (
            "🌱 Crop Recommendation\n\n"
            "KisanVision360 can recommend suitable crops based on "
            "farming conditions such as soil, season, weather "
            "and irrigation availability.\n\n"
            "👉 Open the Crop Recommendation / Crop Advisor module "
            "and enter the required details."
        )


    # -----------------------------------------------------
    # DISEASE
    # -----------------------------------------------------

    if any(word in text for word in [
        "disease",
        "leaf disease",
        "crop disease",
        "plant disease",
        "leaf",
        "disease detection"
    ]):

        return (
            "🩺 AI Disease Detection\n\n"
            "KisanVision360 uses an AI image-classification model "
            "to analyze crop leaf images.\n\n"
            "👉 Open Disease Detection and upload a clear crop-leaf "
            "image.\n\n"
            "The system will predict the possible disease class."
        )


    # -----------------------------------------------------
    # IRRIGATION
    # -----------------------------------------------------

    if any(word in text for word in [
        "irrigation",
        "water management",
        "watering",
        "water requirement"
    ]):

        return (
            "💧 Smart Irrigation\n\n"
            "Irrigation should depend on crop type, soil condition, "
            "crop growth stage and rainfall/weather conditions.\n\n"
            "Avoid unnecessary watering when sufficient rainfall "
            "is expected.\n\n"
            "👉 Open the Smart Irrigation module for app-based guidance."
        )


    # -----------------------------------------------------
    # FERTILIZER
    # -----------------------------------------------------

    if any(word in text for word in [
        "fertilizer",
        "fertiliser",
        "npk",
        "nitrogen",
        "phosphorus",
        "potassium"
    ]):

        return (
            "🧪 Fertilizer / NPK\n\n"
            "NPK stands for:\n"
            "N = Nitrogen\n"
            "P = Phosphorus\n"
            "K = Potassium\n\n"
            "The correct fertilizer depends on the crop, soil "
            "condition and nutrient requirement.\n\n"
            "For exact fertilizer application, use soil-test "
            "information or agricultural expert advice."
        )


    # -----------------------------------------------------
    # MARKET / MANDI
    # -----------------------------------------------------

    if any(word in text for word in [
        "market price",
        "mandi price",
        "mandi",
        "market",
        "crop price",
        "today price",
        "today market price"
    ]):

        try:

            prices = get_market_price()

            if prices:

                result = "📈 Available Mandi Prices\n\n"

                for item in prices[:5]:

                    commodity = item.get(
                        "commodity",
                        "Unknown"
                    )

                    market = item.get(
                        "market",
                        "Unknown"
                    )

                    modal = item.get(
                        "modal_price",
                        "N/A"
                    )

                    result += (
                        f"🌾 {commodity}\n"
                        f"📍 {market}\n"
                        f"💰 Modal Price: ₹{modal}/Quintal\n\n"
                    )

                return result

            return (
                "📈 No live mandi price data is available "
                "from the configured market-data source right now."
            )

        except Exception as e:

            print("CHATBOT MARKET ERROR:", e)

            return (
                "⚠️ I could not fetch live mandi prices right now. "
                "Please open the Market module."
            )


    # -----------------------------------------------------
    # GOVERNMENT SCHEMES
    # -----------------------------------------------------

    if any(word in text for word in [
        "scheme",
        "government scheme",
        "government schemes",
        "farmer scheme",
        "yojana",
        "subsidy"
    ]):

        return (
            "🏛️ Government Schemes\n\n"
            "KisanVision360 includes a Government Schemes section "
            "for agriculture-related schemes and farmer benefits.\n\n"
            "👉 Open Government Schemes from the dashboard "
            "to view the available information."
        )


    # -----------------------------------------------------
    # PEST
    # -----------------------------------------------------

    if any(word in text for word in [
        "pest",
        "insect",
        "insects",
        "keeda",
        "कीड"
    ]):

        return (
            "🐛 Pest Management\n\n"
            "Crop pests can be managed using proper identification, "
            "field monitoring and suitable agricultural practices.\n\n"
            "👉 Use the Pest-related module in KisanVision360 "
            "for available guidance."
        )


    # -----------------------------------------------------
    # MARKETPLACE
    # -----------------------------------------------------

    if any(word in text for word in [
        "marketplace",
        "buy product",
        "sell product",
        "farmer product",
        "product"
    ]):

        return (
            "🛒 KisanVision360 Marketplace\n\n"
            "Farmers can add agricultural products to the marketplace "
            "and consumers can view available products.\n\n"
            "👉 Open Marketplace to browse products.\n"
            "👉 Consumers can select a product and place an order."
        )


    # -----------------------------------------------------
    # ORDER
    # -----------------------------------------------------

    if any(word in text for word in [
        "order",
        "orders",
        "buy",
        "purchase",
        "my order"
    ]):

        return (
            "📦 Orders\n\n"
            "To purchase a marketplace product:\n"
            "1️⃣ Open Marketplace\n"
            "2️⃣ Select a product\n"
            "3️⃣ Click Buy / Place Order\n"
            "4️⃣ Enter the quantity\n"
            "5️⃣ Confirm the order\n\n"
            "Your order can then be viewed from My Orders."
        )


    # -----------------------------------------------------
    # FINANCE
    # -----------------------------------------------------

    if any(word in text for word in [
        "finance",
        "income",
        "expense",
        "profit",
        "money",
        "financial"
    ]):

        return (
            "💰 Finance Management\n\n"
            "KisanVision360 provides Finance features for:\n"
            "• Income\n"
            "• Expenses\n"
            "• Profit calculation\n"
            "• Transaction records\n\n"
            "👉 Open the Finance module to manage your records."
        )


    # -----------------------------------------------------
    # PROFILE
    # -----------------------------------------------------

    if any(word in text for word in [
        "profile",
        "settings",
        "account",
        "my profile"
    ]):

        return (
            "👤 Profile & Settings\n\n"
            "You can manage your profile information and "
            "application settings from the Profile / Settings module."
        )


    # -----------------------------------------------------
    # LANGUAGE
    # -----------------------------------------------------

    if any(word in text for word in [
        "language",
        "marathi",
        "hindi",
        "english",
        "translate"
    ]):

        return (
            "🌐 Language Support\n\n"
            "KisanVision360 provides a language-selection feature "
            "to make the application easier to use for farmers."
        )


    # -----------------------------------------------------
    # NOTIFICATIONS
    # -----------------------------------------------------

    if any(word in text for word in [
        "notification",
        "notifications",
        "alert",
        "alerts"
    ]):

        return (
            "🔔 Notifications\n\n"
            "The Notifications section can be used to view "
            "important updates and alerts from the application."
        )


    # -----------------------------------------------------
    # LOGIN / REGISTER
    # -----------------------------------------------------

    if any(word in text for word in [
        "login",
        "log in",
        "register",
        "signup",
        "sign up",
        "forgot password",
        "password"
    ]):

        return (
            "🔐 Account Help\n\n"
            "Use Login to access your KisanVision360 account.\n"
            "New users can use Register.\n"
            "If you forgot your password, use the Forgot Password "
            "option available on the login page."
        )


    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    if "admin" in text:

        return (
            "🛠️ Admin Module\n\n"
            "The Admin role is intended for managing and monitoring "
            "application-level information and users."
        )


    # -----------------------------------------------------
    # THANK YOU
    # -----------------------------------------------------

    if any(word in text for word in [
        "thank you",
        "thanks",
        "thank"
    ]):

        return (
            "😊 You're welcome!\n\n"
            "I am here to help you with KisanVision360 and "
            "farming-related questions. 🌱"
        )


    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    return (
        "🌱 I can help you with KisanVision360.\n\n"
        "Try asking:\n"
        "• What is the weather today?\n"
        "• Which crop is best?\n"
        "• How does disease detection work?\n"
        "• Give me irrigation advice\n"
        "• What is NPK?\n"
        "• What are today's mandi prices?\n"
        "• Tell me about government schemes\n"
        "• How can I buy a product?\n"
        "• How can I check my orders?\n"
        "• How can I manage finance?\n"
        "• What is KisanVision360?"
    )


# =========================================================
# CHATBOT API
# =========================================================

# =========================================================
# AI CHATBOT API
# =========================================================

@app.route("/ask_chatbot", methods=["POST"])
def ask_chatbot():

    if "user_id" not in session:

        return jsonify({
            "reply": "Please login first."
        }), 401

    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()

    if not message:

        return jsonify({
            "reply": "Please ask me something."
        })

    try:

        reply = agriculture_bot(message)

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        print("CHATBOT ERROR:", e)

        return jsonify({
            "reply": "⚠️ Sorry, something went wrong."
        }), 500
# =========================================================
# NOTIFICATIONS
# =========================================================

def generate_notifications(
    weather=None,
    market=None
):

    notifications = []

    if weather:

        temperature = weather.get(
            "temperature"
        )

        humidity = weather.get(
            "humidity"
        )

        wind = weather.get(
            "wind"
        )

        description = weather.get(
            "description",
            "Current weather"
        )

        if isinstance(
            temperature,
            (int, float)
        ):

            if temperature >= 35:

                notifications.append({
                    "type": "warning",
                    "title": "High Temperature Alert",
                    "message": (
                        f"Temperature is {temperature}°C. "
                        "Check soil moisture."
                    ),
                    "time": "Live weather"
                })

            elif temperature <= 10:

                notifications.append({
                    "type": "warning",
                    "title": "Low Temperature Alert",
                    "message": (
                        f"Temperature is {temperature}°C. "
                        "Protect sensitive crops."
                    ),
                    "time": "Live weather"
                })

        if isinstance(
            humidity,
            (int, float)
        ) and humidity >= 80:

            notifications.append({
                "type": "warning",
                "title": "High Humidity Alert",
                "message": (
                    f"Humidity is {humidity}%. "
                    "Monitor crops for fungal diseases."
                ),
                "time": "Live weather"
            })

        if isinstance(
            wind,
            (int, float)
        ) and wind >= 8:

            notifications.append({
                "type": "warning",
                "title": "Strong Wind Alert",
                "message": (
                    f"Wind speed is {wind} m/s. "
                    "Avoid pesticide spraying."
                ),
                "time": "Live weather"
            })

        notifications.append({
            "type": "weather",
            "title": "Live Weather Update",
            "message": (
                f"{str(description).title()} with "
                f"temperature {temperature}°C."
            ),
            "time": "Updated now"
        })

    if market and isinstance(
        market,
        dict
    ):

        crop = market.get(
            "crop",
            "Crop"
        )

        price = market.get(
            "price"
        )

        if price is not None:

            notifications.append({
                "type": "market",
                "title": "Market Price Update",
                "message": (
                    f"{crop} current market price "
                    f"is ₹{price}."
                ),
                "time": "Market data"
            })

    if not notifications:

        notifications.append({
            "type": "success",
            "title": "Farm Status Normal",
            "message": (
                "No critical farming alerts are currently available."
            ),
            "time": "Updated now"
        })

    return notifications


@app.route("/notifications")
def notifications():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    weather_data = get_weather_data()

    notification_list = generate_notifications(
        weather=weather_data
    )

    return render_template(
        "notifications.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        weather=weather_data,
        notifications=notification_list,
        notification_count=len(
            notification_list
        )
    )


# =========================================================
# PROFILE
# =========================================================

@app.route(
    "/profile",
    methods=["GET", "POST"]
)
def profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        try:

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                UPDATE users
                SET
                    fullname = ?,
                    mobile = ?,
                    email = ?
                WHERE id = ?
                """,
                (
                    name,
                    mobile,
                    email,
                    user_id
                )
            )

            conn.commit()
            conn.close()

            session["name"] = name
            session["mobile"] = mobile
            session["email"] = email

        except Exception as e:

            print(
                "PROFILE UPDATE ERROR:",
                e
            )

        return redirect(
            url_for("profile")
        )

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                fullname,
                mobile,
                email,
                role,
                profile_pic
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        user = cur.fetchone()

        conn.close()

    except Exception as e:

        print(
            "PROFILE ERROR:",
            e
        )

        user = None

    if not user:

        session.clear()

        return redirect(
            url_for("login")
        )

    return render_template(
        "profile.html",
        name=user["fullname"],
        mobile=user["mobile"],
        email=user["email"],
        role=user["role"],
        profile_pic=user["profile_pic"],
        weather=get_weather_data()
    )


# =========================================================
# UPLOAD PROFILE
# =========================================================

@app.route(
    "/upload-profile",
    methods=["POST"]
)
def upload_profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    uploaded_file = request.files.get(
        "profile"
    )

    if uploaded_file and uploaded_file.filename:

        filename = secure_filename(
            uploaded_file.filename
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        uploaded_file.save(
            filepath
        )

        db_path = (
            "/static/uploads/"
            + filename
        )

        try:

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                UPDATE users
                SET profile_pic = ?
                WHERE id = ?
                """,
                (
                    db_path,
                    session["user_id"]
                )
            )

            conn.commit()
            conn.close()

        except Exception as e:

            print(
                "PROFILE IMAGE ERROR:",
                e
            )

    return redirect(
        url_for("profile")
    )


# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings")
def settings():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                fullname,
                mobile,
                email,
                role
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        )

        user = cur.fetchone()

        conn.close()

    except Exception as e:

        print(
            "SETTINGS ERROR:",
            e
        )

        user = None

    if not user:

        session.clear()

        return redirect(
            url_for("login")
        )

    return render_template(
        "settings.html",
        name=user["fullname"],
        mobile=user["mobile"],
        email=user["email"],
        role=user["role"],
        weather=get_weather_data()
    )


# =========================================================
# CHANGE PASSWORD
# =========================================================

@app.route(
    "/change-password",
    methods=["GET", "POST"]
)
def change_password():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if new_password != confirm_password:

            return render_template(
                "change_password.html",
                error="New passwords do not match."
            )

        try:

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                SELECT password
                FROM users
                WHERE id = ?
                """,
                (session["user_id"],)
            )

            user = cur.fetchone()

            if not user:

                conn.close()

                return redirect(
                    url_for("login")
                )

            try:

                valid = check_password_hash(
                    user["password"],
                    current_password
                )

            except Exception:

                valid = (
                    user["password"]
                    ==
                    current_password
                )

            if not valid:

                conn.close()

                return render_template(
                    "change_password.html",
                    error="Current password is incorrect."
                )

            new_hash = generate_password_hash(
                new_password
            )

            cur.execute(
                """
                UPDATE users
                SET password = ?
                WHERE id = ?
                """,
                (
                    new_hash,
                    session["user_id"]
                )
            )

            conn.commit()
            conn.close()

            return render_template(
                "change_password.html",
                success="Password Changed Successfully."
            )

        except Exception as e:

            print(
                "CHANGE PASSWORD ERROR:",
                e
            )

            return render_template(
                "change_password.html",
                error="Unable to change password."
            )

    return render_template(
        "change_password.html"
    )


# =========================================================
# CALCULATOR
# =========================================================

@app.route(
    "/calculator",
    methods=["GET", "POST"]
)
def calculator():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    result = None

    if request.method == "POST":

        try:

            value1 = float(
                request.form.get(
                    "value1",
                    0
                )
            )

            value2 = float(
                request.form.get(
                    "value2",
                    0
                )
            )

            operation = request.form.get(
                "operation",
                "add"
            )

            if operation == "add":

                result = value1 + value2

            elif operation == "subtract":

                result = value1 - value2

            elif operation == "multiply":

                result = value1 * value2

            elif operation == "divide":

                if value2 == 0:

                    result = (
                        "Cannot divide by zero"
                    )

                else:

                    result = value1 / value2

        except Exception:

            result = "Invalid input"

    return render_template(
        "calculator.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        result=result
    )


# =========================================================
# TOOLS
# =========================================================

@app.route("/tools")
def tools():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    tool_list = [

        {
            "name": "🚜 Mahindra Tractor 575 DI",
            "category": "Land Preparation",
            "price": "₹6.7 - ₹7.2 Lakh",
            "image": "",
            "buy": "https://www.mahindratractor.com",
            "rent": "Available through local dealers",
            "subsidy": "Eligible under state agriculture schemes"
        },

        {
            "name": "🌾 Combine Harvester",
            "category": "Harvesting",
            "price": "₹8 Lakh+",
            "image": "",
            "buy": "https://tractorkarvan.com/harvester-machine",
            "rent": "Custom Hiring Centres available",
            "subsidy": "Check state farm mechanization scheme"
        },

        {
            "name": "🔄 Fieldking Rotavator",
            "category": "Soil Preparation",
            "price": "₹1.19 Lakh approx",
            "image": "",
            "buy": "https://www.fieldking.com",
            "rent": "Available",
            "subsidy": "Agriculture machinery subsidy available"
        },

        {
            "name": "🌿 KisanKraft Power Weeder",
            "category": "Weeding",
            "price": "₹37,000 - ₹85,000",
            "image": "",
            "buy": "https://www.kisankraft.com",
            "rent": "Available",
            "subsidy": "Depends on government scheme"
        },

        {
            "name": "🛰 Garuda Agriculture Drone",
            "category": "Smart Farming",
            "price": "₹4.5 - ₹6.5 Lakh",
            "image": "",
            "buy": "https://www.garudaaerospace.com",
            "rent": "Drone service providers available",
            "subsidy": "Drone subsidy available under government programs"
        }

    ]

    return render_template(
        "tools.html",
        tools=tool_list,
        name=session.get(
            "name",
            "Farmer"
        )
    )


# =========================================================
# EMI
# =========================================================

@app.route("/emi")
def emi():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "emi.html",
        name=session.get(
            "name",
            "Farmer"
        )
    )


# =========================================================
# REPORTS
# =========================================================



# =========================================================
# ALERTS
# =========================================================

@app.route("/alerts")
def alerts():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "alerts.html",
        name=session.get(
            "name",
            "Farmer"
        )
    )


# =========================================================
# HELP
# =========================================================

@app.route("/help")
def help():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "help.html",
        name=session.get(
            "name",
            ""
        )
    )


# =========================================================
# CONSUMER REQUEST
# =========================================================

@app.route(
    "/consumer-request",
    methods=["GET", "POST"]
)
def consumer_request():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if str(
        session.get(
            "role",
            ""
        )
    ).lower() != "farmer":

        return redirect(
            url_for("dashboard")
        )

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

    try:

        prices = get_crop_prices()

    except Exception:

        prices = []

    return render_template(
        "consumer_request.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        weather=get_weather_data(),
        prices=prices,
        requests=consumer_requests
    )


# =========================================================
# CHAT PAGE
# =========================================================

@app.route("/chat")
def chat():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    chats = [

        {
            "sender": "Consumer",
            "message": "Hello, I need 500 kg of Soybean.",
            "time": "10:15 AM"
        },

        {
            "sender": session.get(
                "name",
                "Farmer"
            ),
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
        name=session.get(
            "name",
            "Farmer"
        ),
        weather=get_weather_data(),
        chats=chats
    )


# =========================================================
# EDIT PROFILE
# =========================================================

@app.route(
    "/edit-profile",
    methods=["GET", "POST"]
)
def edit_profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        try:

            conn = get_db()

            cur = conn.cursor()

            cur.execute(
                """
                UPDATE users
                SET
                    fullname = ?,
                    mobile = ?,
                    email = ?
                WHERE id = ?
                """,
                (
                    name,
                    mobile,
                    email,
                    session["user_id"]
                )
            )

            conn.commit()
            conn.close()

            session["name"] = name
            session["mobile"] = mobile
            session["email"] = email

        except Exception as e:

            print(
                "EDIT PROFILE ERROR:",
                e
            )

        return redirect(
            url_for("profile")
        )

    return render_template(
        "edit-profile.html",
        name=session.get(
            "name",
            "Farmer"
        ),
        mobile=session.get(
            "mobile",
            ""
        ),
        email=session.get(
            "email",
            ""
        ),
        location=session.get(
            "location",
            "Nagpur"
        )
    )

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print("=" * 50)
    print("KisanVision360 Starting...")
    print("=" * 50)
    print(
        "Database:",
        DATABASE
    )
    print(
        "Marketplace: /marketplace"
    )
    print(
        "Orders: /orders"
    )
    print(
        "Place Order: /place_order/<product_id>"
    )
    print("=" * 50)

    app.run(
        debug=True
    )