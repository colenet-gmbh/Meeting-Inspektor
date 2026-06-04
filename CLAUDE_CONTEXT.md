# CLAUDE_CONTEXT – Meeting-Strukturanalyse Standalone

> Lese diese Datei am Anfang jeder neuen Session vollständig.  
> Sie ist lokal (gitignored) und enthält den vollständigen Projektkkontext.

---

## Projekt-Überblick

**Einzige relevante Datei:** `meeting_strukturanalyse_standalone.html`  
Lokaler Pfad: `/Users/leivbraun/Documents/Claude Code/Organisations-Meeting-Informationsfluss/`  
GitHub: https://github.com/braunle77/Organisations-Meeting-Informationsfluss  
Confluence: https://colenet.atlassian.net/wiki/spaces/KI/pages/2500427777

Reines Browser-Tool: Nutzer öffnet HTML → Paste aus Confluence oder CSV → fertig.  
Kein Python, kein Server, kein Setup. Vollständig offline-fähig.

**Aktueller Stand:** `APP_VERSION = "04.06.2026 23:30"` (~3930 Zeilen)

---

## Datenschutz (fest, nie ändern)

- `LeitMet.csv`, `meetingstruk.csv` bleiben lokal, **nie** ins Repository
- **Keine Echtdaten in Commits**
- Keine Quelldaten hardcoden – alle Algorithmen sind datenagnostisch

---

## Grundprinzip: Single Source of Truth

- Daten kommen **ausschließlich** aus der Confluence-Quelltabelle
- Das Tool **leitet ab** und **visualisiert** – es pflegt keine Daten
- Konfiguration (Personenzuordnungen, Abteilungstypen, FL-Korrekturen) im Konfiguration-Tab
- `Alle Meetings` ist **read-only** – kein Editing im Tool

---

## Datenmodell – 15+ Felder im Meeting-Objekt

| JS-Key | Confluence-Spalte | Typ | Notizen |
|---|---|---|---|
| `abteilung` | Abteilung | String | |
| `name` | Meetingname | String | |
| `kategorie` | Kategorie | String | |
| `zweck` | Zweck | Freitext | |
| `verantwortlich` | Verantwortlich | Kürzel (via canonAbbr) | |
| `teilnehmer` | Personen | Komma-sep. Kürzel | Split auf `,;\n\r` |
| `rhythmus_klasse` | Rhythmus | normalisiert auf 7 Klassen | |
| `wochentage` | (aus Rhythmus) | Array z.B. `["Mo","Do"]` | |
| `dauer` | Dauer | Minuten (Integer, null=leer) | optional |
| `infofluss` | Informationsfluss | Freitext | |
| `wert` | Wirkung (1–4) | Integer 1–4 (null=leer) | **read-only** – aus Confluence |
| `flugebene` | Flugebene (optional) | "FL1"/"FL2"/"FL3"/null | auto-suggested + via deptFunktionen |
| `flugebeneAuto` | (berechnet) | Boolean | true = auto-klassifiziert |
| `status` | Status | "Aktiv" / "Geplant" | |
| `abteilungsuebergreifend` | Abteilungsübergreifend | Boolean | berechnet aus effectivePersonAbt |
| `ist_platzhalter` | Platzhalter | Boolean | |
| `learning` | Learnings | Freitext | |
| `gruppenTeilnehmer` | (berechnet) | Array | Platzhalter-Teilnehmer erkannt |
| `hatGruppenTeilnehmer` | (berechnet) | Boolean | |

---

## Script-Block-Struktur (3 Blöcke für Safari-Kompatibilität)

Safari bricht bei Syntax-Fehlern in einem `<script>`-Block den gesamten Block ab.  
Daher ist der Code in 3 unabhängige Blöcke aufgeteilt:

