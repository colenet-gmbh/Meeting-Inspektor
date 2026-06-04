# CLAUDE_CONTEXT – Meeting-Strukturanalyse Standalone

> Lese diese Datei am Anfang jeder neuen Session vollständig.  
> Sie ist lokal (gitignored) und enthält den vollständigen Projektkkontext.

---

## Projekt-Überblick

**Einzige relevante Datei:** `meeting_strukturanalyse_standalone.html`  
Lokaler Pfad: `/Users/leivbraun/Documents/Claude Code/Organisations-Meeting-Informationsfluss/`  
GitHub: https://github.com/braunle77/Organisations-Meeting-Informationsfluss  
Confluence: https://colenet.atlassian.net/wiki/spaces/KI/pages/2500427777

Reines Browser-Tool: Nutzer öffnet HTML → Paste aus Confluence → fertig.  
Kein Python, kein Server, kein Setup. Vollständig offline-fähig.

**Aktueller Stand:** `APP_VERSION = "04.06.2026 22:00"` (~3490 Zeilen)  
**Testdaten:** `testdaten.tsv` im Repo – 73 fiktive Meetings, vollständige Beispielorganisation

---

## Datenschutz (fest, nie ändern)

- `LeitMet.csv`, `meetingstruk.csv` bleiben lokal, **nie** ins Repository
- **Keine Echtdaten in Commits**
- localStorage speichert nur Config (Zuordnungen, FK-Liste), niemals Meeting-Inhalte
- `wertOverrides` werden bei **neuem Daten-Import gelöscht** (gehören zur jeweiligen Datensession)

---

## Datenmodell – 14 Felder im Meeting-Objekt

| JS-Key | Confluence-Spalte | Typ | Notizen |
|---|---|---|---|
| `abteilung` | Abteilung | String | |
| `name` | Meetingname | String | |
| `kategorie` | Kategorie | String | |
| `zweck` | Zweck | Freitext | |
| `verantwortlich` | Verantwortlich | Kürzel (via canonAbbr) | |
| `teilnehmer` | Personen | Komma-sep. Kürzel (via canonAbbr) | Split auf `,;\n\r` |
| `rhythmus_klasse` | Rhythmus | normalisiert auf 7 Klassen | inkl. Wochentag-Extraktion |
| `wochentage` | (aus Rhythmus) | Array z.B. `["Mo","Do"]` | `extractWochentage()` |
| `dauer` | Dauer | Minuten (Integer, null=leer) | optional |
| `infofluss` | Informationsfluss | Freitext | |
| `wert` | Wirkung (1–4) | Integer 1–4 (null=leer) | optional; editierbar im Dashboard |
| `flugebene` | Flugebene (optional) | "FL1"/"FL2"/"FL3"/null | auto-suggested + editierbar; `flugebeneAuto=true` wenn vorgeschlagen |
| `gruppenTeilnehmer` | (berechnet) | Array | Teilnehmer die als Gruppe erkannt wurden |
| `hatGruppenTeilnehmer` | (berechnet) | Boolean | true wenn Gruppen-Platzhalter in Teilnehmern |
| `status` | Status | "Aktiv" / "Geplant" | |
| `abteilungsuebergreifend` | Abteilungsübergreifend | Boolean | nachträglich aus effectivePersonAbt berechnet |
| `ist_platzhalter` | Platzhalter | Boolean | |
| `learning` | Learnings | Freitext | |

**Wochentag im Rhythmus-Feld kodieren:**  
`"wöchentlich Mo"` → rhythmus_klasse=`wöchentlich`, wochentage=`["Mo"]`  
`"wöchentlich Di Do"` → wochentage=`["Di","Do"]` (Standup 2×/Woche)

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

## Tab-Struktur (11 Tabs, data-tab 0–10)

Navigation via `data-tab`-Attribut. `showTab(idx)` nutzt `querySelector(".panel[data-tab='${idx}']")` – **nicht** DOM-Index.

