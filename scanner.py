import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# ==============================
# CONFIG
# ==============================

TIMEZONE = "America/Sao_Paulo"

# ==============================
# DATA CORRIGIDA
# ==============================

def get_today():
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).date()

# ==============================
# DADOS (FBREF / FOOTYSTATS)
# ==============================

def get_fbref_data(team):
    return {
        "xg": 1.4,
        "xga": 1.2,
        "form": 0.6
    }

def get_footystats_data(team):
    return {
        "xg": 1.3,
        "xga": 1.25,
        "form": 0.55
    }

def get_team_data(team):
    try:
        return get_fbref_data(team)
    except:
        return get_footystats_data(team)

# ==============================
# SCORE AJUSTADO (IMPORTANTE)
# ==============================

def calculate_score(home, away):
    home_data = get_team_data(home)
    away_data = get_team_data(away)

    strength = (
        home_data["xg"] - away_data["xga"]
    ) + (
        home_data["form"] - away_data["form"]
    )

    # curva mais agressiva (evita concentração em 55–60%)
    probability = 50 + (strength * 15)

    # ajustes de cauda (edge real)
    if probability > 68:
        probability += 4
    elif probability < 45:
        probability -= 4

    # limite
    probability = max(1, min(99, probability))

    return round(probability, 2)

# ==============================
# CLASSIFICAÇÃO PROFISSIONAL
# ==============================

def classify(prob):
    if prob >= 70:
        return "🔥 ELITE - Entrada forte"
    elif prob >= 65:
        return "🟢 Baixo risco - Boa entrada"
    elif prob >= 60:
        return "🟡 Médio risco - Valor moderado"
    elif prob >= 54:
        return "🟡 Médio risco - Cautela"
    else:
        return "🔴 Alto risco - Evitar"

# ==============================
# EV (ESPERADO - PREPARADO)
# ==============================

def expected_value(prob, odd):
    return round((prob / 100 * odd) - 1, 3)

# ==============================
# JOGOS (EXEMPLO)
# ==============================

def get_matches():
    return [
        {"home": "Barcelona", "away": "Real Madrid", "odd": 1.85},
        {"home": "CRB", "away": "Sport", "odd": 2.10},
    ]

# ==============================
# ANÁLISE
# ==============================

def run_analysis():
    matches = get_matches()

    results = []

    for m in matches:
        prob = calculate_score(m["home"], m["away"])
        risk = classify(prob)

        ev = expected_value(prob, m["odd"])

        results.append({
            "Jogo": f"{m['home']} vs {m['away']}",
            "Probabilidade": prob,
            "Odd": m["odd"],
            "EV": ev,
            "Classificação": risk
        })

    return pd.DataFrame(results)

# ==============================
# UI
# ==============================

st.title("⚽ Greg Stats X V5.2")

if st.button("Rodar análise"):
    df = run_analysis()
    st.dataframe(df)

    st.markdown("### 🔎 Interpretação")
    st.markdown("""
    - 🔥 ELITE: aposta forte  
    - 🟢 Baixo risco: entrada boa  
    - 🟡 Médio: avaliar odds  
    - 🔴 Evitar: sem valor  
    """)

# ==============================
# DATA DO DIA
# ==============================

st.sidebar.write("📅 Data:", get_today())
