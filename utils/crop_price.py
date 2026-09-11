# ============================================================
# KISANVISION360+
# MANDI / CROP PRICE SERVICE
# ============================================================

import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

DATA_GOV_RESOURCE_URL = os.getenv(
    "DATA_GOV_RESOURCE_URL",
    ""
)

DATA_GOV_API_KEY = os.getenv(
    "DATA_GOV_API_KEY",
    ""
)

REQUEST_TIMEOUT = int(
    os.getenv(
        "MANDI_API_TIMEOUT",
        "20"
    )
)


# ============================================================
# SESSION
# ============================================================

_http_session = requests.Session()

_http_session.headers.update(
    {
        "User-Agent":
            "KisanVision360+/1.0",
        "Accept":
            "application/json"
    }
)


# ============================================================
# NUMBER CONVERSION
# ============================================================

def _to_float(
    value: Any
) -> Optional[float]:

    if value is None:
        return None

    try:

        text = str(
            value
        ).strip()

        if not text:
            return None

        text = (
            text
            .replace(",", "")
            .replace("₹", "")
        )

        return float(
            text
        )

    except (
        TypeError,
        ValueError
    ):

        return None


# ============================================================
# RECORD VALUE HELPER
# ============================================================

def _get_value(
    record: Dict[str, Any],
    *keys: str
) -> Any:

    for key in keys:

        if key in record:

            value = record.get(
                key
            )

            if value not in (
                None,
                ""
            ):

                return value

    # Case-insensitive fallback

    lowered = {
        str(k).lower(): v
        for k, v in record.items()
    }

    for key in keys:

        value = lowered.get(
            key.lower()
        )

        if value not in (
            None,
            ""
        ):

            return value

    return None


# ============================================================
# NORMALIZE MANDI RECORD
# ============================================================

def normalize_price_record(
    item: Dict[str, Any]
) -> Optional[Dict[str, Any]]:

    if not isinstance(
        item,
        dict
    ):

        return None


    commodity = _get_value(
        item,
        "commodity",
        "Commodity",
        "crop",
        "Crop",
        "commodity_name"
    )


    market = _get_value(
        item,
        "market",
        "Market",
        "mandi",
        "Mandi",
        "market_name"
    )


    state = _get_value(
        item,
        "state",
        "State",
        "state_name"
    )


    district = _get_value(
        item,
        "district",
        "District",
        "district_name"
    )


    modal_price = _get_value(
        item,
        "modal_price",
        "Modal_Price",
        "modal price",
        "Modal Price"
    )


    min_price = _get_value(
        item,
        "min_price",
        "Min_Price",
        "minimum_price",
        "Min Price"
    )


    max_price = _get_value(
        item,
        "max_price",
        "Max_Price",
        "maximum_price",
        "Max Price"
    )


    arrival_date = _get_value(
        item,
        "arrival_date",
        "Arrival_Date",
        "arrival date",
        "date",
        "Date"
    )


    if not commodity:

        return None


    modal = _to_float(modal_price)


    minimum = _to_float(min_price)


    maximum = _to_float(max_price)


    return {

        "commodity":
            str(
                commodity
            ).strip(),

        "market":
            str(
                market or ""
            ).strip(),

        "state":
            str(
                state or ""
            ).strip(),

        "district":
            str(
                district or ""
            ).strip(),

        "modal_price":
            modal,

        "min_price":
            minimum,

        "max_price":
            maximum,

        "arrival_date":
            str(
                arrival_date or ""
            ).strip(),

        "updated_at":
            datetime.utcnow()
                .isoformat()

    }


# ============================================================
# FETCH RAW MANDI DATA
# ============================================================

