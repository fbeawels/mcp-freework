# TODO pour la création de l'outil MCP Free-Work

## Structure du projet
- [x] Analyser la structure du projet exemple pour koino.fr
- [x] Créer la structure de base pour free-work.com

## Fichiers de configuration
- [x] Créer le fichier README.md
- [x] Créer le fichier pyproject.toml
- [x] Créer le fichier main.py
- [x] Créer le fichier server.py
- [x] Créer le script start_mcp_server.sh

## Implémentation du scraper
- [x] Créer le répertoire src/
- [x] Créer le fichier src/__init__.py
- [x] Créer le fichier src/freework_scraper.py avec la classe FreeWorkScraper
- [x] Implémenter la méthode pour récupérer les missions récentes
- [x] Implémenter la méthode pour extraire les détails d'une mission

## Implémentation des outils MCP
- [x] Créer le répertoire tools/
- [x] Créer le fichier tools/__init__.py
- [x] Créer le fichier tools/freework_tools.py
- [x] Implémenter l'outil query_freework_missions
- [x] Implémenter l'outil get_mission_details

## Implémentation du batch journalier
- [x] Créer le fichier batch.py à la racine du projet
- [x] Implémenter la récupération des missions récentes via l'outil existant
- [x] Implémenter la génération d'embeddings avec OpenAI
- [x] Implémenter le stockage des missions dans Qdrant
- [x] Gérer les paramètres en ligne de commande pour le nombre de jours
- [x] Ajouter la gestion des erreurs et le logging

## Tests
- [x] Tester le scraper
- [x] Tester les outils MCP
- [x] Vérifier la compatibilité du format JSON avec l'exemple koino.fr
- [ ] Tester le batch journalier avec différents paramètres
- [ ] Vérifier la création et le remplissage de la collection Qdrant

## Validation finale
- [x] Corriger les erreurs de syntaxe et d'indentation dans le scraper
- [x] Améliorer l'extraction du TJM dans le scraper
- [x] Optimiser la structure de l'outil query_freework_missions
- [x] Mettre à jour la documentation dans README.md
- [ ] Documenter l'utilisation du batch journalier dans le README.md
