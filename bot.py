#from brownie import config, Contract, interface
import discord
import requests
import json
import io
import aiohttp

from discord.ext import tasks
from discord.ext.commands import MemberConverter
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

from web3 import Web3
from dotenv import load_dotenv

import os
load_dotenv()


API_KEY = os.environ.get("API_KEY")
DISCORD_GUILD = int(os.environ.get("DISCORD_GUILD"))
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL_LUCHA = os.environ.get("DISCORD_CHANNEL_LUCHA")
DISCORD_CHANNEL_LUCHA_NOT_CLAIMED = os.environ.get("DISCORD_CHANNEL_LUCHA_NOT_CLAIMED")
ALCHEMY_KEY = os.environ.get("ALCHEMY_KEY")

if not "API_KEY" in os.environ:
    exit("ENV VAR API_KEY not defined")

headers = {
    "Accept": "application/json",
    "X-API-KEY": API_KEY
}


RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/"


LUCHA_CONTRACT_ADDR = "0xE8B73c064BD3B8c5DB438118543ACd6AAb18F108"

ETH_PRICE = 4000
LUCHA_PRICE = 1

web3 = Web3(Web3.HTTPProvider(RPC_URL+ALCHEMY_KEY))

with open("./abi.txt", "r") as file:
    abi = json.load(file)

lucha_claim = web3.eth.contract(address=LUCHA_CONTRACT_ADDR, abi=abi)



# check OpenSea API here: https://docs.opensea.io/reference/retrieving-a-single-asset
lucha_SC = "0x8b4616926705fb61e9c4eeac07cd946a5d4b0760"
base_url = "https://api.opensea.io/api/v1/asset/" + lucha_SC + "/"

# $LUCHA yield base on attribute rarity: https://luchadores.io/yield
lyield = {  3:1,
            2:1,
            4:2,
            1:3,
            5:4,
            6:6,
            0:6,
            7:10
}

luchaRoi = {}

client = discord.Client()
i=0

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
    



@client.event
async def on_ready():

    msg="Set up!"


    updateName.start(client.get_guild(DISCORD_GUILD))

    channel = client.get_channel(int(DISCORD_CHANNEL_LUCHA))
    #await client.change_presence(activity=discord.Game('Charles'))
    #await client.change_presence(activity=discord.Streaming(name='Sea of Thieves', url='https://www.twitch.tv/your_channel_here'))

    #guild = client.get_guild(DISCORD_GUILD)
    #client.guild.me.edit(nick="ok")
    #await client.user.edit(username="YOLO")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='Charles :)'))
    await channel.send(msg)
    


@client.event
async def on_message(message):

    if message.author == client.user:
        return
    
    channel_lucha = client.get_channel(int(DISCORD_CHANNEL_LUCHA))
    channel_lucha_not_claimed = client.get_channel(int(DISCORD_CHANNEL_LUCHA_NOT_CLAIMED))

    if message.channel == channel_lucha_not_claimed:
        msg = "Fetching data, plz wait, it can take up to 30min..."
        await channel_lucha_not_claimed.send(msg)
        not_claimed = []
        counter = 0
        for i in range(1,10000):
            hasBeenClaimed = lucha_claim.functions.lastClaim(i).call()
            if( not hasBeenClaimed):
                not_claimed.append(i)
                counter += 1
            if counter == 10:
                counter = 0
                await channel_lucha_not_claimed.send(not_claimed[-10:])
        await channel_lucha_not_claimed.send(not_claimed[-counter:])    

        msg = "Total not claimed on 10k lucha: "
        msg += str(len(not_claimed))

        await channel_lucha_not_claimed.send(msg)


    elif message.channel == channel_lucha:
        try:
            num = int(message.content)
        except ValueError:
            await channel_lucha.send("Type an integer")
            return
        if(num <= 0 or num > 10000):
            await channel_lucha.send("Type an integer between 1 and 10 000")
            return
        

        url = base_url + message.content
        try:
            print(url)
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            msg = "Http error: " + str(errh)
            await channel_lucha.send(msg)
            return
        except requests.exceptions.ConnectionError as errc:
            msg = "Error connecting: " + str(errc)
            await channel_lucha.send(msg)
            return
        except requests.exceptions.Timeout as errt:
            msg = "Timeout error: " + str(errt)
            await channel_lucha.send(msg)
            return
        except requests.exceptions.RequestException as err:
            msg = "Something went wrong: " + str(err)
            await channel_lucha.send(msg)
            return

        try:
            req = json.loads(response.content)
        except ValueError:
            msg = "Invalid json sent by OpenSea"
            await channel_lucha.send(msg)
            return
        

        
        pendingYield = lucha_claim.functions.pendingYield(num).call() / (10**18)
        hasBeenClaimed = lucha_claim.functions.lastClaim(num).call()
        traits = req['traits'][-1]['value']
        luchaYield = lyield[traits]

        if req['orders']:
            for j in range(len(req['orders'])):
                if req['orders'][j]['side']:

                    gweiPrice = float(req['orders'][j]['current_price'])
                    ETHprice = gweiPrice / (10**18)
                    price = gweiPrice / (10**18) * ETH_PRICE

                    realPrice = price - pendingYield * LUCHA_PRICE
                    roi = int(realPrice / (luchaYield * LUCHA_PRICE))

                    if num not in luchaRoi:
                        luchaRoi[num] = [roi,traits]
                    elif num in luchaRoi and roi < luchaRoi[num][0]:
                        luchaRoi[num] = [roi,traits]

        if num in luchaRoi:          
            msg = "Lucha " + str(num) + " on sale!\n"
            if( not hasBeenClaimed):
                msg += "Never claimed\n"
            msg += "ROI in days: "
            msg += str(roi)
            msg += "\nETH Price: "
            msg += str(ETHprice)
            msg += "\n$lucha pending: "
            msg += str(pendingYield)
            msg += "\nTraits: "
            msg += str(traits)
            msg += "\n$LUCHA / day: "
            msg += str(luchaYield)
            msg += "\nReal price with deducted pending $lucha: $ "
            msg += str(int(realPrice))

        else:
            msg = "Lucha " + str(num) + " not on sale!\n"
            if( not hasBeenClaimed):
                msg += "Never claimed\n"
            msg += "$lucha pending: "
            msg += str(pendingYield)
            msg += "\nTraits: "
            msg += str(traits)
            msg += "\n$LUCHA / day: "
            msg += str(luchaYield)

        img_url = "https://luchadores-io.s3.us-east-2.amazonaws.com/img/" + str(num) + ".png"
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as resp:
                if resp.status != 200:
                    return await channel.send('Could not download file...')
                data = io.BytesIO(await resp.read())
                await channel_lucha.send(msg, file=discord.File(data, 'cool_image.png'))
        
        

client.run(DISCORD_TOKEN)

