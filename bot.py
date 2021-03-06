###  IMPORTS  ###
import os
import json
import datetime

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
if not "CHANNEL_GET_DATA" in os.environ:
    exit("ENV VAR CHANNEL_GET_DATA not defined")
if not "CHANNEL_FLOOR" in os.environ:
    exit("ENV VAR CHANNEL_FLOOR not defined")
if not "CHANNEL_ETH_PRICE" in os.environ:
    exit("ENV VAR CHANNEL_ETH_PRICE not defined")
if not "CHANNEL_LUCHA_PRICE" in os.environ:
    exit("ENV VAR CHANNEL_LUCHA_PRICE not defined")
if not "CHANNEL_SALES" in os.environ:
    exit("ENV VAR CHANNEL_SALES not defined")
if not "CHANNEL_LISTINGS" in os.environ:
    exit("ENV VAR CHANNEL_LISTINGS not defined")
if not "CHANNEL_OFFERS" in os.environ:
    exit("ENV VAR CHANNEL_OFFERS not defined")
if not "CHANNEL_TRANSFERS" in os.environ:
    exit("ENV VAR CHANNEL_TRANSFERS not defined")
if not "CHANNEL_DEBUG" in os.environ:
    exit("ENV VAR CHANNEL_DEBUG not defined")
if not "OPENSEA_API_KEY" in os.environ:
    exit("ENV VAR OPENSEA_API_KEY not defined")
if not "ALCHEMY_API_KEY" in os.environ:
    exit("ENV VAR ALCHEMY_API_KEY not defined")

DISCORD_TOKEN       =     os.environ.get("DISCORD_TOKEN")
CHANNEL_GET_DATA    = int(os.environ.get("CHANNEL_GET_DATA"))
CHANNEL_FLOOR       = int(os.environ.get("CHANNEL_FLOOR"))
CHANNEL_ETH_PRICE   = int(os.environ.get("CHANNEL_ETH_PRICE"))
CHANNEL_LUCHA_PRICE = int(os.environ.get("CHANNEL_LUCHA_PRICE"))
CHANNEL_SALES       = int(os.environ.get("CHANNEL_SALES"))
CHANNEL_LISTINGS    = int(os.environ.get("CHANNEL_LISTINGS"))
CHANNEL_OFFERS      = int(os.environ.get("CHANNEL_OFFERS"))
CHANNEL_TRANSFERS   = int(os.environ.get("CHANNEL_TRANSFERS"))
CHANNEL_DEBUG       = int(os.environ.get("CHANNEL_DEBUG"))

OPENSEA_API_KEY     =     os.environ.get("OPENSEA_API_KEY")
ALCHEMY_API_KEY     =     os.environ.get("ALCHEMY_API_KEY")



###  RPC AND CONTRACT ABI  ###
session = requests.Session()
retries = Retry(total = 5,
                backoff_factor = 0.5,
                status_forcelist = [413, 429, 495, 500, 502, 503, 504]
)
session.mount('https://', HTTPAdapter(max_retries=retries))

ALCHEMY_HTTP = "https://polygon-mainnet.g.alchemy.com/v2"
RPC_URL = "{}/{}".format(ALCHEMY_HTTP, ALCHEMY_API_KEY)
web3 = Web3(Web3.HTTPProvider(RPC_URL, session = session))

# Luchadores Polygon contract
CONTRACT_ADDR_1 = "0xE8B73c064BD3B8c5DB438118543ACd6AAb18F108"
# Luchadores Ethereum contract
CONTRACT_ADDR_2 = "0x8b4616926705fb61e9c4eeac07cd946a5d4b0760"

with open("./luchaABI.txt", "r") as file:
    luchaABI = json.load(file)

lucha_claim = web3.eth.contract(address=CONTRACT_ADDR_1, abi=luchaABI)



###  OTHERS  ###
# OpenSea API doc: https://docs.opensea.io/reference/api-overview
OS_API_URL = "https://api.opensea.io/api/v1"
OS_URL     = "https://opensea.io"

# Fetch prices with coingecko: https://www.coingecko.com/en/api/documentation
CG_API_URL = url = "https://api.coingecko.com/api/v3/simple/price"

# $LUCHA yield, based on attribute rarity: https://luchadores.io/yield
lyield = {
    3:1,
    2:1,
    4:2,
    1:3,
    5:4,
    6:6,
    0:6,
    7:10
}
COLLECTION_SLUG = "luchadores-io"
LUCHADORES_IMG_URL = "https://luchadores-io.s3.us-east-2.amazonaws.com/img"



###  Send get requests to API  ###
def handle_request(url, params = {}):

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



