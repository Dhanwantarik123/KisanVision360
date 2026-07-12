import requests


def get_market_price(crop):


    API_KEY = "YOUR_AGMARKNET_API_KEY"


    url = (
        "https://api.data.gov.in/resource/"
        "9ef84268-d588-465a-a308-a864a43d0070"
    )


    params = {

        "api-key": API_KEY,

        "format":"json",

        "limit":10,

        "filters[commodity]":crop

    }


    response=requests.get(
        url,
        params=params
    )


    if response.status_code==200:


        data=response.json()


        return data.get(
            "records",
            []
        )


    return []
