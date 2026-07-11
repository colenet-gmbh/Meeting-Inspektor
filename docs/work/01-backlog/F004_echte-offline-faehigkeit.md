# F004 – Echte Offline-Fähigkeit (Plotly/D3 einbetten)

**Status:** Backlog
**Quelle:** ADR-Review 10.07.2026 – Widerspruch zwischen Doku und Code entdeckt

## Worum es geht

README und CLAUDE.md versprechen „vollständig offline-fähig", aber Plotly und D3 werden
per CDN geladen (`meeting-inspektor.html:9-10`). Beim ersten Öffnen ohne Internet bleiben
alle Diagramme leer. ADR 0001 benennt die Einschränkung; dieses Item stellt echte
Offline-Fähigkeit her.

## Leitplanken

- ADR 0001 (eine Datei, kein Build) bleibt gültig: Bibliotheken werden in die HTML-Datei
  eingebettet, keine Zusatzdateien.
- Dateigröße wächst um mehrere MB (Plotly ~3,5 MB + D3 ~0,3 MB minifiziert) – Auswirkung
  auf Download und Editor-Handhabung vorher prüfen; ggf. schlankeres Plotly-Bundle
  (plotly.js-basic o.ä.) evaluieren, das alle genutzten Chart-Typen abdeckt.
- Versions-Pinning bleibt erhalten (aktuell Plotly 2.35.2, D3 v7).

## Akzeptanzkriterien

- [ ] Frisch heruntergeladene Datei rendert alle Tabs ohne Internetverbindung
- [ ] Keine externen Requests mehr beim Laden
- [ ] „Offline-fähig"-Aussage in README/CLAUDE.md stimmt wieder; ADR 0001 aktualisiert
