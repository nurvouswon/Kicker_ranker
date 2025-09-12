import pandas as pd
import streamlit as st

st.title("NFL Kicker Ranking Tool")

# --- CSV UPLOADER ---
uploaded_file = st.file_uploader("Upload your kicker CSV", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()  # remove trailing spaces

    # --- SCORING HELPERS ---
    def score_game_total(ou):
        if ou >= 50:
            return 5
        if ou >= 47.5:
            return 4
        if ou >= 45:
            return 3
        if ou >= 42.5:
            return 2
        return 1

    def score_spread(spread):
        if -10 <= spread <= -3:
            return 4
        if -2.5 <= spread < 0:
            return 3
        if spread < -10:
            return 2
        return 1

    def score_weather(weather):
        return {0: 3, 1: 2, 2: 1, 3: 0}.get(weather, 1)

    def score_offense_rank(rank):
        if rank <= 15:
            return 3
        if rank <= 20:
            return 2
        return 1

    def score_rz_eff(rz_eff):
        if rz_eff >= 20:
            return 3
        if rz_eff >= 10:
            return 2
        return 1

    def score_rz_def(rz_def):
        if rz_def >= 20:
            return 3
        if rz_def >= 10:
            return 2
        return 1

    def score_boost(boost_flag):
        if pd.isna(boost_flag) or boost_flag == "":
            return 0
        boost_flag = str(boost_flag).lower()
        if "denver" in boost_flag or "altitude" in boost_flag:
            return 3
        if "division" in boost_flag or "slugfest" in boost_flag:
            return 2
        if "yes" in boost_flag:
            return 2
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
        df = df.sort_values("RuleScore", ascending=False).reset_index(drop=True)
        return df

    # --- Apply scoring ---
    df_ranked = apply_kicker_rules(df)

    # --- Show top 5 ranked kickers ---
    st.subheader("Top 5 Kickers This Week")
    st.dataframe(df_ranked[["Rank","Name","TEAM","RuleScore"]].head(32))

    # --- Save ranked CSV ---
    df_ranked.to_csv("week2_kickers_ranked.csv", index=False)
    st.success("Full ranked CSV saved as week2_kickers_ranked.csv")
