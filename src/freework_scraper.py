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
    
    def get_recent_missions(self, days=7, max_pages_limit=None):
        """
        Récupère les missions publiées depuis moins de X jours en utilisant les filtres de fraîcheur de Free-Work
        
        Args:
            days (int): Nombre de jours pour considérer une mission comme récente
                        Valeurs supportées: 1 (24h), 7, 14, 30, ou tout autre nombre (sans filtre)
            max_pages_limit (int, optional): Nombre maximum de pages à parcourir. 
                                           Si None, utilise une valeur par défaut de 10.
                                           Si 0, parcourt toutes les pages disponibles.
            
        Returns:
            list: Liste des missions récentes
        """
        try:
            # Détermination du filtre de fraîcheur en fonction du nombre de jours
            freshness_filter = ""
            if days == 1:
                freshness_filter = "freshness=less_than_24_hours"
                logger.info("Filtrage des missions de moins de 24 heures")
            elif days == 7:
                freshness_filter = "freshness=less_than_7_days"
                logger.info("Filtrage des missions de moins de 7 jours")
            elif days == 14:
                freshness_filter = "freshness=less_than_14_days"
                logger.info("Filtrage des missions de moins de 14 jours")
            elif days == 30:
                freshness_filter = "freshness=less_than_30_days"
                logger.info("Filtrage des missions de moins de 30 jours")
            else:
                logger.info(f"Aucun filtre de fraîcheur spécifique pour {days} jours, récupération de toutes les missions")
            
            # Liste pour stocker tous les liens de missions
            all_mission_links = []
            
            # Récupération de la première page pour déterminer le nombre total de pages
            url = self.MISSIONS_URL
            if freshness_filter:
                url += f"?{freshness_filter}&page=1"
            else:
                url += "?page=1"
            
            logger.info(f"Récupération de la première page pour déterminer le nombre total: {url}")
            response = self.session.get(url)
            response.encoding = 'utf-8'  # Force l'encodage UTF-8
            response.raise_for_status()
            
            # Sauvegarde du HTML pour débogage
            with open('/tmp/freework_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"HTML sauvegardé dans /tmp/freework_debug.html pour débogage")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Recherche du nombre total de pages dans le sélecteur de pagination
            total_pages = 1
            pagination_select = soup.find('select', {'id': 'pagination-select'})
            
            if pagination_select:
                logger.info(f"Sélecteur de pagination trouvé: {pagination_select.get('id')}")
                
                # Méthode 1: Recherche de la dernière option qui contient le nombre total de pages
                options = pagination_select.find_all('option')
                logger.info(f"Nombre d'options de pagination trouvées: {len(options)}")
                
                if options:
                    # Trier les options par valeur numérique pour trouver la plus grande
                    valid_options = []
                    for option in options:
                        if option.get('value') and option.get('value').isdigit():
                            valid_options.append((int(option.get('value')), option))
                    
                    if valid_options:
                        # Trier par valeur numérique décroissante
                        valid_options.sort(reverse=True)
                        highest_value, last_option = valid_options[0]
                        
                        # Extraction du nombre total de pages (format "530 / 530")
                        page_text = last_option.text.strip()
                        logger.info(f"Texte de la dernière option: '{page_text}'" )
                        
                        # Essayer différents formats de pagination
                        total_match = re.search(r'(\d+)\s*/\s*(\d+)', page_text)
                        if total_match:
                            total_pages = int(total_match.group(2))
                            logger.info(f"Format de pagination 'X / Y' détecté: {total_pages} pages")
                        else:
                            # Si le format est différent, essayer de récupérer juste le nombre
                            total_match = re.search(r'(\d+)', page_text)
                            if total_match:
                                total_pages = int(total_match.group(1))
                                logger.info(f"Format de pagination simple détecté: {total_pages} pages")
                            else:
                                # Utiliser la valeur numérique la plus élevée des options
                                total_pages = highest_value
                                logger.info(f"Format de pagination non reconnu, utilisation de la valeur d'option la plus élevée: {total_pages} pages")
            
            logger.info(f"Nombre total de pages détecté: {total_pages}")
            
            # Limitation du nombre de pages à parcourir pour éviter les temps d'exécution trop longs
            if max_pages_limit is None:
                # Valeur par défaut si non spécifiée
                default_limit = 10
                max_pages = min(total_pages, default_limit)
                logger.info(f"Limitation par défaut à {max_pages} pages sur {total_pages} disponibles")
            elif max_pages_limit == 0:
                # Aucune limite, parcourir toutes les pages
                max_pages = total_pages
                logger.info(f"Aucune limitation: parcours des {total_pages} pages disponibles")
            else:
                # Limitation spécifiée par l'utilisateur
                max_pages = min(total_pages, max_pages_limit)
                logger.info(f"Limitation à {max_pages} pages sur {total_pages} disponibles (limite spécifiée: {max_pages_limit})")
            
            # Parcours de toutes les pages de résultats
            for page in range(1, max_pages + 1):
                # Construction de l'URL avec les paramètres de filtre et de pagination
                url = self.MISSIONS_URL
                if freshness_filter:
                    url += f"?{freshness_filter}&page={page}"
                else:
                    url += f"?page={page}"
                
                # Ne pas refaire la requête pour la page 1 car on l'a déjà récupérée
                if page > 1:
                    logger.info(f"Récupération de la page {page}/{max_pages}: {url}")
                    response = self.session.get(url)
                    response.encoding = 'utf-8'  # Force l'encodage UTF-8
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                
                # Recherche des liens de missions sur cette page
                page_mission_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if '/job-mission/' in href:
                        full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                        page_mission_links.append(full_url)
                
                # Si aucun lien trouvé sur cette page, on arrête la pagination
                if not page_mission_links:
                    logger.info(f"Aucune mission trouvée sur la page {page}, fin de la pagination")
                    break
                else:
                    logger.info(f"Trouvé {len(page_mission_links)} liens de missions sur la page {page}/{max_pages}")
                    all_mission_links.extend(page_mission_links)
            
            # Dédupliquer les liens
            all_mission_links = list(set(all_mission_links))
            logger.info(f"Nombre total de liens uniques de missions trouvés: {len(all_mission_links)}")
            
            recent_missions = []
            
            # Parcours des liens de missions pour extraire les détails
            for mission_url in all_mission_links:
                logger.info(f"Traitement de la mission: {mission_url}")
                
                # Extraction des détails de la mission
                mission_details = self._extract_mission_details(mission_url)
                
                # Ajout de la mission à la liste
                recent_missions.append(mission_details)
                logger.info(f"Mission ajoutée: {mission_details['titre']} {mission_details['localisation']}")
            
            logger.info(f"Nombre total de missions récentes trouvées: {len(recent_missions)}")
            return recent_missions
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des missions récentes: {e}")
            return []

if __name__ == "__main__":
    # Test du scraper
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper pour Free-Work.com')
    parser.add_argument('--days', type=int, default=7, 
                        help='Fraîcheur des missions (1, 7, 14, 30 jours, autre=sans filtre)')
    parser.add_argument('--max-pages', type=int, default=None, 
                        help='Nombre maximum de pages à parcourir (0=toutes les pages)')
    args = parser.parse_args()
    
    scraper = FreeWorkScraper()
    missions = scraper.get_recent_missions(days=args.days, max_pages_limit=args.max_pages)
    
    print(f"Nombre total de missions récupérées: {len(missions)}")
    print(json.dumps(missions, indent=2, ensure_ascii=False))
