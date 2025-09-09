
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="FTD Acquisition Dashboard", layout="wide")

st.title("FTD Acquisition Dashboard")
st.caption("Monthly client acquisition by source (campaign / IB), anchored on **portal - ftd_time**. Dates parsed as **DD/MM/YYYY**.")

# --- CSV Format Guide ---
with st.expander("📚 **CSV Format Guide & Instructions**", expanded=False):
    st.markdown("### Required CSV Fields")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1️⃣ `portal - ftd_time` (Required)")
        st.markdown("""
        - **Purpose**: Date when client became FTD
        - **Format**: DD/MM/YYYY (e.g., "25/08/2024")
        - **Notes**: Invalid dates will be dropped
        """)
        
        st.markdown("#### 2️⃣ `portal - source_marketing_campaign` (Required)")
        st.markdown("""
        - **Purpose**: Source/campaign that brought the client
        - **Format**: Text string (can be empty for organic)
        - **Examples**:
          - "Campaign_Name_2024"
          - "IB_Partner_Name" 
          - "Google_Ads_Q1"
          - Empty/null → "(Unknown)" Organic
        """)
    
    with col2:
        st.markdown("#### 3️⃣ `Record ID` (Required)")
        st.markdown("""
        - **Purpose**: Unique identifier for each client
        - **Format**: Any unique value (number/text)
        - **Notes**: Used for counting unique clients
        """)
        
        st.markdown("#### 📊 Source Grouping Logic")
        st.markdown("""
        When grouping is enabled:
        - **🏦 IB Sources**: Contains "IB" in name
        - **🌱 Organic**: Unknown/empty sources
        - **📢 Marketing**: All other sources
        """)
    
    st.markdown("---")
    st.markdown("### Example CSV Structure")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'Record ID': ['1001', '1002', '1003', '1004', '1005'],
        'portal - ftd_time': ['15/01/2024', '16/01/2024', '17/01/2024', '18/02/2024', '19/02/2024'],
        'portal - source_marketing_campaign': ['Google_Campaign_Q1', 'IB_Partner_John', '', 'Facebook_Ads_2024', 'IB_Sarah_Team'],
        'Other_Field_1': ['value1', 'value2', 'value3', 'value4', 'value5'],
        'Other_Field_2': ['data1', 'data2', 'data3', 'data4', 'data5']
    })
    
    st.dataframe(sample_data, hide_index=True, width="stretch")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download sample CSV template
        csv_template = sample_data.to_csv(index=False)
        st.download_button(
            "📥 Download Sample CSV Template",
            data=csv_template,
            file_name="ftd_template.csv",
            mime="text/csv",
            use_container_width=True,
            help="Download a sample CSV with the correct format"
        )
    
    with col2:
        st.info("💡 **Tip**: Column names must match exactly (including spaces)")
    
    with col3:
        st.warning("⚠️ **Note**: Each row = one unique client/FTD")
    
    st.markdown("---")
    st.markdown("### Common Issues & Solutions")
    
    issues_col1, issues_col2 = st.columns(2)
    
    with issues_col1:
        st.markdown("""
        **❌ Issue: Dates not parsing correctly**
        - ✅ Solution: Use DD/MM/YYYY format (e.g., 25/12/2024)
        - ❌ Avoid: MM/DD/YYYY or YYYY-MM-DD formats
        
        **❌ Issue: Missing required columns**
        - ✅ Solution: Ensure column names match exactly
        - ✅ Include spaces: `portal - ftd_time`
        - ❌ Avoid: `portal-ftd_time` (no spaces)
        """)
    
    with issues_col2:
        st.markdown("""
        **❌ Issue: No data showing in chart**
        - ✅ Solution: Check date range filter
        - ✅ Solution: Verify sources are selected
        - ✅ Solution: Check Data Quality Report for issues
        
        **❌ Issue: Sources showing as "(Unknown)"**
        - This happens when source field is empty
        - These are treated as Organic traffic
        """)

# --- Load data ---
uploaded = st.file_uploader("Upload CSV (must include 'portal - ftd_time' and 'portal - source_marketing_campaign')", type=["csv"])

@st.cache_data(show_spinner=False)
def load_df(file):
    df = pd.read_csv(file)
    original_count = len(df)
    
    # Expected columns
    date_col = "portal - ftd_time"
    source_col = "portal - source_marketing_campaign"
    if date_col not in df.columns or source_col not in df.columns:
        raise ValueError(f"CSV is missing required columns: '{date_col}' and '{source_col}'. Found: {list(df.columns)}")
    
    # Count before date parsing
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    invalid_dates = df[date_col].isna().sum()
    
    df[source_col] = df[source_col].fillna("(Unknown)").astype(str).str.strip()
    df = df.dropna(subset=[date_col]).copy()
    df["ftd_month"] = df[date_col].dt.to_period("M").dt.to_timestamp()
    
    # Store diagnostic info
    df.attrs['original_count'] = original_count
    df.attrs['invalid_dates'] = invalid_dates
    df.attrs['final_count'] = len(df)
    
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
        st.warning("Please upload your CSV to proceed. Check the 📚 CSV Format Guide above for requirements.")
        st.info("💡 Need help? Expand the CSV Format Guide above to see the required format and download a sample template.")
        st.stop()

