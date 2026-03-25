import streamlit as st
import pandas as pd
from datetime import datetime, date
import requests
from bs4 import BeautifulSoup
import pytz
import schedule
import time
import threading

# ==============================
# CONFIG
# ==============================

TIMEZONE = "America/Sao_Paulo"

# ==============================
# DATA / HORÁRIO CORRIGIDO
# ==============================

def get_today():
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).date()

# ==============================
# SCRAPERS (BASE - FBREF / FOOTYSTATS)
# ==============================

def get_fbref_data(team):
    # placeholder robusto
    return {
        "xg": 1.4,
        "xga": 1.2,
        "form": 0.6
    }

def get_footystats_data(team):
    # fallback
    return {
        "xg": 1.3,
        "xga": 1.25,
        "form": 0.55
    }

def get_team_data(team):
    try:
        data = get_fbref_data(team)
    except:
        data = get_footystats_data(team)

    return data

# ==============================
# SCORE MODEL (AJUSTADO)
# ==============================

def calculate_score(home, away):
    home_data = get_team_data(home)
    away_data = get_team_data(away)

    score = (
        home_data["xg"] - away_data["xga"]
    ) * 40 + (
        home_data["form"] - away_data["form"]
    ) * 20

    # normalização para probabilidade
    probability = 50 + score

    # limitar entre 0 e 100
    probability = max(0, min(100, probability))

    return round(probability, 2)

# ==============================
# CLASSIFICAÇÃO AJUSTADA
# ==============================

def classify(prob):
    if prob >= 65:
        return "🟢 Baixo risco - Entrada forte"
    elif prob >= 58:
        return "🟡 Médio risco - Entrada moderada"
    elif prob >= 52:
        return "🟡 Médio risco - Com cautela"
    else:
        return "🔴 Alto risco - Evitar"

# ==============================
# BACKTEST
# ==============================

def backtest(df):
    results = {
        "total": 0,
        "wins": 0
    }

    for _, row in df.iterrows():
        if row["result"] == row["prediction"]:
            results["wins"] += 1
        results["total"] += 1

    if results["total"] == 0:
        return 0

    return round((results["wins"] / results["total"]) * 100, 2)

# ==============================
# BUSCA JOGOS (SIMPLIFICADO)
# ==============================

def get_matches():
    today = get_today()

    # EXEMPLO (substituir por API real)
    matches = [
        {"home": "Barcelona", "away": "Real Madrid", "time": "16:00"},
        {"home": "CRB", "away": "Sport", "time": "19:30"},
    ]

    return matches

# ==============================
# BOT DIÁRIO
# ==============================

def run_daily():
    while True:
        print("Rodando análise diária...")
        matches = get_matches()

        for m in matches:
            prob = calculate_score(m["home"], m["away"])
            risk = classify(prob)

            print(f"{m['home']} vs {m['away']} | {prob}% | {risk}")

        time.sleep(86400)  # 24h


def start_bot():
    thread = threading.Thread(target=run_daily)
    thread.daemon = True
    thread.start()

# ==============================
# STREAMLIT UI
# ==============================

st.title("⚽ Greg Stats X V5.1 - Scanner")

if st.button("Rodar análise agora"):
    matches = get_matches()

    results = []

    for m in matches:
        prob = calculate_score(m["home"], m["away"])
        risk = classify(prob)

        results.append({
            "Jogo": f"{m['home']} vs {m['away']}",
            "Probabilidade": prob,
            "Classificação": risk
        })

    df = pd.DataFrame(results)

    st.dataframe(df)

# ==============================
# INICIAR BOT
# ==============================

start_bot()
