import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

BR_TZ = pytz.timezone("America/Sao_Paulo")

VALID_LEAGUE_IDS = [
    325,390,17,18,8,54,35,44,23,53,34,182,955,
    155,703,45,38,247,172,11653,11539,11536,
    170,39,808,36,242,185,37,131,192,937,
    11621,11620,20,11540,11541,406,202,
    238,239,152,40,215,52,278
]

LEAGUE_NAMES = {
    325: "Brasileirão", 390: "Série B", 17: "Premier League",
    18: "Championship", 8: "La Liga", 54: "La Liga 2",
    35: "Bundesliga", 44: "2. Bundesliga", 23: "Serie A",
    53: "Serie B Itália", 34: "Ligue 1", 182: "Ligue 2",
    955: "Saudi Pro League", 155: "Argentina Liga",
    703: "Primera Nacional", 45: "Áustria", 38: "Bélgica",
    247: "Bulgária", 172: "Rep. Tcheca", 11653: "Chile",
    11539: "Colômbia Apertura", 11536: "Colômbia Finalización",
    170: "Croácia", 39: "Dinamarca", 808: "Egito",
    36: "Escócia", 242: "MLS", 185: "Grécia",
    37: "Eredivisie", 131: "Eerste Divisie", 192: "Irlanda",
    937: "Marrocos", 11621: "Liga MX Apertura",
    11620: "Liga MX Clausura", 20: "Noruega",
    11540: "Paraguai Apertura", 11541: "Paraguai Clausura",
    406: "Peru", 202: "Polônia", 238: "Portugal",
    239: "Portugal 2", 152: "Romênia", 40: "Suécia",
    215: "Suíça", 52: "Turquia", 278: "Uruguai"
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

def get_odds(event_id):
    try:
        url = f"https://api.sofascore.com/api/v1/event/{event_id}/odds/1/all"
        data = requests.get(url).json()

        markets = data.get("markets", [])
        for m in markets:
            if m.get("marketName") == "Full time":
                choices = m.get("choices", [])
                odds = {c["name"]: float(c["odds"]) for c in choices}
                return odds.get("1"), odds.get("2")
    except:
        pass
    return None, None

# -------------------------
# STATS
# -------------------------

def get_team_stats(team_id):

    matches = get_team_matches(team_id, 10)

    wins, gf, ga, games = 0,0,0,0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if hs is None or as_ is None:
                continue

            if m["homeTeam"]["id"] == team_id:
                if hs > as_: wins += 1
                gf += hs; ga += as_
            else:
                if as_ > hs: wins += 1
                gf += as_; ga += hs

            games += 1
        except:
            continue

    if games == 0:
        return 0.5,1,1

    return wins/games, gf/games, ga/games

# -------------------------
# LIGAS
# -------------------------

STRONG_HOME = [325,390,155,703,278,11540,11541]
WEAK_HOME = [35,44,37,131,242,20]

def home_adv(lid):
    if lid in STRONG_HOME: return 0.45
    if lid in WEAK_HOME: return 0.20
    return 0.30

def elite_away(win, gf):
    return win >= 0.6 and gf >= 1.5

# -------------------------
# SCORE
# -------------------------

def calculate_score(h, a, lid):

    hw, hgf, hga = get_team_stats(h)
    aw, agf, aga = get_team_stats(a)

    hs = hw*1.6 + hgf*0.9
    as_ = aw*1.6 + agf*0.9

    hwk = hga*0.8
    awk = aga*0.8

    adv = home_adv(lid)

    if elite_away(aw, agf):
        pen = 0.15
    else:
        diff = as_ - hs
        pen = 0.5 if diff < 0.3 else 0.35 if diff < 0.7 else 0.25

    return (hs - awk + adv) - (as_ - hwk + pen)

# -------------------------
# PROBABILIDADE
# -------------------------

def score_to_prob(score):
    import math
    return 1 / (1 + math.exp(-score))

# -------------------------
# PREDICT
# -------------------------

def predict(e):

    lid = e["tournament"]["uniqueTournament"]["id"]

    score = calculate_score(e["homeTeam"]["id"], e["awayTeam"]["id"], lid)

    prob_home = score_to_prob(score)
    prob_away = 1 - prob_home

    odd_home, odd_away = get_odds(e["id"])

    if not odd_home or not odd_away:
        return None

    implied_home = 1 / odd_home
    implied_away = 1 / odd_away

    value_home = prob_home - implied_home
    value_away = prob_away - implied_away

    if value_home > value_away:
        pick = "HOME"
        edge = value_home
        odd = odd_home
    else:
        pick = "AWAY"
        edge = value_away
        odd = odd_away

    if pick == "AWAY" and edge < 0.05:
        return None

    # GOLS
    hw, hgf, hga = get_team_stats(e["homeTeam"]["id"])
    aw, agf, aga = get_team_stats(e["awayTeam"]["id"])

    avg = (hgf + hga + agf + aga)/2

    if lid in WEAK_HOME:
        goals = "OVER 2.5"
    elif lid in STRONG_HOME:
        goals = "UNDER 2.5"
    else:
        goals = "OVER 2.5" if avg >= 2.8 else "UNDER 2.5" if avg <= 2.2 else "BTTS"

    tag = "🔥 VALUE" if edge > 0.08 else "OK"

    return pick, edge, odd, goals, tag

# -------------------------
# UI
# -------------------------

st.title("⚽ Scanner PRO + VALUE BET")

date = st.date_input("Escolha a data")

league_options = ["Todas"] + list(LEAGUE_NAMES.values())
selected_league = st.selectbox("Liga", league_options)

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

        league_name = LEAGUE_NAMES.get(lid, "Outra")

        if selected_league != "Todas" and league_name != selected_league:
            continue

        filtered.append(e)
    except:
        continue

st.write(f"Jogos: {len(filtered)}")

if st.button("Analisar"):

    rows = []

    for e in filtered:

        result = predict(e)

        if not result:
            continue

        pick, edge, odd, goals, tag = result

        if edge < 0.02:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        hora = utc.astimezone(BR_TZ).strftime("%H:%M")

        rows.append({
            "Hora": hora,
            "Liga": LEAGUE_NAMES.get(e["tournament"]["uniqueTournament"]["id"], ""),
            "Jogo": f'{e["homeTeam"]["name"]} vs {e["awayTeam"]["name"]}',
            "Pick": pick,
            "Odd": round(odd,2),
            "Edge": round(edge,3),
            "Gols": goals,
            "Tipo": tag
        })

    if rows:
        df = pd.DataFrame(rows).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sem valor hoje.")
