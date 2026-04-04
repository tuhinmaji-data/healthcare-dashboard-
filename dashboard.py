import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Basic page config setup
st.set_page_config(
    page_title="UAC Care Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a more premium look
st.markdown("""
<style>
    /* Dark mode / Light mode compatible styles */
    /* Enhance headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
    }
    
    /* Enhance metrics containers */
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 5% 5% 5% 10%;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    /* Make tabs look better */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3.5rem;
        white-space: pre-wrap;
        border-radius: 0.5rem 0.5rem 0 0;
        padding-top: 1rem;
        padding-bottom: 1rem;
        font-weight: 600;
        font-size: 1.05rem;
    }
</style>
""", unsafe_allow_html=True)

# Function to load and clean the dataset
@st.cache_data
def load_data():
    # Load dataset
    df = pd.read_csv("HHS_Unaccompanied_Alien_Children_Program.csv")
    df = df.dropna()

    df.columns = [
        "Date", "CBP_Intake", "CBP_Custody",
        "CBP_Transfers", "HHS_Care", "HHS_Discharges"
    ]

    # Clean HHS_Care column
    df["HHS_Care"] = df["HHS_Care"].astype(str).str.replace(",", "").str.strip()
    df["HHS_Care"] = pd.to_numeric(df["HHS_Care"], errors="coerce")

    # Dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    # Adding some useful date columns for analysis
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Month_Name"] = df["Date"].dt.strftime("%b %Y")
    df["Weekday"] = df["Date"].dt.day_name()
    df["Is_Weekend"] = df["Date"].dt.dayofweek >= 5

    # Calculating metrics for the project
    df["Transfer_Efficiency"] = df["CBP_Transfers"] / df["CBP_Custody"].replace(0, np.nan)
    df["Discharge_Effectiveness"] = df["HHS_Discharges"] / df["HHS_Care"].replace(0, np.nan)
    df["Daily_Backlog"] = df["CBP_Custody"] - df["HHS_Discharges"]
    
    total_out = df["HHS_Discharges"] + df["CBP_Transfers"]
    total_in = df["CBP_Custody"] + df["HHS_Care"]
    df["Pipeline_Throughput"] = total_out / total_in.replace(0, np.nan)

    return df

# Load the data
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e} - Please ensure the CSV is in the same folder.")
    st.stop()

# --- Sidebar configuration ---
with st.sidebar:
    st.title("🧩 Filters & Settings")
    st.markdown("Customize your analysis view:")
    
    st.divider()
    
    # Date filter
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    dates = st.date_input("🗓️ Date Range", value=[min_date, max_date], min_value=min_date, max_value=max_date)

    # Year filter
    years = sorted(df["Year"].unique().tolist())
    selected_years = st.multiselect("📅 Select Year(s)", years, default=years)

    st.divider()
    
    # Slider thresholds for KPI alerts
    st.subheader("🎯 KPI Targets")
    eff_target = st.slider("Transfer Efficiency Target", 0.0, 1.0, 0.70, format="%.2f")
    dis_target = st.slider("Discharge Effectiveness Target", 0.0, 1.0, 0.50, format="%.2f")
    
    st.divider()
    st.caption("UAC Transition Analytics Internship Dashboard v2.0")

# Filter the dataframe based on user input
filtered_df = df.copy()
if len(dates) == 2:
    filtered_df = filtered_df[(filtered_df["Date"].dt.date >= dates[0]) & (filtered_df["Date"].dt.date <= dates[1])]
if selected_years:
    filtered_df = filtered_df[filtered_df["Year"].isin(selected_years)]


# --- Main Dashboard Content ---
st.title("🏥 UAC Care Transition Analytics")
st.markdown("""
<p style="font-size: 1.1rem; color: #6b7280; font-weight: 500;">
Tracking the efficiency and outcomes of the UAC program pipeline. Monitor capacity, identify bottlenecks, and optimize the transition process.
</p>
""", unsafe_allow_html=True)
st.caption(f"Currently showing **{len(filtered_df)}** daily records based on selected filters.")

# Add a top-level metrics row layout
st.markdown("### 🏆 Platform Overview")
m1, m2, m3, m4 = st.columns(4)
with m1:
    avg_cbp = filtered_df["CBP_Custody"].mean()
    st.metric("Avg CBP Custody", f"{avg_cbp:,.0f}")
