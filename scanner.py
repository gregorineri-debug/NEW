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

LEAGUE_NAMES = { ... }  # mantém igual

# -------------------------
# API
# -------------------------

def get_events(date):
    try:
        url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
        return requests.get(url).json().get("events", [])
    except:
        return []

def get_team_matches(team_id, limit=30):
    try:
        url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/{limit}"
        return requests.get(url).json().get("events", [])
    except:
        return []

# -------------------------
# CALC OVER RATE
# -------------------------

def calc_over_rate(matches, team_id, venue=None, last_n=10):

    count = 0
    over = 0

    for m in matches[:last_n]:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if hs is None or as_ is None:
                continue

            # filtro casa/fora
            if venue == "home" and m["homeTeam"]["id"] != team_id:
                continue
            if venue == "away" and m["awayTeam"]["id"] != team_id:
                continue

            total = hs + as_

            if total > 2.5:
                over += 1

            count += 1
        except:
            continue

    if count == 0:
        return 0.5

    return over / count

# -------------------------
# MOTOR OVER/UNDER 2.5
# -------------------------

def evaluate_goals(home_id, away_id):

    home_matches = get_team_matches(home_id, 30)
    away_matches = get_team_matches(away_id, 30)

    # -------------------------
    # GERAL
    # -------------------------
    h30 = calc_over_rate(home_matches, home_id, None, 30)
    h10 = calc_over_rate(home_matches, home_id, None, 10)
    h5  = calc_over_rate(home_matches, home_id, None, 5)

    a30 = calc_over_rate(away_matches, away_id, None, 30)
    a10 = calc_over_rate(away_matches, away_id, None, 10)
    a5  = calc_over_rate(away_matches, away_id, None, 5)

    # validação progressiva
    if not (h30 > 0.55 and h10 > 0.55 and h5 > 0.55 and
            a30 > 0.55 and a10 > 0.55 and a5 > 0.55):
        over_general = False
    else:
        over_general = True

    if not (h30 < 0.45 and h10 < 0.45 and h5 < 0.45 and
            a30 < 0.45 and a10 < 0.45 and a5 < 0.45):
        under_general = False
    else:
        under_general = True

    # -------------------------
    # CASA / FORA
    # -------------------------
    h_home_30 = calc_over_rate(home_matches, home_id, "home", 30)
    h_home_10 = calc_over_rate(home_matches, home_id, "home", 10)
    h_home_5  = calc_over_rate(home_matches, home_id, "home", 5)

    a_away_30 = calc_over_rate(away_matches, away_id, "away", 30)
    a_away_10 = calc_over_rate(away_matches, away_id, "away", 10)
    a_away_5  = calc_over_rate(away_matches, away_id, "away", 5)

    if not (h_home_30 > 0.55 and h_home_10 > 0.55 and h_home_5 > 0.55 and
            a_away_30 > 0.55 and a_away_10 > 0.55 and a_away_5 > 0.55):
        over_context = False
    else:
        over_context = True

    if not (h_home_30 < 0.45 and h_home_10 < 0.45 and h_home_5 < 0.45 and
            a_away_30 < 0.45 and a_away_10 < 0.45 and a_away_5 < 0.45):
        under_context = False
    else:
        under_context = True

    # -------------------------
    # DECISÃO FINAL
    # -------------------------
    if over_general and over_context:
        return "OVER 2.5", max(h5, a5)

    if under_general and under_context:
        return "UNDER 2.5", 1 - max(h5, a5)

    return None, 0

# -------------------------
# UI
# -------------------------

st.title("⚽ Scanner PRO (Over/Under 2.5 Profissional)")

date = st.date_input("Escolha a data")

events = get_events(date.strftime("%Y-%m-%d"))

filtered = []

for e in events:
    try:
        lid = e["tournament"]["uniqueTournament"]["id"]

        if lid not in VALID_LEAGUE_IDS:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        br = utc.astimezone(BR_TZ)

        if br.date() != date:
            continue

        filtered.append(e)
    except:
        continue

st.write(f"Jogos: {len(filtered)}")

if st.button("Analisar"):

    rows = []

    for e in filtered:

        result, confidence = evaluate_goals(
            e["homeTeam"]["id"],
            e["awayTeam"]["id"]
        )

        if not result:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        hora = utc.astimezone(BR_TZ).strftime("%H:%M")

        rows.append({
            "Hora": hora,
            "Liga": LEAGUE_NAMES.get(e["tournament"]["uniqueTournament"]["id"], ""),
            "Jogo": f'{e["homeTeam"]["name"]} vs {e["awayTeam"]["name"]}',
            "Pick": result,
            "Confiança": round(confidence,2)
        })

    if rows:
        df = pd.DataFrame(rows).sort_values(by="Confiança", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Nenhuma oportunidade encontrada.")
