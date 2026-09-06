# ============================================================
# KISANVISION360+ | DISEASE DETECTION ROUTES
# File: routes/disease.py
# ============================================================

import os
import io
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash
)

from werkzeug.utils import secure_filename


# ============================================================
# TENSORFLOW / KERAS
# ============================================================

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image

    TENSORFLOW_AVAILABLE = True

except Exception as exc:

    tf = None
    load_model = None
    image = None

    TENSORFLOW_AVAILABLE = False

    logging.warning(
        "TensorFlow unavailable: %s",
        exc
    )


# ============================================================
# BLUEPRINT
# ============================================================

disease_bp = Blueprint(
    "disease",
    __name__,
    url_prefix=""
)


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent


MODEL_PATH = (
    BASE_DIR
    / "ai_models"
    / "disease_model.keras"
)


UPLOAD_FOLDER = (
    BASE_DIR
    / "static"
    / "uploads"
    / "disease"
)


UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

# YOUR MODEL:
# (None, 128, 128, 3)

IMG_SIZE = (
    128,
    128
)


MAX_IMAGE_SIZE_MB = 10

MAX_IMAGE_SIZE_BYTES = (
    MAX_IMAGE_SIZE_MB
    * 1024
    * 1024
)


ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


# ============================================================
# 53 DISEASE CLASSES
# ============================================================

CLASS_NAMES = [

    "Apple_Apple_scab",
    "Apple_Black_rot",
    "Apple_Cedar_apple_rust",
    "Apple_healthy",

    "Cherry_including_sour_Powdery_mildew",
    "Cherry_including_sour_healthy",

    "Corn_maize_Cercospora_leaf_spot_Gray_leaf_spot",
    "Corn_maize_Common_rust",
    "Corn_maize_Northern_Leaf_Blight",
    "Corn_maize_healthy",

    "Cotton_bacterial_blight",
    "Cotton_curl_virus",
    "Cotton_fussarium_wilt",
    "Cotton_healthy",

    "Grape_Black_rot",
    "Grape_Esca_Black_Measles",
    "Grape_Leaf_blight_Isariopsis_Leaf_Spot",
    "Grape_healthy",

    "Orange_Haunglongbing_Citrus_greening",
    "Orange_Healthy_Leaf",

    "Peach_Bacterial_spot",
    "Peach_healthy",

    "Pepper_bell_Bacterial_spot",
    "Pepper_bell_healthy",

    "Potato_Early_blight",
    "Potato_Late_blight",
    "Potato_healthy",

    "Rice_brown_spot",
    "Rice_healthy",
    "Rice_hispa",
    "Rice_leaf_blast",
    "Rice_neck_blast",

    "Soybean_bacterial_blight",
    "Soybean_caterpillar",
    "Soybean_diabrotica_speciosa",
    "Soybean_downy_mildew",
    "Soybean_healthy",
    "Soybean_mosaic_virus",
    "Soybean_powdery_mildew",
    "Soybean_rust",
    "Soybean_southern_blight",

    "Strawberry_Leaf_scorch",
    "Strawberry_healthy",

    "Tomato_Bacterial_spot",
    "Tomato_Early_blight",
    "Tomato_Late_blight",
    "Tomato_Leaf_Mold",
    "Tomato_Septoria_leaf_spot",
    "Tomato_Spider_mites_Two-spotted_spider_mite",
    "Tomato_Target_Spot",
    "Tomato_Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato_Tomato_mosaic_virus",
    "Tomato_healthy"
]


# ============================================================
# VERIFY CLASS COUNT
# ============================================================

print("=" * 70)

print(
    "[DISEASE] CLASS COUNT:",
    len(CLASS_NAMES)
)

print("=" * 70)


# ============================================================
# DISEASE INFORMATION
# ============================================================

