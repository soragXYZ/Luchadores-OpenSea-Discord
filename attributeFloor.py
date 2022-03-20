import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import json
import datetime

OS_API_URL = "https://api.opensea.io/api/v1"
CONTRACT_ADDR_2 = "0x8b4616926705fb61e9c4eeac07cd946a5d4b0760"
OPENSEA_API_KEY = "e866bed80d904e27bc0d56f68367ba0b"

###  Send get requests to opensea API  ###
def handle_request(url, params = {}):

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429,495])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.request(
            'GET',
            url,
            headers = {"Accept": "application/json",
                       "X-API-KEY": OPENSEA_API_KEY},
            params = params
        )
        response.raise_for_status()

    except requests.exceptions.HTTPError as errh:
        msg = "Http error: " + str(errh)
        return {"code": 1, "msg": msg}

    except requests.exceptions.ConnectionError as errc:
        msg = "Error connecting: " + str(errc)
        return {"code": 1, "msg": msg}

    except requests.exceptions.Timeout as errt:
        msg = "Timeout error: " + str(errt)
        return {"code": 1, "msg": msg}

    except requests.exceptions.RequestException as err:
        msg = "Something went wrong: " + str(err)
        return {"code": 1, "msg": msg}


    try:
        body = json.loads(response.content)
        return {"code": 0, "msg": body}

    except ValueError:
        msg = "Invalid json sent when querying" + url
        return {"code": 1, "msg": msg}

floorT = {
    0:100,
    1:100,
    2:100,
    3:100,
    4:100,
    5:100,
    6:100,
    7:100
}


start = datetime.datetime.now()
for tokenId in range(1,10000):

    url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
    events_body = handle_request(url)
    
    if events_body["code"] != 0:
        print("fail")

    name = events_body["msg"]["name"]
    attr = events_body["msg"]["traits"][-1]["value"]

    listing_url = "{}/asset/{}/{}/listings".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
    listing_body = handle_request(listing_url)

    if listing_body["code"] != 0:
        print("fail")

    listings = listing_body["msg"]["listings"]

    # if the lucha is listed on sale
    if listings:

        listingPrices = []
        for price in listings:
            listingPrices += [price["current_price"]]

        listingPrice = float(min(listingPrices)) / (10**18)
        if listingPrice < floorT[attr]:
            floorT[attr] = listingPrice


print(floorT)

end = datetime.datetime.now()

delta = end - start

print(delta)