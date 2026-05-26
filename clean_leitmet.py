"""
clean_leitmet.py
Bereinigt LeitMet.xlsx (oder CSV-Export aus Confluence) und erzeugt leitmet_clean.json

Aufruf:
    python3 clean_leitmet.py
    python3 clean_leitmet.py --input /anderer/pfad/LeitMet.xlsx
    python3 clean_leitmet.py --input /anderer/pfad/confluence_export.csv
    python3 clean_leitmet.py --confluence   # zusätzlich confluence_tabelle.csv erzeugen

Confluence-Import-Workflow:
    1. Confluence-Seite öffnen → Tabelle markieren → kopieren
    2. In Numbers/Excel einfügen → als CSV speichern
    3. python3 clean_leitmet.py --input pfad/zur/export.csv
    ODER: Confluence-Export-Funktion nutzen (Seite > ··· > Export > CSV)

    Erwartete Spaltenreihenfolge (identisch mit LeitMet.xlsx):
    Abteilung | Meeting-Name | Zweck | Verantwortlich | Teilnehmer |
    Rhythmus | Informationsfluss | Status | Learning
"""

import pandas as pd
import json
import re
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Pfade & Argumente
# ---------------------------------------------------------------------------
DEFAULT_INPUT  = Path.home() / "Downloads" / "LeitMet.xlsx"
DEFAULT_OUTPUT = Path(__file__).parent / "leitmet_clean.json"
CONFLUENCE_OUT = Path(__file__).parent / "confluence_tabelle.csv"

parser = argparse.ArgumentParser()
parser.add_argument("--input",      default=str(DEFAULT_INPUT),
                    help="Pfad zur xlsx- oder csv-Quelldatei")
parser.add_argument("--output",     default=str(DEFAULT_OUTPUT))
parser.add_argument("--confluence", action="store_true",
                    help="Zusätzlich confluence_tabelle.csv erzeugen")
args = parser.parse_args()

INPUT  = Path(args.input)
OUTPUT = Path(args.output)

# ---------------------------------------------------------------------------
# 1. Rohdaten einlesen (xlsx ODER csv)
# ---------------------------------------------------------------------------
if INPUT.suffix.lower() == ".csv":
    # CSV-Export aus Confluence (Semikolon oder Komma als Trennzeichen)
    try:
        raw = pd.read_csv(INPUT, dtype=str, sep=";", encoding="utf-8-sig")
        if len(raw.columns) < 5:          # Fallback auf Komma
            raw = pd.read_csv(INPUT, dtype=str, sep=",", encoding="utf-8-sig")
    except Exception:
        raw = pd.read_csv(INPUT, dtype=str, encoding="utf-8-sig")
    # Spalten umbenennen – flexibel per Position (erste 9 Spalten)
    expected = ["abteilung", "name", "zweck", "verantwortlich",
                "teilnehmer", "rhythmus", "infofluss", "status", "learning"]
    raw.columns = expected[:len(raw.columns)] + list(raw.columns[len(expected):])
else:
    raw = pd.read_excel(INPUT, header=0, dtype=str)
    raw.columns = [
        "abteilung", "name", "zweck", "verantwortlich",
        "teilnehmer", "rhythmus", "infofluss", "status", "learning"
    ]

def clean_val(v):
    """NaN und \xa0 → None; sonst strippen."""
    if pd.isna(v):
        return None
    s = str(v).replace("\xa0", "").strip()
    return s if s else None

# ---------------------------------------------------------------------------
# 2. Zeilenweise verarbeiten – Split-Rows zusammenführen
# ---------------------------------------------------------------------------
# Row 7 = unvollständiges Duplikat von Row 4 (Regeltermin Turn - PQR) → skip
SKIP_ROWS = {7}

meetings = []
current  = None

