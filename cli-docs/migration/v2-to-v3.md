# Migration v2 → v3

v3 ist ein **uv-only Release** mit Säuberung von Junior-Code-Mustern und kritischen Security-Fixes. Das `project.json`-Format ist unverändert — bestehende ViUR-Projekte laufen ohne Anpassung mit v3.

## TL;DR

| Was | Aktion |
|---|---|
| `project.json` | nichts zu tun, gleiches Format |
| Pipfile / pipenv | einmalig auf uv migrieren (siehe unten) |
| `viur package install <X>` | weiter funktional, aber **deprecated bis v3.2** — auf `viur <X> install` umstellen |
| Sonstige Befehle (`viur run/build/cloud/env/check`) | unverändert |

## Voraussetzung — uv installieren

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# oder
pip install uv
```

Mindestversion: `0.9.15` (wird vom CLI beim Start geprüft, wenn deine Version niedriger ist erscheint eine Warnung).

## Pipenv → uv für bestehende Projekte

Wenn dein Projekt noch `Pipfile` / `Pipfile.lock` benutzt:

```bash
# 1. Pipfile in pyproject.toml umwandeln (manuell oder mit pipenv-to-uv)
# Inhalt von Pipfile [packages] und [dev-packages] in pyproject.toml's
# [project.dependencies] und [dependency-groups.dev] übertragen.

# 2. Lockfile mit uv erzeugen
uv lock

# 3. Venv anlegen + dependencies installieren
uv sync

# 4. Pipfile + Pipfile.lock entfernen
rm Pipfile Pipfile.lock
```

`viur-cli` selbst wird als Dev-Dependency installiert:

```bash
uv add --dev viur-cli
```

## Befehlsumstellung

Die alten `viur package install <kind>` / `viur package update <kind>` Aufrufe bleiben in v3 funktional, drucken aber eine Deprecation-Warnung auf stderr. **In v3.2 werden sie entfernt.**

| Alt | Neu |
|---|---|
| `viur package install admin` | `viur admin install` |
| `viur package install admin 4.0.8` | `viur admin install 4.0.8` |
| `viur package update admin` | `viur admin update` |
| `viur package install vi` | `viur vi install` |
| `viur package install scriptor` | `viur scriptor install` |
| `viur package install all` | `viur admin install && viur scriptor install` |

In Skripten / `mise.toml`-Tasks / CI-Pipelines die alten Aufrufe finden und ersetzen reicht.

## Security-Hinweise (was sich intern geändert hat)

v3 hat alle `os.system`- und `shell=True`-Aufrufe mit User-Input durch saubere argv-Listen ersetzt. **Für End-User unsichtbar**, aber relevant für CI-Sicherheit:

- Bucket-Namen / Projekt-IDs / Profile-Namen die in deinem `project.json` oder via `click.prompt` reinkommen werden nicht mehr durch eine Shell interpretiert. Deploy-Pfade sind robust gegen Sonderzeichen.
- `viur run` benutzt für die gcloud-Auth-Abfrage jetzt die `requests`-Library statt einer Shell-`curl`-Pipe.
- `viur check` wechselte vom (intern instabilen) `pysentry-rs` auf das von der PyPA gepflegte `pip-audit` (mit OSV-Datenbank).

Wenn du in CI bisher `--skip_checks` gesetzt hattest weil der alte `pysentry`-Wrapper bei jedem Vuln gecrasht ist: das kannst du jetzt entfernen, der Check funktioniert.

## Warum ein Major-Release

- **uv only** — Pipfile-Support ist weg. Wer noch nicht migriert ist muss das tun.
- **Veraltete Cloud-Function-Deploy-Syntax** wurde stillschweigend gefixt. Wenn dein `project.json` Cloud-Functions definiert: nochmal mit `viur cloud deploy cloudfunction` testen, das gcloud-Argument-Format wurde leicht angepasst (z.B. `--region=...` statt `--region='...'`).
- **Eintry-Point in `pyproject.toml`** ist intern auf `viur_cli.cli:main` gewechselt. Wer den Entry-Point nicht selbst patcht: nichts zu tun.

## Wenn du auf v2 bleiben willst

```bash
uv add --dev "viur-cli<3"
```

v2.x bleibt auf PyPI installierbar. Aktive Wartung gibt es nicht mehr (nur kritische Security-Patches nach Maintainer-Ermessen).

## Hilfe

Wenn ein Befehl nach der Umstellung anders reagiert als erwartet — vergleich den `--help`-Output zwischen v2 und v3:

```bash
uvx --from "viur-cli<3" viur <befehl> --help   # v2-Verhalten
uvx --from viur-cli viur <befehl> --help       # v3-Verhalten
```

Bug-Reports und Migrations-Probleme: <https://github.com/viur-framework/viur-cli/issues>.
