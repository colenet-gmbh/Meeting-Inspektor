"""
dashboard_erstellen.py  –  Meeting Strukturanalyse
Erzeugt das interaktive, vollständig offline-fähige HTML-Dashboard

Aufruf:
    python3 dashboard_erstellen.py
"""

import json, re
from pathlib import Path
from collections import defaultdict
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio

INPUT  = Path(__file__).parent / "meetings_bereinigt.json"
OUTPUT = Path(__file__).parent / "meeting_strukturanalyse.html"

# ── Personen-Mapping ────────────────────────────────────────────────────────
PERSON_ABT = {
    "Jco":"PC","MiG":"PC","Ktz":"PC","Lav":"PC","Rls":"PC",
    "Sez":"PC","Bre":"PC","DrS":"PC","Zeller":"PC",
    "Beb":"PCO","Ipa":"PCO","Fln":"PCO","Zes":"PCO","LeB":"PCO",
    "Kip":"PCT","Kis":"PCT","Rre":"PCT","Lic":"PCT","Leo":"PCT","Gam":"PCT","Ran":"PCT",
    "Krö":"PCT","Dem":"PCT","Bas":"PCT","CST":"PCT",
    "Dni":"PCT","Bra":"PCT","Fef":"PCT","FMD":"PCT","Wud":"PCT","Kih":"PCT","HeT":"PCT",
    "TOK":"PCC","ADA":"PCC","JFR":"PCC","SMI":"PCC","MGR":"PCC","MOS":"PCC","AWA":"PCC",
    "Urk":"PCS","Zrb":"PCS","Smt":"PCS","KTF":"PCS","Arg":"PCS","Lke":"PCS","Tih":"PCS","Laa":"PCS",
}
PERSON_SUBTEAM = {
    "Kis":"AC","Rre":"AC","Lic":"AC","Leo":"AC","Gam":"AC","Ran":"AC",
    "Krö":"DC","Dem":"DC","Bas":"DC","CST":"DC",
    "Dni":"PC Products","Bra":"PC Products","Fef":"PC Products",
    "FMD":"PC Products","Wud":"PC Products","Kih":"PC Products","HeT":"PC Products",
    "Kip":"PCT Leitung",
}
# Nur tatsächliche Führungskräfte (laut Organigramm, blau markiert), alphabetisch
FK_LIST = ["Beb","Jco","Kip","Ktz","MiG","TOK","Urk"]

ABT_FARBEN = {
    "PC":"#2563eb","PCO":"#f59e0b","PCT":"#16a34a",
    "PCC":"#dc2626","PCS":"#7c3aed","unbekannt":"#9ca3af",
}
RHY_FARBEN = {
    "täglich":"#dc2626","wöchentlich":"#2563eb","dreiwöchentlich":"#0891b2",
    "zweiwöchentlich":"#16a34a","monatlich":"#f59e0b","quartalsweise":"#7c3aed","variabel":"#9ca3af",
}
FREQ_W = {"täglich":5,"wöchentlich":4,"dreiwöchentlich":3,
          "zweiwöchentlich":2,"monatlich":1,"quartalsweise":0.5,"variabel":0.5}

# ── Daten ────────────────────────────────────────────────────────────────────
with open(INPUT, encoding="utf-8") as f:
    meetings = json.load(f)
aktive = [m for m in meetings if m["status"] == "Aktiv"]

def fig_div(fig):
    # include_plotlyjs=False → Plotly wird einmal global eingebunden (s. HTML-Template)
    return pio.to_html(fig, full_html=False, include_plotlyjs=False,
                       config={"responsive":True,"displayModeBar":True})

