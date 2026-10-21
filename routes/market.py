
"""
KisanVision360+
Market / Mandi Module

Live market-price integration through:
https://api.data.gov.in/resource
"""

import logging

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session,
    redirect,
    url_for
)

from utils.mandi_price import (
    get_crop_prices,
    get_market_price,
    filter_market_prices,
    calculate_market_summary,
    market_api_health
)


logger = logging.getLogger(__name__)


# ============================================================
# BLUEPRINT
# ============================================================

market_bp = Blueprint(
    "market",
    __name__
)


# ============================================================
# DEFAULT LOCATION
# ============================================================

DEFAULT_STATE = "Maharashtra"
DEFAULT_DISTRICT = "Nagpur"


# ============================================================
# HELPERS
# ============================================================

def _role():
    return str(
        session.get("role", "")
    ).strip().lower()


def _is_logged_in():
    return bool(
        session.get("user_id")
        or session.get("logged_in")
        or session.get("name")
    )


def _require_login():
    """
    Redirect to login when user is not logged in.
    """

    if not _is_logged_in():
        return redirect(
            url_for("auth.login")
        )

    return None


def _safe_float(value):
    try:
        if value is None:
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


# ============================================================
# MARKET PAGE
# ============================================================

@market_bp.route(
    "/market",
    methods=["GET"]
)
def market():

    login_redirect = _require_login()

    if login_redirect:
        return login_redirect

    crop = request.args.get(
        "crop",
        ""
    ).strip()

    state = request.args.get(
        "state",
        DEFAULT_STATE
    ).strip()

    district = request.args.get(
        "district",
        DEFAULT_DISTRICT
    ).strip()

    market_name = request.args.get(
        "market",
        ""
    ).strip()

    # --------------------------------------------------------
    # Fetch market data
    # --------------------------------------------------------

    records = []

    api_error = None

    try:

        if crop:
            records = get_market_price(
                crop=crop
            )

        else:
            records = get_crop_prices(
                state=state,
                district=district,
                limit=100
            )

        # Additional local filtering.
        records = filter_market_prices(
            records,
            crop=crop,
            state=state,
            district=district,
            market=market_name
        )

    except Exception as exc:

        logger.exception(
            "Market page error: %s",
            exc
        )

        api_error = (
            "Unable to fetch market prices "
            "from Data.gov.in."
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = calculate_market_summary(
        records
    )

    # --------------------------------------------------------
    # Unique crops / markets
    # --------------------------------------------------------

    crops = sorted(
        {
            item.get("crop", "")
            for item in records
            if item.get("crop")
        }
    )

    markets = sorted(
        {
            item.get("market", "")
            for item in records
            if item.get("market")
        }
    )

    return render_template(
        "market.html",

        prices=records,

        market_prices=records,

        records=records,

        summary=summary,

        crops=crops,

        markets=markets,

        selected_crop=crop,

        selected_state=state,

        selected_district=district,

        selected_market=market_name,

        api_error=api_error,

        source="data.gov.in",

        role=_role(),

        name=session.get(
            "name",
            "Farmer"
        ),

        language=session.get(
            "language",
            "en"
        ),

        notification_count=session.get(
            "notification_count",
            0
        )
    )


# ============================================================
# API: MARKET PRICES
# ============================================================

@market_bp.route(
    "/api/market/prices",
    methods=["GET"]
)
def api_market_prices():

    login_redirect = _require_login()

    if login_redirect:
        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    crop = request.args.get(
        "crop",
        ""
    ).strip()

    state = request.args.get(
        "state",
        ""
    ).strip()

    district = request.args.get(
        "district",
        ""
    ).strip()

    market_name = request.args.get(
        "market",
        ""
    ).strip()

    try:

        records = get_crop_prices(
            crop=crop or None,
            state=state or None,
            district=district or None,
            market=market_name or None,
            limit=100
        )

        records = filter_market_prices(
            records,
            crop=crop,
            state=state,
            district=district,
            market=market_name
        )

        summary = calculate_market_summary(
            records
        )

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "count": len(records),
            "prices": records,
            "summary": summary
        })

    except Exception as exc:

        logger.exception(
            "Market price API error: %s",
            exc
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to fetch market prices."
            )
        }), 500


# ============================================================
# API: ONE CROP
# ============================================================

@market_bp.route(
    "/api/market/price/<path:crop>",
    methods=["GET"]
)
def api_single_crop_price(crop):

    login_redirect = _require_login()

    if login_redirect:
        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    try:

        records = get_market_price(
            crop=crop
        )

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crop": crop,
            "count": len(records),
            "prices": records
        })

    except Exception as exc:

        logger.exception(
            "Single crop market API error: %s",
            exc
        )

        return jsonify({
            "success": False,
            "message": "Unable to fetch crop price."
        }), 500


# ============================================================
# API: MARKET INTELLIGENCE
# ============================================================