| Block | Inhalt | Kritisch |
|---|---|---|
| **Block 1** | Haupt-Script: alle Kern-Funktionen (loadFromFile, parseData, showDashboard, renderTable, showTab, alle Analyse-Render-Funktionen bis auf Datenpflege) | Ja – Import + Dashboard |
| **Block 2** | Datenpflege-Funktionen (DEPT_TYP_OPTS, renderDatapflege, renderDeptTypenGrid, setDeptTyp, renderQualitaetsCockpit, renderGruppenTeilnehmerSection, saveGruppenAufloesung, exportConfig, importConfigFile) | Nein – nur Konfiguration-Tab |
| **Block 3** | renderFlightLevels + refreshAllCharts + localStorage + DOMContentLoaded | Ja – Charts |

**Wichtig für Debugging:** Nested Template-Literals (`` `${x.map(y => `...`)}` ``) sind in Safari verboten!  
Immer String-Konkatenation oder vorab berechnete Variablen verwenden.

---

## Tab-Struktur (13 Tabs, data-tab 0–12)

Navigation in zwei Gruppen: **Analyse** (Tabs 1–11) | **Datenpflege** (Tabs 0, 9, 12).

| data-tab | Tab | Panel-ID | Render-Funktion | Besonderheit |
|---|---|---|---|---|
| 0 | Personen | panel-7 | `renderPersonenTab()` | Erster Tab nach Import |
| 1 | Netzwerk | panel-0 | `renderNetzwerk()` | d3-force + Plotly |
| 2 | Abteilungen | panel-3 | `renderAbteilung()` | Horizontal + Toggle Anzahl/Freq. |
| 3 | Kalender | panel-1 | `renderKalender()` | Wochentag-basiert |
| 4 | Kommunikation | panel-4 | `renderSankey()` | Sankey immer sichtbar; Chord einklappbar via `toggleChordDiagram()` |
| 5 | Überschneidungen | panel-2 | `renderOverlap()` | Top-10 in 2-Spalten; Heatmap einklappbar via `toggleOverlapHeatmap()` |
| 6 | Engpass | panel-8 | `renderEngpass()` + `renderZeitlast()` | Top-10 + Aufklappen; FK-Filter Toggle |
| 7 | Zeitverteilung | panel-9 | `renderTreemap()` | Executive Briefing oben |
| 8 | Wirkung | panel-10 | `renderWirkungsMatrix()` | Y-Jitter + Quadrant-Farben + Executive Briefing |
| 9 | Alle Meetings | panel-5 | `renderTable()` | **Read-only** – Suche/Filter; kompakte Summary-Zeile oben |
| 10 | Flight Levels | panel-fl | `renderFlightLevels()` | 5 Diagnose-Visualisierungen (F1–F5) + Executive Briefing |
| 11 | KI Analyse | panel-6 | statisch | Placeholder |
| 12 | Konfiguration | panel-dp | `renderDatapflege()` | **[ADMIN]** Abteilungstypen · Datenqualität · Gruppen · Config Export/Import |

**Tab-Bar:** Zwei Gruppen – „Analyse" (Tabs 1–11) und „Datenpflege" (Tabs 0, 9, 12).  
**Lazy-Rendering:** `renderedTabs` Set. `showDashboard()` ruft `showTab(0)` (Personen) auf.

---

## Executive Briefings (Pattern)

Folgende Tabs haben ein Executive Briefing (dynamisch berechnet, kein Hardcoding):

| Tab | Funktion | Inhalt |
|---|---|---|
| Kommunikation | `_renderKommunikationBriefing()` | Zentrum, stärkste Achse, Coverage, least connected |
| Zeitverteilung | `_renderTreemapBriefing()` | Top-5 teuerste Meetings + FK-Flag |
| Wirkung | `_renderWirkungsBriefing()` | Optimieren-Meetings + Hinterfragen-Liste |
| Flight Levels | `_renderFLBriefing()` | Pyramidenstatus, FL2-Lücken, Brückenköpfe, F5-Mismatches |

---

## Rhythmus-Normalisierung

7 Klassen: `täglich | wöchentlich | dreiwöchentlich | zweiwöchentlich | monatlich | quartalsweise | variabel`

```javascript
const FREQ_MONTHLY = {
  "täglich":22, "wöchentlich":4, "dreiwöchentlich":1.33,
  "zweiwöchentlich":2, "monatlich":1, "quartalsweise":0.33, "variabel":0.5
};
```

