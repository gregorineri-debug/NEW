import requests
import pandas as pd
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ==============================
# SCRAPING FBREF (TABELA)
# ==============================

def get_fbref_team_stats():

    url = "https://fbref.com/en/comps/9/Premier-League-Stats"

    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    tables = pd.read_html(str(soup))

    # tabela principal (ajuste se necessário)
    df = tables[0]

    # limpa colunas duplicadas
    df.columns = df.columns.droplevel()

    return df
