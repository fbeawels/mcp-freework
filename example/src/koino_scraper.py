#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Scraper pour récupérer les missions publiées sur Koino.fr
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
from dateutil.parser import parse
import logging
import html

# Configuration du logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('koino_scraper')

class KoinoScraper:
    """
    Classe pour scraper les missions publiées sur Koino.fr
    """
    
    BASE_URL = "https://www.koino.fr"
    MISSIONS_URL = f"{BASE_URL}/nosmissions"
    
    def __init__(self):
        """
        Initialisation du scraper
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _parse_date(self, date_str):
        """
        Parse une date au format JJ/M/AA
        
        Args:
            date_str (str): Date au format JJ/M/AA
            
        Returns:
            datetime: Objet datetime représentant la date
        """
        try:
            # Format: JJ/M/AA (ex: 16/5/25)
            if not date_str or date_str == "Non spécifié":
                logger.error(f"Date non spécifiée ou invalide: '{date_str}'")
                return None
                
            # Nettoyage de la date
            date_str = date_str.strip()
            
            # Vérification du format de la date
            if not re.match(r'^[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}$', date_str):
                logger.error(f"Format de date invalide: '{date_str}'")
                return None
                
            day, month, year = map(int, date_str.split('/'))
            
            # Ajout du préfixe '20' pour l'année si nécessaire
            if year < 100:
                year = 2000 + year
                
            # Vérification de la validité de la date
            if not (1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100):
                logger.error(f"Valeurs de date invalides: jour={day}, mois={month}, année={year}")
                return None
                
            return datetime(year, month, day)
        except (ValueError, AttributeError) as e:
            logger.error(f"Erreur lors du parsing de la date '{date_str}': {e}")
            return None
    
    def _is_recent(self, date_str, days=7):
        """
        Vérifie si une date est récente (moins de X jours)
        
        Args:
            date_str (str): Date au format JJ/M/AA
            days (int): Nombre de jours pour considérer une mission comme récente
            
        Returns:
            bool: True si la date est récente, False sinon
        """
        date = self._parse_date(date_str)
        if not date:
            logger.warning(f"Impossible de déterminer si la date '{date_str}' est récente")
            return False
        
        today = datetime.now()
        delta = today - date
        
        is_recent = delta.days < days
        logger.info(f"Date '{date_str}' ({date.strftime('%Y-%m-%d')}) est récente ({delta.days} jours): {is_recent}")
        
        return is_recent
    
    def _clean_text(self, text):
        """
        Nettoie le texte des caractères spéciaux mal encodés
        
        Args:
            text (str): Texte à nettoyer
            
        Returns:
            str: Texte nettoyé
        """
        if not text:
            return ""
            
        # Décoder les entités HTML
        text = html.unescape(text)
        
        # Remplacer les caractères spéciaux mal encodés
        replacements = {
            'Ã©': 'é',
            'Ã¨': 'è',
            'Ã§': 'ç',
            'Ã ': 'à',
            'Ã¢': 'â',
            'Ãª': 'ê',
            'Ã®': 'î',
            'Ã´': 'ô',
            'Ã»': 'û',
            'Ã¹': 'ù',
            'Ã«': 'ë',
            'Ã¯': 'ï',
            'Ã¼': 'ü',
            'Ã': 'É',
            'Ã': 'È',
            'Ã': 'Ê',
            'Ã': 'À',
            'Ã': 'Â',
            'Ã': 'Ó',
            'Ã': 'Û',
            'Ã': 'Ù',
            'Ã': 'Ë',
            'Ã¯': 'Ï',
            'Ã': 'Ü',
            'â': "'",
            'â': '"',
            'â': '"',
            'â¦': '...',
            'â': '-',
            'â': '-',
            'Â': '',
            '\xa0': ' '
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Supprimer les caractères non imprimables
        text = ''.join(c for c in text if c.isprintable() or c in '\n\t ')
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limiter la longueur à 100 caractères pour éviter les textes trop longs
        if len(text) > 100:
            text = text[:97] + '...'
            
        return text
    
    def _extract_mission_details(self, mission_url):
        """
        Extrait les détails d'une mission à partir de son URL
        
        Args:
            mission_url (str): URL de la mission
            
        Returns:
            dict: Détails de la mission
        """
        try:
            logger.info(f"Extraction des détails de la mission: {mission_url}")
            response = self.session.get(mission_url)
            response.encoding = 'utf-8'  # Force l'encodage UTF-8
            response.raise_for_status()
            
            # Sauvegarde du HTML pour débogage
            with open(f"/tmp/koino_mission_{mission_url.split('/')[-1]}.html", 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction des informations de base
            title = soup.find('h1').text.strip() if soup.find('h1') else "Titre non disponible"
            title = self._clean_text(title)
            logger.info(f"Titre extrait: {title}")
            
            # Initialisation des données de mission
            mission_data = {
                'localisation': "Non spécifié",
                'département': "Non spécifié",
                'date': "25/5/25",  # Date par défaut: aujourd'hui
                'tjm': "Non spécifié",
                'numéro mission': f"AUTO-{hash(mission_url) % 10000}"
            }
            
            # Extraction des informations structurées basée sur la structure observée dans l'image
            # Recherche des éléments de type "job_label-card" qui contiennent les informations
            job_cards = soup.find_all('div', class_='job_label-card')
            logger.info(f"Nombre de job_label-card trouvés: {len(job_cards)}")
            
            for card in job_cards:
                # Recherche du label (Localisation, Département, Date, TJM)
                label_elem = card.find('p', class_='paragraph-18')
                if not label_elem:
                    continue
                
                label = self._clean_text(label_elem.text.strip().lower())
                logger.info(f"Label trouvé: {label}")
                
                # Recherche de la valeur associée au label
                value_elem = card.find('p', class_='h6-2')
                if not value_elem:
                    continue
                
                value = self._clean_text(value_elem.text.strip())
                logger.info(f"Valeur trouvée pour {label}: {value}")
                
                # Mapping des labels aux clés de notre dictionnaire
                if 'localisation' in label:
                    mission_data['localisation'] = value
                elif 'département' in label:
                    mission_data['département'] = value
                elif 'date' in label:
                    mission_data['date'] = value
                elif 'tjm' in label:
                    mission_data['tjm'] = value
            
            # Recherche du numéro de mission
            numero_elem = soup.find(string=re.compile('Numéro mission', re.IGNORECASE))
            if numero_elem and numero_elem.parent:
                numero_text = numero_elem.parent.text.strip()
                match = re.search(r'Numéro mission\s*([0-9]+)', numero_text, re.IGNORECASE)
                if match:
                    mission_data['numéro mission'] = match.group(1).strip()
                    logger.info(f"Numéro de mission trouvé: {mission_data['numéro mission']}")
            
            # Si les informations structurées n'ont pas été trouvées, essayons une approche basée sur le texte
            if mission_data['localisation'] == "Non spécifié" or mission_data['département'] == "Non spécifié":
                logger.info("Tentative d'extraction par pattern matching sur le texte complet")
                
                # Extraction du texte complet de la page
                all_text = soup.get_text()
                all_text = self._clean_text(all_text)
                
                # Patterns pour extraire les informations
                patterns = {
                    'localisation': [r'Localisation[\s\n]*:?[\s\n]*([^\n]+)', r'Lieu[\s\n]*:?[\s\n]*([^\n]+)'],
                    'département': [r'Département[\s\n]*:?[\s\n]*([^\n]+)', r'Catégorie[\s\n]*:?[\s\n]*([^\n]+)'],
                    'date': [r'Date[\s\n]*:?[\s\n]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})', r'Publié le[\s\n]*:?[\s\n]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})'],
                    'tjm': [r'TJM[\s\n]*:?[\s\n]*([^\n]+)', r'Tarif[\s\n]*:?[\s\n]*([^\n]+)'],
                    'numéro mission': [r'Numéro mission[\s\n]*:?[\s\n]*([0-9]+)', r'Référence[\s\n]*:?[\s\n]*([0-9]+)']
                }
                
                for key, pattern_list in patterns.items():
                    # Ne remplacer que si la valeur n'a pas été trouvée par la méthode structurée
                    if mission_data.get(key) in ["Non spécifié", None, ""] or (key == 'date' and mission_data.get(key) == "25/5/25"):
                        for pattern in pattern_list:
                            match = re.search(pattern, all_text, re.IGNORECASE)
                            if match:
                                value = match.group(1).strip()
                                value = self._clean_text(value)
                                mission_data[key] = value
                                logger.info(f"Pattern match pour {key}: {mission_data[key]}")
                                break
            
            # Construction du dictionnaire de retour
            mission_details = {
                "titre": title,
                "tjm": mission_data.get("tjm", "Non spécifié"),
                "localisation": mission_data.get("localisation", "Non spécifié"),
                "departement": mission_data.get("département", "Non spécifié"),
                "date": mission_data.get("date", "25/5/25"),
                "numero_mission": mission_data.get("numéro mission", f"AUTO-{hash(mission_url) % 10000}"),
                "url": mission_url
            }
            
            logger.info(f"Détails extraits avec succès: {mission_details}")
            return mission_details
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des détails de la mission '{mission_url}': {e}")
            return {
                "titre": "Erreur lors de l'extraction",
                "tjm": "Non disponible",
                "localisation": "Non disponible",
                "departement": "Non disponible",
                "date": "Non disponible",
                "numero_mission": "Non disponible",
                "url": mission_url
            }
    
    def get_recent_missions(self, days=7):
        """
        Récupère les missions publiées depuis moins de X jours
        
        Args:
            days (int): Nombre de jours pour considérer une mission comme récente
            
        Returns:
            list: Liste des missions récentes
        """
        try:
            logger.info(f"Récupération des missions des {days} derniers jours")
            response = self.session.get(self.MISSIONS_URL)
            response.encoding = 'utf-8'  # Force l'encodage UTF-8
            response.raise_for_status()
            
            logger.info(f"Page principale récupérée avec succès: {self.MISSIONS_URL}")
            
            # Sauvegarde du HTML pour débogage
            with open('/tmp/koino_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"HTML sauvegardé dans /tmp/koino_debug.html pour débogage")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Recherche des sections de missions ouvertes
            mission_sections = []
            h2_elements = soup.find_all('h2')
            
            for h2 in h2_elements:
                if 'Missions ouvertes' in h2.text:
                    # Trouver la section parent qui contient les missions
                    parent_section = h2.find_parent('div')
                    if parent_section:
                        mission_sections.append(parent_section)
                        logger.info(f"Section de missions ouvertes trouvée")
            
            # Si aucune section n'est trouvée, utiliser toute la page
            if not mission_sections:
                mission_sections = [soup]
                logger.info(f"Aucune section spécifique trouvée, utilisation de toute la page")
            
            # Approche directe: recherche de tous les liens vers des missions
            mission_links = []
            
            # Recherche de tous les liens contenant 'missions-freelance' dans les sections identifiées
            for section in mission_sections:
                for link in section.find_all('a', href=True):
                    href = link.get('href')
                    if 'missions-freelance' in href:
                        full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                        mission_links.append(full_url)
                        logger.info(f"Lien de mission trouvé: {full_url}")
            
            logger.info(f"Nombre total de liens de missions trouvés: {len(mission_links)}")
            
            # Dédupliquer les liens
            mission_links = list(set(mission_links))
            logger.info(f"Nombre de liens uniques: {len(mission_links)}")
            
            recent_missions = []
            
            # Parcours des liens de missions
            for mission_url in mission_links:
                logger.info(f"Traitement de la mission: {mission_url}")
                
                # Extraction des détails de la mission
                mission_details = self._extract_mission_details(mission_url)
                logger.info(f"Détails extraits: {mission_details}")
                
                # Vérifier si la mission est récente (moins de X jours)
                if self._is_recent(mission_details['date'], days):
                    recent_missions.append(mission_details)
                    logger.info(f"Mission récente ajoutée: {mission_details['titre']} - {mission_details['date']}")
                else:
                    logger.info(f"Mission non récente ignorée: {mission_details['titre']} - {mission_details['date']}")
            
            logger.info(f"Nombre total de missions récentes trouvées: {len(recent_missions)}")
            return recent_missions
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des missions récentes: {e}")
            return []

if __name__ == "__main__":
    # Test du scraper
    scraper = KoinoScraper()
    missions = scraper.get_recent_missions()
    
    print(json.dumps(missions, indent=2, ensure_ascii=False))
