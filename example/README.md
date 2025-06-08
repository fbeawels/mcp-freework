# Serveur MCP Koino

Ce serveur MCP (Model Context Protocol) permet d'accéder aux fonctionnalités de scraping de Koino.fr via une interface compatible avec Claude et d'autres assistants IA.

## Fonctionnalités

Le serveur MCP Koino expose les outils suivants :

- `query_koino_missions` : Récupère les missions publiées sur Koino.fr depuis moins de X jours
- `get_mission_details` : Récupère les détails d'une mission spécifique à partir de son URL

## Installation

1. Assurez-vous d'avoir Python 3.8+ installé
2. Installez les dépendances :

```bash
pip install -e .
```

## Utilisation

### Démarrer le serveur

```bash
python main.py
```

### Configuration avec Claude pour Desktop

1. Ouvrez le fichier de configuration de Claude :
   - MacOS/Linux : `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows : `%APPDATA%\Claude\claude_desktop_config.json`

2. Ajoutez la configuration suivante (remplacez "/CHEMIN/ABSOLU/VERS" par le chemin absolu vers le répertoire mcp-koino) :

```json
{
  "mcpServers": {
    "koino-mcp": {
      "command": "python",
      "args": [
        "/CHEMIN/ABSOLU/VERS/koino/mcp-koino/main.py"
      ]
    }
  }
}
```

3. Redémarrez Claude pour Desktop

## Exemples d'utilisation

Une fois le serveur configuré avec Claude, vous pouvez poser des questions comme :

- "Quelles sont les missions publiées sur Koino.fr ces 10 derniers jours ?"
- "Peux-tu me donner les détails de cette mission : https://www.koino.fr/mission/123456 ?"

## Développement

Pour ajouter de nouveaux outils, créez de nouvelles fonctions dans le répertoire `tools/` et décorez-les avec `@mcp.tool()`.
