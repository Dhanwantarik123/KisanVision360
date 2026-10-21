
"""
KisanVision360+
Live Mandi / Market Prices
Data source: Data.gov.in

No fake/demo price generation.
"""

import logging

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session,
    redirect,
    url_for,
)

from utils.mandi_price import (
    get_crop_prices,
    get_market_price,
    filter_market_prices,
    calculate_market_summary,
    market_api_health,
)

logger = logging.getLogger(__name__)

market_bp = Blueprint("market", __name__)

DEFAULT_STATE = "Maharashtra"
DEFAULT_DISTRICT = "Nagpur"


# ============================================================
# AUTHENTICATION
# ============================================================

def _role():
    return str(session.get("role", "")).strip().lower()


def _is_logged_in():
    return bool(
        session.get("user_id")
        or session.get("logged_in")
        or session.get("name")
    )


def _page_login_redirect():
    if not _is_logged_in():
        return redirect(url_for("auth.login"))
    return None


def _api_login_error():
    if not _is_logged_in():
        return jsonify({
            "success": False,
            "message": "Authentication required. Please log in.",
            "login_required": True,
        }), 401
    return None


# ============================================================
# FILTERS AND DATA
# ============================================================

def _get_filters():
    return {
        "crop": request.args.get("crop", "").strip(),
        "state": request.args.get(
            "state", DEFAULT_STATE
        ).strip(),
        "district": request.args.get(
            "district", DEFAULT_DISTRICT
        ).strip(),
        "market": request.args.get("market", "").strip(),
    }


def _fetch_prices(filters, limit=100):
    """
    Retrieve actual records from the existing Data.gov.in
    integration and apply the selected filters.
    """

    crop = filters["crop"]
    state = filters["state"]
    district = filters["district"]
    market_name = filters["market"]

    if crop:
        records = get_market_price(crop=crop)
    else:
        records = get_crop_prices(
            state=state or None,
            district=district or None,
            limit=limit,
        )

    records = records or []

    return filter_market_prices(
        records,
        crop=crop,
        state=state,
        district=district,
        market=market_name,
    )


def _error_response(message, status=500):
    return jsonify({
        "success": False,
        "message": message,
        "count": 0,
        "prices": [],
    }), status


def _unique_values(records, key):
    return sorted({
        str(item.get(key, "")).strip()
        for item in records
        if item.get(key)
    })


# ============================================================
# MARKET PAGE
# ============================================================

@market_bp.route("/market", methods=["GET"])
def market():
    redirect_response = _page_login_redirect()
    if redirect_response:
        return redirect_response

    filters = _get_filters()
    records = []
    api_error = None

    try:
        records = _fetch_prices(filters, limit=100)

        if not records:
            api_error = (
                "No live market records found for these filters. "
                "Try another crop, district, or market."
            )

    except Exception:
        logger.exception("Failed to load Mandi page")
        api_error = (
            "Live market prices are temporarily unavailable."
        )

    try:
        summary = calculate_market_summary(records)
    except Exception:
        logger.exception("Failed to calculate market summary")
        summary = {}

    return render_template(
        "market.html",
        prices=records,
        market_prices=records,
        records=records,
        summary=summary,
        crops=_unique_values(records, "crop"),
        markets=_unique_values(records, "market"),
        selected_crop=filters["crop"],
        selected_state=filters["state"],
        selected_district=filters["district"],
        selected_market=filters["market"],
        api_error=api_error,
        source="data.gov.in",
        role=_role(),
        name=session.get("name", "Farmer"),
        language=session.get("language", "en"),
        notification_count=session.get("notification_count", 0),
    )


# ============================================================
# API: MARKET PRICES
# ============================================================

@market_bp.route("/api/market/prices", methods=["GET"])
def api_market_prices():
    auth_error = _api_login_error()
    if auth_error:
        return auth_error

    filters = _get_filters()

    try:
        records = _fetch_prices(filters, limit=100)
        summary = calculate_market_summary(records)

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "count": len(records),
            "prices": records,
            "summary": summary,
            "filters": filters,
        }), 200

    except Exception:
        logger.exception("Market price API failed")
        return _error_response(
            "Unable to fetch live market prices. Check server logs."
        )


# ============================================================
# API: ONE CROP
# ============================================================

