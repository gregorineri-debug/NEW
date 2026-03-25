import streamlit as st
import pandas as pd

# ==============================
# DADOS
# ==============================

def get_team_data(team):

    db = {
        "Manchester City": {"xg": 2.4, "xga": 0.9, "form": 0.78},
        "Arsenal": {"xg": 2.0, "xga": 1.1, "form": 0.72},
        "Barcelona": {"xg": 2.2, "xga": 1.0, "form": 0.75},
        "Real Madrid": {"xg": 2.1, "xga": 1.0, "form": 0.74},
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
        (home_data["xg"] - away_data["xga"]) * 2.0 +
        (home_data["form"] - away_data["form"]) * 1.5
    )

    prob = 50 + (strength * 20)

    if prob > 65:
        prob += 5
    elif prob < 45:
        prob -= 5

    return round(max(1, min(99, prob)), 2)


# ==============================
# EV
# ==============================

def expected_value(prob, odd):
    return round((prob / 100 * odd) - 1, 3)


# ==============================
# CLASSIFICAÇÃO
# ==============================

def classify(prob, ev):

    if ev >= 0.07 and prob >= 66:
        return "🔥 ELITE"
    elif ev >= 0.04:
        return "🟢 VALOR FORTE"
    elif ev >= 0.02:
        return "🟡 VALOR"
    else:
        return "🔴 EVITAR"


# ==============================
# APP
# ==============================

st.title("📊 Scanner de Apostas")

home = st.selectbox("Time da Casa", [
    "Manchester City", "Arsenal", "Barcelona", "Real Madrid", "CRB", "Sport"
])

away = st.selectbox("Time Visitante", [
    "Manchester City", "Arsenal", "Barcelona", "Real Madrid", "CRB", "Sport"
])

odd = st.number_input("Odd", value=1.85)

if st.button("Analisar"):

    prob = calculate_score(home, away)
    ev = expected_value(prob, odd)
    risk = classify(prob, ev)

    st.subheader("Resultado")

    st.write(f"**Probabilidade:** {prob}%")
    st.write(f"**EV:** {ev}")
    st.write(f"**Classificação:** {risk}")
