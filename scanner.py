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
    325:"Brasileirão",390:"Série B",17:"Premier League",
    18:"Championship",8:"La Liga",54:"La Liga 2",
    35:"Bundesliga",44:"2. Bundesliga",23:"Serie A",
    53:"Serie B Itália",34:"Ligue 1",182:"Ligue 2",
    955:"Saudi Pro League",155:"Argentina Liga",
    703:"Primera Nacional",45:"Áustria",38:"Bélgica",
    247:"Bulgária",172:"Rep. Tcheca",11653:"Chile",
    11539:"Colômbia Apertura",11536:"Colômbia Finalización",
    170:"Croácia",39:"Dinamarca",808:"Egito",
    36:"Escócia",242:"MLS",185:"Grécia",
    37:"Eredivisie",131:"Eerste Divisie",192:"Irlanda",
    937:"Marrocos",11621:"Liga MX Apertura",
    11620:"Liga MX Clausura",20:"Noruega",
    11540:"Paraguai Apertura",11541:"Paraguai Clausura",
    406:"Peru",202:"Polônia",238:"Portugal",
    239:"Portugal 2",152:"Romênia",40:"Suécia",
    215:"Suíça",52:"Turquia",278:"Uruguai"
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

def get_standings(league_id):

    try:
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/standings/total"
        data = requests.get(url).json()

        table = data["standings"][0]["rows"]

        ranking = {}
        total = len(table)

        for i, team in enumerate(table):
            team_id = team["team"]["id"]
            pos = i + 1

            ranking[team_id] = pos / total  # normalizado (0 topo, 1 fundo)

        return ranking
    except:
        return {}

# -------------------------
# STATS V5
# -------------------------

def get_team_stats(team_id):

    matches = get_team_matches(team_id, 10)

    points = 0
    goals_for = 0
    goals_against = 0
    count = 0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if hs is None or as_ is None:
                continue

            if m["homeTeam"]["id"] == team_id:
                gf, ga = hs, as_
            else:
                gf, ga = as_, hs

            goals_for += gf
            goals_against += ga

            if gf > ga:
                points += 3
            elif gf == ga:
                points += 1

            count += 1
        except:
            continue

    if count == 0:
        return 1,1,1

    return (
        points / count,
        goals_for / count,
        goals_against / count
    )

# -------------------------
# CASA/FORA
# -------------------------

def get_home_away_stats(team_id, venue):

    matches = get_team_matches(team_id, 10)

    gf = 0
    ga = 0
    count = 0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if hs is None or as_ is None:
                continue

            if venue == "home" and m["homeTeam"]["id"] == team_id:
                gf += hs
                ga += as_
                count += 1

            elif venue == "away" and m["awayTeam"]["id"] == team_id:
                gf += as_
                ga += hs
                count += 1

        except:
            continue

    if count == 0:
        return 1,1

    return gf / count, ga / count

# -------------------------
# SCORE V5 + RANKING
# -------------------------

def calculate_score(home_id, away_id, ranking):

    hp, hg, hga = get_team_stats(home_id)
    ap, ag, aga = get_team_stats(away_id)

    h_home_g, h_home_ga = get_home_away_stats(home_id, "home")
    a_away_g, a_away_ga = get_home_away_stats(away_id, "away")

    # FORÇA
    home_strength = (hp * 0.6) + (hg * 0.4)
    away_strength = (ap * 0.6) + (ag * 0.4)

    # FRAQUEZA
    home_weak = hga * 0.7 + h_home_ga * 0.3
    away_weak = aga * 0.7 + a_away_ga * 0.3

    score = (home_strength - away_weak) - (away_strength - home_weak)

    # -------------------------
    # AJUSTE RANKING
    # -------------------------
    if ranking:

        hr = ranking.get(home_id, 0.5)
        ar = ranking.get(away_id, 0.5)

        diff = ar - hr  # positivo = home melhor

        score += diff * 1.5

    return score

def predict(e, ranking):

    score = calculate_score(
        e["homeTeam"]["id"],
        e["awayTeam"]["id"],
        ranking
    )

    if score > 0:
        return "HOME", score
    else:
        return "AWAY", abs(score)

# -------------------------
# UI
# -------------------------

st.title("⚽ Scanner PRO (Greg Stats X V5 + Ranking)")

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

st.write(f"Jogos encontrados: {len(filtered)}")

if st.button("Analisar"):

    rows = []

    league_rank_cache = {}

    for e in filtered:

        lid = e["tournament"]["uniqueTournament"]["id"]

        if lid not in league_rank_cache:
            league_rank_cache[lid] = get_standings(lid)

        ranking = league_rank_cache[lid]

        pick, edge = predict(e, ranking)

        if edge < 0.5:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        hora = utc.astimezone(BR_TZ).strftime("%H:%M")

        tag = "ELITE" if edge >= 1.2 else "BOM"

        rows.append({
            "Hora": hora,
            "Liga": LEAGUE_NAMES.get(lid, "Outra"),
            "Jogo": f'{e["homeTeam"]["name"]} vs {e["awayTeam"]["name"]}',
            "Pick": pick,
            "Edge": round(edge,2),
            "Classificação": tag
        })

    if rows:
        df = pd.DataFrame(rows).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)
        st.write(f"Total de picks: {len(df)}")
    else:
        st.warning("Nenhuma oportunidade encontrada.")
