import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import math
from datetime import datetime

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
        "Sport": {"xg": 1.2, "xga": 1.4, "form": 0.50},
        "Sparta Prague": {"xg": 1.7, "xga": 1.2, "form": 0.60},
        "Hammarby IF": {"xg": 1.6, "xga": 1.3, "form": 0.58}
    }

    return db.get(team, {"xg": 1.3, "xga": 1.3, "form": 0.5})


def calculate_score(home, away):

    h = get_team_data(home)
    a = get_team_data(away)

    raw_strength = (
        (h["xg"] - a["xga"]) +
        (h["form"] - a["form"]) * 0.9
    )

    strength = math.tanh(raw_strength)

    prob = 50 + (strength * 45)
    prob += (h["form"] - 0.5) * 6

    return round(max(5, min(95, prob)), 2)


# ==============================
# EV
# ==============================

def expected_value(prob, odd):

    return round((prob / 100) - (1 / odd), 3)


# ==============================
# CLASSIFICAÇÃO
# ==============================

def classify(prob, ev):

    if ev >= 0.06 and prob >= 62:
        return "🔥 ELITE"
    elif ev >= 0.04:
        return "🟢 VALOR FORTE"
    elif ev >= 0.02:
        return "🟡 VALOR"
    else:
        return "🔴 EVITAR"


# ==============================
# PICK (CORRIGIDO)
# ==============================

def get_pick(prob, ev):

    if ev <= 0:
        return "❌ NO BET"

    if 48 <= prob <= 52:
        return "❌ NO BET"

    if prob > 52:
        return "🏠 HOME"

    if prob < 48:
        return "✈️ AWAY"

    return "❌ NO BET"


# ==============================
# FILTRO
# ==============================

def is_valid_game(home, away):

    banned = ["U12", "U13", "U14", "U15"]

    for b in banned:
        if b in home or b in away:
            return False

    return True


# ==============================
# COLETA ESPN
# ==============================

def get_matches_espn():

    url = "https://www.espn.com/soccer/fixtures"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        matches = []

        for row in soup.find_all("tr"):
            teams = row.find_all("span")

            if len(teams) >= 2:
                home = teams[0].text.strip()
                away = teams[1].text.strip()

                if home and away:
                    matches.append((home, away, 1.90))

        return matches[:20]

    except:
        return []


# ==============================
# FALLBACK
# ==============================

def get_matches_fallback():

    return [
        ("Real Madrid", "Barcelona", 1.90),
        ("Manchester City", "Arsenal", 1.85),
        ("CRB", "Sport", 2.10),
        ("Sparta Prague", "Hammarby IF", 1.95),
    ]


# ==============================
# APP
# ==============================

st.title("📊 Scanner Profissional Completo")

date = st.date_input("📅 Data do Backtest", datetime.today())

if st.button("Rodar Análise"):

    matches = get_matches_espn()

    if not matches:
        st.warning("ESPN falhou — usando fallback")
        matches = get_matches_fallback()

    results = []

    for home, away, odd in matches:

        if not is_valid_game(home, away):
            continue

        prob = calculate_score(home, away)
        ev = expected_value(prob, odd)
        risk = classify(prob, ev)
        pick = get_pick(prob, ev)

        results.append({
            "Jogo": f"{home} vs {away}",
            "Probabilidade": prob,
            "Odd": odd,
            "EV": ev,
            "Classificação": risk,
            "Pick": pick
        })

    if results:

        df = pd.DataFrame(results)

        st.dataframe(df)

        # métricas
        st.subheader("📈 Resumo")

        st.write("Total jogos:", len(df))
        st.write("ELITE:", len(df[df["Classificação"] == "🔥 ELITE"]))
        st.write("VALOR:", len(df[df["Classificação"] == "🟢 VALOR FORTE"]))
        st.write("NO BET:", len(df[df["Pick"] == "❌ NO BET"]))
        st.write("EV médio:", round(df["EV"].mean(), 3))

    else:
        st.warning("Nenhum jogo encontrado.")
