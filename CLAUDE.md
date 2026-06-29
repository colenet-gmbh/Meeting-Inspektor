# Meeting-Inspektor

Reines Browser-Tool (HTML Onepager) zur Analyse von Meeting-Strukturen 
in Organisationen. Keine Server, kein Build-Prozess, vollständig offline-fähig.

## Projektdateien
- `meeting-inspektor.html` – die einzige relevante Quelldatei
- `testdaten.tsv` – synthetische Testdaten (darf im Repo liegen)
- `README.md` – öffentliche Dokumentation
- `CLAUDE_CONTEXT.md` – vollständiger technischer Kontext (PFLICHT: vor 
  jeder Session vollständig lesen)

## Wichtigste Regeln (Details in CLAUDE_CONTEXT.md)
- Vor jeder Implementierung: User-Story-Skill ausführen
- Kein Direkt-Commit auf `main`
- Keine Echtdaten im Repository
- Quellenbezeichnung immer „Urliste" – nie „Confluence" o.ä.
- Safari-Kompatibilität: kein nested Template-Literal

## Stack
HTML · Vanilla JavaScript · Plotly · D3
