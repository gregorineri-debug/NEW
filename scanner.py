import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

# -------------------------
# CONFIG
# -------------------------
BR_TZ = ZoneInfo("America/Sao_Paulo")

API_KEY = "COLE_SUA_CHAVE_AQUI"

VALID_LEAGUE_IDS = [
    71, 72, 73, 74, 75,
    39, 40, 41,
    140, 141,
    135, 136,
    78, 79,
    61, 62,
    94,
    203,
    218,
    144,
    119,
    103,
    113,
    179,
    307,
    128,
    262,
    2, 3, 848,
    13,
    11
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
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            st.error(f"Erro API: HTTP {response.status_code}")
            st.text(response.text[:500])
            return []

        data = response.json()

        if "errors" in data and data["errors"]:
            st.error(f"Erro retornado pela API: {data['errors']}")
            return []

        return data.get("response", [])

    except Exception as err:
        st.error(f"Erro de conexão com API: {err}")
        return []

# -------------------------
# FILTROS
# -------------------------
def is_valid_league(event):
    try:
        return event["league"]["id"] in VALID_LEAGUE_IDS
    except Exception:
        return False


def format_game(event):
    try:
        utc_time = datetime.fromisoformat(
            event["fixture"]["date"].replace("Z", "+00:00")
        )

        br_time = utc_time.astimezone(BR_TZ).strftime("%H:%M")

        league_id = event["league"]["id"]
        league_name = event["league"]["name"]
        country = event["league"]["country"]

        home = event["teams"]["home"]["name"]
        away = event["teams"]["away"]["name"]

        status = event["fixture"]["status"]["short"]

        return {
            "Hora": br_time,
            "País": country,
            "Liga": league_name,
            "Liga ID": league_id,
            "Jogo": f"{home} vs {away}",
            "Status": status
        }

    except Exception as err:
        st.warning(f"Erro ao processar jogo: {err}")
        return None

# -------------------------
# UI
# -------------------------
st.set_page_config(
    page_title="Scanner PRO V7",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Scanner PRO V7 — API-Football")
st.caption("Scanner com API-Football / API-Sports")

date = st.date_input("Escolha a data")

if API_KEY == "COLE_SUA_CHAVE_AQUI":
    st.error("⚠️ Troque COLE_SUA_CHAVE_AQUI pela sua chave da API-Sports.")
    st.stop()

events = get_events(date.strftime("%Y-%m-%d"))

st.write(f"Total bruto retornado pela API: {len(events)}")

filtered_events = [
    e for e in events
    if is_valid_league(e)
]

st.write(f"Jogos válidos nas ligas cadastradas: {len(filtered_events)}")

if st.button("Analisar Jogos"):

    results = []

    for event in filtered_events:
        item = format_game(event)
        if item:
            results.append(item)

    if results:
        df = pd.DataFrame(results)
        df = df.sort_values(by="Hora")

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.success(f"Total de jogos encontrados: {len(df)}")

        csv = df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name=f"scanner_pro_{date.strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )

    else:
        st.warning("Nenhum jogo encontrado nas ligas cadastradas.")
