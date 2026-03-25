import streamlit as st
import pandas as pd
import requests

# ==============================
# TIMES (modelo)
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
# MODELO
# ==============================

def calculate_score(home, away):

    home_data = get_team_data(home)
    away_data = get_team_data(away)

    strength = (
        (home_data["xg"] - away_data["xga"]) * 2 +
        (home_data["form"] - away_data["form"]) * 1.5
    )

    prob = 50 + strength * 20

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
# COLETA DE JOGOS (API)
# ==============================

def get_matches():

    url = "https://api.football-data.org/v4/matches"

    headers = {
        "X-Auth-Token": "SUA_API_KEY_AQUI"
    }

    try:
        res = requests.get(url, headers=headers)
        data = res.json()

        matches = []

        for m in data.get("matches", []):

            home = m["homeTeam"]["name"]
            away = m["awayTeam"]["name"]

            # filtro simples (evita dados irrelevantes)
            if home and away:

                matches.append((home, away, 1.90))

        return matches[:10]

    except:

        return []


# ==============================
# APP
# ==============================

st.title("📊 Scanner Automático de Jogos")

if st.button("Buscar Jogos e Analisar"):

    matches = get_matches()

    if not matches:
        st.warning("Nenhum jogo encontrado (API ou token inválido)")
    else:

        results = []

        for home, away, odd in matches:

            prob = calculate_score(home, away)
            ev = expected_value(prob, odd)
            risk = classify(prob, ev)

            results.append({
                "Jogo": f"{home} vs {away}",
                "Probabilidade": prob,
                "Odd": odd,
                "EV": ev,
                "Classificação": risk
            })

        df = pd.DataFrame(results)

        st.dataframe(df)
