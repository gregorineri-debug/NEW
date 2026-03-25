import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ==============================
# MODELO DE TIMES
# ==============================

def get_team_data(team):

    db = {
        "Barcelona": {"xg": 2.2, "xga": 1.0, "form": 0.75},
        "Real Madrid": {"xg": 2.1, "xga": 1.0, "form": 0.74},
        "Manchester City": {"xg": 2.4, "xga": 0.9, "form": 0.78},
        "Arsenal": {"xg": 2.0, "xga": 1.1, "form": 0.72},
        "CRB": {"xg": 1.1, "xga": 1.3, "form": 0.48},
        "Sport": {"xg": 1.2, "xga": 1.4, "form": 0.50}
    }

    return db.get(team, {"xg": 1.3, "xga": 1.3, "form": 0.5})


# ==============================
# MODELO AJUSTADO
# ==============================

def calculate_score(home, away):

    h = get_team_data(home)
    a = get_team_data(away)

    strength = (
        (h["xg"] - a["xga"]) * 2.5 +
        (h["form"] - a["form"]) * 2.0
    )

    prob = 50 + strength * 25

    return round(max(5, min(95, prob)), 2)


# ==============================
# EV REAL (EDGE)
# ==============================

def expected_value(prob, odd):

    implied = 1 / odd
    edge = (prob / 100) - implied

    return round(edge, 3)


# ==============================
# CLASSIFICAÇÃO
# ==============================

def classify(prob, ev):

    if ev >= 0.07:
        return "🔥 ELITE"
    elif ev >= 0.04:
        return "🟢 VALOR FORTE"
    elif ev >= 0.02:
        return "🟡 VALOR"
    else:
        return "🔴 EVITAR"


# ==============================
# FILTRO DE JOGOS FRACOS
# ==============================

def is_valid_game(home, away):

    banned = ["U12", "U13", "U14", "U15", "U16", "U17", "U18"]

    for b in banned:
        if b in home or b in away:
            return False

    return True


# ==============================
# COLETA SOFASCORE
# ==============================

def get_matches_sofascore():

    url = "https://api.sofascore.com/api/v1/sport/football/events/live"

    matches = []

    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        for e in data.get("events", []):

            home = e["homeTeam"]["name"]
            away = e["awayTeam"]["name"]

            if is_valid_game(home, away):

                matches.append((home, away, 1.90))

    except:
        pass

    return matches


# ==============================
# COLETA ESPN
# ==============================

def get_matches_espn():

    url = "https://www.espn.com/soccer/fixtures"

    headers = {"User-Agent": "Mozilla/5.0"}

    matches = []

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        rows = soup.find_all("tr")

        for r in rows:

            teams = r.find_all("a")

            if len(teams) >= 2:

                home = teams[0].text.strip()
                away = teams[1].text.strip()

                if is_valid_game(home, away):

                    matches.append((home, away, 1.90))

    except:
        pass

    return matches


# ==============================
# FALLBACK
# ==============================

def get_matches():

    matches = get_matches_sofascore()

    if not matches:
        matches = get_matches_espn()

    if not matches:
        matches = [
            ("Barcelona", "Real Madrid", 1.90),
            ("Manchester City", "Arsenal", 1.85),
            ("CRB", "Sport", 2.10)
        ]

    return matches[:15]


# ==============================
# APP
# ==============================

st.title("📊 Scanner Profissional Ajustado")

if st.button("Rodar Análise"):

    matches = get_matches()

    results = []

    for home, away, odd in matches:

        prob = calculate_score(home, away)
        ev = expected_value(prob, odd)
        risk = classify(prob, ev)

        results.append({
            "Jogo": f"{home} vs {away}",
            "Probabilidade (%)": prob,
            "Odd": odd,
            "EV": ev,
            "Classificação": risk
        })

    df = pd.DataFrame(results)

    st.dataframe(df)
