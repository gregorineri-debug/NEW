import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import json
import time

# -------------------------
# CONFIG
# -------------------------
BR_TZ = ZoneInfo("America/Sao_Paulo")

VALID_LEAGUE_IDS = [
    325,390,17,18,8,54,35,44,23,53,34,182,955,
    155,703,45,38,247,172,11653,11539,11536,
    170,39,808,36,242,185,37,131,192,937,
    11621,11620,20,11540,11541,406,202,
    238,239,152,40,215,52,278,
    357,7,679,17015,16,384,480,133,1
]

LEAGUE_NAMES = {
    325: "Brasileirão", 390: "Série B", 17: "Premier League",
    18: "Championship", 8: "La Liga", 54: "La Liga 2",
    35: "Bundesliga", 44: "2. Bundesliga", 23: "Serie A",
    53: "Serie B Itália", 34: "Ligue 1", 182: "Ligue 2",
    955: "Saudi Pro League", 155: "Argentina Liga",
    703: "Primera Nacional", 45: "Áustria", 38: "Bélgica",
    247: "Bulgária", 172: "Rep. Tcheca", 11653: "Chile",
    11539: "Colômbia Apertura", 11536: "Colômbia Finalización",
    170: "Croácia", 39: "Dinamarca", 808: "Egito",
    36: "Escócia", 242: "MLS", 185: "Grécia",
    37: "Eredivisie", 131: "Eerste Divisie", 192: "Irlanda",
    937: "Marrocos", 11621: "Liga MX Apertura",
    11620: "Liga MX Clausura", 20: "Noruega",
    11540: "Paraguai Apertura", 11541: "Paraguai Clausura",
    406: "Peru", 202: "Polônia", 238: "Portugal",
    239: "Portugal 2", 152: "Romênia", 40: "Suécia",
    215: "Suíça", 52: "Turquia", 278: "Uruguai",
    357: "FIFA Club World Cup", 7: "Champions League",
    679: "Europa League", 17015: "Conference League",
    16: "FIFA World Cup", 384: "Libertadores",
    480: "Sudamericana", 133: "Copa América",
    1: "Eurocopa"
}

# -------------------------
# REQUESTS
# -------------------------
def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.sofascore.com/football",
        "Origin": "https://www.sofascore.com"
    }


def get_events_requests(date_str):
    urls = [
        f"https://www.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}",
        f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
    ]

    session = requests.Session()
    session.headers.update(get_headers())

    try:
        session.get("https://www.sofascore.com/football", timeout=15)
        time.sleep(1)
    except Exception:
        pass

    last_error = ""

    for url in urls:
        try:
            r = session.get(url, timeout=20)

            if r.status_code == 200:
                data = r.json()
                return data.get("events", []), "OK via requests"

            last_error = f"HTTP {r.status_code}"

        except Exception as err:
            last_error = str(err)

    return [], f"Requests falhou: {last_error}"


# -------------------------
# PLAYWRIGHT
# -------------------------
def get_events_playwright(date_str):
    try:
        from playwright.sync_api import sync_playwright
    except Exception as err:
        return [], f"Playwright não instalado: {err}"

    url = f"https://www.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
                locale="pt-BR",
                timezone_id="America/Sao_Paulo"
            )

            page = context.new_page()

            page.goto("https://www.sofascore.com/football", wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)

            page.goto(url, wait_until="networkidle", timeout=60000)

            content = page.inner_text("body")

            browser.close()

            data = json.loads(content)

            return data.get("events", []), "OK via Playwright"

    except Exception as err:
        return [], f"Playwright falhou: {err}"


# -------------------------
# BUSCA PRINCIPAL
# -------------------------
@st.cache_data(ttl=300)
def get_events(date_str):
    events, status = get_events_requests(date_str)

    if events:
        return events, status

    events, status2 = get_events_playwright(date_str)

    if events:
        return events, status2

    return [], f"{status} | {status2}"


# -------------------------
# FILTROS
# -------------------------
def get_league_id(event):
    try:
        return event["tournament"]["uniqueTournament"]["id"]
    except Exception:
        return None


def is_valid_league(event):
    return get_league_id(event) in VALID_LEAGUE_IDS


def is_same_day_br(event, selected_date):
    try:
        utc_time = datetime.fromtimestamp(
            event["startTimestamp"],
            tz=ZoneInfo("UTC")
        )
        br_time = utc_time.astimezone(BR_TZ)
        return br_time.date() == selected_date
    except Exception:
        return False


def format_game(event):
    try:
        league_id = get_league_id(event)

        utc_time = datetime.fromtimestamp(
            event["startTimestamp"],
            tz=ZoneInfo("UTC")
        )

        br_time = utc_time.astimezone(BR_TZ).strftime("%H:%M")

        home = event.get("homeTeam", {}).get("name", "Mandante")
        away = event.get("awayTeam", {}).get("name", "Visitante")

        return {
            "Hora": br_time,
            "Liga": LEAGUE_NAMES.get(league_id, f"Liga ID {league_id}"),
            "Jogo": f"{home} vs {away}",
            "SofaScore ID": event.get("id", "")
        }

    except Exception as err:
        st.warning(f"Erro ao processar jogo: {err}")
        return None


# -------------------------
# UI
# -------------------------
st.set_page_config(
    page_title="Scanner PRO SofaScore",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Scanner PRO — SofaScore Automático")
st.caption("Tentativa automática via requests + Playwright + fallback manual.")

date = st.date_input("Escolha a data")
date_str = date.strftime("%Y-%m-%d")

events, status = get_events(date_str)

st.write(f"Status da busca: {status}")
st.write(f"Total bruto retornado: {len(events)}")

if len(events) == 0:
    st.warning("Automático falhou. Use o fallback manual abaixo.")

    with st.expander("Fallback manual por JSON"):
        st.write("Abra o link, copie o JSON e cole abaixo:")
        st.code(f"https://www.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}")

        pasted_json = st.text_area("Cole aqui o JSON do SofaScore")

        if pasted_json:
            try:
                data = json.loads(pasted_json)
                events = data.get("events", [])
                st.success(f"JSON carregado manualmente: {len(events)} jogos")
            except Exception as err:
                st.error(f"JSON inválido: {err}")

filtered_events = [
    e for e in events
    if is_valid_league(e) and is_same_day_br(e, date)
]

st.write(f"Jogos válidos nas ligas cadastradas: {len(filtered_events)}")

if st.button("Analisar Jogos"):

    results = []

    for event in filtered_events:
        item = format_game(event)
        if item:
            results.append(item)

    if results:
        df = pd.DataFrame(results).sort_values(by="Hora")

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.success(f"Total de jogos encontrados: {len(df)}")

        csv = df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name=f"scanner_sofascore_{date_str}.csv",
            mime="text/csv"
        )

    else:
        st.warning("Nenhum jogo encontrado.")
