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

from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

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
if not "CHANNEL_NEVER_CLAIMED" in os.environ:
    exit("ENV VAR CHANNEL_NEVER_CLAIMED not defined")
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
if not "CHANNEL_KEEPALIVE" in os.environ:
    exit("ENV VAR CHANNEL_KEEPALIVE not defined")
if not "OPENSEA_API_KEY" in os.environ:
    exit("ENV VAR OPENSEA_API_KEY not defined")
if not "ALCHEMY_API_KEY" in os.environ:
    exit("ENV VAR ALCHEMY_API_KEY not defined")

DISCORD_TOKEN         =     os.environ.get("DISCORD_TOKEN")
DISCORD_GUILD         = int(os.environ.get("DISCORD_GUILD"))
CHANNEL_GET_DATA      = int(os.environ.get("CHANNEL_GET_DATA"))
CHANNEL_NEVER_CLAIMED = int(os.environ.get("CHANNEL_NEVER_CLAIMED"))
CHANNEL_FLOOR         = int(os.environ.get("CHANNEL_FLOOR"))
CHANNEL_ETH_PRICE     = int(os.environ.get("CHANNEL_ETH_PRICE"))
CHANNEL_LUCHA_PRICE   = int(os.environ.get("CHANNEL_LUCHA_PRICE"))
CHANNEL_SALES         = int(os.environ.get("CHANNEL_SALES"))
CHANNEL_LISTINGS      = int(os.environ.get("CHANNEL_LISTINGS"))
CHANNEL_OFFERS        = int(os.environ.get("CHANNEL_OFFERS"))
CHANNEL_KEEPALIVE     = int(os.environ.get("CHANNEL_KEEPALIVE"))
OPENSEA_API_KEY       =     os.environ.get("OPENSEA_API_KEY")
ALCHEMY_API_KEY       =     os.environ.get("ALCHEMY_API_KEY")



###  RPC AND CONTRACT ABI  ###
ALCHEMY_WS = "wss://polygon-mainnet.g.alchemy.com/v2"

RPC_URL = "{}/{}".format(ALCHEMY_WS, ALCHEMY_API_KEY)
web3 = Web3(Web3.WebsocketProvider(RPC_URL, websocket_timeout=20))

with open("./luchaABI.txt", "r") as file:
    luchaABI = json.load(file)

# Luchadores Polygon contract
CONTRACT_ADDR_1 = "0xE8B73c064BD3B8c5DB438118543ACd6AAb18F108"
# Luchadores Ethereum contract
CONTRACT_ADDR_2 = "0x8b4616926705fb61e9c4eeac07cd946a5d4b0760"
lucha_claim = web3.eth.contract(address=CONTRACT_ADDR_1, abi=luchaABI)



###  OTHERS  ###
# OpenSea API doc: https://docs.opensea.io/reference/api-overview
OS_API_URL = "https://api.opensea.io/api/v1"
OS_URL     = "https://opensea.io"

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



###  Send get requests to opensea API  ###
def handle_request(url, params = {}):

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.3)
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



