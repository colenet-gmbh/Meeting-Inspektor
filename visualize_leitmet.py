"""
visualize_leitmet.py
Erzeugt das interaktive HTML-Dashboard aus leitmet_clean.json

Aufruf:
    python3 visualize_leitmet.py
"""

import json
import math
import re
from pathlib import Path
from collections import Counter, defaultdict

import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

INPUT  = Path(__file__).parent / "leitmet_clean.json"
OUTPUT = Path(__file__).parent / "leitmet_dashboard.html"

# ---------------------------------------------------------------------------
# Farben
# ---------------------------------------------------------------------------
ABT_FARBEN = {
    "PC":        "#1f77b4",
    "PCO":       "#ff7f0e",
    "PCT":       "#2ca02c",
    "PCTAC/DC":  "#17becf",
    "PCTProduct":"#bcbd22",
    "PCTDC":     "#9467bd",
    "PCC":       "#d62728",
    "PCS":       "#8c564b",
    "unbekannt": "#7f7f7f",
}
KAT_FARBEN = {
    "Jour Fixe":           "#4e79a7",
    "Einzelgespräch":      "#f28e2b",
    "Teammeeting":         "#59a14f",
    "Regeltermin / Review":"#e15759",
    "Sprint Review":       "#76b7b2",
    "Weekly / Update":     "#edc948",
    "Sitzung":             "#b07aa1",
    "Sonstiges":           "#aecde8",
}
RHY_FARBEN = {
    "täglich":         "#d62728",
    "wöchentlich":     "#1f77b4",
    "dreiwöchentlich": "#17becf",
    "zweiwöchentlich": "#2ca02c",
    "monatlich":       "#ff7f0e",
    "quartalsweise":   "#9467bd",
    "variabel":        "#7f7f7f",
}
FREQ_GEWICHT = {
    "täglich": 5, "wöchentlich": 4, "dreiwöchentlich": 3,
    "zweiwöchentlich": 2, "monatlich": 1, "quartalsweise": 0.5, "variabel": 0.5,
}

# ---------------------------------------------------------------------------
# Daten laden
# ---------------------------------------------------------------------------
with open(INPUT, encoding="utf-8") as f:
    meetings = json.load(f)

aktive = [m for m in meetings if m["status"] == "Aktiv"]

# ---------------------------------------------------------------------------
# Hilfsfunktion: Plotly-Figure → HTML-div (ohne plotly.js)
# ---------------------------------------------------------------------------
def fig_to_div(fig):
    return pio.to_html(fig, full_html=False, include_plotlyjs=False,
                       config={"displayModeBar": True, "responsive": True})

