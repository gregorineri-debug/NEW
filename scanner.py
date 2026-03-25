import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import math
from datetime import datetime

# ==============================
# MODELO SIMPLIFICADO (ESTÁVEL)
# ==============================

def get_team_strength(team):

    team = team.lower()

    strong = ["real madrid", "barcelona", "bayern munich", "manchester city"]
    medium = ["arsenal", "manchester united", "chelsea"]

    if team in strong:
        return {"xg": 2.2, "xga": 1.0, "form": 0.75}

    elif team in medium:
        return {"xg": 1.9, "xga": 1.1, "form": 0.65}

    else:
        return {"xg": 1.4, "xga": 1.4, "form": 0.50}


def calculate_score(home, away):

    h = get_team_strength(home)
    a = get_team_strength(away)

    raw = (
        (h["xg"] - a["xga"]) +
        (h["form"] - a["form"]) * 0.9
    )

    strength = math.tanh(raw)

    prob = 50 + (strength * 45)
    prob += (h["form"] - 0.5) * 5

    return round(max(5, min(95, prob)), 2)


# ==============================
# EV
# ==============================

def expected_value(prob, odd):

    return round((prob / 100) - (1 / odd), 3)


# ==============================
# PICK
# ==============================

def get_pick(prob, ev):

    if ev <= 0:
        return "❌ NO BET"

    if prob >= 55:
        return "🏠 HOME"

    if prob <= 45:
        return "✈️ AWAY"

    return "❌ NO BET"


# ==============================
# COLETA DE JOGOS (ESPN)
# ==============================

def get_matches():

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

        if matches:
            return matches[:20]

    except:
        pass

    # fallback
    return [
        ("Real Madrid", "Barcelona", 1.90),
        ("Manchester City", "Arsenal", 1.85),
        ("CRB", "Sport", 2.10),
        ("Sparta Prague", "Hammarby IF", 1.95),
    ]


# ==============================
# APP
# ==============================

st.title("📊 Scanner Profissional (Versão Estável)")

date = st.date_input("📅 Data da análise", datetime.today())

if st.button("Rodar Análise"):

    matches = get_matches()

    results = []

    for home, away, odd in matches:

        prob = calculate_score(home, away)
        ev = expected_value(prob, odd)
        pick = get_pick(prob, ev)

        results.append({
            "Jogo": f"{home} vs {away}",
            "Probabilidade": prob,
            "Odd": odd,
            "EV": ev,
            "Pick": pick
        })

    df = pd.DataFrame(results)

    st.dataframe(df)

    st.subheader("📈 Resumo")

    st.write("Total jogos:", len(df))
    st.write("Picks válidas:", len(df[df["Pick"] != "❌ NO BET"]))
    st.write("EV médio:", round(df["EV"].mean(), 3))