| data-tab | Tab | Panel-ID | Render-Funktion | Besonderheit |
|---|---|---|---|---|
| 0 | Personen | panel-7 | `renderPersonenTab()` | Erster Tab nach Import; adaptive Spalten |
| 1 | Netzwerk | panel-0 | `renderNetzwerk()` | d3-force + Plotly |
| 2 | Abteilungen | panel-3 | `renderAbteilung()` | Horizontal + Toggle Anzahl/Freq. |
| 3 | Kalender | panel-1 | `renderKalender()` | Wochentag-basiert |
| 4 | Kommunikation | panel-4 | `renderSankey()` + `renderChord()` | Bidirektional, D3-Chord darunter |
| 5 | Überschneidungen | panel-2 | `renderOverlap()` | Top-Paare-Liste oben, Heatmap darunter |
| 6 | Engpass | panel-8 | `renderEngpass()` + `renderZeitlast()` | h/Monat pro Person |
| 7 | Zeitverteilung | panel-9 | `renderTreemap()` | cornerradius:6, uniformtext hide |
| 8 | Wirkung | panel-10 | `renderWirkungsMatrix()` | Scatter: Zeit vs. Wirkung, Quadranten |
| 9 | Alle Meetings | panel-5 | `renderTable()` | Wirkung + Flugebene editierbar per Klick · ⚑ = Gruppen-Teilnehmer |
| 10 | Flight Levels | panel-fl | `renderFlightLevels()` | 5 Diagnose-Visualisierungen (F1–F5) |
| 11 | KI Analyse | panel-6 | statisch | Placeholder für KI-Ausbaustufe |
| 12 | Datenpflege | panel-dp | `renderDatapflege()` | **[ADMIN]** Abteilungstypen · Datenqualität · Gruppen · Config Export/Import |

**Tab-Bar:** Zwei Gruppen – „Analyse" (Tabs 1–11) und „Datenpflege" (Tabs 0, 9, 12). Admin-Gruppe `.tab-group-admin` → grauer active-State (statt teal).

**Lazy-Rendering:** `renderedTabs` Set. `showDashboard()` ruft `showTab(0)` (Personen) auf.  
**`refreshAllCharts()`** invalidiert alle renderedTabs und re-rendert direkt Tab 0 (Personen).

---

## Info-Overlay

Jeder Tab hat einen ℹ-Button (`class="tab-info-btn"`) oben rechts im Panel.  
Klick → `showTabInfo(idx)` → Modal mit drei Abschnitten:  
- Was zeigt dieses Chart?  
- Worauf achten?  
- Folgefragen  

`TAB_INFO`-Konstante enthält Inhalte für alle 11 Tabs (idx 0–10).

---

## Header

Teal-Header mit:
- Links: App-Titel + Subtitle (Stand, Anzahl Meetings)
- Rechts: `[↩ Neue Daten laden]` Button + Colenet-Logo (klickbar → colenet.de neuer Tab)

**Colenet-Logo:** Base64-PNG direkt eingebettet (`data:image/png;base64,...`), vollständig offline.  
In weißem Wrapper-Div (für Safari-Kompatibilität – kein padding auf img-Tag direkt).

---

## Personen-Tab – Adaptives Layout

`renderPersonenTab()` und `_buildDeptCol()`:
- Sortierung nach Personenanzahl absteigend (vollste Abteilung zuerst)
- Leere Abteilungen werden nicht angezeigt
- `SPECIAL_DEPTS` (Stabsfunktion, Geschäftsleitung, Extern, Kunden) nur wenn nicht schon als reguläre Abteilung vorhanden → **kein Duplikat-Problem**
- Abteilungen mit ≥9 Personen: 2-spaltiges Inner-Grid (`grid-template-columns:1fr 1fr`)
- `dept-col`: `flex:0 0 auto; align-self:flex-start` → nur so breit wie nötig, keine gleichhohen Spalten
- `person-chip`: kompakter (padding 3px 7px)

---

## Abteilungen-Tab

- **Hauptchart:** Horizontal (wie Engpass), 4 Rhythmus-Gruppen statt 7 Farben:
  - Hochfrequent (täglich+wöchentlich) → Teal
  - Regelmäßig (zwei-+dreiwöchentlich) → Blau
  - Selten (monatlich+quartalsweise) → Olivgrün
  - Variabel → Grau