with m2:
    avg_dis = filtered_df["HHS_Discharges"].mean()
    st.metric("Avg Daily Discharges", f"{avg_dis:,.0f}")
with m3:
    avg_trans_eff = filtered_df["Transfer_Efficiency"].mean()
    trans_delta = (avg_trans_eff - eff_target) * 100
    st.metric("Average Transfer Efficiency", f"{avg_trans_eff:.1%}", delta=f"{trans_delta:+.1f}% vs Target", help="Transfers / CBP Custody")
with m4:
    avg_dis_eff = filtered_df["Discharge_Effectiveness"].mean()
    dis_delta = (avg_dis_eff - dis_target) * 100
    st.metric("Average Discharge Effectiveness", f"{avg_dis_eff:.1%}", delta=f"{dis_delta:+.1f}% vs Target", help="Discharges / HHS Care")

st.divider()

# Create stylized tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Executive Overview", 
    "🌀 Pipeline Flow", 
    "⚡ Efficiency Metrics", 
    "🚨 Bottlenecks & Alerts"
])

# Use common Plotly layout updates (more generic themes)
def update_plotly_layout(fig):
    fig.update_layout(
        font=dict(family="Inter"),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    return fig

# Tab 1: Executive Overview
with tab1:
    st.markdown("### 📊 Custody vs Discharges Over Time")
    
    # Area chart for better visualization
    fig1 = px.area(
        filtered_df, x="Date", y=["CBP_Custody", "HHS_Discharges"],
        color_discrete_sequence=["#ef4444", "#10b981"]
    )
    fig1.update_traces(opacity=0.3)
    fig1 = update_plotly_layout(fig1)
    fig1.update_layout(
        yaxis_title="Number of Children",
        legend_title_text="Metric",
        hovermode="x unified"
    )
    st.plotly_chart(fig1, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.info("💡 **Insight:** Monitoring the gap between CBP Custody (red) and HHS Discharges (green) helps understand real-time capacity stress.")
    with c2:
        if avg_trans_eff < eff_target:
            st.warning(f"⚠️ **Alert:** Transfer Efficiency is currently below target ({eff_target:.1%}).")
        else:
            st.success(f"✅ **Success:** Transfer Efficiency is meeting target.")

# Tab 2: Pipeline Flow
with tab2:
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("### 🌀 Care Pipeline Funnel")
        st.write("Volume reduction across transition stages.")
        fig_funnel = go.Figure(go.Funnel(
            y=["CBP Custody", "CBP Transfers", "HHS Care", "HHS Discharges"],
            x=[
                filtered_df["CBP_Custody"].sum(),
                filtered_df["CBP_Transfers"].sum(),
                filtered_df["HHS_Care"].sum(),
                filtered_df["HHS_Discharges"].sum()
            ],
            textinfo="value+percent initial",
            marker={"color": ["#3b82f6", "#60a5fa", "#8b5cf6", "#a78bfa"]}
        ))
        fig_funnel = update_plotly_layout(fig_funnel)
        st.plotly_chart(fig_funnel, use_container_width=True)
        
    with col2:
        st.markdown("### 📅 Weekday vs Weekend")
        st.write("Average processing volume.")
        wd_df = filtered_df.groupby("Is_Weekend")[["CBP_Transfers", "HHS_Discharges"]].mean().reset_index()
        wd_df["Day Type"] = wd_df["Is_Weekend"].apply(lambda x: "Weekend" if x else "Weekday")
        
        fig2 = px.bar(
            wd_df, x="Day Type", y=["CBP_Transfers", "HHS_Discharges"], 
            barmode="group",
            color_discrete_sequence=["#f59e0b", "#10b981"]
        )
        fig2 = update_plotly_layout(fig2)
        fig2.update_traces(marker_line_width=0)
        fig2.update_layout(
            yaxis_title="Avg Volume",
            legend_title_text="Metric"
        )
        st.plotly_chart(fig2, use_container_width=True)

# Tab 3: Efficiency Metrics
with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚡ Transfer Efficiency Trend")
        fig3 = px.line(
            filtered_df, x="Date", y="Transfer_Efficiency",
            color_discrete_sequence=["#3b82f6"]
        )
        fig3.add_hline(y=eff_target, line_dash="dash", line_color="#ef4444", annotation_text="Target")
        fig3 = update_plotly_layout(fig3)
        fig3.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig3, use_container_width=True)
        
    with col2:
        st.markdown("### 🔋 Discharge Effectiveness Trend")
        fig4 = px.line(
            filtered_df, x="Date", y="Discharge_Effectiveness",
            color_discrete_sequence=["#8b5cf6"]
        )
        fig4.add_hline(y=dis_target, line_dash="dash", line_color="#ef4444", annotation_text="Target")
        fig4 = update_plotly_layout(fig4)
        fig4.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig4, use_container_width=True)
    
    # Monthly Breakdown Table
    st.markdown("### 🗂️ Monthly Summary Data")
    monthly_data = filtered_df.groupby(["Year", "Month", "Month_Name"])[["Transfer_Efficiency", "Discharge_Effectiveness"]].mean().reset_index()
    monthly_data = monthly_data.sort_values(["Year", "Month"])
    
    display_df = monthly_data[["Month_Name", "Transfer_Efficiency", "Discharge_Effectiveness"]].copy()
    
    st.dataframe(
        display_df,
        column_config={
            "Month_Name": st.column_config.TextColumn("Month"),
            "Transfer_Efficiency": st.column_config.ProgressColumn(
                "Avg Transfer Efficiency",
                format="%.2f",
                min_value=0,
                max_value=1,
            ),
            "Discharge_Effectiveness": st.column_config.ProgressColumn(
                "Avg Discharge Effectiveness",
                format="%.2f",
                min_value=0,
                max_value=1,
            ),
        },
        hide_index=True,
        use_container_width=True
    )

