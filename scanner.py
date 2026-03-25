import requests
import pandas as pd
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}


# ==============================
# BUSCAR JOGOS (API SIMPLES)
# ==============================

def get_matches():

    url = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d=2024-01-01&s=Soccer"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        data = res.json()

        matches = []

        for m in data.get("events", []):

            home = m.get("strHomeTeam")
            away = m.get("strAwayTeam")

            if home and away:
                matches.append((home, away))

        return matches

    except:
        return []


# ==============================
# DADOS SIMPLIFICADOS POR TIME
# ==============================

def get_team_data(team):

    # simulação controlada (evita falha total)
    base_strength = {
        "Real Madrid": 2.2,
        "Barcelona": 2.1,
        "Manchester City": 2.3,
        "Arsenal": 1.9
    }

    strength = base_strength.get(team, 1.3)

    return {
        "xg": strength,
        "xga": 1.5,
        "form": strength / 3
    }


# ==============================
# MONTAR DATASET
# ==============================

def build_dataset():

    matches = get_matches()

    if not matches:
        print("Nenhum jogo encontrado")
        return pd.DataFrame()

    rows = []

    for home, away in matches:

        h = get_team_data(home)
        a = get_team_data(away)

        rows.append({
            "home": home,
            "away": away,

            "home_xg": h["xg"],
            "away_xg": a["xg"],

            "home_form": h["form"],
            "away_form": a["form"],
        })

    return pd.DataFrame(rows)


# ==============================
# EXPORTAR
# ==============================

def save_csv(df):

    if df.empty:
        print("DataFrame vazio")
        return

    filename = f"matches_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(filename, index=False)

    print(f"CSV salvo: {filename}")


# ==============================
# EXECUÇÃO
# ==============================

df = build_dataset()

print(df)

save_csv(df)