# ===========================================================================
# VIEW 1: Netzwerk-Diagramm
# ===========================================================================
def build_network():
    G = nx.Graph()

    # Personen-Knoten
    alle_personen = set()
    for m in aktive:
        for t in m["teilnehmer"]:
            alle_personen.add(t)

    for p in alle_personen:
        G.add_node(p)

    # Kanten: je Meeting eine Kante zwischen allen Teilnehmerpaaren
    for m in aktive:
        t = [x for x in m["teilnehmer"] if x in alle_personen]
        gewicht = FREQ_GEWICHT.get(m["rhythmus_klasse"], 0.5)
        for i in range(len(t)):
            for j in range(i + 1, len(t)):
                a, b = t[i], t[j]
                if G.has_edge(a, b):
                    G[a][b]["weight"] += gewicht
                    G[a][b]["meetings"].append(m["name"])
                else:
                    G.add_edge(a, b, weight=gewicht, meetings=[m["name"]])

    # Layout
    pos = nx.spring_layout(G, k=2.2, seed=42, weight="weight")

    # Abteilungszuordnung für Knotenfarbe
    PERSON_ABT = {
        "Jco": "PC",  "MiG": "PC",  "Ktz": "PC",  "Sez": "PC",
        "Bre": "PC",  "DrS": "PC",  "Zeller": "PC",
        "Beb": "PCO", "Fln": "PCO", "Ipa": "PCO", "Zes": "PCO", "LeB": "PCO",
        "Kip": "PCT", "Krö": "PCT", "Kis": "PCT", "Wud": "PCT", "Bra": "PCT",
        "Kih": "PCT", "FMD": "PCT", "Tih": "PCT", "SMI": "PCT",
        "Dem": "PCT", "Bas": "PCT", "CST": "PCT", "Dni": "PCT",
        "HeT": "PCT", "Fef": "PCT",
        "TOK": "PCC", "ADA": "PCC", "JFR": "PCC", "MGR": "PCC",
        "MOS": "PCC", "AWA": "PCC",
        "Urk": "PCS", "Zrb": "PCS", "Smt": "PCS", "KTF": "PCS",
    }

    # Kanten-Traces
    edge_traces = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        w = min(data["weight"], 10)
        meetings_str = "<br>".join(data["meetings"][:5])
        if len(data["meetings"]) > 5:
            meetings_str += f"<br>... (+{len(data['meetings'])-5} weitere)"
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=w * 0.6 + 0.5, color="rgba(150,150,150,0.4)"),
            hoverinfo="text",
            text=f"{u} ↔ {v}<br>Meetings: {meetings_str}",
            showlegend=False,
        ))

    # Knoten-Traces (gruppiert nach Abteilung für Legende)
    abt_gruppen = defaultdict(list)
    for p in G.nodes():
        abt = PERSON_ABT.get(p, "unbekannt")
        abt_gruppen[abt].append(p)

    node_traces = []
    for abt, personen in sorted(abt_gruppen.items()):
        xs = [pos[p][0] for p in personen]
        ys = [pos[p][1] for p in personen]
        # Knotengrad für Größe
        sizes = [8 + G.degree(p) * 2.5 for p in personen]
        # Hover-Text
        hover = []
        for p in personen:
            m_namen = sorted({m["name"] for m in aktive if p in m["teilnehmer"]})
            hover.append(
                f"<b>{p}</b> ({abt})<br>"
                f"Meetings ({len(m_namen)}): "
                + ", ".join(m_namen[:6])
                + ("..." if len(m_namen) > 6 else "")
            )
        node_traces.append(go.Scatter(
            x=xs, y=ys,
            mode="markers+text",
            text=personen,
            textposition="top center",
            textfont=dict(size=9),
            marker=dict(
                size=sizes,
                color=ABT_FARBEN.get(abt, "#7f7f7f"),
                line=dict(width=1, color="white"),
            ),
            name=abt,
            hovertext=hover,
            hoverinfo="text",
        ))

    fig = go.Figure(data=edge_traces + node_traces)
    fig.update_layout(
        title="Kommunikationsnetzwerk – Wer trifft wen?",
        title_font_size=16,
        showlegend=True,
        legend=dict(title="Abteilung", itemsizing="constant"),
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="white",
        height=620,
        margin=dict(l=20, r=20, t=50, b=20),
        annotations=[dict(
            text="Knotengröße = Anzahl Meetings · Liniendicke = Frequenz",
            xref="paper", yref="paper", x=0, y=-0.02,
            showarrow=False, font=dict(size=10, color="gray")
        )],
    )
    return fig