def create_embed(type,
                 event_date,
                 data,
                 price  = None,
                 seller = None,
                 buyer  = None):

    tokenId = data["token_id"]
    traits = data['traits'][-1]['value']

    done = False
    while not done:
        try:
            hasBeenClaimed = lucha_claim.functions.lastClaim(int(tokenId)).call()
            claimed = True if hasBeenClaimed else False

            pendingYield = lucha_claim.functions.pendingYield(int(tokenId)).call() / (10**18)
            done = True

        except:
            pass

    img_url  = "{}/{}.png".format(LUCHADORES_IMG_URL, tokenId)
    url = "{}/assets/{}/{}".format(OS_URL, CONTRACT_ADDR_2, tokenId)


    date = datetime.datetime.fromisoformat(event_date)
    date = date.strftime("%H:%M:%S") # only H:M:S
    title = "Luchadores {} {} ({})".format(tokenId, type, date)

    embed = discord.Embed(title = title,
                          url   = url,
                          color = discord.Color.from_rgb(255,0,0))
    embed.set_thumbnail(url = img_url)
    embed.add_field(name    = "Attributes",
                    value   = traits,
                    inline  = True)
    embed.add_field(name    = "Daily yield",
                    value   = lyield[traits],
                    inline  = True)
    embed.add_field(name    = "Pending $lucha",
                    value   = int(pendingYield),
                    inline  = True)
    embed.add_field(name    = "Claimed Once",
                    value   = claimed,
                    inline  = True)


    if( "listed"  in type
     or "sold"    in type
     or type == "checked"):
        if price:
            
            channel_debug = client.get_channel(CHANNEL_DEBUG)
            
            params = {'ids':'ethereum,lucha', 'vs_currencies':'usd'}
            price_body = handle_request(CG_API_URL, params)
            
            if price_body["code"] != 0:
                channel_debug.send(price_body["msg"])
                
            lucha_price    = price_body["msg"]["lucha"]["usd"]
            ethereum_price = price_body["msg"]["ethereum"]["usd"]

            fiat_price = price * ethereum_price
            
            # $ price with $lucha token deducted
            realPrice = fiat_price - pendingYield * lucha_price
            roi = int(realPrice / (lyield[traits] * lucha_price))

            embed.add_field(name   = "ETH Price",
                            value  = price,
                            inline = True)
            embed.add_field(name   = "Seller",
                            value  = seller,
                            inline = True)
            if buyer:
                embed.add_field(name   = "Buyer",
                                value  = buyer,
                                inline = True)
            embed.add_field(name   = "Real $ price",
                            value  = int(realPrice),
                            inline = True)
            embed.add_field(name   = "ROI in days",
                            value  = roi,
                            inline = True)
        
        else:
            embed.add_field(name   = "Owner",
                            value  = seller,
                            inline = True)

    elif "wanted" in type:
        embed.add_field(name   = "ETH Proposed Price",
                        value  = price,
                        inline = True)
        embed.add_field(name   = "Owner",
                        value  = seller,
                        inline = True)
        embed.add_field(name   = "Proposer",
                        value  = buyer,
                        inline = True)

    elif type == "transfered":
        embed.add_field(name   = "From",
                        value  = seller,
                        inline = True)
        embed.add_field(name   = "To",
                        value  = buyer,
                        inline = True)

    return embed



###  Refresh floor price  ###
@tasks.loop(minutes=15)
async def getFloor():

    channel_floor = client.get_channel(CHANNEL_FLOOR)
    channel_debug = client.get_channel(CHANNEL_DEBUG)

    stats_url = "{}/collection/{}/stats".format(OS_API_URL, COLLECTION_SLUG)
    stats_body = handle_request(stats_url)

    if stats_body["code"] != 0:
        await channel_debug.send(stats_body["msg"])
        return

    floorPrice = stats_body["msg"]['stats']['floor_price']
    
    name = '???floor???{}???'.format(round(floorPrice,3)).replace('.','???')
    await channel_floor.edit(name=name)



###  Refresh eth and lucha price  ###
@tasks.loop(minutes=15)
async def getPrice():

    channel_eth_price = client.get_channel(CHANNEL_ETH_PRICE)
    channel_lucha_price = client.get_channel(CHANNEL_LUCHA_PRICE)
    channel_debug = client.get_channel(CHANNEL_DEBUG)

    params = {'ids':'ethereum,lucha', 'vs_currencies':'usd'}
    price_body = handle_request(CG_API_URL, params)

    if price_body["code"] != 0:
        await channel_debug.send(price_body["msg"])
        return

    lucha_price    = price_body["msg"]["lucha"]["usd"]
    ethereum_price = int(price_body["msg"]["ethereum"]["usd"])

    eth_name = '???ETH???{}????'.format(ethereum_price)
    lucha_name = '???LUCHA???{}????'.format(round(lucha_price,3)).replace('.','???')

    await channel_eth_price.edit(name=eth_name)
    await channel_lucha_price.edit(name=lucha_name)



