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

# -------------------------
# PERFIL DE GOLS
# -------------------------

OVER15_LEAGUES = [17,18,35,44,242,37,131,20,215,36,11621,11620,202,52,39]
UNDER35_LEAGUES = [325,390,155,703,278,11540,11541,406,11539,11536,
                   23,53,8,54,170,808,185,192,937,238,239,152,247,11653]

def get_league_goal_base(lid):
    if lid in OVER15_LEAGUES:
        return "OVER 1.5"
    if lid in UNDER35_LEAGUES:
        return "UNDER 3.5"
    return "NEUTRO"

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
# LIGAS (MANDO)
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
# GOLS (MICRO)
# -------------------------

def predict_goals(h_id, a_id, lid):

    h_win, h_gf, h_ga = get_team_stats(h_id)
    a_win, a_gf, a_ga = get_team_stats(a_id)

    avg = (h_gf + h_ga + a_gf + a_ga) / 2

    if avg >= 3:
        return "OVER 2.5"
    elif avg <= 2:
        return "UNDER 2.5"
    elif h_gf > 1.2 and a_gf > 1.2:
        return "BTTS"
    else:
        return "BTTS NÃO"

# -------------------------
# UI
# -------------------------

st.title("⚽ Scanner PRO (Liga + Jogo)")

date = st.date_input("Escolha a data")

mode = st.selectbox("Agressividade", ["Conservador","Balanceado","Agressivo"])

league_options = ["Todas"] + list(LEAGUE_NAMES.values())
selected_league = st.selectbox("Liga", league_options)

if mode == "Conservador":
    min_edge, away_min = 0.6, 0.7
elif mode == "Balanceado":
    min_edge, away_min = 0.45, 0.55
else:
    min_edge, away_min = 0.30, 0.40

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

        lid = e["tournament"]["uniqueTournament"]["id"]

        score = calculate_score(e["homeTeam"]["id"], e["awayTeam"]["id"], lid)

        pick = "HOME" if score > 0 else "AWAY"
        edge = abs(score)

        if edge < min_edge:
            continue

        if pick == "AWAY" and edge < away_min:
            continue

        base = get_league_goal_base(lid)
        goals = predict_goals(e["homeTeam"]["id"], e["awayTeam"]["id"], lid)

        utc = datetime.utcfromtimestamp(e["startTimestamp"]).replace(tzinfo=pytz.utc)
        hora = utc.astimezone(BR_TZ).strftime("%H:%M")

        tag = "ELITE" if edge >= (min_edge + 0.3) else "BOM"

        rows.append({
            "Hora": hora,
            "Liga": LEAGUE_NAMES.get(lid, ""),
            "Jogo": f'{e["homeTeam"]["name"]} vs {e["awayTeam"]["name"]}',
            "Pick": pick,
            "Edge": round(edge,2),
            "Base Liga": base,
            "Gols": goals,
            "Classificação": tag
        })

    if rows:
        df = pd.DataFrame(rows).sort_values(by="Edge", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Nenhuma oportunidade encontrada.")
