#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Scraper pour récupérer les missions publiées sur Free-Work.com
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
logger = logging.getLogger('freework_scraper')

class FreeWorkScraper:
    """
    Classe pour scraper les missions publiées sur Free-Work.com
    """
    
    BASE_URL = "https://www.free-work.com"
    MISSIONS_URL = f"{BASE_URL}/fr/tech-it/jobs"
    
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
        Parse une date au format français
        
        Args:
            date_str (str): Date au format français (JJ/MM/AAAA ou similaire)
            
        Returns:
            datetime: Objet datetime représentant la date
        """
        try:
            if not date_str or date_str == "Non spécifié":
                logger.error(f"Date non spécifiée ou invalide: '{date_str}'")
                return None
                
            # Nettoyage de la date
            date_str = date_str.strip()
            
            # Essayer de parser la date avec dateutil
            try:
                return parse(date_str, dayfirst=True)  # Format français: jour en premier
            except:
                # Si dateutil échoue, essayer avec des formats spécifiques
                formats = [
                    "%d/%m/%Y",  # 01/01/2023
                    "%d/%m/%y",  # 01/01/23
                    "%d-%m-%Y",  # 01-01-2023
                    "%d-%m-%y",  # 01-01-23
                    "%d %B %Y",  # 01 janvier 2023
                    "%d %b %Y",  # 01 jan 2023
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
                
                logger.error(f"Impossible de parser la date: '{date_str}'")
                return None
                
        except (ValueError, AttributeError) as e:
            logger.error(f"Erreur lors du parsing de la date '{date_str}': {e}")
            return None
    
    def _is_recent(self, date_str, days=7):
        """
        Vérifie si une date est récente (moins de X jours)
        
        Args:
            date_str (str): Date au format français
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
            with open(f"/tmp/freework_mission_{mission_url.split('/')[-1]}.html", 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction du titre (plusieurs méthodes possibles)
            title = "Titre non disponible"
            # Méthode 1: Chercher dans le titre de la page
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.text.strip()
                # Format typique: "ENTREPRISE — Offre d'emploi TITRE LIEU | Free-work"
                if "—" in title_text and "Offre d'emploi" in title_text:
                    title_parts = title_text.split("—")
                    if len(title_parts) > 1:
                        title_part = title_parts[1].strip()
                        if "Offre d'emploi" in title_part:
                            title = title_part.replace("Offre d'emploi", "").strip()
                            if "|" in title:
                                title = title.split("|")[0].strip()
            
            # Méthode 2: Chercher dans le contenu de la page
            if title == "Titre non disponible":
                job_title_elem = soup.select_one("div.job-title")
                if job_title_elem:
                    title = job_title_elem.text.strip()
            
            # Méthode 3: Chercher dans les éléments de la page
            if title == "Titre non disponible":
                # Chercher dans les éléments h1 ou h2
                for h_elem in soup.find_all(['h1', 'h2', 'h3']):
                    if h_elem.text and len(h_elem.text.strip()) > 5 and not h_elem.text.strip().startswith("Offre d'emploi"):
                        title = h_elem.text.strip()
                        break
            
            # Méthode 4: Extraire du chemin de l'URL
            if title == "Titre non disponible":
                url_parts = mission_url.split('/')
                if len(url_parts) > 0:
                    last_part = url_parts[-1]
                    title = last_part.replace('-', ' ').title()
            
            title = self._clean_text(title)
            logger.info(f"Titre extrait: {title}")
            
            # Extraction de l'entreprise
            company = "Entreprise non spécifiée"
            company_elem = soup.select_one("div.company-name")
            if company_elem:
                company = company_elem.text.strip()
            else:
                # Essayer d'extraire du titre de la page
                page_title = soup.find('title')
                if page_title and "—" in page_title.text:
                    company = page_title.text.split("—")[0].strip()
            
            company = self._clean_text(company)
            
            # Extraction de la localisation
            location = "Non spécifié"
            location_elem = soup.select_one("h2")
            if location_elem and "(" in location_elem.text and ")" in location_elem.text:
                location = location_elem.text.strip()
            
            # Extraction de la date (par défaut, on utilise la date du jour)
            date = datetime.now().strftime("%d/%m/%Y")
            
            # Extraction du TJM/salaire
            tjm = "Non spécifié"
            
            # Recherche du TJM dans le texte de la page
            all_text = soup.get_text()
            
            # Patterns pour extraire le TJM
            tjm_patterns = [
                r'TJM[\s\n]*:?[\s\n]*([0-9]+[\s]*[€k][^\n.,;]{0,10})',
                r'Tarif[\s\n]*:?[\s\n]*([0-9]+[\s]*[€k][^\n.,;]{0,10})',
                r'Salaire[\s\n]*:?[\s\n]*([0-9]+[\s]*[€k][^\n.,;]{0,10})',
                r'Rémunération[\s\n]*:?[\s\n]*([0-9]+[\s]*[€k][^\n.,;]{0,10})',
                r'([0-9]+[\s]*[€k][\s]*[-–/à][\s]*[0-9]+[\s]*[€k])',  # Format: 500€ - 700€ ou 50k - 70k
                r'([0-9]+[\s]*€[\s]*(?:par|/|-)[\s]*jour)',  # Format: 500€ par jour
                r'([0-9]+[\s]*€/j)',  # Format: 500€/j
                r'([0-9]+[\s]*k€)',  # Format: 50k€
                r'([0-9]+[\s]*k)',  # Format: 50k
            ]
            
            for pattern in tjm_patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    tjm = match.group(1).strip()
                    logger.info(f"TJM trouvé: {tjm}")
                    break
            
            # Extraction du profil recherché
            profile_text = ""
            profile_section = soup.find('h2', string=re.compile('Profil recherché', re.IGNORECASE))
            if profile_section:
                profile_content = profile_section.find_next('div')
                if profile_content:
                    profile_text = profile_content.text.strip()
                    profile_text = self._clean_text(profile_text)
            
            # Génération d'un ID unique pour la mission
            mission_id = f"FW-{hash(mission_url) % 100000}"
            
            # Construction du dictionnaire de retour
            mission_details = {
                "titre": title,
                "tjm": tjm,
                "localisation": location,
                "departement": location.split('(')[1].split(')')[0] if '(' in location and ')' in location else "Non spécifié",
                "date": date,
                "numero_mission": mission_id,
                "entreprise": company,
                "profil": profile_text,
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
                "date": datetime.now().strftime("%d/%m/%Y"),
                "numero_mission": f"FW-{hash(mission_url) % 100000}",
                "entreprise": "Non disponible",
                "profil": "Non disponible",
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
            with open('/tmp/freework_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"HTML sauvegardé dans /tmp/freework_debug.html pour débogage")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Recherche des offres d'emploi
            mission_links = []
            
            # Recherche de tous les liens contenant 'job-mission' qui correspondent aux pages de détail des missions
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if '/job-mission/' in href:
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
                
                # Pour Free-Work, nous n'avons pas de date précise de publication
                # Donc on considère toutes les missions comme récentes
                recent_missions.append(mission_details)
                logger.info(f"Mission ajoutée: {mission_details['titre']}")
            
            logger.info(f"Nombre total de missions récentes trouvées: {len(recent_missions)}")
            return recent_missions
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des missions récentes: {e}")
            return []

if __name__ == "__main__":
    # Test du scraper
    scraper = FreeWorkScraper()
    missions = scraper.get_recent_missions()
    
    print(json.dumps(missions, indent=2, ensure_ascii=False))