###  INIT EVENT ID  ###    
params = {'asset_contract_address': CONTRACT_ADDR_2}
events_url = "{}/events".format(OS_API_URL)
events_body = handle_request(events_url, params)
last_event_id_treated = int(events_body["msg"]["asset_events"][0]["id"])
#last_event_id_treated = 5324346000

###  Get events from OS: sales, listings, offers  ###
@tasks.loop(minutes=1)
async def getLastEvents():

    global last_event_id_treated

    channel_debug = client.get_channel(CHANNEL_DEBUG)
    
    params = {'asset_contract_address': CONTRACT_ADDR_2}
    events_url = "{}/events".format(OS_API_URL)
    events_body = handle_request(events_url, params)

    if events_body["code"] != 0:
        await channel_debug.send(events_body["msg"])
        return
    
    current_event_id = int(events_body["msg"]["asset_events"][0]["id"])
    listings  = []
    sales     = []
    offers    = []
    transfers = []
    
    done = False
    while not done:

        for event in events_body["msg"]["asset_events"]:

            # done when eventId = the last eventId treated
            eventId = int(event["id"])
            if eventId == last_event_id_treated:
                done = True
                break

            # sale
            if event["event_type"] == "successful":

                try:
                    seller = event["seller"]["user"]["username"]
                except:
                    seller = event["seller"]["address"][:8]
                if seller == None: seller = event["seller"]["address"][:8]
                
                try:
                    buyer = event["winner_account"]["user"]["username"]
                except:
                    buyer = event["winner_account"]["address"][:8]
                if buyer == None: buyer = event["winner_account"]["address"][:8]

                price = int(event["total_price"]) / (10**18)

                # bundle
                if event["asset_bundle"]:

                    for asset in event["asset_bundle"]["assets"]:
                        
                        tokenId = asset["token_id"]
                    
                        asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
                        asset_body = handle_request(asset_url)

                        if asset_body["code"] != 0:
                            await channel_debug.send(asset_body["msg"])
                            return

                        embed = create_embed("sold (bundle)",
                                            event["created_date"],
                                            asset_body["msg"],
                                            price,
                                            seller,
                                            buyer)

                        sales += [embed]

                # single asset
                elif event["asset"]:

                    tokenId = event["asset"]["token_id"]

                    asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
                    asset_body = handle_request(asset_url)

                    if asset_body["code"] != 0:
                        await channel_debug.send(asset_body["msg"])
                        return

                    embed = create_embed("sold",
                                        event["created_date"],
                                        asset_body["msg"],
                                        price,
                                        seller,
                                        buyer)

                    sales += [embed]


            # listing
            elif event["event_type"] == "created":

                try:
                    seller = event["seller"]["user"]["username"]
                except:
                    seller = event["seller"]["address"][:8]
                if seller == None: seller = event["seller"]["address"][:8]
                
                price = int(event["ending_price"]) / (10**18)

                # bundle
                if event["asset_bundle"]:

                    for asset in event["asset_bundle"]["assets"]:
                        tokenId = asset["token_id"]
                    
                        asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
                        asset_body = handle_request(asset_url)

                        if asset_body["code"] != 0:
                            await channel_debug.send(asset_body["msg"])
                            return

                        embed = create_embed("listed (bundle)",
                                            event["created_date"],
                                            asset_body["msg"],
                                            price,
                                            seller)

                        listings += [embed]

                # single asset
                elif event["asset"]:

                    tokenId = event["asset"]["token_id"]
                    
                    asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
                    asset_body = handle_request(asset_url)

                    if asset_body["code"] != 0:
                        await channel_debug.send(asset_body["msg"])
                        return

                    embed = create_embed("listed",
                                        event["created_date"],
                                        asset_body["msg"],
                                        price,
                                        seller)

                    listings += [embed]


            # offer
            elif event["event_type"] == "offer_entered":
                
                try:
                    buyer = event["from_account"]["user"]["username"]
                except:
                    buyer = event["from_account"]["address"][:8]
                if buyer == None: buyer = event["from_account"]["address"][:8]

                # bundle
                if event["asset_bundle"]:

                    try:
                        seller = event["asset_bundle"]["maker"]["user"]["username"]
                    except:
                        seller = event["asset_bundle"]["maker"]["address"][:8]
                    if seller == None: seller = event["asset_bundle"]["maker"]["address"][:8]

                    price = int(event["bid_amount"]) / (10**18)

                    for asset in event["asset_bundle"]["assets"]:
                        tokenId = asset["token_id"]
                    
                        asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
                        asset_body = handle_request(asset_url)

                        if asset_body["code"] != 0:
                            await channel_debug.send(asset_body["msg"])
                            return

                        embed = create_embed("wanted (bundle)",
                                            event["created_date"],
                                            asset_body["msg"],
                                            price,
                                            seller,
                                            buyer)

                        offers += [embed]


                # single asset
                elif event["asset"]:
                    try:
                        seller = event["asset"]["owner"]["user"]["username"]
                    except:
                        seller = event["asset"]["owner"]["address"][:8]
                    if seller == None: seller = event["asset"]["owner"]["address"][:8]

                    price = int(event["bid_amount"]) / (10**18)

                    tokenId = event["asset"]["token_id"]
                    
                    asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
                    asset_body = handle_request(asset_url)

                    if asset_body["code"] != 0:
                        await channel_debug.send(asset_body["msg"])
                        return

                    embed = create_embed("wanted",
                                        event["created_date"],
                                        asset_body["msg"],
                                        price,
                                        seller,
                                        buyer)

                    offers += [embed]


            # transfer
            if event["event_type"] == "transfer":

                try:
                    seller = event["from_account"]["user"]["username"]
                except:
                    seller = event["from_account"]["address"][:8]
                if seller == None: seller = event["from_account"]["address"][:8]
                
                try:
                    buyer = event["to_account"]["user"]["username"]
                except:
                    buyer = event["to_account"]["address"][:8]
                if buyer == None: buyer = event["to_account"]["address"][:8]

                tokenId = event["asset"]["token_id"]

                asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
                asset_body = handle_request(asset_url)

                if asset_body["code"] != 0:
                    await channel_debug.send(asset_body["msg"])
                    return

                embed = create_embed("transfered",
                                    event["created_date"],
                                    asset_body["msg"],
                                    seller = seller,
                                    buyer = buyer)

                transfers += [embed]

        # the OS API sends back the last 20 events:
        # if more than 20 events happened in 1min,
        # do an another API call on previous events
        # and loop until all events are treated
        if not done:
            params = {'asset_contract_address': CONTRACT_ADDR_2,
                      'cursor': events_body["msg"]["next"]}
        
            events_url = "{}/events".format(OS_API_URL)
            events_body = handle_request(events_url, params)

            if events_body["code"] != 0:
                await channel_debug.send(events_body["msg"])
                return

    last_event_id_treated = current_event_id

    channel_listings  = client.get_channel(CHANNEL_LISTINGS)
    channel_sales     = client.get_channel(CHANNEL_SALES)
    channel_offers    = client.get_channel(CHANNEL_OFFERS)
    channel_transfers = client.get_channel(CHANNEL_TRANSFERS)

    for msg in reversed(sales):
        await channel_sales.send(embed=msg)
    for msg in reversed(listings):
        await channel_listings.send(embed=msg)
    for msg in reversed(offers):
        await channel_offers.send(embed=msg)
    for msg in reversed(transfers):
        await channel_transfers.send(embed=msg)



