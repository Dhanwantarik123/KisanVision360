import requests
from datetime import datetime


def get_market_price(crop=None):
    """
    Get Maharashtra mandi prices.
    If live API is unavailable, fallback data is returned.
    """

    prices = []

    # =====================================================
    # TRY LIVE DATA
    # =====================================================

    try:

        url = "https://api.data.gov.in/resource"

        # API unavailable / key required in many cases
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        if response.status_code == 200:

            data = response.json()

            records = (
                data.get("records", [])
                if isinstance(data, dict)
                else []
            )

            for item in records:

                commodity = str(
                    item.get("commodity")
                    or item.get("Commodity")
                    or ""
                )

                market = str(
                    item.get("market")
                    or item.get("Market")
                    or ""
                )

                state = str(
                    item.get("state")
                    or item.get("State")
                    or "Maharashtra"
                )

                modal_price = (
                    item.get("modal_price")
                    or item.get("Modal_Price")
                    or item.get("modalPrice")
                    or ""
                )

                min_price = (
                    item.get("min_price")
                    or item.get("Min_Price")
                    or ""
                )

                max_price = (
                    item.get("max_price")
                    or item.get("Max_Price")
                    or ""
                )

                arrival_date = (
                    item.get("arrival_date")
                    or item.get("Arrival_Date")
                    or datetime.now().strftime("%Y-%m-%d")
                )

                if crop:

                    if crop.lower() not in commodity.lower():
                        continue

                if commodity and modal_price:

                    prices.append({

                        "commodity": commodity,

                        "market": market,

                        "state": state,

                        "modal_price": modal_price,

                        "min_price": min_price,

                        "max_price": max_price,

                        "arrival_date": arrival_date

                    })

    except Exception as e:

        print("LIVE MARKET API ERROR:", e)


    # =====================================================
    # FALLBACK DATA
    # =====================================================

    if not prices:

        prices = [

            {
                "commodity": "Soybean",
                "market": "Nagpur",
                "state": "Maharashtra",
                "modal_price": "4800",
                "min_price": "4500",
                "max_price": "5100",
                "arrival_date": datetime.now().strftime("%Y-%m-%d")
            },

            {
                "commodity": "Cotton",
                "market": "Nagpur",
                "state": "Maharashtra",
                "modal_price": "7200",
                "min_price": "6800",
                "max_price": "7500",
                "arrival_date": datetime.now().strftime("%Y-%m-%d")
            },

            {
                "commodity": "Wheat",
                "market": "Nagpur",
                "state": "Maharashtra",
                "modal_price": "2600",
                "min_price": "2400",
                "max_price": "2800",
                "arrival_date": datetime.now().strftime("%Y-%m-%d")
            },

            {
                "commodity": "Gram",
                "market": "Nagpur",
                "state": "Maharashtra",
                "modal_price": "6200",
                "min_price": "5900",
                "max_price": "6500",
                "arrival_date": datetime.now().strftime("%Y-%m-%d")
            },

            {
                "commodity": "Tomato",
                "market": "Nagpur",
                "state": "Maharashtra",
                "modal_price": "2200",
                "min_price": "1800",
                "max_price": "2600",
                "arrival_date": datetime.now().strftime("%Y-%m-%d")
            }

        ]


    # =====================================================
    # CROP FILTER
    # =====================================================

    if crop:

        prices = [

            p for p in prices

            if crop.lower()
            in p["commodity"].lower()

        ]


    return prices