# ── VIEW 1: Netzwerk ─────────────────────────────────────────────────────────
def build_network():
    G = nx.Graph()
    for m in aktive:
        for t in m["teilnehmer"]:
            if t in PERSON_ABT:
                G.add_node(t)
    for m in aktive:
        knoten = [t for t in m["teilnehmer"] if t in PERSON_ABT]
        w = FREQ_W.get(m["rhythmus_klasse"], 0.5)
        for i in range(len(knoten)):
            for j in range(i+1, len(knoten)):
                a,b = knoten[i], knoten[j]
                if G.has_edge(a,b):
                    G[a][b]["weight"] += w
                    G[a][b]["meetings"].append(m["name"])
                else:
                    G.add_edge(a,b,weight=w,meetings=[m["name"]])

    pos = nx.spring_layout(G, k=2.5, seed=42, weight="weight")
    persons = list(G.nodes())
    edges   = list(G.edges())

    # Kanten-Traces (eine pro Paar)
    edge_traces = []
    for u,v in edges:
        x0,y0 = pos[u]; x1,y1 = pos[v]
        w = min(G[u][v]["weight"],10)
        mn = "<br>".join(G[u][v]["meetings"][:5])
        edge_traces.append(go.Scatter(
            x=[x0,x1,None], y=[y0,y1,None], mode="lines",
            line=dict(width=w*0.5+0.3, color="rgba(156,163,175,0.45)"),
            hovertext=f"<b>{u} ↔ {v}</b><br>{mn}",
            hoverinfo="text", showlegend=False, opacity=1.0,
        ))

    # Knoten-Traces (eine pro Person, für präzise Filter-Kontrolle)
    node_traces = []
    for p in persons:
        abt  = PERSON_ABT.get(p,"unbekannt")
        sub  = PERSON_SUBTEAM.get(p,"")
        deg  = G.degree(p)
        mn   = sorted({m["name"] for m in aktive if p in m["teilnehmer"]})
        hover = (f"<b>{p}</b> · {abt}{' / '+sub if sub else ''}<br>"
                 f"Meetings ({len(mn)}): " + ", ".join(mn[:6]) + ("…" if len(mn)>6 else ""))
        is_fk = p in FK_LIST
        node_traces.append(go.Scatter(
            x=[pos[p][0]], y=[pos[p][1]],
            mode="markers+text",
            text=[p], textposition="top center",
            textfont=dict(size=9, color="#374151"),
            marker=dict(
                size=10+deg*2.8,
                color=ABT_FARBEN.get(abt,"#9ca3af"),
                symbol="star" if is_fk else "circle",
                line=dict(width=2 if is_fk else 1, color="white"),
                opacity=1.0,
            ),
            name=p, hovertext=hover, hoverinfo="text",
            showlegend=False, opacity=1.0,
        ))

    # Updatemenus: eine Schaltfläche pro FK + "Alle"
    n_edge = len(edge_traces)
    n_node = len(node_traces)

    def make_ops(fk):
        nbrs = set(G.neighbors(fk)) | {fk}
        e_ops = [0.7 if fk in (u,v) else 0.04 for u,v in edges]
        n_ops = [1.0 if p in nbrs else 0.08 for p in persons]
        return e_ops + n_ops

    alle_ops = [1.0]*(n_edge+n_node)
    buttons = [dict(label="Alle", method="restyle", args=[{"opacity": alle_ops}])]
    for fk in FK_LIST:
        if fk in G:
            buttons.append(dict(label=fk, method="restyle", args=[{"opacity": make_ops(fk)}]))

    # Legende: eine Dummy-Trace pro Abteilung
    legend_traces = []
    shown = set()
    for p in persons:
        abt = PERSON_ABT.get(p,"unbekannt")
        if abt not in shown:
            shown.add(abt)
            legend_traces.append(go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(size=12, color=ABT_FARBEN.get(abt,"#9ca3af")),
                name=abt, showlegend=True,
            ))

    all_traces = edge_traces + node_traces + legend_traces

    fig = go.Figure(data=all_traces)
    fig.update_layout(
        title=dict(text="Kommunikationsnetzwerk – Wer trifft wen?", font=dict(size=16,family="Inter")),
        updatemenus=[dict(
            type="dropdown", direction="down",
            x=0.01, xanchor="left", y=1.12, yanchor="top",
            bgcolor="white", bordercolor="#e5e7eb", font=dict(size=12),
            buttons=buttons,
            active=0,
            pad={"r":10,"t":5},
        )],
        annotations=[dict(
            text="<b>Personen-Filter:</b>", x=0.01, xanchor="left",
            y=1.15, yanchor="top", xref="paper", yref="paper",
            showarrow=False, font=dict(size=11,color="#6b7280"),
        )],
        showlegend=True,
        legend=dict(title="Abteilung", itemsizing="constant", x=1.01, y=1),
        hovermode="closest",
        xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
        yaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
        plot_bgcolor="white", paper_bgcolor="white",
        height=640, margin=dict(l=10,r=140,t=80,b=10),
    )
    return fig

# ── VIEW 2: Kalender ─────────────────────────────────────────────────────────
def build_kalender():
    tage_o = ["Mo","Di","Mi","Do","Fr","—"]
    rhy_o  = list(reversed(["täglich","wöchentlich","dreiwöchentlich",
                             "zweiwöchentlich","monatlich","quartalsweise","variabel"]))
    agg = defaultdict(list)
    for m in aktive:
        for tag in (m["wochentage"] or ["—"]):
            agg[(tag, m["rhythmus_klasse"])].append(m["name"])
    xs,ys,szs,txts,hvrs,cols = [],[],[],[],[],[]
    for (tag,rhy), namen in agg.items():
        xs.append(tag); ys.append(rhy)
        szs.append(14+len(namen)*16); txts.append(str(len(namen)))
        hvrs.append(f"<b>{tag} / {rhy}</b><br>"+"<br>".join(namen))
        cols.append(RHY_FARBEN.get(rhy,"#9ca3af"))
    fig = go.Figure(go.Scatter(
        x=xs,y=ys,mode="markers+text",text=txts,
        textfont=dict(size=12,color="white"),
        marker=dict(size=szs,color=cols,sizemode="diameter",line=dict(width=1,color="white")),
        hovertext=hvrs,hoverinfo="text",
    ))
    fig.update_layout(
        title=dict(text="Meeting-Kalender – Wann findet was statt?",font=dict(size=16,family="Inter")),
        xaxis=dict(title="Wochentag",categoryorder="array",categoryarray=tage_o,
                   showgrid=True,gridcolor="#f3f4f6"),
        yaxis=dict(title="Rhythmus",categoryorder="array",categoryarray=rhy_o,
                   showgrid=True,gridcolor="#f3f4f6"),
        plot_bgcolor="white",paper_bgcolor="white",
        height=460,margin=dict(l=150,r=20,t=60,b=80),
        annotations=[dict(text="Bubble-Größe = Anzahl Meetings · Hover für Details",
            xref="paper",yref="paper",x=0,y=-0.16,showarrow=False,
            font=dict(size=10,color="#9ca3af"))],
    )
    return fig