# Tab 4: Bottlenecks & Outcome Trends
with tab4:
    st.markdown("### 🚧 System Bottlenecks: Daily Backlog")
    st.write("Difference between CBP Custody and HHS Discharges. Positive values indicate growing backlog.")
    
    colors = ["#ef4444" if b > 0 else "#10b981" for b in filtered_df["Daily_Backlog"]]
    fig5 = go.Figure(go.Bar(
        x=filtered_df["Date"], 
        y=filtered_df["Daily_Backlog"],
        marker_color=colors,
        marker_line_width=0
    ))
    fig5 = update_plotly_layout(fig5)
    st.plotly_chart(fig5, use_container_width=True)
    
    st.markdown("### 📉 Outcome Stability & Drop Detection")
    std_discharges = filtered_df["HHS_Discharges"].std()
    mean_discharges = filtered_df["HHS_Discharges"].mean()
    cv = std_discharges / mean_discharges if mean_discharges > 0 else 0
    
    cc1, cc2 = st.columns(2)
    with cc1:
        st.metric("Std Dev of Discharges", f"{std_discharges:,.1f}", help="Lower means daily processing is consistent")
    with cc2:
        st.metric("Coefficient of Variation", f"{cv:.1%}", help="Lower means outcomes are more stable over time")
    
    st.markdown("#### 🚨 Alerts: Drops in Discharges (>50% Day over Day)")
    
    filtered_df["Prev_Day_Discharges"] = filtered_df["HHS_Discharges"].shift(1)
    drops = filtered_df[
        (filtered_df["Prev_Day_Discharges"] > 0) & 
        (filtered_df["HHS_Discharges"] < filtered_df["Prev_Day_Discharges"] * 0.5)
    ].copy()
    
    if len(drops) > 0:
        st.error(f"Found **{len(drops)} days** where discharges suddenly dropped by over 50%.")
        
        drops["Drop_Percentage"] = (1 - (drops["HHS_Discharges"] / drops["Prev_Day_Discharges"])) * 100
        display_drops = drops[["Date", "Prev_Day_Discharges", "HHS_Discharges", "Drop_Percentage"]]
        display_drops["Date"] = display_drops["Date"].dt.strftime("%Y-%m-%d")
        
        st.dataframe(
            display_drops,
            column_config={
                "Date": "Date",
                "Prev_Day_Discharges": "Previous Day Discharges",
                "HHS_Discharges": "Current Day Discharges",
                "Drop_Percentage": st.column_config.NumberColumn(
                    "Drop Severity",
                    format="%.1f%%"
                )
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("No major sudden drops in discharges detected in this time period.")