DISEASE_INFO = {

    # --------------------------------------------------------
    # APPLE
    # --------------------------------------------------------

    "Apple_Apple_scab": {
        "display_name": "Apple - Apple Scab",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Olive or brown spots may appear on leaves.",
            "Lesions may become darker as they develop.",
            "Fruit can develop scabby lesions."
        ],
        "treatment": [
            "Remove heavily affected plant material.",
            "Maintain field sanitation.",
            "Follow locally recommended fungicide practices."
        ],
        "prevention": [
            "Remove fallen infected leaves.",
            "Maintain good airflow.",
            "Monitor plants regularly."
        ]
    },

    "Apple_Black_rot": {
        "display_name": "Apple - Black Rot",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Brown circular leaf lesions may appear.",
            "Fruit may develop dark rotting areas.",
            "Affected tissue can become black."
        ],
        "treatment": [
            "Remove infected plant material.",
            "Maintain orchard sanitation.",
            "Follow locally recommended disease management."
        ],
        "prevention": [
            "Remove mummified fruit.",
            "Prune affected branches where appropriate.",
            "Monitor plants regularly."
        ]
    },

    "Apple_Cedar_apple_rust": {
        "display_name": "Apple - Cedar Apple Rust",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Yellow-orange spots may develop on leaves.",
            "Spots can enlarge over time.",
            "Premature leaf drop may occur."
        ],
        "treatment": [
            "Remove severely affected material.",
            "Improve orchard sanitation.",
            "Use locally recommended disease-management practices."
        ],
        "prevention": [
            "Monitor plants regularly.",
            "Maintain good airflow.",
            "Follow recommended orchard management."
        ]
    },

    "Apple_healthy": {
        "display_name": "Apple - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected.",
            "The image was classified as healthy."
        ],
        "treatment": [
            "No disease treatment is indicated by this prediction."
        ],
        "prevention": [
            "Continue regular monitoring.",
            "Maintain proper irrigation and nutrition."
        ]
    },

    # --------------------------------------------------------
    # CHERRY
    # --------------------------------------------------------

    "Cherry_including_sour_Powdery_mildew": {
        "display_name": "Cherry - Powdery Mildew",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "White powdery growth may appear on leaves.",
            "Young leaves may become distorted.",
            "Plant growth can be affected."
        ],
        "treatment": [
            "Remove severely affected material where appropriate.",
            "Improve airflow.",
            "Follow locally recommended fungicide practices."
        ],
        "prevention": [
            "Avoid excessive humidity around foliage.",
            "Maintain plant spacing.",
            "Monitor regularly."
        ]
    },

    "Cherry_including_sour_healthy": {
        "display_name": "Cherry - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected.",
            "The image was classified as healthy."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring.",
            "Maintain proper crop nutrition."
        ]
    },

    # --------------------------------------------------------
    # CORN
    # --------------------------------------------------------

    "Corn_maize_Cercospora_leaf_spot_Gray_leaf_spot": {
        "display_name": "Corn - Cercospora / Gray Leaf Spot",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Gray or brown rectangular leaf lesions may appear.",
            "Lesions can expand along leaf veins.",
            "Severe infection can reduce healthy leaf area."
        ],
        "treatment": [
            "Remove severely affected material where practical.",
            "Maintain crop sanitation.",
            "Follow locally recommended disease-management practices."
        ],
        "prevention": [
            "Use appropriate crop rotation.",
            "Maintain good field sanitation.",
            "Monitor leaves regularly."
        ]
    },

    "Corn_maize_Common_rust": {
        "display_name": "Corn - Common Rust",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Rust-colored pustules may appear on leaves.",
            "Pustules can occur on both leaf surfaces.",
            "Severe infection may reduce photosynthetic area."
        ],
        "treatment": [
            "Monitor disease progression.",
            "Follow locally recommended management practices."
        ],
        "prevention": [
            "Use appropriate resistant varieties where available.",
            "Maintain crop health.",
            "Monitor fields regularly."
        ]
    },

    "Corn_maize_Northern_Leaf_Blight": {
        "display_name": "Corn - Northern Leaf Blight",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Long gray-green lesions may appear.",
            "Lesions can enlarge along leaves.",
            "Severe infection may reduce leaf area."
        ],
        "treatment": [
            "Maintain field sanitation.",
            "Follow locally recommended disease-management practices."
        ],
        "prevention": [
            "Use suitable resistant varieties.",
            "Practice appropriate crop rotation.",
            "Monitor fields regularly."
        ]
    },

    "Corn_maize_healthy": {
        "display_name": "Corn - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected.",
            "The image was classified as healthy."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Maintain proper irrigation.",
            "Maintain balanced crop nutrition."
        ]
    },

    # --------------------------------------------------------
    # COTTON
    # --------------------------------------------------------

    "Cotton_bacterial_blight": {
        "display_name": "Cotton - Bacterial Blight",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Water-soaked spots may appear.",
            "Brown or dark lesions can develop.",
            "Leaves may dry progressively."
        ],
        "treatment": [
            "Remove severely affected material where appropriate.",
            "Avoid unnecessary overhead irrigation.",
            "Maintain field sanitation."
        ],
        "prevention": [
            "Use healthy planting material.",
            "Maintain suitable crop spacing.",
            "Monitor fields regularly."
        ]
    },

    "Cotton_curl_virus": {
        "display_name": "Cotton - Curl Virus",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Leaves may curl.",
            "Leaves may become distorted.",
            "Plant growth can become stunted."
        ],
        "treatment": [
            "Remove heavily affected plants where appropriate.",
            "Control insect vectors according to local recommendations.",
            "Follow integrated pest-management practices."
        ],
        "prevention": [
            "Use healthy planting material.",
            "Monitor vector insects.",
            "Remove heavily infected plants where appropriate."
        ]
    },

    "Cotton_fussarium_wilt": {
        "display_name": "Cotton - Fusarium Wilt",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Leaves may wilt gradually.",
            "Older leaves may turn yellow.",
            "Plant growth may become weak."
        ],
        "treatment": [
            "Remove severely affected plants where appropriate.",
            "Maintain good drainage.",
            "Follow locally recommended management."
        ],
        "prevention": [
            "Use disease-free planting material.",
            "Practice suitable crop rotation.",
            "Maintain soil health."
        ]
    },

    "Cotton_healthy": {
        "display_name": "Cotton - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected.",
            "The image was classified as healthy."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring.",
            "Maintain good crop management."
        ]
    },

    # --------------------------------------------------------
    # GRAPE
    # --------------------------------------------------------

    "Grape_Black_rot": {
        "display_name": "Grape - Black Rot",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Brown circular leaf spots may appear.",
            "Dark lesions can develop on fruit.",
            "Fruit may eventually become shriveled."
        ],
        "treatment": [
            "Remove infected fruit and plant material.",
            "Maintain vineyard sanitation.",
            "Follow locally recommended fungicide practices."
        ],
        "prevention": [
            "Remove mummified fruit.",
            "Maintain good airflow.",
            "Monitor vines regularly."
        ]
    },

    "Grape_Esca_Black_Measles": {
        "display_name": "Grape - Esca / Black Measles",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Leaf discoloration may develop.",
            "Dark spots can appear on fruit.",
            "Vine vigor may decrease."
        ],
        "treatment": [
            "Remove severely affected material where appropriate.",
            "Maintain vineyard sanitation.",
            "Consult local crop-management recommendations."
        ],
        "prevention": [
            "Use healthy planting material.",
            "Sanitize pruning tools.",
            "Monitor vines regularly."
        ]
    },

    "Grape_Leaf_blight_Isariopsis_Leaf_Spot": {
        "display_name": "Grape - Leaf Blight / Isariopsis Leaf Spot",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Dark leaf spots may appear.",
            "Affected areas may expand.",
            "Leaves may dry under severe infection."
        ],
        "treatment": [
            "Remove heavily infected leaves where appropriate.",
            "Improve canopy airflow.",
            "Follow local disease-management recommendations."
        ],
        "prevention": [
            "Maintain proper vine spacing.",
            "Avoid excessive leaf wetness.",
            "Monitor regularly."
        ]
    },

    "Grape_healthy": {
        "display_name": "Grape - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected.",
            "The image was classified as healthy."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring."
        ]
    },

    # --------------------------------------------------------
    # ORANGE
    # --------------------------------------------------------

    "Orange_Haunglongbing_Citrus_greening": {
        "display_name": "Orange - Citrus Greening",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Leaves may show uneven yellowing.",
            "Veins may remain greener than surrounding tissue.",
            "Plant vigor and fruit development may decline."
        ],
        "treatment": [
            "Inspect affected trees carefully.",
            "Manage insect vectors according to local recommendations.",
            "Consult a qualified agricultural expert."
        ],
        "prevention": [
            "Use healthy planting material.",
            "Monitor vector insects.",
            "Remove severely affected trees where locally recommended."
        ]
    },

    "Orange_Healthy_Leaf": {
        "display_name": "Orange - Healthy Leaf",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected.",
            "The image was classified as healthy."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring."
        ]
    },

    # --------------------------------------------------------
    # PEACH
    # --------------------------------------------------------

    "Peach_Bacterial_spot": {
        "display_name": "Peach - Bacterial Spot",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Small dark leaf spots may appear.",
            "Spots may enlarge or merge.",
            "Fruit lesions can occur."
        ],
        "treatment": [
            "Remove severely affected material where appropriate.",
            "Maintain orchard sanitation.",
            "Follow local disease-management recommendations."
        ],
        "prevention": [
            "Maintain good airflow.",
            "Avoid excessive leaf wetness.",
            "Monitor plants regularly."
        ]
    },

    "Peach_healthy": {
        "display_name": "Peach - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring."
        ]
    },

    # --------------------------------------------------------
    # PEPPER
    # --------------------------------------------------------

    "Pepper_bell_Bacterial_spot": {
        "display_name": "Pepper Bell - Bacterial Spot",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Small water-soaked spots may appear.",
            "Spots can become brown or dark.",
            "Leaves may develop damaged areas."
        ],
        "treatment": [
            "Remove severely affected material.",
            "Avoid unnecessary overhead irrigation.",
            "Follow local management recommendations."
        ],
        "prevention": [
            "Use healthy seedlings.",
            "Maintain field sanitation.",
            "Monitor crops regularly."
        ]
    },

    "Pepper_bell_healthy": {
        "display_name": "Pepper Bell - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring."
        ]
    },

    # --------------------------------------------------------
    # POTATO
    # --------------------------------------------------------

    "Potato_Early_blight": {
        "display_name": "Potato - Early Blight",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Dark circular leaf spots may appear.",
            "Concentric rings can develop in lesions.",
            "Older leaves are often affected first."
        ],
        "treatment": [
            "Remove severely affected plant material where appropriate.",
            "Maintain field sanitation.",
            "Follow locally recommended fungicide practices."
        ],
        "prevention": [
            "Practice suitable crop rotation.",
            "Avoid prolonged leaf wetness.",
            "Monitor crops regularly."
        ]
    },

    "Potato_Late_blight": {
        "display_name": "Potato - Late Blight",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Dark irregular leaf lesions may appear.",
            "Lesions can spread rapidly under favorable conditions.",
            "Severe infection can destroy foliage."
        ],
        "treatment": [
            "Remove severely infected material where appropriate.",
            "Improve field sanitation.",
            "Follow locally recommended disease-management practices."
        ],
        "prevention": [
            "Monitor weather and crop conditions.",
            "Avoid prolonged leaf wetness.",
            "Use recommended resistant varieties where available."
        ]
    },

    "Potato_healthy": {
        "display_name": "Potato - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring."
        ]
    },

    # --------------------------------------------------------
    # RICE
    # --------------------------------------------------------

    "Rice_brown_spot": {
        "display_name": "Rice - Brown Spot",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Brown spots may appear on leaves.",
            "Lesions can enlarge over time.",
            "Severe infection can reduce healthy leaf area."
        ],
        "treatment": [
            "Maintain appropriate crop nutrition.",
            "Follow locally recommended disease-management practices."
        ],
        "prevention": [
            "Use healthy seed.",
            "Maintain balanced nutrition.",
            "Monitor fields regularly."
        ]
    },

    "Rice_healthy": {
        "display_name": "Rice - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring."
        ]
    },

    "Rice_hispa": {
        "display_name": "Rice - Hispa",
        "status": "Disease / Pest Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Leaf surfaces may show scraped areas.",
            "Leaves can develop damaged or whitish patches.",
            "Plant vigor may decline."
        ],
        "treatment": [
            "Monitor pest levels.",
            "Follow locally recommended integrated pest management."
        ],
        "prevention": [
            "Monitor fields regularly.",
            "Maintain appropriate crop management."
        ]
    },

    "Rice_leaf_blast": {
        "display_name": "Rice - Leaf Blast",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Spindle-shaped lesions may appear.",
            "Lesions can develop gray centers.",
            "Severe infection can damage leaves."
        ],
        "treatment": [
            "Maintain balanced crop nutrition.",
            "Follow locally recommended fungicide practices."
        ],
        "prevention": [
            "Use healthy seed.",
            "Avoid excessive nitrogen.",
            "Monitor fields regularly."
        ]
    },

    "Rice_neck_blast": {
        "display_name": "Rice - Neck Blast",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Dark lesions can develop around the neck of the panicle.",
            "Panicles may fail to fill normally.",
            "Yield can be reduced."
        ],
        "treatment": [
            "Follow locally recommended disease-management practices.",
            "Monitor crop development carefully."
        ],
        "prevention": [
            "Use healthy seed.",
            "Maintain balanced nutrition.",
            "Monitor crop during reproductive stages."
        ]
    },

    # --------------------------------------------------------
    # SOYBEAN
    # --------------------------------------------------------

    "Soybean_bacterial_blight": {
        "display_name": "Soybean - Bacterial Blight",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Small water-soaked leaf spots may appear.",
            "Spots can become brown.",
            "Leaves may develop irregular lesions."
        ],
        "treatment": [
            "Maintain field sanitation.",
            "Avoid unnecessary overhead irrigation.",
            "Follow local recommendations."
        ],
        "prevention": [
            "Use healthy seed.",
            "Maintain crop spacing.",
            "Monitor fields regularly."
        ]
    },

    "Soybean_caterpillar": {
        "display_name": "Soybean - Caterpillar",
        "status": "Pest Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Leaves may show chewing damage.",
            "Leaf area can be reduced.",
            "Severe infestation can weaken plants."
        ],
        "treatment": [
            "Inspect plants for caterpillars.",
            "Use integrated pest management."
        ],
        "prevention": [
            "Monitor fields regularly.",
            "Use locally recommended pest-management practices."
        ]
    },

    "Soybean_diabrotica_speciosa": {
        "display_name": "Soybean - Diabrotica Speciosa",
        "status": "Pest Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Leaf feeding damage may be visible.",
            "Irregular holes may appear in leaves."
        ],
        "treatment": [
            "Monitor pest population.",
            "Follow locally recommended pest management."
        ],
        "prevention": [
            "Regular field scouting.",
            "Maintain appropriate crop management."
        ]
    },

    "Soybean_downy_mildew": {
        "display_name": "Soybean - Downy Mildew",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Pale or yellow areas may appear on leaves.",
            "Downy growth may occur under suitable conditions.",
            "Leaves may become weakened."
        ],
        "treatment": [
            "Improve airflow where possible.",
            "Follow locally recommended disease management."
        ],
        "prevention": [
            "Use healthy seed.",
            "Avoid prolonged leaf wetness.",
            "Monitor crops regularly."
        ]
    },

    "Soybean_healthy": {
        "display_name": "Soybean - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring."
        ]
    },

    "Soybean_mosaic_virus": {
        "display_name": "Soybean - Mosaic Virus",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Mottled leaf patterns may appear.",
            "Leaves can become distorted.",
            "Plant growth may be reduced."
        ],
        "treatment": [
            "Remove heavily affected plants where appropriate.",
            "Manage insect vectors according to local recommendations."
        ],
        "prevention": [
            "Use healthy planting material.",
            "Monitor vector insects.",
            "Maintain field sanitation."
        ]
    },

    "Soybean_powdery_mildew": {
        "display_name": "Soybean - Powdery Mildew",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "White powdery growth may appear.",
            "Leaf surfaces may become covered by fungal growth."
        ],
        "treatment": [
            "Improve airflow.",
            "Follow locally recommended disease-management practices."
        ],
        "prevention": [
            "Avoid excessive humidity.",
            "Monitor fields regularly."
        ]
    },

    "Soybean_rust": {
        "display_name": "Soybean - Rust",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Small rust-colored spots may appear.",
            "Lesions can increase in number.",
            "Severe infection can cause leaf loss."
        ],
        "treatment": [
            "Monitor crop closely.",
            "Follow locally recommended fungicide practices."
        ],
        "prevention": [
            "Use appropriate resistant varieties where available.",
            "Monitor fields regularly."
        ]
    },

    "Soybean_southern_blight": {
        "display_name": "Soybean - Southern Blight",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Plant tissue may wilt.",
            "Lower stems can develop lesions.",
            "Plants may weaken or die."
        ],
        "treatment": [
            "Remove severely affected plants where appropriate.",
            "Improve drainage.",
            "Follow local disease-management practices."
        ],
        "prevention": [
            "Maintain field sanitation.",
            "Use suitable crop rotation.",
            "Avoid excessive soil moisture."
        ]
    },

    # --------------------------------------------------------
    # STRAWBERRY
    # --------------------------------------------------------

    "Strawberry_Leaf_scorch": {
        "display_name": "Strawberry - Leaf Scorch",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Dark spots may appear on leaves.",
            "Leaf tissue may dry or scorch.",
            "Severe infection may reduce leaf area."
        ],
        "treatment": [
            "Remove severely affected leaves.",
            "Maintain field sanitation.",
            "Follow locally recommended management."
        ],
        "prevention": [
            "Maintain good airflow.",
            "Avoid prolonged leaf wetness.",
            "Monitor plants regularly."
        ]
    },

    "Strawberry_healthy": {
        "display_name": "Strawberry - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular monitoring."
        ]
    },

    # --------------------------------------------------------
    # TOMATO
    # --------------------------------------------------------

    "Tomato_Bacterial_spot": {
        "display_name": "Tomato - Bacterial Spot",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Small dark spots may appear on leaves.",
            "Spots can enlarge.",
            "Fruit may develop lesions."
        ],
        "treatment": [
            "Remove severely affected plant material.",
            "Avoid unnecessary overhead irrigation.",
            "Follow locally recommended management."
        ],
        "prevention": [
            "Use healthy seedlings.",
            "Maintain field sanitation.",
            "Monitor crops regularly."
        ]
    },

    "Tomato_Early_blight": {
        "display_name": "Tomato - Early Blight",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Dark circular spots may appear.",
            "Concentric rings may develop.",
            "Older leaves are often affected first."
        ],
        "treatment": [
            "Remove severely affected leaves where appropriate.",
            "Maintain field sanitation.",
            "Follow locally recommended fungicide practices."
        ],
        "prevention": [
            "Avoid prolonged leaf wetness.",
            "Maintain crop spacing.",
            "Monitor regularly."
        ]
    },

    "Tomato_Late_blight": {
        "display_name": "Tomato - Late Blight",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Dark irregular lesions may appear.",
            "Lesions can spread rapidly.",
            "Severe infection can damage foliage and fruit."
        ],
        "treatment": [
            "Remove severely infected material.",
            "Improve field sanitation.",
            "Follow locally recommended disease-management practices."
        ],
        "prevention": [
            "Monitor weather and crop conditions.",
            "Avoid prolonged leaf wetness.",
            "Use recommended resistant varieties where available."
        ]
    },

    "Tomato_Leaf_Mold": {
        "display_name": "Tomato - Leaf Mold",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Yellow patches may appear on upper leaf surfaces.",
            "Mold growth may occur underneath leaves.",
            "Leaves may dry under severe infection."
        ],
        "treatment": [
            "Improve ventilation.",
            "Reduce excessive humidity.",
            "Follow local disease-management recommendations."
        ],
        "prevention": [
            "Maintain good airflow.",
            "Avoid excessive leaf wetness.",
            "Monitor plants regularly."
        ]
    },

    "Tomato_Septoria_leaf_spot": {
        "display_name": "Tomato - Septoria Leaf Spot",
        "status": "Disease Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Small circular spots may appear.",
            "Spots can contain darker centers.",
            "Older leaves may be affected first."
        ],
        "treatment": [
            "Remove affected leaves where appropriate.",
            "Maintain field sanitation.",
            "Follow local recommendations."
        ],
        "prevention": [
            "Avoid overhead irrigation.",
            "Maintain good spacing.",
            "Monitor crops regularly."
        ]
    },

    "Tomato_Spider_mites_Two-spotted_spider_mite": {
        "display_name": "Tomato - Two-Spotted Spider Mites",
        "status": "Pest Detected",
        "risk": "Medium",
        "severity": "Medium",
        "symptoms": [
            "Fine stippling may appear on leaves.",
            "Leaves may become yellow or bronzed.",
            "Fine webbing may occur under heavy infestation."
        ],
        "treatment": [
            "Inspect leaf undersides.",
            "Use integrated pest management.",
            "Follow locally recommended controls."
        ],
        "prevention": [
            "Monitor plants regularly.",
            "Maintain appropriate field hygiene."
        ]
    },

    "Tomato_Target_Spot": {
        "display_name": "Tomato - Target Spot",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Circular brown lesions may appear.",
            "Concentric rings may develop.",
            "Leaves can dry under severe infection."
        ],
        "treatment": [
            "Remove severely affected leaves.",
            "Improve airflow.",
            "Follow locally recommended fungicide practices."
        ],
        "prevention": [
            "Avoid prolonged leaf wetness.",
            "Maintain proper crop spacing.",
            "Monitor regularly."
        ]
    },

    "Tomato_Tomato_Yellow_Leaf_Curl_Virus": {
        "display_name": "Tomato - Yellow Leaf Curl Virus",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Leaves may curl upward.",
            "Leaves may become yellow and distorted.",
            "Plant growth can become stunted."
        ],
        "treatment": [
            "Remove heavily infected plants where appropriate.",
            "Control insect vectors according to local recommendations.",
            "Follow integrated pest management."
        ],
        "prevention": [
            "Use healthy seedlings.",
            "Monitor vector insects.",
            "Remove infected plants where appropriate."
        ]
    },

    "Tomato_Tomato_mosaic_virus": {
        "display_name": "Tomato - Mosaic Virus",
        "status": "Disease Detected",
        "risk": "High",
        "severity": "High",
        "symptoms": [
            "Mottled green and yellow patterns may appear.",
            "Leaves may become distorted.",
            "Plant growth may be reduced."
        ],
        "treatment": [
            "Remove heavily affected plants where appropriate.",
            "Sanitize tools.",
            "Follow locally recommended disease-management practices."
        ],
        "prevention": [
            "Use healthy planting material.",
            "Sanitize tools regularly.",
            "Maintain field hygiene."
        ]
    },

    "Tomato_healthy": {
        "display_name": "Tomato - Healthy",
        "status": "Healthy",
        "risk": "Low",
        "severity": "None",
        "symptoms": [
            "No major disease pattern detected.",
            "The image was classified as healthy."
        ],
        "treatment": [
            "No disease treatment is indicated."
        ],
        "prevention": [
            "Continue regular crop monitoring.",
            "Maintain proper irrigation and nutrition."
        ]
    }
}