for idx, row in raw.iterrows():
    if idx in SKIP_ROWS:
        continue

    abt   = clean_val(row["abteilung"])
    name  = clean_val(row["name"])
    zweck = clean_val(row["zweck"])
    vera  = clean_val(row["verantwortlich"])
    teil  = clean_val(row["teilnehmer"])
    rhy   = clean_val(row["rhythmus"])
    info  = clean_val(row["infofluss"])
    stat  = clean_val(row["status"])
    learn = clean_val(row["learning"])

    # Sonderfall: Excel hat "1:1" als datetime 01:01:00 geparst (TOK/PCC)
    raw_name = str(row["name"]).strip()
    if name is None and raw_name in ("01:01:00", "1:01:00"):
        name = "1:1 MA Gespräche"

    if name is not None:
        # Neues Meeting
        if current is not None:
            meetings.append(current)
        current = {
            "abteilung":      abt,
            "name":           name,
            "zweck":          zweck,
            "verantwortlich": vera,
            "teilnehmer":     teil,
            "rhythmus":       rhy,
            "infofluss":      info,
            "status":         stat,
            "learning":       learn,
        }
    else:
        # Continuation-Zeile → Felder ergänzen
        if current is None:
            continue
        for field, val in [
            ("abteilung", abt), ("zweck", zweck), ("verantwortlich", vera),
            ("teilnehmer", teil), ("rhythmus", rhy), ("infofluss", info),
            ("status", stat), ("learning", learn),
        ]:
            if val is None:
                continue
            if current[field] is None:
                current[field] = val
            elif field in ("infofluss", "rhythmus", "zweck"):
                current[field] = current[field] + "\n" + val

if current is not None:
    meetings.append(current)

# ---------------------------------------------------------------------------
# 3. Normalisierungen
# ---------------------------------------------------------------------------

ALIAS_MAP = {
    "ipa": "Ipa", "jco": "Jco", "mig": "MiG", "tok": "TOK",
    "kip": "Kip", "urk": "Urk", "beb": "Beb", "fln": "Fln",
    "ktz": "Ktz", "zes": "Zes", "leb": "LeB", "ada": "ADA",
    "sez": "Sez", "bre": "Bre", "drs": "DrS", "zrb": "Zrb",
    "krö": "Krö", "kro": "Krö", "kis": "Kis", "dem": "Dem",
    "bas": "Bas", "cst": "CST", "dni": "Dni", "fmd": "FMD",
    "tih": "Tih", "smi": "SMI", "kih": "Kih", "bra": "Bra",
    "wud": "Wud", "het": "HeT", "fef": "Fef", "smt": "Smt",
    "pic": "Pic", "klb": "Klb", "zeller": "Zeller", "mgr": "MGR",
    "jfr": "JFR", "awa": "AWA", "mos": "MOS",
    "karim": "KTF",   # anonymisiert
    "ktf": "KTF",
}

PLATZHALTER_BEGRIFFE = {
    "pct alle", "pcs", "pc", "pco", "pcc", "qm", "pm", "extern",
    "steakholder", "stakeholder", "jeweilige ticketowner",
    "projektverantwortliche", "kundenbetreuer", "pcd",
    "tok + jeweiliger mitarbeiter", "optional:",
}

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

RHYTHMUS_MAP = [
    (r"täglich|daily",                              "täglich"),
    (r"dreiwöch",                                   "dreiwöchentlich"),
    (r"zwei.*wöch|alle\s*2\s*woch|bi.?week",        "zweiwöchentlich"),
    (r"wöchentl|weekly|1x.*woch",                   "wöchentlich"),
    (r"monatl|monthly|letzt.*monat|dritten.*mi",    "monatlich"),
    (r"quartal|quarterly|beirat|ende.*quartal",     "quartalsweise"),
    (r"divers|variabel|nach bedarf",                "variabel"),
]