---

## Flight Levels – Konzept

**3 Ebenen:**
- FL1 (Operativ): Einzelteam, täglich/wöchentlich, Tasks/Stories
- FL2 (Koordination): Teamübergreifend, Abhängigkeitsmanagement, Epics
- FL3 (Strategisch): Portfolioebene, OKRs, Quartals-/Jahreshorizont

**Auto-Klassifikation:** `suggestFlightLevel(m)` – stärkstes Signal: `deptFunktionen[m.abteilung]` (+5 Punkte), dann `abteilungsuebergreifend`, Teilnehmerzahl, Rhythmus, Keywords.

**5 Diagnose-Fragen:**
- F1: Existiert FL2? (Kommunikationspyramide)
- F2: Wo sind Koordinations-Silos? (FL2-Verbindungsmatrix)
- F3: Wirkungsgrad nach Ebene (Box+Scatter)
- F4: Brückenköpfe (Personen auf allen 3 Ebenen)
- F5: Frequenz passend zur Ebene?

---

## Abteilungstypen (`deptFunktionen`)

5 Typen (industrie-neutral, FL-relevant):

| Typ | FL-Tendenz | Beispiele |
|---|---|---|
| `strategisch` | FL3 | Geschäftsleitung, Vorstand |
| `koordination` | FL2 | PMO, Projektmanagement |
| `operativ` | FL1 | Entwicklung, Support, Vertrieb |
| `unterstützend` | neutral | HR, Finance, Legal |
| `extern` | variabel | Partner, Kunden |

---

## localStorage-Struktur

```json
{
  "personAbt": { "Maa": "Business Unit" },
  "fkList": ["Maa", "Bsc"],
  "flugebeneOverrides": { "Business Unit||Leitungsmeeting": "FL3" },
  "deptFunktionen": { "Business Unit": "operativ", "Management": "strategisch" },
  "gruppenAufloesungen": { "Business Unit||Daily||BU-Team": ["Maa", "Bsc"] }
}
```

**Persistenz-Regeln:**
- `wertOverrides` wurde entfernt – Wirkung kommt aus Confluence, kein Tool-Override
- `personAbt`, `fkList`, `flugebeneOverrides`, `deptFunktionen`, `gruppenAufloesungen` bleiben über Imports erhalten
- Export/Import als `meeting-config.json` über Konfiguration-Tab

---

## Wichtige Konstanten und Funktionen

### Globale Zustands-Variablen (Laufzeit)
```javascript
let effectivePersonAbt = {};  // Person → Abteilung
let effectiveAbtFarben = {};  // Abteilung → Hex-Farbe
let allDepts = [];
let deptFunktionen = {};      // Abteilung → Typ ("operativ" etc.)
let fkSet = new Set(FK_LIST);
let engpassMode = "alle";     // "alle" | "fk" | "ma"
let engpassExpanded = false;
let abtMode = "anzahl";
let _overlapCache = null;     // gecachte Overlap-Matrix
let _sankeyCache = null;      // gecachte Sankey-Daten für Chord on-demand
```

### Kern-Funktionen
| Funktion | Wo | Zweck |
|---|---|---|
| `suggestFlightLevel(m)` | Block 1 | FL-Auto-Klassifikation |
| `isGruppenParticipant(name)` | Block 1 | Erkennt Gruppen-Platzhalter |
| `setEngpassMode(mode)` | Block 1 | FK-Filter Toggle Engpass |
| `toggleEngpassExpand()` | Block 1 | Top-10 / Alle toggle |
| `toggleChordDiagram()` | Block 1 | Chord on-demand |
| `toggleOverlapHeatmap()` | Block 1 | Heatmap on-demand |
| `_renderKommunikationBriefing()` | Block 1 | Kommunikation Briefing |
| `_renderTreemapBriefing()` | Block 1 | Zeitverteilung Briefing |
| `_renderWirkungsBriefing()` | Block 1 | Wirkung Briefing |
| `_renderFLBriefing()` | Block 3 | Flight Levels Briefing |
| `exportConfig()` | Block 2 | JSON-Download (data: URI, Safari-kompatibel) |
| `importConfigFile(input)` | Block 2 | JSON importieren + re-init |
| `renderDatapflege()` | Block 2 | Konfiguration-Tab rendern |
| `setDeptTyp(sel)` | Block 2 | Abteilungstyp speichern |
| `setImportMethod(m)` | Block 1 | Import-Screen Methode (bleibt für resetToImport) |

