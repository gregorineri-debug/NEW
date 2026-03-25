import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==============================
# CONFIG
# ==============================

API_URL = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={date}&s=Soccer"


# ==============================
# PEGAR JOGOS
# ==============================

def get_matches(date):

    url = API_URL.format(date=date)

    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        matches = []

        for m in data.get("events", []):

            home = m.get("strHomeTeam")
            away = m.get("strAwayTeam")

            if home and away:
                matches.append((home, away))

        return matches

    except Exception as e:
        st.error(f"Erro ao buscar jogos: {e}")
        return []


# ==============================
# MODELO SIMPLES
# ==============================

def strength(team):

    elite = ["Real Madrid", "Manchester City", "Bayern Munich"]

    if team in elite:
        return 2.2

    return 1.5


def predict(home, away):

    diff = strength(home) - strength(away)

    prob = 50 + diff * 20

    return max(5, min(95, prob))


def ev(prob, odd):
    return (prob / 100) - (1 / odd)


def pick(prob, ev):

    if ev <= 0:
        return "❌ NO BET"

    if prob > 55:
        return "🏠 HOME"

    if prob < 45:
        return "✈️ AWAY"

    return "❌ NO BET"


# ==============================
# STREAMLIT UI
# ==============================

st.title("⚽ Scanner de Jogos")

date = st.date_input("Escolha a data", datetime.today())

if st.button("Rodar Análise"):

    date_str = date.strftime("%Y-%m-%d")

    matches = get_matches(date_str)

    if not matches:
        st.warning("Nenhum jogo encontrado")
    else:

        results = []

        for home, away in matches:

            prob = predict(home, away)
            odd = 1.9
            ev_value = ev(prob, odd)
            p = pick(prob, ev_value)

            results.append({
                "Jogo": f"{home} vs {away}",
                "Probabilidade": round(prob, 2),
                "EV": round(ev_value, 3),
                "Pick": p
            })

        df = pd.DataFrame(results)

        st.dataframe(df)