TAG_MAP_RE = [
    (r"(?<![a-zA-Z])montag(?![a-zA-Z])|(?<![a-zA-Z])mo\.?(?![a-zA-Z])", "Mo"),
    (r"(?<![a-zA-Z])dienstag(?![a-zA-Z])|(?<![a-zA-Z])di\.?(?![a-zA-Z])", "Di"),
    (r"(?<![a-zA-Z])mittwoch(?![a-zA-Z])|(?<![a-zA-Z])mi\.?(?![a-zA-Z])", "Mi"),
    (r"(?<![a-zA-Z])donnerstag(?![a-zA-Z])|(?<![a-zA-Z])do\.?(?![a-zA-Z])", "Do"),
    (r"(?<![a-zA-Z])freitag(?![a-zA-Z])|(?<![a-zA-Z])fr\.?(?![a-zA-Z])", "Fr"),
]
TAG_REIHENFOLGE = ["Mo", "Di", "Mi", "Do", "Fr"]


def norm_status(s):
    if s is None:
        return "Unbekannt"
    sl = s.strip().lower()
    if sl in ("aktiv", "active"):
        return "Aktiv"
    if sl == "geplant":
        return "Geplant"
    return s.strip().capitalize()


def norm_rhythmus_klasse(r):
    if r is None:
        return "variabel"
    rl = r.lower()
    for pattern, label in RHYTHMUS_MAP:
        if re.search(pattern, rl):
            return label
    return "variabel"


def extrahiere_tage(r):
    if r is None:
        return []
    rl = r.lower()
    gefunden = []
    for pattern, tag in TAG_MAP_RE:
        if re.search(pattern, rl) and tag not in gefunden:
            gefunden.append(tag)
    return sorted(gefunden, key=lambda t: TAG_REIHENFOLGE.index(t) if t in TAG_REIHENFOLGE else 99)


def parse_teilnehmer(t):
    if t is None:
        return []
    t = re.sub(r"\(.*?\)", "", t)
    t = t.replace(";", ",").replace(" und ", ",").replace(" + ", ",")
    teile = [x.strip().rstrip(".,") for x in t.split(",") if x.strip().rstrip(".,")]
    ergebnis = []
    for p in teile:
        key = p.lower()
        ergebnis.append(ALIAS_MAP.get(key, p))
    return ergebnis


def hat_platzhalter(teilnehmer_liste):
    for t in teilnehmer_liste:
        if t.lower() in PLATZHALTER_BEGRIFFE:
            return True
    return False


def norm_vera(v):
    if v is None:
        return None
    teile = re.split(r"[/,]", v)
    return ", ".join(ALIAS_MAP.get(t.strip().lower(), t.strip()) for t in teile)


def kategorisiere(name):
    n = (name or "").lower()
    if re.search(r"^1:1|einzelgespr|ma.gesp|mitarbeitergespr", n):
        return "Einzelgespräch"
    if re.search(r"^jf |^jf$|jour fixe", n) or " jf" in n:
        return "Jour Fixe"
    if re.search(r"teammeeting|team.meeting|standup|stand.up", n):
        return "Teammeeting"
    if re.search(r"regeltermin|quarterly|quartal|^3m ", n):
        return "Regeltermin / Review"
    if re.search(r"sprint.*review|sprintreview", n):
        return "Sprint Review"
    if re.search(r"sitzung", n):
        return "Sitzung"
    if re.search(r"weekly|update|pcc-update", n):
        return "Weekly / Update"
    return "Sonstiges"

