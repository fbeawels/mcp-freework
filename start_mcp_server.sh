#!/bin/bash

# Script pour démarrer le serveur MCP Free-Work
# Utilisation: ./start_mcp_server.sh

# Chemin vers le répertoire du projet
PROJECT_DIR="$(dirname "$(readlink -f "$0")")"

# Activation de l'environnement virtuel si présent
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Démarrage du serveur MCP
python "$PROJECT_DIR/main.py"
