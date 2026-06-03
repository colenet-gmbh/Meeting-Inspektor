# CLAUDE_CONTEXT – Meeting-Strukturanalyse Standalone

> Lese diese Datei am Anfang jeder neuen Session vollständig.  
> Sie ist lokal (gitignored) und enthält den vollständigen Kontext.

---

## Projekt-Überblick

**Einzige relevante Datei:** `meeting_strukturanalyse_standalone.html`  
Lokaler Pfad: `/Users/leivbraun/Documents/Claude Code/Organisations-Meeting-Informationsfluss/`  
GitHub: https://github.com/braunle77/Organisations-Meeting-Informationsfluss  
Confluence: https://colenet.atlassian.net/wiki/spaces/KI/pages/2500427777

Reines Browser-Tool: Nutzer öffnet HTML → Paste aus Confluence → fertig.  
Kein Python, kein Server, kein Setup.

**Aktueller Stand:** `APP_VERSION = "30.05.2026 16:42"` (ca. 1940 Zeilen)

---

## Datenschutz (fest, nie ändern)

- `LeitMet.csv`, `meetingstruk.csv` bleiben lokal, **nie** ins Repository
- **Keine Echtdaten in Commits**
- localStorage speichert nur Config (Zuordnungen, FK-Liste), niemals Meeting-Inhalte

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
| `rhythmus_klasse` | Rhythmus | normalisiert auf 7 Klassen | |
| `dauer` | Dauer | Minuten (Integer, null=leer) | optional |
| `infofluss` | Informationsfluss | Freitext | |
| `wert` | Wirkung (1–4) | Integer 1–4 (null=leer) | optional; Selbsteinschätzung Kopf |
| `status` | Status | "Aktiv" / "Geplant" | |
| `abteilungsuebergreifend` | Abteilungsübergreifend | Boolean | nachträglich aus effectivePersonAbt berechnet |
| `ist_platzhalter` | Platzhalter | Boolean | |
| `learning` | Learnings | Freitext | |

**Spalten-Reihenfolge in Confluence** (für Paste-Hinweis):  
`Abteilung · Meetingname · Kategorie · Zweck · Verantwortlich · Personen · Rhythmus · Dauer · Informationsfluss · Wirkung (1–4) · Status · Abteilungsübergreifend · Platzhalter · Learnings`

**Kein `multiplikator`** – gleichartige Meetings als separate Zeilen gepflegt.

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

Navigation via `data-tab`-Attribut (nicht DOM-Index). `showTab(idx)` selektiert per `querySelector(".panel[data-tab='idx']")`.

| data-tab | Tab | Panel-ID | Render-Funktion |
|---|---|---|---|
| 0 | Personen | panel-7 | `renderPersonenTab()` |
| 1 | Netzwerk | panel-0 | `renderNetzwerk()` |
| 2 | Abteilungen | panel-3 | `renderAbteilung()` (inkl. Toggle Anzahl/Freq.) |
| 3 | Kalender | panel-1 | `renderKalender()` |
| 4 | Kommunikation | panel-4 | `renderSankey()` + `renderChord()` |
| 5 | Überschneidungen | panel-2 | `renderOverlap()` + Top-Paare-Liste |
| 6 | Engpass | panel-8 | `renderEngpass()` + `renderZeitlast()` |
| 7 | Zeitverteilung | panel-9 | `renderTreemap()` (cornerradius:6) |
| 8 | Wirkung | panel-10 | `renderWirkungsMatrix()` |
| 9 | Alle Meetings | panel-5 | `renderTable()` |
| 10 | KI Analyse | panel-6 | statisch (Placeholder) |

**Lazy-Rendering:** `renderedTabs` Set. `showDashboard()` ruft `showTab(0)` (Personen) auf.  
**Info-Overlay:** Jeder Tab hat ℹ-Button → `showTabInfo(idx)` → Modal mit Erklärung.  
**Colenet-Logo:** Base64-PNG im Header, rechts, klickbar → colenet.de (neuer Tab).

---

## Wichtige Funktionen und Konzepte

### `canonAbbr(s)` (lokal in `parseData()`)
Case-insensitive Deduplication von Kürzeln innerhalb eines Parse-Aufrufs.  
`"urk"` → nach `normalizeAlias` → `"Urk"` → `canonAbbr` stellt konsistente Schreibweise sicher.