# Data Quality Check
with st.expander("📊 Data Quality Report", expanded=False):
    date_col = "portal - ftd_time"
    source_col = "portal - source_marketing_campaign"
    
    # Show loading diagnostics
    st.markdown("#### Data Loading Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Records in CSV", f"{df.attrs.get('original_count', len(df)):,}")
    
    with col2:
        dropped = df.attrs.get('invalid_dates', 0)
        st.metric("Invalid Dates Dropped", f"{dropped:,}",
                  f"-{dropped/df.attrs.get('original_count', 1)*100:.1f}%" if dropped > 0 else None,
                  delta_color="inverse" if dropped > 0 else "off")
    
    with col3:
        st.metric("Valid Records", f"{df.attrs.get('final_count', len(df)):,}")
    
    with col4:
        retention = (df.attrs.get('final_count', len(df)) / df.attrs.get('original_count', len(df)) * 100) if df.attrs.get('original_count', 1) > 0 else 100
        st.metric("Data Retention", f"{retention:.1f}%")
    
    if df.attrs.get('invalid_dates', 0) > 0:
        st.warning(f"⚠️ **{df.attrs.get('invalid_dates', 0)} records were dropped** due to invalid dates in 'portal - ftd_time' column. These dates could not be parsed as DD/MM/YYYY format.")
    
    st.markdown("#### Data Quality Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Date Range", f"{df['ftd_month'].min():%b %Y} - {df['ftd_month'].max():%b %Y}")
        # Show sample dates for verification
        sample_dates = df[date_col].dropna().head(3)
        if len(sample_dates) > 0:
            st.caption("Sample parsed dates:")
            for d in sample_dates:
                st.caption(f"  • {d:%d/%m/%Y}")
    
    with col2:
        unknown_sources = (df[source_col] == "(Unknown)").sum()
        st.metric("Unknown Sources", f"{unknown_sources:,}")
        if unknown_sources > 0:
            st.warning(f"⚠️ {unknown_sources} records with unknown source")
    
    with col3:
        st.metric("Unique Sources", f"{df[source_col].nunique()}")
        # Check for data gaps
        expected_months = pd.period_range(df['ftd_month'].min(), df['ftd_month'].max(), freq='M')
        actual_months = df['ftd_month'].dt.to_period('M').unique()
        missing_months = len(expected_months) - len(actual_months)
        if missing_months > 0:
            st.warning(f"⚠️ {missing_months} months with no data")
    
    # Show monthly breakdown for verification
    st.markdown("#### Monthly Record Count (All Sources)")
    monthly_counts = df.groupby(df['ftd_month'].dt.to_period('M'))['Record ID'].count().sort_index()
    monthly_df = pd.DataFrame({
        'Month': monthly_counts.index.strftime('%B %Y'),
        'All Sources': monthly_counts.values
    })
    
    # Add a note about filtering
    st.info("💡 **Note:** This table shows ALL records in your data. The chart below only shows records from your SELECTED sources. If you've selected fewer sources, the chart numbers will be lower.")
    
    st.dataframe(monthly_df, hide_index=True, width="stretch")

# --- Sidebar filters ---
source_col = "portal - source_marketing_campaign"
group_sources = False  # Initialize here so it's available outside sidebar

with st.sidebar:
    st.header("Filters")
    # Source selection
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
    
    st.markdown("---")
    st.subheader("Display Options")
    show_total = st.checkbox("Show Total (All Sources)", value=True, help="Display a line showing the total across all selected sources")
    
    # Source grouping option
    group_sources = st.checkbox("Group Sources by Type", value=False, 
                                help="Group sources into IB, Organic (Unknown), and Marketing categories")
    
    if group_sources:
        st.caption("📊 **Grouping Logic:**")
        st.caption("• **IB**: Sources containing 'IB' in the name")
        st.caption("• **Organic**: Unknown sources")
        st.caption("• **Marketing**: All other sources")

# Apply filters
mask_time = (df["ftd_month"] >= pd.Timestamp(start)) & (df["ftd_month"] <= pd.Timestamp(end))
mask_source = df[source_col].isin(selected_sources) if selected_sources else pd.Series(True, index=df.index)
dff = df.loc[mask_time & mask_source].copy()

# Also get data for ALL sources in the timeframe (for active sources calculation)
dff_all_sources = df.loc[mask_time].copy()

