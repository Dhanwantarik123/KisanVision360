# ============================================================
# KISANVISION360+
# GOVERNMENT SCHEME INTELLIGENCE SERVICE
# ============================================================

from typing import Any, Dict, List, Optional


# ============================================================
# SCHEME DATABASE
# ============================================================

SCHEMES: List[Dict[str, Any]] = [

    {
        "name": "PM-KISAN",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Financial support for eligible farmer families.",
        "eligibility":
            "Eligible farmer families.",
        "category":
            "Financial Support",
        "farmer_need":
            "income support",
        "benefit_type":
            "Financial Assistance",
        "link":
            "https://pmkisan.gov.in/",
        "official":
            True
    },

    {
        "name":
            "Pradhan Mantri Fasal Bima Yojana",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Crop insurance against eligible crop losses.",
        "eligibility":
            "Eligible farmers growing notified crops.",
        "category":
            "Crop Insurance",
        "farmer_need":
            "crop protection",
        "benefit_type":
            "Crop Insurance",
        "link":
            "https://pmfby.gov.in/",
        "official":
            True
    },

    {
        "name":
            "Kisan Credit Card",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Credit support for agricultural activities.",
        "eligibility":
            "Eligible farmers.",
        "category":
            "Credit & Finance",
        "farmer_need":
            "farm credit",
        "benefit_type":
            "Credit",
        "link":
            "https://www.myscheme.gov.in/",
        "official":
            True
    },

    {
        "name":
            "Pradhan Mantri Krishi Sinchayee Yojana",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Support for irrigation and water management.",
        "eligibility":
            "Eligible farmers.",
        "category":
            "Irrigation",
        "farmer_need":
            "water management",
        "benefit_type":
            "Irrigation Support",
        "link":
            "https://pmksy.gov.in/",
        "official":
            True
    },

    {
        "name":
            "Soil Health Card Scheme",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Soil testing and fertilizer recommendations.",
        "eligibility":
            "Farmers.",
        "category":
            "Soil & Fertilizer",
        "farmer_need":
            "soil health",
        "benefit_type":
            "Soil Testing",
        "link":
            "https://soilhealth.dac.gov.in/",
        "official":
            True
    },

    {
        "name":
            "e-NAM",
        "department":
            "Government of India",
        "purpose":
            "Online agricultural marketplace connecting farmers and traders.",
        "eligibility":
            "Farmers and traders.",
        "category":
            "Marketing",
        "farmer_need":
            "selling produce",
        "benefit_type":
            "Market Access",
        "link":
            "https://enam.gov.in/",
        "official":
            True
    },

    {
        "name":
            "PM-KUSUM",
        "department":
            "Ministry of New and Renewable Energy",
        "purpose":
            "Promotes solar energy and solar pumps for agriculture.",
        "eligibility":
            "Eligible farmers.",
        "category":
            "Solar & Energy",
        "farmer_need":
            "solar irrigation",
        "benefit_type":
            "Solar Energy",
        "link":
            "https://pmkusum.mnre.gov.in/",
        "official":
            True
    },

    {
        "name":
            "Agriculture Infrastructure Fund",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Support for agricultural infrastructure such as storage and processing.",
        "eligibility":
            "Eligible farmers, FPOs and agricultural projects.",
        "category":
            "Infrastructure",
        "farmer_need":
            "farm infrastructure",
        "benefit_type":
            "Infrastructure Finance",
        "link":
            "https://agriinfra.dac.gov.in/",
        "official":
            True
    },

    {
        "name":
            "National Food Security Mission",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Improves production of rice, wheat, pulses and other crops.",
        "eligibility":
            "Eligible farmers.",
        "category":
            "Crop Development",
        "farmer_need":
            "crop productivity",
        "benefit_type":
            "Production Support",
        "link":
            "https://nfsm.gov.in/",
        "official":
            True
    },

    {
        "name":
            "Paramparagat Krishi Vikas Yojana",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Promotes organic and sustainable farming.",
        "eligibility":
            "Eligible farmers and farmer groups.",
        "category":
            "Organic Farming",
        "farmer_need":
            "organic farming",
        "benefit_type":
            "Sustainable Farming",
        "link":
            "https://pgsindia-ncof.gov.in/",
        "official":
            True
    },

    {
        "name":
            "Mission for Integrated Development of Horticulture",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Provides support for fruits, vegetables and horticulture development.",
        "eligibility":
            "Horticulture farmers.",
        "category":
            "Horticulture",
        "farmer_need":
            "horticulture",
        "benefit_type":
            "Horticulture Support",
        "link":
            "https://midh.gov.in/",
        "official":
            True
    },

    {
        "name":
            "National Mission for Sustainable Agriculture",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Promotes sustainable and climate-resilient agriculture.",
        "eligibility":
            "Eligible farmers.",
        "category":
            "Sustainable Agriculture",
        "farmer_need":
            "climate resilience",
        "benefit_type":
            "Sustainable Agriculture",
        "link":
            "https://nmsa.dac.gov.in/",
        "official":
            True
    },

    {
        "name":
            "Sub-Mission on Agricultural Mechanization",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Promotes access to modern agricultural machinery.",
        "eligibility":
            "Eligible farmers and agricultural groups.",
        "category":
            "Farm Machinery",
        "farmer_need":
            "agricultural machinery",
        "benefit_type":
            "Mechanization Support",
        "link":
            "https://agrimachinery.nic.in/",
        "official":
            True
    },

    {
        "name":
            "Rashtriya Krishi Vikas Yojana",
        "department":
            "Ministry of Agriculture & Farmers Welfare",
        "purpose":
            "Supports agriculture development and related projects.",
        "eligibility":
            "Eligible agricultural projects and farmers.",
        "category":
            "Agriculture Development",
        "farmer_need":
            "agriculture development",
        "benefit_type":
            "Development Support",
        "link":
            "https://rkvy.nic.in/",
        "official":
            True
    }

]


