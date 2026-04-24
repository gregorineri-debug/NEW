import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

# -------------------------
# CONFIG
# -------------------------
BR_TZ = ZoneInfo("America/Sao_Paulo")

API_KEY = st.secrets["API_FOOTBALL_KEY"]  # coloque no secrets.toml

VALID_LEAGUE_IDS = [
    71, 72, 73, 74, 75,  # Brasil
    39, 40, 41,          # Inglaterra
    140, 141,            # Espanha
    135, 136,            # Itália
    78, 79,              # Alemanha
    61, 62,              # França
    94,                  # Portugal
    203,                 # Turquia
    218,                 # Áustria
    144,                 # Bélgica
    119,                 # Dinamarca
    103,                 # Noruega
    113,                 # Suécia
    179,                 # Escócia
    307,                 # Arábia Saudita
    128,                 # Argentina
    262,                 # Liga MX
    2, 3, 848,           # Champions / Europa / Conference
    13,                  # Libertadores
    11                   # Sudamericana
]

# -------------------------
# API FOOTBALL
# -------------------------
def get_events(date):
    url = "https://v3.football.api-sports.io/fixtures"

    headers = {
        "x-apisports-key": API_KEY
    }

    params = {
        "date": date
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)

        if response.status_code != 200:
            st.error(f"Erro API: {response.status_code}")
            return []

        data = response.json()
        return data.get("response", [])

    except Exception as err:
        st.error(f"Erro conexão API: {err}")
        return []

# -------------------------
# FILTROS
# -------------------------
def is_valid_league(event):
    try:
        return event["league"]["id"] in VALID_LEAGUE_IDS
    except:
        return False


def format_game(event):
    try:
        utc_time = datetime.fromisoformat(event["fixture"]["date"].replace("Z", "+00:00"))
        br_time = utc_time.astimezone(BR_TZ).strftime("%H:%M")

        return {
            "Hora": br_time,
            "Liga": event["league"]["name"],
            "Jogo": f"{event['teams']['home']['name']} vs {event['teams']['away']['name']}",
            "Status": event["fixture"]["status"]["short"]
        }

    except Exception as err:
        st.warning(f"Erro ao processar jogo: {err}")
        return None

# -------------------------
# UI
# -------------------------
st.set_page_config(
    page_title="Scanner PRO V7 (API-Football)",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Scanner PRO V7 (API-Football)")

date = st.date_input("Escolha a data")

events = get_events(date.strftime("%Y-%m-%d"))

st.write(f"Total retornado pela API: {len(events)}")

filtered_events = [e for e in events if is_valid_league(e)]

st.write(f"Jogos válidos: {len(filtered_events)}")

if st.button("Analisar Jogos"):

    results = []

    for event in filtered_events:
        item = format_game(event)
        if item:
            results.append(item)

    if results:
        df = pd.DataFrame(results).sort_values(by="Hora")

        st.dataframe(df, use_container_width=True)

        st.success(f"Total de jogos: {len(df)}")

        csv = df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name=f"scanner_{date}.csv",
            mime="text/csv"
        )

    else:
        st.warning("Nenhum jogo encontrado.")
