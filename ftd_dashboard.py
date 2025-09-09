
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="FTD Acquisition Dashboard", layout="wide")

st.title("FTD Acquisition Dashboard")
st.caption("Monthly client acquisition by source (campaign / IB), anchored on **portal - ftd_time**. Dates parsed as **DD/MM/YYYY**.")

# --- Load data ---
uploaded = st.file_uploader("Upload CSV (must include 'portal - ftd_time' and 'portal - source_marketing_campaign')", type=["csv"])

@st.cache_data(show_spinner=False)
def load_df(file):
    df = pd.read_csv(file)
    # Expected columns
    date_col = "portal - ftd_time"
    source_col = "portal - source_marketing_campaign"
    if date_col not in df.columns or source_col not in df.columns:
        raise ValueError(f"CSV is missing required columns: '{date_col}' and '{source_col}'. Found: {list(df.columns)}")
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    df[source_col] = df[source_col].fillna("(Unknown)").astype(str).str.strip()
    df = df.dropna(subset=[date_col]).copy()
    df["ftd_month"] = df[date_col].dt.to_period("M").dt.to_timestamp()
    return df

if uploaded is not None:
    try:
        df = load_df(uploaded)
    except Exception as e:
        st.error(str(e))
        st.stop()
else:
    # Fallback: try to load a local file named source.csv if present
    try:
        df = load_df("source.csv")
        st.info("Using local 'source.csv' found in the same folder (since you didn't upload a file here).")
    except Exception:
        st.warning("Please upload your CSV to proceed.")
        st.stop()

# Data Quality Check
with st.expander("📊 Data Quality Report", expanded=False):
    date_col = "portal - ftd_time"
    source_col = "portal - source_marketing_campaign"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Records", f"{len(df):,}")
        invalid_dates = df[date_col].isna().sum()
        if invalid_dates > 0:
            st.warning(f"⚠️ {invalid_dates} records with invalid dates")
        else:
            st.success("✅ All dates valid")
    
    with col2:
        st.metric("Date Range", f"{df['ftd_month'].min():%b %Y} - {df['ftd_month'].max():%b %Y}")
        unknown_sources = (df[source_col] == "(Unknown)").sum()
        if unknown_sources > 0:
            st.warning(f"⚠️ {unknown_sources} records with unknown source")
        else:
            st.success("✅ All sources identified")
    
    with col3:
        st.metric("Unique Sources", f"{df[source_col].nunique()}")
        # Check for data gaps
        expected_months = pd.period_range(df['ftd_month'].min(), df['ftd_month'].max(), freq='M')
        actual_months = df['ftd_month'].dt.to_period('M').unique()
        missing_months = len(expected_months) - len(actual_months)
        if missing_months > 0:
            st.warning(f"⚠️ {missing_months} months with no data")
        else:
            st.success("✅ No gaps in data")

# --- Sidebar filters ---
with st.sidebar:
    st.header("Filters")
    # Source selection
    source_col = "portal - source_marketing_campaign"
    totals = df.groupby(source_col, dropna=False)["Record ID"].size().sort_values(ascending=False)
    all_sources = totals.index.tolist()
    
    st.subheader("Source Selection")
    
    # Search box
    search_term = st.text_input("🔍 Search sources", placeholder="Type to filter...")
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Select All", use_container_width=True):
            st.session_state.selected_sources = all_sources.copy()
    with col2:
        if st.button("Clear All", use_container_width=True):
            st.session_state.selected_sources = []
    with col3:
        top_n = st.number_input("Top N", min_value=1, max_value=max(1, len(all_sources)), value=min(10, len(all_sources)), label_visibility="collapsed")
        if st.button(f"Top {top_n}", use_container_width=True):
            st.session_state.selected_sources = all_sources[:top_n]
    
    # Initialize session state if not exists
    if "selected_sources" not in st.session_state:
        st.session_state.selected_sources = all_sources[:min(5, len(all_sources))]
    
    # Filter sources based on search
    filtered_sources = [s for s in all_sources if search_term.lower() in s.lower()]
    
    # Display count
    st.caption(f"Showing {len(filtered_sources)} of {len(all_sources)} sources | {len(st.session_state.selected_sources)} selected")
    
    # Scrollable container with checkboxes
    st.markdown("---")
    container = st.container(height=300)  # Fixed height for scrolling
    
    with container:
        for source in filtered_sources:
            count = totals[source]
            is_selected = source in st.session_state.selected_sources
            
            # Create checkbox with source name and count
            new_state = st.checkbox(
                f"{source} ({count:,} clients)",
                value=is_selected,
                key=f"checkbox_{source}"
            )
            
            # Update session state based on checkbox
            if new_state and source not in st.session_state.selected_sources:
                st.session_state.selected_sources.append(source)
            elif not new_state and source in st.session_state.selected_sources:
                st.session_state.selected_sources.remove(source)
    
    selected_sources = st.session_state.selected_sources
    
    st.markdown("---")
    st.subheader("Date Range")
    
    # Month range
    min_m, max_m = df["ftd_month"].min(), df["ftd_month"].max()
    
    # Quick date range buttons
    st.caption("Quick select:")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Last 3M", use_container_width=True):
            st.session_state.date_range = (max_m - pd.DateOffset(months=2), max_m)
    with col2:
        if st.button("Last 6M", use_container_width=True):
            st.session_state.date_range = (max_m - pd.DateOffset(months=5), max_m)
    with col3:
        if st.button("Last 12M", use_container_width=True):
            st.session_state.date_range = (max_m - pd.DateOffset(months=11), max_m)
    with col4:
        if st.button("YTD", use_container_width=True):
            ytd_start = pd.Timestamp(max_m.year, 1, 1)
            st.session_state.date_range = (ytd_start, max_m)
    
    # Initialize date range if not in session state
    if "date_range" not in st.session_state:
        st.session_state.date_range = (min_m.to_pydatetime(), max_m.to_pydatetime())
    
    start, end = st.slider(
        "Month range",
        min_value=min_m.to_pydatetime(),
        max_value=max_m.to_pydatetime(),
        value=st.session_state.date_range,
        format="MMM YYYY",
        key="date_slider"
    )

    chart_type = st.radio("Chart type", ["Line", "Stacked bars"], horizontal=True)

