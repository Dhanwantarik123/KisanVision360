
"""
KisanVision360 - Mandi Price Service

API:
    https://mandi-api.onrender.com/v1/prices

Features:
    - Fetches real API price records
    - Filters by crop, state, district and market
    - Normalizes price and market fields
    - Lists available crops and markets
    - Checks API health without assuming query parameters
    - Never generates fake prices

Note:
    API records can be older than today. Check arrival_date before
    presenting a price as current.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

API_URL = os.getenv(
    "MANDI_API_URL",
    "https://mandi-api.onrender.com/v1/prices",
)
API_TIMEOUT = int(os.getenv("MANDI_API_TIMEOUT", "30"))


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def _clean(value):
    """Convert a value to a trimmed string."""
    if value is None:
        return ""
    return str(value).strip()


def _number(value):
    """Convert a valid price to float; otherwise return None."""
    if value is None or _clean(value) == "":
        return None

    try:
        result = float(_clean(value).replace(",", ""))
        return result if result >= 0 else None
    except (ValueError, TypeError):
        return None


def _matches(value, requested):
    """Case-insensitive exact match; empty filters match everything."""
    if requested is None or _clean(requested) == "":
        return True

    return _clean(value).casefold() == _clean(requested).casefold()


def _normalize_record(record):
    """Normalize common API fields while preserving original fields."""
    if not isinstance(record, dict):
        return None

    item = dict(record)

    aliases = {
        "state": ("state", "state_name"),
        "district": ("district", "district_name"),
        "market": ("market", "market_name", "mandi"),
        "commodity": ("commodity", "crop", "commodity_name"),
        "variety": ("variety", "variety_name"),
        "grade": ("grade", "quality"),
        "arrival_date": ("arrival_date", "date", "price_date"),
        "min_price": ("min_price", "minimum_price"),
        "max_price": ("max_price", "maximum_price"),
        "modal_price": ("modal_price", "modal", "price"),
    }

    for target, possible_keys in aliases.items():
        for key in possible_keys:
            if key in record and record[key] is not None:
                item[target] = record[key]
                break

    for field in (
        "state",
        "district",
        "market",
        "commodity",
        "variety",
        "grade",
        "arrival_date",
    ):
        item[field] = _clean(item.get(field)) or None

    for field in ("min_price", "max_price", "modal_price"):
        item[field] = _number(item.get(field))

    item["source"] = "Mandi API (third-party)"
    return item


def _extract_records(payload):
    """Extract records from common JSON response structures."""
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    if payload.get("success") is False:
        logger.warning("Mandi API returned success=false.")
        return []

    data = payload.get("data")

    if data is None:
        for key in ("records", "prices", "results"):
            if isinstance(payload.get(key), list):
                data = payload[key]
                break

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("records", "data", "prices", "results"):
            nested = data.get(key)
            if isinstance(nested, list):
                return nested

        # Support an API returning a single record as an object.
        if any(key in data for key in ("commodity", "crop", "modal_price")):
            return [data]

    return []


# =========================================================
# API REQUEST
# =========================================================

def _request_data(
    commodity=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
):
    """Fetch and filter price records from the Mandi API."""
    try:
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
    except (ValueError, TypeError):
        limit, offset = 100, 0

    params = {
        "limit": limit,
        "offset": offset,
    }

    if commodity:
        params["commodity"] = commodity
    if state:
        params["state"] = state
    if district:
        params["district"] = district
    if market:
        params["market"] = market

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=(5, API_TIMEOUT),
            headers={"Accept": "application/json"},
        )

        response.raise_for_status()
        payload = response.json()
        records = _extract_records(payload)

        results = []

        for record in records:
            item = _normalize_record(record)
            if item is None:
                continue

            # Apply filters locally, even if the API ignores parameters.
            if not _matches(item.get("commodity"), commodity):
                continue
            if not _matches(item.get("state"), state):
                continue
            if not _matches(item.get("district"), district):
                continue
            if not _matches(item.get("market"), market):
                continue

            results.append(item)

        logger.info("Mandi API returned %d matching records.", len(results))
        return results

    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        body = exc.response.text[:300] if exc.response is not None else ""
        logger.error(
            "Mandi API HTTP error %s: %s",
            status,
            body,
        )
    except requests.exceptions.RequestException as exc:
        logger.error(
            "Mandi API connection failed (%s): %s",
            type(exc).__name__,
            str(exc)[:300],
        )
    except (ValueError, TypeError) as exc:
        logger.error("Invalid Mandi API response: %s", str(exc)[:300])
    except Exception:
        logger.exception("Unexpected error fetching Mandi prices.")

    return []


# =========================================================
# PUBLIC PRICE FUNCTIONS
# =========================================================

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
    Get actual API prices.

    Examples:
        get_crop_prices(crop="Onion", state="Maharashtra")
        get_crop_prices(
            crop="Onion",
            state="Maharashtra",
            district="Nagpur",
            limit=10,
        )

    Returns:
        A list of normalized price dictionaries.
        Returns [] when the API fails or has no matching records.
    """
    crop = (
        crop
        or kwargs.get("commodity")
        or kwargs.get("crop_name")
    )

    return _request_data(
        commodity=crop,
        state=state,
        district=district,
        market=market,
        limit=limit,
        offset=offset,
    )