### `normalizeAlias(raw)`
Sucht in `ALIAS_MAP` (standardmäßig leer), sonst: ersten Buchstaben uppercase.

### `effectivePersonAbt`
```javascript
effectivePersonAbt = { ...autoDerivePERSON_ABT(MEETINGS).map, ...PERSON_ABT };
// danach patcht applyStoredConfig() localStorage-Overrides drüber
```

### `autoDerivePERSON_ABT(meetings)`
Läuft über **alle** Meetings (inkl. Platzhalter). Verantwortliche/r wird explizit einbezogen.  
Gibt der Person die Abteilung, in der sie am häufigsten vorkommt.

### `_rawCandidates` in `renderPersonenTab()`
```javascript
// KEIN Platzhalter-Filter – echte Personen stehen auch in Platzhalter-Meetings (PR #13)
const _rawCandidates = [...new Set(
  MEETINGS.flatMap(m => [...m.teilnehmer, m.verantwortlich].filter(Boolean))
)].sort();
```

### `saveConfig()` / `applyStoredConfig()`
localStorage-Key: `"meeting-strukturanalyse-config"`  
Aktuelles Format: `{ personAbt: {...}, fkList: [...] }`

### `SPECIAL_DEPTS`
Feste Sonder-Spalten im Personen-Tab:  
`["Stabsfunktion", "Geschäftsleitung", "Extern", "Kunden"]`

### `findCol(headers, candidates)`
Matcht Header-Spalten case-insensitiv via `h.includes(c)`.  
`"Wirkung (1–4)"` matcht auf Candidate `"wirkung"` ✓

---

## Alle bisherigen PRs (alle gemergt außer wo anders angegeben)

| PR | Branch | Was |
|---|---|---|
| #1 | initial | Standalone-HTML Dashboard |
| #2 | feat/engpass-karte | Engpass-Karte Tab 8 |
| #3 | feat/status-verteilung | Status-Verteilung Chart in Tab 3 |
| #4 | feat/rhythmus-chart | Rhythmus×Kategorie-Chart in Tab 3 |
| #5 | feat/dauer-feld | Dauer-Spalte (Minuten) im Parser + Tabelle |
| #6 | fix/kalender-farben | Kalender-Tab Abteilungsfarben + Legende |
| #7 | feat/kategorie-treemap | Zeitverteilung Treemap in Tab 9 |
| #8 | feat/zeitlast-fk | Zeitlast pro Person in Stunden/Monat (Tab 8) |
| #9 | fix/kalender-dodge | Dodge-Versatz bei überlappenden Abteilungskreisen |
| #10 | fix/spalten-hinweis | Spalten-Hinweis im Paste-Dialog (14 Spalten) |
| #11 | fix/personen-vera-sichtbar | Verantwortliche/r auch im Personen-Tab sichtbar |
| #12 | fix/personen-space-filter | Personen mit Leerzeichen (Jana Müller) sichtbar |
| #13 | fix/personen-platzhalter | Personen aus Platzhalter-Meetings sichtbar |
| #14 | feat/wert-feld | Wirkung (1–4) in Tab 5 anzeigen + editieren + localStorage |
| #15 | feat/wirkungs-matrix | Scatter-Chart Zeit vs. Wirkung in Tab 10 |
| #16 | fix/treemap-label-kollision | Zeitverteilung bricht nicht bei Namenskollision (ids-Array) |
| #17 | fix/wirkung-legende-overflow | Legende in Tab 10 überlappt nicht mehr den Hinweis-Text |
| #18 | feat/abt-toggle | Pill-Toggle Anzahl / Freq./Monat in Tab Abteilungen |
| #19 | feat/ux-refactor | Tab-Reihenfolge neu (data-tab), visuelle Konsistenz (Treemap, Wirkung) |
| #20 | feat/chart-redesign | Abteilungen horizontal + 4 Rhythmusgruppen + Zeitverteilung Varianten |
| #21 | feat/tab-info | ℹ-Overlay pro Tab + Überschneidungen Top-Paare + Sunburst entfernt |
| #22 | fix/ux-feedback | 7 UX-Korrekturen: Legende, Reihenfolge, Sankey-Text, wertOverrides, KI-Text |
| #23 | fix/treemap-corners-sankey | native cornerradius + Sankey-Beschreibung bidirektional |
| #24 | feat/chord-sankey-redesign | Chord-Diagramm (D3) + Sankey nach Vernetzungsgrad sortiert + Treemap-Text |
| #25 | fix/sankey-syntax | Syntaxfehler im Sankey-Hover behoben (?.0.92 → ? 0.92 : 0.04) |
| #26 | fix/chord-size-hover | Chord-Größe (clientWidth) + D3-Tooltip statt SVG-title |
| #27 | feat/chord-hover-highlight | Hover-Highlight auf Chord-Bändern + Label-Clipping behoben |
| #28 | fix/sankey-revert-sort | Sankey bidirektional zurück, Nodes nach Vernetzungsgrad sortiert |
| #29 | feat/colenet-logo | Colenet-Logo als Base64-PNG in Header eingebettet |
| #30 | fix/logo-png | WebP → PNG (WebP wurde nicht gerendert) |
| #31 | fix/logo-safari | Padding auf Wrapper-Div (Safari-Fix) |
| – | direkt | Logo-Position: ganz rechts, Button links daneben |
| – | direkt | Logo klickbar → colenet.de in neuem Tab |

