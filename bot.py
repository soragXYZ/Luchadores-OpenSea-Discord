###  IMPORTS  ###
import os
import requests
import json

import discord
from discord.ext import tasks

from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

from web3 import Web3

from dotenv import load_dotenv
load_dotenv()



###  ENVIRONNEMENT VARIABLES  ###
DISCORD_TOKEN     =     os.environ.get("DISCORD_TOKEN")
DISCORD_GUILD     = int(os.environ.get("DISCORD_GUILD"))
DISCORD_CHANNEL_1 = int(os.environ.get("DISCORD_CHANNEL_1"))
DISCORD_CHANNEL_2 = int(os.environ.get("DISCORD_CHANNEL_2"))
OPENSEA_API_KEY   =     os.environ.get("OPENSEA_API_KEY")
ALCHEMY_API_KEY   =     os.environ.get("ALCHEMY_API_KEY")

if not "DISCORD_TOKEN" in os.environ:
    exit("ENV VAR DISCORD_TOKEN not defined")
if not "DISCORD_GUILD" in os.environ:
    exit("ENV VAR DISCORD_GUILD not defined")
if not "DISCORD_CHANNEL_1" in os.environ:
    exit("ENV VAR DISCORD_CHANNEL_1 not defined")
if not "DISCORD_CHANNEL_2" in os.environ:
    exit("ENV VAR DISCORD_CHANNEL_2 not defined")
if not "OPENSEA_API_KEY" in os.environ:
    exit("ENV VAR OPENSEA_API_KEY not defined")
if not "ALCHEMY_API_KEY" in os.environ:
    exit("ENV VAR ALCHEMY_API_KEY not defined")



###  RPC AND CONTRACT ABI  ###
RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/"
web3 = Web3(Web3.HTTPProvider(RPC_URL+ALCHEMY_API_KEY))

with open("./luchaABI.txt", "r") as file:
    luchaABI = json.load(file)

# Luchadores Polygon contract
CONTRACT_ADDR_1 = "0xE8B73c064BD3B8c5DB438118543ACd6AAb18F108"
lucha_claim = web3.eth.contract(address=CONTRACT_ADDR_1, abi=luchaABI)



###  OPENSEA  ###
# OpenSea API doc: https://docs.opensea.io/reference/api-overview
# Luchadores Ethereum contract
CONTRACT_ADDR_2 = "0x8b4616926705fb61e9c4eeac07cd946a5d4b0760"
OPENSEA_API_URL = "https://api.opensea.io/api/v1/asset/" + CONTRACT_ADDR_2 + "/"
OPENSEA_URL     = "https://opensea.io/assets/"           + CONTRACT_ADDR_2 + "/"



###  OTHERS  ###
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
LUCHADORES_IMG_URL = "https://luchadores-io.s3.us-east-2.amazonaws.com/img/"



