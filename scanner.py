import requests
import pandas as pd
from bs4 import BeautifulSoup

# ==============================
# CONFIG
# ==============================

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ==============================
# SCRAPER (ROBUSTO)
# ==============================

def get_fbref_table():

    url = "https://fbref.com/en/comps/9/Premier-League-Stats"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            print("Erro HTTP:", res.status_code)
            return None

        tables = pd.read_html(res.text)

        print(f"Tabelas encontradas: {len(tables)}")

        # pega a maior tabela (geralmente a correta)
        df = max(tables, key=lambda x: x.shape[1])

        return df

    except Exception as e:
        print("Erro no scraping:", e)
        return None

# ==============================
# DADOS DO TIME
# ==============================

def get_team_data(team, df):

    if df is None:
        return {"xg": 1.3, "xga": 1.3, "form": 0.5}

    try:
        row = df[df.iloc[:, 0].astype(str).str.contains(team, na=False)]

        if row.empty:
            print(f"Time não encontrado: {team}")
            return {"xg": 1.3, "xga": 1.3, "form": 0.5}

        row = row.iloc[0]

        def get_col_value(possible_names):
            for col in df.columns:
                for name in possible_names:
                    if name.lower() in str(col).lower():
                        try:
                            return float(row[col])
                        except:
                            return 1.3
            return 1.3

        xg = get_col_value(["xg"])
        xga = get_col_value(["xga", "xg against"])

        form = (xg - xga) / 2 + 0.5

        return {
            "xg": xg,
            "xga": xga,
            "form": form
        }

    except Exception as e:
        print("Erro ao extrair time:", e)
        return {"xg": 1.3, "xga": 1.3, "form": 0.5}

# ==============================
# MODELO (AJUSTADO)
# ==============================

def calculate_score(home, away, df):

    home_data = get_team_data(home, df)
    away_data = get_team_data(away, df)

    strength = (
        (home_data["xg"] - away_data["xga"]) * 1.8 +
        (home_data["form"] - away_data["form"]) * 1.2
    )

    prob = 50 + (strength * 25)

    # dispersão (corrige 53% travado)
    if prob > 65:
        prob += 4
    elif prob < 45:
        prob -= 4

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
# JOGOS DE TESTE
# ==============================

def get_matches():
    return [
        {"home": "Manchester City", "away": "Arsenal", "odd": 1.85},
        {"home": "Barcelona", "away": "Real Madrid", "odd": 1.90},
        {"home": "CRB", "away": "Sport", "odd": 2.10}
    ]

# ==============================
# EXECUÇÃO
# ==============================

def run():

    df = get_fbref_table()

    if df is None:
        print("Falha ao carregar dados")
        return

    results = []

    for m in get_matches():

        prob = calculate_score(m["home"], m["away"], df)
        ev = expected_value(prob, m["odd"])
        risk = classify(prob, ev)

        results.append({
            "Jogo": f"{m['home']} vs {m['away']}",
            "Probabilidade": prob,
            "Odd": m["odd"],
            "EV": ev,
            "Classificação": risk
        })

    df_result = pd.DataFrame(results)

    print("\nRESULTADO FINAL:\n")
    print(df_result)


# ==============================
# BACKTEST SIMPLES
# ==============================

def backtest():

    df = get_fbref_table()

    if df is None:
        return

    # histórico simulado (trocar por jogos reais depois)
    matches = [
        ("Manchester City", "Arsenal", 1.8, 1),
        ("Barcelona", "Real Madrid", 1.9, 0),
        ("CRB", "Sport", 2.1, 0)
    ]

    results = []

    for home, away, odd, real in matches:

        prob = calculate_score(home, away, df)

        pred = 1 if prob > 55 else 0

        results.append({
            "Jogo": f"{home} vs {away}",
            "Prob": prob,
            "Acertou": pred == real
        })

    df_backtest = pd.DataFrame(results)

    print("\nBACKTEST:\n")
    print(df_backtest)


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    run()

    print("\n--- BACKTEST ---\n")

    backtest()