---

## Branch-Workflow

```
main  ←  feat/<name>  (gh pr create → squash merge)
```
- Kein Direkt-Commit auf `main` für neue Features
- Jeder Branch = genau ein Feature
- **APP_VERSION-Timestamp** (`DD.MM.YYYY HH:MM`) im letzten Commit vor dem Merge setzen
- PRs via `gh pr create`
- Lokal mergen: `gh pr merge <nr> --squash --delete-branch && git checkout main && git pull`

---

## Gruppe 3 – Erledigt ✅

`feat/wert-feld` (PR #14) und `feat/wirkungs-matrix` (PR #15) sind gemergt.  
Fixes: `fix/treemap-label-kollision` (PR #16), `fix/wirkung-legende-overflow` (PR #17).

---

### feat/wert-feld ✅ (PR #14)

**Ziel:** `wert` (Wirkung 1–4) im Alle-Meetings-Tab (Tab 5) anzeigen und editierbar machen.

**Tabellen-Header** – neue Spalte nach `<th title="Dauer in Minuten">Min.</th>`:
```html
<th title="Empfundener Wert 1–4 (Selbsteinschätzung)">Wirkg.</th>
```

**Tabellen-Zelle** – klickbar, zeigt Füllkreise:
```javascript
const wertDisplay = m.wert
  ? '●'.repeat(m.wert) + '○'.repeat(4 - m.wert)
  : '–';
// <td class="wert-cell" data-idx="${idx}" ...>${wertDisplay}</td>
```

**Editier-Logik:**
- Klick auf Wert-Zelle → kleines Inline-Dropdown mit Optionen: –, 1, 2, 3, 4
- Auswahl → `MEETINGS[idx].wert = neuerWert` → Zelle aktualisieren → `saveConfig()`
- Alternativ: Popover analog zum Personen-Popover

**Persistenz in localStorage** – neues Feld `wertOverrides`:
```json
{
  "personAbt": { ... },
  "fkList": [ ... ],
  "wertOverrides": { "Abteilung||Meetingname||idx": 3 }
}
```
Key-Aufbau: `m.abteilung + "||" + m.name + "||" + idx` (idx für Eindeutigkeit bei gleichnamigen Meetings).

**`saveConfig()` erweitern:**
```javascript
const wertOverrides = {};
MEETINGS.forEach((m, i) => {
  if (m.wert !== null) wertOverrides[m.abteilung+"||"+m.name+"||"+i] = m.wert;
});
// dann wertOverrides in localStorage-JSON aufnehmen
```

**`applyStoredConfig()` erweitern:**
```javascript
if (cfg.wertOverrides) {
  MEETINGS.forEach((m, i) => {
    const key = m.abteilung+"||"+m.name+"||"+i;
    if (cfg.wertOverrides[key] != null) m.wert = cfg.wertOverrides[key];
  });
}
```

---

### feat/wirkungs-matrix (C3) ✅ (PR #15)

**Ziel:** Scatter-Chart – welche Meetings kosten viel Zeit und bringen wenig Wirkung?

**Neuer Tab 10 "Wirkung"**

HTML (Tab-Button + Panel analog zu den bestehenden):
```html
<button class="tab-btn" onclick="showTab(10)">Wirkung</button>
...
<div class="panel" id="panel-10">
  <div id="chart-wirkung" style="height:520px"></div>
</div>
```

**`showTab()`** erweitern:
```javascript
if (idx === 10) renderWirkungsMatrix();
```

**`renderWirkungsMatrix()`:**
```javascript
function renderWirkungsMatrix() {
  // Nur Meetings mit dauer UND wert einbeziehen
  const data = MEETINGS.filter(m => m.dauer !== null && m.wert !== null);
  if (!data.length) {
    // Fallback-Meldung rendern
    return;
  }
  // X = Stunden/Monat: m.dauer * FREQ_MONTHLY[m.rhythmus_klasse] / 60
  // Y = m.wert (1–4)
  // Bubble-Größe = m.teilnehmer_anzahl (mind. 1)
  // Farbe = Kategorie (PALETTE per katIndex)
  // Hover = Name, Abteilung, Rhythmus, Dauer, Wert
  // Quadranten-Annotations (Plotly shapes + annotations):
  //   Q1 (viel Zeit, hohe Wirkung) = "Effizient halten"
  //   Q2 (wenig Zeit, hohe Wirkung) = "Bereichernd"
  //   Q3 (wenig Zeit, geringe Wirkung) = "Hinterfragen"
  //   Q4 (viel Zeit, geringe Wirkung) = "Optimieren"
}
```

**Quadranten-Mittelpunkt:** X-Median der sichtbaren Daten (nicht fix), Y = 2.5 (Mitte 1–4).

**`refreshAllCharts()` erweitern:** `renderedTabs.delete(10)` hinzufügen.

---

## Alle-Meetings-Tabelle – aktueller HTML-Stand

```html
<thead><tr>
  <th>Abteilung</th><th>Meeting</th><th>Kategorie</th><th>Rhythmus</th>
  <th title="Dauer in Minuten">Min.</th>
  <!-- HIER kommt neu: <th title="Empfundener Wert 1–4">Wirkg.</th> -->
  <th>Verantwortl.</th><th>Teilnehmer</th><th>Status</th>
  <th title="Abteilungsübergreifend">Übergr.</th><th>Zweck</th><th>Learnings</th>
</tr></thead>
```

---

## localStorage-Struktur

**Aktuell:**
```json
{ "personAbt": { "Urk": "IT" }, "fkList": ["Urk"] }
```

**Nach feat/wert-feld:**
```json
{ "personAbt": { "Urk": "IT" }, "fkList": ["Urk"], "wertOverrides": { "IT||Daily-Standup||0": 3 } }
```

---

## Kalender-Dodge (PR #9 – Referenz)

X-Achse numerisch, Offset pro Abteilung bei Kollision:
```javascript
const tagIdx = { "Mo":0, "Di":1, "Mi":2, "Do":3, "Fr":4, "—":5 };
// tickvals: [0,1,2,3,4,5], ticktext: ["Mo","Di","Mi","Do","Fr","—"], range: [-0.65, 5.65]
```

---

## Gruppe 4 – Später (nicht jetzt)

| Feature | Anmerkung |
|---|---|
| D2 – Reifegrad-Indikator | Spider-Chart, komplex, niedriger Sofortwert |
| C1/C2 – Zweck-Typisierung | Braucht neues Feld `zweck_typ` + Daten-Nacherfassung |
| E1 – Längsschnitt | Eigene Architektur für mehrere Datensätze nötig |

---

## Bekannte gelöste Bugs (zur Info)

- ~~Personen aus Platzhalter-Meetings unsichtbar~~ → PR #13
- ~~Verantwortliche/r fehlte in Personen-Tab~~ → PR #11
- ~~Namen mit Leerzeichen (Jana Müller) gefiltert~~ → PR #12
- ~~Kalender-Kreise überlappend~~ → PR #9 (Dodge)
- ~~Diagnose-Box zeigte `else if (dept)` Fall nicht~~ → kein eigener PR nötig (nach PR #13 obsolet)
- ~~Zeitverteilung bricht bei Meetingname = Kategoriename~~ → PR #16 (ids-Array)
- ~~Legende in Wirkungsmatrix überlappt Hinweis-Text~~ → PR #17
- ~~Doppelklick FK-Toggle synchronisiert Personen-Tab nicht~~ → war bereits implementiert (renderedTabs.delete(7))