# ============================================================
# GET ALL SCHEMES
# ============================================================

def get_schemes() -> List[Dict[str, Any]]:
    """
    Backward-compatible function.

    Existing route:
        schemes = get_schemes()
    """

    return [
        dict(scheme)
        for scheme in SCHEMES
    ]


# ============================================================
# GET SCHEME BY NAME
# ============================================================

def get_scheme(
    scheme_name: str
) -> Optional[Dict[str, Any]]:

    if not scheme_name:

        return None


    search_name = scheme_name.strip().lower()


    for scheme in SCHEMES:

        if (
            scheme["name"]
            .lower()
            ==
            search_name
        ):

            return dict(
                scheme
            )


    return None


# ============================================================
# SEARCH SCHEMES
# ============================================================

def search_schemes(
    query: str
) -> List[Dict[str, Any]]:

    if not query:

        return get_schemes()


    query = query.strip().lower()


    results = []


    for scheme in SCHEMES:

        searchable_text = " ".join(
            [

                scheme.get(
                    "name",
                    ""
                ),

                scheme.get(
                    "department",
                    ""
                ),

                scheme.get(
                    "purpose",
                    ""
                ),

                scheme.get(
                    "eligibility",
                    ""
                ),

                scheme.get(
                    "category",
                    ""
                ),

                scheme.get(
                    "farmer_need",
                    ""
                ),

                scheme.get(
                    "benefit_type",
                    ""
                )

            ]
        ).lower()


        if query in searchable_text:

            results.append(
                dict(
                    scheme
                )
            )


    return results


# ============================================================
# CATEGORY FILTER
# ============================================================

def get_schemes_by_category(
    category: str
) -> List[Dict[str, Any]]:

    if not category:

        return get_schemes()


    category = category.strip().lower()


    return [

        dict(scheme)

        for scheme in SCHEMES

        if
        scheme.get(
            "category",
            ""
        ).lower()
        ==
        category

    ]


# ============================================================
# FARMER NEED RECOMMENDATION
# ============================================================

