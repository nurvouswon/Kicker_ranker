import pandas as pd
# === Step 1: Load your kicker chart ===
# Save your chart into a CSV file named "week2_kickers.csv"
# Make sure headers match what’s in the chart: 
# ["Rank","ECR","Name","TEAM","Opponent","O/U","Spread","OPP RZ D","RZ EFF","OFF RNK","Consistency","Weather"]
df = pd.read_csv("week2_kickers.csv")

# --- SCORING HELPERS ---
def score_game_total(ou):
    if ou >= 50: return 5
    if ou >= 47.5: return 4
    if ou >= 45: return 3
    return 1

def score_spread(spread):
    # Negative spread = favorite
    if -10 <= spread <= -3: return 4
    if -2.5 <= spread <= 0: return 2
    if spread < -10: return 1  # blowout risk (less FG attempts)
    return 1

def score_weather(weather):
    if weather == 0: return 3  # dome/controlled
    if weather == 1: return 2  # neutral
    if weather == 2: return 1
    if weather == 3: return 0  # bad

def score_offense_rank(rank):
    if rank <= 15: return 3
    if rank <= 20: return 2
    return 1

def score_rz_eff(rz_eff):
    # worse red-zone = more FGs
    if rz_eff >= 20: return 3
    if rz_eff >= 10: return 2
    return 1

def score_rz_def(rz_def):
    if rz_def >= 20: return 3
    if rz_def >= 10: return 2
    return 1

def score_boost(boost_flag):
    # Rule #6 Special boosts
    if pd.isna(boost_flag): return 0
    boost_flag = str(boost_flag).lower()
    if "denver" in boost_flag or "altitude" in boost_flag:
        return 3
    if "division" in boost_flag or "slugfest" in boost_flag:
        return 2
    if "yes" in boost_flag:  # manual flag
        return 2
    return 0

# --- MAIN ---
def apply_kicker_rules(df):
    df["RuleScore"] = (
        df["O/U"].apply(score_game_total)
        + df["Spread"].apply(score_spread)
        + df["Weather"].apply(score_weather)
        + df["OFF RNK"].apply(score_offense_rank)
        + df["RZ EFF*"].apply(score_rz_eff)
        + df["OPP RZ D"].apply(score_rz_def)
        + df["Boost"].apply(score_boost)  # NEW RULE #6
    )
    df = df.sort_values("RuleScore", ascending=False).reset_index(drop=True)
    return df
