#!/bin/bash

# Script de démarrage du serveur MCP Koino

# Aller dans le répertoire du projet
cd "$(dirname "$0")"

# Activer l'environnement virtuel si nécessaire
# source ../.venv/bin/activate

# Démarrer le serveur MCP
python main.py