---

## Import-Screen

Zwei gleichwertige Optionen nebeneinander:
- **Aus Confluence**: Textarea + „Prüfen & Laden"-Button; shortcuts OS-neutral (Strg/⌘)
- **CSV/TSV-Datei**: Drag & Drop-Zone + „Datei auswählen"-Button

```javascript
// handleFileDrop(event, el) – Block 1
// loadFromFile(input) – Block 1 (mit reader.onerror)
// tryLoad(text) – Block 1 (mit innerem try-catch für showDashboard)
```

---

## Branch-Workflow

```
main  ←  feat/<name>  (gh pr create → squash merge)
```
- Kein Direkt-Commit auf `main` für neue Features
- **APP_VERSION-Timestamp** (`DD.MM.YYYY HH:MM`) im letzten Commit setzen
- `gh pr merge <nr> --squash --delete-branch && git checkout main && git pull`

---

## Alle PRs (alle gemergt)

| PR | Was |
|---|---|
| #1–#13 | Diverse Features + Fixes (Grundstruktur) |
| #14 | Wirkung (1–4) editierbar – **später wieder entfernt (read-only)** |
| #15 | Wirkungsmatrix (Scatter-Chart Zeit vs. Wirkung) |
| #16–#28 | Treemap, Chord, Sankey, Personen-Fixes, Logo |
| #29–#32 | Personen-Tab: adaptives Layout, Sortierung |
| #33 | Flight Levels Tab (5 Diagnose-Visualisierungen F1–F5) |
| #34 | Datenpflege-Tab, Abteilungstypen, Konfiguration Export/Import, Tab-Grouping, Import-Screen UX, UX-Verbesserungen auf 8 Tabs, Alle Meetings read-only, Stats-Bar entfernt, Safari-Bug-Fix (Script 3 Blöcke) |
| #35 | Bug: CSV-Import Safari-Fix (nested Template-Literals), Chord-Labels im Ring |

---

## Offene Punkte

### Mittel-Priorität
- **Gruppen-Teilnehmer expandieren**: Gespeicherte Auflösungen aus `gruppenAufloesungen` in den Analyse-Charts (Netzwerk, Engpass, Überschneidungen) anwenden

### Niedrig-Priorität
- **KI-Analyse Tab** mit echten Beobachtungen befüllen

### Bewusst zurückgestellt (Gruppe 4)
| Feature | Anmerkung |
|---|---|
| D2 – Reifegrad-Indikator | Spider-Chart, braucht Definition von "Reife" |
| C1/C2 – Zweck-Typisierung | Neue Confluence-Spalte + Datennacherfassung nötig |
| E1 – Längsschnitt | Eigene Architektur für mehrere Datensätze über Zeit |

---

## Gelöste Bugs (Referenz)

- ~~Safari: gesamter Script-Block lädt nicht~~ → Script in 3 Blöcke aufgeteilt
- ~~Nested Template-Literals brechen Safari-Parser~~ → Alle auf String-Konkatenation umgestellt
- ~~saveConfig JSON.parse außerhalb try-catch~~ → In try-catch verschoben
- ~~showDashboard-Fehler nach 400ms-Timeout unsichtbar~~ → Inneres try-catch
- ~~wertOverrides aus alter Session übernommen~~ → Wirkung ist jetzt read-only
- ~~Chord-Labels laufen sternförmig nach außen~~ → textPath-Labels im Ring
- ~~Überschneidungs-Heatmap dominiert den Tab~~ → Top-10-Liste + Heatmap einklappbar
