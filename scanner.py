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

def get_event_xg(event_id):
    try:
        url = f"https://api.sofascore.com/api/v1/event/{event_id}/statistics"
        data = requests.get(url).json()
        stats = data["statistics"][0]["groups"]

        for g in stats:
            for s in g["statisticsItems"]:
                if s["name"] == "Expected goals":
                    return float(s["home"]), float(s["away"])
        return 0, 0
    except:
        return 0, 0

# -------------------------
# MÉTRICAS
# -------------------------

def calc_points(matches, team_id):
    pts, total = 0, 0
    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if hs is None or as_ is None:
                continue

            if m["homeTeam"]["id"] == team_id:
                pts += 3 if hs > as_ else 1 if hs == as_ else 0
            else:
                pts += 3 if as_ > hs else 1 if hs == as_ else 0

            total += 3
        except:
            continue
    return pts / total if total else 0.5


def calc_home_advantage(home_id, away_id):
    home_matches = get_team_matches(home_id, 10)
    away_matches = get_team_matches(away_id, 10)

    home_home = [m for m in home_matches if m["homeTeam"]["id"] == home_id][:5]
    away_away = [m for m in away_matches if m["awayTeam"]["id"] == away_id][:5]

    home_perf = calc_points(home_home, home_id)
    away_perf = calc_points(away_away, away_id)

    return home_perf - away_perf


def calc_form(team_id):
    matches = get_team_matches(team_id, 10)
    return calc_points(matches, team_id)


def calc_xg(team_id):
    matches = get_team_matches(team_id, 5)
    total, count = 0, 0

    for m in matches:
        try:
            xg_h, xg_a = get_event_xg(m["id"])

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

    hf = calc_form(home_id)
    af = calc_form(away_id)

    home_adv = calc_home_advantage(home_id, away_id)

    hxg = calc_xg(home_id)
    axg = calc_xg(away_id)

    score = (
        (hf - af) * 0.6 +
        home_adv * 0.5 +
        (hxg - axg) * 0.25
    )

    return score


def predict(e):
    score = calculate_score(e["homeTeam"]["id"], e["awayTeam"]["id"])
    return ("HOME" if score > 0 else "AWAY"), abs(score)

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

        winner, edge = predict(e)

        if edge < 0.25:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        br_time = utc.astimezone(BR_TZ).strftime("%H:%M")

        tag = "ELITE" if edge >= 0.6 else "BOM"

        results.append({
            "Hora": br_time,
            "Liga": LEAGUE_NAMES.get(e["tournament"]["uniqueTournament"]["id"], "Outra"),
            "Jogo": f'{e["homeTeam"]["name"]} vs {e["awayTeam"]["name"]}',
            "Pick": winner,
            "Edge": round(edge, 2),
            "Classificação": tag
        })

    if results:
        df = pd.DataFrame(results).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)
        st.write(f"Total de picks relevantes: {len(df)}")
    else:
        st.warning("Nenhuma oportunidade encontrada.")
