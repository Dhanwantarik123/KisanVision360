
"""
KisanVision360+
Mandi / Market Price Utility

Data source:
Data.gov.in - Variety-wise Daily Market Prices Data of Commodity.

Features:
- Loads configuration from the project-root .env file.
- Fetches genuine market data from Data.gov.in.
- Supports crop, state, district, and market filters.
- Normalizes market prices and calculates summaries.
- Provides API health and source information.
- Never generates fake or demo prices.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Explicit path prevents load_dotenv() errors when the application
# is started from a different working directory.
load_dotenv(dotenv_path=ENV_FILE, override=False)

DEFAULT_MANDI_RESOURCE_URL = (
    "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
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


# ============================================================
# COMMON HELPERS
# ============================================================

def _clean(value):
    """Convert a value to a trimmed string."""
    if value is None:
        return ""
    return str(value).strip()


def _first_value(record, *keys):
    """Return the first non-empty field value."""
    if not isinstance(record, dict):
        return ""

    for key in keys:
        value = record.get(key)
        if value is not None:
            value = str(value).strip()
            if value:
                return value

    return ""


def _to_float(value):
    """Convert a price to float, or None when invalid."""
    if value is None:
        return None

    try:
        text = str(value).strip()

        if not text:
            return None

        text = (
            text.replace(",", "")
            .replace("₹", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .strip()
        )

        number = float(text)

        # Avoid treating invalid numerical values as real prices.
        if number < 0:
            return None

        return number

    except (ValueError, TypeError):
        return None


def _normalize_record(record):
    """Normalize one genuine Data.gov.in record."""
    if not isinstance(record, dict):
        return None

    crop = _first_value(
        record,
        "commodity", "Commodity",
        "crop", "Crop",
        "commodity_name", "Commodity_Name",
    )

    market = _first_value(
        record,
        "market", "Market",
        "market_name", "Market_Name",
        "mandi", "Mandi",
    )

    state = _first_value(
        record,
        "state", "State",
        "state_name", "State_Name",
    )

    district = _first_value(
        record,
        "district", "District",
        "district_name", "District_Name",
    )

    variety = _first_value(record, "variety", "Variety")
    grade = _first_value(record, "grade", "Grade")

    min_price = _first_value(
        record,
        "min_price", "Min_Price",
        "minimum_price", "Minimum_Price",
    )

    max_price = _first_value(
        record,
        "max_price", "Max_Price",
        "maximum_price", "Maximum_Price",
    )

    modal_price = _first_value(
        record,
        "modal_price", "Modal_Price",
        "modal", "Modal",
    )

    arrival_date = _first_value(
        record,
        "arrival_date", "Arrival_Date",
        "date", "Date", "reported_date",
    )

    # Reject records without identifiable market or commodity data.
    if not any((crop, market, state, district)):
        return None

    return {
        "crop": crop or "Unknown",
        "commodity": crop or "Unknown",
        "market": market or "Unknown",
        "state": state,
        "district": district,
        "variety": variety,
        "grade": grade,
        "min_price": _to_float(min_price),
        "max_price": _to_float(max_price),
        "modal_price": _to_float(modal_price),
        "arrival_date": arrival_date,
        "source": "data.gov.in",
        "fetched_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "raw": record,
    }


# ============================================================
# API REQUEST
# ============================================================

def _request_data(
    crop=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
):
    """
    Fetch genuine records from Data.gov.in.

    Returns an empty list on failure. It never substitutes demo data.
    """
    if not DATA_GOV_API_KEY:
        logger.error(
            "DATA_GOV_API_KEY is missing. Check %s",
            ENV_FILE,
        )
        return []

    if not DATA_GOV_URL:
        logger.error("Data.gov.in resource URL is missing.")
        return []

    try:
        limit = max(1, min(int(limit), 1000))
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

    # Filters are sent to the API and applied locally as well.
    if crop:
        params["filters[commodity]"] = _clean(crop)

    if state:
        params["filters[state]"] = _clean(state)

    if district:
        params["filters[district]"] = _clean(district)

    if market:
        params["filters[market]"] = _clean(market)

    logger.info("Requesting live mandi data from Data.gov.in.")

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

        logger.info(
            "Data.gov.in returned HTTP status %s.",
            response.status_code,
        )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            logger.error("Data.gov.in returned invalid JSON.")
            return []

        if not isinstance(data, dict):
            logger.error("Unexpected Data.gov.in response structure.")
            return []

        records = data.get("records", [])

        if not isinstance(records, list):
            logger.error("The API response has no valid records list.")
            return []

        logger.info("Received %s API records.", len(records))

        if not records:
            logger.warning(
                "The API returned zero records. Check the resource "
                "schema, API key, and filters."
            )

        return records

    except requests.exceptions.Timeout:
        logger.error(
            "Data.gov.in timed out after %s seconds. "
            "The API may be slow or unreachable.",
            REQUEST_TIMEOUT,
        )

    except requests.exceptions.HTTPError as exc:
        # Do not log the full request URL because it contains the key.
        status = response.status_code if "response" in locals() else None

        logger.error(
            "Data.gov.in HTTP error %s: %s",
            status,
            exc,
        )

        if "response" in locals():
            logger.error(
                "API response body: %s",
                response.text[:500],
            )

    except requests.exceptions.RequestException as exc:
        logger.error(
            "Data.gov.in network request failed: %s",
            type(exc).__name__,
        )

    except Exception:
        logger.exception("Unexpected error fetching mandi data.")

    return []


# ============================================================
# LOCAL FILTERING
# ============================================================

def filter_market_prices(
    records,
    crop=None,
    state=None,
    district=None,
    market=None,
):
    """Filter normalized records without fabricating data."""
    if not records:
        return []

    crop_text = _clean(crop).casefold()
    state_text = _clean(state).casefold()
    district_text = _clean(district).casefold()
    market_text = _clean(market).casefold()

    result = []

    for item in records:
        if crop_text:
            crop_value = _clean(
                item.get("crop") or item.get("commodity")
            ).casefold()

            if crop_text not in crop_value:
                continue

        if state_text and state_text not in _clean(
            item.get("state")
        ).casefold():
            continue

        if district_text and district_text not in _clean(
            item.get("district")
        ).casefold():
            continue

        if market_text and market_text not in _clean(
            item.get("market")
        ).casefold():
            continue

        result.append(item)

    return result


# ============================================================
# PUBLIC PRICE FUNCTIONS
# ============================================================

def get_crop_prices(
    crop=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
):
    """Return normalized live prices with optional filters."""
    records = _request_data(
        crop=crop,
        state=state,
        district=district,
        market=market,
        limit=limit,
        offset=offset,
    )

    normalized = []

    for record in records:
        item = _normalize_record(record)

        if item:
            normalized.append(item)

    return filter_market_prices(
        normalized,
        crop=crop,
        state=state,
        district=district,
        market=market,
    )


def get_market_price(crop=None):
    """Return current API records for a crop, or recent records."""
    return get_crop_prices(crop=crop, limit=100)


# ============================================================
# PRICE SUMMARY
# ============================================================

def calculate_market_summary(records):
    """Calculate price statistics from available genuine records."""
    if not records:
        return {
            "records": 0,
            "min_price": None,
            "max_price": None,
            "average_modal_price": None,
        }

    min_values = [
        item["min_price"]
        for item in records
        if item.get("min_price") is not None
    ]

    max_values = [
        item["max_price"]
        for item in records
        if item.get("max_price") is not None
    ]

    modal_values = [
        item["modal_price"]
        for item in records
        if item.get("modal_price") is not None
    ]

    return {
        "records": len(records),
        "min_price": min(min_values) if min_values else None,
        "max_price": max(max_values) if max_values else None,
        "average_modal_price": (
            round(sum(modal_values) / len(modal_values), 2)
            if modal_values else None
        ),
    }


# ============================================================
# CROP AND MARKET LISTS
# ============================================================

def get_available_crops(state=None, district=None, limit=1000):
    """Return unique crop names from live API records."""
    records = get_crop_prices(
        state=state,
        district=district,
        limit=limit,
    )

    crops = {
        _clean(item.get("commodity") or item.get("crop"))
        for item in records
    }

    return sorted(
        (crop_name for crop_name in crops if crop_name),
        key=str.casefold,
    )


def get_available_markets(state=None, district=None, limit=1000):
    """Return unique market names from live API records."""
    records = get_crop_prices(
        state=state,
        district=district,
        limit=limit,
    )

    markets = {
        _clean(item.get("market"))
        for item in records
    }

    return sorted(
        (market_name for market_name in markets if market_name),
        key=str.casefold,
    )


# ============================================================
# HEALTH AND SOURCE INFORMATION
# ============================================================

def market_api_health():
    """Test API configuration and whether records are returned."""
    if not DATA_GOV_API_KEY:
        return {
            "success": False,
            "connected": False,
            "message": "DATA_GOV_API_KEY is not configured.",
        }

    records = _request_data(limit=1)

    if records:
        return {
            "success": True,
            "connected": True,
            "message": "Data.gov.in returned market records.",
            "records_received": len(records),
            "source": "data.gov.in",
        }

    return {
        "success": False,
        "connected": False,
        "message": (
            "No market records received. The API may be unavailable, "
            "or the resource, key, or response schema may need checking."
        ),
        "source": "data.gov.in",
    }


def get_market_source_info():
    """Return safe source configuration without exposing the API key."""
    return {
        "source": "Data.gov.in",
        "resource_url": DATA_GOV_URL,
        "api_key_configured": bool(DATA_GOV_API_KEY),
        "timeout_seconds": REQUEST_TIMEOUT,
        "fake_data": False,
    }


def initialize_market_service():
    """Initialize the service without preventing Flask from starting."""
    if not DATA_GOV_API_KEY:
        logger.warning("Mandi API key is not configured.")
        return False

    logger.info("Mandi service initialized.")
    logger.info("Mandi resource URL: %s", DATA_GOV_URL)
    return True


__all__ = [
    "get_crop_prices",
    "get_market_price",
    "filter_market_prices",
    "calculate_market_summary",
    "get_available_crops",
    "get_available_markets",
    "market_api_health",
    "get_market_source_info",
    "initialize_market_service",
]
