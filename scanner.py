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

# -------------------------
# MODELOS POR LIGA
# -------------------------

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

# -------------------------
# FILTROS
# -------------------------

def is_valid_league(event):
    try:
        return event["tournament"]["uniqueTournament"]["id"] in VALID_LEAGUE_IDS
    except:
        return False


def is_same_day_br(event, selected_date):
    utc = datetime.utcfromtimestamp(event["startTimestamp"]).replace(tzinfo=pytz.utc)
    return utc.astimezone(BR_TZ).date() == selected_date

# -------------------------
# DADOS
# -------------------------

def get_team_last_matches(team_id):
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/5"
    return requests.get(url).json().get("events", [])


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
            return 0, 0

        return find("Expected goals"), find("Total shots")
    except:
        return (0,0),(0,0)

# -------------------------
# BASE
# -------------------------

def calculate_form(team_id):
    matches = get_team_last_matches(team_id)
    points = 0
    total = 0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if m["homeTeam"]["id"] == team_id:
                if hs > as_: points += 3
                elif hs == as_: points += 1
            else:
                if as_ > hs: points += 3
                elif hs == as_: points += 1

            total += 3
        except:
            continue

    return points / total if total else 0.5


def calculate_home_strength(team_id):
    matches = get_team_last_matches(team_id)
    points = 0
    total = 0

    for m in matches:
        try:
            if m["homeTeam"]["id"] != team_id:
                continue

            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if hs > as_: points += 3
            elif hs == as_: points += 1

            total += 3
        except:
            continue

    return points / total if total else 0.5


def calculate_averages(team_id):
    matches = get_team_last_matches(team_id)
    xg_total = 0
    shots_total = 0
    count = 0

    for m in matches:
        try:
            (xg_h,xg_a),(s_h,s_a) = get_event_stats(m["id"])

            if m["homeTeam"]["id"] == team_id:
                xg_total += xg_h
                shots_total += s_h
            else:
                xg_total += xg_a
                shots_total += s_a

            count += 1
        except:
            continue

    if count == 0:
        return 1, 10

    return xg_total / count, shots_total / count

# -------------------------
# MODELOS
# -------------------------

def model_dominance(home_id, away_id):
    hxg, hs = calculate_averages(home_id)
    axg, as_ = calculate_averages(away_id)

    return (hxg - axg)*1.5 + (hs - as_)*0.05


def model_consistency(home_id, away_id):
    return (calculate_form(home_id) - calculate_form(away_id))*1.8 + calculate_home_strength(home_id)


def model_balanced(home_id, away_id):
    hf = calculate_form(home_id)
    af = calculate_form(away_id)
    hxg, _ = calculate_averages(home_id)
    axg, _ = calculate_averages(away_id)

    return (hf - af)*1.2 + (hxg - axg)*0.8


def model_chaos(home_id, away_id):
    # 🔥 só força bruta + filtro
    return (calculate_form(home_id) - calculate_form(away_id))*1.5

# -------------------------
# PREDIÇÃO
# -------------------------

def predict(e):

    league_id = e["tournament"]["uniqueTournament"]["id"]

    home_id = e["homeTeam"]["id"]
    away_id = e["awayTeam"]["id"]

    if league_id in DOMINANCE:
        score = model_dominance(home_id, away_id)
    elif league_id in CONSISTENCY:
        score = model_consistency(home_id, away_id)
    elif league_id in BALANCED:
        score = model_balanced(home_id, away_id)
    else:
        score = model_chaos(home_id, away_id)

    return ("HOME" if score > 0 else "AWAY"), abs(score)

# -------------------------
# UI
# -------------------------

st.title("⚽ Scanner PRO (4 Modelos Inteligentes)")

date = st.date_input("Escolha a data")

events = get_events(date.strftime("%Y-%m-%d"))

filtered_events = [
    e for e in events
    if is_valid_league(e) and is_same_day_br(e, date)
]

st.write(f"Jogos válidos: {len(filtered_events)}")

# -------------------------
# EXECUÇÃO
# -------------------------

if st.button("Analisar Jogos"):

    results = []

    for e in filtered_events:

        winner, edge = predict(e)

        if edge < 0.5:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        br_time = utc.astimezone(BR_TZ).strftime("%H:%M")

        results.append({
            "Hora": br_time,
            "Jogo": f"{e['homeTeam']['name']} vs {e['awayTeam']['name']}",
            "Pick": winner,
            "Edge": round(edge,2),
            "Classificação": "ELITE" if edge >= 1 else "BOM"
        })

    if results:
        df = pd.DataFrame(results).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Nenhuma oportunidade encontrada.")
