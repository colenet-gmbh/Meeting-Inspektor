# F002 – Neue Abteilungen frei benennen

**Status:** Backlog
**Quelle:** Kundenwunsch (vor 10.07.2026, aus CLAUDE_CONTEXT.md übernommen)

## Worum es geht

Personen sollen einer Abteilung zugeordnet werden können, die in der Urliste nicht
vorkommt. Aktueller Behelfsweg ist die Sammelkategorie „Zuarbeitend" (siehe Glossar);
gewünscht sind frei benennbare neue Abteilungen in der Personen-Zuordnung.

## Leitplanken

- ADR 0003: Abteilungszuordnung ist Konfiguration (interpretiert Daten, verändert sie
  nicht) – das Feature ist damit vereinbar.
- Neue Abteilungen leben im `localStorage`/Config-Export wie die übrige Zuordnung.

## Akzeptanzkriterien

- [ ] Im Konfiguration-Tab lässt sich eine neue Abteilung mit freiem Namen anlegen
- [ ] Personen können dieser Abteilung zugeordnet werden
- [ ] Die Abteilung erscheint in allen Analysen wie eine Urliste-Abteilung
- [ ] Config-Export/Import erhält die neuen Abteilungen