# ===========================================================================
# VIEW 2: Rhythmus-Kalender (Bubble-Chart: Wochentag × Rhythmus-Klasse)
# ===========================================================================
def build_kalender():
    tage_order  = ["Mo", "Di", "Mi", "Do", "Fr", "—"]
    rhy_order   = ["täglich", "wöchentlich", "dreiwöchentlich",
                   "zweiwöchentlich", "monatlich", "quartalsweise", "variabel"]

    rows = []
    for m in aktive:
        tage = m["wochentage"] if m["wochentage"] else ["—"]
        for tag in tage:
            rows.append({
                "tag":      tag,
                "rhythmus": m["rhythmus_klasse"],
                "name":     m["name"],
                "abt":      m["abteilung"],
                "kategorie":m["kategorie"],
                "platzh":   "⚠ Platzhalter" if m["ist_platzhalter"] else "",
            })

    # Aggregieren
    agg = defaultdict(list)
    for r in rows:
        agg[(r["tag"], r["rhythmus"])].append(r["name"])

    xs, ys, sizes, texts, hovers, colors = [], [], [], [], [], []
    for (tag, rhy), namen in agg.items():
        xs.append(tag)
        ys.append(rhy)
        sizes.append(12 + len(namen) * 14)
        texts.append(str(len(namen)))
        hovers.append(f"<b>{tag} / {rhy}</b><br>" + "<br>".join(namen))
        colors.append(RHY_FARBEN.get(rhy, "#aaa"))

    fig = go.Figure(go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        text=texts,
        textfont=dict(size=11, color="white"),
        marker=dict(size=sizes, color=colors, sizemode="diameter",
                    line=dict(width=1, color="white")),
        hovertext=hovers,
        hoverinfo="text",
    ))
    fig.update_layout(
        title="Meeting-Kalender – Wann findet was statt?",
        title_font_size=16,
        xaxis=dict(title="Wochentag", categoryorder="array",
                   categoryarray=tage_order),
        yaxis=dict(title="Rhythmus", categoryorder="array",
                   categoryarray=list(reversed(rhy_order))),
        plot_bgcolor="white",
        height=480,
        margin=dict(l=140, r=20, t=50, b=60),
        annotations=[dict(
            text="Zahl = Anzahl Meetings an diesem Tag / in diesem Rhythmus",
            xref="paper", yref="paper", x=0, y=-0.13,
            showarrow=False, font=dict(size=10, color="gray")
        )],
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eee")
    fig.update_yaxes(showgrid=True, gridcolor="#eee")
    return fig

# ===========================================================================
# VIEW 3: Teilnehmer-Overlap-Heatmap
# ===========================================================================
def build_overlap():
    # Nur Meetings mit bekannten Teilnehmern
    m_gefiltert = [m for m in aktive if len(m["teilnehmer"]) >= 2]
    namen = [m["name"] for m in m_gefiltert]
    sets  = [set(m["teilnehmer"]) for m in m_gefiltert]
    n     = len(m_gefiltert)

    matrix = []
    for i in range(n):
        zeile = []
        for j in range(n):
            if i == j:
                zeile.append(1.0)
            elif not sets[i] or not sets[j]:
                zeile.append(0.0)
            else:
                jaccard = len(sets[i] & sets[j]) / len(sets[i] | sets[j])
                zeile.append(round(jaccard, 2))
        matrix.append(zeile)

    # Hover-Text
    hover = []
    for i in range(n):
        zeile = []
        for j in range(n):
            gemeinsam = sets[i] & sets[j]
            zeile.append(
                f"<b>{namen[i]}</b><br>vs.<br><b>{namen[j]}</b><br>"
                f"Ähnlichkeit: {matrix[i][j]:.0%}<br>"
                f"Gemeinsame Teilnehmer: {', '.join(sorted(gemeinsam)) or '–'}"
            )
        hover.append(zeile)

    fig = go.Figure(go.Heatmap(
        z=matrix, x=namen, y=namen,
        text=[[f"{v:.0%}" if v > 0 else "" for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont=dict(size=8),
        colorscale="RdYlGn_r",
        zmin=0, zmax=1,
        hovertext=hover,
        hoverinfo="text",
        colorbar=dict(title="Jaccard-<br>Ähnlichkeit"),
    ))
    fig.update_layout(
        title="Teilnehmer-Überschneidung – Welche Meetings sind ähnlich?",
        title_font_size=16,
        height=700,
        margin=dict(l=200, r=100, t=60, b=200),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=9)),
        annotations=[dict(
            text="Rot = hohe Überschneidung (potenzielle Redundanz) · Grün = keine Überschneidung",
            xref="paper", yref="paper", x=0, y=-0.28,
            showarrow=False, font=dict(size=10, color="gray")
        )],
    )
    return fig

# ===========================================================================
# VIEW 4: Abteilungs-Übersicht (gestapelter Balken nach Rhythmus)
# ===========================================================================
def build_abteilung():
    abt_order = ["PC", "PCO", "PCT", "PCTAC/DC", "PCTProduct", "PCTDC", "PCC", "PCS"]
    rhy_order = ["täglich", "wöchentlich", "dreiwöchentlich",
                 "zweiwöchentlich", "monatlich", "quartalsweise", "variabel"]

    # Daten aufbereiten
    abt_rhy = defaultdict(lambda: defaultdict(list))
    for m in aktive:
        abt_rhy[m["abteilung"]][m["rhythmus_klasse"]].append(m["name"])

    traces = []
    for rhy in rhy_order:
        ys    = []
        hover = []
        for abt in abt_order:
            m_namen = abt_rhy[abt][rhy]
            ys.append(len(m_namen))
            hover.append(f"<b>{abt} / {rhy}</b><br>" + ("<br>".join(m_namen) if m_namen else "–"))
        traces.append(go.Bar(
            name=rhy, x=abt_order, y=ys,
            marker_color=RHY_FARBEN.get(rhy, "#aaa"),
            hovertext=hover, hoverinfo="text",
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        barmode="stack",
        title="Meeting-Dichte pro Abteilung",
        title_font_size=16,
        xaxis_title="Abteilung",
        yaxis_title="Anzahl Meetings",
        legend_title="Rhythmus",
        plot_bgcolor="white",
        height=450,
        margin=dict(l=60, r=20, t=60, b=60),
    )
    fig.update_yaxes(showgrid=True, gridcolor="#eee")
    return fig

# ===========================================================================
# VIEW 5: Informationsfluss-Sankey
# ===========================================================================
def build_sankey():
    # Meetings mit Abteilungs-Zuordnung der Teilnehmer
    PERSON_ABT = {
        "Jco": "PC",  "MiG": "PC",  "Ktz": "PC",  "Sez": "PC",
        "Bre": "PC",  "DrS": "PC",  "Zeller": "PC",
        "Beb": "PCO", "Fln": "PCO", "Ipa": "PCO", "Zes": "PCO", "LeB": "PCO",
        "Kip": "PCT", "Krö": "PCT", "Kis": "PCT", "Wud": "PCT", "Bra": "PCT",
        "Kih": "PCT", "FMD": "PCT", "Tih": "PCT", "SMI": "PCT",
        "Dem": "PCT", "Bas": "PCT", "CST": "PCT", "Dni": "PCT",
        "HeT": "PCT", "Fef": "PCT",
        "TOK": "PCC", "ADA": "PCC", "JFR": "PCC", "MGR": "PCC",
        "MOS": "PCC", "AWA": "PCC",
        "Urk": "PCS", "Zrb": "PCS", "Smt": "PCS", "KTF": "PCS",
    }

    abt_list = ["PC", "PCO", "PCT", "PCC", "PCS", "Extern"]
    abt_idx  = {a: i for i, a in enumerate(abt_list)}

    fluss = defaultdict(float)
    for m in aktive:
        # Nur übergreifende Meetings
        abts_im_meeting = set()
        for t in m["teilnehmer"]:
            abt = PERSON_ABT.get(t, None)
            if abt:
                abts_im_meeting.add(abt)
        if "Extern" in (m["teilnehmer_raw"] or "").lower() or \
           any(t.lower() == "extern" for t in m["teilnehmer"]):
            abts_im_meeting.add("Extern")

        abts_im_meeting.add(m["abteilung"].split("/")[0].replace("PCT", "PCT").replace("PCTProduct", "PCT").replace("PCTDC", "PCT").replace("PCTAC/DC", "PCT"))

        abts_liste = sorted(abts_im_meeting & set(abt_list))
        gewicht    = FREQ_GEWICHT.get(m["rhythmus_klasse"], 0.5)
        # Bidirektionaler Fluss zwischen allen Abt-Paaren
        for i in range(len(abts_liste)):
            for j in range(i + 1, len(abts_liste)):
                a, b = abts_liste[i], abts_liste[j]
                key = (a, b) if a < b else (b, a)
                fluss[key] += gewicht

    sources, targets, values, labels_hover = [], [], [], []
    for (a, b), v in fluss.items():
        sources.append(abt_idx[a])
        targets.append(abt_idx[b])
        values.append(round(v, 1))
        labels_hover.append(f"{a} ↔ {b}: {v:.1f} Freq.-Punkte")

    node_colors = [ABT_FARBEN.get(a, "#aaa") for a in abt_list]

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=20, thickness=20,
            line=dict(color="white", width=0.5),
            label=abt_list,
            color=node_colors,
            hovertemplate="%{label}<extra></extra>",
        ),
        link=dict(
            source=sources, target=targets, value=values,
            customdata=labels_hover,
            hovertemplate="%{customdata}<extra></extra>",
            color="rgba(180,180,180,0.4)",
        ),
    ))
    fig.update_layout(
        title="Informationsfluss zwischen Abteilungen<br>"
              "<sup>Flussdicke = gewichtete Meeting-Frequenz</sup>",
        title_font_size=16,
        height=450,
        margin=dict(l=20, r=20, t=70, b=40),
    )
    return fig