def create_embed(type,
                 data,
                 price  = None,
                 seller = None,
                 buyer  = None):

    tokenId = data["token_id"]
    traits = data['traits'][-1]['value']

    hasBeenClaimed = lucha_claim.functions.lastClaim(int(tokenId)).call()
    claimed = True if hasBeenClaimed else False

    pendingYield   = lucha_claim.functions.pendingYield(int(tokenId)).call() / (10**18)

    img_url  = "{}/{}.png".format(LUCHADORES_IMG_URL, tokenId)
    url = "{}/assets/{}/{}".format(OS_URL, CONTRACT_ADDR_2, tokenId)


    embed = discord.Embed(title = "Luchadores {} {}".format(tokenId, type),
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


    if( type in "listed"
     or type in "sold"
     or type in "checked"):
        if price:
            lucha    = cg.get_price(ids='lucha',    vs_currencies='usd')
            ethereum = cg.get_price(ids='ethereum', vs_currencies='usd')

            lucha_price    = lucha['lucha']['usd']
            ethereum_price = ethereum['ethereum']['usd']

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

    if type in "wanted":
        embed.add_field(name   = "ETH Proposed Price",
                        value  = price,
                        inline = True)
        embed.add_field(name   = "Owner",
                        value  = seller,
                        inline = True)
        embed.add_field(name   = "Proposer",
                        value  = buyer,
                        inline = True)

    return embed



###  Refresh lucha, eth and floor price  ###
@tasks.loop(minutes=10)
async def getFloor():

    channel = client.get_channel(CHANNEL_FLOOR)

    
    stats_url = "{}/collection/{}/stats".format(OS_API_URL, COLLECTION_SLUG)
    stats_body = handle_request(stats_url)
    if stats_body["code"] != 0:
        await channel.send(stats_body["msg"])
        return

    floorPrice = stats_body["msg"]['stats']['floor_price']
    
    name = '『floor』{}♟'.format(round(floorPrice,3)).replace('.','༝')
    await channel.edit(name=name)



@tasks.loop(minutes=10)
async def getEth():

    channel = client.get_channel(CHANNEL_ETH_PRICE)

    ethereum = cg.get_price(ids='ethereum', vs_currencies='usd')
    ethereum_price = int(ethereum['ethereum']['usd'])

    name = '『ETH』{}💲'.format(ethereum_price)
    await channel.edit(name=name)



@tasks.loop(minutes=10)
async def getLucha():

    channel = client.get_channel(CHANNEL_LUCHA_PRICE)

    lucha = cg.get_price(ids='lucha', vs_currencies='usd')
    lucha_price = lucha['lucha']['usd']

    name = '『LUCHA』{}💲'.format(round(lucha_price,3)).replace('.','༝')
    await channel.edit(name=name)



@tasks.loop(seconds=30)
async def keepAlive():

    channel = client.get_channel(CHANNEL_KEEPALIVE)
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d %H:%M:%S")

    await channel.send(str(date))
    


last_event_id_treated = 4201212623
@tasks.loop(minutes=2)
async def getLastEvents():

    global last_event_id_treated

    channel_listings = client.get_channel(CHANNEL_LISTINGS)
    channel_sales    = client.get_channel(CHANNEL_SALES)
    channel_offers   = client.get_channel(CHANNEL_OFFERS)
    
    params = {'asset_contract_address': CONTRACT_ADDR_2}
    
    events_url = "{}/events".format(OS_API_URL)
    events_body = handle_request(events_url, params)

    if events_body["code"] != 0:
        await channel_sales.send(events_body["msg"])
        return
    
    current_event_id = int(events_body["msg"]["asset_events"][0]["id"])
    listings = []
    sales    = []
    offers   = []
    
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
                            await channel_sales.send(asset_body["msg"])
                            return

                        embed = create_embed("sold (bundle)",
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
                        await channel_sales.send(asset_body["msg"])
                        return

                    embed = create_embed("sold",
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
                            await channel_sales.send(asset_body["msg"])
                            return

                        embed = create_embed("listed (bundle)",
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
                        await channel_sales.send(asset_body["msg"])
                        return

                    embed = create_embed("listed",
                                        asset_body["msg"],
                                        price,
                                        seller)

                    listings += [embed]


            # offer
            elif event["event_type"] == "offer_entered":

                try:
                    seller = event["asset"]["owner"]["user"]["username"]
                except:
                    seller = event["asset"]["owner"]["address"][:8]
                if seller == None: seller = event["asset"]["owner"]["address"][:8]

                try:
                    buyer = event["from_account"]["user"]["username"]
                except:
                    buyer = event["from_account"]["address"][:8]
                if buyer == None: buyer = event["from_account"]["address"][:8]

                price = int(event["bid_amount"]) / (10**18)


                tokenId = event["asset"]["token_id"]
                
                asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
                asset_body = handle_request(asset_url)

                if asset_body["code"] != 0:
                    await channel_offers.send(asset_body["msg"])
                    return

                embed = create_embed("wanted",
                                    asset_body["msg"],
                                    price,
                                    seller,
                                    buyer)

                offers += [embed]

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
                await channel_sales.send(events_body["msg"])
                return

    last_event_id_treated = current_event_id
    for msg in reversed(sales):
        await channel_sales.send(embed=msg)
    for msg in reversed(listings):
        await channel_listings.send(embed=msg)
    for msg in reversed(offers):
        await channel_offers.send(embed=msg)



@client.event
async def on_ready():

    if not getFloor.is_running():
        getFloor.start()

    if not getEth.is_running():
        getEth.start()
    
    if not getLucha.is_running():
        getLucha.start()
    
    if not getLastEvents.is_running():
        getLastEvents.start()

    if not keepAlive.is_running():
        keepAlive.start()



@client.event
async def on_message(message):

    channel_get_data      = client.get_channel(CHANNEL_GET_DATA)
    channel_never_claimed = client.get_channel(CHANNEL_NEVER_CLAIMED)

    # If the bot send a msg, do nothing
    if message.author == client.user:
        return
    

    # Check how many lucha have been claimed out of 10k
    if message.channel == channel_never_claimed:

        msg = "Fetching data, plz wait, it can take up to 1h..."
        await channel_never_claimed.send(msg)
        
        not_claimed = []
        counter = 0

        for i in range(1,10000):

            hasBeenClaimed = lucha_claim.functions.lastClaim(i).call()
            if not hasBeenClaimed:
                not_claimed.append(i)
                counter += 1

            if counter == 10:
                counter = 0
                await channel_never_claimed.send(not_claimed[-10:])
        await channel_never_claimed.send(not_claimed[-counter:])    

        msg = "Total not claimed on 10k lucha: "
        msg += str(len(not_claimed))
        await channel_never_claimed.send(msg)


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
            await channel_get_data.send(listing_body["msg"])
            return

        asset_url = "{}/asset/{}/{}".format(OS_API_URL,CONTRACT_ADDR_2, tokenId)
        asset_body = handle_request(asset_url)

        if asset_body["code"] != 0:
            await channel_get_data.send(asset_body["msg"])
            return


        listingPrice = 0
        seller = 0

        listings = listing_body["msg"]["listings"]

        # if the lucha is listed on sale
        if listings:

            listingPrices = []
            for price in listings:
                listingPrices += [price["current_price"]]

            listingPrice = float(min(listingPrices)) / (10**18)
            try:
                seller = asset_body["msg"]["owner"]["user"]["username"]
            except:
                seller = asset_body["msg"]["owner"]["address"][:8]
            if seller == None: seller = asset_body["msg"]["owner"]["address"][:8]

        embed = create_embed("checked",
                            asset_body["msg"],
                            listingPrice,
                            seller)

        await channel_get_data.send(embed=embed)
        
        

client.run(DISCORD_TOKEN)