# ============================================================
# FALLBACK INFORMATION
# ============================================================

def get_disease_info(class_name):

    info = DISEASE_INFO.get(class_name)

    if info:
        return info

    return {
        "display_name":
            class_name.replace(
                "_",
                " "
            ).title(),

        "status":
            "Prediction Available",

        "risk":
            "Unknown",

        "severity":
            "Unknown",

        "symptoms": [],

        "treatment": [
            "Consult a qualified agricultural expert."
        ],

        "prevention": [
            "Continue regular crop monitoring."
        ]
    }


# ============================================================
# MODEL STATE
# ============================================================

MODEL = None

MODEL_ERROR = None


# ============================================================
# LOAD MODEL
# ============================================================

def load_disease_model():

    global MODEL
    global MODEL_ERROR

    if MODEL is not None:
        return MODEL

    if not TENSORFLOW_AVAILABLE:

        MODEL_ERROR = (
            "TensorFlow is not available."
        )

        return None

    if not MODEL_PATH.exists():

        MODEL_ERROR = (
            f"Disease model not found: "
            f"{MODEL_PATH}"
        )

        logger.error(
            MODEL_ERROR
        )

        return None

    try:

        logger.info(
            "Loading disease model: %s",
            MODEL_PATH
        )

        MODEL = load_model(
            str(MODEL_PATH),
            compile=False
        )

        MODEL_ERROR = None

        logger.info(
            "Model input shape: %s",
            MODEL.input_shape
        )

        logger.info(
            "Model output shape: %s",
            MODEL.output_shape
        )

        # ----------------------------------------------------
        # VERIFY OUTPUT CLASS COUNT
        # ----------------------------------------------------

        output_shape = MODEL.output_shape

        if isinstance(
            output_shape,
            list
        ):
            output_shape = output_shape[0]

        output_classes = output_shape[-1]

        logger.info(
            "Model output classes: %s",
            output_classes
        )

        logger.info(
            "Configured classes: %s",
            len(CLASS_NAMES)
        )

        if output_classes != len(CLASS_NAMES):

            MODEL_ERROR = (
                "Model/class mismatch: "
                f"model outputs {output_classes} "
                f"classes but disease.py contains "
                f"{len(CLASS_NAMES)} classes."
            )

            logger.error(
                MODEL_ERROR
            )

            MODEL = None

            return None

        logger.info(
            "Disease model loaded successfully."
        )

        return MODEL

    except Exception as exc:

        MODEL = None

        MODEL_ERROR = str(exc)

        logger.exception(
            "Failed to load disease model."
        )

        return None


