
"""
KisanVision360+
Mandi / Market Price Utility

Data source:
Data.gov.in - Current Daily Price of Various Commodities
from Various Markets (Mandi).

Features:
- Loads environment variables from the project-root .env file.
- Retrieves genuine market records from Data.gov.in.
- Supports crop, state, district, and market filters.
- Normalizes prices and calculates market summaries.
- Does not generate fake/demo prices.
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

# Load .env from the project root, not the current terminal folder.
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

DATA_GOV_API_KEY = os.getenv(
    "DATA_GOV_API_KEY", ""
).strip()

try:
    REQUEST_TIMEOUT = int(
        os.getenv("DATA_GOV_TIMEOUT", "15")
    )
except (TypeError, ValueError):
    REQUEST_TIMEOUT = 15

REQUEST_TIMEOUT = max(5, min(REQUEST_TIMEOUT, 60))


# ============================================================
# COMMON HELPERS
# ============================================================

def _clean(value):
    """Convert a value to a trimmed string."""
    if value is None:
        return ""
    return str(value).strip()


def _first_value(record, *keys):
    """Return the first non-empty value from a record."""
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
    """Convert a price to float, or None if invalid."""
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

        return float(text)

    except (ValueError, TypeError):
        return None


def _normalize_record(record):
    """Normalize a Data.gov.in record for the application."""
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

    # Do not return records that contain no useful market data.
    if not any((
        crop, market, state, district,
        min_price, max_price, modal_price,
    )):
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
        "fetched_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
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
):
    """Fetch genuine market records from Data.gov.in."""
    if not DATA_GOV_API_KEY:
        logger.error(
            "DATA_GOV_API_KEY is missing. "
            "Check the project-root .env file."
        )
        return []

    try:
        limit = max(1, min(int(limit), 1000))
    except (TypeError, ValueError):
        limit = 100

    params = {
        "api-key": DATA_GOV_API_KEY,
        "format": "json",
        "limit": limit,
    }

    if crop:
        params["filters[commodity]"] = str(crop).strip()

    if state:
        params["filters[state]"] = str(state).strip()

    if district:
        params["filters[district]"] = str(district).strip()

    if market:
        params["filters[market]"] = str(market).strip()

    logger.info("Requesting Data.gov.in market data.")

    try:
        response = requests.get(
            DATA_GOV_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={
                "Accept": "application/json",
                "User-Agent": "KisanVision360Plus/1.0",
            },
        )

        logger.info(
            "Data.gov.in HTTP status: %s",
            response.status_code,
        )

        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            logger.error(
                "Data.gov.in returned an unexpected JSON format."
            )
            return []

        records = data.get("records", [])

        if not isinstance(records, list):
            logger.error(
                "Data.gov.in response has no valid records list."
            )
            return []

        logger.info(
            "Data.gov.in records received: %s",
            len(records),
        )

        if not records:
            logger.warning(
                "Data.gov.in returned zero records. "
                "Check resource URL, API key and filters."
            )

        return records

    except requests.exceptions.Timeout:
        logger.error(
            "Data.gov.in timed out after %s seconds.",
            REQUEST_TIMEOUT,
        )

    except requests.exceptions.HTTPError as exc:
        status = (
            response.status_code
            if "response" in locals()
            else "unknown"
        )

        logger.error(
            "Data.gov.in HTTP error %s: %s",
            status,
            exc,
        )

        if "response" in locals():
            # Do not log the complete request URL: it contains the API key.
            logger.error(
                "Data.gov.in response body: %s",
                response.text[:500],
            )

    except requests.exceptions.RequestException as exc:
        logger.error(
            "Data.gov.in request failed: %s",
            exc,
        )

    except ValueError:
        logger.error(
            "Data.gov.in returned invalid JSON."
        )

    except Exception:
        logger.exception(
            "Unexpected error requesting Data.gov.in."
        )

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
    """Filter normalized market records without fabricating data."""
    if not records:
        return []

    crop_text = _clean(crop).casefold()
    state_text = _clean(state).casefold()
    district_text = _clean(district).casefold()
    market_text = _clean(market).casefold()

    result = []

    for item in records:
        if crop_text:
            value = _clean(
                item.get("crop") or item.get("commodity")
            ).casefold()
            if crop_text not in value:
                continue

        if state_text:
            if state_text not in _clean(
                item.get("state")
            ).casefold():
                continue

        if district_text:
            if district_text not in _clean(
                item.get("district")
            ).casefold():
                continue

        if market_text:
            if market_text not in _clean(
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
):
    """Return normalized Data.gov.in prices with optional filters."""
    records = _request_data(
        crop=crop,
        state=state,
        district=district,
        market=market,
        limit=limit,
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
    """Return market records for one crop, or recent records if omitted."""
    return get_crop_prices(crop=crop, limit=100)


# ============================================================
# PRICE SUMMARY
# ============================================================

def calculate_market_summary(records):
    """Calculate min, max and average modal prices."""
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
        (crop for crop in crops if crop),
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
        (market for market in markets if market),
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
            "No records returned. Check the API key, resource URL, "
            "network connection and Data.gov.in response."
        ),
        "source": "data.gov.in",
    }


def get_market_source_info():
    """Return safe configuration information without exposing the key."""
    return {
        "source": "Data.gov.in",
        "resource_url": DATA_GOV_URL,
        "api_key_configured": bool(DATA_GOV_API_KEY),
        "timeout_seconds": REQUEST_TIMEOUT,
        "fake_data": False,
    }


def initialize_market_service():
    """Initialize the service without stopping Flask on API failure."""
    if not DATA_GOV_API_KEY:
        logger.warning(
            "Mandi service: DATA_GOV_API_KEY is missing."
        )
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
