
"""
KisanVision360+ — Live Mandi Price Service
Data source: Data.gov.in AGMARKNET API

Required environment variables:
    DATA_GOV_API_KEY=your_actual_api_key
    DATA_GOV_RESOURCE_URL=https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070
    DATA_GOV_TIMEOUT=30

This module never creates demo or fabricated market prices.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Do not override environment variables already configured on Render.
load_dotenv(dotenv_path=ENV_FILE, override=False)

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
MAX_RECORDS = 1000


# ---------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------

def _clean(value):
    """Convert a value to a clean string."""
    if value is None:
        return ""
    return str(value).strip()


def _number(value):
    """Convert a numeric API value to float, or None."""
    if value is None:
        return None

    value = str(value).strip().replace(",", "")

    if not value or value.lower() in {
        "na", "n/a", "none", "null", "-", "--"
    }:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_record(record):
    """
    Normalize an AGMARKNET record while retaining its original fields.
    Actual API field names can vary, so common alternatives are supported.
    """
    if not isinstance(record, dict):
        return {}

    result = dict(record)

    # Normalize field names without discarding original data.
    lower_fields = {
        str(key).strip().lower().replace(" ", "_"): value
        for key, value in record.items()
    }

    def first_value(*keys):
        for key in keys:
            value = lower_fields.get(key)
            if value is not None and _clean(value):
                return value
        return ""

    commodity = first_value("commodity", "crop", "commodity_name")
    state = first_value("state", "state_name")
    district = first_value("district", "district_name")
    market = first_value("market", "market_name", "mandi")
    variety = first_value("variety", "commodity_variety")
    grade = first_value("grade")
    arrival_date = first_value(
        "arrival_date", "date", "reported_date"
    )

    min_price = _number(
        first_value("min_price", "minimum_price", "min")
    )
    max_price = _number(
        first_value("max_price", "maximum_price", "max")
    )
    modal_price = _number(
        first_value(
            "modal_price",
            "model_price",
            "modal",
            "price",
        )
    )

    result.update({
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

    return result


def _request_data(
    commodity=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
):
    """
    Fetch genuine records from Data.gov.in.

    Returns:
        list[dict]: API records, or [] if the request fails.
    """
    if not DATA_GOV_API_KEY:
        logger.error(
            "Data.gov.in API key is not configured. "
            "Set DATA_GOV_API_KEY in the environment."
        )
        return []

    if not DATA_GOV_URL.startswith(("https://", "http://")):
        logger.error("Data.gov.in resource URL is invalid.")
        return []

    try:
        limit = max(1, min(int(limit), MAX_RECORDS))
        offset = max(0, int(offset))
    except (TypeError, ValueError):
        limit = 100
        offset = 0

    params = {
        "api-key": DATA_GOV_API_KEY,
        "format": "json",
        "limit": limit,
        "offset": offset,
    }

    # Data.gov.in API filtering syntax.
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
            logger.error(
                "Data.gov.in returned an unexpected JSON structure."
            )
            return []

        records = data.get("records", [])

        if not isinstance(records, list):
            logger.error(
                "Data.gov.in response does not contain a records list."
            )
            return []

        logger.info(
            "Data.gov.in request succeeded: %s record(s) received.",
            len(records),
        )

        return [
            _normalize_record(record)
            for record in records
            if isinstance(record, dict)
        ]

    except requests.exceptions.Timeout as exc:
        logger.error(
            "Data.gov.in timeout (%s): %s",
            type(exc).__name__,
            str(exc)[:500],
        )

    except requests.exceptions.HTTPError as exc:
        status = response.status_code if response is not None else None

        # Do not log response/request URLs because they can contain the API key.
        logger.error(
            "Data.gov.in HTTP error %s: %s",
            status,
            type(exc).__name__,
        )

        if response is not None:
            logger.error(
                "Data.gov.in response body: %s",
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

    except ValueError as exc:
        logger.error(
            "Data.gov.in returned invalid JSON: %s",
            str(exc)[:500],
        )

    except Exception:
        logger.exception("Unexpected error fetching mandi data.")

    return []


# ---------------------------------------------------------
# Market price functions
# ---------------------------------------------------------

def filter_market_prices(
    records,
    commodity=None,
    state=None,
    district=None,
    market=None,
):
    """Filter records locally using case-insensitive comparisons."""
    if not records:
        return []

    filters = {
        "commodity": commodity,
        "state": state,
        "district": district,
        "market": market,
    }

    filtered = []

    for record in records:
        normalized = _normalize_record(record)
        matches = True

        for field, expected in filters.items():
            if not expected:
                continue

            actual_value = _clean(normalized.get(field)).casefold()
            expected_value = _clean(expected).casefold()

            if actual_value != expected_value:
                matches = False
                break

        if matches:
            filtered.append(normalized)

    return filtered


def get_crop_prices(
    crop=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
    **kwargs,
):
    """
    Get live crop prices.

    `crop` is supported for existing application code.
    `commodity` is also accepted as an alternative keyword.
    """
    commodity = crop or kwargs.get("commodity")

    records = _request_data(
        commodity=commodity,
        state=state,
        district=district,
        market=market,
        limit=limit,
        offset=offset,
    )

    # Do not return records that fail the requested local filters.
    return filter_market_prices(
        records,
        commodity=commodity,
        state=state,
        district=district,
        market=market,
    )


def get_market_price(
    crop,
    state=None,
    district=None,
    market=None,
):
    """Return the first matching genuine market-price record."""
    records = get_crop_prices(
        crop=crop,
        state=state,
        district=district,
        market=market,
        limit=100,
    )

    return records[0] if records else None


def calculate_market_summary(records):
    """Calculate a summary from real records with available prices."""
    records = records or []

    modal_prices = [
        record.get("modal_price")
        for record in records
        if record.get("modal_price") is not None
    ]

    min_prices = [
        record.get("min_price")
        for record in records
        if record.get("min_price") is not None
    ]

    max_prices = [
        record.get("max_price")
        for record in records
        if record.get("max_price") is not None
    ]

    return {
        "total_records": len(records),
        "records_with_modal_price": len(modal_prices),
        "average_modal_price": (
            round(sum(modal_prices) / len(modal_prices), 2)
            if modal_prices else None
        ),
        "lowest_min_price": min(min_prices) if min_prices else None,
        "highest_max_price": max(max_prices) if max_prices else None,
        "source": "Data.gov.in AGMARKNET",
        "updated_at": datetime.now().astimezone().isoformat(),
    }


def get_available_crops(state=None, district=None, limit=1000):
    """Return unique crop names present in live API records."""
    records = _request_data(
        state=state,
        district=district,
        limit=limit,
    )

    crops = {
        record["commodity"]
        for record in records
        if record.get("commodity")
    }

    return sorted(crops, key=str.casefold)


def get_available_markets(state=None, district=None, limit=1000):
    """Return unique market names present in live API records."""
    records = _request_data(
        state=state,
        district=district,
        limit=limit,
    )

    markets = {
        record["market"]
        for record in records
        if record.get("market")
    }

    return sorted(markets, key=str.casefold)


# ---------------------------------------------------------
# Health and configuration helpers
# ---------------------------------------------------------

def market_api_health():
    """
    Check configuration and attempt a small real API request.
    A successful HTTP response with zero records still means
    the API is reachable.
    """
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
    result["reachable"] = True
    result["message"] = "Request completed; inspect records for data."

    return result


def get_market_source_info():
    """Return safe configuration details without exposing the API key."""
    return {
        "source": "Data.gov.in AGMARKNET",
        "resource_url": DATA_GOV_URL,
        "api_key_configured": bool(DATA_GOV_API_KEY),
        "timeout_seconds": REQUEST_TIMEOUT,
        "uses_demo_prices": False,
    }


def initialize_market_service(app=None):
    """
    Initialize market service logging.
    Safe to call from a Flask application factory.
    """
    if app is not None:
        app.logger.info(
            "KisanVision360+ market service initialized. "
            "Data.gov.in API key configured: %s",
            bool(DATA_GOV_API_KEY),
        )

    logger.info(
        "Market service initialized. API key configured: %s",
        bool(DATA_GOV_API_KEY),
    )

    return True