# ── VIEW 3: Überschneidungen ─────────────────────────────────────────────────
def build_overlap():
    ml = [m for m in aktive if len(m["teilnehmer"])>=2]
    namen = [m["name"] for m in ml]
    sets  = [set(m["teilnehmer"]) for m in ml]
    n = len(ml)
    matrix, hover = [],[]
    for i in range(n):
        mr,hr = [],[]
        for j in range(n):
            if i==j: v=1.0
            elif not sets[i] or not sets[j]: v=0.0
            else: v=round(len(sets[i]&sets[j])/len(sets[i]|sets[j]),2)
            mr.append(v)
            gem = sets[i]&sets[j]
            hr.append(f"<b>{namen[i]}</b> ↔ <b>{namen[j]}</b><br>"
                      f"Ähnlichkeit: {v:.0%}<br>Gemeinsam: {', '.join(sorted(gem)) or '–'}")
        matrix.append(mr); hover.append(hr)
    fig = go.Figure(go.Heatmap(
        z=matrix,x=namen,y=namen,
        text=[[f"{v:.0%}" if v>0 else "" for v in r] for r in matrix],
        texttemplate="%{text}",textfont=dict(size=8),
        colorscale="RdYlGn_r",zmin=0,zmax=1,
        hovertext=hover,hoverinfo="text",
        colorbar=dict(title="Jaccard<br>Ähnlichkeit"),
    ))
    fig.update_layout(
        title=dict(text="Teilnehmer-Überschneidung – Welche Meetings sind ähnlich?",
                   font=dict(size=16,family="Inter")),
        height=700,margin=dict(l=210,r=100,t=60,b=210),
        xaxis=dict(tickangle=-45,tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=9)),
        annotations=[dict(text="Rot = hohe Überschneidung (potenzielle Redundanz) · Hover für Details",
            xref="paper",yref="paper",x=0,y=-0.3,showarrow=False,
            font=dict(size=10,color="#9ca3af"))],
    )
    return fig

# ── VIEW 4: Abteilungen ──────────────────────────────────────────────────────
def build_abteilung():
    abt_o = ["PC","PCO","PCT","PCTAC/DC","PCTProduct","PCTDC","PCC","PCS"]
    rhy_o = ["täglich","wöchentlich","dreiwöchentlich","zweiwöchentlich","monatlich","quartalsweise","variabel"]
    abt_rhy = defaultdict(lambda: defaultdict(list))
    for m in aktive:
        abt_rhy[m["abteilung"]][m["rhythmus_klasse"]].append(m["name"])
    traces = []
    for rhy in rhy_o:
        ys,hv = [],[]
        for abt in abt_o:
            mn = abt_rhy[abt][rhy]
            ys.append(len(mn))
            hv.append(f"<b>{abt} / {rhy}</b><br>" + ("<br>".join(mn) if mn else "–"))
        traces.append(go.Bar(name=rhy,x=abt_o,y=ys,
            marker_color=RHY_FARBEN.get(rhy,"#9ca3af"),
            hovertext=hv,hoverinfo="text"))
    fig = go.Figure(data=traces)
    fig.update_layout(
        barmode="stack",
        title=dict(text="Meeting-Dichte pro Abteilung",font=dict(size=16,family="Inter")),
        xaxis_title="Abteilung",yaxis_title="Anzahl Meetings",legend_title="Rhythmus",
        plot_bgcolor="white",paper_bgcolor="white",
        height=440,margin=dict(l=60,r=20,t=60,b=60),
    )
    fig.update_yaxes(showgrid=True,gridcolor="#f3f4f6")
    return fig

# ── VIEW 5: Sankey ───────────────────────────────────────────────────────────
def build_sankey():
    abt_list = ["PC","PCO","PCT","PCC","PCS","Extern"]
    abt_idx  = {a:i for i,a in enumerate(abt_list)}
    fluss = defaultdict(float)
    for m in aktive:
        abts = set()
        for t in m["teilnehmer"]:
            if t in PERSON_ABT: abts.add(PERSON_ABT[t])
        if any(t.lower()=="extern" for t in m["teilnehmer"]):
            abts.add("Extern")
        raw_abt = m["abteilung"].replace("PCTAC/DC","PCT").replace("PCTProduct","PCT").replace("PCTDC","PCT")
        abts.add(raw_abt if raw_abt in abt_list else "PC")
        al = sorted(abts & set(abt_list))
        w  = FREQ_W.get(m["rhythmus_klasse"],0.5)
        for i in range(len(al)):
            for j in range(i+1,len(al)):
                k = (al[i],al[j]) if al[i]<al[j] else (al[j],al[i])
                fluss[k] += w
    srcs,tgts,vals,lbl,link_colors = [],[],[],[],[]
    for (a,b),v in fluss.items():
        srcs.append(abt_idx[a]); tgts.append(abt_idx[b])
        vals.append(round(v,1)); lbl.append(f"{a} ↔ {b}: {v:.1f} Freq.-Punkte")
        # Farbige Links (Quell-Abteilungsfarbe, gut sichtbar)
        hex_col = ABT_FARBEN.get(a,"#9ca3af").lstrip("#")
        r,g,b_c = int(hex_col[0:2],16),int(hex_col[2:4],16),int(hex_col[4:6],16)
        link_colors.append(f"rgba({r},{g},{b_c},0.35)")
    fig = go.Figure(go.Sankey(
        node=dict(pad=24,thickness=24,
                  line=dict(color="white",width=0.5),
                  label=abt_list,
                  color=[ABT_FARBEN.get(a,"#9ca3af") for a in abt_list],
                  hovertemplate="<b>%{label}</b><extra></extra>"),
        link=dict(source=srcs,target=tgts,value=vals,
                  customdata=lbl,
                  hovertemplate="<b>%{customdata}</b><extra></extra>",
                  color=link_colors),
    ))
    fig.update_layout(
        title=dict(text="Informationsfluss zwischen Abteilungen · Flussdicke = gewichtete Meeting-Frequenz",
                   font=dict(size=15,family="Inter")),
        height=440,margin=dict(l=20,r=20,t=60,b=30),
    )
    return fig

