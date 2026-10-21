
"""
KisanVision360 - Live Mandi Price Service
Source: https://mandi-api.onrender.com/v1/prices

Returns real API records only. If the API is unavailable, returns an
empty list instead of inventing prices.
"""

import logging
import os
from datetime import date, datetime, timezone

import requests

logger = logging.getLogger(__name__)

API_URL = os.getenv(
    "MANDI_API_URL",
    "https://mandi-api.onrender.com/v1/prices",
)
API_TIMEOUT = int(os.getenv("MANDI_API_TIMEOUT", "30"))


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _clean(value):
    """Convert a value to a clean string."""
    if value is None:
        return ""
    return str(value).strip()


def _number(value):
    """Convert a price to a number; return None if invalid."""
    if value is None or _clean(value) == "":
        return None

    try:
        number = float(_clean(value).replace(",", ""))
        return number if number >= 0 else None
    except (ValueError, TypeError):
        return None


def _normalize_record(record):
    """Normalize common field names while preserving original data."""
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

    for target, choices in aliases.items():
        for key in choices:
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


def _matches(value, requested):
    """Case-insensitive comparison; blank requested values match all."""
    if requested is None or _clean(requested) == "":
        return True

    return _clean(value).casefold() == _clean(requested).casefold()


# ---------------------------------------------------------
# API request
# ---------------------------------------------------------

def _request_data(
    commodity=None,
    state=None,
    district=None,
    market=None,
    limit=100,
    offset=0,
):
    """Fetch records from the configured Mandi API."""
    params = {
        "limit": max(1, min(int(limit), 500)),
        "offset": max(0, int(offset)),
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

        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            if payload.get("success") is False:
                logger.error("Mandi API reported success=false.")
                return []

            records = payload.get("data", [])

            # Support APIs that wrap records in another object.
            if isinstance(records, dict):
                for key in ("records", "data", "prices", "results"):
                    if isinstance(records.get(key), list):
                        records = records[key]
                        break
                else:
                    records = [records] if records else []
        else:
            logger.error("Mandi API returned an unsupported response.")
            return []

        if not isinstance(records, list):
            logger.error("Mandi API data field is not a list.")
            return []

        normalized = []

        for record in records:
            item = _normalize_record(record)
            if item is None:
                continue

            # Filter locally too, in case the API ignores query parameters.
            if not _matches(item.get("commodity"), commodity):
                continue
            if not _matches(item.get("state"), state):
                continue
            if not _matches(item.get("district"), district):
                continue
            if not _matches(item.get("market"), market):
                continue

            normalized.append(item)

        logger.info("Mandi API returned %d matching records.", len(normalized))
        return normalized

    except requests.exceptions.RequestException as exc:
        logger.error(
            "Mandi API request failed (%s): %s",
            type(exc).__name__,
            str(exc)[:300],
        )
    except (ValueError, TypeError) as exc:
        logger.error("Invalid Mandi API response: %s", str(exc)[:300])
    except Exception:
        logger.exception("Unexpected error fetching Mandi prices.")

    return []


# ---------------------------------------------------------
# Public functions used by KisanVision360
# ---------------------------------------------------------

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
    Get real prices for a crop.

    Example:
        get_crop_prices(
            crop="Onion",
            state="Maharashtra",
            limit=10,
        )
    """
    crop = crop or kwargs.get("commodity") or kwargs.get("crop_name")

    records = _request_data(
        commodity=crop,
        state=state,
        district=district,
        market=market,
        limit=limit,
        offset=offset,
    )

    return records


def get_available_crops(state=None, district=None):
    """Return crop names found in the API response."""
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
    """Return market names found in the API response."""
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


def market_api_health():
    """Check whether the API is reachable and returning valid data."""
    try:
        response = requests.get(
            API_URL,
            params={"limit": 1, "offset": 0},
            timeout=(5, API_TIMEOUT),
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()

        valid = isinstance(payload, (dict, list))
        if isinstance(payload, dict) and payload.get("success") is False:
            valid = False

        return {
            "reachable": valid,
            "status_code": response.status_code,
            "source": "Mandi API (third-party)",
            "message": (
                "API responded successfully."
                if valid
                else "API returned an unsuccessful response."
            ),
        }

    except Exception as exc:
        logger.warning("Mandi API health check failed: %s", str(exc)[:300])
        return {
            "reachable": False,
            "status_code": None,
            "source": "Mandi API (third-party)",
            "message": "Mandi API is currently unavailable.",
        }
