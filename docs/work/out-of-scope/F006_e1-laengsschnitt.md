# F006 – E1: Längsschnitt (mehrere Zeitpunkte)

**Status:** Out of scope (bewusst zurückgestellt, Stand 10.07.2026)

## Worum es geht

Die Meeting-Landschaft über mehrere Erhebungszeitpunkte vergleichen (Feature-Idee E1) –
Entwicklung sichtbar statt nur Momentaufnahme.

## Warum zurückgestellt

Braucht eine eigene Architektur für die Verwaltung mehrerer Urlisten-Stände (Speicherung,
Abgleich, Versionierung) und kollidiert mit dem aktuellen Modell „eine Urliste, ein
Zustand" (ADR 0003, localStorage-Konfiguration). Kein Anbau ans bestehende Tool – wenn,
dann als bewusst geplanter Ausbau.
