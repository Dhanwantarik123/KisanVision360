# ============================================================
# KISANVISION360+
# GOVERNMENT SCHEME INTELLIGENCE ROUTES
# ============================================================

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session
)

from utils.schemes import (
    get_schemes,
    get_scheme,
    search_schemes,
    get_schemes_by_category,
    recommend_schemes,
    get_scheme_categories,
    get_scheme_statistics,
    is_official_scheme
)

import logging


# ============================================================
# BLUEPRINT
# ============================================================

government_bp = Blueprint(
    "government",
    __name__
)

logger = logging.getLogger(__name__)


# ============================================================
# PREPARE SCHEME FOR HTML
# ============================================================

def prepare_scheme(scheme):

    item = dict(scheme)

    # Your database uses "purpose".
    # HTML can use "benefit".
    item["benefit"] = item.get(
        "purpose",
        ""
    )

    # Smart discovery score.
    category = item.get(
        "category",
        ""
    ).lower()

    score_map = {

        "financial support": 92,

        "crop insurance": 90,

        "credit & finance": 88,

        "irrigation": 87,

        "solar & energy": 86,

        "soil & fertilizer": 84,

        "marketing": 84,

        "farm machinery": 82,

        "horticulture": 81,

        "organic farming": 80,

        "natural farming": 80,

        "sustainable agriculture": 80,

        "livestock": 78,

        "fisheries": 78,

        "crop development": 78,

        "crop protection": 78,

        "infrastructure": 80,

        "agriculture development": 76,

        "farmer organization": 76,

        "allied agriculture": 75

    }

    item["match_score"] = score_map.get(
        category,
        75
    )

    item["official_verified"] = (
        is_official_scheme(item)
    )

    return item


# ============================================================
# PREPARE ALL SCHEMES
# ============================================================

def prepare_schemes(schemes):

    return [
        prepare_scheme(scheme)
        for scheme in schemes
    ]


# ============================================================
# GOVERNMENT PAGE
# ============================================================

@government_bp.route(
    "/government"
)
def government():

    try:

        schemes = get_schemes()

        # Search
        search = request.args.get(
            "search",
            ""
        ).strip()

        # Category
        category = request.args.get(
            "category",
            ""
        ).strip()

        # Apply search
        if search:

            schemes = search_schemes(
                search
            )

        # Apply category
        if category and category.lower() != "all":

            schemes = [
                scheme
                for scheme in schemes
                if scheme.get(
                    "category",
                    ""
                ).lower()
                == category.lower()
            ]

        schemes = prepare_schemes(
            schemes
        )

        categories = get_scheme_categories()

        statistics = get_scheme_statistics()

        # ----------------------------------------------------
        # FARMER PROFILE
        # ----------------------------------------------------

        farmer_name = session.get(
            "name",
            "किसान"
        )

        farmer_role = session.get(
            "role",
            "farmer"
        )

        farmer_state = session.get(
            "state",
            "Maharashtra"
        )

        farmer_district = session.get(
            "district",
            "Nagpur"
        )

        profile = {

            "name":
                farmer_name,

            "role":
                farmer_role,

            "state":
                farmer_state,

            "district":
                farmer_district

        }

        # ----------------------------------------------------
        # RENDER
        # ----------------------------------------------------

        return render_template(

            "government.html",

            schemes=schemes,

            categories=categories,

            profile=profile,

            statistics=statistics,

            total_schemes=len(
                schemes
            ),

            search_query=search,

            selected_category=category

        )

    except Exception as e:

        logger.exception(
            "Government page error"
        )

        return render_template(

            "government.html",

            schemes=[],

            categories=[],

            profile={},

            statistics={

                "total": 0,

                "categories": 0,

                "departments": 0,

                "official_links": 0

            },

            total_schemes=0,

            search_query="",

            selected_category="",

            error=str(e)

        )


# ============================================================
# API - ALL SCHEMES
# ============================================================

@government_bp.route(
    "/api/government/schemes"
)
def government_schemes_api():

    try:

        search = request.args.get(
            "search",
            ""
        ).strip()

        category = request.args.get(
            "category",
            ""
        ).strip()

        schemes = get_schemes()

        # Search
        if search:

            schemes = search_schemes(
                search
            )

        # Category
        if category and category.lower() != "all":

            schemes = [
                scheme
                for scheme in schemes
                if scheme.get(
                    "category",
                    ""
                ).lower()
                == category.lower()
            ]

        schemes = prepare_schemes(
            schemes
        )

        return jsonify({

            "success":
                True,

            "count":
                len(schemes),

            "schemes":
                schemes

        })

    except Exception as e:

        logger.exception(
            "Government schemes API error"
        )

        return jsonify({

            "success":
                False,

            "count":
                0,

            "schemes":
                [],

            "error":
                str(e)

        }), 500


# ============================================================
# API - SINGLE SCHEME
# ============================================================

@government_bp.route(
    "/api/government/schemes/<string:scheme_name>"
)
def government_scheme_detail(
    scheme_name
):

    try:

        scheme = get_scheme(
            scheme_name
        )

        if not scheme:

            return jsonify({

                "success":
                    False,

                "message":
                    "Scheme not found"

            }), 404

        scheme = prepare_scheme(
            scheme
        )

        return jsonify({

            "success":
                True,

            "scheme":
                scheme

        })

    except Exception as e:

        logger.exception(
            "Scheme detail error"
        )

        return jsonify({

            "success":
                False,

            "message":
                str(e)

        }), 500


# ============================================================
# API - CATEGORIES
# ============================================================

@government_bp.route(
    "/api/government/categories"
)
def government_categories_api():

    try:

        categories = get_scheme_categories()

        return jsonify({

            "success":
                True,

            "categories":
                categories

        })

    except Exception as e:

        return jsonify({

            "success":
                False,

            "categories":
                [],

            "error":
                str(e)

        }), 500


# ============================================================
# API - RECOMMENDATIONS
# ============================================================

@government_bp.route(
    "/api/government/recommendations"
)
def government_recommendations_api():

    try:

        need = request.args.get(
            "need",
            ""
        ).strip()

        if not need:

            return jsonify({

                "success":
                    True,

                "count":
                    0,

                "recommendations":
                    []

            })

        recommendations = recommend_schemes(
            need
        )

        recommendations = prepare_schemes(
            recommendations
        )

        return jsonify({

            "success":
                True,

            "count":
                len(
                    recommendations
                ),

            "recommendations":
                recommendations

        })

    except Exception as e:

        logger.exception(
            "Recommendation API error"
        )

        return jsonify({

            "success":
                False,

            "count":
                0,

            "recommendations":
                [],

            "error":
                str(e)

        }), 500


# ============================================================
# API - STATISTICS
# ============================================================

@government_bp.route(
    "/api/government/statistics"
)
def government_statistics_api():

    try:

        statistics = get_scheme_statistics()

        return jsonify({

            "success":
                True,

            "statistics":
                statistics

        })

    except Exception as e:

        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# API - HEALTH
# ============================================================

@government_bp.route(
    "/api/government/health"
)
def government_health():

    try:

        schemes = get_schemes()

        return jsonify({

            "success":
                True,

            "status":
                "healthy",

            "scheme_count":
                len(schemes),

            "message":
                "Government Scheme Intelligence Service is working."

        })

    except Exception as e:

        return jsonify({

            "success":
                False,

            "status":
                "error",

            "scheme_count":
                0,

            "error":
                str(e)

        }), 500