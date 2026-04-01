# 🔥 TROCAR APENAS ESSAS PARTES

MIN_MATCHES = 5  # mais flexível

# -------------------------
# CONSISTÊNCIA (CORRIGIDO)
# -------------------------
def check_min_matches(standings):
    try:
        games = standings[0].get("matches", 0)
        return games >= MIN_MATCHES
    except:
        return False

# -------------------------
# SCORE (CORRIGIDO)
# -------------------------
def calculate_score(event):

    home_id = event["homeTeam"]["id"]
    away_id = event["awayTeam"]["id"]

    league_id = event["tournament"]["uniqueTournament"]["id"]
    season_id = event["season"]["id"]

    standings = get_standings(league_id, season_id)

    # 🔥 NÃO BLOQUEIA MAIS
    valid_table = standings and check_min_matches(standings)

    hf = calculate_form(home_id)
    af = calculate_form(away_id)

    hxg, hs = calculate_averages(home_id)
    axg, as_ = calculate_averages(away_id)

    home_strength = calculate_home_strength(home_id)

    league_weight = calculate_league_strength(league_id)

    # 🔥 MOTIVAÇÃO SÓ SE TIVER DADOS
    if valid_table:
        motivation_home = calculate_motivation(home_id, standings)
        motivation_away = calculate_motivation(away_id, standings)
    else:
        motivation_home = 0.5
        motivation_away = 0.5

    lineup_home = estimate_lineup_impact(home_id)
    lineup_away = estimate_lineup_impact(away_id)

    score = (
        (hf - af) * 1.5 +
        (hxg - axg) * 1.2 +
        ((hs - as_) * 0.05) +
        home_strength +
        ((motivation_home - motivation_away) * 0.4) +
        (lineup_home - lineup_away)
    )

    # 🔥 PESO SUAVE (não trava edge)
    score = score * (0.8 + (league_weight * 0.2))

    return score
