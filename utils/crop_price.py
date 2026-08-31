import requests
from datetime import datetime


def get_crop_prices():

    url = "https://api.data.gov.in/resource"

    try:

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        data = response.json()

        crop_prices = {}

        for item in data.get("records", []):

            crop = (
                item.get("commodity")
                or item.get("Commodity")
            )

            price = (
                item.get("modal_price")
                or item.get("Modal_Price")
            )

            if crop and price:

                try:
                    crop_prices[crop] = float(price)
                except:
                    continue

        return crop_prices

    except Exception as e:

        print("Live crop price error:", e)

        return {}