- **Toggle:** Pill-Buttons `[ Anzahl ] [ Freq./Monat ]` – schaltet Y-Achse
- **Darunter:** Rhythmus-Chart (vertikal, informativer), dann Status-Chart

---

## Kommunikation-Tab

Zwei Charts untereinander:
1. **Sankey:** Bidirektionale Flows, Nodes nach Gesamtvolumen sortiert (am stärksten vernetzt oben). Richtung nicht bedeutsam.
2. **Chord-Diagramm (D3.js):** Bidirektional, Hover-Highlight (aktives Band voll, andere 0.08). Bogengröße = Gesamtvolumen.

---

## Zeitverteilung-Tab (Treemap)

- `marker.cornerradius: 6` (Plotly-native, ab 2.35.2)
- Kategorie-Knoten: volle Farbe (dunkler Rahmen)
- Meeting-Knoten: `lightenColor(color, 0.42)` (heller innen)
- `texttemplate: "%{label}"` – nur Label, keine Stunden im Feld
- `uniformtext: { mode:"hide", minsize:12 }` – kein Pixelmatsch in kleinen Kacheln
- `ids`-Array mit Präfixen `cat::` / `m::` – verhindert Label-Kollision

---

## Wirkungsmatrix-Tab

- X = Stunden/Monat, Y = Wirkung 1–4, Bubble = Teilnehmerzahl, Farbe = Kategorie
- Quadranten: Bereichernd / Effizient halten / Hinterfragen / Optimieren
- X-Trennlinie = Median der Zeitlast (dynamisch)
- `displayModeBar: false`

---

## localStorage-Struktur

```json
{
  "personAbt": { "Maa": "Business Unit" },
  "fkList": ["Maa", "Bsc"],
  "wertOverrides": { "Business Unit||Leitungsmeeting||0": 3 },
  "flugebeneOverrides": { "Business Unit||Leitungsmeeting": "FL3" },
  "deptFunktionen": { "Business Unit": "operativ", "Management": "strategisch" },
  "gruppenAufloesungen": { "Business Unit||Daily||BU-Team": ["Maa", "Bsc", "Tho"] }
}
```

**Wichtig:**
- `wertOverrides` werden bei neuem Daten-Import (in `showDashboard()`) gelöscht.
- `flugebeneOverrides` **bleiben** bei neuem Import erhalten (stabiler Schlüssel `abt||name` ohne idx) – FL-Klassifikation ist eine stabile Eigenschaft eines Meeting-Typs.
- `personAbt`, `fkList`, `flugebeneOverrides`, `deptFunktionen` und `gruppenAufloesungen` bleiben sessions-übergreifend erhalten.
- Export/Import als `meeting-config.json` über den Datenpflege-Tab möglich.

---

## Wichtige Konstanten und Funktionen

### `SPECIAL_DEPTS`
```javascript
const SPECIAL_DEPTS = [
  { key:"Stabsfunktion", color:"#5b8fa8", cssClass:"special-stab", title:"Stab / andere interne Funktion" },
  { key:"Geschäftsleitung", color:"#7c6bab", cssClass:"special-gl", title:"Geschäftsleitung" },
  { key:"Extern", color:"#6b7280", cssClass:"special-extern", title:"Externe Partner / Dienstleister" },
  { key:"Kunden", color:"#c2607a", cssClass:"special-kunden", title:"Kunden" }
]
```

### `RHYTHM_GROUPS` (für Abteilungen-Chart)
```javascript
const RHYTHM_GROUPS = [
  { label:"Hochfrequent", rhythms:["täglich","wöchentlich"], color:"#59B2A5" },
  { label:"Regelmäßig", rhythms:["zweiwöchentlich","dreiwöchentlich"], color:"#2176ae" },
  { label:"Selten", rhythms:["monatlich","quartalsweise"], color:"#7c9e44" },
  { label:"Variabel", rhythms:["variabel"], color:"#9ca3af" }
];
const RHYTHM_TO_GROUP = {}; // { "täglich": {label:"Hochfrequent",...}, ... }
```

