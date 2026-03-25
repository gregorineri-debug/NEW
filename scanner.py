from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import time

# ==============================
# INICIAR NAVEGADOR
# ==============================

options = webdriver.ChromeOptions()
options.add_argument("--headless")  # roda sem abrir janela

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# ==============================
# PEGAR JOGOS
# ==============================

def get_matches():

    url = "https://www.espn.com/soccer/fixtures"

    driver.get(url)
    time.sleep(5)

    matches = []

    rows = driver.find_elements(By.TAG_NAME, "tr")

    for row in rows:

        spans = row.find_elements(By.TAG_NAME, "span")

        if len(spans) >= 2:

            home = spans[0].text
            away = spans[1].text

            if home and away:
                matches.append((home, away))

    return matches


# ==============================
# SIMULAÇÃO DE DADOS
# ==============================

def get_team_stats(team):

    return {
        "xg": 1.5,
        "xga": 1.3,
        "form": 0.6
    }


# ==============================
# ANALISE
# ==============================

def analyze(matches):

    results = []

    for home, away in matches:

        h = get_team_stats(home)
        a = get_team_stats(away)

        score = 50 + ((h["xg"] - a["xga"]) * 20)

        results.append({
            "home": home,
            "away": away,
            "score": round(score, 2)
        })

    return pd.DataFrame(results)


# ==============================
# EXECUÇÃO
# ==============================

matches = get_matches()

print("Jogos encontrados:", len(matches))

df = analyze(matches)

print(df)

df.to_csv("jogos.csv", index=False)

driver.quit()
