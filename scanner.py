import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

# -------------------------
# CONFIG
# -------------------------
BR_TZ = pytz.timezone("America/Sao_Paulo")

VALID_LEAGUE_IDS = [
    325,390,17,18,8,54,35,44,23,53,34,182,955,
    155,703,45,38,247,172,11653,11539,11536,
    170,39,808,36,242,185,37,131,192,937,
    11621,11620,20,11540,11541,406,202,
    238,239,152,40,215,52,278
]

DOMINANCE = [17,8,35,23,34,37,238]
CONSISTENCY = [325,390,155,703]
BALANCED = [18,54,53,182,131,239]
CHAOS = [11653,11539,11536,808,937,192,202,406]

# -------------------------
# API
# -------------------------

def get_events(date):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
    return requests.get(url).json().get("events", [])

def get_team_matches(team_id, limit=10):
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/{limit}"
    return requests.get(url).json().get("events", [])

# -------------------------
# FILTROS
# -------------------------

def is_valid_league(e):
    try:
        return e["tournament"]["uniqueTournament"]["id"] in VALID_LEAGUE_IDS
    except:
        return False

def is_same_day_br(e, date):
    utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
    return utc.astimezone(BR_TZ).date() == date

# -------------------------
# FORMA GERAL (10 jogos)
# -------------------------

def calculate_form_10(team_id):

    matches = get_team_matches(team_id, 10)

    pts, total = 0, 0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if m["homeTeam"]["id"] == team_id:
                if hs > as_: pts += 3
                elif hs == as_: pts += 1
            else:
                if as_ > hs: pts += 3
                elif hs == as_: pts += 1

            total += 3
        except:
            continue

    return pts / total if total else 0.5

# -------------------------
# CASA / FORA (5 jogos)
# -------------------------

def calculate_home_away_strength(team_id):

    matches = get_team_matches(team_id, 10)

    home_pts = home_total = 0
    away_pts = away_total = 0

    home_count = away_count = 0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if m["homeTeam"]["id"] == team_id and home_count < 5:
                if hs > as_: home_pts += 3
                elif hs == as_: home_pts += 1
                home_total += 3
                home_count += 1

            elif m["awayTeam"]["id"] == team_id and away_count < 5:
                if as_ > hs: away_pts += 3
                elif hs == as_: away_pts += 1
                away_total += 3
                away_count += 1

        except:
            continue

    home_strength = home_pts / home_total if home_total else 0.5
    away_strength = away_pts / away_total if away_total else 0.5

    return home_strength, away_strength

# -------------------------
# xG / SHOTS
# -------------------------

def get_event_stats(event_id):
    try:
        url = f"https://api.sofascore.com/api/v1/event/{event_id}/statistics"
        data = requests.get(url).json()
        stats = data["statistics"][0]["groups"]

        def find(name):
            for g in stats:
                for s in g["statisticsItems"]:
                    if s["name"] == name:
                        return float(s["home"]), float(s["away"])
            return 0,0

        return find("Expected goals"), find("Total shots")
    except:
        return (0,0),(0,0)


def calculate_averages(team_id):

    matches = get_team_matches(team_id, 10)

    xg_total = shots_total = count = 0

    for m in matches:
        try:
            (xh,xa),(sh,sa) = get_event_stats(m["id"])

            if m["homeTeam"]["id"] == team_id:
                xg_total += xh
                shots_total += sh
            else:
                xg_total += xa
                shots_total += sa

            count += 1
        except:
            continue

    if count == 0:
        return 1,10

    return xg_total/count, shots_total/count

# -------------------------
# MODELOS
# -------------------------

def model_dominance(h,a):
    hxg,hs = calculate_averages(h)
    axg,as_ = calculate_averages(a)
    return (hxg-axg)*1.5 + (hs-as_)*0.05

def model_consistency(h,a):
    hf = calculate_form_10(h)
    af = calculate_form_10(a)

    h_home,_ = calculate_home_away_strength(h)
    _,a_away = calculate_home_away_strength(a)

    return (hf-af)*1.5 + (h_home - a_away)

def model_balanced(h,a):
    hf = calculate_form_10(h)
    af = calculate_form_10(a)

    hxg,_ = calculate_averages(h)
    axg,_ = calculate_averages(a)

    return (hf-af)*1.2 + (hxg-axg)*0.8

def model_chaos(h,a):
    hf = calculate_form_10(h)
    af = calculate_form_10(a)
    return (hf-af)*1.5

# -------------------------
# PREDIÇÃO
# -------------------------

def predict(e):

    league_id = e["tournament"]["uniqueTournament"]["id"]

    h = e["homeTeam"]["id"]
    a = e["awayTeam"]["id"]

    if league_id in DOMINANCE:
        score = model_dominance(h,a)
    elif league_id in CONSISTENCY:
        score = model_consistency(h,a)
    elif league_id in BALANCED:
        score = model_balanced(h,a)
    else:
        score = model_chaos(h,a)

    return ("HOME" if score > 0 else "AWAY"), abs(score)

# -------------------------
# UI
# -------------------------

st.title("⚽ Scanner PRO (Contexto Real 10 + 5/5)")

date = st.date_input("Escolha a data")

events = get_events(date.strftime("%Y-%m-%d"))

filtered = [e for e in events if is_valid_league(e) and is_same_day_br(e,date)]

st.write(f"Jogos válidos: {len(filtered)}")

# -------------------------
# EXECUÇÃO
# -------------------------

if st.button("Analisar Jogos"):

    rows = []

    for e in filtered:

        pick,edge = predict(e)

        if edge < 0.5:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        hora = utc.astimezone(BR_TZ).strftime("%H:%M")

        rows.append({
            "Hora": hora,
            "Jogo": f"{e['homeTeam']['name']} vs {e['awayTeam']['name']}",
            "Pick": pick,
            "Edge": round(edge,2),
            "Classificação": "ELITE" if edge>=1 else "BOM"
        })

    if rows:
        df = pd.DataFrame(rows).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sem oportunidades relevantes.")
