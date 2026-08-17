def disease_details(disease):

    diseases = {


    "Mosaic Virus":{

        "status":"Disease Detected",

        "symptoms":
        "Yellow mosaic patterns, leaf curling, reduced plant growth",

        "treatment":
        "Remove infected plants. Control virus vectors like whiteflies. Use healthy seeds.",

        "prevention":
        "Use resistant varieties, maintain field hygiene and control insects."

    },



    "powdery_mildew":{

        "status":"Disease Detected",

        "symptoms":
        "White powder-like patches on leaves and stems",

        "treatment":
        "Apply sulfur-based fungicide and improve air circulation.",

        "prevention":
        "Avoid excess moisture and maintain proper plant spacing."

    },



    "septoria":{

        "status":"Disease Detected",

        "symptoms":
        "Brown spots with yellow borders on leaves",

        "treatment":
        "Remove infected leaves and apply recommended fungicide.",

        "prevention":
        "Practice crop rotation and avoid overhead irrigation."

    },



    "bacterial_blight":{

        "status":"Disease Detected",

        "symptoms":
        "Water-soaked spots and leaf drying",

        "treatment":
        "Use copper-based bactericide and remove infected parts.",

        "prevention":
        "Use disease-free seeds and maintain field cleanliness."

    },



    "brown_spot":{

        "status":"Disease Detected",

        "symptoms":
        "Brown circular spots on leaves",

        "treatment":
        "Apply suitable fungicide and improve nutrition.",

        "prevention":
        "Balanced fertilizer use and proper irrigation."

    },



    "Yellow Mosaic":{

        "status":"Disease Detected",

        "symptoms":
        "Yellow patches and distorted leaves",

        "treatment":
        "Control whiteflies and remove affected plants.",

        "prevention":
        "Use resistant seeds and insect control methods."

    },



    "Southern blight":{

        "status":"Disease Detected",

        "symptoms":
        "Stem rot and yellowing leaves",

        "treatment":
        "Apply fungicide and remove infected plant debris.",

        "prevention":
        "Crop rotation and proper soil management."

    },


    "Healthy":{

        "status":"No Disease",

        "symptoms":
        "Plant appears healthy",

        "treatment":
        "No treatment required",

        "prevention":
        "Continue regular monitoring."

    }


    }



    return diseases.get(
        disease,
        {

        "status":"Unknown Disease",

        "symptoms":"Unable to identify symptoms",

        "treatment":"Consult agriculture expert",

        "prevention":"Maintain proper crop management"

        }

    )