# Apply filters
mask_time = (df["ftd_month"] >= pd.Timestamp(start)) & (df["ftd_month"] <= pd.Timestamp(end))
mask_source = df[source_col].isin(selected_sources) if selected_sources else pd.Series(True, index=df.index)
dff = df.loc[mask_time & mask_source].copy()

# Aggregate
counts = (
    dff.groupby(["ftd_month", source_col])["Record ID"].size().reset_index(name="clients")
)
months = pd.period_range(dff["ftd_month"].min(), dff["ftd_month"].max(), freq="M").to_timestamp()
# Ensure all (month, source) combos exist for proper stacking/lines
full = (
    pd.MultiIndex.from_product([months, selected_sources], names=["ftd_month", source_col])
    .to_frame(index=False)
)
counts = (
    full.merge(counts, on=["ftd_month", source_col], how="left")
    .fillna({"clients": 0})
)

# KPI row
total_clients = int(counts["clients"].sum())
span_months = len(months)
avg_monthly = total_clients / span_months if span_months > 0 else 0

st.markdown("### Overview")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Clients", f"{total_clients:,}")
k2.metric("Avg/Month", f"{avg_monthly:.0f}")
k3.metric("Sources", f"{len(selected_sources)} / {len(all_sources)}")
k4.metric("Period", f"{span_months} months")

# Performance Metrics
if len(counts) > 0 and span_months > 1:
    st.markdown("### Performance Metrics")
    
    # Calculate month-over-month growth
    monthly_totals = counts.groupby("ftd_month")["clients"].sum().reset_index()
    monthly_totals["mom_growth"] = monthly_totals["clients"].pct_change() * 100
    
    # Calculate metrics
    latest_month = monthly_totals.iloc[-1]["clients"] if len(monthly_totals) > 0 else 0
    prev_month = monthly_totals.iloc[-2]["clients"] if len(monthly_totals) > 1 else 0
    mom_change = ((latest_month - prev_month) / prev_month * 100) if prev_month > 0 else 0
    
    best_month = monthly_totals.loc[monthly_totals["clients"].idxmax()]
    worst_month = monthly_totals.loc[monthly_totals["clients"].idxmin()]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Latest Month", 
        f"{latest_month:.0f} clients",
        f"{mom_change:+.1f}%" if mom_change != 0 else "0%"
    )
    m2.metric(
        "Best Month", 
        f"{best_month['clients']:.0f} clients",
        f"{best_month['ftd_month']:%b %Y}"
    )
    m3.metric(
        "Worst Month", 
        f"{worst_month['clients']:.0f} clients",
        f"{worst_month['ftd_month']:%b %Y}"
    )
    m4.metric(
        "Avg Growth",
        f"{monthly_totals['mom_growth'].mean():.1f}%",
        "month-over-month"
    )

# Chart
import altair as alt

alt.data_transformers.disable_max_rows()

chart_base = alt.Chart(counts).encode(
    x=alt.X("ftd_month:T", 
            axis=alt.Axis(title="Month", format="%b %Y"),
            scale=alt.Scale(padding=20)),
    y=alt.Y("clients:Q", 
            axis=alt.Axis(title="Clients"), 
            stack=None if chart_type == "Line" else "zero"),
    color=alt.Color(f"{source_col}:N", 
                   legend=alt.Legend(title="Source")),
    tooltip=[
        alt.Tooltip("ftd_month:T", title="Month", format="%B %Y"),
        alt.Tooltip(f"{source_col}:N", title="Source"),
        alt.Tooltip("clients:Q", title="Clients", format=",.0f")
    ]
)