# ── VIEW 6: Tabelle ──────────────────────────────────────────────────────────
def build_tabelle_html():
    """Gibt eine reine HTML-Tabelle zurück (kein Plotly) – filterbar per JS."""
    rows_html = ""
    for m in meetings:
        platzh = "⚠" if m["ist_platzhalter"] else ""
        ug     = "✓" if m["abteilungsuebergreifend"] else ""
        teiln  = ", ".join(m["teilnehmer"]) or m.get("teilnehmer_raw") or "–"
        vera   = m["verantwortlich"] or "–"
        status_cls = "badge-aktiv" if m["status"]=="Aktiv" else "badge-geplant"
        zweck  = (m["zweck"] or "–")[:110] + ("…" if (m["zweck"] or "")[:110] != (m["zweck"] or "") else "")
        learning = m["learning"] or "–"

        # data-attrs für JS-Filter
        data_abt   = m["abteilung"]
        data_vera  = vera
        data_teiln = teiln

        rows_html += f"""<tr data-abt="{data_abt}" data-vera="{data_vera}" data-teiln="{data_teiln}">
          <td><span class="abt-badge" style="background:{ABT_FARBEN.get(m['abteilung'],'#9ca3af')}22;color:{ABT_FARBEN.get(m['abteilung'],'#6b7280')};border:1px solid {ABT_FARBEN.get(m['abteilung'],'#9ca3af')}55">{m['abteilung']}</span></td>
          <td class="meeting-name">{m['name']}{' <span class="platzh-badge">⚠ Platzhalter</span>' if platzh else ''}</td>
          <td><span class="kat-pill">{m['kategorie']}</span></td>
          <td><span class="rhy-dot" style="background:{RHY_FARBEN.get(m['rhythmus_klasse'],'#9ca3af')}"></span>{m['rhythmus_klasse']}</td>
          <td>{vera}</td>
          <td class="teiln-cell">{teiln}</td>
          <td><span class="badge {status_cls}">{m['status']}</span></td>
          <td style="text-align:center">{ug}</td>
          <td class="zweck-cell">{zweck}</td>
          <td class="learning-cell">{learning}</td>
        </tr>"""

    return f"""
    <div class="table-toolbar">
      <input type="text" id="table-search" placeholder="🔍  Meeting, Person, Abteilung …" oninput="filterTable()">
      <div class="table-meta" id="table-count"></div>
    </div>
    <div class="table-wrap">
    <table id="meeting-table">
      <thead><tr>
        <th>Abteilung</th><th>Meeting</th><th>Kategorie</th><th>Rhythmus</th>
        <th>Verantwortl.</th><th>Teilnehmer</th><th>Status</th>
        <th title="Abteilungsübergreifend">Übergr.</th><th>Zweck</th><th>Learnings</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>"""