@market_bp.route(
    "/api/market/price/<path:crop>",
    methods=["GET"],
)
def api_single_crop_price(crop):
    auth_error = _api_login_error()
    if auth_error:
        return auth_error

    try:
        records = get_market_price(crop=crop) or []

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crop": crop,
            "count": len(records),
            "prices": records,
        })

    except Exception:
        logger.exception("Single crop price API failed")
        return _error_response("Unable to fetch crop prices.")


# ============================================================
# API: CROPS
# ============================================================

@market_bp.route("/api/market/crops", methods=["GET"])
def api_market_crops():
    auth_error = _api_login_error()
    if auth_error:
        return auth_error

    try:
        records = get_crop_prices(limit=200) or []

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crops": _unique_values(records, "crop"),
        })

    except Exception:
        logger.exception("Market crops API failed")
        return _error_response("Unable to fetch crop list.")


# ============================================================
# API: MARKETS
# ============================================================

@market_bp.route("/api/market/markets", methods=["GET"])
def api_markets():
    auth_error = _api_login_error()
    if auth_error:
        return auth_error

    state = request.args.get("state", DEFAULT_STATE).strip()
    district = request.args.get("district", "").strip()

    try:
        records = get_crop_prices(
            state=state or None,
            district=district or None,
            limit=200,
        ) or []

        records = filter_market_prices(
            records,
            state=state,
            district=district,
        )

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "markets": _unique_values(records, "market"),
        })

    except Exception:
        logger.exception("Markets API failed")
        return _error_response("Unable to fetch markets.")


# ============================================================
# API: MARKET INTELLIGENCE
# ============================================================

@market_bp.route("/api/market/intelligence", methods=["GET"])
def api_market_intelligence():
    auth_error = _api_login_error()
    if auth_error:
        return auth_error

    crop = request.args.get("crop", "").strip()

    try:
        records = get_market_price(crop=crop or None) or []

        if not records:
            return jsonify({
                "success": True,
                "source": "data.gov.in",
                "crop": crop,
                "records": 0,
                "message": "No market-price records returned.",
                "intelligence": {
                    "trend": "No data",
                    "signal": "Unavailable",
                    "advice": "Try another crop or market.",
                },
            })

        summary = calculate_market_summary(records)
        values = []

        for item in records:
            try:
                value = item.get("modal_price")
                if value is not None:
                    values.append(float(value))
            except (TypeError, ValueError):
                continue

        trend = "Stable"

        if len(values) >= 2 and values[0] != 0:
            change = (values[-1] - values[0]) / abs(values[0]) * 100

            if change >= 5:
                trend = "Rising"
            elif change <= -5:
                trend = "Falling"

        advice = {
            "Rising": (
                "Prices may be rising. Compare nearby markets "
                "before deciding when and where to sell."
            ),
            "Falling": (
                "Prices may be falling. Compare other markets "
                "and consider practical storage options."
            ),
            "Stable": (
                "Compare prices across nearby markets before selling."
            ),
        }[trend]

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crop": crop,
            "records": len(records),
            "summary": summary,
            "intelligence": {
                "trend": trend,
                "signal": trend,
                "advice": advice,
            },
        })

    except Exception:
        logger.exception("Market intelligence API failed")
        return _error_response(
            "Unable to calculate market intelligence."
        )


# ============================================================
# API: TREND
# ============================================================

@market_bp.route("/api/market/trend", methods=["GET"])
def api_market_trend():
    auth_error = _api_login_error()
    if auth_error:
        return auth_error

    crop = request.args.get("crop", "").strip()

    try:
        records = get_market_price(crop=crop or None) or []
        points = []

        for item in records:
            modal = item.get("modal_price")
            if modal is None:
                continue

            points.append({
                "date": item.get("arrival_date"),
                "market": item.get("market"),
                "price": modal,
            })

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crop": crop,
            "trend": points,
        })

    except Exception:
        logger.exception("Market trend API failed")
        return _error_response("Unable to fetch market trend.")


# ============================================================
# HEALTH CHECK
# ============================================================

@market_bp.route("/api/market/health", methods=["GET"])
def market_health():
    try:
        result = market_api_health()
        return jsonify(result), (
            200 if result.get("success") else 503
        )

    except Exception:
        logger.exception("Market health check failed")
        return jsonify({
            "success": False,
            "message": "Market health check failed.",
        }), 503


# ============================================================
# INITIALIZER
# ============================================================

def initialize_market_service():
    logger.info("KisanVision360+ Market service initialized.")
    return True