def fetch_mandi_records(
    limit: int = 100,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:

    if not DATA_GOV_RESOURCE_URL:

        logger.warning(
            "DATA_GOV_RESOURCE_URL is not configured."
        )

        return []


    params = {}


    if DATA_GOV_API_KEY:

        params[
            "api-key"
        ] = DATA_GOV_API_KEY


    params[
        "format"
    ] = "json"


    params[
        "limit"
    ] = max(
        1,
        min(
            int(limit),
            1000
        )
    )


    if offset > 0:

        params[
            "offset"
        ] = int(
            offset
        )


    # --------------------------------------------------------
    # Optional API filters
    # --------------------------------------------------------

    if filters:

        for key, value in filters.items():

            if value in (
                None,
                ""
            ):

                continue


            params[
                key
            ] = value


    try:

        response = _http_session.get(
                DATA_GOV_RESOURCE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )


        response.raise_for_status()


        data = response.json()


        records = data.get(
                "records",
                []
            )


        if not isinstance(
            records,
            list
        ):

            logger.warning(
                "Unexpected mandi API response format."
            )

            return []


        return records


    except requests.RequestException as exc:

        logger.error(
            "Mandi API request failed: %s",
            exc
        )

        return []


    except ValueError as exc:

        logger.error(
            "Invalid JSON received from mandi API: %s",
            exc
        )

        return []


    except Exception as exc:

        logger.exception(
            "Unexpected mandi service error: %s",
            exc
        )

        return []


# ============================================================
# GET NORMALIZED CROP PRICES
# ============================================================

def get_crop_price_records(
    limit: int = 100
) -> List[Dict[str, Any]]:

    records = fetch_mandi_records(
            limit=limit
        )


    normalized = []


    for item in records:

        record = normalize_price_record(
                item
            )


        if record:

            normalized.append(
                record
            )


    return normalized


# ============================================================
# GET CROP PRICES AS DICTIONARY
# ============================================================

def get_crop_prices() -> Dict[str, float]:

    records = get_crop_price_records()


    crop_prices = {}


    for item in records:

        commodity = item.get(
                "commodity"
            )


        modal_price = item.get(
                "modal_price"
            )


        if (
            commodity and
            modal_price is not None
        ):

            crop_prices[
                commodity
            ] = float(
                modal_price
            )


    return crop_prices


# ============================================================
# SEARCH CROP
# ============================================================

def search_crop_prices(
    crop_name: str,
    limit: int = 100
) -> List[Dict[str, Any]]:

    crop_name = str(
            crop_name or ""
        ).strip()


    if not crop_name:

        return []


    records = get_crop_price_records(
            limit=limit
        )


    search_text = crop_name.lower()


    results = []


    for item in records:

        commodity = str(
                item.get(
                    "commodity",
                    ""
                )
            ).lower()


        if search_text in commodity:

            results.append(
                item
            )


    return results


# ============================================================
# FILTER BY STATE
# ============================================================

def get_state_prices(
    state: str,
    limit: int = 100
) -> List[Dict[str, Any]]:

    state = str(
            state or ""
        ).strip().lower()


    if not state:

        return []


    records = get_crop_price_records(
            limit=limit
        )


    return [
        item
        for item in records
        if state in
        str(
            item.get(
                "state",
                ""
            )
        ).lower()
    ]


# ============================================================
# FILTER BY MARKET
# ============================================================

def get_market_prices(
    market: str,
    limit: int = 100
) -> List[Dict[str, Any]]:

    market = str(
            market or ""
        ).strip().lower()


    if not market:

        return []


    records = get_crop_price_records(
            limit=limit
        )


    return [
        item
        for item in records
        if market in
        str(
            item.get(
                "market",
                ""
            )
        ).lower()
    ]


# ============================================================
# PRICE RANGE
# ============================================================

def get_price_range(
    crop_name: str
) -> Dict[str, Optional[float]]:

    records = search_crop_prices(
            crop_name
        )


    minimum_values = []
    maximum_values = []
    modal_values = []


    for item in records:

        if item.get(
            "min_price"
        ) is not None:

            minimum_values.append(
                item[
                    "min_price"
                ]
            )


        if item.get(
            "max_price"
        ) is not None:

            maximum_values.append(
                item[
                    "max_price"
                ]
            )


        if item.get(
            "modal_price"
        ) is not None:

            modal_values.append(
                item[
                    "modal_price"
                ]
            )


    return {

        "min_price":
            min(
                minimum_values
            )
            if minimum_values
            else None,

        "max_price":
            max(
                maximum_values
            )
            if maximum_values
            else None,

        "average_modal_price":
            (
                sum(
                    modal_values
                )
                /
                len(
                    modal_values
                )
            )
            if modal_values
            else None

    }


# ============================================================
# CROP PRICE INTELLIGENCE
# ============================================================

def get_price_intelligence(
    crop_name: str
) -> Dict[str, Any]:

    records = search_crop_prices(
            crop_name
        )


    if not records:

        return {

            "crop":
                crop_name,

            "available":
                False,

            "message":
                "No current mandi price record was found."

        }


    modal_prices = [
        item["modal_price"]
        for item in records
        if item.get(
            "modal_price"
        ) is not None
    ]


    if not modal_prices:

        return {

            "crop":
                crop_name,

            "available":
                False,

            "message":
                "Mandi records were found, but modal price is unavailable."

        }


    average_price = sum(
            modal_prices
        ) / len(
            modal_prices
        )


    lowest = min(
            modal_prices
        )


    highest = max(
            modal_prices
        )


    return {

        "crop":
            crop_name,

        "available":
            True,

        "records":
            len(
                records
            ),

        "average_modal_price":
            round(
                average_price,
                2
            ),

        "lowest_modal_price":
            lowest,

        "highest_modal_price":
            highest,

        "price_spread":
            round(
                highest -
                lowest,
                2
            ),

        "message":
            (
                f"Current mandi records show "
                f"an average modal price of "
                f"₹{average_price:.2f}."
            )

    }


# ============================================================
# HEALTH CHECK
# ============================================================

def mandi_health_check() -> Dict[str, Any]:

    if not DATA_GOV_RESOURCE_URL:

        return {

            "status":
                "not_configured",

            "message":
                "DATA_GOV_RESOURCE_URL is not configured."

        }


    try:

        records = fetch_mandi_records(
                limit=1
            )


        if records:

            return {

                "status":
                    "ok",

                "message":
                    "Mandi data service is reachable."

            }


        return {

            "status":
                "empty",

            "message":
                "Mandi service responded but returned no records."

        }


    except Exception as exc:

        return {

            "status":
                "error",

            "message":
                str(
                    exc
                )

        }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [

    "get_crop_prices",

    "get_crop_price_records",

    "search_crop_prices",

    "get_state_prices",

    "get_market_prices",

    "get_price_range",

    "get_price_intelligence",

    "fetch_mandi_records",

    "mandi_health_check"

]


# ============================================================
# END
# ============================================================

