import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Backtest Greg Stats X", layout="wide")

st.title("📊 Backtest - Greg Stats X (V4.5)")

# =========================
# 📥 Upload de dados
# =========================
st.sidebar.header("📂 Upload da Base Histórica")
uploaded_file = st.sidebar.file_uploader("Envie seu CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # =========================
    # 🔎 Ajuste dos dados
    # =========================
    # Esperado no CSV:
    # Date, League, Market, Score, Odd, Result (1/0)

    df["Profit"] = np.where(df["Result"] == 1, df["Odd"] - 1, -1)

    # =========================
    # 🎛️ Filtros
    # =========================
    st.sidebar.header("🎯 Filtros")

    min_score = st.sidebar.slider("Score mínimo", 0, 100, 70)
    selected_leagues = st.sidebar.multiselect(
        "Selecione as ligas",
        options=df["League"].unique(),
        default=df["League"].unique()
    )
    selected_markets = st.sidebar.multiselect(
        "Selecione os mercados",
        options=df["Market"].unique(),
        default=df["Market"].unique()
    )

    # Aplicando filtros
    filtered_df = df[
        (df["Score"] >= min_score) &
        (df["League"].isin(selected_leagues)) &
        (df["Market"].isin(selected_markets))
    ].copy()

    st.subheader("📋 Dados Filtrados")
    st.dataframe(filtered_df)

    # =========================
    # 📊 Métricas
    # =========================
    total_bets = len(filtered_df)
    total_profit = filtered_df["Profit"].sum()
    total_stake = total_bets  # stake fixa = 1 unidade

    roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
    winrate = (filtered_df["Result"].sum() / total_bets) * 100 if total_bets > 0 else 0

    st.subheader("📈 Resultados do Backtest")

    col1, col2, col3 = st.columns(3)
    col1.metric("Lucro Total", f"{total_profit:.2f}")
    col2.metric("ROI (%)", f"{roi:.2f}%")
    col3.metric("Winrate (%)", f"{winrate:.2f}%")

    # =========================
    # 📉 Curva de banca
    # =========================
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df["Equity"] = filtered_df["Profit"].cumsum()

    st.subheader("📉 Curva de Banca")

    fig, ax = plt.subplots()
    ax.plot(filtered_df["Equity"])
    ax.set_title("Evolução da Banca")
    ax.set_xlabel("Jogos")
    ax.set_ylabel("Lucro Acumulado")

    st.pyplot(fig)

    # =========================
    # 🔍 Análise por Score
    # =========================
    st.subheader("🔎 Performance por Score")

    bins = [0, 60, 70, 80, 90, 100]
    labels = ["<60", "60-69", "70-79", "80-89", "90+"]

    filtered_df["Score_Range"] = pd.cut(filtered_df["Score"], bins=bins, labels=labels)

    score_analysis = filtered_df.groupby("Score_Range").agg(
        Bets=("Result", "count"),
        Wins=("Result", "sum"),
        Profit=("Profit", "sum")
    )

    score_analysis["Winrate (%)"] = (score_analysis["Wins"] / score_analysis["Bets"]) * 100
    score_analysis["ROI (%)"] = (score_analysis["Profit"] / score_analysis["Bets"]) * 100

    st.dataframe(score_analysis)

else:
    st.info("⬆️ Faça upload de um CSV para iniciar o backtest.")
