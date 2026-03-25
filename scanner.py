import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt

st.set_page_config(page_title="Greg Stats X - Backtest + SofaScore", layout="wide")

st.title("📊 Greg Stats X - Backtest + Jogos do Dia (SofaScore)")

# =========================
# ⏰ FUSO HORÁRIO (São Paulo)
# =========================
tz_sp = timezone(timedelta(hours=-3))
hoje_sp = datetime.now(tz_sp).date()
data_api = hoje_sp.strftime("%Y-%m-%d")

# =========================
# 📡 FUNÇÃO SOFASCORE
# =========================
def buscar_jogos_sofascore(data):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{data}"
    
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return pd.DataFrame()

    data_json = response.json()

    jogos = []

    for event in data_json.get("events", []):
        jogos.append({
            "Home": event["homeTeam"]["name"],
            "Away": event["awayTeam"]["name"],
            "League": event["tournament"]["name"],
            "Timestamp": event["startTimestamp"]
        })

    df = pd.DataFrame(jogos)

    if not df.empty:
        df["Date_SP"] = pd.to_datetime(df["Timestamp"], unit="s", utc=True).dt.tz_convert("America/Sao_Paulo")

    return df

# =========================
# 📂 BACKTEST UPLOAD
# =========================
st.sidebar.header("📂 Upload da Base Histórica")

uploaded_file = st.sidebar.file_uploader("Envie seu CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Esperado:
    # Score, League, Market, Odd, Result (1/0)

    df["Profit"] = np.where(df["Result"] == 1, df["Odd"] - 1, -1)

    # =========================
    # 🎯 FILTROS
    # =========================
    st.sidebar.header("🎯 Filtros")

    min_score = st.sidebar.slider("Score mínimo", 0, 100, 70)

    selected_leagues = st.sidebar.multiselect(
        "Ligas",
        options=df["League"].unique(),
        default=df["League"].unique()
    )

    selected_markets = st.sidebar.multiselect(
        "Mercados",
        options=df["Market"].unique(),
        default=df["Market"].unique()
    )

    filtered_df = df[
        (df["Score"] >= min_score) &
        (df["League"].isin(selected_leagues)) &
        (df["Market"].isin(selected_markets))
    ].copy()

    # =========================
    # 📊 MÉTRICAS
    # =========================
    total_bets = len(filtered_df)
    total_profit = filtered_df["Profit"].sum()
    total_stake = total_bets

    roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
    winrate = (filtered_df["Result"].sum() / total_bets) * 100 if total_bets > 0 else 0

    st.subheader("📈 Resultados do Backtest")

    col1, col2, col3 = st.columns(3)
    col1.metric("Lucro", f"{total_profit:.2f}")
    col2.metric("ROI (%)", f"{roi:.2f}%")
    col3.metric("Winrate (%)", f"{winrate:.2f}%")

    # =========================
    # 📉 CURVA DE BANCA
    # =========================
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df["Equity"] = filtered_df["Profit"].cumsum()

    st.subheader("📉 Curva de Banca")

    fig, ax = plt.subplots()
    ax.plot(filtered_df["Equity"])
    ax.set_title("Evolução da Banca")
    ax.set_xlabel("Jogos")
    ax.set_ylabel("Lucro")

    st.pyplot(fig)

    # =========================
    # 🔎 ANÁLISE POR SCORE
    # =========================
    st.subheader("🔎 Performance por Score")

    bins = [0, 60, 70, 80, 90, 100]
    labels = ["<60", "60-69", "70-79", "80-89", "90+"]

    filtered_df["Score_Range"] = pd.cut(filtered_df["Score"], bins=bins, labels=labels)

    score_table = filtered_df.groupby("Score_Range").agg(
        Bets=("Result", "count"),
        Wins=("Result", "sum"),
        Profit=("Profit", "sum")
    )

    score_table["Winrate (%)"] = (score_table["Wins"] / score_table["Bets"]) * 100
    score_table["ROI (%)"] = (score_table["Profit"] / score_table["Bets"]) * 100

    st.dataframe(score_table)

else:
    st.info("⬆️ Faça upload do CSV para análise")

# =========================
# 📡 JOGOS DO DIA (SOFASCORE)
# =========================
st.sidebar.header("📅 Jogos do Dia")

if st.sidebar.button("Carregar jogos do dia (SofaScore)"):

    jogos_df = buscar_jogos_sofascore(data_api)

    if jogos_df.empty:
        st.warning("Nenhum jogo encontrado.")
    else:
        st.subheader("⚽ Jogos do dia (GMT-3 São Paulo)")
        st.dataframe(jogos_df)

        st.success(f"Total de jogos encontrados: {len(jogos_df)}")

# =========================
# 🔮 ESPAÇO PARA SEU MODELO
# =========================
st.subheader("🧠 Integração com Greg Stats X")

st.info("""
Aqui você deve integrar sua lógica de score (Greg Stats X V4.5).

Para cada jogo:
1. Calcular Score
2. Converter para probabilidade
3. Comparar com odds
4. Aplicar filtro de EV
5. Gerar apostas
""")