### `lightenColor(hex, factor)`
Hilfsfunktion: Hex-Farbe aufhellen. `lightenColor("#59B2A5", 0.42)` → rgb-String.

### `showTabInfo(idx)` / `closeTabInfo()`
Info-Modal für Tab idx öffnen/schließen.

### `setAbtMode(mode)`
Toggle zwischen `"anzahl"` und `"freq"` im Abteilungen-Tab. Ruft `renderAbtChart()` auf.

### `isGruppenParticipant(name)`
Erkennt Gruppen-Platzhalter in Teilnehmern: Kleinbuchstabe-Start, >30 Zeichen, passt zu `allDepts`, SPECIAL_DEPTS oder enthält „alle/team/gruppe"-Keywords.

### `suggestFlightLevel(m)`
Auto-Klassifikation FL1/FL2/FL3. Stärkstes Signal: **`deptFunktionen[m.abteilung]`** (+5 Punkte). Dann `abteilungsuebergreifend`, Teilnehmeranzahl, Rhythmus, Keywords.

### `renderDatapflege()`
Drei Sektionen: Abteilungstypen-Grid (`renderDeptTypenGrid`), Datenqualitäts-Cockpit (`renderQualitaetsCockpit`), Gruppen-Teilnehmer-Auflösung (`renderGruppenTeilnehmerSection`).

### `setDeptTyp(sel)`, `saveGruppenAufloesung(btn)`
Inline-Editierung im Datenpflege-Tab. Speichern via `saveConfig()`.

### `exportConfig()`, `importConfigFile(input)`
Export: Download `meeting-config.json`. Import: JSON lesen → validieren → `applyStoredConfig()` → re-init → `refreshAllCharts()`.

### `renderFlightLevels()`
5 Diagnose-Visualisierungen im Flight-Levels-Tab:
- F1: Kommunikationspyramide (Horizontal-Bar FL1/FL2/FL3)
- F2: FL2-Verbindungsmatrix (Heatmap Abt × Abt)
- F3: Wirkung nach Flugebene (Box+Scatter)
- F4: Brückenkopf-Heatmap (Person × Ebene, h/Monat)
- F5: Rhythmus-Level-Matrix (Bubble FL × Rhythmus)
Jede Visualisierung hat ein `fl-alert-fN` Diagnose-Element (warn/ok).

### `handleFlightLevelClick(e)`
Inline-Editing der FL-Spalte in Tab 9 (wie `handleWertClick`). Setzt `m.flugebeneAuto = false`.

### `renderChord(flussSymm, abtList, abtIdx)`
D3.js Chord-Diagramm in `chart-chord`. Hover-Highlight: aktives Band 0.92, andere 0.08.

---

## Branch-Workflow

```
main  ←  feat/<name>  (gh pr create → squash merge)
```
- Kein Direkt-Commit auf `main` für neue Features
- **APP_VERSION-Timestamp** (`DD.MM.YYYY HH:MM`) im letzten Commit setzen
- `gh pr merge <nr> --squash --delete-branch && git checkout main && git pull`

---

## Flight Levels – Konzept (für künftige Sessions)

**3 Ebenen:**
- FL1 (Operativ): Einzelteam, täglich/wöchentlich, Tasks/Stories
- FL2 (Koordination): Teamübergreifend, Abhängigkeitsmanagement, Epics
- FL3 (Strategisch): Portfolioebene, OKRs, Quartals-/Jahreshorizont

**Auto-Klassifikation:** `suggestFlightLevel(m)` – stärkstes Signal: `abteilungsuebergreifend`. Badges mit `~` = auto-vorgeschlagen (halbtransparent). Manuell änderbar per Klick in Tab „Alle Meetings".

**Diagnose-Logik:**
- F1: Fehlende FL2 = häufigste Dysfunktion
- F2: Weiße Felder in Matrix = Koordinations-Silos
- F3: FL2/FL3 mit Wirkung ≤ 2 = Koordinationstheater
- F4: Person auf allen 3 Ebenen = potentieller Informationsrouter/Bottleneck
- F5: FL3+wöchentlich oder FL1+quartalsweise = falsche Ebene

