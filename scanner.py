import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

# -----------------------------
# CONFIG
# -----------------------------

BR_TZ = pytz.timezone("America/Sao_Paulo")

VALID_LEAGUE_IDS = [
    325,390,17,18,8,54,35,44,23,53,34,182,955,
    155,703,45,38,247,172,11653,11539,11536,
    170,39,808,36,242,185,37,131,192,937,
    11621,11620,20,11540,11541,406,202,
    238,239,152,40,215,52,278
]

# -----------------------------
# API SOFASCORE
# -----------------------------

def get_events(date):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
    return requests.get(url).json().get("events", [])

def get_team_matches(team_id, n=25):
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/{n}"
    return requests.get(url).json().get("events", [])

# -----------------------------
# FILTROS
# -----------------------------

def is_valid_league(event):
    try:
        return event["tournament"]["uniqueTournament"]["id"] in VALID_LEAGUE_IDS
    except:
        return False

def is_same_day(event, date):
    utc = datetime.utcfromtimestamp(event["startTimestamp"]).replace(tzinfo=pytz.utc)
    return utc.astimezone(BR_TZ).date() == date

# -----------------------------
# FORMA (W/D/L)
# -----------------------------

def get_form(team_id, limit=10):

    matches = get_team_matches(team_id, 30)

    w = d = l = gf = ga = 0
    count = 0

    for m in matches:
        try:
            if m.get("status", {}).get("type") != "finished":
                continue

            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if m["homeTeam"]["id"] == team_id:
                gf += hs
                ga += as_

                if hs > as_:
                    w += 1
                elif hs == as_:
                    d += 1
                else:
                    l += 1

            else:
                gf += as_
                ga += hs

                if as_ > hs:
                    w += 1
                elif hs == as_:
                    d += 1
                else:
                    l += 1

            count += 1
            if count == limit:
                break

        except:
            continue

    return {
        "w": w,
        "d": d,
        "l": l,
        "gf": gf,
        "ga": ga,
        "gd": gf - ga
    }

# -----------------------------
# HOME / AWAY (5 JOGOS)
# -----------------------------

def get_home_away(team_id, is_home):

    matches = get_team_matches(team_id, 30)

    w = d = l = gf = ga = 0
    count = 0

    for m in matches:
        try:
            if m.get("status", {}).get("type") != "finished":
                continue

            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if is_home and m["homeTeam"]["id"] == team_id:

                gf += hs
                ga += as_

                if hs > as_:
                    w += 1
                elif hs == as_:
                    d += 1
                else:
                    l += 1

                count += 1

            elif not is_home and m["awayTeam"]["id"] == team_id:

                gf += as_
                ga += hs

                if as_ > hs:
                    w += 1
                elif hs == as_:
                    d += 1
                else:
                    l += 1

                count += 1

            if count == 5:
                break

        except:
            continue

    return {
        "w": w,
        "d": d,
        "l": l,
        "gf": gf,
        "ga": ga,
        "gd": gf - ga
    }

# -----------------------------
# VALIDAÇÃO SIMPLES (CORRETA)
# -----------------------------

def has_min_10_games(team_id):

    matches = get_team_matches(team_id, 30)

    finished = 0

    for m in matches:
        if m.get("status", {}).get("type") == "finished":
            finished += 1

    return finished >= 10

# -----------------------------
# COMPARAÇÃO FINAL
# -----------------------------

def evaluate(home_id, away_id):

    home = get_form(home_id)
    away = get_form(away_id)

    home_home = get_home_away(home_id, True)
    away_away = get_home_away(away_id, False)

    score_h = 0
    score_a = 0

    # forma geral
    home_points = home["w"] * 3 + home["d"]
    away_points = away["w"] * 3 + away["d"]

    if home_points > away_points:
        score_h += 1
    elif away_points > home_points:
        score_a += 1

    # saldo geral
    if home["gd"] > away["gd"]:
        score_h += 1
    elif away["gd"] > home["gd"]:
        score_a += 1

    # forma home vs away
    home_home_points = home_home["w"] * 3 + home_home["d"]
    away_away_points = away_away["w"] * 3 + away_away["d"]

    if home_home_points > away_away_points:
        score_h += 1
    elif away_away_points > home_home_points:
        score_a += 1

    # saldo home vs away
    if home_home["gd"] > away_away["gd"]:
        score_h += 1
    elif away_away["gd"] > home_home["gd"]:
        score_a += 1

    if score_h > score_a:
        return "HOME", score_h - score_a
    elif score_a > score_h:
        return "AWAY", score_a - score_h
    else:
        return "SKIP", 0

# -----------------------------
# STREAMLIT UI
# -----------------------------

st.title("⚽ Greg Stats V5 - Stable Engine")

date = st.date_input("Escolha a data")

events = get_events(date.strftime("%Y-%m-%d"))

results = []

for e in events:

    if not is_valid_league(e):
        continue

    if not is_same_day(e, date):
        continue

    home_id = e["homeTeam"]["id"]
    away_id = e["awayTeam"]["id"]

    # 🔥 filtro correto agora simples e confiável
    if not has_min_10_games(home_id):
        continue
    if not has_min_10_games(away_id):
        continue

    winner, edge = evaluate(home_id, away_id)

    if winner == "SKIP":
        continue

    utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
    br_time = utc.astimezone(BR_TZ).strftime("%H:%M")

    results.append({
        "Hora": br_time,
        "Jogo": f"{e['homeTeam']['name']} vs {e['awayTeam']['name']}",
        "Pick": winner,
        "Edge": edge,
        "Força": "ALTA" if edge >= 2 else "MEDIA"
    })

if results:
    df = pd.DataFrame(results).sort_values("Edge", ascending=False)
    st.dataframe(df, use_container_width=True)
    st.write(f"Total de picks: {len(df)}")
else:
    st.warning("Nenhuma oportunidade encontrada.")
