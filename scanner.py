import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# ==============================
# CONFIG
# ==============================

TIMEZONE = "America/Sao_Paulo"

# ==============================
# DATA CORRETA
# ==============================

def get_today():
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).date()

# ==============================
# DADOS (PLACEHOLDER - SUBSTITUIR FUTURO)
# ==============================

def get_team_data(team):
    # Dados simulados (substituir por FBref / FootyStats)
    return {
        "xg": 1.35,
        "xga": 1.20,
        "form": 0.60
    }

# ==============================
# MODELO DE PROBABILIDADE (CALIBRADO)
# ==============================

def calculate_score(home, away):
    home_data = get_team_data(home)
    away_data = get_team_data(away)

    strength = (
        home_data["xg"] - away_data["xga"]
    ) + (
        home_data["form"] - away_data["form"]
    )

    # curva mais agressiva (resolve problema de 53%)
    probability = 50 + (strength * 22)

    # ajuste de cauda (evita concentração)
    if probability > 65:
        probability += 6
    elif probability < 45:
        probability -= 6

    return round(max(1, min(99, probability)), 2)

# ==============================
# EV (VALOR ESPERADO)
# ==============================

def expected_value(prob, odd):
    return round((prob / 100) * odd - 1, 3)

# ==============================
# CLASSIFICAÇÃO PROFISSIONAL
# ==============================

def classify(prob, ev):
    if ev >= 0.05 and prob >= 62:
        return "🔥 ELITE - Entrada forte"
    elif ev >= 0.02 and prob >= 58:
        return "🟢 Valor positivo"
    elif ev >= 0 and prob >= 55:
        return "🟡 Médio risco - Valor neutro"
    else:
        return "🔴 Alto risco - Evitar"

# ==============================
# JOGOS (EXEMPLO)
# ==============================

def get_matches():
    return [
        {"home": "Barcelona", "away": "Real Madrid", "odd": 1.85},
        {"home": "CRB", "away": "Sport", "odd": 2.10},
    ]

# ==============================
# ANÁLISE PRINCIPAL
# ==============================

def run_analysis():
    matches = get_matches()

    results = []

    for m in matches:
        prob = calculate_score(m["home"], m["away"])
        ev = expected_value(prob, m["odd"])
        risk = classify(prob, ev)

        results.append({
            "Jogo": f"{m['home']} vs {m['away']}",
            "Probabilidade": prob,
            "Odd": m["odd"],
            "EV": ev,
            "Classificação": risk
        })

    return pd.DataFrame(results)

# ==============================
# STREAMLIT UI
# ==============================

st.title("⚽ Greg Stats X V5.3")

if st.button("Rodar análise"):
    df = run_analysis()
    st.dataframe(df)

    st.markdown("### 📊 Interpretação")
    st.markdown("""
    - 🔥 ELITE: maior valor estatístico  
    - 🟢 Valor positivo: entrada interessante  
    - 🟡 Médio risco: depende da odd  
    - 🔴 Evitar: sem valor esperado  
    """)

# ==============================
# DATA
# ==============================

st.sidebar.write("📅 Data:", get_today())
