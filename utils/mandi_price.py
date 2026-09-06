
"""
KisanVision360+
Mandi / Market Price Utility

Data Source:
Data.gov.in - Current Daily Price of Various Commodities
from Various Markets (Mandi)

File:
utils/mandi_price.py

IMPORTANT:
- No fake/demo prices
- API key comes from .env
- Uses official Data.gov.in Mandi resource
"""

import os
import logging
from datetime import datetime

import requests


logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

# Official Data.gov.in Mandi resource
DEFAULT_MANDI_RESOURCE_URL = (
    "https://api.data.gov.in/resource/"
    "9ef84268-d588-465a-a308-a864a43d0070"
)

DATA_GOV_URL = os.getenv(
    "DATA_GOV_RESOURCE_URL",
    DEFAULT_MANDI_RESOURCE_URL
).strip()

# IMPORTANT:
# getenv() must contain the ENVIRONMENT VARIABLE NAME,
# NOT the actual API key.
DATA_GOV_API_KEY = os.getenv(
    "DATA_GOV_API_KEY",
    ""
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
    """Convert value to a clean string."""
    if value is None:
        return ""

    return str(value).strip()


def _first_value(record, *keys):
    """
    Return the first non-empty value from a record.
    Data.gov.in field names may vary slightly.
    """

    if not isinstance(record, dict):
        return ""

    for key in keys:
        if key in record:
            value = record.get(key)

            if value is not None:
                text = str(value).strip()

                if text:
                    return text

    return ""


def _to_float(value):
    """Safely convert a price value to float."""

    if value is None:
        return None

    try:
        text = str(value).strip()

        if not text:
            return None

        text = (
            text
            .replace(",", "")
            .replace("â‚¹", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .strip()
        )

        return float(text)

    except (ValueError, TypeError):
        return None


def _normalize_record(record):
    """
    Convert Data.gov.in Mandi record into
    KisanVision360+ standard format.
    """

    if not isinstance(record, dict):
        return None

    crop = _first_value(
        record,
        "commodity",
        "Commodity",
        "crop",
        "Crop",
        "commodity_name",
        "Commodity_Name"
    )

    market = _first_value(
        record,
        "market",
        "Market",
        "market_name",
        "Market_Name",
        "mandi",
        "Mandi"
    )

    state = _first_value(
        record,
        "state",
        "State",
        "state_name",
        "State_Name"
    )

    district = _first_value(
        record,
        "district",
        "District",
        "district_name",
        "District_Name"
    )

    variety = _first_value(
        record,
        "variety",
        "Variety"
    )

    grade = _first_value(
        record,
        "grade",
        "Grade"
    )

    min_price = _first_value(
        record,
        "min_price",
        "Min_Price",
        "minimum_price",
        "Minimum_Price"
    )

    max_price = _first_value(
        record,
        "max_price",
        "Max_Price",
        "maximum_price",
        "Maximum_Price"
    )

    modal_price = _first_value(
        record,
        "modal_price",
        "Modal_Price",
        "modal",
        "Modal"
    )

    arrival_date = _first_value(
        record,
        "arrival_date",
        "Arrival_Date",
        "date",
        "Date",
        "reported_date"
    )

    # Ignore completely empty records
    if not any(
        [
            crop,
            market,
            state,
            district,
            min_price,
            max_price,
            modal_price
        ]
    ):
        return None

    return {
        "crop": crop or "Unknown",
        "commodity": crop or "Unknown",

        "market": market or "Unknown",

        "state": state or "",

        "district": district or "",

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

        "raw": record
    }


# ============================================================
# API REQUEST
# ============================================================

def _request_data(
    crop=None,
    state=None,
    district=None,
    market=None,
    limit=100
):
    """
    Request Mandi records from Data.gov.in.

    Returns:
        list[dict]
    """

    if not DATA_GOV_API_KEY:
        logger.error(
            "DATA_GOV_API_KEY is not configured."
        )
        return []

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 100

    limit = max(1, min(limit, 1000))

    params = {
        "api-key": DATA_GOV_API_KEY,
        "format": "json",
        "limit": limit
    }

    # --------------------------------------------------------
    # Data.gov.in filters
    # --------------------------------------------------------

    if crop:
        params["filters[commodity]"] = str(crop).strip()

    if state:
        params["filters[state]"] = str(state).strip()

    if district:
        params["filters[district]"] = str(district).strip()

    if market:
        params["filters[market]"] = str(market).strip()

    logger.info(
        "Requesting Data.gov.in Mandi data: %s",
        DATA_GOV_URL
    )

    try:

        response = requests.get(
            DATA_GOV_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={
                "Accept": "application/json",
                "User-Agent": "KisanVision360+/1.0"
            }
        )

        logger.info(
            "Data.gov.in response status: %s",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            logger.error(
                "Data.gov.in returned non-dictionary JSON."
            )
            return []

        records = data.get("records", [])

        if not isinstance(records, list):
            logger.error(
                "Data.gov.in 'records' is not a list."
            )
            return []

        logger.info(
            "Data.gov.in records received: %s",
            len(records)
        )

        return records

    except requests.exceptions.Timeout:
        logger.error(
            "Data.gov.in request timed out after %s seconds.",
            REQUEST_TIMEOUT
        )
        return []

    except requests.exceptions.HTTPError as exc:

        status = (
            response.status_code
            if response is not None
            else "unknown"
        )

        logger.error(
            "Data.gov.in HTTP error %s: %s",
            status,
            exc
        )

        # Log response body when available
        if response is not None:
            try:
                logger.error(
                    "Data.gov.in response: %s",
                    response.text[:1000]
                )
            except Exception:
                pass

        return []

    except requests.exceptions.RequestException as exc:

        logger.error(
            "Data.gov.in request error: %s",
            exc
        )

        return []

    except ValueError:

        logger.error(
            "Data.gov.in returned invalid JSON."
        )

        return []

    except Exception:

        logger.exception(
            "Unexpected Data.gov.in error."
        )

        return []


# ============================================================
# GET CROP PRICES
# ============================================================

def get_crop_prices(
    crop=None,
    state=None,
    district=None,
    market=None,
    limit=100
):
    """
    Get Mandi prices from Data.gov.in.

    Example:

        get_crop_prices(
            crop="Wheat",
            state="Maharashtra",
            district="Nagpur"
        )
    """

    records = _request_data(
        crop=crop,
        state=state,
        district=district,
        market=market,
        limit=limit
    )

    normalized = []

    for record in records:

        item = _normalize_record(record)

        if item:
            normalized.append(item)

    # --------------------------------------------------------
    # Local filtering
    # --------------------------------------------------------

    return filter_market_prices(
        normalized,
        crop=crop,
        state=state,
        district=district,
        market=market
    )


# ============================================================
# GET MARKET PRICE FOR ONE CROP
# ============================================================

def get_market_price(crop=None):
    """
    Get Mandi prices for one crop.

    Example:

        get_market_price("Wheat")
    """

    return get_crop_prices(
        crop=crop,
        limit=100
    )


# ============================================================
# LOCAL FILTERING
# ============================================================

def filter_market_prices(
    records,
    crop=None,
    state=None,
    district=None,
    market=None
):
    """
    Perform additional local filtering.

    This protects the application if Data.gov.in
    ignores one of the supplied filters.
    """

    if not records:
        return []

    crop_text = _clean(crop).lower()
    state_text = _clean(state).lower()
    district_text = _clean(district).lower()
    market_text = _clean(market).lower()

    result = []

    for item in records:

        if crop_text:

            value = (
                _clean(item.get("crop"))
                or _clean(item.get("commodity"))
            ).lower()

            if crop_text not in value:
                continue

        if state_text:

            value = _clean(
                item.get("state")
            ).lower()

            if state_text not in value:
                continue

        if district_text:

            value = _clean(
                item.get("district")
            ).lower()

            if district_text not in value:
                continue

        if market_text:

            value = _clean(
                item.get("market")
            ).lower()

            if market_text not in value:
                continue

        result.append(item)

    return result


# ============================================================
# PRICE SUMMARY
# ============================================================

def calculate_market_summary(records):
    """
    Calculate market price statistics.
    """

    if not records:

        return {
            "records": 0,
            "min_price": None,
            "max_price": None,
            "average_modal_price": None
        }

    min_values = []
    max_values = []
    modal_values = []

    for item in records:

        min_price = item.get("min_price")

        if min_price is not None:
            try:
                min_values.append(
                    float(min_price)
                )
            except (ValueError, TypeError):
                pass

        max_price = item.get("max_price")

        if max_price is not None:
            try:
                max_values.append(
                    float(max_price)
                )
            except (ValueError, TypeError):
                pass

        modal_price = item.get("modal_price")

        if modal_price is not None:
            try:
                modal_values.append(
                    float(modal_price)
                )
            except (ValueError, TypeError):
                pass

    return {
        "records": len(records),

        "min_price": (
            min(min_values)
            if min_values
            else None
        ),

        "max_price": (
            max(max_values)
            if max_values
            else None
        ),

        "average_modal_price": (
            round(
                sum(modal_values)
                / len(modal_values),
                2
            )
            if modal_values
            else None
        )
    }


# ============================================================
# CROP LIST
# ============================================================

def get_available_crops(
    state=None,
    district=None,
    limit=1000
):
    """
    Get unique crop/commodity names.
    """

    records = get_crop_prices(
        state=state,
        district=district,
        limit=limit
    )

    crops = set()

    for item in records:

        crop = _clean(
            item.get("commodity")
            or item.get("crop")
        )

        if crop:
            crops.add(crop)

    return sorted(
        crops,
        key=lambda value: value.lower()
    )


# ============================================================
# MARKET LIST
# ============================================================

def get_available_markets(
    state=None,
    district=None,
    limit=1000
):
    """
    Get unique Mandi/market names.
    """

    records = get_crop_prices(
        state=state,
        district=district,
        limit=limit
    )

    markets = set()

    for item in records:

        market = _clean(
            item.get("market")
        )

        if market:
            markets.add(market)

    return sorted(
        markets,
        key=lambda value: value.lower()
    )


# ============================================================
# HEALTH CHECK
# ============================================================

def market_api_health():
    """
    Check Data.gov.in Mandi API.
    """

    if not DATA_GOV_API_KEY:

        return {
            "success": False,
            "connected": False,
            "message": (
                "DATA_GOV_API_KEY is not configured."
            )
        }

    records = _request_data(
        limit=1
    )

    if records:

        return {
            "success": True,
            "connected": True,
            "message": (
                "Data.gov.in Mandi API "
                "is responding."
            ),
            "records_received": len(records),
            "source": "data.gov.in"
        }

    return {
        "success": False,
        "connected": False,
        "message": (
            "Data.gov.in returned no records. "
            "Check API key, resource URL, "
            "network connection and dataset."
        ),
        "source": "data.gov.in"
    }


# ============================================================
# MODULE INFORMATION
# ============================================================

def get_market_source_info():
    """
    Return configuration information useful for
    debugging/API health pages.

    API key itself is NEVER returned.
    """

    return {
        "source": "Data.gov.in",
        "resource_url": DATA_GOV_URL,
        "api_key_configured": bool(DATA_GOV_API_KEY),
        "timeout_seconds": REQUEST_TIMEOUT,
        "fake_data": False
    }


# ============================================================
# STARTUP CHECK
# ============================================================

def initialize_market_service():
    """
    Initialize/check market service.

    Does not crash the application if Data.gov.in
    is temporarily unavailable.
    """

    if not DATA_GOV_API_KEY:

        logger.warning(
            "Mandi service: DATA_GOV_API_KEY missing."
        )

        return False

    logger.info(
        "Mandi service initialized."
    )

    logger.info(
        "Mandi resource: %s",
        DATA_GOV_URL
    )

    return True


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "get_crop_prices",
    "get_market_price",
    "filter_market_prices",
    "calculate_market_summary",
    "get_available_crops",
    "get_available_markets",
    "market_api_health",
    "get_market_source_info",
    "initialize_market_service"
]

