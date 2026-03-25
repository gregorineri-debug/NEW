import pandas as pd

# ==============================
# DADOS (BASE REALISTA)
# ==============================

def get_team_data(team):

    db = {
        "Manchester City": {"xg": 2.4, "xga": 0.9, "form": 0.78},
        "Arsenal": {"xg": 2.0, "xga": 1.1, "form": 0.72},
        "Barcelona": {"xg": 2.2, "xga": 1.0, "form": 0.75},
        "Real Madrid": {"xg": 2.1, "xga": 1.0, "form": 0.74},
        "CRB": {"xg": 1.1, "xga": 1.3, "form": 0.48},
        "Sport": {"xg": 1.2, "xga": 1.4, "form": 0.50}
    }

    return db.get(team, {"xg": 1.3, "xga": 1.3, "form": 0.5})


# ==============================
# MODELO
# ==============================

def calculate_score(home, away):

    home_data = get_team_data(home)
    away_data = get_team_data(away)

    strength = (
        (home_data["xg"] - away_data["xga"]) * 2.0 +
        (home_data["form"] - away_data["form"]) * 1.5
    )

    prob = 50 + (strength * 20)

    # dispersão (corrige 53% travado)
    if prob > 65:
        prob += 5
    elif prob < 45:
        prob -= 5

    return round(max(1, min(99, prob)), 2)


# ==============================
# EV
# ==============================

def expected_value(prob, odd):
    return round((prob / 100 * odd) - 1, 3)


# ==============================
# CLASSIFICAÇÃO
# ==============================

def classify(prob, ev):

    if ev >= 0.07 and prob >= 66:
        return "🔥 ELITE"
    elif ev >= 0.04:
        return "🟢 VALOR FORTE"
    elif ev >= 0.02:
        return "🟡 VALOR"
    else:
        return "🔴 EVITAR"


# ==============================
# JOGOS
# ==============================

def get_matches():
    return [
        ("Manchester City", "Arsenal", 1.85),
        ("Barcelona", "Real Madrid", 1.90),
        ("CRB", "Sport", 2.10)
    ]


# ==============================
# ANÁLISE
# ==============================

def run():

    results = []

    for home, away, odd in get_matches():

        prob = calculate_score(home, away)
        ev = expected_value(prob, odd)
        risk = classify(prob, ev)

        results.append({
            "Jogo": f"{home} vs {away}",
            "Probabilidade": prob,
            "Odd": odd,
            "EV": ev,
            "Classificação": risk
        })

    df = pd.DataFrame(results)

    print("\nRESULTADO:\n")
    print(df)


# ==============================
# BACKTEST
# ==============================

def backtest():

    matches = [
        ("Manchester City", "Arsenal", 1.85, 1),
        ("Barcelona", "Real Madrid", 1.90, 0),
        ("CRB", "Sport", 2.10, 0)
    ]

    correct = 0

    for home, away, odd, real in matches:

        prob = calculate_score(home, away)

        pred = 1 if prob > 55 else 0

        if pred == real:
            correct += 1

    acc = correct / len(matches)

    print("\nBACKTEST")
    print(f"Acurácia: {round(acc * 100, 2)}%")


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    run()
    backtest()