# ── VIEW 7: Findings / Auffälligkeiten ───────────────────────────────────────
def build_findings_html():
    findings = [
        # (kategorie, emoji, titel, beschreibung)
        ("redundanz","🔴","PC Leitungsmeeting ↔ 3M (Monthly Management Meeting)",
         "Fast identische Teilnehmer: Jco, Ktz, Beb, TOK, MiG, Kip, Urk. Das Leitungsmeeting läuft wöchentlich, das 3M monatlich – mit sehr ähnlichem Reporting-Fokus. Ist das monatliche Meeting eine eigenständige Eskalationsebene oder ein Duplikat?"),
        ("redundanz","🔴","Reklamationsmeeting ↔ Reklamation",
         "Zwei Meetings mit sehr ähnlichem Namen unter PCC. Das Reklamationsmeeting ist wöchentlich (operativ), die Reklamation ist quartalsweise (statistisch/strategisch). Abgrenzung ist in der Quelltabelle nicht klar dokumentiert."),
        ("redundanz","🔴","JF Beschaffung ↔ JF Enasys",
         "Beide wöchentlich, beide mit Ipa und Beb, beide thematisch um Beschaffung/Vorkomponenten. JF Beschaffung fokussiert auf strategische Beschaffung, JF Enasys auf Enasys-spezifische Themen. Könnten sie kombiniert oder gestaffelt werden?"),
        ("last","⚠️","Kip (PCT) – höchste Meeting-Last im Netzwerk",
         "Kip ist in ≥12 aktiven Meetings involviert, davon verantwortet er 6 direkt. Täglich, wöchentlich, zweiwöchentlich. Ist diese Meeting-Dichte für eine Führungskraft langfristig nachhaltig?"),
        ("last","⚠️","Beb (PCO) – 4 individuelle JFs + Teammeeting",
         "Beb führt wöchentliche Einzel-JFs mit Ipa, Fln und Jco (jeweils getrennt), plus das PCO Teammeeting. Bietet das Teammeeting noch eigenständigen Mehrwert, wenn alle 1:1-Themen schon abgedeckt sind?"),
        ("last","⚠️","TOK (PCC) – 7 Meetings, davon 2 täglich",
         "TOK verantwortet PCC-Update (täglich) und hat 1:1 MA Gespräche (wöchentlich, Platzhalter für alle Einzelgespräche mit dem Team). Dazu Teilnahme am Leitungsmeeting, 3M und wöchentlichem CCU2 UL Meeting."),
        ("luecke","🕳️","Keine regelmäßige Schiene PCC ↔ PCS dokumentiert",
         "Customer (PCC) und Sales (PCS) haben kein gemeinsames regelmäßiges Meeting. Bei Reklamationen, Kundenanfragen oder Eskalationen ist unklar, wie Informationen zwischen diesen Abteilungen fließen. Informell geregelt?"),
        ("luecke","🕳️","Keine regelmäßige Schiene PCO ↔ PCS dokumentiert",
         "Einkauf/Operations (PCO) und Sales (PCS) sind im Netzwerk nicht direkt verbunden. Bei kundenseitigen Bedarfen, Lieferzeiten oder Beschaffungsfragen wäre eine direkte Schiene relevant."),
        ("luecke","🕳️","Kein übergreifendes Führungskräfte-Forum auf Teamlead-Ebene",
         "Unterhalb des Leitungsmeetings (GF-Ebene) gibt es kein dokumentiertes Meeting, in dem die Teamleads abteilungsübergreifend koordinieren. Beb, TOK, Urk, Kip treffen sich nur im Leitungsmeeting gemeinsam."),
        ("klaerung","✅","1:1 MA Gespräche (Kip/PCT) – rotierendes Format",
         "Geklärt: Je Wochentag trifft Kip einen anderen Mitarbeiter aus PCT (Rotationsplan). Das erklärt die tägliche Eintragung. Die Meeting-Last-Einschätzung für Kip bleibt hoch, aber das Format ist strukturiert und nicht täglich mit allen."),
        ("klaerung","❓","'Regeltermin Turn – PQR' doppelt in der Quelltabelle",
         "Das Meeting erschien in Zeile 4 (mit vollständigen Daten) und Zeile 7 (unvollständig, ohne Teilnehmer und Zweck). Das zweite Vorkommen wurde bereinigt. Handelt es sich um zwei verschiedene Meeting-Instanzen oder ein Duplikat?"),
        ("klaerung","❓","PSG Sitzung – wer sind 'Projektverantwortliche' konkret?",
         "Als Teilnehmer steht nur 'Projektverantwortliche'. Für eine vollständige Analyse des Informationsflusses: Welche Personen bzw. Rollen sind regelmäßig dabei? Alle POs (Kip, Krö, Kis)?"),
        ("klaerung","❓","JF Kunden – wer ist 'Kundenbetreuer' konkret?",
         "Verantwortlich = 'Kundenbetreuer'. Ist das eine Rolle, die von Urk oder anderen PCS-Mitgliedern je nach Kunde übernommen wird? Für Netzwerk-Analyse relevant."),
        ("klaerung","❓","'PCS/ACF Sprintreview' – Name irreführend",
         "Laut Klärung ist das ein Produkt-Review innerhalb PCT AC. Verantwortlich ist Kip, durchgeführt von Kis. Der Name suggeriert PCS-Beteiligung, tatsächlich ist es ein PCT-internes Meeting. Sollte der Name in der Quelltabelle angepasst werden?"),
        ("luecke","🕳️","Ktz (PCP Produktmanagement) – keine eigenen Meetings dokumentiert",
         "Ktz ist Führungskraft von PCP Produktmanagement (mit Lav und Rls). Er erscheint nur als Teilnehmer in PC-Leitungsmeetings, hat aber keine eigenen Meetings verantwortet – weder 1:1s mit seinem Team noch ein PCP-Teammeeting. Entweder nicht erfasst oder tatsächlich nicht vorhanden. Klärung empfohlen."),
        ("datenqualitaet","📝","11 Meetings ohne Informationsfluss-Dokumentation",
         "Für 11 aktive Meetings ist nicht dokumentiert, welche Informationen hineinfließen und welche Entscheidungen/Outputs herauskommen. Empfehlung: Im Rahmen der Meeting-Überprüfung nachpflegen – der Informationsfluss ist entscheidend für die Qualitätsbeurteilung."),
        ("datenqualitaet","📝","Asymmetrie in der Dokumentation von Einzelgesprächen",
         "Urk und Beb listen ihre 1:1-Gespräche namentlich auf (pro Person ein eigenes Meeting). TOK und Kip verwenden Platzhalter. Das macht den Vergleich schwierig. Empfehlung: Einheitlichen Standard festlegen."),
        ("datenqualitaet","📝","Uneinheitliche Terminologie: '1:1' vs. 'Jour Fixe (JF)'",
         "Bilateral-Meetings zwischen zwei Personen werden in der Tabelle unterschiedlich bezeichnet: Urk nennt sie '1:1' (Einzelgespräch), Beb nennt identische Formate 'JF' (Jour Fixe). Funktional sind beide dasselbe: ein regelmäßiges bilaterales Meeting. Die unterschiedliche Benennung erschwert systemische Auswertung und Kategorisierung. Empfehlung: Gemeinsame Nomenklatur festlegen."),
        ("datenqualitaet","📝","Abteilung 'PCS/ACF Sprintreview' weist auf PCT hin",
         "Meeting ist unter PCT geführt, Name enthält PCS. Im Netzwerk wird dieses Meeting korrekt bei PCT verortet, aber der Name könnte zu Verwechslungen führen."),
    ]

    kat_meta = {
        "redundanz":      ("Mögliche Redundanzen",    "#dc2626","#fef2f2","#fca5a5"),
        "last":           ("Hohe Meeting-Last",        "#d97706","#fffbeb","#fcd34d"),
        "luecke":         ("Kommunikationslücken",     "#7c3aed","#f5f3ff","#c4b5fd"),
        "klaerung":       ("Klärungsbedarf",           "#0369a1","#eff6ff","#93c5fd"),
        "datenqualitaet": ("Datenqualität",            "#374151","#f9fafb","#d1d5db"),
    }

    html = ""
    for kat, (titel, col, bg, border) in kat_meta.items():
        items = [f for f in findings if f[0]==kat]
        html += f"""<div class="finding-category">
      <h3 style="color:{col};border-left:4px solid {col};padding-left:10px">{titel} <span class="finding-count">{len(items)}</span></h3>"""
        for i, (_, emoji, heading, desc) in enumerate(items):
            fid = f"{kat}-{i}"
            html += f"""<div class="finding-card" id="card-{fid}" style="border-left:3px solid {border};background:{bg}">
        <div class="finding-header" onclick="toggleFinding('{fid}')">
          <span class="finding-emoji">{emoji}</span>
          <span class="finding-title">{heading}</span>
          <span class="finding-arrow" id="arrow-{fid}">▸</span>
        </div>
        <div class="finding-body" id="body-{fid}">
          <p>{desc}</p>
        </div>
      </div>"""
        html += "</div>"

    summary = f"<div class='findings-summary'>Gesamt: <b>{len(findings)} Auffälligkeiten</b> in {len(kat_meta)} Kategorien · Klicke auf eine Karte zum Aufklappen</div>"
    return summary + html

