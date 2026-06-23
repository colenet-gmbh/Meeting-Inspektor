# Meeting-Inspektor

Interaktives Browser-Dashboard zur Analyse der Meeting-Landschaft einer Organisation.  
Kein Server, keine Installation, keine KI für den Betrieb erforderlich – eine einzige HTML-Datei.

---

## Wozu

- Meeting-Landschaft visualisieren und auf einen Blick erfassen
- Kommunikations- und Informationsfluss zwischen Abteilungen sichtbar machen
- Redundante Meetings und Teilnehmer-Überschneidungen identifizieren
- Personen-Engpässe und Meeting-Last pro Person erkennen
- Kommunikationsfluss über Flight Levels diagnostizieren
- Datenqualität der Urliste verbessern (Vollständigkeits-Impulse)

Das Dashboard ist als Gesprächsgrundlage für Management-Reviews gedacht, nicht als statischer Bericht.

---

## Schnellstart

1. [`meeting-inspektor.html`](https://raw.githubusercontent.com/braunle77/Meeting-Inspektor/main/meeting-inspektor.html) herunterladen (Rechtsklick → „Ziel speichern unter") und im Browser öffnen
2. Daten laden – zwei Wege:

**Option A – Paste aus Confluence:**
1. Confluence-Seite mit der Meeting-Tabelle öffnen
2. Alles markieren (`⌘A` / `Strg+A`) und kopieren
3. Im Dashboard einfügen → „Prüfen & Laden"

**Option B – Datei wählen:**
CSV, TSV oder TXT mit den [erwarteten Spalten](#eingabeformat) hochladen.  
Trennzeichen (Komma, Semikolon, Tab) und UTF-8-BOM (Excel/Numbers) werden automatisch erkannt.

3. Im **Personen-Tab** Abteilungszuordnungen prüfen und ggf. bestätigen
4. Im **Konfiguration-Tab** Abteilungstypen und weitere Einstellungen vornehmen

Quelldaten bleiben **lokal** im Browser – keine Daten verlassen das Gerät.

---

## Eingabeformat

Spalten werden automatisch per **Name** erkannt – Reihenfolge spielt keine Rolle.

| Spalte | Beschreibung | Pflicht |
|--------|-------------|---------|
| Abteilung | Bezeichnung der Organisationseinheit | ✓ |
| Meetingname | Bezeichnung des Meetings | ✓ |
| Kategorie | Frei definierbar | |
| Zweck | Kurzbeschreibung | |
| Verantwortlich | Kürzel der verantwortlichen Person | |
| Personen | Komma- oder semikolon-getrennte Kürzel | ✓ |
| Rhythmus | Freitext – wird automatisch normalisiert | ✓ |
| Dauer | Dauer in Minuten | |
| Informationsfluss | Beschreibung des Informationsflusses | |
| Wirkung (1–4) | Empfundener Wert – direkt in der Quelltabelle pflegen | |
| Status | „Aktiv" oder „Geplant" | ✓ |
| Abteilungsübergreifend | „Ja" / „Nein" (wird automatisch berechnet) | |
| Platzhalter | „Ja" wenn Teilnehmerkreis variabel | |
| Learnings | Optionale Notizen | |
| Flugebene | FL1 / FL2 / FL3 – wird automatisch klassifiziert wenn leer | |

---

## Analyse-Tabs

| Tab | Inhalt |
|-----|--------|
| **Netzwerk** | Wer kommuniziert mit wem? Zentralität und Brücken sichtbar machen |
| **Abteilungen** | Meeting-Dichte, Frequenz und Rollen pro Abteilung |
| **Kalender** | Wann findet was statt? Rhythmus-Verteilung über die Woche |
| **Kommunikation** | Sankey- und Chord-Diagramm der Kommunikationsintensität |
| **Überschneidungen** | Meetings mit ähnlichen Teilnehmergruppen (Jaccard-Ähnlichkeit) |
| **Engpass** | Meeting-Last und Zeitaufwand je Person |
| **Zeitverteilung** | Monatliche Personen-Stunden nach Kategorie |
| **Wirkung** | Zeitaufwand vs. empfundene Wirkung (Optimierungspotenzial) |
| **Flight Levels** | Kommunikationsfluss-Diagnose auf FL1 / FL2 / FL3 |
| **Personen** | Abteilungszuordnung und Führungskräfte-Verwaltung |
| **Alle Meetings** | Filterbare Read-only-Tabelle aller Meetings |
| **Konfiguration** | Datenpflege, Datenqualität und Tool-Einstellungen |

---

## Konfiguration

Der **Konfiguration-Tab** bietet mehrere Bereiche:

- **Individuelle Impulse zur Datenoptimierung** – Name oder Kürzel eingeben und sofort sehen, welche eigenen Meetings noch Lücken in der Urliste haben (fehlende Dauer, Wirkung, Infofluss, Wochentag)
- **Personen-Zuordnung** – Abteilungen manuell übersteuern und Führungskräfte markieren
- **Abteilungstypen** – Abteilungen als Linie, Stab oder Projekt klassifizieren
- **Datenqualität: Gruppen-Bezeichnungen** – Platzhalter und Gruppenbezeichnungen erkennen und markieren
- **Config Export/Import** – Konfiguration als JSON sichern und auf anderen Geräten wiederverwenden

Alle Einstellungen werden im `localStorage` des Browsers gespeichert und bleiben beim nächsten Öffnen erhalten.

---

## Testdaten

[`testdaten.tsv`](https://raw.githubusercontent.com/braunle77/Meeting-Inspektor/main/testdaten.tsv) enthält 73 fiktive Meetings für einen Schnelltest ohne echte Daten.

---

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `meeting-inspektor.html` | Das Dashboard – die einzige Datei, die du brauchst |
| `testdaten.tsv` | Synthetische Testdaten (73 Meetings) |

Echte Quelldaten (`*.xlsx`, `*.csv`) sind in `.gitignore` ausgeschlossen und verbleiben lokal.
