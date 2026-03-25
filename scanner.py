import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Greg Stats X Pro", layout="wide")

st.title("📊 Greg Stats X - Análise + Backtest + Jogos do Dia")

# =========================
# ⏰ TIMEZONE CORRIGIDO (SÃO PAULO)
# =========================
tz_sp = timezone(timedelta(hours=-3))
now_sp = datetime.now(tz_sp)

data_api = now_sp.strftime("%Y-%m-%d")

# =========================
# 📡 SOFASCORE (FILTRANDO DATA CORRETA)
# =========================
def buscar_jogos_sofascore(data):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{data}"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return []

    data_json = r.json()

    jogos = []

    for event in data_json.get("events", []):
        # Converter timestamp
        dt_utc = datetime.fromtimestamp(event["startTimestamp"], tz=timezone.utc)
        dt_sp = dt_utc.astimezone(tz_sp)

        # 🔥 FILTRO: somente jogos do DIA CORRETO
        if dt_sp.date() == now_sp.date():

            jogos.append({
                "Home": event["homeTeam"]["name"],
                "Away": event["awayTeam"]["name"],
                "League": event["tournament"]["name"],
                "Time (SP)": dt_sp.strftime("%H:%M")
            })

    return pd.DataFrame(jogos)

# =========================
# 🧠 SCORE HÍBRIDO (BASE)
# =========================
def calcular_score(jogo):

    # 🔴 PLACEHOLDER (substituir pelo seu Greg Stats X real)
    forma = np.random.uniform(0, 1)
    xg_diff = np.random.uniform(-1, 1)
    elenco = np.random.uniform(-1, 1)

    # 🔥 MODELO HÍBRIDO SIMPLIFICADO
    score = (
        50 +
        (forma * 20) +
        (xg_diff * 15) +
        (elenco * 15)
    )

    return round(score, 2)

# =========================
# 📊 ANÁLISE COMPLETA DO JOGO
# =========================
def analisar_jogo(row):

    score_home = calcular_score(row["Home"])
    score_away = calcular_score(row["Away"])

    diff = score_home - score_away

    # Probabilidade estimada
    prob_home = 50 + (diff * 1.2)

    if prob_home > 65:
        pick = f"{row['Home']} vence"
        risco = "🟢 Baixo risco"
    elif prob_home > 55:
        pick = f"{row['Home']} ou empate"
        risco = "🟡 Médio risco"
    else:
        pick = "Jogo equilibrado / evitar"
        risco = "🔴 Alto risco"

    return {
        "Score Casa": score_home,
        "Score Fora": score_away,
        "Diferença": round(diff, 2),
        "Prob Casa (%)": round(prob_home, 2),
        "Pick": pick,
        "Risco": risco
    }

# =========================
# 📅 BUSCAR JOGOS
# =========================
st.sidebar.header("📅 Jogos do Dia")

if st.sidebar.button("Carregar jogos de hoje"):

    jogos_df = buscar_jogos_sofascore(data_api)

    if jogos_df.empty:
        st.warning("Nenhum jogo encontrado para hoje.")
    else:
        st.success(f"{len(jogos_df)} jogos encontrados")

        resultados = []

        for _, jogo in jogos_df.iterrows():

            analise = analisar_jogo(jogo)

            resultados.append({
                **jogo,
                **analise
            })

        df_final = pd.DataFrame(resultados)

        st.subheader("📊 Análise dos Jogos (Greg Stats X)")

        st.dataframe(df_final)

# =========================
# 🧪 BACKTEST (BASE)
# =========================
st.sidebar.header("📂 Backtest")

uploaded_file = st.sidebar.file_uploader("Envie CSV", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # ⚠️ Esperado:
    # Score, League, Market, Odd, Result

    df["Profit"] = np.where(df["Result"] == 1, df["Odd"] - 1, -1)

    # =========================
    # 🎯 FILTROS
    # =========================
    min_score = st.sidebar.slider("Score mínimo", 0, 100, 70)

    leagues = df["League"].unique()
    markets = df["Market"].unique()

    selected_leagues = st.sidebar.multiselect("Ligas", leagues, default=leagues)
    selected_markets = st.sidebar.multiselect("Mercados", markets, default=markets)

    filtered = df[
        (df["Score"] >= min_score) &
        (df["League"].isin(selected_leagues)) &
        (df["Market"].isin(selected_markets))
    ]

    # =========================
    # 📊 MÉTRICAS
    # =========================
    total = len(filtered)
    lucro = filtered["Profit"].sum()

    roi = (lucro / total) * 100 if total > 0 else 0
    winrate = (filtered["Result"].sum() / total) * 100 if total > 0 else 0

    st.subheader("📈 Backtest")

    col1, col2, col3 = st.columns(3)
    col1.metric("Lucro", f"{lucro:.2f}")
    col2.metric("ROI %", f"{roi:.2f}%")
    col3.metric("Winrate %", f"{winrate:.2f}%")

    # =========================
    # 📉 CURVA DE BANCA
    # =========================
    filtered = filtered.reset_index(drop=True)
    filtered["Equity"] = filtered["Profit"].cumsum()

    st.subheader("📉 Curva de Banca")

    st.line_chart(filtered["Equity"])

else:
    st.info("Envie um CSV para análise")
