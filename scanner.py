import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ==============================
# MODELO
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


def calculate_score(home, away):

    h = get_team_data(home)
    a = get_team_data(away)

    strength = (
        (h["xg"] - a["xga"]) * 1.8 +
        (h["form"] - a["form"]) * 1.2
    )

    prob = 50 + strength * 18

    return round(max(1, min(99, prob)), 2)


def expected_value(prob, odd):
    return round((prob / 100 * odd) - 1, 3)


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
# SOFASCORE (PRIMEIRO)
# ==============================

def get_matches_sofascore():

    url = "https://api.sofascore.com/api/v1/sport/football/events/live"

    matches = []

    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        for event in data.get("events", []):

            home = event["homeTeam"]["name"]
            away = event["awayTeam"]["name"]

            matches.append((home, away, 1.90))

    except:
        pass

    return matches


# ==============================
# ESPN (SEGUNDO)
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

                if home and away and home != away:
                    matches.append((home, away, 1.90))

    except:
        pass

    return matches


# ==============================
# FALLBACK
# ==============================

def get_matches():

    # 1º tenta Sofascore
    matches = get_matches_sofascore()

    # 2º tenta ESPN
    if not matches:
        matches = get_matches_espn()

    # 3º fallback garantido
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

st.title("📊 Scanner Profissional (Sofascore → ESPN)")

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
