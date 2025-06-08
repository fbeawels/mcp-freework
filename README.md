# Serveur MCP Free-Work

Ce serveur MCP (Model Context Protocol) permet d'accéder aux fonctionnalités de scraping de Free-Work.com via une interface compatible avec Claude et d'autres assistants IA. Il suit la même structure et le même format JSON que l'outil MCP Koino existant.

## Fonctionnalités

Le serveur MCP Free-Work expose les outils suivants :

- `query_freework_missions(days: int = 7)` : Récupère les missions publiées sur Free-Work.com depuis moins de X jours (par défaut 7 jours)
- `get_mission_details(mission_url: str)` : Récupère les détails d'une mission spécifique à partir de son URL

De plus, un batch journalier est disponible pour récupérer les missions et les stocker dans une base Qdrant pour des recherches sémantiques ultérieures.

## Structure des données

### Format des missions retournées par `query_freework_missions`

Chaque mission est représentée par un dictionnaire avec les champs suivants :

```json
{
  "titre": "Titre de la mission",
  "tjm": "Tarif journalier moyen ou salaire",
  "localisation": "Ville (Code postal)",
  "departement": "Code postal",
  "date": "JJ/MM/AAAA",
  "numero_mission": "FW-XXXXX",
  "entreprise": "Nom de l'entreprise",
  "profil": "Description du profil recherché",
  "url": "URL de la mission sur Free-Work.com"
}
```

### Format des détails retournés par `get_mission_details`

```json
{
  "status": "success",
  "mission": {
    "titre": "Titre de la mission",
    "tjm": "Tarif journalier moyen ou salaire",
    "localisation": "Ville (Code postal)",
    "departement": "Code postal",
    "date": "JJ/MM/AAAA",
    "numero_mission": "FW-XXXXX",
    "entreprise": "Nom de l'entreprise",
    "profil": "Description du profil recherché",
    "url": "URL de la mission sur Free-Work.com"
  }
}
```

## Installation

1. Assurez-vous d'avoir Python 3.8+ installé
2. Installez les dépendances :

```bash
pip install requests beautifulsoup4 python-dateutil mcp-python-core
```

## Utilisation

### Démarrer le serveur

```bash
python main.py
```

Le serveur démarrera et sera accessible via le protocole MCP.

### Configuration avec Claude pour Desktop

1. Ouvrez le fichier de configuration de Claude :
   - MacOS/Linux : `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows : `%APPDATA%\Claude\claude_desktop_config.json`

2. Ajoutez la configuration suivante (remplacez "/CHEMIN/ABSOLU/VERS" par le chemin absolu vers le répertoire mcp-freework) :

```json
{
  "mcpServers": {
    "freework-mcp": {
      "command": "python",
      "args": [
        "/CHEMIN/ABSOLU/VERS/mcp-freework/main.py"
      ]
    }
  }
}
```

3. Redémarrez Claude pour Desktop

### Exemples d'utilisation avec Claude

#### Récupérer les missions récentes

```
Utilise l'outil MCP query_freework_missions pour me montrer les missions publiées ces 5 derniers jours.
```

#### Récupérer les détails d'une mission spécifique

```
Utilise l'outil MCP get_mission_details pour me montrer les détails de cette mission : https://www.free-work.com/fr/tech-it/ingenieur-apres-vente/job-mission/ingenieur-operations-h-f-2
```

## Architecture

Le projet est organisé comme suit :

- `main.py` : Point d'entrée principal pour démarrer le serveur MCP
- `server.py` : Définition de l'instance FastMCP
- `tools/freework_tools.py` : Implémentation des outils MCP
- `src/freework_scraper.py` : Implémentation du scraper pour Free-Work.com

## Débogage

Le scraper sauvegarde les pages HTML dans `/tmp/` pour faciliter le débogage :
- Liste des missions : `/tmp/freework_debug.html`
- Détails d'une mission : `/tmp/freework_mission_XXXXX.html`

## Exemples d'utilisation

Une fois le serveur configuré avec Claude, vous pouvez poser des questions comme :

- "Quelles sont les missions publiées sur Free-Work.com ces 10 derniers jours ?"
- "Peux-tu me donner les détails de cette mission : https://www.free-work.com/fr/tech-it/jobs/12345 ?"

## Batch journalier

Un batch journalier est disponible pour récupérer automatiquement les missions et les stocker dans une base Qdrant. Cette fonctionnalité permet d'effectuer des recherches sémantiques sur les missions récupérées.

### Prérequis

1. Une base Qdrant accessible sur http://localhost:6333
2. Une clé API OpenAI configurée dans l'environnement (variable OPENAI_API_KEY)
3. Les dépendances supplémentaires :

```bash
pip install qdrant-client openai
```

### Utilisation

```bash
python batch.py <nombre_de_jours>
```

Où `<nombre_de_jours>` est le nombre de jours à couvrir (maximum 30 jours). Si non spécifié, la valeur par défaut est de 7 jours.

Exemples :

```bash
# Récupérer les missions des 7 derniers jours (par défaut)
python batch.py

# Récupérer les missions des 14 derniers jours
python batch.py 14

# Récupérer les missions des 30 derniers jours (maximum)
python batch.py 30
```

### Fonctionnement

Le batch effectue les opérations suivantes :

1. Récupération des missions récentes via l'outil `query_freework_missions`
2. Génération d'embeddings pour chaque mission en utilisant le modèle OpenAI `text-embedding-3-large`
3. Création d'une collection Qdrant nommée `missions-freework` si elle n'existe pas déjà
4. Stockage des missions dans la collection Qdrant avec leurs embeddings

### Structure des données dans Qdrant

Chaque mission est stockée dans Qdrant avec les champs suivants :

- `mission_id` : Identifiant unique de la mission
- `titre` : Titre de la mission
- `entreprise` : Nom de l'entreprise
- `localisation` : Localisation de la mission
- `tjm` : Tarif journalier moyen ou salaire
- `date` : Date de publication
- `url` : URL de la mission sur Free-Work.com
- `page_content` : Mission complète au format JSON

### Logs

Les logs du batch sont disponibles dans le fichier `batch_freework.log` à la racine du projet.

## Développement

Pour ajouter de nouveaux outils, créez de nouvelles fonctions dans le répertoire `tools/` et décorez-les avec `@mcp.tool()`.