def recommend_schemes(
    farmer_need: str
) -> List[Dict[str, Any]]:

    """
    Finds schemes related to a farmer's requirement.

    This is a recommendation/ranking function,
    NOT an eligibility verification system.
    """

    if not farmer_need:

        return []


    query = farmer_need.strip().lower()


    scored = []


    for scheme in SCHEMES:

        score = 0


        fields = [

            scheme.get(
                "name",
                ""
            ),

            scheme.get(
                "purpose",
                ""
            ),

            scheme.get(
                "category",
                ""
            ),

            scheme.get(
                "farmer_need",
                ""
            ),

            scheme.get(
                "benefit_type",
                ""
            )

        ]


        for field in fields:

            if query in field.lower():

                score += 3


        # Related keyword matching

        keywords = {

            "water": [
                "irrigation",
                "water",
                "solar"
            ],

            "irrigation": [
                "irrigation",
                "water",
                "solar"
            ],

            "machine": [
                "machinery",
                "mechanization"
            ],

            "machinery": [
                "machinery",
                "mechanization"
            ],

            "finance": [
                "financial",
                "credit",
                "finance"
            ],

            "loan": [
                "credit",
                "finance"
            ],

            "crop": [
                "crop",
                "production",
                "insurance"
            ],

            "insurance": [
                "insurance",
                "crop protection"
            ],

            "organic": [
                "organic",
                "sustainable"
            ],

            "market": [
                "market",
                "selling"
            ],

            "solar": [
                "solar",
                "energy",
                "irrigation"
            ],

            "soil": [
                "soil",
                "fertilizer"
            ]

        }


        related = keywords.get(
                query,
                []
            )


        for keyword in related:

            combined = " ".join(
                    fields
                ).lower()


            if keyword in combined:

                score += 2


        if score > 0:

            scored.append(
                (
                    score,
                    scheme
                )
            )


    scored.sort(
        key=lambda item:
            item[0],
        reverse=True
    )


    results = []


    for score, scheme in scored:

        item = dict(
                scheme
            )

        item[
            "recommendation_score"
        ] = min(
            score,
            100
        )

        results.append(
            item
        )


    return results


# ============================================================
# FARM MACHINERY SCHEMES
# ============================================================

def get_machinery_schemes():

    return get_schemes_by_category(
        "Farm Machinery"
    )


# ============================================================
# FINANCIAL SCHEMES
# ============================================================

def get_financial_schemes():

    categories = {

        "Financial Support",

        "Credit & Finance",

        "Infrastructure"

    }


    return [

        dict(scheme)

        for scheme in SCHEMES

        if scheme.get(
            "category"
        ) in categories

    ]


# ============================================================
# IRRIGATION SCHEMES
# ============================================================

def get_irrigation_schemes():

    categories = {

        "Irrigation",

        "Solar & Energy"

    }


    return [

        dict(scheme)

        for scheme in SCHEMES

        if scheme.get(
            "category"
        ) in categories

    ]


# ============================================================
# MARKET-RELATED SCHEMES
# ============================================================

def get_market_schemes():

    return get_schemes_by_category(
        "Marketing"
    )


# ============================================================
# HORTICULTURE SCHEMES
# ============================================================

def get_horticulture_schemes():

    return get_schemes_by_category(
        "Horticulture"
    )


# ============================================================
# SCHEME CATEGORIES
# ============================================================

def get_scheme_categories() -> List[str]:

    categories = sorted({

        scheme.get(
            "category",
            "Other"
        )

        for scheme in SCHEMES

    })


    return categories


# ============================================================
# SCHEME STATISTICS
# ============================================================

def get_scheme_statistics() -> Dict[str, Any]:

    schemes = get_schemes()


    categories = get_scheme_categories()


    departments = {

        scheme.get(
            "department",
            ""
        )

        for scheme in schemes

    }


    official_count = sum(

        1

        for scheme in schemes

        if scheme.get(
            "official"
        )

    )


    return {

        "total":
            len(
                schemes
            ),

        "categories":
            len(
                categories
            ),

        "departments":
            len(
                departments
            ),

        "official_links":
            official_count

    }


# ============================================================
# VERIFY OFFICIAL LINK
# ============================================================

def is_official_scheme(
    scheme: Dict[str, Any]
) -> bool:

    return bool(
        scheme.get(
            "official",
            False
        )
        and
        scheme.get(
            "link"
        )
    )


# ============================================================
# SAFE SCHEME SUMMARY
# ============================================================

def get_scheme_summary(
    scheme_name: str
) -> Optional[Dict[str, Any]]:

    scheme = get_scheme(
            scheme_name
        )


    if not scheme:

        return None


    return {

        "name":
            scheme["name"],

        "category":
            scheme.get(
                "category"
            ),

        "department":
            scheme.get(
                "department"
            ),

        "purpose":
            scheme.get(
                "purpose"
            ),

        "eligibility":
            scheme.get(
                "eligibility"
            ),

        "benefit_type":
            scheme.get(
                "benefit_type"
            ),

        "official_link":
            scheme.get(
                "link"
            ),

        "verification_required":
            True

    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [

    "get_schemes",

    "get_scheme",

    "search_schemes",

    "get_schemes_by_category",

    "recommend_schemes",

    "get_machinery_schemes",

    "get_financial_schemes",

    "get_irrigation_schemes",

    "get_market_schemes",

    "get_horticulture_schemes",

    "get_scheme_categories",

    "get_scheme_statistics",

    "is_official_scheme",

    "get_scheme_summary"

]


# ============================================================
# END
# ============================================================