###  Deal with msgs sent to Discord  ###
@client.event
async def on_message(message):

    channel_get_data = client.get_channel(CHANNEL_GET_DATA)
    channel_debug    = client.get_channel(CHANNEL_DEBUG)

    # If the bot send a msg, do nothing
    if message.author == client.user:
        return

    # fetch opensea data on a specific lucha
    elif message.channel == channel_get_data:

        try:
            tokenId = int(message.content)
        except ValueError:
            await channel_get_data.send("Type an integer")
            return
        if(tokenId <= 0 or tokenId > 10000):
            await channel_get_data.send("Type an integer between 1 and 10 000")
            return
        
        listing_url = "{}/asset/{}/{}/listings".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
        listing_body = handle_request(listing_url)

        if listing_body["code"] != 0:
            await channel_debug.send(listing_body["msg"])
            return

        asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
        asset_body = handle_request(asset_url)

        if asset_body["code"] != 0:
            await channel_debug.send(asset_body["msg"])
            return

        try:
            seller = asset_body["msg"]["owner"]["user"]["username"]
        except:
            seller = asset_body["msg"]["owner"]["address"][:8]
        if seller == None: seller = asset_body["msg"]["owner"]["address"][:8]

        listingPrice = 0
        listings = listing_body["msg"]["listings"]

        # if the lucha is listed on sale
        if listings:

            listingPrices = []
            for price in listings:
                listingPrices += [price["current_price"]]

            listingPrice = float(min(listingPrices)) / (10**18)

        embed = create_embed("checked",
                            str(datetime.datetime.now()),
                            asset_body["msg"],
                            listingPrice,
                            seller)

        await channel_get_data.send(embed=embed)



###  Start  ###
@client.event
async def on_ready():

    if not getFloor.is_running():
        getFloor.start()

    if not getPrice.is_running():
        getPrice.start()
    
    if not getLastEvents.is_running():
        getLastEvents.start()



client.run(DISCORD_TOKEN)