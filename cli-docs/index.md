# viur-cli

Command-line interface für ViUR-Projekt-Maintenance.

`viur-cli` orchestriert alle wiederkehrenden Aufgaben rund um ein ViUR-Projekt aus einer zentralen CLI: lokales Starten, Bauen, Deployen auf Google Cloud, Abhängigkeits-Updates, Frontend-Bundle-Installation und mehr.

## Installation

```bash
uv add --dev viur-cli
```

Voraussetzungen: Python ≥ 3.11, [uv](https://docs.astral.sh/uv/) ≥ 0.9.15.

!!! note "Migration von v2"
    Wer von v2 kommt: das `project.json`-Format ist unverändert. Pipenv-Projekte müssen zuerst auf uv migrieren. Details siehe Migration-Sektion.

## Schnellstart

```bash
# Neues Projekt anlegen
viur create mein-projekt
cd mein-projekt

# Lokal starten
viur run

# Admin-Frontend installieren
viur admin install

# Auf Google Cloud deployen
viur cloud deploy app
```

Vollständige Befehlsreferenz: [Befehle](commands/index.md).

## Hauptfeatures

- **Project-Lifecycle** — `viur create`, `viur run`, `viur build`, `viur cloud deploy`
- **Frontend-Bundle-Management** — `viur admin/vi/scriptor install` für die ViUR-Frontends
- **Security-Audit** — `viur check` führt `pip-audit` (Python) und `npm audit` (npm-Builds) parallel aus
- **Cloud-Funktionen** — Deploy, IAM-Setup, Backup-Bucket-Management
- **Skripting** — `viur script` für Pull/Push/Run von ViUR-Scriptor-Skripten
