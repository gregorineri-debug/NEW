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
# MODELO (AJUSTADO)
# ==============================

def calculate_score(home, away):

    home_data = get_team_data(home)
    away_data = get_team_data(away)

    strength = (
        (home_data["xg"] - away_data["xga"]) * 1.8 +
        (home_data["form"] - away_data["form"]) * 1.2
    )

    prob = 50 + (strength * 18)

    return round(max(1, min(99, prob)), 2)


def expected_value(prob, odd):
    return round((prob / 100 * odd) - 1, 3)


def classify(prob, ev):

    if ev >= 0.07 and prob >= 65:
        return "🔥 ELITE"
    elif ev >= 0.04:
        return "🟢 VALOR FORTE"
    elif ev >= 0.02:
        return "🟡 VALOR"
    else:
        return "🔴 EVITAR"


# ==============================
# SCRAPING DE JOGOS
# ==============================

def get_matches():

    url = "https://www.espn.com/soccer/fixtures"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        matches = []

        rows = soup.find_all("tr")

        for r in rows:

            teams = r.find_all("a")

            if len(teams) >= 2:

                home = teams[0].text.strip()
                away = teams[1].text.strip()

                if home and away and home != away:
                    matches.append((home, away, 1.90))

        return matches[:15]

    except:

        return []


# ==============================
# APP
# ==============================

st.title("📊 Scanner Automático de Jogos")

if st.button("Rodar Análise"):

    matches = get_matches()

    if not matches:

        st.error("❌ Nenhum jogo encontrado. (site pode ter bloqueado scraping)")

    else:

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
