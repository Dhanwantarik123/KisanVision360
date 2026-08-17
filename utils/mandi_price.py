import requests
from bs4 import BeautifulSoup


def get_market_price(crop=None):

    url = "https://agmarknet.gov.in/daily-price-and-arrival-report"

    try:

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        prices = []

        # Find tables on the page
        tables = soup.find_all("table")

        for table in tables:

            rows = table.find_all("tr")

            for row in rows:

                cells = row.find_all(
                    ["td", "th"]
                )

                values = [
                    cell.get_text(
                        " ",
                        strip=True
                    )
                    for cell in cells
                ]

                if not values:
                    continue

                # Ignore header
                if "Commodity" in values:
                    continue

                if len(values) >= 5:

                    commodity = values[0]

                    if crop:

                        if crop.lower() not in commodity.lower():
                            continue

                    prices.append({

                        "commodity":
                        commodity,

                        "market":
                        values[1],

                        "state":
                        values[2],

                        "modal_price":
                        values[3],

                        "arrival_date":
                        values[4]

                    })


        return prices


    except Exception as e:

        print(
            "AGMARKNET Error:",
            e
        )

        return []