def get_available_crops(state=None, district=None):
    """Return distinct crop names present in API records."""
    records = _request_data(
        state=state,
        district=district,
        limit=500,
    )

    crops = {
        _clean(record.get("commodity"))
        for record in records
        if _clean(record.get("commodity"))
    }

    return sorted(crops, key=str.casefold)


def get_available_markets(state=None, district=None, commodity=None):
    """Return distinct market names present in API records."""
    records = _request_data(
        commodity=commodity,
        state=state,
        district=district,
        limit=500,
    )

    markets = {
        _clean(record.get("market"))
        for record in records
        if _clean(record.get("market"))
    }

    return sorted(markets, key=str.casefold)


# =========================================================
# API HEALTH CHECK
# =========================================================


def market_api_health():
    """Check Mandi API using a required query parameter."""
    try:
        response = requests.get(
            API_URL,
            params={
                "state": "Maharashtra",
                "commodity": "Onion",
            },
            timeout=(5, API_TIMEOUT),
            headers={"Accept": "application/json"},
        )

        status_code = response.status_code

        if status_code != 200:
            message = response.text[:300]
            logger.warning(
                "Mandi API health check returned HTTP %s: %s",
                status_code,
                message,
            )
            return {
                "reachable": False,
                "status_code": status_code,
                "source": "Mandi API (third-party)",
                "message": f"API returned HTTP {status_code}: {message}",
            }

        try:
            payload = response.json()
        except ValueError:
            return {
                "reachable": False,
                "status_code": status_code,
                "source": "Mandi API (third-party)",
                "message": "API returned invalid JSON.",
            }

        if not isinstance(payload, (dict, list)):
            return {
                "reachable": False,
                "status_code": status_code,
                "source": "Mandi API (third-party)",
                "message": "Unexpected API response format.",
            }

        if isinstance(payload, dict) and payload.get("success") is False:
            return {
                "reachable": False,
                "status_code": status_code,
                "source": "Mandi API (third-party)",
                "message": str(payload.get("error", "API request failed")),
            }

        return {
            "reachable": True,
            "status_code": status_code,
            "source": "Mandi API (third-party)",
            "message": "Mandi API responded successfully.",
        }

    except requests.exceptions.RequestException as exc:
        logger.warning("Mandi API health check failed: %s", str(exc)[:300])
        return {
            "reachable": False,
            "status_code": None,
            "source": "Mandi API (third-party)",
            "message": str(exc)[:300],
        }



# Optional alias for older code that uses this function name.
def check_mandi_api():
    """Backward-compatible alias for the API health check."""
    return market_api_health()
