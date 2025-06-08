#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Point d'entrée principal pour le serveur MCP Free-Work
"""

from server import mcp

# Import des outils pour les enregistrer via les décorateurs
import tools.freework_tools

# Point d'entrée pour exécuter le serveur
if __name__ == "__main__":
    print("Démarrage du serveur MCP Free-Work...")
    mcp.run()
