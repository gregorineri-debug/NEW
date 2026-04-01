import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

# -------------------------
# CONFIG
# -------------------------
BR_TZ = ZoneInfo("America/Sao_Paulo")

MIN_MATCHES = 5  # 🔥 menos rígido

LEAGUE_STRENGTH = {
    17: 1.0, 8: 1.0, 23: 1.0, 35: 1.0, 34: 1.0,
    325: 0.9, 390: 0.85,
    155: 0.9,
    238: 0.9,
    242: 0.85,
}

DEFAULT_LEAGUE_STRENGTH = 0.8

# 🔥 VOLTAMOS TODAS AS LIGAS
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
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
    return requests.get(url).json().get("events", [])

def get_standings(tournament_id, season_id):
    try:
        url = f"https://api.sofascore.com/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        data = requests.get(url).json()
        return data["standings"][0]["rows"]
    except:
        return []

# -------------------------
# FILTROS
# -------------------------

def is_valid_league(event):
    try:
        return event["tournament"]["uniqueTournament"]["id"] in VALID_LEAGUE_IDS
    except:
        return False


def is_same_day_br(event, selected_date):
    utc = datetime.utcfromtimestamp(event["startTimestamp"]).replace(tzinfo=ZoneInfo("UTC"))
    br_time = utc.astimezone(BR_TZ)
    return br_time.date() == selected_date

# -------------------------
# STATS
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
# CRITÉRIOS NOVOS
# -------------------------

def calculate_league_strength(league_id):
    return LEAGUE_STRENGTH.get(league_id, DEFAULT_LEAGUE_STRENGTH)


def calculate_motivation(team_id, standings):
    try:
        for row in standings:
            if row["team"]["id"] == team_id:
                pos = row["position"]
                total = len(standings)

                if pos <= 3:
                    return 1.0
                elif pos >= total - 3:
                    return 1.0
                else:
                    return 0.5
    except:
        pass

    return 0.5


def check_min_matches(standings):
    try:
        games = standings[0].get("matches", 0)
        return games >= MIN_MATCHES
    except:
        return False


def estimate_lineup_impact(team_id):
    matches = get_team_last_matches(team_id)

    if len(matches) < 3:
        return 0

    wins = 0
    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if m["homeTeam"]["id"] == team_id and hs > as_:
                wins += 1
            elif m["awayTeam"]["id"] == team_id and as_ > hs:
                wins += 1
        except:
            continue

    if wins <= 1:
        return -0.2

    return 0

# -------------------------
# BASE ORIGINAL
# -------------------------

def calculate_form(team_id):

    matches = get_team_last_matches(team_id)

    points = 0
    total_weight = 0

    for m in matches:
        try:
            opponent_id = (
                m["awayTeam"]["id"] if m["homeTeam"]["id"] == team_id
                else m["homeTeam"]["id"]
            )

            opponent_matches = get_team_last_matches(opponent_id)

            opp_points = 0
            opp_total = 0

            for om in opponent_matches:
                try:
                    hs = om["homeScore"]["current"]
                    as_ = om["awayScore"]["current"]

                    if om["homeTeam"]["id"] == opponent_id:
                        if hs > as_: opp_points += 3
                        elif hs == as_: opp_points += 1
                    else:
                        if as_ > hs: opp_points += 3
                        elif hs == as_: opp_points += 1

                    opp_total += 3
                except:
                    continue

            opponent_form = opp_points / opp_total if opp_total else 0.5
            weight = 0.5 + opponent_form

            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if m["homeTeam"]["id"] == team_id:
                result = 3 if hs > as_ else 1 if hs == as_ else 0
            else:
                result = 3 if as_ > hs else 1 if hs == as_ else 0

            points += result * weight
            total_weight += 3 * weight

        except:
            continue

    return points / total_weight if total_weight else 0.5


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
# SCORE FINAL
# -------------------------

def calculate_score(event):

    home_id = event["homeTeam"]["id"]
    away_id = event["awayTeam"]["id"]

    league_id = event["tournament"]["uniqueTournament"]["id"]
    season_id = event["season"]["id"]

    standings = get_standings(league_id, season_id)

    valid_table = standings and check_min_matches(standings)

    hf = calculate_form(home_id)
    af = calculate_form(away_id)

    hxg, hs = calculate_averages(home_id)
    axg, as_ = calculate_averages(away_id)

    home_strength = calculate_home_strength(home_id)

    league_weight = calculate_league_strength(league_id)

    if valid_table:
        motivation_home = calculate_motivation(home_id, standings)
        motivation_away = calculate_motivation(away_id, standings)
    else:
        motivation_home = 0.5
        motivation_away = 0.5

    lineup_home = estimate_lineup_impact(home_id)
    lineup_away = estimate_lineup_impact(away_id)

    score = (
        (hf - af) * 1.5 +
        (hxg - axg) * 1.2 +
        ((hs - as_) * 0.05) +
        home_strength +
        ((motivation_home - motivation_away) * 0.4) +
        (lineup_home - lineup_away)
    )

    score = score * (0.8 + (league_weight * 0.2))

    return score

# -------------------------
# PREDIÇÃO
# -------------------------

def predict(e):

    score = calculate_score(e)

    if score is None:
        return None, None

    return ("HOME" if score > 0 else "AWAY"), abs(score)

# -------------------------
# UI
# -------------------------

st.title("⚽ Scanner PRO V6.1")

date = st.date_input("Escolha a data")

events = get_events(date.strftime("%Y-%m-%d"))

filtered_events = [
    e for e in events
    if is_valid_league(e) and is_same_day_br(e, date)
]

st.write(f"Jogos válidos: {len(filtered_events)}")

if st.button("Analisar Jogos"):

    results = []

    for e in filtered_events:

        winner, edge = predict(e)

        if winner is None or edge < 0.5:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=ZoneInfo("UTC"))
        br_time = utc.astimezone(BR_TZ).strftime("%H:%M")

        results.append({
            "Hora": br_time,
            "Liga": LEAGUE_NAMES.get(e["tournament"]["uniqueTournament"]["id"], "Outra"),
            "Jogo": f"{e['homeTeam']['name']} vs {e['awayTeam']['name']}",
            "Pick": winner,
            "Edge": round(edge, 2),
            "Classificação": "ELITE" if edge >= 1 else "BOM"
        })

    if results:
        df = pd.DataFrame(results).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)
        st.write(f"Total de picks: {len(df)}")
    else:
        st.warning("Nenhuma oportunidade encontrada.")