# ---------------------------------------------------------------------------
# 4. Zusammensetzen
# ---------------------------------------------------------------------------
result = []
for m in meetings:
    # Fehlende Abteilung per Vorwärtsfüllung (Fallback PC für übergreifende Meetings)
    if m["abteilung"] is None:
        m["abteilung"] = "PC"

    teilnehmer_liste = parse_teilnehmer(m["teilnehmer"])
    rhythmus_klasse  = norm_rhythmus_klasse(m["rhythmus"])
    tage             = extrahiere_tage(m["rhythmus"])

    # Platzhalter: vage Teilnehmer-Angaben ODER explizite Sammelbezeichnungen
    ist_platzhalter = hat_platzhalter(teilnehmer_liste) or (
        re.search(r"^1:1", (m["name"] or "").lower())
        and (m["teilnehmer"] or "").lower() in (
            "pct alle", "tok + jeweiliger mitarbeiter"
        )
    )

    # Abteilungsübergreifend
    abts = {PERSON_ABT[t] for t in teilnehmer_liste if t in PERSON_ABT}
    abt_uebergreifend = len(abts) > 1

    result.append({
        "abteilung":             m["abteilung"],
        "name":                  m["name"],
        "zweck":                 m["zweck"],
        "verantwortlich":        norm_vera(m["verantwortlich"]),
        "teilnehmer_raw":        m["teilnehmer"],
        "teilnehmer":            teilnehmer_liste,
        "teilnehmer_anzahl":     len(teilnehmer_liste),
        "rhythmus_raw":          m["rhythmus"],
        "rhythmus_klasse":       rhythmus_klasse,
        "wochentage":            tage,
        "infofluss":             m["infofluss"],
        "status":                norm_status(m["status"]),
        "learning":              m["learning"],
        "kategorie":             kategorisiere(m["name"]),
        "ist_platzhalter":       ist_platzhalter,
        "abteilungsuebergreifend": abt_uebergreifend,
    })

# ---------------------------------------------------------------------------
# 5. Ausgabe JSON
# ---------------------------------------------------------------------------
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"✅  {len(result)} Meetings bereinigt  →  {OUTPUT}\n")

# ---------------------------------------------------------------------------
# 6. Optional: Confluence-Tabelle als CSV
# ---------------------------------------------------------------------------
if args.confluence:
    import csv
    confluence_cols = [
        ("Abteilung",       lambda m: m["abteilung"]),
        ("Meeting-Name",    lambda m: m["name"]),
        ("Kategorie",       lambda m: m["kategorie"]),
        ("Zweck",           lambda m: (m["zweck"] or "").replace("\n", " ")),
        ("Verantwortlich",  lambda m: m["verantwortlich"] or ""),
        ("Teilnehmer",      lambda m: ", ".join(m["teilnehmer"]) or m.get("teilnehmer_raw") or ""),
        ("Rhythmus",        lambda m: m["rhythmus_klasse"]),
        ("Wochentage",      lambda m: ", ".join(m["wochentage"])),
        ("Rhythmus (orig)", lambda m: (m["rhythmus_raw"] or "").replace("\n", " ")),
        ("Informationsfluss", lambda m: (m["infofluss"] or "").replace("\n", " | ")),
        ("Status",          lambda m: m["status"]),
        ("Abt.übergreifend",lambda m: "Ja" if m["abteilungsuebergreifend"] else "Nein"),
        ("Platzhalter",     lambda m: "Ja" if m["ist_platzhalter"] else ""),
        ("Learnings",       lambda m: m["learning"] or ""),
    ]
    with open(CONFLUENCE_OUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([c[0] for c in confluence_cols])
        for m in result:
            writer.writerow([fn(m) for _, fn in confluence_cols])
    print(f"📋  Confluence-Tabelle  →  {CONFLUENCE_OUT}")
    print(f"    Tipp: In Confluence > Einfügen > Makro > 'CSV' oder direkt in")
    print(f"    eine Tabelle kopieren (Numbers/Excel öffnen → kopieren → einfügen)")

from collections import Counter
stats = [
    ("Aktiv",                  sum(1 for m in result if m["status"] == "Aktiv")),
    ("Geplant",                sum(1 for m in result if m["status"] == "Geplant")),
    ("Platzhalter",            sum(1 for m in result if m["ist_platzhalter"])),
    ("Abteilungsübergreifend", sum(1 for m in result if m["abteilungsuebergreifend"])),
]
for label, val in stats:
    print(f"  {label:<28} {val}")

print("\n  Kategorien:")
for k, v in Counter(m["kategorie"] for m in result).most_common():
    print(f"    {k:<28} {v}")

print("\n  Rhythmus:")
for k, v in Counter(m["rhythmus_klasse"] for m in result).most_common():
    print(f"    {k:<28} {v}")

print("\n  Abteilungen:")
for k, v in Counter(m["abteilung"] for m in result).most_common():
    print(f"    {k:<28} {v}")