@market_bp.route(
    "/api/market/intelligence",
    methods=["GET"]
)
def api_market_intelligence():

    login_redirect = _require_login()

    if login_redirect:
        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    crop = request.args.get(
        "crop",
        ""
    ).strip()

    try:

        records = get_market_price(
            crop=crop or None
        )

        if not records:

            return jsonify({
                "success": True,
                "source": "data.gov.in",
                "crop": crop,
                "records": 0,
                "message": (
                    "No market-price records "
                    "were returned."
                ),
                "intelligence": {
                    "trend": "No data",
                    "signal": "Unavailable",
                    "advice": (
                        "Try another crop or market."
                    )
                }
            })

        summary = calculate_market_summary(
            records
        )

        modal_values = [
            item["modal_price"]
            for item in records
            if item.get("modal_price") is not None
        ]

        trend = "Stable"

        if len(modal_values) >= 2:

            first = modal_values[-1]
            last = modal_values[0]

            if first and last:

                difference = (
                    last - first
                )

                percentage = (
                    abs(difference / first) * 100
                )

                if percentage >= 5:

                    if difference > 0:
                        trend = "Rising"

                    elif difference < 0:
                        trend = "Falling"

        advice = (
            "Compare prices across nearby markets "
            "before deciding where to sell."
        )

        if trend == "Rising":

            advice = (
                "Prices show an upward signal. "
                "Compare nearby markets and consider "
                "selling when logistics and quality "
                "conditions are suitable."
            )

        elif trend == "Falling":

            advice = (
                "Prices show a downward signal. "
                "Compare other nearby markets and "
                "consider storage or timing options "
                "where practical."
            )

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crop": crop,
            "records": len(records),
            "summary": summary,
            "intelligence": {
                "trend": trend,
                "signal": trend,
                "advice": advice
            }
        })

    except Exception as exc:

        logger.exception(
            "Market intelligence error: %s",
            exc
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to calculate market intelligence."
            )
        }), 500


# ============================================================
# API: CROPS
# ============================================================

@market_bp.route(
    "/api/market/crops",
    methods=["GET"]
)
def api_market_crops():

    login_redirect = _require_login()

    if login_redirect:
        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    try:

        records = get_crop_prices(
            limit=200
        )

        crops = sorted(
            {
                item.get("crop", "").strip()
                for item in records
                if item.get("crop")
            }
        )

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crops": crops
        })

    except Exception as exc:

        logger.exception(
            "Market crops error: %s",
            exc
        )

        return jsonify({
            "success": False,
            "message": "Unable to fetch crop list."
        }), 500


# ============================================================
# API: MARKETS
# ============================================================

@market_bp.route(
    "/api/market/markets",
    methods=["GET"]
)
def api_markets():

    login_redirect = _require_login()

    if login_redirect:
        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    state = request.args.get(
        "state",
        ""
    ).strip()

    district = request.args.get(
        "district",
        ""
    ).strip()

    try:

        records = get_crop_prices(
            state=state or None,
            district=district or None,
            limit=200
        )

        records = filter_market_prices(
            records,
            state=state,
            district=district
        )

        markets = sorted(
            {
                item.get("market", "").strip()
                for item in records
                if item.get("market")
            }
        )

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "markets": markets
        })

    except Exception as exc:

        logger.exception(
            "Market list error: %s",
            exc
        )

        return jsonify({
            "success": False,
            "message": "Unable to fetch markets."
        }), 500


# ============================================================
# API: TREND
# ============================================================

@market_bp.route(
    "/api/market/trend",
    methods=["GET"]
)
def api_market_trend():

    login_redirect = _require_login()

    if login_redirect:
        return jsonify({
            "success": False,
            "message": "Authentication required."
        }), 401

    crop = request.args.get(
        "crop",
        ""
    ).strip()

    try:

        records = get_market_price(
            crop=crop or None
        )

        points = []

        for item in records:

            modal = item.get(
                "modal_price"
            )

            if modal is None:
                continue

            points.append({
                "date": item.get(
                    "arrival_date"
                ),
                "market": item.get(
                    "market"
                ),
                "price": modal
            })

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crop": crop,
            "trend": points
        })

    except Exception as exc:

        logger.exception(
            "Market trend error: %s",
            exc
        )

        return jsonify({
            "success": False,
            "message": "Unable to fetch market trend."
        }), 500


# ============================================================
# HEALTH
# ============================================================

@market_bp.route(
    "/api/market/health",
    methods=["GET"]
)
def market_health():

    result = market_api_health()

    status_code = (
        200
        if result.get("success")
        else 503
    )

    return jsonify(result), status_code


# ============================================================
# INITIALIZER
# ============================================================

def initialize_market_service():
    """
    Called by app.py during application startup if required.

    This function intentionally does not insert demo prices.
    """

    logger.info(
        "KisanVision360+ Market service initialized."
    )

    return True