# ── Alle Charts rendern ──────────────────────────────────────────────────────
print("🔨 Erzeuge Charts…")
div_netz    = fig_div(build_network())
div_kal     = fig_div(build_kalender())
div_overlap = fig_div(build_overlap())
div_abt     = fig_div(build_abteilung())
div_sankey  = fig_div(build_sankey())
html_tabelle  = build_tabelle_html()
html_findings = build_findings_html()
print("   ✓ Alle Views erzeugt")

# ── Statistiken ──────────────────────────────────────────────────────────────
n_aktiv  = sum(1 for m in meetings if m["status"]=="Aktiv")
n_woech  = sum(1 for m in meetings if m["rhythmus_klasse"]=="wöchentlich")
n_ug     = sum(1 for m in meetings if m["abteilungsuebergreifend"])
n_einzel = sum(1 for m in meetings if m["kategorie"]=="Einzelgespräch")
n_platzh = sum(1 for m in meetings if m["ist_platzhalter"])
n_ohne_info = sum(1 for m in meetings if not m["infofluss"])

warn_items = []
if n_platzh: warn_items.append(f"<b>{n_platzh} Meetings</b> mit unvollständigen Teilnehmer-Angaben (Platzhalter ⚠)")
if n_ohne_info: warn_items.append(f"<b>{n_ohne_info} Meetings</b> ohne Informationsfluss-Dokumentation")
warn_html = "".join(f"<li>{w}</li>" for w in warn_items)

# ── Plotly.js einmalig inline extrahieren (offline-fähig, ~3 MB) ─────────────
import re as _re
_dummy_html = pio.to_html(go.Figure(), full_html=True, include_plotlyjs=True)
# Script 0: PlotlyConfig (~47 chars), Script 1: plotly.js (~4.8MB), Script 2: env-setup
_all_scripts = _re.findall(r'(<script[^>]*>.*?</script>)', _dummy_html, _re.DOTALL)
# Die ersten zwei Blöcke (Config + plotly.js) einbetten
_plotly_js_inline = "\n".join(_all_scripts[:2]) if len(_all_scripts) >= 2 else \
    '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'

# ── HTML zusammensetzen ──────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Meeting Strukturanalyse</title>
<!-- Google Fonts: wird nur mit Internet geladen; Fallback: system-ui -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<!-- Plotly inline eingebettet → Dashboard funktioniert vollständig offline -->
{_plotly_js_inline}
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Inter",system-ui,sans-serif;background:#f8fafc;color:#1e293b;font-size:14px}}

