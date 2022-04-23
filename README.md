# Luchadores Discord Bot

## Description :

Ce bot discord permet d'afficher les données en temps réel sur la collection NFT luchadores-io en récupérant les données depuis l'API d'OpenSea.  
Il permet d'afficher:  
* Les ventes, listings, offres et transferts
* Le floor price des luchadores en fonction de leur nombre d'attributs
* Les détails d'un luchadore spécifique en écrivant son identifiant dans le salon dédié  

![Exemple_bot](https://zupimages.net/viewer.php?id=22/16/rwxf.png)  

![Exemple_channel](https://zupimages.net/viewer.php?id=22/16/9t36.png)  

![Exemple_getData](https://zupimages.net/viewer.php?id=22/16/kpu4.png)

## Prérequis et variables d'environnement :

Pour faire fonctionner le bot, il est nécessaire de créer un fichier d'environnement .env et de définir les variables suivantes:
```
DISCORD_TOKEN = xxx

CHANNEL_GET_DATA    = xxx
CHANNEL_FLOOR       = xxx
CHANNEL_ETH_PRICE   = xxx
CHANNEL_LUCHA_PRICE = xxx
CHANNEL_SALES       = xxx
CHANNEL_LISTINGS    = xxx
CHANNEL_OFFERS      = xxx
CHANNEL_TRANSFERS   = xxx
CHANNEL_DEBUG       = xxx

CHANNEL_0T = xxx
CHANNEL_1T = xxx
CHANNEL_2T = xxx
CHANNEL_3T = xxx
CHANNEL_4T = xxx
CHANNEL_5T = xxx
CHANNEL_6T = xxx
CHANNEL_7T = xxx

OPENSEA_API_KEY = xxx
ALCHEMY_API_KEY = xxx
```

Les variables channel correspondent aux identifiants de vos salons Discord.  
Vous pouvez faire la demande de votre clé API OpenSea [ici](https://docs.opensea.io/reference/request-an-api-key).  
De même, pour récupérer une clé API Alchemy, vous pouvez vous créer un compte [ici](https://dashboard.alchemyapi.io/).

## Installation :

Le bot est codé en python. Pour l'installer et le lancer, suivre les étapes suivantes :

Création d'un environnement virtuel
```
python3 -m venv venv
```

Se placer dans l'environnement virtuel (Windows)
```
venv/Scripts/activate
```

Installation des dépendences
```
pip install -r requirements.txt
```

Lancer le bot
```
python bot.py
python attributeFloor.py
```

Pour lancer le bot sur une VM / le laisser tourner en tâche de fond
```
nohup python bot.py > logBot.txt &
nohup python attributeFloor.py > logAttr.txt &
```

Quitter l'environnement virtuel
```
deactivate
```

## Bugs / Me contacter :

Pour tout bug, demande d'améliorations, propositions ou autre, n'hésitez pas à ouvrir une issue