
"""
KisanVision360+ Live Mandi Price Service
Source: Data.gov.in AGMARKNET API
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

DEFAULT_MANDI_RESOURCE_URL = (
    "https://api.data.gov.in/resource/"
    "9ef84268-d588-465a-a308-a864a43d0070"
)

DATA_GOV_URL = (
    os.getenv("DATA_GOV_RESOURCE_URL")
    or os.getenv("DATA_GOV_URL")
    or DEFAULT_MANDI_RESOURCE_URL
).strip()

DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY", "").strip()

try:
    REQUEST_TIMEOUT = int(os.getenv("DATA_GOV_TIMEOUT", "30"))
except (TypeError, ValueError):
    REQUEST_TIMEOUT = 30

REQUEST_TIMEOUT = max(5, min(REQUEST_TIMEOUT, 60))
USER_AGENT = "KisanVision360Plus/1.0"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _clean(value):
    return "" if value is None else str(value).strip()


def _number(value):
    if value is None:
        return None

    value = _clean(value).replace(",", "")
    if not value or value.lower() in {
        "na", "n/a", "none", "null", "-", "--"
    }:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _field_map(record):
    return {
        str(key).strip().lower().replace(" ", "_"): value
        for key, value in record.items()
    }


def _first(fields, *names):
    for name in names:
        value = fields.get(name)
        if value is not None and _clean(value):
            return value
    return ""


def _normalize_record(record):
    if not isinstance(record, dict):
        return {}

    fields = _field_map(record)

    commodity = _first(fields, "commodity", "crop", "commodity_name")
    state = _first(fields, "state", "state_name")
    district = _first(fields, "district", "district_name")
    market = _first(fields, "market", "market_name", "mandi")
    variety = _first(fields, "variety", "commodity_variety")
    grade = _first(fields, "grade")
    arrival_date = _first(
        fields, "arrival_date", "date", "reported_date"
    )

    min_price = _number(
        _first(fields, "min_price", "minimum_price", "min")
    )
    max_price = _number(
        _first(fields, "max_price", "maximum_price", "max")
    )
    modal_price = _number(
        _first(fields, "modal_price", "model_price", "modal", "price")
    )

    normalized = dict(record)
    normalized.update({
        "commodity": _clean(commodity),
        "state": _clean(state),
        "district": _clean(district),
        "market": _clean(market),
        "variety": _clean(variety),
        "grade": _clean(grade),
        "arrival_date": _clean(arrival_date),
        "min_price": min_price,
        "max_price": max_price,
        "modal_price": modal_price,
        "source": "Data.gov.in AGMARKNET",
    })

    return normalized


# --------------------------------------------------
# Live API request
# --------------------------------------------------

def _request_data(
    commodity=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
):
    """Fetch real API records. Return [] on failure; never fake data."""

    if not DATA_GOV_API_KEY:
        logger.error("DATA_GOV_API_KEY is not configured.")
        return []

    if not DATA_GOV_URL.startswith(("https://", "http://")):
        logger.error("Data.gov.in resource URL is invalid.")
        return []

    try:
        limit = max(1, min(int(limit), 1000))
        offset = max(0, int(offset))
    except (TypeError, ValueError):
        limit, offset = 100, 0

    params = {
        "api-key": DATA_GOV_API_KEY,
        "format": "json",
        "limit": limit,
        "offset": offset,
    }

    filters = {
        "commodity": commodity,
        "state": state,
        "district": district,
        "market": market,
    }

    for field, value in filters.items():
        if value and _clean(value):
            params[f"filters[{field}]"] = _clean(value)

    response = None

    try:
        response = requests.get(
            DATA_GOV_URL,
            params=params,
            timeout=(5, REQUEST_TIMEOUT),
            headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
        )

        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            logger.error("Data.gov.in returned unexpected JSON.")
            return []

        records = data.get("records", [])

        if not isinstance(records, list):
            logger.error("Data.gov.in response has no valid records list.")
            return []

        logger.info("Data.gov.in returned %d records.", len(records))
        return [
            _normalize_record(item)
            for item in records
            if isinstance(item, dict)
        ]

    except requests.exceptions.Timeout as exc:
        logger.error(
            "Data.gov.in timeout (%s): %s",
            type(exc).__name__,
            str(exc)[:500],
        )

    except requests.exceptions.HTTPError as exc:
        status = response.status_code if response is not None else None
        logger.error(
            "Data.gov.in HTTP error %s (%s).",
            status,
            type(exc).__name__,
        )

        if response is not None:
            # Response body only; do not log the request URL/API key.
            logger.error(
                "Data.gov.in response: %s",
                response.text[:500],
            )

    except requests.exceptions.ConnectionError as exc:
        message = str(exc)
        if DATA_GOV_API_KEY:
            message = message.replace(DATA_GOV_API_KEY, "[REDACTED]")

        logger.error(
            "Data.gov.in connection failure (%s): %s",
            type(exc).__name__,
            message[:1000],
        )

    except requests.exceptions.RequestException as exc:
        message = str(exc)
        if DATA_GOV_API_KEY:
            message = message.replace(DATA_GOV_API_KEY, "[REDACTED]")

        logger.error(
            "Data.gov.in request failure (%s): %s",
            type(exc).__name__,
            message[:1000],
        )

    except (ValueError, TypeError) as exc:
        logger.error(
            "Invalid Data.gov.in response (%s): %s",
            type(exc).__name__,
            str(exc)[:500],
        )

    except Exception:
        logger.exception("Unexpected error fetching mandi data.")

    return []


# --------------------------------------------------
# Filtering and public functions
# --------------------------------------------------

def filter_market_prices(
    records,
    commodity=None,
    crop=None,
    state=None,
    district=None,
    market=None,
):
    """Apply case-insensitive filters to returned records."""

    commodity = commodity or crop
    filters = {
        "commodity": commodity,
        "state": state,
        "district": district,
        "market": market,
    }

    result = []

    for record in records or []:
        item = _normalize_record(record)
        matches = True

        for field, expected in filters.items():
            if not expected:
                continue

            actual = _clean(item.get(field)).casefold()
            expected = _clean(expected).casefold()

            if actual != expected:
                matches = False
                break

        if matches:
            result.append(item)

    return result


def get_crop_prices(
    crop=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
    **kwargs,
):
    """Return live prices for a crop and/or location."""

    commodity = crop or kwargs.get("commodity")

    records = _request_data(
        commodity=commodity,
        state=state,
        district=district,
        market=market,
        limit=limit,
        offset=offset,
    )

    return filter_market_prices(
        records,
        commodity=commodity,
        state=state,
        district=district,
        market=market,
    )


def get_market_price(crop, state=None, district=None, market=None):
    """Return one matching record, or None if unavailable."""

    records = get_crop_prices(
        crop=crop,
        state=state,
        district=district,
        market=market,
        limit=100,
    )

    return records[0] if records else None


def calculate_market_summary(records):
    """Summarize available real prices."""

    records = records or []

    modal = [
        item["modal_price"]
        for item in records
        if item.get("modal_price") is not None
    ]
    minimum = [
        item["min_price"]
        for item in records
        if item.get("min_price") is not None
    ]
    maximum = [
        item["max_price"]
        for item in records
        if item.get("max_price") is not None
    ]

    return {
        "total_records": len(records),
        "records_with_modal_price": len(modal),
        "average_modal_price": (
            round(sum(modal) / len(modal), 2) if modal else None
        ),
        "lowest_min_price": min(minimum) if minimum else None,
        "highest_max_price": max(maximum) if maximum else None,
        "source": "Data.gov.in AGMARKNET",
        "updated_at": datetime.now().astimezone().isoformat(),
    }


def get_available_crops(state=None, district=None, limit=1000):
    records = _request_data(
        state=state,
        district=district,
        limit=limit,
    )
    return sorted({
        item["commodity"]
        for item in records
        if item.get("commodity")
    }, key=str.casefold)


def get_available_markets(state=None, district=None, limit=1000):
    records = _request_data(
        state=state,
        district=district,
        limit=limit,
    )
    return sorted({
        item["market"]
        for item in records
        if item.get("market")
    }, key=str.casefold)


def market_api_health():
    """Attempt a real request and report its result."""

    result = {
        "configured": bool(DATA_GOV_API_KEY and DATA_GOV_URL),
        "api_key_configured": bool(DATA_GOV_API_KEY),
        "resource_url_configured": bool(DATA_GOV_URL),
        "reachable": False,
        "records_received": 0,
        "source": "Data.gov.in AGMARKNET",
        "checked_at": datetime.now().astimezone().isoformat(),
    }

    if not result["configured"]:
        result["message"] = "Missing API key or resource URL."
        return result

    records = _request_data(limit=1)
    result["records_received"] = len(records)
    result["reachable"] = len(records) > 0
    result["message"] = (
        "Live records received."
        if records
        else "No records received; inspect server logs."
    )
    return result


def get_market_source_info():
    """Return safe configuration information; never expose the API key."""

    return {
        "source": "Data.gov.in AGMARKNET",
        "resource_url": DATA_GOV_URL,
        "api_key_configured": bool(DATA_GOV_API_KEY),
        "timeout_seconds": REQUEST_TIMEOUT,
        "uses_demo_prices": False,
    }


def initialize_market_service(app=None):
    """Initialize service logging; compatible with Flask startup."""

    logger.info(
        "Mandi service initialized. API key configured: %s",
        bool(DATA_GOV_API_KEY),
    )

    if app is not None:
        app.logger.info(
            "Mandi service initialized. API key configured: %s",
            bool(DATA_GOV_API_KEY),
        )

    return True
