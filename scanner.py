import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import math
from datetime import datetime

# ==============================
# MODELO
# ==============================

def calculate_score(home, away):

    strength = (len(home) - len(away)) / 20  # placeholder simples

    prob = 50 + (math.tanh(strength) * 45)

    return round(max(5, min(95, prob)), 2)


def expected_value(prob, odd):
    return round((prob / 100) - (1 / odd), 3)


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
# COLETA ESPN (REAL)
# ==============================

def get_matches_espn():

    url = "https://www.espn.com/soccer/fixtures"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    matches = []

    # ESPN muda estrutura com frequência — por isso buscamos genericamente
    for match in soup.find_all("tr"):

        teams = match.find_all("span")

        if len(teams) >= 2:
            home = teams[0].text.strip()
            away = teams[1].text.strip()

            if home and away:
                matches.append((home, away, 1.9))

    return matches[:20]


# ==============================
# BACKUP (GENÉRICO)
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

st.title("📊 Scanner com Jogos Reais")

date = st.date_input("📅 Data da análise", datetime.today())

if st.button("Buscar jogos e analisar"):

    # 🔥 tenta ESPN
    matches = get_matches_espn()

    # fallback se falhar
    if not matches:
        st.warning("⚠️ ESPN bloqueado — usando fallback")
        matches = get_matches_fallback()

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

    # métricas
    st.subheader("📈 Resumo")

    st.write("Total jogos:", len(df))
    st.write("ELITE:", len(df[df["Classificação"] == "🔥 ELITE"]))
    st.write("VALOR:", len(df[df["Classificação"] == "🟢 VALOR FORTE"]))
    st.write("EV médio:", round(df["EV"].mean(), 3))