# Function to categorize sources
def categorize_source(source_name):
    """Categorize source into IB, Organic, or Marketing"""
    source_lower = source_name.lower()
    if 'ib' in source_lower:
        return '🏦 IB Sources'
    elif source_lower in ['(unknown)', 'unknown']:
        return '🌱 Organic'
    else:
        return '📢 Marketing'

# Aggregate
if group_sources:
    # Add source category column
    dff['source_category'] = dff[source_col].apply(categorize_source)
    
    # Group by category instead of individual source
    counts = (
        dff.groupby(["ftd_month", "source_category"])["Record ID"].size().reset_index(name="clients")
    )
    counts.rename(columns={"source_category": source_col}, inplace=True)
    
    # Get unique categories from selected sources
    selected_categories = dff['source_category'].unique().tolist()
    
    months = pd.period_range(dff["ftd_month"].min(), dff["ftd_month"].max(), freq="M").to_timestamp()
    # Ensure all (month, category) combos exist
    full = (
        pd.MultiIndex.from_product([months, selected_categories], names=["ftd_month", source_col])
        .to_frame(index=False)
    )
    counts = (
        full.merge(counts, on=["ftd_month", source_col], how="left")
        .fillna({"clients": 0})
    )
    
    # Update selected_sources to be categories for display purposes
    display_sources = selected_categories
else:
    # Original aggregation by individual source
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
    display_sources = selected_sources

# KPI row
total_clients = int(counts["clients"].sum())
span_months = len(months)
avg_monthly = total_clients / span_months if span_months > 0 else 0

# Calculate active sources (sources with at least 1 client in the timeframe)
# Get unique sources that have data in the filtered timeframe (across ALL sources, not just selected)
sources_with_clients_in_period = dff_all_sources.groupby(source_col)["Record ID"].size()
active_sources_in_period = len(sources_with_clients_in_period[sources_with_clients_in_period > 0])
total_sources_with_data = df[source_col].nunique()
active_percentage = (active_sources_in_period / total_sources_with_data * 100) if total_sources_with_data > 0 else 0

st.markdown("### Overview")
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Clients", f"{total_clients:,}",
          help="Total clients from SELECTED sources only")
k2.metric("Avg/Month", f"{avg_monthly:.0f}")
k3.metric("Active Sources", f"{active_sources_in_period} / {total_sources_with_data}", 
          f"{active_percentage:.1f}% active",
          help="Sources with ≥1 client in selected timeframe (across ALL sources)")
k4.metric("Selected" if not group_sources else "Categories", 
          f"{len(display_sources)} / {len(all_sources) if not group_sources else 3}",
          help="Sources currently selected for display")
k5.metric("Period", f"{span_months} months")

# Add info about what's being displayed
if group_sources:
    st.info(f"📊 **Viewing grouped data:** {', '.join(display_sources)}")
elif len(selected_sources) < len(all_sources):
    if len(selected_sources) == 1:
        st.info(f"📌 **Viewing data for 1 source:** {selected_sources[0]}")
    else:
        st.info(f"📌 **Viewing data for {len(selected_sources)} selected sources.** Select more sources in the sidebar to see additional data.")

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

# Prepare data for chart
chart_data = counts.copy()

# Add total line if requested
if show_total and (len(display_sources) > 1 or group_sources):
    # Calculate monthly totals
    monthly_totals = counts.groupby("ftd_month")["clients"].sum().reset_index()
    monthly_totals[source_col] = "📊 TOTAL"
    
    # Combine with original data
    chart_data = pd.concat([counts, monthly_totals], ignore_index=True)
    
    # Adjust color scale
    if group_sources:
        # Use specific colors for grouped categories
        color_mapping = {
            '🏦 IB Sources': '#4CAF50',  # Green for IB
            '🌱 Organic': '#2196F3',      # Blue for Organic
            '📢 Marketing': '#FF9800',     # Orange for Marketing
            '📊 TOTAL': '#ff0000'          # Red for Total
        }
        domain = display_sources + ["📊 TOTAL"]
        range_colors = [color_mapping.get(s, '#808080') for s in domain]
        color_scale = alt.Scale(domain=domain, range=range_colors)
    else:
        # Original color scale for individual sources
        color_scale = alt.Scale(
            domain=display_sources + ["📊 TOTAL"],
            range=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"][:len(display_sources)] + ["#ff0000"]
        )
else:
    if group_sources:
        # Use specific colors for grouped categories without total
        color_mapping = {
            '🏦 IB Sources': '#4CAF50',  # Green for IB
            '🌱 Organic': '#2196F3',      # Blue for Organic
            '📢 Marketing': '#FF9800'      # Orange for Marketing
        }
        domain = display_sources
        range_colors = [color_mapping.get(s, '#808080') for s in domain]
        color_scale = alt.Scale(domain=domain, range=range_colors)
    else:
        color_scale = None

