# Luchadores Discord Bot

## Description :

Ce bot discord permet d'afficher les données en temps réel sur la collection NFT luchadores-io en récupérant les données depuis l'API d'OpenSea (ventes, offres, transferts...), et aussi d'afficher le floor price des luchadores en fonction de leur nombre d'attributs.

## Prérequis et variables d'environnement :

Pour faire fonctionner le bot, une clé API OpenSea est nécessaire. Vous pouvez en faire la demande [ici](https://docs.opensea.io/reference/request-an-api-key).

Il faut ensuite créer plusieurs salons discord

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