# F001 – Flight-Levels-Tab quellentreu nach Klaus Leopold neu aufbauen

**Status:** Backlog – gegrillt, reviewt (Architektur + Security), bereit zur Umsetzung
**Quelle:** Leiv, 10./11.07.2026 · Entscheidungen: quellentreuer Neuaufbau · neutrale
Verteilung statt Pyramide · Kürzel-Standard + Klartext-Toggle
**Referenz:** `docs/research/flight-levels-originalquelle.md` (verbindlich) · Glossar

## Worum es geht

Der Flight-Levels-Tab entstand aus einer KI-Recherche ohne Quellentreue. Er wird um die
Original-Diagnostik des Modells herum neu aufgebaut: Konzepte, Schule und Methodik 1:1
nach Leopold/Kaltenecker. Tool-eigene Auswertungen sind zulässig, wenn ehrlich als solche
gekennzeichnet („Tool-Beobachtung, keine Flight-Levels-Aussage").

## Vollständiges Inventar & Ziel-Struktur

Rahmen: die drei Levels mit ihrer **offiziellen Leitfrage** (FL1 "Are you working
effectively on the right things?" · FL2 "How do teams work together toward common
goals?" · FL3 "Are you turning strategy into real-world results?").

### Block 3 – Render-Funktionen

| Alt | Neu |
|---|---|
| `_renderFLPyramide` + Trichterform + Norm „FL1 > FL2 > FL3" | **Neutrales Balkendiagramm „Verteilung je Flight Level"**; Funktion/IDs umbenennen (`_renderFLVerteilung`, `chart-fl-verteilung`, …). Klickbare Meeting-Liste je Level bleibt. Keine Form/Farbe, die eine Soll-Mengenrelation suggeriert. |
| `_renderFLMatrix` („Koordinations-Silos") | Bleibt, umbenannt/umgetextet: welche Abteilungspaare sind über FL2-Interaktionen verbunden (Anker: FL2 visualisiert den Wertstrom). Kennzeichnung: Tool-Beobachtung. |
| `_renderFLWirkung` + „Koordinationstheater" | Bleibt; neuer Anker **„result-neutral"** (Originalbegriff, siehe Glossar). „Koordinationstheater" entfällt ersatzlos (auch statisches HTML Z. ~548). |
| `_renderFLBrueckenkoepfe` + Heatmap | **People-as-Routers-Diagnose** (`_renderFLRouterDiagnose` o.ä.): Personen, über die viel ebenenübergreifender Informationsfluss läuft, als Hinweis auf Board-/Systemlücken. **Kürzel-Standard**, Toggle „Namen anzeigen" für die Arbeit mit dem Datenowner. Formulierungen diagnostizieren das System, nie die Person. Statisches HTML Z. ~550 („Wer ist Brückenkopf…") mit. |
| `_renderFLRhythmusMatrix` + „Frequenz-Mismatches" | Mismatch-Wertung **entfällt** (Modell verweigert Rhythmus-Vorgaben). Ersatz: neutrale Rhythmus-Übersicht je Level, gekennzeichnet als Tool-Beobachtung. |
| `_renderFLBriefing` (Kacheln, Z. ~4223–4345) | Kachel 1 (Koordinations-Lücken): bleibt, Text an Wertstrom-Anker. Kachel 2 (heute „Brückenkopf-Personen"/„Rollentrennung"): bleibt inhaltlich (Router-Anti-Pattern), neue Formulierung ohne erfundenes Vokabular, zählt weiterhin nur (keine Namen). Kachel 3 („Frequenz-Mismatches"): entfällt mit F5-Wertung; Ersatzkachel aus Original-Diagnostik (z.B. Anteil result-neutraler Kandidaten). Pyramiden-Norm-Ampel (Z. ~4231–4245) entfällt. |
| `_renderFLEinfuehrung` (Z. ~4718 „Die gesunde Pyramide") | Neu geschrieben aus dem Referenz-Report: Denkmodell-Charakter, fünf Kernaktivitäten, Leitfragen. |
| `_renderFLSchluesselFragen` – **sechs** Fragen Q1–Q6 | Q1 (kodiert „keine FL2 = Dysfunktionssignal", „FL2 ≥ FL3 = gute Basis"): neu auf Basis der offiziellen FL2-Leitfrage, ohne widerlegte Wertungen. Q3 („keine Brückenkopf-Personen = Fragmentierung"): **entfällt** (Ebenen verbindet die Systemarchitektur). Q4 (nutzt `FL_MISMATCH`): entfällt oder wird neutral neu gefasst – darf nach Wegfall von `FL_MISMATCH` nicht brechen. Q2/Q5/Q6: gegen Report prüfen, Wertungen nur mit Beleg. |

### Block 1 – blockübergreifende Fundorte (ADR 0002 beachten)

- `FL_MISMATCH`-Konstante (Z. ~708): entfällt; vorher verifiziert, dass nur FL-Funktionen
  sie nutzen (Review-Ergebnis: Z. 4269, 4632, 4656, 4867 – kein anderer Tab bricht)
- TAB_INFO-Eintrag `10:` (Z. ~1504–1507): „Brückenkopf-Heatmap" und „fehlende
  FL2-Meetings sind das häufigste Dysfunktionssignal" ersetzen – neu aus dem Report
  (fünf Kernaktivitäten, vier Schlüsselfragen, Leitfragen je Level)

### Statisches HTML

- Z. ~538 (Pyramiden-Norm-Hint), Z. ~548 („Koordinationstheater"), Z. ~550
  („Wer ist Brückenkopf zwischen den Ebenen?") – alle drei ersetzen

## Leitplanken

- Referenz-Report ist bindend; bei Konflikt gewinnt die Originalquelle
- **Escaping-Pflicht (Security-Review):** Jede aus der Urliste stammende Zeichenkette
  (Person/Kürzel, Abteilung, Meetingname, Zweck) läuft in den neu geschriebenen Sektionen
  durch `escapeHtml` – auch in Plotly `text`/`hovertemplate`-Inhalten. Ausnahme gemäß
  bindender Repo-Regel: `escapeHtml` nie auf Daten-Schlüssel (Plotly-Achsen-Kategorien,
  Lookup-Keys) anwenden. Die Q-Karten escapen korrekt – beim Neuschreiben erhalten
- Safari-Regeln (ADR 0002): keine nested Template-Literals, keine „…"-Quotes in JS
  (Bestandscode Z. ~4880 verletzt das bereits – nicht kopieren)
- ADR 0003: reine Diagnostik; Auto-Klassifikation bleibt als gekennzeichnete Heuristik
- Status- vs. Identitätsfarben strikt trennen (FL-Farben sind Identität)
- Screenshots/Test-Nachweise für PRs ausschließlich aus `testdaten.tsv`
- Branch-Workflow: feat-Branch + PR, kein Direkt-Commit auf main

## Akzeptanzkriterien

- [ ] Kein „Brückenkopf", kein „Koordinationstheater", keine Rhythmus-Mismatch-Wertung,
      keine Pyramiden-Norm mehr – weder in UI-Texten noch in Bezeichnern (inkl.
      `_renderFLPyramide`-Familie, statisches HTML, TAB_INFO, Q1/Q4)
- [ ] Alle sechs Q-Karten adressiert: jede verbleibende Wertung quellenbelegt oder als
      Tool-Beobachtung gekennzeichnet; Q3 entfernt; nichts referenziert `FL_MISMATCH`
- [ ] Router-Diagnose: Kürzel-Standard, Klartext-Toggle, systemdiagnostizierende Texte
- [ ] Escaping-Kriterium erfüllt (alle Urliste-Strings in neuen Sektionen escaped)
- [ ] Leitfragen je Level und „result-neutral" stammen wörtlich/sinngetreu aus der Quelle
- [ ] Glossar und Report bleiben konsistent zum Tab
