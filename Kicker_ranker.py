import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression
import numpy as np

st.title("🏈 NFL Kicker Ranking & Projection Tool")

# --- CSV UPLOADER ---
uploaded_file = st.file_uploader("Upload this week's kicker CSV", type=["csv"])
history_file = st.file_uploader("Optional: Upload previous weeks with 'score_outcome' column", type=["csv"])

# --- SCORING HELPERS ---
def score_game_total(ou):
    if ou >= 52: return 5
    if ou >= 49: return 4
    if ou >= 46: return 3
    if ou >= 43: return 2
    return 1

def score_spread(spread):
    if -14 <= spread <= -7: return 5
    if -6.5 <= spread <= -3: return 4
    if -2.5 <= spread <= 3: return 3
    if 3.5 <= spread <= 7: return 2
    return 1

def score_weather(weather):
    return {0: 3, 1: 2, 2: 1, 3: 0}.get(weather, 1)

def score_offense_rank(rank):
    if rank <= 10: return 4
    if rank <= 15: return 3
    if rank <= 20: return 2
    return 1

def score_rz_eff(rz_eff):
    if rz_eff >= 25: return 4
    if rz_eff >= 20: return 3
    if rz_eff >= 15: return 2
    return 1

def score_rz_def(rz_def):
    if rz_def >= 25: return 4
    if rz_def >= 20: return 3
    if rz_def >= 15: return 2
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
        return 1
    return 0

# --- Granular Fantasy Point Projection ---
def projected_points(row):
    base_attempts = max(1, (row["RuleScore"]/10 + row["O/U"]/50 + row["RZ EFF*"]/20))
    
    xp_attempts = max(0.5, min(base_attempts*0.5, row["RZ EFF*"]/10))
    fg_1_39 = max(0, base_attempts*0.3)
    fg_40_49 = max(0, base_attempts*0.2)
    fg_50p  = max(0, base_attempts*0.1 + 0.05*row["Boost_Num"])
    
    points = xp_attempts*1 + fg_1_39*3 + fg_40_49*4 + fg_50p*5
    return round(points, 1)

# --- MAIN SCORING FUNCTION ---
def apply_kicker_rules(df):
    df["Boost_Num"] = df["Boost"].apply(score_boost)
    df["RuleScore"] = (
        df["O/U"].apply(score_game_total) * 1.5
        + df["Spread"].apply(score_spread) * 1.2
        + df["Weather"].apply(score_weather) * 0.5
        + df["OFF RNK"].apply(score_offense_rank) * 1
        + df["RZ EFF*"].apply(score_rz_eff) * 2
        + df["OPP RZ D"].apply(score_rz_def) * 2
        + df["Boost_Num"] * 0.5
    )
    df["ProjPoints"] = df.apply(projected_points, axis=1)
    df = df.sort_values("ProjPoints", ascending=False).reset_index(drop=True)
    return df

# --- MAIN APP LOGIC ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    df_ranked = apply_kicker_rules(df)

    st.subheader("📊 Ranked Kickers with Projected Points")
    st.dataframe(df_ranked[["Rank","Name","TEAM","Opponent","RuleScore","ProjPoints","Boost","Boost_Num"]])

    df_ranked.to_csv("week_kickers_ranked.csv", index=False)
    st.success("✅ Full ranked CSV saved as week_kickers_ranked.csv")

    # --- Optional ML projection using score_outcome ---
    if history_file is not None:
        hist = pd.read_csv(history_file)
        hist = hist.dropna(subset=["score_outcome"])
        
        features = ["RuleScore", "Boost_Num", "O/U", "Spread", "RZ EFF*", "OPP RZ D", "OFF RNK"]
        X_train = hist[features]
        y_train = hist["score_outcome"]
        
        # Handle single-row historical data gracefully with tiny smoothing
        if len(hist) < 2:
            st.warning("⚠️ Only one historical row provided. ML prediction will be smoothed for realism.")
            base_pred = float(y_train.iloc[0])
            df_ranked["ML_Pred"] = df_ranked["ProjPoints"] * 0.3 + base_pred * 0.7
            df_ranked["ML_Pred"] = df_ranked["ML_Pred"].round(1)
        else:
            model = LinearRegression()
            model.fit(X_train, y_train)
            df_ranked["ML_Pred"] = model.predict(df_ranked[features]).round(1)
        
        st.subheader("🤖 ML-Enhanced Projections (if history provided)")
        st.dataframe(df_ranked[["Name","TEAM","ProjPoints","ML_Pred"]])
