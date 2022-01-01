from brownie import config, Contract
import discord
import requests
import json



DISCORD_TOKEN = config["discord"]["token"]
DISCORD_CHANNEL_LUCHA = config["discord"]["channel_lucha"]


lucha_claim_address = config["networks"]["polygon-main"]["lucha_claim"]
lucha_claim = Contract.from_explorer(lucha_claim_address)

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
    if message.channel == channel_lucha:
        
        url = base_url + message.content
        response = requests.get(url)
        req = json.loads(response.content)

        num = int(message.content)
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

