###  IMPORTS  ###
import os
import json

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

import discord
from discord.ext import tasks
client = discord.Client()

from web3 import Web3

from dotenv import load_dotenv
load_dotenv()



###  ENVIRONNEMENT VARIABLES  ###
if not "DISCORD_TOKEN" in os.environ:
    exit("ENV VAR DISCORD_TOKEN not defined")
if not "DISCORD_GUILD" in os.environ:
    exit("ENV VAR DISCORD_GUILD not defined")
if not "CHANNEL_GET_DATA" in os.environ:
    exit("ENV VAR CHANNEL_GET_DATA not defined")
if not "CHANNEL_DEBUG" in os.environ:
    exit("ENV VAR CHANNEL_DEBUG not defined")
if not "OPENSEA_API_KEY" in os.environ:
    exit("ENV VAR OPENSEA_API_KEY not defined")


DISCORD_TOKEN         =     os.environ.get("DISCORD_TOKEN")
DISCORD_GUILD         = int(os.environ.get("DISCORD_GUILD"))
CHANNEL_GET_DATA      = int(os.environ.get("CHANNEL_GET_DATA"))
CHANNEL_DEBUG         = int(os.environ.get("CHANNEL_DEBUG"))
OPENSEA_API_KEY       =     os.environ.get("OPENSEA_API_KEY")

# OpenSea API doc: https://docs.opensea.io/reference/api-overview
OS_API_URL = "https://api.opensea.io/api/v1"
LUCHA_ADDR = "0x8b4616926705fb61e9c4eeac07cd946a5d4b0760"



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



for tokenId in range(1,10000):

    url = "{}/asset/{}/{}".format(OS_API_URL, LUCHA_ADDR, tokenId)
    events_body = handle_request(url)
    
    if events_body["code"] != 0:
        print("fail")

    name = events_body["msg"]["name"]
    attr = events_body["msg"]["traits"][-1]["value"]

    listing_url = "{}/asset/{}/{}/listings".format(OS_API_URL, LUCHA_ADDR, tokenId)
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