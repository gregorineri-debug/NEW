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

LEAGUE_NAMES = {
    325: "Brasileirão",
    390: "Série B",
    17: "Premier League",
    18: "Championship",
    8: "La Liga",
    54: "La Liga 2",
    35: "Bundesliga",
    44: "2. Bundesliga",
    23: "Serie A",
    53: "Serie B Itália",
    34: "Ligue 1",
    182: "Ligue 2",
    955: "Saudi Pro League",
    155: "Argentina Liga",
    703: "Primera Nacional",
    45: "Áustria",
    38: "Bélgica",
    247: "Bulgária",
    172: "Rep. Tcheca",
    11653: "Chile",
    11539: "Colômbia Apertura",
    11536: "Colômbia Finalización",
    170: "Croácia",
    39: "Dinamarca",
    808: "Egito",
    36: "Escócia",
    242: "MLS",
    185: "Grécia",
    37: "Eredivisie",
    131: "Eerste Divisie",
    192: "Irlanda",
    937: "Marrocos",
    11621: "Liga MX Apertura",
    11620: "Liga MX Clausura",
    20: "Noruega",
    11540: "Paraguai Apertura",
    11541: "Paraguai Clausura",
    406: "Peru",
    202: "Polônia",
    238: "Portugal",
    239: "Portugal 2",
    152: "Romênia",
    40: "Suécia",
    215: "Suíça",
    52: "Turquia",
    278: "Uruguai"
}

# -------------------------
# API
# -------------------------

def get_events(date):
    try:
        url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
        return requests.get(url).json().get("events", [])
    except:
        return []

def get_team_matches(team_id, limit=10):
    try:
        url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/{limit}"
        return requests.get(url).json().get("events", [])
    except:
        return []

# -------------------------
# MÉTRICAS NOVAS
# -------------------------

def get_team_stats(team_id):

    matches = get_team_matches(team_id, 10)

    wins = 0
    goals_for = 0
    goals_against = 0
    games = 0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if hs is None or as_ is None:
                continue

            if m["homeTeam"]["id"] == team_id:
                gf, ga = hs, as_
                if hs > as_:
                    wins += 1
            else:
                gf, ga = as_, hs
                if as_ > hs:
                    wins += 1

            goals_for += gf
            goals_against += ga
            games += 1
        except:
            continue

    if games == 0:
        return 0.5, 1, 1

    winrate = wins / games
    avg_gf = goals_for / games
    avg_ga = goals_against / games

    return winrate, avg_gf, avg_ga

# -------------------------
# PERFIL DE LIGAS
# -------------------------

OVER_LEAGUES = [35, 44, 37, 131, 242, 20]
UNDER_LEAGUES = [155, 703, 11540, 11541, 278, 406]

# -------------------------
# SCORE
# -------------------------

def calculate_score(home_id, away_id, league_id):

    h_win, h_gf, h_ga = get_team_stats(home_id)
    a_win, a_gf, a_ga = get_team_stats(away_id)

    home_strength = (h_win * 1.5) + (h_gf * 0.8)
    away_strength = (a_win * 1.5) + (a_gf * 0.8)

    home_weak = h_ga * 0.7
    away_weak = a_ga * 0.7

    home_adv = 0.25
    away_penalty = 0.15

    score = (home_strength - away_weak + home_adv) - (away_strength - home_weak + away_penalty)

    return score

# -------------------------
# PREDICT
# -------------------------

def predict(e):

    league_id = e["tournament"]["uniqueTournament"]["id"]

    score = calculate_score(
        e["homeTeam"]["id"],
        e["awayTeam"]["id"],
        league_id
    )

    winner = "HOME" if score > 0 else "AWAY"
    edge = abs(score)

    # GOLS
    h_win, h_gf, h_ga = get_team_stats(e["homeTeam"]["id"])
    a_win, a_gf, a_ga = get_team_stats(e["awayTeam"]["id"])

    avg_total_goals = (h_gf + h_ga + a_gf + a_ga) / 2

    if league_id in OVER_LEAGUES:
        goal_pick = "OVER 2.5"
    elif league_id in UNDER_LEAGUES:
        goal_pick = "UNDER 2.5"
    else:
        if avg_total_goals >= 2.8:
            goal_pick = "OVER 2.5"
        elif avg_total_goals <= 2.2:
            goal_pick = "UNDER 2.5"
        else:
            goal_pick = "BTTS"

    return winner, edge, goal_pick

# -------------------------
# UI
# -------------------------

st.title("⚽ Scanner PRO (Filtro por Liga)")

date = st.date_input("Escolha a data")

league_options = ["Todas"] + list(LEAGUE_NAMES.values())
selected_league = st.selectbox("Escolha a liga", league_options)

events = get_events(date.strftime("%Y-%m-%d"))

filtered_events = []

for e in events:
    try:
        if e["tournament"]["uniqueTournament"]["id"] not in VALID_LEAGUE_IDS:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        br_time = utc.astimezone(BR_TZ)

        if br_time.date() != date:
            continue

        league_id = e["tournament"]["uniqueTournament"]["id"]
        league_name = LEAGUE_NAMES.get(league_id, "Outra")

        if selected_league != "Todas" and league_name != selected_league:
            continue

        filtered_events.append(e)
    except:
        continue

st.write(f"Jogos válidos: {len(filtered_events)}")

if st.button("Analisar Jogos"):

    results = []

    for e in filtered_events:

        winner, edge, goals = predict(e)

        if edge < 0.30:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        br_time = utc.astimezone(BR_TZ).strftime("%H:%M")

        tag = "ELITE" if edge >= 0.8 else "BOM"

        results.append({
            "Hora": br_time,
            "Liga": LEAGUE_NAMES.get(e["tournament"]["uniqueTournament"]["id"], "Outra"),
            "Jogo": f'{e["homeTeam"]["name"]} vs {e["awayTeam"]["name"]}',
            "Pick": winner,
            "Mercado Gols": goals,
            "Edge": round(edge, 2),
            "Classificação": tag
        })

    if results:
        df = pd.DataFrame(results).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)
        st.write(f"Total de picks relevantes: {len(df)}")
    else:
        st.warning("Nenhuma oportunidade encontrada.")
