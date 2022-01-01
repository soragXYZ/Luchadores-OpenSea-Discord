from brownie import config, interface, Contract
from web3 import Web3
import requests
import json

import sys


def main():

    lucha_claim_address = config["networks"]["polygon-main"]["lucha_claim"]
    lucha_claim = Contract.from_explorer(lucha_claim_address)

    # check OpenSea API here: https://docs.opensea.io/reference/retrieving-a-single-asset
    lucha_SC = config["networks"]["polygon-main"]["lucha_SC"]
    base_url = "https://api.opensea.io/api/v1/asset/" + lucha_SC + "/"

    # $LUCHA yield base on attribute rarity: https://luchadores.io/yield
    lyield = {3:1,
              2:1,
              4:2,
              1:3,
              5:4,
              6:6,
              0:6,
              7:10
    }
    
    luchaRoi = {}


    for i in range(60,100):

        url = base_url + str(i)
        response = requests.get(url)
        req = json.loads(response.content)

        if req['orders']:
            for j in range(len(req['orders'])):
                if req['orders'][j]['side']:

                    gweiPrice = float(req['orders'][j]['current_price'])
                    ETHprice = gweiPrice / (10**18)
                    price = gweiPrice / (10**18) * config["price"]["eth"]

                    pendingYield = lucha_claim.pendingYield(i) / (10**18)
                    hasBeenClaimed = lucha_claim.lastClaim(i)

                    traits = req['traits'][-1]['value']
                    luchaYield = lyield[traits]

                    realPrice = price - pendingYield * config["price"]["lucha"]
                    roi = int(realPrice / (luchaYield * config["price"]["lucha"]))

                    print("Lucha",i,"on sale")
                    if( not hasBeenClaimed):
                        print("\033[91mNever claimed \033[0m")
                    print("ROI in days:", roi)
                    print("Price eth:", ETHprice)
                    print("$lucha pending:", pendingYield)
                    print("Traits:", traits)
                    print("$LUCHA / day: ", luchaYield)
                    print("Real price with deducted pending $lucha: $", int(realPrice))
                    print("---")
                    if i not in luchaRoi:
                        luchaRoi[i] = [roi,traits]
                    elif i in luchaRoi and roi < luchaRoi[i][0]:
                        luchaRoi[i] = [roi,traits]

    with open('log.txt', 'w') as f:
        sys.stdout = f
        print(sorted(luchaRoi.items(), key=lambda x: x[1]))