#!/bin/bash

# Script pour exécuter le batch Free-Work
# Ce script est destiné à être exécuté par cron

# Chemin absolu vers le répertoire du projet
PROJECT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$PROJECT_DIR" || exit 1

# Configuration de l'environnement
# Décommentez et configurez si nécessaire
# export OPENAI_API_KEY="votre_clé_api"

# Paramètres par défaut
DAYS=1  # Récupérer les missions des 30 derniers jours
MAX_PAGES=5  # 0 = toutes les pages

# Exécution du batch avec logging
echo "===== Démarrage du batch Free-Work $(date) =====" >> "$PROJECT_DIR/cron_batch.log"
python batch.py $DAYS $MAX_PAGES >> "$PROJECT_DIR/cron_batch.log" 2>&1
EXIT_CODE=$?

# Logging du résultat
if [ $EXIT_CODE -eq 0 ]; then
    echo "===== Batch terminé avec succès $(date) =====" >> "$PROJECT_DIR/cron_batch.log"
else
    echo "===== Batch terminé avec erreur (code: $EXIT_CODE) $(date) =====" >> "$PROJECT_DIR/cron_batch.log"
fi

exit $EXIT_CODE
