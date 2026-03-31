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

    filtered = []

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if hs is None or as_ is None:
                continue

            if venue == "home" and m["homeTeam"]["id"] != team_id:
                continue
            if venue == "away" and m["awayTeam"]["id"] != team_id:
                continue

            filtered.append(hs + as_)
        except:
            continue

    if len(filtered) == 0:
        return 0.5

    filtered = filtered[:last_n]

    over = sum(1 for g in filtered if g > 2.5)

    return over / len(filtered)

# -------------------------
# MOTOR PRINCIPAL
# -------------------------

def evaluate_goals(home_id, away_id):

    home_matches = get_team_matches(home_id, 30)
    away_matches = get_team_matches(away_id, 30)

    # -------- GERAL --------
    h30 = calc_over_rate(home_matches, home_id, None, 30)
    h10 = calc_over_rate(home_matches, home_id, None, 10)
    h5  = calc_over_rate(home_matches, home_id, None, 5)

    a30 = calc_over_rate(away_matches, away_id, None, 30)
    a10 = calc_over_rate(away_matches, away_id, None, 10)
    a5  = calc_over_rate(away_matches, away_id, None, 5)

    over_general = all(x > 0.55 for x in [h30,h10,h5,a30,a10,a5])
    under_general = all(x < 0.45 for x in [h30,h10,h5,a30,a10,a5])

    # -------- CASA/FORA --------
    h_home_30 = calc_over_rate(home_matches, home_id, "home", 30)
    h_home_10 = calc_over_rate(home_matches, home_id, "home", 10)
    h_home_5  = calc_over_rate(home_matches, home_id, "home", 5)

    a_away_30 = calc_over_rate(away_matches, away_id, "away", 30)
    a_away_10 = calc_over_rate(away_matches, away_id, "away", 10)
    a_away_5  = calc_over_rate(away_matches, away_id, "away", 5)

    over_context = all(x > 0.55 for x in [h_home_30,h_home_10,h_home_5,a_away_30,a_away_10,a_away_5])
    under_context = all(x < 0.45 for x in [h_home_30,h_home_10,h_home_5,a_away_30,a_away_10,a_away_5])

    # -------- DECISÃO --------
    if over_general and over_context:
        confidence = (h5 + a5 + h_home_5 + a_away_5) / 4
        return "OVER 2.5", confidence

    if under_general and under_context:
        confidence = 1 - ((h5 + a5 + h_home_5 + a_away_5) / 4)
        return "UNDER 2.5", confidence

    return None, 0

# -------------------------
# UI
# -------------------------

st.title("⚽ Scanner PRO (Over/Under 2.5)")

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

    for e in filtered:

        pick, conf = evaluate_goals(
            e["homeTeam"]["id"],
            e["awayTeam"]["id"]
        )

        if not pick:
            continue

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        hora = utc.astimezone(BR_TZ).strftime("%H:%M")

        rows.append({
            "Hora": hora,
            "Liga": LEAGUE_NAMES.get(e["tournament"]["uniqueTournament"]["id"], "Outra"),
            "Jogo": f'{e["homeTeam"]["name"]} vs {e["awayTeam"]["name"]}',
            "Pick": pick,
            "Confiança": round(conf,2)
        })

    if rows:
        df = pd.DataFrame(rows).sort_values(by="Confiança", ascending=False)
        st.dataframe(df, use_container_width=True)
        st.write(f"Total de picks: {len(df)}")
    else:
        st.warning("Nenhuma oportunidade encontrada.")