###  Send get requests to opensea API  ###
def handle_request(url):
    try:
        response = requests.get(
            url,
            headers = {"Accept": "application/json","X-API-KEY": OPENSEA_API_KEY}
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



###  Refresh lucha, eth and floor price  ###
@tasks.loop(minutes=1)
async def updateName(guild):

    
    lucha = cg.get_price(ids='lucha', vs_currencies='usd')
    lucha_price = str(lucha['lucha']['usd'])
    print(lucha_price)
    await guild.me.edit(nick=lucha_price)
    #print("KEEP ALIVE")

    #guild = client.get_guild(DISCORD_GUILD) # Get the guild in question so you can actually get a member object
    #converter = MemberConverter()
    #member = await converter.convert(guild, id) # conver
    #await member.edit(nick=btc_price)
    

client = discord.Client()

@client.event
async def on_ready():

    msg="Set up!"


    updateName.start(client.get_guild(DISCORD_GUILD))

    channel = client.get_channel(DISCORD_CHANNEL_1)
    #await client.change_presence(activity=discord.Game('Charles'))
    #await client.change_presence(activity=discord.Streaming(name='Sea of Thieves', url='https://www.twitch.tv/your_channel_here'))

    #guild = client.get_guild(DISCORD_GUILD)
    #client.guild.me.edit(nick="ok")
    #await client.user.edit(username="YOLO")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='Charles :)'))
    await channel.send(msg)
    


@client.event
async def on_message(message):

    channel_lucha             = client.get_channel(DISCORD_CHANNEL_1)
    channel_lucha_not_claimed = client.get_channel(DISCORD_CHANNEL_2)

    # If the bot send a msg, do nothing
    if message.author == client.user:
        return
    

    # Check how many lucha have been claimed out of 10k
    if message.channel == channel_lucha_not_claimed:

        msg = "Fetching data, plz wait, it can take up to 1h..."
        await channel_lucha_not_claimed.send(msg)
        
        not_claimed = []
        counter = 0

        for i in range(1,10000):

            hasBeenClaimed = lucha_claim.functions.lastClaim(i).call()
            if not hasBeenClaimed:
                not_claimed.append(i)
                counter += 1

            if counter == 10:
                counter = 0
                await channel_lucha_not_claimed.send(not_claimed[-10:])
        await channel_lucha_not_claimed.send(not_claimed[-counter:])    

        msg = "Total not claimed on 10k lucha: "
        msg += str(len(not_claimed))
        await channel_lucha_not_claimed.send(msg)


    # fetch opensea data on a specific lucha
    elif message.channel == channel_lucha:

        try:
            num = int(message.content)
        except ValueError:
            await channel_lucha.send("Type an integer")
            return
        if(num <= 0 or num > 10000):
            await channel_lucha.send("Type an integer between 1 and 10 000")
            return
        

        listing_url  = OPENSEA_API_URL + message.content + "/listings"
        listing_body = handle_request(listing_url)

        if listing_body["code"] != 0:
            channel_lucha.send(listing_body["msg"])
            return

        asset_url  = OPENSEA_API_URL + message.content
        asset_body = handle_request(asset_url)

        if asset_body["code"] != 0:
            channel_lucha.send(asset_body["msg"])
            return


        traits = asset_body["msg"]['traits'][-1]['value']
        luchaYield = lyield[traits]
        hasBeenClaimed = lucha_claim.functions.lastClaim(num).call()
        pendingYield = lucha_claim.functions.pendingYield(num).call() / (10**18)

        listings = listing_body["msg"]["listings"]

        # if the lucha is listed on sale
        if len(listings) == 1:

            lucha = cg.get_price(ids='lucha', vs_currencies='usd')
            lucha_price = lucha['lucha']['usd']
            ethereum = cg.get_price(ids='ethereum', vs_currencies='usd')
            ethereum_price = ethereum['ethereum']['usd']

            # eth price, then $ price
            listingPrice = float(listings[0]["current_price"]) / (10**18)
            price = listingPrice * ethereum_price
            
            # $ price with $lucha token deducted
            realPrice = price - pendingYield * lucha_price
            roi = int(realPrice / (luchaYield * lucha_price))

        elif len(listings) > 1:
            channel_lucha.send("alerte > 1 listing! plz check")
      

        # send data back in discord
        img_url = LUCHADORES_IMG_URL + str(num) + ".png"

        embed = discord.Embed(title = "Luchadores {}".format(num),
                              url   = OPENSEA_URL+str(num),
                              color = discord.Color.from_rgb(255,0,0))
        embed.set_thumbnail(url = img_url)
        embed.add_field(name   = "Attributes",
                        value  = traits,
                        inline = True)
        embed.add_field(name   = "Daily yield",
                        value  = luchaYield,
                        inline = True)
        embed.add_field(name   = "Pending $lucha",
                        value  = int(pendingYield),
                        inline = True)

        if hasBeenClaimed:
            embed.add_field(name   = "Never claimed",
                            value  = "No",
                            inline = True)
        else:
            embed.add_field(name   = "Never claimed",
                            value  = "Yes",
                            inline = True)

        if len(listings) == 1:
            embed.add_field(name   = "ROI in days",
                            value  = roi,
                            inline = True)
            embed.add_field(name   = "ETH Price",
                            value  = listingPrice,
                            inline = True)
            embed.add_field(name   = "Real $ price",
                            value  = int(realPrice),
                            inline = True)


        await channel_lucha.send(embed=embed)
        
        

client.run(DISCORD_TOKEN)