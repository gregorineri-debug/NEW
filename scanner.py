import requests
import pandas as pd

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ==============================
# SCRAPER ROBUSTO
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

        # tenta achar tabela com "Squad" ou "Team"
        for i, t in enumerate(tables):

            for col in t.columns:
                if "Squad" in str(col) or "Team" in str(col):
                    print(f"Usando tabela {i}")
                    return t

        # fallback: maior tabela
        df = max(tables, key=lambda x: x.shape[1])

        return df

    except Exception as e:
        print("Erro no scraping:", e)
        return None


# ==============================
# DADOS DO TIME
# ==============================

def get_team_data(team, df):

    # fallback padrão (NUNCA quebra)
    fallback = {"xg": 1.3, "xga": 1.3, "form": 0.5}

    if df is None:
        return fallback

    try:
        row = df[df.iloc[:, 0].astype(str).str.contains(team, na=False)]

        if row.empty:
            print(f"Time não encontrado: {team}")
            return fallback

        row = row.iloc[0]

        xg = 1.3
        xga = 1.3

        for col in df.columns:
            col_str = str(col).lower()

            try:
                val = float(row[col])
            except:
                continue

            if "xg" in col_str and "against" not in col_str:
                xg = val

            if "against" in col_str and "xg" in col_str:
                xga = val

        form = (xg - xga) / 2 + 0.5

        return {
            "xg": xg,
            "xga": xga,
            "form": form
        }

    except Exception as e:
        print("Erro no time:", e)
        return fallback


# ==============================
# MODELO CALIBRADO
# ==============================

def calculate_score(home, away, df):

    home_data = get_team_data(home, df)
    away_data = get_team_data(away, df)

    strength = (
        (home_data["xg"] - away_data["xga"]) * 2.2 +
        (home_data["form"] - away_data["form"]) * 1.5
    )

    prob = 50 + (strength * 22)

    # dispersão (corrige travamento em 53%)
    if prob > 65:
        prob += 5
    elif prob < 45:
        prob -= 5

    return round(max(1, min(99, prob)), 2)


# ==============================
# EXPECTED VALUE
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
# EXECUÇÃO PRINCIPAL
# ==============================

def run():

    df = get_fbref_table()

    if df is None:
        print("\n⚠️ Usando fallback (sem scraping)\n")

    matches = get_matches()

    for home, away, odd in matches:

        prob = calculate_score(home, away, df)
        ev = expected_value(prob, odd)
        risk = classify(prob, ev)

        print(f"\n{home} vs {away}")
        print(f"Probabilidade: {prob}%")
        print(f"Odd: {odd}")
        print(f"EV: {ev}")
        print(f"Classificação: {risk}")
        print("-" * 40)


# ==============================
# BACKTEST SIMPLES
# ==============================

def backtest():

    df = get_fbref_table()

    matches = [
        ("Manchester City", "Arsenal", 1.85, 1),
        ("Barcelona", "Real Madrid", 1.90, 0),
        ("CRB", "Sport", 2.10, 0)
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

    print("\nBACKTEST:\n")

    for r in results:
        print(r)


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    run()

    print("\n=================\n")

    backtest()