# ===========================================================================
# VIEW 6: Interaktive Tabelle
# ===========================================================================
def build_tabelle():
    zeilen = []
    for m in meetings:  # alle, inkl. Geplant
        platzh = "⚠" if m["ist_platzhalter"] else ""
        abt_ug = "✓" if m["abteilungsuebergreifend"] else ""
        zeilen.append({
            "Abteilung":   m["abteilung"],
            "Meeting":     m["name"],
            "Kategorie":   m["kategorie"],
            "Rhythmus":    m["rhythmus_klasse"],
            "Verantwortl.": m["verantwortlich"] or "–",
            "Teilnehmer":  ", ".join(m["teilnehmer"]) or m.get("teilnehmer_raw") or "–",
            "Status":      m["status"],
            "Übergreif.":  abt_ug,
            "Platzh.":     platzh,
            "Zweck":       (m["zweck"] or "–")[:120],
            "Learnings":   m["learning"] or "–",
        })

    cols = ["Abteilung", "Meeting", "Kategorie", "Rhythmus", "Verantwortl.",
            "Teilnehmer", "Status", "Übergreif.", "Platzh.", "Zweck", "Learnings"]
    col_widths = [70, 200, 120, 110, 90, 200, 60, 75, 60, 280, 260]

    fig = go.Figure(go.Table(
        header=dict(
            values=[f"<b>{c}</b>" for c in cols],
            fill_color="#2c3e50",
            font=dict(color="white", size=11),
            align="left",
            height=32,
        ),
        cells=dict(
            values=[[r[c] for r in zeilen] for c in cols],
            fill_color=[
                ["#f0f4f8" if i % 2 == 0 else "white" for i in range(len(zeilen))]
            ] * len(cols),
            align="left",
            font=dict(size=10),
            height=28,
        ),
        columnwidth=col_widths,
    ))
    fig.update_layout(
        title="Alle Meetings im Überblick",
        title_font_size=16,
        height=max(500, 50 + len(zeilen) * 30),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig

# ===========================================================================
# Dashboard zusammenbauen
# ===========================================================================
print("🔨 Erzeuge Charts...")
fig_netz    = build_network()
fig_kal     = build_kalender()
fig_overlap = build_overlap()
fig_abt     = build_abteilung()
fig_sankey  = build_sankey()
fig_tabelle = build_tabelle()
print("   ✓ Alle 6 Charts erzeugt")

div_netz    = fig_to_div(fig_netz)
div_kal     = fig_to_div(fig_kal)
div_overlap = fig_to_div(fig_overlap)
div_abt     = fig_to_div(fig_abt)
div_sankey  = fig_to_div(fig_sankey)
div_tabelle = fig_to_div(fig_tabelle)

# Datenqualitäts-Warnungen
n_platzh = sum(1 for m in meetings if m["ist_platzhalter"])
n_ohne_info = sum(1 for m in meetings if not m["infofluss"])
n_geplant = sum(1 for m in meetings if m["status"] == "Geplant")
warnungen = []
if n_platzh:
    warnungen.append(
        f"<b>{n_platzh} Meetings</b> haben unvollständige Teilnehmer-Angaben (Platzhalter ⚠). "
        "Diese erscheinen im Netzwerk-Diagramm nicht mit allen Verbindungen."
    )
if n_ohne_info:
    warnungen.append(
        f"<b>{n_ohne_info} Meetings</b> ohne Informationsfluss-Dokumentation – "
        "Nachpflege in der Quelltabelle empfohlen."
    )
if n_geplant:
    warnungen.append(
        f"<b>{n_geplant} Meeting</b> ist noch im Status 'Geplant' und noch nicht aktiv."
    )

warn_html = "".join(f'<li>{w}</li>' for w in warnungen)

# Statistik-Kacheln
n_aktiv    = sum(1 for m in meetings if m["status"] == "Aktiv")
n_uebergr  = sum(1 for m in meetings if m["abteilungsuebergreifend"])
n_einzel   = sum(1 for m in meetings if m["kategorie"] == "Einzelgespräch")
n_woech    = sum(1 for m in meetings if m["rhythmus_klasse"] == "wöchentlich")

html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Organisations-Meeting-Informationsfluss</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #f5f6fa; color: #2c3e50; }}

  .header {{ background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
             color: white; padding: 28px 40px; }}
  .header h1 {{ font-size: 1.6rem; font-weight: 700; margin-bottom: 4px; }}
  .header p  {{ opacity: 0.85; font-size: 0.9rem; }}

  .kacheln {{ display: flex; gap: 16px; padding: 20px 40px;
              flex-wrap: wrap; }}
  .kachel {{ background: white; border-radius: 8px; padding: 16px 22px;
             box-shadow: 0 1px 6px rgba(0,0,0,.08); min-width: 140px;
             flex: 1; text-align: center; }}
  .kachel .zahl {{ font-size: 2rem; font-weight: 700; color: #3498db; }}
  .kachel .label {{ font-size: 0.8rem; color: #666; margin-top: 2px; }}

  .tabs {{ display: flex; gap: 4px; padding: 0 40px;
           border-bottom: 2px solid #ddd; background: #f5f6fa; }}
  .tab  {{ padding: 10px 18px; cursor: pointer; font-size: 0.88rem;
           border: none; background: none; color: #555; font-weight: 500;
           border-bottom: 3px solid transparent; margin-bottom: -2px;
           transition: all .15s; }}
  .tab:hover  {{ color: #3498db; }}
  .tab.aktiv  {{ color: #3498db; border-bottom-color: #3498db; }}

  .panel {{ display: none; padding: 24px 40px; }}
  .panel.aktiv {{ display: block; }}

  .chart-box {{ background: white; border-radius: 8px; padding: 16px;
                box-shadow: 0 1px 6px rgba(0,0,0,.08); }}
  .chart-hint {{ font-size: 0.82rem; color: #888; margin-top: 8px; }}

  .warnungen {{ margin: 0 40px 16px; background: #fff8e1; border-left: 4px solid #f39c12;
                border-radius: 4px; padding: 12px 16px; font-size: 0.85rem; }}
  .warnungen h3 {{ font-size: 0.9rem; margin-bottom: 6px; color: #e67e22; }}
  .warnungen li {{ margin-left: 16px; margin-bottom: 4px; }}

  .footer {{ text-align: center; padding: 24px; font-size: 0.78rem; color: #aaa; }}
</style>
</head>
<body>

<div class="header">
  <h1>Organisations-Meeting &amp; Informationsfluss</h1>
  <p>Interaktives Dashboard · Stand: 26.05.2026 · Quelle: LeitMet.xlsx</p>
</div>

<div class="kacheln">
  <div class="kachel"><div class="zahl">{n_aktiv}</div><div class="label">Aktive Meetings</div></div>
  <div class="kachel"><div class="zahl">{n_woech}</div><div class="label">Wöchentlich</div></div>
  <div class="kachel"><div class="zahl">{n_uebergr}</div><div class="label">Abteilungsübergreifend</div></div>
  <div class="kachel"><div class="zahl">{n_einzel}</div><div class="label">Einzelgespräche</div></div>
  <div class="kachel"><div class="zahl">{n_platzh}</div><div class="label">⚠ Platzhalter</div></div>
</div>

{"<div class='warnungen'><h3>⚠ Datenqualitäts-Hinweise</h3><ul>" + warn_html + "</ul></div>" if warnungen else ""}

<div class="tabs">
  <button class="tab aktiv" onclick="zeigTab(0)">🕸 Netzwerk</button>
  <button class="tab" onclick="zeigTab(1)">📅 Kalender</button>
  <button class="tab" onclick="zeigTab(2)">🔴 Überschneidungen</button>
  <button class="tab" onclick="zeigTab(3)">📊 Abteilungen</button>
  <button class="tab" onclick="zeigTab(4)">🌊 Informationsfluss</button>
  <button class="tab" onclick="zeigTab(5)">📋 Alle Meetings</button>
</div>

<div id="panel-0" class="panel aktiv">
  <div class="chart-box">{div_netz}</div>
  <p class="chart-hint">💡 Klicke auf einen Namen oder eine Verbindungslinie, um Details zu sehen. Knotengröße = Anzahl Meetings. Liniendicke = Frequenz-Gewicht.</p>
</div>
<div id="panel-1" class="panel">
  <div class="chart-box">{div_kal}</div>
  <p class="chart-hint">💡 Blasengröße = Anzahl Meetings an diesem Tag/Rhythmus. Hover für Meeting-Namen.</p>
</div>
<div id="panel-2" class="panel">
  <div class="chart-box">{div_overlap}</div>
  <p class="chart-hint">💡 Rote Felder = hohe Teilnehmer-Überschneidung = potenzielle Redundanz. Grüne Felder = keine gemeinsamen Teilnehmer.</p>
</div>
<div id="panel-3" class="panel">
  <div class="chart-box">{div_abt}</div>
  <p class="chart-hint">💡 Gestapelte Balken zeigen die Rhythmus-Verteilung pro Abteilung. Hover für Meeting-Namen.</p>
</div>
<div id="panel-4" class="panel">
  <div class="chart-box">{div_sankey}</div>
  <p class="chart-hint">💡 Flussdicke = gewichtete Meeting-Frequenz zwischen Abteilungen. Nur aktive, abteilungsübergreifende Meetings.</p>
</div>
<div id="panel-5" class="panel">
  <div class="chart-box">{div_tabelle}</div>
  <p class="chart-hint">💡 ✓ = abteilungsübergreifend · ⚠ = unvollständige Teilnehmer-Angabe</p>
</div>

<div class="footer">
  Erstellt mit Claude Code · Colenet · {len(meetings)} Meetings · Daten: LeitMet.xlsx (vertraulich, lokal)
</div>

<script>
function zeigTab(idx) {{
  document.querySelectorAll(".tab").forEach((t, i) => {{
    t.classList.toggle("aktiv", i === idx);
  }});
  document.querySelectorAll(".panel").forEach((p, i) => {{
    p.classList.toggle("aktiv", i === idx);
  }});
  // Plotly neu rendern (für korrekte Größe nach Tab-Wechsel)
  var plots = document.getElementById("panel-" + idx).querySelectorAll(".plotly-graph-div");
  plots.forEach(function(p) {{ Plotly.relayout(p, {{}}); }});
}}
</script>
</body>
</html>"""

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Dashboard gespeichert → {OUTPUT}")
print(f"   Öffne mit: open '{OUTPUT}'")
