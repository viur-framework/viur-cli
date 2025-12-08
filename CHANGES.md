# Changelog

## Unreleased

### Änderungen
- Pipenv entfernt und durch uv ersetzt
- Projekt umstrukturiert und alle pipenv-Befehle durch uv-Äquivalente ersetzt

### Offene Fragen
- **Update-Befehl**: Wieso existiert `viur update requirements`? Was ist noch möglich bei update?
- **Tool requirement**: Warum existiert bei tool nur der Befehl `requirement`? Funktioniert nicht - vermutlich war es nie funktionsfähig
- **Run-Befehl**: Seit dem Umstieg auf uv gibt es "invalid escape character" Fehler (kein Pipfile mehr vorhanden)
- **Installation**:
  - Aktuell Copy-Paste von ZIP-Dateien für Scriptor und Admin
  - Scriptor API sollte als Dependency installiert werden
  - Admin könnte per npm installiert werden (weniger kritisch als Scriptor)
- **Security check**:
  - fix anbieten? wenn ja muss ja erst uv sync --dev vorher wieder gemacht werden wegen --no-pip und --no-deps flag bei pip-audit
  - was kann ich statt pip-audit nutzen
  - --dev überhaupt notwendig? sollte std sein wegen !security!
### TODO
- [ ] `viur run` Escape-Character-Fehler beheben
- [ ] ZIP Copy-Paste Installation durch proper Dependency Management ersetzen
- [ ] Scriptor API als Package-Dependency integrieren
- [ ] npm-Installation für Admin evaluieren
