
"""
KisanVision360+
Live Mandi Price Service
Source: Data.gov.in
"""

import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.data.gov.in/resource"

RESOURCE_ID = os.getenv(
    "DATA_GOV_RESOURCE_ID",
    "9ef84268-d588-465a-a308-a864a43d0070",
).strip()

API_KEY = os.getenv("DATA_GOV_API_KEY", "").strip()
API_TIMEOUT = int(os.getenv("DATA_GOV_TIMEOUT", "20"))

DEFAULT_STATE = "Maharashtra"


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _first(record, *keys):
    for key in keys:
        value = record.get(key)
        if value is not None and _text(value):
            return value
    return ""


def _number(value):
    """Convert a price to a number, or None if unavailable."""
    if value is None or _text(value) == "":
        return None

    try:
        cleaned = _text(value).replace(",", "").replace("₹", "")
        result = float(cleaned)
        return result if result >= 0 else None
    except (TypeError, ValueError):
        return None


def _normalize_record(record):
    if not isinstance(record, dict):
        return None

    return {
        "crop": _text(_first(
            record, "commodity", "crop", "crop_name"
        )),
        "state": _text(_first(record, "state")),
        "district": _text(_first(record, "district")),
        "market": _text(_first(record, "market", "market_name")),
        "variety": _text(_first(record, "variety")),
        "grade": _text(_first(record, "grade")),
        "arrival_date": _text(_first(
            record, "arrival_date", "date"
        )),
        "min_price": _number(_first(
            record, "min_price", "minimum_price"
        )),
        "max_price": _number(_first(
            record, "max_price", "maximum_price"
        )),
        "modal_price": _number(_first(
            record, "modal_price", "modal"
        )),
        "unit": "₹/quintal",
    }


def _request_records(params=None):
    """
    Request actual records from Data.gov.in.
    Raises an exception on missing configuration or API failure.
    """
    if not API_KEY:
        raise RuntimeError(
            "DATA_GOV_API_KEY is not configured."
        )

    if not RESOURCE_ID:
        raise RuntimeError(
            "DATA_GOV_RESOURCE_ID is not configured."
        )

    url = f"{API_BASE_URL}/{RESOURCE_ID}"

    query = {
        "api-key": API_KEY,
        "format": "json",
        "limit": 100,
    }

    if params:
        query.update(params)

    response = requests.get(
        url,
        params=query,
        timeout=API_TIMEOUT,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("Unexpected Data.gov.in response.")

    records = payload.get("records", [])

    if not isinstance(records, list):
        raise ValueError("API records field is not a list.")

    return records


def _fetch_prices(crop=None, state=None, district=None,
                  market=None, limit=100, offset=0):
    params = {
        "limit": max(1, min(int(limit), 1000)),
        "offset": max(0, int(offset)),
    }

    # Data.gov.in resource filters.
    if crop:
        params["filters[commodity]"] = crop
    if state:
        params["filters[state]"] = state
    if district:
        params["filters[district]"] = district
    if market:
        params["filters[market]"] = market

    raw_records = _request_records(params)

    normalized = [
        _normalize_record(record)
        for record in raw_records
    ]

    normalized = [
        item for item in normalized
        if item is not None
    ]

    # Apply local filtering too, in case the API ignores a filter.
    return filter_market_prices(
        normalized,
        crop=crop,
        state=state,
        district=district,
        market=market,
    )


def filter_market_prices(prices, crop=None, state=None,
                         district=None, market=None, **kwargs):
    """Case-insensitive local filtering."""
    crop = crop or kwargs.get("commodity")

    def matches(actual, expected):
        if not expected:
            return True
        return _text(expected).casefold() in _text(actual).casefold()

    filtered = []

    for item in prices or []:
        if not isinstance(item, dict):
            continue

        if not matches(item.get("crop"), crop):
            continue
        if not matches(item.get("state"), state):
            continue
        if not matches(item.get("district"), district):
            continue
        if not matches(item.get("market"), market):
            continue

        filtered.append(item)

    return filtered


def get_crop_prices(crop=None, state=None, district=None,
                    market=None, limit=100, offset=0):
    """
    Fetch crop prices. No fabricated fallback data is returned.
    An API error is logged and an empty list is returned.
    """
    try:
        return _fetch_prices(
            crop=crop,
            state=state,
            district=district,
            market=market,
            limit=limit,
            offset=offset,
        )
    except (requests.RequestException, ValueError, TypeError,
            RuntimeError, KeyError) as exc:
        logger.warning("Data.gov.in Mandi request failed: %s", exc)
        return []


def get_market_price(crop, state=None, district=None, market=None):
    if not crop:
        return get_crop_prices(
            state=state,
            district=district,
            market=market,
        )

    return get_crop_prices(
        crop=crop,
        state=state,
        district=district,
        market=market,
        limit=100,
    )


def calculate_market_summary(prices):
    modal_values = [
        _number(item.get("modal_price"))
        for item in (prices or [])
    ]
    modal_values = [
        value for value in modal_values
        if value is not None
    ]

    return {
        "total_records": len(prices or []),
        "average_price": (
            round(sum(modal_values) / len(modal_values), 2)
            if modal_values else None
        ),
        "minimum_price": (
            min(modal_values) if modal_values else None
        ),
        "maximum_price": (
            max(modal_values) if modal_values else None
        ),
    }


def get_available_crops(state=None, district=None):
    records = get_crop_prices(
        state=state,
        district=district,
        limit=500,
    )
    return sorted({
        item["crop"] for item in records if item.get("crop")
    })


def get_available_markets(state=None, district=None):
    records = get_crop_prices(
        state=state,
        district=district,
        limit=500,
    )
    return sorted({
        item["market"] for item in records if item.get("market")
    })


def market_api_health():
    checked_at = datetime.now().isoformat(timespec="seconds")

    try:
        records = _request_records({
            "limit": 1,
            "filters[state]": DEFAULT_STATE,
        })

        return {
            "success": True,
            "ok": True,
            "source": "data.gov.in",
            "status": "reachable",
            "records_returned": len(records),
            "checked_at": checked_at,
        }

    except Exception as exc:
        logger.warning("Mandi API health check failed: %s", exc)

        return {
            "success": False,
            "ok": False,
            "source": "data.gov.in",
            "status": "unavailable",
            "message": str(exc),
            "checked_at": checked_at,
        }


def check_mandi_api():
    """Compatibility alias for older project code."""
    return market_api_health()
