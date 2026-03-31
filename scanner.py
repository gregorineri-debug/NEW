# -------------------------
# MÉTRICAS NOVAS (REFINADAS)
# -------------------------

def get_team_stats(team_id):

    matches = get_team_matches(team_id, 10)

    wins = 0
    goals_for = 0
    goals_against = 0
    games = 0

    for m in matches:
        try:
            hs = m["homeScore"]["current"]
            as_ = m["awayScore"]["current"]

            if hs is None or as_ is None:
                continue

            if m["homeTeam"]["id"] == team_id:
                gf, ga = hs, as_
                if hs > as_:
                    wins += 1
            else:
                gf, ga = as_, hs
                if as_ > hs:
                    wins += 1

            goals_for += gf
            goals_against += ga
            games += 1
        except:
            continue

    if games == 0:
        return 0.5, 1, 1

    winrate = wins / games
    avg_gf = goals_for / games
    avg_ga = goals_against / games

    return winrate, avg_gf, avg_ga


# -------------------------
# PERFIL DA LIGA (GOLS)
# -------------------------

OVER_LEAGUES = [35, 44, 37, 131, 242, 20]  # Alemanha, Holanda, MLS, Noruega
UNDER_LEAGUES = [155, 703, 11540, 11541, 278, 406]  # Argentina, Paraguai, Uruguai, Peru


# -------------------------
# SCORE NOVO (INTELIGENTE)
# -------------------------

def calculate_score(home_id, away_id, league_id):

    h_win, h_gf, h_ga = get_team_stats(home_id)
    a_win, a_gf, a_ga = get_team_stats(away_id)

    # Força base
    home_strength = (h_win * 1.5) + (h_gf * 0.8)
    away_strength = (a_win * 1.5) + (a_gf * 0.8)

    # Fragilidade
    home_weak = h_ga * 0.7
    away_weak = a_ga * 0.7

    # Vantagem de mando
    home_adv = 0.25

    # Penalização favorito fora
    away_penalty = 0.15

    score = (home_strength - away_weak + home_adv) - (away_strength - home_weak + away_penalty)

    return score


# -------------------------
# PREVISÃO FINAL
# -------------------------

def predict(e):

    league_id = e["tournament"]["uniqueTournament"]["id"]

    score = calculate_score(
        e["homeTeam"]["id"],
        e["awayTeam"]["id"],
        league_id
    )

    # PICK DE VITÓRIA
    winner = "HOME" if score > 0 else "AWAY"
    edge = abs(score)

    # -------------------------
    # PICK DE GOLS
    # -------------------------

    h_win, h_gf, h_ga = get_team_stats(e["homeTeam"]["id"])
    a_win, a_gf, a_ga = get_team_stats(e["awayTeam"]["id"])

    avg_total_goals = (h_gf + h_ga + a_gf + a_ga) / 2

    if league_id in OVER_LEAGUES:
        goal_pick = "OVER 2.5"
    elif league_id in UNDER_LEAGUES:
        goal_pick = "UNDER 2.5"
    else:
        if avg_total_goals >= 2.8:
            goal_pick = "OVER 2.5"
        elif avg_total_goals <= 2.2:
            goal_pick = "UNDER 2.5"
        else:
            goal_pick = "BTTS"

    return winner, edge, goal_pick
