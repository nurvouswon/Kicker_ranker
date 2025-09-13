import pandas as pd
import streamlit as st

st.title("NFL Kicker Ranking & Projection Tool")

# --- CSV UPLOAD ---
current_file = st.file_uploader("Upload this week's kicker CSV", type=["csv"])
historical_file = st.file_uploader("Optional: Upload previous weeks CSV with OutcomePoints", type=["csv"])

# --- Base Scoring Values ---
XP_POINTS = 1
FG_0_39 = 3
FG_40_49 = 4
FG_50_PLUS = 5

# --- Boost mapping ---
BOOST_VALUES = {
    "denver": 1.0,      # altitude boost
    "altitude": 1.0,
    "division": 0.5,    # divisional boost
    "slugfest": 0.5,
    "yes": 0.5
}

def compute_boost_numeric(boost_label):
    if pd.isna(boost_label) or boost_label == "":
        return 0.0
    boost_label = str(boost_label).lower()
    value = 0.0
    for key, val in BOOST_VALUES.items():
        if key in boost_label:
            value += val
    return value

def project_fantasy_points(row, historical_avg=None):
    # baseline assumptions if historical data is not provided
    xp_attempts = row.get("XP_Attempts", 2)
    fg_0_39_attempts = row.get("FG_0_39", 2)
    fg_40_49_attempts = row.get("FG_40_49", 1)
    fg_50_plus_attempts = row.get("FG_50_plus", 0.5)

    # apply boost multiplier (increase attempts proportionally)
    boost_multiplier = 1 + compute_boost_numeric(row.get("Boost", ""))
    xp_attempts *= boost_multiplier
    fg_0_39_attempts *= boost_multiplier
    fg_40_49_attempts *= boost_multiplier
    fg_50_plus_attempts *= boost_multiplier

    proj_points = (
        xp_attempts * XP_POINTS +
        fg_0_39_attempts * FG_0_39 +
        fg_40_49_attempts * FG_40_49 +
        fg_50_plus_attempts * FG_50_PLUS
    )

    # if historical average provided, blend 70/30 with projection
    if historical_avg is not None:
        proj_points = 0.7 * proj_points + 0.3 * historical_avg

    return round(proj_points, 1)

if current_file is not None:
    df = pd.read_csv(current_file)
    df.columns = df.columns.str.strip()

    # compute numeric boost
    df["Boost_Num"] = df["Boost"].apply(compute_boost_numeric)

    # --- historical average points if historical file uploaded ---
    historical_avg_map = {}
    if historical_file is not None:
        hist_df = pd.read_csv(historical_file)
        hist_df.columns = hist_df.columns.str.strip()
        historical_avg_map = hist_df.groupby("Name")["OutcomePoints"].mean().to_dict()

    # --- Project Fantasy Points ---
    proj_points_list = []
    for _, row in df.iterrows():
        hist_avg = historical_avg_map.get(row["Name"], None)
        proj_points_list.append(project_fantasy_points(row, hist_avg))
    df["ProjPoints"] = proj_points_list

    # --- Show full kicker table with projections ---
    st.subheader("Kicker Projections for This Week")
    st.dataframe(df[["Rank","Name","TEAM","Opponent","O/U","Spread","Boost","Boost_Num","ProjPoints"]])

    # --- Save CSV ---
    df.to_csv("kicker_projections_week.csv", index=False)
    st.success("CSV with projections saved as kicker_projections_week.csv")
