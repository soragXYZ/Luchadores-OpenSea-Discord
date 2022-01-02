from brownie import config, Contract, interface
import discord
import requests
import json



DISCORD_TOKEN = config["discord"]["token"]
DISCORD_CHANNEL_LUCHA = config["discord"]["channel_lucha"]
DISCORD_CHANNEL_LUCHA_NOT_CLAIMED = config["discord"]["channel_lucha_not_claimed"]


lucha_claim_address = config["networks"]["polygon-main"]["lucha_claim"]
#lucha_claim = Contract.from_explorer(lucha_claim_address)
abi=[{"inputs":[{"internalType":"address","name":"_luchaToken","type":"address"},{"internalType":"address","name":"_luchaMirror","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Claimed","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"account","type":"address"}],"name":"Paused","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"bytes32","name":"role","type":"bytes32"},{"indexed":True,"internalType":"bytes32","name":"previousAdminRole","type":"bytes32"},{"indexed":True,"internalType":"bytes32","name":"newAdminRole","type":"bytes32"}],"name":"RoleAdminChanged","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"bytes32","name":"role","type":"bytes32"},{"indexed":True,"internalType":"address","name":"account","type":"address"},{"indexed":True,"internalType":"address","name":"sender","type":"address"}],"name":"RoleGranted","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"bytes32","name":"role","type":"bytes32"},{"indexed":True,"internalType":"address","name":"account","type":"address"},{"indexed":True,"internalType":"address","name":"sender","type":"address"}],"name":"RoleRevoked","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"account","type":"address"}],"name":"Unpaused","type":"event"},{"inputs":[],"name":"DEFAULT_ADMIN_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"claim","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"end","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"}],"name":"getRoleAdmin","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"grantRole","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"hasRole","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"lastClaim","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"luchaMirror","outputs":[{"internalType":"contract ILuchaMirror","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"luchaToken","outputs":[{"internalType":"contract ILuchaToken","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"paused","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"id","type":"uint256"}],"name":"pendingYield","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"renounceRole","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"revokeRole","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes","name":"yieldRates","type":"bytes"}],"name":"setYieldRates","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"start","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"startYield","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"totalClaimable","outputs":[{"internalType":"uint256","name":"totalClaim","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"unpause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newMirror","type":"address"}],"name":"updateMirror","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"id","type":"uint256"}],"name":"yieldRate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
lucha_claim = Contract.from_abi("Token",lucha_claim_address,abi)

# check OpenSea API here: https://docs.opensea.io/reference/retrieving-a-single-asset
lucha_SC = config["networks"]["polygon-main"]["lucha_SC"]
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


@client.event
async def on_ready():

    msg="Set up!"
    channel = client.get_channel(int(DISCORD_CHANNEL_LUCHA))
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
            hasBeenClaimed = lucha_claim.lastClaim(i)
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
            response = requests.get(url)
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
        

        
        pendingYield = lucha_claim.pendingYield(num) / (10**18)
        hasBeenClaimed = lucha_claim.lastClaim(num)
        traits = req['traits'][-1]['value']
        luchaYield = lyield[traits]

        if req['orders']:
            for j in range(len(req['orders'])):
                if req['orders'][j]['side']:

                    gweiPrice = float(req['orders'][j]['current_price'])
                    ETHprice = gweiPrice / (10**18)
                    price = gweiPrice / (10**18) * config["price"]["eth"]

                    realPrice = price - pendingYield * config["price"]["lucha"]
                    roi = int(realPrice / (luchaYield * config["price"]["lucha"]))

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

        await channel_lucha.send(msg)
        

client.run(DISCORD_TOKEN)

