import streamlit as st
import pandas as pd
import math
from datetime import datetime

# ==============================
# BASE DE DADOS (SIMULADA)
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


# ==============================
# MODELO
# ==============================

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

    implied = 1 / odd
    return round((prob / 100) - implied, 3)


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
# FILTRO
# ==============================

def is_valid_game(home, away):

    banned = ["U12", "U13", "U14", "U15"]

    for b in banned:
        if b in home or b in away:
            return False

    return True


# ==============================
# DADOS DE JOGOS (BACKTEST)
# ==============================

def get_matches_by_date(selected_date):

    # 🔥 aqui depois você conecta com scraping real
    # por enquanto é simulado

    base_matches = [
        ("Real Madrid", "Barcelona", 1.90),
        ("Manchester City", "Arsenal", 1.85),
        ("CRB", "Sport", 2.10),
        ("Sparta Prague", "Hammarby IF", 1.95),
    ]

    return base_matches


# ==============================
# APP
# ==============================

st.title("📊 Backtest com Data (Scanner Profissional)")

# 🔥 SELETOR DE DATA
selected_date = st.date_input("📅 Selecione a data do backtest", datetime.today())

st.write(f"Analisando jogos do dia: {selected_date}")

if st.button("Rodar Backtest"):

    matches = get_matches_by_date(selected_date)

    results = []

    for home, away, odd in matches:

        if not is_valid_game(home, away):
            continue

        prob = calculate_score(home, away)
        ev = expected_value(prob, odd)
        risk = classify(prob, ev)

        results.append({
            "Data": selected_date,
            "Jogo": f"{home} vs {away}",
            "Probabilidade (%)": prob,
            "Odd": odd,
            "EV": ev,
            "Classificação": risk
        })

    if results:

        df = pd.DataFrame(results)

        st.dataframe(df)

        # 🔥 métricas do backtest
        st.subheader("📈 Resumo")

        st.write("Picks:", len(df))
        st.write("ELITE:", len(df[df["Classificação"] == "🔥 ELITE"]))
        st.write("VALOR FORTE:", len(df[df["Classificação"] == "🟢 VALOR FORTE"]))
        st.write("VALOR:", len(df[df["Classificação"] == "🟡 VALOR"]))
        st.write("EV médio:", round(df["EV"].mean(), 3))

    else:
        st.warning("Nenhum jogo encontrado para essa data.")
