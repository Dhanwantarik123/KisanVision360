from flask import Blueprint, render_template
import requests

government_bp = Blueprint("government", __name__)

# Home
@government_bp.route("/government")
def government():

    schemes = [

        {
            "name":"PM-KISAN",
            "benefit":"₹6000 per year",
            "eligibility":"All eligible farmers"
        },

        {
            "name":"PMFBY",
            "benefit":"Crop Insurance",
            "eligibility":"Registered Farmers"
        },

        {
            "name":"Kisan Credit Card",
            "benefit":"Low Interest Loan",
            "eligibility":"Farmers"
        },

        {
            "name":"Soil Health Card",
            "benefit":"Free Soil Report",
            "eligibility":"All Farmers"
        },

        {
            "name":"PM Kusum",
            "benefit":"Solar Pump Subsidy",
            "eligibility":"Farmers"
        }

    ]

    return render_template(
        "government/schemes.html",
        schemes=schemes
    )


# Eligibility Page
@government_bp.route("/government/eligibility")
def eligibility():

    return render_template(
        "government/eligibility.html"
    )


# Subsidy Page
@government_bp.route("/government/subsidy")
def subsidy():

    return render_template(
        "government/subsidy.html"
    )


# Government API
@government_bp.route("/government/api")
def api():

    data = {

        "status":"success",

        "schemes":[

            "PM-KISAN",

            "PMFBY",

            "KCC",

            "PM Kusum",

            "Soil Health Card"

        ]

    }

    return data