---

## Alle PRs (alle gemergt)

| PR | Was |
|---|---|
| #1 | Standalone-HTML Dashboard |
| #2–#13 | Diverse Features + Fixes (Engpass, Treemap, Kalender, Personen-Fixes) |
| #14 | Wirkung (1–4) in Tab Alle Meetings – editierbar + localStorage |
| #15 | Wirkungsmatrix (Scatter-Chart Zeit vs. Wirkung) |
| #16 | Treemap: ids-Array gegen Label-Kollision |
| #17 | Wirkungsmatrix Legende-Overflow fix |
| #18 | Abteilungen: Pill-Toggle Anzahl/Freq. |
| #19 | UX-Refactor: Tab-Reihenfolge (data-tab), visuelle Konsistenz |
| #20 | Abteilungen horizontal + 4 Rhythmusgruppen; Zeitverteilung Varianten |
| #21 | ℹ-Overlay pro Tab; Überschneidungen Top-Paare; Sunburst entfernt |
| #22 | 7 UX-Fixes: Legende, Reihenfolge Charts, Sankey-Text, wertOverrides, KI-Text |
| #23 | Treemap cornerradius (Plotly-native); Sankey bidirektional beschrieben |
| #24 | Chord-Diagramm (D3); Sankey nach Vernetzungsgrad sortiert; Treemap-Text |
| #25 | Syntaxfehler Sankey-Hover (?.0.92 → ? 0.92 : 0.04) |
| #26 | Chord: Größe aus clientWidth; D3-Tooltip |
| #27 | Chord: Hover-Highlight Bänder; Label-Clipping behoben |
| #28 | Sankey: bidirektional zurück, Nodes nach Vernetzungsgrad |
| #29–#31 | Colenet-Logo: Base64-PNG, Safari-Fix, Position |
| #32 | Personen-Tab: adaptives Layout, Sortierung, 2-Spalten, kein Duplikat |
| #33 | Flight Levels: Tab 10, 5 Diagnose-Visualisierungen (F1–F5), Auto-Klassifikation, ~-Badge |
| #34 | Datenpflege-Tab: Abteilungstypen, Datenqualität, Gruppen-Teilnehmer, Config Export/Import, Tab-Grouping |
| #35 | Bug: CSV-Import kaputt (Safari nested Template-Literals); Script in 3 Blöcke aufgeteilt; Import-Screen UX-Redesign (zwei gleichwertige Optionen, OS-neutral) |

---

## Offene Punkte

### Confluence-Seite (Nächste Schritte)
- KI-Analyse Tab (Tab 11) mit echten Beobachtungen befüllen
- Flight Levels: Testdaten mit FL-Spalte versehen oder Auto-Klassifikation evaluieren
- Import-Screen: `setImportMethod('confluence'|'csv')` toggle-Funktion; `handleFileDrop(event)` für Drag&Drop

### Gruppe 4 – Bewusst zurückgestellt

| Feature | Anmerkung |
|---|---|
| D2 – Reifegrad-Indikator | Spider-Chart, komplex |
| C1/C2 – Zweck-Typisierung | Braucht neues Feld + Daten-Nacherfassung |
| E1 – Längsschnitt | Eigene Architektur für mehrere Datensätze |

---

## Gelöste Bugs (Referenz)

- ~~Treemap bricht bei Meetingname = Kategoriename~~ → PR #16
- ~~Wirkungsmatrix Legende überlappt Hinweis~~ → PR #17
- ~~Sankey-Hover Syntaxfehler (?.0.92)~~ → PR #25
- ~~Chord zu klein / kein Hover~~ → PR #26/27
- ~~Geschäftsleitung doppelt im Personen-Tab~~ → PR #32
- ~~wertOverrides aus alter Session werden übernommen~~ → PR #22
- ~~Logo in Safari unsichtbar~~ → PR #30/31
