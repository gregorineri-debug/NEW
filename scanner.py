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
    325:"Brasileirão",390:"Série B",17:"Premier League",18:"Championship",
    8:"La Liga",54:"La Liga 2",35:"Bundesliga",44:"2. Bundesliga",
    23:"Serie A",53:"Serie B Itália",34:"Ligue 1",182:"Ligue 2",
    955:"Saudi Pro League",155:"Argentina Liga",703:"Primera Nacional",
    45:"Áustria",38:"Bélgica",247:"Bulgária",172:"Rep. Tcheca",
    11653:"Chile",11539:"Colômbia Apertura",11536:"Colômbia Finalización",
    170:"Croácia",39:"Dinamarca",808:"Egito",36:"Escócia",
    242:"MLS",185:"Grécia",37:"Eredivisie",131:"Eerste Divisie",
    192:"Irlanda",937:"Marrocos",11621:"Liga MX Apertura",
    11620:"Liga MX Clausura",20:"Noruega",11540:"Paraguai Apertura",
    11541:"Paraguai Clausura",406:"Peru",202:"Polônia",
    238:"Portugal",239:"Portugal 2",152:"Romênia",40:"Suécia",
    215:"Suíça",52:"Turquia",278:"Uruguai"
}

# ---------------- API ----------------

def get_events(date):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
    return requests.get(url).json().get("events", [])

def get_team_matches(team_id, n):
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/{n}"
    return requests.get(url).json().get("events", [])

# ---------------- FILTROS ----------------

def is_valid_league(event):
    try:
        return event["tournament"]["uniqueTournament"]["id"] in VALID_LEAGUE_IDS
    except:
        return False

def is_same_day_br(event, selected_date):
    utc = datetime.utcfromtimestamp(event["startTimestamp"]).replace(tzinfo=pytz.utc)
    return utc.astimezone(BR_TZ).date() == selected_date

# ---------------- TABELA 10 JOGOS ----------------

def get_table_stats(team_id):

    matches = get_team_matches(team_id, 10)

    pts = 0
    goals_for = 0
    goals_against = 0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if m["homeTeam"]["id"] == team_id:
                goals_for += hs
                goals_against += as_

                if hs > as_: pts += 3
                elif hs == as_: pts += 1
            else:
                goals_for += as_
                goals_against += hs

                if as_ > hs: pts += 3
                elif hs == as_: pts += 1
        except:
            continue

    return {
        "points": pts,
        "gd": goals_for - goals_against,
        "gf": goals_for,
        "ga": goals_against
    }

# ---------------- HOME / AWAY ----------------

def get_home_away_stats(team_id, is_home):

    matches = get_team_matches(team_id, 10)

    pts = 0
    gf = 0
    ga = 0
    count = 0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if is_home and m["homeTeam"]["id"] == team_id:
                gf += hs
                ga += as_
                count += 1

                if hs > as_: pts += 3
                elif hs == as_: pts += 1

            elif not is_home and m["awayTeam"]["id"] == team_id:
                gf += as_
                ga += hs
                count += 1

                if as_ > hs: pts += 3
                elif hs == as_: pts += 1

            if count == 5:
                break

        except:
            continue

    return {
        "points": pts,
        "gf": gf,
        "ga": ga
    }

# ---------------- COMPARAÇÃO FINAL ----------------

def evaluate_match(home_id, away_id):

    home_table = get_table_stats(home_id)
    away_table = get_table_stats(away_id)

    home_home = get_home_away_stats(home_id, True)
    away_away = get_home_away_stats(away_id, False)

    # ranking hipotético
    if home_table["points"] > away_table["points"]:
        table_leader = "HOME"
    elif away_table["points"] > home_table["points"]:
        table_leader = "AWAY"
    else:
        table_leader = "EQUAL"

    # comparação numérica
    score_home = 0
    score_away = 0

    # pontos tabela
    if home_table["points"] > away_table["points"]:
        score_home += 1
    elif away_table["points"] > home_table["points"]:
        score_away += 1

    # saldo gols geral
    if home_table["gd"] > away_table["gd"]:
        score_home += 1
    elif away_table["gd"] > home_table["gd"]:
        score_away += 1

    # desempenho casa vs fora
    if home_home["points"] > away_away["points"]:
        score_home += 1
    elif away_away["points"] > home_home["points"]:
        score_away += 1

    # gols casa vs fora
    if home_home["gf"] - home_home["ga"] > away_away["gf"] - away_away["ga"]:
        score_home += 1
    elif away_away["gf"] - away_away["ga"] > home_home["gf"] - home_home["ga"]:
        score_away += 1

    if score_home > score_away:
        return "HOME", score_home - score_away
    elif score_away > score_home:
        return "AWAY", score_away - score_home
    else:
        return "SKIP", 0

# ---------------- UI ----------------

st.title("⚽ Scanner Tabela 10 Jogos")

date = st.date_input("Escolha a data")

league_options = ["Todas"] + list(LEAGUE_NAMES.values())
selected_league = st.selectbox("Escolha a liga", league_options)

events = get_events(date.strftime("%Y-%m-%d"))

filtered_events = []

for e in events:

    if not is_valid_league(e):
        continue

    if not is_same_day_br(e, date):
        continue

    league_id = e["tournament"]["uniqueTournament"]["id"]
    league_name = LEAGUE_NAMES.get(league_id, "Outra")

    if selected_league != "Todas" and league_name != selected_league:
        continue

    filtered_events.append(e)

st.write(f"Jogos válidos: {len(filtered_events)}")

if st.button("Analisar Jogos"):

    results = []

    for e in filtered_events:

        home_id = e["homeTeam"]["id"]
        away_id = e["awayTeam"]["id"]

        winner, edge = evaluate_match(home_id, away_id)

        if winner == "SKIP":
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        br_time = utc.astimezone(BR_TZ).strftime("%H:%M")

        home = e["homeTeam"]["name"]
        away = e["awayTeam"]["name"]

        tag = "ELITE" if edge >= 2 else "BOM"

        results.append({
            "Hora": br_time,
            "Liga": LEAGUE_NAMES.get(e["tournament"]["uniqueTournament"]["id"], "Outra"),
            "Jogo": f"{home} vs {away}",
            "Pick": winner,
            "Edge": edge,
            "Classificação": tag
        })

    if results:
        df = pd.DataFrame(results).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)
        st.write(f"Total de picks relevantes: {len(df)}")
    else:
        st.warning("Nenhuma oportunidade encontrada.")
