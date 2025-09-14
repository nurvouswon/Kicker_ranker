import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor

st.title("NFL Kicker Ranking Tool with Granular Scoring & Projected Points")

# --- CSV UPLOADER ---
uploaded_file = st.file_uploader("Upload this week's kicker CSV", type=["csv"])
previous_file = st.file_uploader("Optional: Upload previous week(s) CSV with Actual_Points", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()  # remove trailing spaces

    # --- GRANULAR SCORING HELPERS ---
    def score_game_total(ou):
        # 42-43.9: 1, 44-44.9: 2, 45-45.9: 3, 46-47.4: 3.5, 47.5-49.9: 4, 50+: 5
        if ou >= 50: return 5
        if ou >= 47.5: return 4
        if ou >= 46: return 3.5
        if ou >= 45: return 3
        if ou >= 44: return 2
        return 1

    def score_spread(spread):
        # heavy favorites -10 or less: 4, moderate favorites -9 to -3: 3.5
        # slight favorite -2.5 to 0 or slight underdog 0-3: 3, heavy underdog >3: 2
        if spread <= -10: return 4
        if -9 <= spread <= -3: return 3.5
        if -2.5 <= spread <= 3: return 3
        return 2

    def score_weather(weather):
        # 0=perfect, 1=good, 2=neutral, 3=bad
        return {0: 3, 1: 2, 2: 1, 3: 0}.get(weather, 1)

    def score_offense_rank(rank):
        # 1-10: 3, 11-20: 2, 21-32:1
        if rank <= 10: return 3
        if rank <= 20: return 2
        return 1

    def score_rz_eff(rz_eff):
        # higher number = better scoring opportunity for kicker
        if rz_eff >= 25: return 3
        if rz_eff >= 15: return 2
        return 1

    def score_rz_def(rz_def):
        # higher number = weaker defense = more FG opportunities
        if rz_def >= 25: return 3
        if rz_def >= 15: return 2
        return 1

    def score_boost(boost_flag):
        if pd.isna(boost_flag) or boost_flag == "": return 0
        boost_flag = str(boost_flag).lower()
        if "denver" in boost_flag or "altitude" in boost_flag: return 3
        if "division" in boost_flag or "slugfest" in boost_flag: return 2
        if "yes" in boost_flag: return 2
        return 0

    def tie_breaker(row):
        tie_adjust = 0
        tie_adjust += (row["O/U"] - 40) / 15 * 0.5
        boost_flag = str(row.get("Boost", "")).lower()
        if "denver" in boost_flag or "altitude" in boost_flag:
            tie_adjust += 0.3
        elif "division" in boost_flag or "slugfest" in boost_flag:
            tie_adjust += 0.2
        elif "yes" in boost_flag:
            tie_adjust += 0.2
        return tie_adjust

    # --- MAIN SCORING FUNCTION ---
    def apply_kicker_rules(df):
        df["RuleScore"] = (
            df["O/U"].apply(score_game_total) * 1.5
            + df["Spread"].apply(score_spread) * 1
            + df["Weather"].apply(score_weather) * 0.5
            + df["OFF RNK"].apply(score_offense_rank) * 1
            + df["RZ EFF*"].apply(score_rz_eff) * 2
            + df["OPP RZ D"].apply(score_rz_def) * 2
            + df["Boost"].apply(score_boost) * 0.5
        )
        df["RuleScore"] += df.apply(tie_breaker, axis=1)
        return df.sort_values("RuleScore", ascending=False).reset_index(drop=True)

    # --- Apply scoring ---
    df_ranked = apply_kicker_rules(df)

    # --- Convert Boost to numerical for ML ---
    df_ranked["Boost_Num"] = df_ranked["Boost"].apply(score_boost)

    # --- PROJECTED FANTASY POINTS ---
    features = ["O/U", "Spread", "OFF RNK", "RZ EFF*", "OPP RZ D", "Weather", "Boost_Num"]

    if previous_file is not None:
        df_hist = pd.read_csv(previous_file)
        df_hist.columns = df_hist.columns.str.strip()
        X_hist = df_hist[features]
        y_hist = df_hist["Actual_Points"]

        # Train a Random Forest Regressor
        model = RandomForestRegressor(n_estimators=200, random_state=42)
        model.fit(X_hist, y_hist)

        df_ranked["Projected_Points"] = model.predict(df_ranked[features])
    else:
        # fallback: scale RuleScore for projection
        df_ranked["Projected_Points"] = df_ranked["RuleScore"] / df_ranked["RuleScore"].max() * 10

    # --- Show top 32 ranked kickers ---
    st.subheader("Ranked Kickers with Granular Scoring & Projected Points")
    st.dataframe(df_ranked[["Rank","Name","TEAM","RuleScore","Boost_Num","Projected_Points"]].head(32))

    # --- Save ranked CSV ---
    df_ranked.to_csv("week_ranked_kickers.csv", index=False)
    st.success("Full ranked CSV saved as week_ranked_kickers.csv")