# ============================================================
# FILE VALIDATION
# ============================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = (
        filename
        .rsplit(".", 1)[1]
        .lower()
        .strip()
    )

    return extension in ALLOWED_EXTENSIONS


# ============================================================
# VALIDATE FILE
# ============================================================

def validate_uploaded_file(file):

    if file is None:

        return (
            False,
            "No image was uploaded."
        )

    if not file.filename:

        return (
            False,
            "Please select an image."
        )

    if not allowed_file(
        file.filename
    ):

        return (
            False,
            "Only JPG, JPEG, PNG and WEBP images are allowed."
        )

    return (
        True,
        None
    )


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def prepare_image(image_path):

    if not TENSORFLOW_AVAILABLE:

        raise RuntimeError(
            "TensorFlow is not available."
        )

    if image is None:

        raise RuntimeError(
            "Keras image preprocessing is unavailable."
        )

    # --------------------------------------------------------
    # LOAD IMAGE
    # --------------------------------------------------------

    img = image.load_img(
        str(image_path),
        target_size=IMG_SIZE,
        color_mode="rgb"
    )

    # --------------------------------------------------------
    # ARRAY
    # --------------------------------------------------------

    img_array = image.img_to_array(
        img
    )

    # --------------------------------------------------------
    # FLOAT32
    # --------------------------------------------------------

    img_array = img_array.astype(
        np.float32
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # DO NOT DIVIDE BY 255 HERE.
    #
    # Current disease_model.keras already contains:
    #
    # layers.Rescaling(1./255)
    #
    # Therefore model performs normalization internally.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # BATCH
    # --------------------------------------------------------

    img_array = np.expand_dims(
        img_array,
        axis=0
    )

    # --------------------------------------------------------
    # CHECK
    # --------------------------------------------------------

    expected_shape = (
        1,
        128,
        128,
        3
    )

    if img_array.shape != expected_shape:

        raise ValueError(
            "Prepared image has wrong shape. "
            f"Expected {expected_shape}, "
            f"found {img_array.shape}"
        )

    logger.info(
        "Prepared image shape: %s",
        img_array.shape
    )

    logger.info(
        "Prepared image dtype: %s",
        img_array.dtype
    )

    logger.info(
        "Prepared image range: %.2f - %.2f",
        float(np.min(img_array)),
        float(np.max(img_array))
    )

    return img_array


# ============================================================
# PREDICT IMAGE
# ============================================================

def predict_image(image_path):

    model = load_disease_model()

    if model is None:

        raise RuntimeError(
            MODEL_ERROR
            or
            "Disease model is unavailable."
        )

    # --------------------------------------------------------
    # PREPARE
    # --------------------------------------------------------

    processed_image = prepare_image(
        image_path
    )

    # --------------------------------------------------------
    # PREDICT
    # --------------------------------------------------------

    predictions = model.predict(
        processed_image,
        verbose=0
    )

    # --------------------------------------------------------
    # HANDLE MODEL OUTPUT
    # --------------------------------------------------------

    if isinstance(
        predictions,
        list
    ):

        if len(predictions) == 0:

            raise RuntimeError(
                "The model returned an empty prediction."
            )

        predictions = predictions[0]

    predictions = np.asarray(
        predictions
    ).flatten()

    logger.info(
        "Prediction output shape: %s",
        predictions.shape
    )

    # --------------------------------------------------------
    # EMPTY CHECK
    # --------------------------------------------------------

    if predictions.size == 0:

        raise RuntimeError(
            "The model returned an empty prediction."
        )

    # --------------------------------------------------------
    # CLASS COUNT
    # --------------------------------------------------------

    if predictions.size != len(
        CLASS_NAMES
    ):

        raise RuntimeError(

            "Model output/class mismatch. "

            f"Model returned {predictions.size} "
            f"outputs, but {len(CLASS_NAMES)} "
            "classes are configured."

        )

    # --------------------------------------------------------
    # NUMERIC SAFETY
    # --------------------------------------------------------

    predictions = predictions.astype(
        np.float32
    )

    if not np.all(
        np.isfinite(predictions)
    ):

        raise RuntimeError(
            "The model returned invalid prediction values."
        )

    # --------------------------------------------------------
    # CONVERT TO PROBABILITIES
    #
    # Current model is expected to return probabilities.
    # If output is not probability-like, apply softmax.
    # --------------------------------------------------------

    prediction_sum = float(
        np.sum(predictions)
    )

    prediction_min = float(
        np.min(predictions)
    )

    prediction_max = float(
        np.max(predictions)
    )

    logger.info(
        "Prediction raw range: %.6f - %.6f",
        prediction_min,
        prediction_max
    )

    logger.info(
        "Prediction raw sum: %.6f",
        prediction_sum
    )

    if (
        prediction_min < 0
        or
        prediction_max > 1
        or
        not np.isclose(
            prediction_sum,
            1.0,
            atol=0.05
        )
    ):

        predictions = (
            tf.nn.softmax(
                predictions
            ).numpy()
        )

    else:

        # Safety normalization
        if prediction_sum > 0:

            predictions = (
                predictions
                / prediction_sum
            )

    # --------------------------------------------------------
    # FINAL PROBABILITY CHECK
    # --------------------------------------------------------

    if not np.all(
        np.isfinite(predictions)
    ):

        raise RuntimeError(
            "Invalid probability values generated."
        )

    # --------------------------------------------------------
    # BEST CLASS
    # --------------------------------------------------------

    predicted_index = int(
        np.argmax(
            predictions
        )
    )

    if (
        predicted_index < 0
        or
        predicted_index >= len(
            CLASS_NAMES
        )
    ):

        raise RuntimeError(
            "Invalid predicted class index."
        )

    predicted_class = (
        CLASS_NAMES[
            predicted_index
        ]
    )

    confidence = float(
        predictions[
            predicted_index
        ] * 100
    )

    confidence = round(
        confidence,
        2
    )

    # --------------------------------------------------------
    # TOP 5
    # --------------------------------------------------------

    ranked_indices = np.argsort(
        predictions
    )[::-1]

    top_predictions = []

    for index in ranked_indices[:5]:

        index = int(index)

        class_name = (
            CLASS_NAMES[index]
        )

        info = get_disease_info(
            class_name
        )

        score = float(
            predictions[index] * 100
        )

        top_predictions.append({

            "class":
                class_name,

            "name":
                info[
                    "display_name"
                ],

            "confidence":
                round(
                    score,
                    2
                )
        })

    # --------------------------------------------------------
    # INFORMATION
    # --------------------------------------------------------

    info = get_disease_info(
        predicted_class
    )

    # --------------------------------------------------------
    # RELIABILITY
    # --------------------------------------------------------

    if confidence >= 85:

        reliability = "High"

    elif confidence >= 65:

        reliability = "Medium"

    else:

        reliability = "Low"

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    if "healthy" in predicted_class.lower():

        risk = "Low"

    elif confidence >= 85:

        risk = "High"

    elif confidence >= 65:

        risk = "Medium"

    else:

        risk = "Uncertain"

    # --------------------------------------------------------
    # CROP
    # --------------------------------------------------------

    crop = predicted_class.split(
        "_",
        1
    )[0]

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result = {

        "prediction":
            predicted_class,

        "display_name":
            info[
                "display_name"
            ],

        "confidence":
            confidence,

        "status":
            info[
                "status"
            ],

        "risk":
            risk,

        "severity":
            info[
                "severity"
            ],

        "reliability":
            reliability,

        "crop":
            crop,

        "symptoms":
            info[
                "symptoms"
            ],

        "treatment":
            info[
                "treatment"
            ],

        "prevention":
            info[
                "prevention"
            ],

        "top_predictions":
            top_predictions,

        "model":
            "KisanVision360+ CNN",

        "model_version":
            "disease-model-v1",

        "image_size":
            "128x128",

        "timestamp":
            datetime.utcnow().isoformat()

    }

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    logger.info(
        "Disease prediction: %s | %.2f%%",
        predicted_class,
        confidence
    )

    return result


# ============================================================
# FARMER CHECK
# ============================================================

def farmer_required():

    role = (
        session.get(
            "role",
            ""
        )
        or ""
    )

    return (
        role.lower().strip()
        == "farmer"
    )


# ============================================================
# DISEASE PAGE
# ============================================================

@disease_bp.route(
    "/disease",
    methods=["GET"]
)
def disease():

    if not farmer_required():

        flash(
            "Please login as a farmer to use Disease Detection.",
            "warning"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    return render_template(
        "disease.html"
    )


# ============================================================
# PREDICT DISEASE
# ============================================================

@disease_bp.route(
    "/predict-disease",
    methods=["POST"]
)
def predict_disease():

    if not farmer_required():

        if request.is_json:

            return jsonify({

                "success":
                    False,

                "message":
                    "Farmer login required."

            }), 401

        flash(
            "Please login as a farmer.",
            "warning"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # --------------------------------------------------------
    # GET IMAGE
    # --------------------------------------------------------

    uploaded_file = request.files.get(
        "image"
    )

    if uploaded_file is None:

        uploaded_file = request.files.get(
            "file"
        )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    valid, error = (
        validate_uploaded_file(
            uploaded_file
        )
    )

    if not valid:

        if request.accept_mimetypes.accept_html:

            flash(
                error,
                "danger"
            )

            return redirect(
                url_for(
                    "disease.disease"
                )
            )

        return jsonify({

            "success":
                False,

            "message":
                error

        }), 400

    file_path = None

    try:

        # ----------------------------------------------------
        # SECURE NAME
        # ----------------------------------------------------

        original_name = (
            secure_filename(
                uploaded_file.filename
            )
        )

        if not original_name:

            return jsonify({

                "success":
                    False,

                "message":
                    "Invalid image filename."

            }), 400

        # ----------------------------------------------------
        # UNIQUE NAME
        # ----------------------------------------------------

        timestamp = (
            datetime.utcnow()
            .strftime(
                "%Y%m%d%H%M%S%f"
            )
        )

        filename = (
            f"disease_"
            f"{timestamp}_"
            f"{original_name}"
        )

        file_path = (
            UPLOAD_FOLDER
            / filename
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        uploaded_file.save(
            str(file_path)
        )

        # ----------------------------------------------------
        # SIZE
        # ----------------------------------------------------

        file_size = (
            file_path.stat().st_size
        )

        if file_size > MAX_IMAGE_SIZE_BYTES:

            file_path.unlink(
                missing_ok=True
            )

            return jsonify({

                "success":
                    False,

                "message":
                    (
                        f"Image size must be below "
                        f"{MAX_IMAGE_SIZE_MB} MB."
                    )

            }), 400

        # ----------------------------------------------------
        # PREDICT
        # ----------------------------------------------------

        result = predict_image(
            file_path
        )

        # ----------------------------------------------------
        # IMAGE URL
        # ----------------------------------------------------

        result["image_url"] = url_for(

            "static",

            filename=(
                f"uploads/disease/"
                f"{filename}"
            )

        )

        result["filename"] = (
            filename
        )

        # ----------------------------------------------------
        # HTML
        # ----------------------------------------------------

        if request.accept_mimetypes.accept_html:

            return render_template(

                "disease.html",

                prediction=
                    result[
                        "display_name"
                    ],

                confidence=
                    result[
                        "confidence"
                    ],

                status=
                    result[
                        "status"
                    ],

                symptoms=
                    result[
                        "symptoms"
                    ],

                treatment=
                    result[
                        "treatment"
                    ],

                prevention=
                    result[
                        "prevention"
                    ],

                risk=
                    result[
                        "risk"
                    ],

                severity=
                    result[
                        "severity"
                    ],

                reliability=
                    result[
                        "reliability"
                    ],

                crop=
                    result[
                        "crop"
                    ],

                top_predictions=
                    result[
                        "top_predictions"
                    ],

                image=
                    result[
                        "filename"
                    ],

                image_url=
                    result[
                        "image_url"
                    ],

                disease_result=
                    result

            )

        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        return jsonify({

            "success":
                True,

            "message":
                "Disease prediction completed.",

            "data":
                result

        })

    except Exception as exc:

        logger.exception(
            "Disease prediction failed."
        )

        if file_path is not None:

            try:

                file_path.unlink(
                    missing_ok=True
                )

            except Exception:

                pass

        if request.accept_mimetypes.accept_html:

            flash(

                (
                    "Disease prediction failed: "
                    f"{str(exc)}"
                ),

                "danger"

            )

            return redirect(
                url_for(
                    "disease.disease"
                )
            )

        return jsonify({

            "success":
                False,

            "message":
                "Disease prediction failed.",

            "error":
                str(exc)

        }), 500


# ============================================================
# JSON API
# ============================================================

@disease_bp.route(
    "/api/disease/predict",
    methods=["POST"]
)
def api_predict_disease():

    if not farmer_required():

        return jsonify({

            "success":
                False,

            "message":
                "Farmer login required."

        }), 401

    uploaded_file = request.files.get(
        "image"
    )

    if uploaded_file is None:

        uploaded_file = request.files.get(
            "file"
        )

    valid, error = (
        validate_uploaded_file(
            uploaded_file
        )
    )

    if not valid:

        return jsonify({

            "success":
                False,

            "message":
                error

        }), 400

    file_path = None

    try:

        original_name = (
            secure_filename(
                uploaded_file.filename
            )
        )

        if not original_name:

            return jsonify({

                "success":
                    False,

                "message":
                    "Invalid image filename."

            }), 400

        timestamp = (
            datetime.utcnow()
            .strftime(
                "%Y%m%d%H%M%S%f"
            )
        )

        filename = (
            f"api_disease_"
            f"{timestamp}_"
            f"{original_name}"
        )

        file_path = (
            UPLOAD_FOLDER
            / filename
        )

        uploaded_file.save(
            str(file_path)
        )

        if (
            file_path.stat().st_size
            > MAX_IMAGE_SIZE_BYTES
        ):

            file_path.unlink(
                missing_ok=True
            )

            return jsonify({

                "success":
                    False,

                "message":
                    (
                        f"Image size must be below "
                        f"{MAX_IMAGE_SIZE_MB} MB."
                    )

            }), 400

        result = predict_image(
            file_path
        )

        result["filename"] = (
            filename
        )

        result["image_url"] = url_for(

            "static",

            filename=(
                f"uploads/disease/"
                f"{filename}"
            )

        )

        return jsonify({

            "success":
                True,

            "message":
                "Disease prediction completed.",

            "data":
                result

        })

    except Exception as exc:

        logger.exception(
            "API disease prediction failed."
        )

        if file_path is not None:

            try:

                file_path.unlink(
                    missing_ok=True
                )

            except Exception:

                pass

        return jsonify({

            "success":
                False,

            "message":
                "Prediction failed.",

            "error":
                str(exc)

        }), 500


# ============================================================
# CLASSES API
# ============================================================

@disease_bp.route(
    "/api/disease/classes",
    methods=["GET"]
)
def disease_classes():

    classes = []

    for class_name in CLASS_NAMES:

        info = get_disease_info(
            class_name
        )

        classes.append({

            "id":
                class_name,

            "name":
                info[
                    "display_name"
                ],

            "status":
                info[
                    "status"
                ],

            "risk":
                info[
                    "risk"
                ]

        })

    return jsonify({

        "success":
            True,

        "count":
            len(classes),

        "classes":
            classes

    })


# ============================================================
# SINGLE DISEASE DETAILS
# ============================================================

@disease_bp.route(
    "/api/disease/<path:disease_name>",
    methods=["GET"]
)
def disease_details(
    disease_name
):

    disease_name = (
        disease_name
        .strip()
    )

    if disease_name not in CLASS_NAMES:

        return jsonify({

            "success":
                False,

            "message":
                "Disease class not found."

        }), 404

    info = get_disease_info(
        disease_name
    )

    return jsonify({

        "success":
            True,

        "data": {

            "id":
                disease_name,

            **info

        }

    })


# ============================================================
# MODEL HEALTH
# ============================================================

@disease_bp.route(
    "/api/disease/health",
    methods=["GET"]
)
def disease_health():

    model_exists = (
        MODEL_PATH.exists()
    )

    model_loaded = (
        MODEL is not None
    )

    # Load model for health check
    if (
        model_exists
        and not model_loaded
    ):

        load_disease_model()

        model_loaded = (
            MODEL is not None
        )

    actual_input_shape = None
    actual_output_shape = None
    actual_output_classes = None

    if MODEL is not None:

        try:

            actual_input_shape = (
                list(
                    MODEL.input_shape
                )
                if isinstance(
                    MODEL.input_shape,
                    tuple
                )
                else str(
                    MODEL.input_shape
                )
            )

        except Exception:

            pass

        try:

            actual_output_shape = (
                list(
                    MODEL.output_shape
                )
                if isinstance(
                    MODEL.output_shape,
                    tuple
                )
                else str(
                    MODEL.output_shape
                )
            )

        except Exception:

            pass

        try:

            shape = MODEL.output_shape

            if isinstance(
                shape,
                list
            ):
                shape = shape[0]

            actual_output_classes = (
                shape[-1]
            )

        except Exception:

            pass

    return jsonify({

        "success":
            (
                model_exists
                and model_loaded
                and actual_output_classes
                == len(CLASS_NAMES)
            ),

        "service":
            "Disease Detection",

        "model_exists":
            model_exists,

        "model_loaded":
            model_loaded,

        "tensorflow_available":
            TENSORFLOW_AVAILABLE,

        "model_path":
            str(MODEL_PATH),

        "configured_classes":
            len(CLASS_NAMES),

        "actual_model_output_classes":
            actual_output_classes,

        "configured_input_size":
            list(IMG_SIZE),

        "actual_model_input_shape":
            actual_input_shape,

        "actual_model_output_shape":
            actual_output_shape,

        "error":
            MODEL_ERROR

    })


# ============================================================
# SIMPLE TEST
# ============================================================

@disease_bp.route(
    "/api/disease/test",
    methods=["GET"]
)
def disease_test():

    return jsonify({

        "success":
            True,

        "service":
            "KisanVision360+ Disease Detection",

        "message":
            "Disease route is working.",

        "classes":
            len(CLASS_NAMES),

        "model_path":
            str(MODEL_PATH),

        "model_exists":
            MODEL_PATH.exists(),

        "tensorflow_available":
            TENSORFLOW_AVAILABLE

    })


# ============================================================
# INTELLIGENCE SUMMARY
# ============================================================

@disease_bp.route(
    "/api/disease/intelligence",
    methods=["POST"]
)
def disease_intelligence():

    if not farmer_required():

        return jsonify({

            "success":
                False,

            "message":
                "Farmer login required."

        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    prediction = str(
        data.get(
            "prediction",
            ""
        )
    ).strip()

    try:

        confidence = float(
            data.get(
                "confidence",
                0
            )
            or 0
        )

    except (
        TypeError,
        ValueError
    ):

        confidence = 0

    if prediction not in CLASS_NAMES:

        return jsonify({

            "success":
                False,

            "message":
                "Invalid disease class."

        }), 400

    confidence = max(
        0,
        min(
            100,
            confidence
        )
    )

    info = get_disease_info(
        prediction
    )

    if "healthy" in prediction.lower():

        priority = (
            "Routine Monitoring"
        )

    elif confidence >= 85:

        priority = (
            "Immediate Field Inspection"
        )

    elif confidence >= 65:

        priority = (
            "Inspect Within 24 Hours"
        )

    else:

        priority = (
            "Manual Verification Recommended"
        )

    return jsonify({

        "success":
            True,

        "data": {

            "disease":
                info[
                    "display_name"
                ],

            "confidence":
                confidence,

            "risk":
                info[
                    "risk"
                ],

            "priority":
                priority,

            "recommended_actions":
                info[
                    "treatment"
                ],

            "prevention":
                info[
                    "prevention"
                ],

            "next_step":
                (
                    "For severe or uncertain cases, "
                    "confirm the diagnosis with a "
                    "qualified agricultural expert."
                )

        }

    })


# ============================================================
# PRELOAD MODEL
# ============================================================

def initialize_disease_service():

    try:

        model = (
            load_disease_model()
        )

        return (
            model is not None
        )

    except Exception:

        logger.exception(
            "Disease service initialization failed."
        )

        return False


# ============================================================
# END
# ============================================================