if chart_type == "Line":
    # Create line with visible points for better hover experience
    line = chart_base.mark_line(strokeWidth=2, opacity=0.8)
    points = chart_base.mark_circle(size=50, opacity=1)
    
    # Add hover selection for highlighting
    hover = alt.selection_point(
        fields=["ftd_month"], 
        nearest=True, 
        on="mouseover",
        empty=False
    )
    
    # Create a vertical rule at hover position
    rules = alt.Chart(counts).mark_rule(color="gray", strokeDash=[3, 3], opacity=0.5).encode(
        x="ftd_month:T"
    ).transform_filter(hover)
    
    # Update points to be larger when hovered
    points = points.add_params(hover).encode(
        size=alt.condition(hover, alt.value(100), alt.value(50))
    )
    
    chart = line + points + rules
else:
    # Add hover effect for bars
    hover = alt.selection_point(on="mouseover", empty=False)
    chart = chart_base.mark_bar(opacity=0.9).add_params(hover).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0.7))
    )

st.markdown("### Monthly acquisition by source")
st.altair_chart(chart.properties(height=380).interactive(), use_container_width=True)

# Pivot table
st.markdown("### Table: counts by month")
pivot = counts.pivot_table(index="ftd_month", columns=source_col, values="clients", fill_value=0).sort_index()
st.dataframe(pivot, width="stretch")

# Source Performance Ranking
if len(selected_sources) > 0:
    st.markdown("### Source Performance Ranking")
    
    # Calculate source statistics
    source_stats = []
    for source in selected_sources:
        source_data = counts[counts[source_col] == source]
        total = source_data["clients"].sum()
        avg = source_data["clients"].mean()
        max_val = source_data["clients"].max()
        min_val = source_data["clients"].min()
        
        # Calculate trend (simple linear regression slope)
        if len(source_data) > 1:
            from scipy import stats
            x = np.arange(len(source_data))
            y = source_data["clients"].values
            slope, _, _, _, _ = stats.linregress(x, y)
            trend = "📈" if slope > 0.5 else "📉" if slope < -0.5 else "➡️"
        else:
            trend = "➡️"
        
        source_stats.append({
            "Source": source,
            "Total Clients": int(total),
            "Avg/Month": f"{avg:.1f}",
            "Best Month": int(max_val),
            "Worst Month": int(min_val),
            "Trend": trend
        })
    
    source_df = pd.DataFrame(source_stats).sort_values("Total Clients", ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption("🏆 **Top Performers**")
        top_5 = source_df.head(5)
        st.dataframe(top_5, hide_index=True, width="stretch")
    
    with col2:
        if len(source_df) > 5:
            st.caption("⚠️ **Bottom Performers**")
            bottom_5 = source_df.tail(5).sort_values("Total Clients", ascending=True)
            st.dataframe(bottom_5, hide_index=True, width="stretch")

# Download section with multiple formats
st.markdown("### Export Data")
col1, col2, col3 = st.columns(3)

with col1:
    # CSV download
    csv_bytes = pivot.reset_index().to_csv(index=False).encode("utf-8")
    st.download_button(
        "📄 Download CSV", 
        data=csv_bytes, 
        file_name=f"ftd_by_source_{pd.Timestamp.now():%Y%m%d}.csv", 
        mime="text/csv",
        use_container_width=True
    )

with col2:
    # Excel download
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        pivot.reset_index().to_excel(writer, sheet_name='Monthly Data', index=False)
        if len(selected_sources) > 0:
            source_df.to_excel(writer, sheet_name='Source Rankings', index=False)
    excel_bytes = buffer.getvalue()
    st.download_button(
        "📊 Download Excel",
        data=excel_bytes,
        file_name=f"ftd_analysis_{pd.Timestamp.now():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col3:
    # JSON download
    import json
    json_data = {
        "summary": {
            "total_clients": total_clients,
            "period": f"{months.min():%Y-%m-%d} to {months.max():%Y-%m-%d}",
            "sources_count": len(selected_sources)
        },
        "monthly_data": pivot.reset_index().to_dict(orient="records"),
        "source_rankings": source_df.to_dict(orient="records") if len(selected_sources) > 0 else []
    }
    json_str = json.dumps(json_data, indent=2, default=str)
    st.download_button(
        "🔧 Download JSON",
        data=json_str,
        file_name=f"ftd_data_{pd.Timestamp.now():%Y%m%d}.json",
        mime="application/json",
        use_container_width=True
    )

st.caption("""
Notes:
- Dates parsed with `dayfirst=True` (DD/MM/YYYY).
- Uses only `portal - ftd_time` as requested.
- "Source" = `portal - source_marketing_campaign` (campaign or IB). 
- All contacts are assumed FTDs; the chart counts clients (rows) per month per source.
""")