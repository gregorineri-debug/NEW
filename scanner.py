import requests
import pandas as pd
import math
from datetime import datetime

# ==============================
# CONFIG
# ==============================

API_URL = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={date}&s=Soccer"


# ==============================
# PEGAR JOGOS
# ==============================

def get_matches(date):

    url = API_URL.format(date=date)

    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        matches = []

        for m in data.get("events", []):

            home = m.get("strHomeTeam")
            away = m.get("strAwayTeam")

            if home and away:
                matches.append((home, away))

        return matches

    except Exception as e:
        print("Erro ao buscar jogos:", e)
        return []


# ==============================
# MODELO SIMPLES (ROBUSTO)
# ==============================

def team_strength(team):

    elite = ["Real Madrid", "Manchester City", "Bayern Munich", "Barcelona"]

    strong = ["Arsenal", "Liverpool", "PSG", "Chelsea"]

    if team in elite:
        return 2.3

    elif team in strong:
        return 2.0

    return 1.5


def calculate_prob(home, away):

    h = team_strength(home)
    a = team_strength(away)

    diff = h - a

    prob = 50 + (diff * 20)

    return max(5, min(95, prob))


# ==============================
# EV
# ==============================

def expected_value(prob, odd):

    return round((prob / 100) - (1 / odd), 3)


# ==============================
# PICK
# ==============================

def get_pick(prob, ev):

    if ev <= 0:
        return "❌ NO BET"

    if prob >= 55:
        return "🏠 HOME"

    if prob <= 45:
        return "✈️ AWAY"

    return "❌ NO BET"


# ==============================
# EXECUÇÃO
# ==============================

def run_analysis(date):

    matches = get_matches(date)

    results = []

    for home, away in matches:

        prob = calculate_prob(home, away)

        odd = 1.90  # pode integrar depois

        ev = expected_value(prob, odd)

        pick = get_pick(prob, ev)

        results.append({
            "Jogo": f"{home} vs {away}",
            "Probabilidade": round(prob, 2),
            "Odd": odd,
            "EV": ev,
            "Pick": pick
        })

    return pd.DataFrame(results)


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    date = datetime.today().strftime("%Y-%m-%d")

    df = run_analysis(date)

    print(df)

    df.to_csv(f"analise_{date}.csv", index=False)
