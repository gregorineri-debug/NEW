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

LEAGUE_NAMES = { ... }  # (mantido igual ao seu)

# -------------------------
# API
# -------------------------

def get_events(date):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
    return requests.get(url).json().get("events", [])

def get_team_matches(team_id, limit=10):
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/{limit}"
    return requests.get(url).json().get("events", [])

def get_event_stats(event_id):
    try:
        url = f"https://api.sofascore.com/api/v1/event/{event_id}/statistics"
        data = requests.get(url).json()
        stats = data["statistics"][0]["groups"]

        for g in stats:
            for s in g["statisticsItems"]:
                if s["name"] == "Expected goals":
                    return float(s["home"]), float(s["away"])
        return 0,0
    except:
        return 0,0

# -------------------------
# MÉTRICAS
# -------------------------

def calc_points(matches, team_id):
    pts, total = 0, 0
    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if m["homeTeam"]["id"] == team_id:
                pts += 3 if hs > as_ else 1 if hs == as_ else 0
            else:
                pts += 3 if as_ > hs else 1 if hs == as_ else 0

            total += 3
        except:
            continue
    return pts / total if total else 0.5


def calc_home_away(team_id):
    matches = get_team_matches(team_id, 10)

    home = [m for m in matches if m["homeTeam"]["id"] == team_id][:5]
    away = [m for m in matches if m["awayTeam"]["id"] == team_id][:5]

    return calc_points(home, team_id), calc_points(away, team_id)


def calc_opponent_strength(matches, team_id):
    total = 0
    count = 0

    for m in matches:
        try:
            opp_id = m["awayTeam"]["id"] if m["homeTeam"]["id"] == team_id else m["homeTeam"]["id"]
            opp_matches = get_team_matches(opp_id, 5)
            total += calc_points(opp_matches, opp_id)
            count += 1
        except:
            continue

    return total / count if count else 0.5


def calc_xg(team_id):
    matches = get_team_matches(team_id, 5)

    total = 0
    count = 0

    for m in matches:
        try:
            xg_h, xg_a = get_event_stats(m["id"])

            if m["homeTeam"]["id"] == team_id:
                total += xg_h
            else:
                total += xg_a

            count += 1
        except:
            continue

    return total / count if count else 1.0

# -------------------------
# SCORE NOVO
# -------------------------

def calculate_score(home_id, away_id):

    home_matches = get_team_matches(home_id, 10)
    away_matches = get_team_matches(away_id, 10)

    # Forma geral
    hf = calc_points(home_matches, home_id)
    af = calc_points(away_matches, away_id)

    # Casa / Fora
    h_home, _ = calc_home_away(home_id)
    _, a_away = calc_home_away(away_id)

    # Força adversário
    hos = calc_opponent_strength(home_matches, home_id)
    aos = calc_opponent_strength(away_matches, away_id)

    # xG
    hxg = calc_xg(home_id)
    axg = calc_xg(away_id)

    # DIFERENÇAS
    form_diff = hf - af
    home_away_diff = h_home - a_away
    opp_diff = hos - aos
    xg_diff = hxg - axg

    score = (
        form_diff * 0.50 +
        home_away_diff * 0.35 +
        opp_diff * 0.15 +
        xg_diff * 0.20
    )

    return score

# -------------------------
# RESTANTE IGUAL
# -------------------------

def predict(e):
    score = calculate_score(e["homeTeam"]["id"], e["awayTeam"]["id"])
    return ("HOME" if score > 0 else "AWAY"), abs(score)


def validate_pick(event, pick):
    try:
        hs = event["homeScore"]["current"]
        as_ = event["awayScore"]["current"]

        if hs is None or as_ is None:
            return "null"

        if pick == "HOME":
            return "WIN" if hs > as_ else "LOSS"
        else:
            return "WIN" if as_ > hs else "LOSS"
    except:
        return "null"

# -------------------------
# UI (100% IGUAL)
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

col1, col2 = st.columns(2)
analyze_btn = col1.button("Analisar Jogos")
backtest_btn = col2.button("Backtest (Validar Picks)")

if analyze_btn or backtest_btn:

    results = []

    for e in filtered_events:

        winner, edge = predict(e)

        if edge < 0.5:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        br_time = utc.astimezone(BR_TZ).strftime("%H:%M")

        tag = "ELITE" if edge >= 1.0 else "BOM"
        result_status = validate_pick(e, winner) if backtest_btn else ""

        results.append({
            "Hora": br_time,
            "Liga": LEAGUE_NAMES.get(e["tournament"]["uniqueTournament"]["id"], "Outra"),
            "Jogo": f'{e["homeTeam"]["name"]} vs {e["awayTeam"]["name"]}',
            "Pick": winner,
            "Edge": round(edge, 2),
            "Classificação": tag,
            "Resultado": result_status
        })

    if results:
        df = pd.DataFrame(results).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)

        if backtest_btn:
            valid = df[df["Resultado"].isin(["WIN","LOSS"])]

            if len(valid):
                total_win = (valid["Resultado"]=="WIN").sum()
                elite = valid[valid["Classificação"]=="ELITE"]

                st.write(f"Winrate Total: {round(total_win/len(valid)*100,2)}%")

                if len(elite):
                    elite_win = (elite["Resultado"]=="WIN").sum()
                    st.write(f"Winrate ELITE: {round(elite_win/len(elite)*100,2)}%")
