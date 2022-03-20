###  IMPORTS  ###
import os
import json

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

import discord
from discord.ext import tasks
client = discord.Client()

from dotenv import load_dotenv
load_dotenv()



###  ENVIRONNEMENT VARIABLES  ###
if not "DISCORD_TOKEN" in os.environ:
    exit("ENV VAR DISCORD_TOKEN not defined")
if not "DISCORD_GUILD" in os.environ:
    exit("ENV VAR DISCORD_GUILD not defined")
if not "CHANNEL_0T" in os.environ:
    exit("ENV VAR CHANNEL_0T not defined")
if not "CHANNEL_1T" in os.environ:
    exit("ENV VAR CHANNEL_1T not defined")
if not "CHANNEL_2T" in os.environ:
    exit("ENV VAR CHANNEL_2T not defined")
if not "CHANNEL_3T" in os.environ:
    exit("ENV VAR CHANNEL_3T not defined")
if not "CHANNEL_4T" in os.environ:
    exit("ENV VAR CHANNEL_4T not defined")
if not "CHANNEL_5T" in os.environ:
    exit("ENV VAR CHANNEL_5T not defined")
if not "CHANNEL_6T" in os.environ:
    exit("ENV VAR CHANNEL_6T not defined")
if not "CHANNEL_7T" in os.environ:
    exit("ENV VAR CHANNEL_7T not defined")
if not "CHANNEL_DEBUG" in os.environ:
    exit("ENV VAR CHANNEL_DEBUG not defined")
if not "OPENSEA_API_KEY" in os.environ:
    exit("ENV VAR OPENSEA_API_KEY not defined")


DISCORD_TOKEN   =     os.environ.get("DISCORD_TOKEN")
DISCORD_GUILD   = int(os.environ.get("DISCORD_GUILD"))
CHANNEL_0T      = int(os.environ.get("CHANNEL_0T"))
CHANNEL_1T      = int(os.environ.get("CHANNEL_1T"))
CHANNEL_2T      = int(os.environ.get("CHANNEL_2T"))
CHANNEL_3T      = int(os.environ.get("CHANNEL_3T"))
CHANNEL_4T      = int(os.environ.get("CHANNEL_4T"))
CHANNEL_5T      = int(os.environ.get("CHANNEL_5T"))
CHANNEL_6T      = int(os.environ.get("CHANNEL_6T"))
CHANNEL_7T      = int(os.environ.get("CHANNEL_7T"))
CHANNEL_DEBUG   = int(os.environ.get("CHANNEL_DEBUG"))
OPENSEA_API_KEY =     os.environ.get("OPENSEA_API_KEY")

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



###  Get Floor by number of attributes  ###
@tasks.loop(hours=6)
async def Floors():


    channels = [client.get_channel(CHANNEL_0T),
                client.get_channel(CHANNEL_1T),
                client.get_channel(CHANNEL_2T),
                client.get_channel(CHANNEL_3T),
                client.get_channel(CHANNEL_4T),
                client.get_channel(CHANNEL_5T),
                client.get_channel(CHANNEL_6T),
                client.get_channel(CHANNEL_7T)]

    channel_debug = client.get_channel(CHANNEL_DEBUG)

    floorT = {
        0:1000,
        1:1000,
        2:1000,
        3:1000,
        4:1000,
        5:1000,
        6:1000,
        7:1000
    }

    for tokenId in range(1,10001):

        asset_url = "{}/asset/{}/{}".format(OS_API_URL, LUCHA_ADDR, tokenId)
        asset_body = handle_request(asset_url)
        
        if asset_body["code"] != 0:
            await channel_debug.send(asset_body["msg"])
            return

        attr = asset_body["msg"]["traits"][-1]["value"]


        listing_url = "{}/asset/{}/{}/listings".format(OS_API_URL, LUCHA_ADDR, tokenId)
        listing_body = handle_request(listing_url)

        if listing_body["code"] != 0:
            await channel_debug.send(asset_body["msg"])
            return

        listings = listing_body["msg"]["listings"]


        # if the lucha is listed on sale
        if listings:

            listingPrices = []
            for price in listings:
                listingPrices += [price["current_price"]]

            listingPrice = float(min(listingPrices)) / (10**18)
            if listingPrice < floorT[attr]:
                floorT[attr] = listingPrice


    for i in range(len(floorT)):

        floor = floorT[i]
        name = '『{}T』{}⬨'.format(i,round(floor,3)).replace('.','༝')
        await channels[i].edit(name=name)



###  Start  ###
@client.event
async def on_ready():

    if not Floors.is_running():
        Floors.start()



client.run(DISCORD_TOKEN)