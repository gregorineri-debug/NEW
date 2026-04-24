import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

# -------------------------
# CONFIG
# -------------------------
BR_TZ = ZoneInfo("America/Sao_Paulo")

# 🔐 API KEY (pode vir do secrets ou direto aqui)
try:
    API_KEY = st.secrets["API_FOOTBALL_KEY"]
except:
    API_KEY = import http.client

conn = http.client.HTTPSConnection("v3.football.api-sports.io")

headers = {
    'x-apisports-key': "XxXxXxXxXxXxXxXxXxXxXxXx"
    }

conn.request("GET", "/leagues", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))  # 👈 COLE SUA CHAVE AQUI SE NÃO USAR SECRETS

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

        if data.get("errors"):
            st.error(f"Erro da API: {data['errors']}")
            return []

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
        utc_time = datetime.fromisoformat(
            event["fixture"]["date"].replace("Z", "+00:00")
        )

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
    page_title="Scanner PRO V7",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Scanner PRO V7 — API-Football")

date = st.date_input("Escolha a data")

# trava se não colocou chave
if API_KEY == "SUA_CHAVE_AQUI":
    st.error("⚠️ Cole sua chave da API-Football no código ou no secrets.toml")
    st.stop()

events = get_events(date.strftime("%Y-%m-%d"))

st.write(f"Total bruto: {len(events)}")

filtered_events = [
    e for e in events if is_valid_league(e)
]

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

    else:
        st.warning("Nenhum jogo encontrado.")
