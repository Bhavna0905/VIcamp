
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. PATH CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "data" / "processed" / "voice_analytics.db"
VALIDATION_PATH = (
    BASE_DIR / "data" / "processed" / "outcome_validation_report.csv"
)
LOADER_SCRIPT = BASE_DIR / "scripts" / "load_database.py"


# --------------------------------------------------
# 2. STREAMLIT PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="VIcamp | Voice AI Campaign Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 VIcamp — Voice AI Campaign Analytics")
st.caption(
    "Monitor campaign performance, call outcomes, "
    "and data quality."
)


# --------------------------------------------------
# 3. AUTOMATIC DATABASE CREATION
# --------------------------------------------------

def ensure_database():
    """
    Create the SQLite database from raw CSV files
    if the database does not already exist.
    """

    if DB_PATH.exists():
        return

    st.info("Database not found. Creating it from raw CSV files...")

    try:
        result = subprocess.run(
            [sys.executable, str(LOADER_SCRIPT)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=True
        )

        if not DB_PATH.exists():
            st.error("Database creation did not produce the expected file.")
            if result.stdout:
                st.code(result.stdout)
            if result.stderr:
                st.code(result.stderr)
            st.stop()

        st.success("Database created successfully!")

    except subprocess.CalledProcessError as error:
        st.error("Could not create the database.")

        if error.stdout:
            st.code(error.stdout)

        if error.stderr:
            st.code(error.stderr)

        st.stop()

    except Exception as error:
        st.error(f"Unexpected database error: {error}")
        st.stop()


ensure_database()


# --------------------------------------------------
# 4. LOAD DATABASE AND VALIDATION REPORT
# --------------------------------------------------

@st.cache_data
def load_data():

    if not DB_PATH.exists():
        return pd.DataFrame(), pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)

    try:
        query = """
            SELECT
                l.lead_id,
                l.customer_name,
                l.campaign,
                l.city,
                c.call_id,
                c.status,
                c.outcome,
                c.duration_sec,
                c.transcript
            FROM leads l
            LEFT JOIN calls c
                ON l.lead_id = c.lead_id
        """

        df = pd.read_sql_query(query, conn)

    finally:
        conn.close()

    if VALIDATION_PATH.exists():
        validation_df = pd.read_csv(VALIDATION_PATH)
    else:
        validation_df = pd.DataFrame()

    return df, validation_df


df, validation_df = load_data()

if df.empty:
    st.error(
        "No data available. Please check your raw CSV files "
        "and database loading script."
    )
    st.stop()


# --------------------------------------------------
# 5. SIDEBAR FILTER
# --------------------------------------------------

st.sidebar.header("Filters")

campaigns = ["All"] + sorted(
    df["campaign"].dropna().unique().tolist()
)

selected_campaign = st.sidebar.selectbox(
    "Select Campaign",
    campaigns
)

if selected_campaign != "All":
    filtered_df = df[df["campaign"] == selected_campaign].copy()
else:
    filtered_df = df.copy()


# --------------------------------------------------
# 6. KPI CALCULATIONS
# --------------------------------------------------

total_leads = filtered_df["lead_id"].nunique()

calls_df = filtered_df.dropna(subset=["call_id"]).copy()

total_calls = calls_df["call_id"].nunique()

connected_calls = calls_df[
    calls_df["status"].str.lower() == "connected"
]["call_id"].nunique()

converted_customers = calls_df[
    calls_df["outcome"].str.lower() == "converted"
]["lead_id"].nunique()

connection_rate = (
    connected_calls / total_calls * 100
    if total_calls > 0 else 0
)

conversion_rate = (
    converted_customers / total_leads * 100
    if total_leads > 0 else 0
)


# --------------------------------------------------
# 7. KPI DISPLAY
# --------------------------------------------------

st.subheader("Campaign Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Leads", total_leads)
col2.metric("Total Calls", total_calls)
col3.metric("Connected Calls", connected_calls)

col4, col5, col6 = st.columns(3)

col4.metric("Converted Customers", converted_customers)
col5.metric("Connection Rate", f"{connection_rate:.2f}%")
col6.metric("Lead Conversion Rate", f"{conversion_rate:.2f}%")


st.divider()


# --------------------------------------------------
# 8. CAMPAIGN-WISE SUMMARY
# --------------------------------------------------

st.subheader("Campaign Performance")

campaign_summary = (
    filtered_df.groupby("campaign")
    .agg(
        total_leads=("lead_id", "nunique"),
        total_calls=("call_id", "nunique"),
        connected_calls=(
            "status",
            lambda x: (
                x.str.lower() == "connected"
            ).sum()
        ),
        converted_customers=(
            "outcome",
            lambda x: (
                x.str.lower() == "converted"
            ).sum()
        )
    )
    .reset_index()
)

campaign_summary["connection_rate_pct"] = (
    campaign_summary["connected_calls"]
    / campaign_summary["total_calls"].replace(0, pd.NA)
    * 100
).fillna(0).round(2)

