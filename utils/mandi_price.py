
"""
KisanVision360+ - Mandi Price Service

API:
    https://mandi-api.onrender.com/v1/prices

Provides:
    get_crop_prices()
    get_market_price()
    get_available_crops()
    get_available_markets()
    market_api_health()
    check_mandi_api()

Only real API records are returned. No sample or fabricated prices.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

API_URL = os.getenv(
    "MANDI_API_URL",
    "https://mandi-api.onrender.com/v1/prices",
)

try:
    API_TIMEOUT = max(5, int(os.getenv("MANDI_API_TIMEOUT", "30")))
except (TypeError, ValueError):
    API_TIMEOUT = 30


# =========================================================
# HELPERS
# =========================================================

def _clean(value):
    """Return a trimmed string."""
    return "" if value is None else str(value).strip()


def _number(value):
    """Convert a valid price to float, or None."""
    if value is None or _clean(value) == "":
        return None

    try:
        result = float(_clean(value).replace(",", ""))
        return result if result >= 0 else None
    except (TypeError, ValueError):
        return None


def _matches(value, requested):
    """Case-insensitive exact matching."""
    if requested is None or _clean(requested) == "":
        return True

    return _clean(value).casefold() == _clean(requested).casefold()


def _normalize_record(record):
    """Normalize API fields without discarding original fields."""
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

    for target, keys in aliases.items():
        for key in keys:
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
    """Read records from supported JSON response formats."""
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    if payload.get("success") is False:
        error = payload.get("error", "API reported failure")
        logger.warning("Mandi API error: %s", error)
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
            if isinstance(data.get(key), list):
                return data[key]

        if any(
            key in data
            for key in ("commodity", "crop", "modal_price")
        ):
            return [data]

    return []


# =========================================================
# FETCH MANDI RECORDS
# =========================================================

def _request_data(
    commodity=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
):
    """Fetch real price records from the Mandi API."""
    try:
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
    except (TypeError, ValueError):
        limit, offset = 100, 0

    # The API requires state or commodity.
    # Do not make an unfiltered request.
    if not state and not commodity:
        logger.warning(
            "Mandi API requires at least one of state or commodity."
        )
        return []

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

            # Apply local filtering in case the API ignores a filter.
            if not _matches(item.get("commodity"), commodity):
                continue
            if not _matches(item.get("state"), state):
                continue
            if not _matches(item.get("district"), district):
                continue
            if not _matches(item.get("market"), market):
                continue

            results.append(item)

        logger.info(
            "Mandi API returned %d records.",
            len(results),
        )
        return results

    except requests.exceptions.HTTPError as exc:
        status = (
            exc.response.status_code
            if exc.response is not None
            else None
        )
        body = (
            exc.response.text[:300]
            if exc.response is not None
            else ""
        )
        logger.error(
            "Mandi API HTTP error %s: %s",
            status,
            body,
        )

    except requests.exceptions.RequestException as exc:
        logger.error(
            "Mandi API request failed (%s): %s",
            type(exc).__name__,
            str(exc)[:300],
        )

    except (ValueError, TypeError) as exc:
        logger.error(
            "Invalid Mandi API response: %s",
            str(exc)[:300],
        )

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
    """Get real prices for a crop and optional location filters."""
    crop = (
        crop
        or kwargs.get("commodity")
        or kwargs.get("crop_name")
    )

    state = state or kwargs.get("state_name")
    district = district or kwargs.get("district_name")
    market = market or kwargs.get("market_name")

    return _request_data(
        commodity=crop,
        state=state,
        district=district,
        market=market,
        limit=limit,
        offset=offset,
    )


def get_market_price(
    crop=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
    **kwargs,
):
    """
    Compatibility function for existing market blueprint imports.

    Supports calls using crop=, commodity= or crop_name=.
    Returns a list of normalized records.
    """
    return get_crop_prices(
        crop=crop,
        state=state,
        district=district,
        market=market,
        limit=limit,
        offset=offset,
        **kwargs,
    )


def get_available_crops(state=None, district=None):
    """List distinct crops returned by the API."""
    records = _request_data(
        state=state,
        district=district,
        limit=500,
    )

    return sorted(
        {
            _clean(record.get("commodity"))
            for record in records
            if _clean(record.get("commodity"))
        },
        key=str.casefold,
    )


def get_available_markets(
    state=None,
    district=None,
    commodity=None,
):
    """List distinct markets returned by the API."""
    records = _request_data(
        commodity=commodity,
        state=state,
        district=district,
        limit=500,
    )

    return sorted(
        {
            _clean(record.get("market"))
            for record in records
            if _clean(record.get("market"))
        },
        key=str.casefold,
    )


# =========================================================
# API HEALTH CHECK
# =========================================================

def market_api_health():
    """Check API connectivity using the required commodity parameter."""
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
                "message": (
                    f"API returned HTTP {status_code}: {message}"
                ),
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

        if isinstance(payload, dict) and payload.get("success") is False:
            return {
                "reachable": False,
                "status_code": status_code,
                "source": "Mandi API (third-party)",
                "message": str(payload.get("error", "API request failed")),
            }

        if not isinstance(payload, (dict, list)):
            return {
                "reachable": False,
                "status_code": status_code,
                "source": "Mandi API (third-party)",
                "message": "Unexpected API response format.",
            }

        return {
            "reachable": True,
            "status_code": status_code,
            "source": "Mandi API (third-party)",
            "message": "Mandi API responded successfully.",
        }

    except requests.exceptions.RequestException as exc:
        logger.warning(
            "Mandi API health check failed: %s",
            str(exc)[:300],
        )
        return {
            "reachable": False,
            "status_code": None,
            "source": "Mandi API (third-party)",
            "message": str(exc)[:300],
        }

    except Exception as exc:
        logger.exception("Unexpected Mandi API health-check error.")
        return {
            "reachable": False,
            "status_code": None,
            "source": "Mandi API (third-party)",
            "message": str(exc)[:300],
        }


def check_mandi_api():
    """Backward-compatible health-check alias."""
    return market_api_health()
