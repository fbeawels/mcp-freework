# Serveur MCP Free-Work

Ce serveur MCP (Model Context Protocol) permet d'accéder aux fonctionnalités de scraping de Free-Work.com via une interface compatible avec Claude et d'autres assistants IA. Il suit la même structure et le même format JSON que l'outil MCP Koino existant.

## Fonctionnalités

Le serveur MCP Free-Work expose les outils suivants :

- `query_freework_missions(days: int = 7)` : Récupère les missions publiées sur Free-Work.com depuis moins de X jours (par défaut 7 jours)
- `get_mission_details(mission_url: str)` : Récupère les détails d'une mission spécifique à partir de son URL

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

## Développement

Pour ajouter de nouveaux outils, créez de nouvelles fonctions dans le répertoire `tools/` et décorez-les avec `@mcp.tool()`.
