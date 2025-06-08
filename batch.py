#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Batch journalier pour récupérer les missions de Free-Work.com et les stocker dans une base Qdrant
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# Import des outils Free-Work
from tools.freework_tools import query_freework_missions

# Import pour Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Import pour les embeddings OpenAI
import openai

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_freework.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('batch_freework')

def get_openai_embedding(text: str) -> List[float]:
    """
    Génère un embedding pour le texte donné en utilisant le modèle OpenAI
    
    Args:
        text (str): Texte à encoder
        
    Returns:
        List[float]: Vecteur d'embedding
    """
    try:
        # Récupération de la clé API depuis l'environnement
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("La clé API OpenAI n'est pas définie dans l'environnement (OPENAI_API_KEY)")
            sys.exit(1)
            
        # Configuration du client OpenAI
        openai.api_key = api_key
        
        # Génération de l'embedding
        response = openai.embeddings.create(
            model="text-embedding-3-large",
            input=text,
            encoding_format="float"
        )
        
        # Extraction du vecteur d'embedding
        embedding = response.data[0].embedding
        
        return embedding
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'embedding: {e}")
        return []

def init_qdrant_collection(client: QdrantClient, collection_name: str) -> bool:
    """
    Initialise la collection Qdrant si elle n'existe pas
    
    Args:
        client (QdrantClient): Client Qdrant
        collection_name (str): Nom de la collection
        
    Returns:
        bool: True si la collection a été créée ou existe déjà, False sinon
    """
    try:
        # Vérification si la collection existe déjà
        collections = client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name in collection_names:
            logger.info(f"La collection '{collection_name}' existe déjà")
            return True
            
        # Création de la collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=3072,  # Taille du vecteur pour text-embedding-3-large
                distance=Distance.COSINE
            )
        )
        
        logger.info(f"Collection '{collection_name}' créée avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la collection: {e}")
        return False

def store_missions_in_qdrant(missions: List[Dict[str, Any]], collection_name: str) -> bool:
    """
    Stocke les missions dans la base Qdrant
    
    Args:
        missions (List[Dict[str, Any]]): Liste des missions à stocker
        collection_name (str): Nom de la collection Qdrant
        
    Returns:
        bool: True si les missions ont été stockées avec succès, False sinon
    """
    try:
        # Initialisation du client Qdrant
        client = QdrantClient(host="localhost", port=6333)
        
        # Initialisation de la collection
        if not init_qdrant_collection(client, collection_name):
            return False
            
        # Préparation des points à insérer
        points = []
        
        for i, mission in enumerate(missions):
            # Conversion de la mission en JSON pour le stockage
            mission_json = json.dumps(mission, ensure_ascii=False)
            
            # Génération de l'embedding pour la mission
            embedding = get_openai_embedding(mission_json)
            
            if not embedding:
                logger.warning(f"Impossible de générer un embedding pour la mission {mission['numero_mission']}")
                continue
                
            # Création du point
            point = PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "mission_id": mission["numero_mission"],
                    "titre": mission["titre"],
                    "entreprise": mission["entreprise"],
                    "localisation": mission["localisation"],
                    "tjm": mission["tjm"],
                    "date": mission["date"],
                    "url": mission["url"],
                    "page_content": mission_json
                }
            )
            
            points.append(point)
            
        # Insertion des points dans la collection
        if points:
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"{len(points)} missions stockées dans la collection '{collection_name}'")
            return True
        else:
            logger.warning("Aucune mission à stocker")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors du stockage des missions dans Qdrant: {e}")
        return False

def main():
    """
    Fonction principale du batch
    """
    try:
        # Récupération du nombre de jours depuis les arguments
        days = 7  # Valeur par défaut
        
        if len(sys.argv) > 1:
            try:
                days = int(sys.argv[1])
                # Limitation à 30 jours maximum
                if days > 30:
                    logger.warning("Le nombre de jours est limité à 30")
                    days = 30
                elif days < 1:
                    logger.warning("Le nombre de jours doit être au moins 1")
                    days = 1
            except ValueError:
                logger.error("Le nombre de jours doit être un entier")
                sys.exit(1)
                
        logger.info(f"Récupération des missions des {days} derniers jours")
        
        # Récupération des missions récentes
        missions = query_freework_missions(days=days)
        
        if not missions:
            logger.warning("Aucune mission récente trouvée")
            sys.exit(0)
            
        logger.info(f"{len(missions)} missions récentes trouvées")
        
        # Stockage des missions dans Qdrant
        collection_name = "missions-freework"
        if store_missions_in_qdrant(missions, collection_name):
            logger.info("Batch exécuté avec succès")
        else:
            logger.error("Erreur lors de l'exécution du batch")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du batch: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