campaign_summary["lead_conversion_rate_pct"] = (
    campaign_summary["converted_customers"]
    / campaign_summary["total_leads"].replace(0, pd.NA)
    * 100
).fillna(0).round(2)


# --------------------------------------------------
# 9. CAMPAIGN CHARTS
# --------------------------------------------------

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("#### Leads by Campaign")

    leads_chart = px.bar(
        campaign_summary,
        x="campaign",
        y="total_leads",
        color="campaign",
        text="total_leads",
        labels={
            "campaign": "Campaign",
            "total_leads": "Total Leads"
        }
    )

    leads_chart.update_layout(
        showlegend=False,
        xaxis_title="Campaign",
        yaxis_title="Number of Leads"
    )

    st.plotly_chart(leads_chart, use_container_width=True)


with chart_col2:
    st.markdown("#### Connection vs Conversion Rate")

    rate_data = campaign_summary.melt(
        id_vars="campaign",
        value_vars=[
            "connection_rate_pct",
            "lead_conversion_rate_pct"
        ],
        var_name="metric",
        value_name="rate"
    )

    rate_data["metric"] = rate_data["metric"].map({
        "connection_rate_pct": "Connection Rate",
        "lead_conversion_rate_pct": "Conversion Rate"
    })

    rate_chart = px.bar(
        rate_data,
        x="campaign",
        y="rate",
        color="metric",
        barmode="group",
        text="rate",
        labels={
            "campaign": "Campaign",
            "rate": "Rate (%)",
            "metric": "Metric"
        }
    )

    rate_chart.update_layout(
        yaxis_title="Rate (%)",
        xaxis_title="Campaign"
    )

    st.plotly_chart(rate_chart, use_container_width=True)


st.markdown("#### Campaign Summary Table")

st.dataframe(
    campaign_summary,
    use_container_width=True,
    hide_index=True
)


st.divider()


# --------------------------------------------------
# 10. CALL OUTCOME DISTRIBUTION
# --------------------------------------------------

st.subheader("Call Outcome Analysis")

outcome_df = calls_df.dropna(subset=["outcome"]).copy()

if not outcome_df.empty:

    outcome_counts = (
        outcome_df["outcome"]
        .value_counts()
        .reset_index()
    )

    outcome_counts.columns = ["outcome", "count"]

    outcome_chart = px.pie(
        outcome_counts,
        names="outcome",
        values="count",
        hole=0.4,
        title="Distribution of Call Outcomes"
    )

    st.plotly_chart(
        outcome_chart,
        use_container_width=True
    )

else:
    st.info("No call outcome data available.")


# --------------------------------------------------
# 11. CALL DURATION ANALYSIS
# --------------------------------------------------

st.subheader("Call Duration Analysis")

duration_df = calls_df.dropna(
    subset=["duration_sec", "status"]
).copy()

if not duration_df.empty:

    duration_chart = px.histogram(
        duration_df,
        x="duration_sec",
        color="status",
        nbins=20,
        title="Call Duration Distribution",
        labels={
            "duration_sec": "Duration (seconds)",
            "status": "Call Status"
        }
    )

    st.plotly_chart(
        duration_chart,
        use_container_width=True
    )

else:
    st.info("No call duration data available.")


st.divider()


# --------------------------------------------------
# 12. DATA QUALITY AND OUTCOME VALIDATION
# --------------------------------------------------

st.subheader("Data Quality & Outcome Validation")

if not validation_df.empty:

    if "call_id" in validation_df.columns:

        selected_call_ids = calls_df["call_id"].dropna().unique()

        filtered_validation = validation_df[
            validation_df["call_id"].isin(selected_call_ids)
        ].copy()

    else:
        filtered_validation = validation_df.copy()

    if "validation_status" in filtered_validation.columns:

        validation_counts = (
            filtered_validation["validation_status"]
            .value_counts()
        )

        ok_count = validation_counts.get("OK", 0)
        mismatch_count = validation_counts.get("MISMATCH", 0)
        review_count = validation_counts.get("REVIEW", 0)

        vcol1, vcol2, vcol3 = st.columns(3)

        vcol1.metric("Valid Records", int(ok_count))
        vcol2.metric("Mismatches", int(mismatch_count))
        vcol3.metric("Needs Review", int(review_count))

    st.markdown("#### Validation Report")

    st.dataframe(
        filtered_validation,
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning(
        "Outcome validation report not found. "
        "Run python scripts/outcome_validation.py"
    )


# --------------------------------------------------
# 13. RAW CALL DATA
# --------------------------------------------------

st.divider()

with st.expander("View Raw Call Data"):

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 14. FOOTER
# --------------------------------------------------

st.caption(
    "VIcamp | Voice AI Campaign Analytics "
    "• Built using Python, Pandas, SQLite, Streamlit and Plotly"
)
