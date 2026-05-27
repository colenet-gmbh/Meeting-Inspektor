# Organisations-Meeting-Informationsfluss

Interaktives Analyse-Dashboard für Meeting-Strukturen in Organisationen.  
Zwei Ansätze: **Python-Pipeline** (xlsx/csv → aufbereitetes HTML) oder **Standalone-HTML** (direkt im Browser, kein Python).

---

## Wozu

- Meeting-Landschaft einer Organisation visualisieren
- Informationsfluss zwischen Abteilungen sichtbar machen
- Redundante Meetings identifizieren (Teilnehmer-Überschneidungen)
- Kommunikationslücken aufdecken
- Bereinigtes Ergebnis als Tabelle zurück in Confluence spielen

Das Dashboard ist als Gesprächsgrundlage für Management-Reviews gedacht, nicht als statischer Bericht.

---

## Voraussetzungen

```bash
pip install pandas openpyxl networkx plotly pyvis
```

---

## Eingabedatei

Die Quelldatei ist eine Excel-Tabelle (`.xlsx`) mit folgenden Spalten:

| Spalte | Beschreibung |
|--------|-------------|
| Abteilung | Kürzel der Organisationseinheit |
| Meeting-Name | Bezeichnung des Meetings |
| Zweck | Kurzbeschreibung des Meeting-Inhalts |
| Verantwortlich | Kürzel der verantwortlichen Person |
| Teilnehmer | Komma- oder semikolon-getrennte Kürzel |
| Rhythmus | Freitext (z.B. „wöchentlich", „alle 2 Wochen montags") |
| Informationsfluss (rein / raus / an wen) | Beschreibung des Informationsflusses |
| Status | „Aktiv" oder „Geplant" |
| Learnings | Optionale Notizen/Verbesserungsideen |

Rohdatei bleibt **lokal** und wird nicht ins Repository eingecheckt (`.gitignore`).

---

## Modus 1: Python-Pipeline

Für vollständige Datenbereinigung, Normalisierung und ein reich bebildertes HTML-Dashboard.

### 1. Daten bereinigen

```bash
python3 daten_bereinigen.py --input /pfad/zur/meetings.xlsx
```

Erzeugt: `meetings_bereinigt.json`

Optionen:
- `--input`      Pfad zur Quelldatei (`.xlsx` oder `.csv`) — **Pflichtangabe**
- `--output`     Pfad zur JSON-Ausgabe (Standard: `meetings_bereinigt.json`)
- `--confluence` Zusätzlich eine CSV für den Confluence-Import erzeugen (`confluence_tabelle.csv`)

### 2. Dashboard erzeugen

```bash
python3 dashboard_erstellen.py
```

Liest `meetings_bereinigt.json`, erzeugt `meeting_strukturanalyse.html`.

### 3. Dashboard öffnen

```bash
open meeting_strukturanalyse.html
```

Die HTML-Datei ist vollständig offline-fähig (Plotly.js eingebettet, ~5 MB) und kann per E-Mail oder Confluence geteilt werden.

---

## Modus 2: Standalone-HTML

Kein Python, kein Server. Die Datei `meeting_strukturanalyse_standalone.html` läuft komplett im Browser.

### Daten laden

**Option A – Confluence-Paste:**

1. Confluence-Seite mit der Meeting-Tabelle öffnen
2. Alles markieren (`⌘A`) und kopieren (`⌘C`)
3. HTML öffnen → „Aus Confluence einfügen" → `⌘V`

Der Header wird automatisch erkannt (überspringt Seitenname und Navigation).

**Option B – CSV-Upload:**

CSV, TSV oder TXT mit den [erwarteten Spalten](#eingabedatei) hochladen.  
Trennzeichen (Komma, Semikolon, Tab) wird automatisch erkannt. UTF-8-BOM (Excel/Numbers) wird unterstützt.

### Konfiguration

Oben in der HTML-Datei befindet sich ein optionaler Config-Block. Alle Felder können leer bleiben – Abteilungen und Farben werden dann automatisch aus den Daten abgeleitet.

```javascript
const ALIAS_MAP   = { /* Kürzel-Normalisierung, z.B. "max": "Max" */ };
const PERSON_ABT  = { /* Override Person→Abteilung;  leer = auto  */ };
const FK_LIST     = [ /* Führungskräfte (Stern im Netzwerk)        */ ];
const ABT_FARBEN  = { /* Override Abteilungsfarben;   leer = auto  */ };
```

### Neue Daten laden

Über den Button „Neue Daten laden" kann jederzeit eine neue Datei eingelesen werden, ohne die Seite neu zu öffnen.

---

## Confluence-Export (Pipeline)

```bash
python3 daten_bereinigen.py --input /pfad/zur/meetings.xlsx --confluence
```

Erzeugt `confluence_tabelle.csv` (Semikolon-getrennt, UTF-8-BOM).  
In Numbers/Excel öffnen → alles markieren → kopieren → in Confluence-Tabelle einfügen.

---

## Dashboard-Tabs

| Tab | Inhalt |
|-----|--------|
| Netzwerk | Wer kommuniziert mit wem? Zentralität und Brücken |
| Kalender | Wann findet was statt? Rhythmus-Verteilung |
| Überschneidungen | Jaccard-Ähnlichkeit der Teilnehmergruppen |
| Abteilungen | Meeting-Anzahl und -Frequenz pro Abteilung |
| Informationsfluss | Sankey-Diagramm der Informationswege |
| Alle Meetings | Filterbare Tabelle mit allen Daten |
| Auffälligkeiten | Kommentierte Beobachtungen als Gesprächsgrundlage |

---

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `meeting_strukturanalyse_standalone.html` | Standalone-Dashboard (Modus 2) |
| `daten_bereinigen.py` | Datenbereinigung und Normalisierung (Modus 1) |
| `dashboard_erstellen.py` | Chart-Generierung und HTML-Zusammenbau (Modus 1) |
| `meetings_bereinigt.json` | Bereinigte Daten (Zwischenschritt, Modus 1) |
| `meeting_strukturanalyse.html` | Fertiges Pipeline-Dashboard (Modus 1) |
| `confluence_tabelle.csv` | Exporttabelle für Confluence |

Quelldaten (`*.xlsx`, `*.csv`) sind in `.gitignore` ausgeschlossen.

---

## Anpassen

Alle Config-Dicts können leer bleiben – Abteilungen, Zuordnungen und Farben werden dann automatisch aus den Daten abgeleitet.

**`daten_bereinigen.py`** und **`dashboard_erstellen.py`**
- `ALIAS_MAP` – Kürzel-Normalisierung (Kleinschreibung → Anzeigename)
- `PERSON_ABT` – Override Person→Abteilung; leer = auto
- `PERSON_SUBTEAM` – optionale Subteam-Zuordnung für Hover-Texte
- `FK_LIST` – Führungskräfte (Stern-Symbol im Netzwerk); leer = keine Hervorhebung
- `ABT_FARBEN` – Override Abteilungsfarben; leer = automatisch aus Palette
