# =========================================================
# DISEASE DETAILS
# =========================================================

def disease_details(disease):

    diseases = {

        # =================================================
        # BACTERIAL BLIGHT
        # =================================================

        "bacterial_blight": {

            "status": "Disease Detected",

            "symptoms":
            "Water-soaked spots, brown lesions, leaf drying and yellowing may appear on cotton leaves.",

            "treatment":
            "Remove severely infected plant parts and follow recommended crop-specific bacterial disease management practices.",

            "prevention":
            "Use healthy seeds, maintain field sanitation, avoid unnecessary leaf wetness and monitor the crop regularly."
        },


        # =================================================
        # CURL VIRUS
        # =================================================

        "curl_virus": {

            "status": "Disease Detected",

            "symptoms":
            "Leaves may curl, become distorted and show yellowing. Plant growth may also be reduced.",

            "treatment":
            "Remove severely infected plants and control insect vectors such as whiteflies according to agricultural recommendations.",

            "prevention":
            "Use healthy planting material, monitor whiteflies and maintain good field hygiene."
        },


        # =================================================
        # FUSARIUM WILT
        # =================================================

        "fussarium_wilt": {

            "status": "Disease Detected",

            "symptoms":
            "Leaves may turn yellow, wilt and dry. The plant may show reduced growth and vascular discoloration.",

            "treatment":
            "Remove severely affected plants and follow crop-specific wilt management practices recommended by agricultural experts.",

            "prevention":
            "Use healthy and disease-free planting material, practice crop rotation and maintain proper field sanitation."
        },


        # =================================================
        # HEALTHY
        # =================================================

        "healthy": {

            "status": "No Disease",

            "symptoms":
            "The cotton leaf appears healthy without major visible disease symptoms.",

            "treatment":
            "No disease treatment is required. Continue normal crop care.",

            "prevention":
            "Continue regular monitoring, proper irrigation, balanced nutrition and good field management."
        }

    }


    # =====================================================
    # RETURN INFORMATION
    # =====================================================

    return diseases.get(

        disease,

        {

            "status": "Unknown Disease",

            "symptoms":
            "Disease symptoms information is not available.",

            "treatment":
            "Please consult an agricultural expert for proper diagnosis and treatment.",

            "prevention":
            "Monitor the crop regularly and maintain good field hygiene."
        }

    )