chart_base = alt.Chart(chart_data).encode(
    x=alt.X("ftd_month:T", 
            axis=alt.Axis(title="Month", format="%b %Y"),
            scale=alt.Scale(padding=20)),
    y=alt.Y("clients:Q", 
            axis=alt.Axis(title="Clients"), 
            stack=None if chart_type == "Line" or (show_total and len(selected_sources) > 1) else "zero"),
    color=alt.Color(f"{source_col}:N", 
                   legend=alt.Legend(title="Source"),
                   scale=color_scale),
    tooltip=[
        alt.Tooltip("ftd_month:T", title="Month", format="%B %Y"),
        alt.Tooltip(f"{source_col}:N", title="Source"),
        alt.Tooltip("clients:Q", title="Clients", format=",.0f")
    ]
)

if chart_type == "Line":
    # Create line with visible points for better hover experience
    # Make TOTAL line thicker if present
    if show_total and len(selected_sources) > 1:
        line = chart_base.mark_line().encode(
            strokeWidth=alt.condition(
                alt.datum[source_col] == "📊 TOTAL",
                alt.value(4),  # Thicker line for total
                alt.value(2)   # Normal line for sources
            ),
            opacity=alt.condition(
                alt.datum[source_col] == "📊 TOTAL",
                alt.value(1),    # Full opacity for total
                alt.value(0.7)   # Slightly transparent for sources
            )
        )
        points = chart_base.mark_circle().encode(
            size=alt.condition(
                alt.datum[source_col] == "📊 TOTAL",
                alt.value(70),   # Bigger points for total
                alt.value(40)    # Normal points for sources
            ),
            opacity=alt.value(1)
        )
    else:
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
    rules = alt.Chart(chart_data).mark_rule(color="gray", strokeDash=[3, 3], opacity=0.5).encode(
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
if group_sources:
    st.caption("📊 Data grouped by category (IB / Organic / Marketing)")
    
pivot = counts.pivot_table(index="ftd_month", columns=source_col, values="clients", fill_value=0).sort_index()

# Add total column if more than one source/category
if len(display_sources) > 1:
    pivot["📊 TOTAL"] = pivot.sum(axis=1)
    
# Format the index to show month names
pivot.index = pivot.index.strftime("%b %Y")

st.dataframe(pivot, width="stretch")

# Source Performance Ranking
if len(display_sources) > 0:
    st.markdown("### Source Performance Ranking")
    
    if group_sources:
        st.info("📊 Showing performance for grouped categories")
    
    # Calculate source statistics
    source_stats = []
    for source in display_sources:
        source_data = counts[counts[source_col] == source]
        total = source_data["clients"].sum()
        avg = source_data["clients"].mean()
        max_val = source_data["clients"].max()
        min_val = source_data["clients"].min()
        
        # Calculate trend (simple comparison of first half vs second half)
        if len(source_data) > 2:
            values = source_data["clients"].values
            mid = len(values) // 2
            first_half_avg = np.mean(values[:mid])
            second_half_avg = np.mean(values[mid:])
            
            # Compare averages to determine trend
            change_percent = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
            trend = "📈" if change_percent > 10 else "📉" if change_percent < -10 else "➡️"
        else:
            trend = "➡️"
        
        label = "Category" if group_sources else "Source"
        source_stats.append({
            label: source,
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
        if len(display_sources) > 0:
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
            "sources_count": len(display_sources)
        },
        "monthly_data": pivot.reset_index().to_dict(orient="records"),
        "source_rankings": source_df.to_dict(orient="records") if len(display_sources) > 0 else []
    }
    json_str = json.dumps(json_data, indent=2, default=str)
    st.download_button(
        "🔧 Download JSON",
        data=json_str,
        file_name=f"ftd_data_{pd.Timestamp.now():%Y%m%d}.json",
        mime="application/json",
        use_container_width=True
    )

# Footer with quick reference
with st.expander("ℹ️ Quick Reference", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📅 Date Processing**
        - Format: DD/MM/YYYY
        - Field: `portal - ftd_time`
        - Invalid dates are dropped
        """)
    
    with col2:
        st.markdown("""
        **📊 Source Categories**
        - IB: Contains "IB" in name
        - Organic: Unknown/empty
        - Marketing: All others
        """)
    
    with col3:
        st.markdown("""
        **📈 Metrics**
        - Each row = 1 client
        - Grouped by month
        - Filtered by date range
        """)

st.caption("""
Notes: Dates parsed with `dayfirst=True` (DD/MM/YYYY). Uses only `portal - ftd_time` as requested.
"Source" = `portal - source_marketing_campaign` (campaign or IB). All contacts are assumed FTDs; the chart counts clients (rows) per month per source.
""")