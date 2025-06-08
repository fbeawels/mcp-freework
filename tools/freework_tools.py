#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Outils MCP pour récupérer les missions publiées sur Free-Work.com
"""

from typing import Dict, Any, List, Optional
from server import mcp

# Import du scraper intégré
from src.freework_scraper import FreeWorkScraper

@mcp.tool()
def query_freework_missions(days: int = 7) -> List[Dict[str, Any]]:
    """
    Récupère les missions publiées sur Free-Work.com depuis moins de X jours
    
    Args:
        days (int): Nombre de jours pour considérer une mission comme récente (défaut: 7)
        
    Returns:
        List[Dict[str, Any]]: Liste des missions récentes avec leurs détails
    """
    try:
        # Initialisation du scraper
        scraper = FreeWorkScraper()
        
        # Validation des paramètres
        if not isinstance(days, int) or days < 1 or days > 30:
            return []
        
        # Récupération des missions récentes
        missions = scraper.get_recent_missions(days)
        
        return missions
    except Exception as e:
        print(f"Erreur lors de la récupération des missions: {e}")
        return []

@mcp.tool()
def get_mission_details(mission_url: str) -> Dict[str, Any]:
    """
    Récupère les détails d'une mission spécifique sur Free-Work.com
    
    Args:
        mission_url (str): URL de la mission à récupérer
        
    Returns:
        Dict[str, Any]: Détails de la mission spécifiée
    """
    try:
        # Initialisation du scraper
        scraper = FreeWorkScraper()
        
        # Validation de l'URL
        if not mission_url or not mission_url.startswith("https://www.free-work.com/"):
            return {
                "status": "error",
                "error": "URL de mission invalide. L'URL doit commencer par 'https://www.free-work.com/'"
            }
        
        # Récupération des détails de la mission
        mission_details = scraper._extract_mission_details(mission_url)
        
        if not mission_details:
            return {
                "status": "error",
                "error": f"Impossible de récupérer les détails de la mission à l'URL: {mission_url}"
            }
        
        return {
            "status": "success",
            "mission": mission_details
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
