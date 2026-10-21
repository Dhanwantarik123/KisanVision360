
"""
KisanVision360+
Market / Mandi Routes
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


def _role():
    return str(session.get("role", "")).strip().lower()


def _is_logged_in():
    return bool(
        session.get("user_id")
        or session.get("logged_in")
        or session.get("name")
    )


def _require_login():
    if not _is_logged_in():
        return redirect(url_for("auth.login"))
    return None


def _auth_error():
    return jsonify({
        "success": False,
        "message": "Authentication required.",
    }), 401


def _filters(defaults=False):
    return {
        "crop": request.args.get("crop", "").strip(),
        "state": request.args.get(
            "state", DEFAULT_STATE if defaults else ""
        ).strip(),
        "district": request.args.get(
            "district", DEFAULT_DISTRICT if defaults else ""
        ).strip(),
        "market": request.args.get("market", "").strip(),
    }


def _fetch(filters, limit=100):
    return get_crop_prices(
        crop=filters["crop"] or None,
        state=filters["state"] or None,
        district=filters["district"] or None,
        market=filters["market"] or None,
        limit=limit,
    )


def _trend_info(records):
    dated = []

    for item in records:
        price = item.get("modal_price")
        date = item.get("arrival_date")

        if price is None or not date:
            continue

        try:
            price = float(str(price).replace(",", ""))
        except (TypeError, ValueError):
            continue

        dated.append((str(date), price))

    # Compare only when dates can be sorted and at least two
    # observations exist. This is not a forecast.
    dated.sort(key=lambda point: point[0])

    if len(dated) < 2:
        return {
            "trend": "Insufficient data",
            "signal": "Unavailable",
            "advice": (
                "More dated market observations are needed "
                "before comparing prices."
            ),
        }

    first_date, first_price = dated[0]
    last_date, last_price = dated[-1]

    if first_price <= 0:
        trend = "Insufficient data"
    else:
        change_percent = (
            (last_price - first_price) / first_price
        ) * 100

        if change_percent >= 5:
            trend = "Rising"
        elif change_percent <= -5:
            trend = "Falling"
        else:
            trend = "Stable"

    advice = (
        "Compare prices across nearby markets, transport "
        "costs and crop quality before deciding where to sell."
    )

    return {
        "trend": trend,
        "signal": trend,
        "first_date": first_date,
        "last_date": last_date,
        "advice": advice,
    }


@market_bp.route("/market", methods=["GET"])
def market():
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    filters = _filters(defaults=True)
    api_error = None

    try:
        records = _fetch(filters)
        health = market_api_health()

        if not health.get("success"):
            api_error = (
                "Data.gov.in is unavailable or its API "
                "configuration needs checking."
            )

    except Exception:
        logger.exception("Market page error")
        records = []
        health = {"success": False, "ok": False}
        api_error = "Unable to fetch market prices."

    summary = calculate_market_summary(records)

    crops = sorted({
        item["crop"] for item in records if item.get("crop")
    })
    markets = sorted({
        item["market"] for item in records if item.get("market")
    })

    return render_template(
        "market.html",
        prices=records,
        market_prices=records,
        records=records,
        summary=summary,
        crops=crops,
        markets=markets,
        selected_crop=filters["crop"],
        selected_state=filters["state"],
        selected_district=filters["district"],
        selected_market=filters["market"],
        filters=filters,
        api_error=api_error,
        api_status=health,
        source="data.gov.in",
        role=_role(),
        name=session.get("name", "Farmer"),
        language=session.get("language", "en"),
        notification_count=session.get("notification_count", 0),
    )


@market_bp.route("/api/market/prices", methods=["GET"])
def api_market_prices():
    if not _is_logged_in():
        return _auth_error()

    try:
        records = _fetch(_filters(), limit=100)

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "count": len(records),
            "prices": records,
            "summary": calculate_market_summary(records),
        })

    except Exception:
        logger.exception("Market prices API error")
        return jsonify({
            "success": False,
            "message": "Unable to fetch market prices.",
        }), 500


@market_bp.route("/api/market/price/<path:crop>", methods=["GET"])
def api_single_crop_price(crop):
    if not _is_logged_in():
        return _auth_error()

    try:
        records = get_market_price(
            crop=crop,
            state=request.args.get("state") or None,
            district=request.args.get("district") or None,
            market=request.args.get("market") or None,
        )

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crop": crop,
            "count": len(records),
            "prices": records,
        })

    except Exception:
        logger.exception("Single crop API error")
        return jsonify({
            "success": False,
            "message": "Unable to fetch crop prices.",
        }), 500


@market_bp.route("/api/market/intelligence", methods=["GET"])
def api_market_intelligence():
    if not _is_logged_in():
        return _auth_error()

    filters = _filters()
    try:
        records = _fetch(filters, limit=200)
        summary = calculate_market_summary(records)

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crop": filters["crop"],
            "records": len(records),
            "summary": summary,
            "intelligence": _trend_info(records),
        })

    except Exception:
        logger.exception("Market intelligence API error")
        return jsonify({
            "success": False,
            "message": "Unable to calculate market intelligence.",
        }), 500


@market_bp.route("/api/market/crops", methods=["GET"])
def api_market_crops():
    if not _is_logged_in():
        return _auth_error()

    try:
        records = get_crop_prices(
            state=request.args.get("state") or DEFAULT_STATE,
            district=request.args.get("district") or None,
            limit=500,
        )
        crops = sorted({
            item["crop"] for item in records if item.get("crop")
        })

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "crops": crops,
        })

    except Exception:
        logger.exception("Market crops API error")
        return jsonify({
            "success": False,
            "message": "Unable to fetch crop list.",
        }), 500


@market_bp.route("/api/market/markets", methods=["GET"])
def api_markets():
    if not _is_logged_in():
        return _auth_error()

    try:
        filters = _filters()
        records = _fetch(filters, limit=500)

        markets = sorted({
            item["market"] for item in records if item.get("market")
        })

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "markets": markets,
        })

    except Exception:
        logger.exception("Market list API error")
        return jsonify({
            "success": False,
            "message": "Unable to fetch market list.",
        }), 500


@market_bp.route("/api/market/trend", methods=["GET"])
def api_market_trend():
    if not _is_logged_in():
        return _auth_error()

    try:
        records = _fetch(_filters(), limit=200)
        points = [
            {
                "date": item.get("arrival_date"),
                "market": item.get("market"),
                "crop": item.get("crop"),
                "price": item.get("modal_price"),
            }
            for item in records
            if item.get("arrival_date")
            and item.get("modal_price") is not None
        ]

        points.sort(key=lambda item: item["date"])

        return jsonify({
            "success": True,
            "source": "data.gov.in",
            "count": len(points),
            "trend": points,
            "intelligence": _trend_info(records),
        })

    except Exception:
        logger.exception("Market trend API error")
        return jsonify({
            "success": False,
            "message": "Unable to fetch market trend.",
        }), 500


@market_bp.route("/api/market/health", methods=["GET"])
def market_health():
    # Health check reveals configuration status, so require login.
    if not _is_logged_in():
        return _auth_error()

    result = market_api_health()
    return jsonify(result), (
        200 if result.get("success") else 503
    )


def initialize_market_service():
    logger.info("KisanVision360+ market service initialized.")
    return True