/* Header */
.header{{background:linear-gradient(135deg,#1e40af 0%,#2563eb 60%,#0891b2 100%);
  color:white;padding:22px 36px 20px}}
.header h1{{font-size:1.45rem;font-weight:700;letter-spacing:-0.3px}}
.header p{{opacity:.8;font-size:.82rem;margin-top:3px}}

/* Stats */
.stats{{display:flex;gap:12px;padding:16px 36px;flex-wrap:wrap}}
.stat{{background:white;border-radius:10px;padding:14px 20px;flex:1;min-width:120px;
  text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.07);border:1px solid #f1f5f9}}
.stat .val{{font-size:1.9rem;font-weight:700;color:#2563eb;line-height:1}}
.stat .lbl{{font-size:.75rem;color:#64748b;margin-top:3px}}

/* Warnungen */
.warnings{{margin:0 36px 12px;background:#fffbeb;border:1px solid #fcd34d;
  border-left:4px solid #f59e0b;border-radius:6px;padding:10px 14px;font-size:.82rem}}
.warnings ul{{padding-left:16px}}
.warnings li{{margin-bottom:2px}}

/* Tabs */
.tab-bar{{display:flex;gap:2px;padding:0 36px;background:#f8fafc;
  border-bottom:2px solid #e2e8f0;position:sticky;top:0;z-index:100}}
.tab-btn{{padding:10px 16px;border:none;background:none;cursor:pointer;
  font-family:inherit;font-size:.83rem;font-weight:500;color:#64748b;
  border-bottom:3px solid transparent;margin-bottom:-2px;transition:all .15s}}
.tab-btn:hover{{color:#2563eb}}
.tab-btn.active{{color:#2563eb;border-bottom-color:#2563eb}}

/* Panel */
.panel{{display:none;padding:20px 36px 30px}}
.panel.active{{display:block}}
.chart-card{{background:white;border-radius:10px;padding:16px;
  box-shadow:0 1px 4px rgba(0,0,0,.07);border:1px solid #f1f5f9}}
.hint{{font-size:.78rem;color:#94a3b8;margin-top:8px;padding-left:4px}}

/* Tabellen-Panel */
.table-toolbar{{display:flex;align-items:center;gap:12px;margin-bottom:12px}}
#table-search{{flex:1;max-width:380px;padding:8px 12px;border:1px solid #e2e8f0;
  border-radius:8px;font-family:inherit;font-size:.85rem;outline:none}}
#table-search:focus{{border-color:#2563eb;box-shadow:0 0 0 3px #dbeafe}}
.table-meta{{font-size:.8rem;color:#94a3b8}}
.table-wrap{{overflow-x:auto;border-radius:8px;border:1px solid #e2e8f0}}
#meeting-table{{width:100%;border-collapse:collapse;font-size:.82rem}}
#meeting-table thead th{{background:#1e293b;color:white;padding:10px 12px;
  text-align:left;font-weight:600;white-space:nowrap;position:sticky;top:0}}
#meeting-table tbody tr{{border-bottom:1px solid #f1f5f9;transition:background .1s}}
#meeting-table tbody tr:hover{{background:#f8fafc}}
#meeting-table td{{padding:9px 12px;vertical-align:top}}
.abt-badge{{display:inline-block;padding:2px 7px;border-radius:4px;
  font-size:.75rem;font-weight:600;white-space:nowrap}}
.meeting-name{{font-weight:500;min-width:160px}}
.platzh-badge{{display:inline-block;font-size:.7rem;background:#fef3c7;
  color:#d97706;border:1px solid #fcd34d;border-radius:3px;padding:1px 5px;margin-left:4px}}
.kat-pill{{display:inline-block;background:#f1f5f9;color:#475569;border-radius:4px;
  padding:2px 7px;font-size:.74rem;white-space:nowrap}}
.rhy-dot{{display:inline-block;width:8px;height:8px;border-radius:50%;
  margin-right:5px;vertical-align:middle}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:600}}
.badge-aktiv{{background:#dcfce7;color:#15803d}}
.badge-geplant{{background:#dbeafe;color:#1d4ed8}}
.teiln-cell,.zweck-cell,.learning-cell{{max-width:220px;font-size:.8rem;color:#475569}}

/* Findings */
.findings-summary{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
  padding:10px 16px;margin-bottom:16px;font-size:.85rem;color:#475569}}
.finding-category{{margin-bottom:20px}}
.finding-category h3{{font-size:.95rem;font-weight:700;margin-bottom:10px;
  display:flex;align-items:center;gap:8px}}
.finding-count{{background:currentColor;color:white;border-radius:20px;
  padding:1px 8px;font-size:.75rem;font-weight:700;opacity:.85}}
.finding-card{{border-radius:8px;margin-bottom:8px;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.finding-header{{display:flex;align-items:center;gap:10px;padding:11px 14px;
  cursor:pointer;user-select:none}}
.finding-header:hover{{filter:brightness(.97)}}
.finding-emoji{{font-size:1rem;flex-shrink:0}}
.finding-title{{flex:1;font-weight:500;font-size:.88rem}}
.finding-status{{padding:3px 9px;border-radius:20px;font-size:.73rem;font-weight:700;
  cursor:pointer;white-space:nowrap;flex-shrink:0}}
.offen{{background:#fee2e2;color:#dc2626}}
.klaerung{{background:#fef3c7;color:#d97706}}
.geklaert{{background:#dcfce7;color:#16a34a}}
.finding-arrow{{color:#9ca3af;font-size:.8rem;transition:transform .2s;flex-shrink:0}}
.finding-body{{display:none;padding:12px 16px 14px 42px;border-top:1px solid rgba(0,0,0,.06)}}
.finding-body p{{font-size:.85rem;color:#374151;line-height:1.6}}

/* Overlap-Legende */
.overlap-legend{{display:flex;flex-direction:column;gap:8px;margin-top:12px;
  background:white;border-radius:8px;padding:12px 16px;border:1px solid #f1f5f9;
  font-size:.83rem;color:#374151}}
.ol-item{{display:flex;align-items:flex-start;gap:10px}}
.ol-dot{{width:14px;height:14px;border-radius:3px;flex-shrink:0;margin-top:2px}}


/* Footer */
.footer{{text-align:center;padding:24px;font-size:.74rem;color:#94a3b8;border-top:1px solid #f1f5f9}}
</style>
</head>
<body>

<div class="header">
  <h1>Organisations-Meeting &amp; Informationsfluss</h1>
  <p>Interaktives Dashboard · Stand: 26.05.2026 · Quelle: LeitMet.xlsx · {len(meetings)} Meetings</p>
</div>

<div class="stats">
  <div class="stat"><div class="val">{n_aktiv}</div><div class="lbl">Aktive Meetings</div></div>
  <div class="stat"><div class="val">{n_woech}</div><div class="lbl">Wöchentlich</div></div>
  <div class="stat"><div class="val">{n_ug}</div><div class="lbl">Abteilungsübergreifend</div></div>
  <div class="stat"><div class="val">{n_einzel}</div><div class="lbl">Einzelgespräche</div></div>
  <div class="stat"><div class="val">{n_platzh}</div><div class="lbl">⚠ Platzhalter</div></div>
</div>

{"<div class='warnings'><ul>" + warn_html + "</ul></div>" if warn_html else ""}

<div class="tab-bar">
  <button class="tab-btn active" onclick="showTab(0)">🕸 Netzwerk</button>
  <button class="tab-btn" onclick="showTab(1)">📅 Kalender</button>
  <button class="tab-btn" onclick="showTab(2)">🔴 Überschneidungen</button>
  <button class="tab-btn" onclick="showTab(3)">📊 Abteilungen</button>
  <button class="tab-btn" onclick="showTab(4)">🌊 Informationsfluss</button>
  <button class="tab-btn" onclick="showTab(5)">📋 Alle Meetings</button>
  <button class="tab-btn" onclick="showTab(6)">💡 Auffälligkeiten</button>
</div>

<div id="panel-0" class="panel active">
  <div class="chart-card">{div_netz}</div>
  <p class="hint">⭐ = Führungskraft · Knotengröße = Meeting-Anzahl · Liniendicke = Frequenz · Person-Filter oben links im Chart</p>
</div>
<div id="panel-1" class="panel">
  <div class="chart-card">{div_kal}</div>
  <p class="hint">Bubble-Größe = Anzahl Meetings an diesem Tag/Rhythmus · Hover für Meeting-Namen</p>
</div>
<div id="panel-2" class="panel">
  <div class="chart-card">{div_overlap}</div>
  <div class="overlap-legend">
    <span class="ol-item"><span class="ol-dot" style="background:#dc2626"></span><b>Hohe Überschneidung (rot)</b> → ähnliche Teilnehmergruppe → mögliche Redundanz. Frage: Brauchen wir beide Meetings?</span>
    <span class="ol-item"><span class="ol-dot" style="background:#16a34a"></span><b>Keine Überschneidung (grün)</b> → völlig verschiedene Teilnehmer → kein direkter Informationsaustausch via Meeting. Hinweis: Lücke hier ist <em>kein Befund</em> – zwei Meetings müssen nicht dieselben Personen haben. Fehlende Meetings erkennst du besser im Netzwerk (isolierte Knoten) oder im Tab <b>💡 Auffälligkeiten</b> (dokumentierte Lücken).</span>
  </div>
</div>
<div id="panel-3" class="panel">
  <div class="chart-card">{div_abt}</div>
  <p class="hint">Gestapelte Balken nach Rhythmus · Hover für Meeting-Namen</p>
</div>
<div id="panel-4" class="panel">
  <div class="chart-card">{div_sankey}</div>
  <p class="hint">Flussdicke = gewichtete Meeting-Frequenz zwischen Abteilungen</p>
</div>
<div id="panel-5" class="panel">
  {html_tabelle}
  <p class="hint">Suche filtert über Meeting-Name, Teilnehmer und Abteilung</p>
</div>
<div id="panel-6" class="panel">
  {html_findings}
</div>

<div class="footer">
  Erstellt mit Claude Code · Colenet · {len(meetings)} Meetings · Daten: LeitMet.xlsx (vertraulich, lokal)
</div>

<script>
// ── Tab-Navigation ────────────────────────────────────────────────────────
function showTab(idx) {{
  document.querySelectorAll(".tab-btn").forEach((b,i)=>b.classList.toggle("active",i===idx));
  document.querySelectorAll(".panel").forEach((p,i)=>p.classList.toggle("active",i===idx));
  if(idx===5) updateTableCount();
  // Plotly-Charts erst nach vollständigem DOM-Update auf korrekte Breite bringen
  requestAnimationFrame(function() {{
    setTimeout(function() {{
      var panel = document.getElementById("panel-"+idx);
      panel.querySelectorAll(".plotly-graph-div").forEach(function(p) {{
        Plotly.Plots.resize(p);
      }});
    }}, 50);
  }});
}}

// Auch bei Browser-Resize alle sichtbaren Charts neu skalieren
window.addEventListener("resize", function() {{
  document.querySelectorAll(".panel.active .plotly-graph-div").forEach(function(p) {{
    Plotly.Plots.resize(p);
  }});
}});

// ── Tabellen-Filter ───────────────────────────────────────────────────────
function filterTable() {{
  var q = (document.getElementById("table-search").value||"").toLowerCase().trim();
  var rows = document.querySelectorAll("#meeting-table tbody tr");
  var shown = 0;
  rows.forEach(function(row) {{
    var text = (row.querySelector(".meeting-name").textContent + " " +
                row.getAttribute("data-teiln") + " " +
                row.getAttribute("data-abt") + " " +
                row.getAttribute("data-vera")).toLowerCase();
    var vis = !q || text.includes(q);
    row.style.display = vis ? "" : "none";
    if(vis) shown++;
  }});
  document.getElementById("table-count").textContent = shown + " von {len(meetings)} Meetings";
}}
function updateTableCount() {{
  var total = document.querySelectorAll("#meeting-table tbody tr").length;
  document.getElementById("table-count").textContent = total + " von {len(meetings)} Meetings";
}}

// ── Findings-Interaktion ──────────────────────────────────────────────────
function toggleFinding(id) {{
  var body  = document.getElementById("body-"+id);
  var arrow = document.getElementById("arrow-"+id);
  var open  = body.style.display==="block";
  body.style.display    = open ? "none" : "block";
  arrow.style.transform = open ? "" : "rotate(90deg)";
  arrow.textContent     = open ? "▸" : "▾";
}}
</script>
</body>
</html>"""

with open(OUTPUT,"w",encoding="utf-8") as f:
    f.write(html)
print(f"✅ Dashboard → {OUTPUT}")
print(f"   open '{OUTPUT}'")
