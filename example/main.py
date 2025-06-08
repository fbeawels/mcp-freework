#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Point d'entrée principal pour le serveur MCP Koino
"""

from server import mcp

# Import des outils pour les enregistrer via les décorateurs
import tools.koino_tools

# Point d'entrée pour exécuter le serveur
if __name__ == "__main__":
    print("Démarrage du serveur MCP Koino...")
    mcp.run()
