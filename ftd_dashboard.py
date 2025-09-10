
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np

def safe_int_convert(value, default=0):
    """Safely convert value to int with fallback for None/NaN values"""
    try:
        if value is None or pd.isna(value):
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

st.set_page_config(page_title="FTD Acquisition Dashboard", layout="wide")

# Custom CSS to reduce font size in sidebar by 35%
st.markdown("""
<style>
    /* Global sidebar font size reduction - 35% smaller (65% of original) */
    section[data-testid="stSidebar"] * {
        font-size: 0.65rem !important;
    }
    
    /* Main sidebar title */
    section[data-testid="stSidebar"] h1 {
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Sidebar subheaders */
    section[data-testid="stSidebar"] h2 {
        font-size: 0.9rem !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Sidebar h3 headers */
    section[data-testid="stSidebar"] h3 {
        font-size: 0.8rem !important;
        margin-top: 0.3rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Checkbox labels specifically */
    section[data-testid="stSidebar"] .stCheckbox label span {
        font-size: 0.65rem !important;
        line-height: 1.2 !important;
    }
    
    /* Reduce checkbox spacing even more */
    section[data-testid="stSidebar"] .stCheckbox {
        margin-bottom: -0.8rem !important;
    }
    
    /* Buttons in sidebar */
    section[data-testid="stSidebar"] button {
        font-size: 0.65rem !important;
        padding: 0.2rem 0.4rem !important;
        height: auto !important;
        min-height: 1.5rem !important;
    }
    
    /* Search box and other inputs */
    section[data-testid="stSidebar"] input {
        font-size: 0.65rem !important;
        padding: 0.3rem !important;
        height: 2rem !important;
    }
    
    /* Caption text */
    section[data-testid="stSidebar"] .caption, 
    section[data-testid="stSidebar"] small {
        font-size: 0.6rem !important;
    }
    
    /* Number inputs */
    section[data-testid="stSidebar"] .stNumberInput label {
        font-size: 0.65rem !important;
    }
    
    /* Slider labels */
    section[data-testid="stSidebar"] .stSlider label {
        font-size: 0.65rem !important;
    }
    
    /* Date inputs */
    section[data-testid="stSidebar"] .stDateInput label {
        font-size: 0.65rem !important;
    }
    
    /* Reduce overall padding in sidebar */
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }
    
    /* Reduce spacing between sections */
    section[data-testid="stSidebar"] hr {
        margin: 0.5rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Dashboard selector
dashboard_type = st.radio(
    "Select Dashboard",
    ["FTD Dashboard", "KYC Dashboard"],
    horizontal=True,
    help="Switch between FTD (First Time Deposit) and KYC (Know Your Customer) dashboards"
)

# Dynamic title and caption based on selection
if dashboard_type == "FTD Dashboard":
    st.title("FTD Acquisition Dashboard")
    st.caption("Monthly client acquisition by source (campaign / IB), anchored on **portal - ftd_time**. Dates parsed as **DD/MM/YYYY**.")
    date_column = "portal - ftd_time"
    metric_name = "FTD Clients"
else:
    st.title("KYC Clients Dashboard")
    st.caption("Monthly KYC'd clients by source (campaign / IB), anchored on **DATE_CREATED**. Dates parsed as **DD/MM/YYYY** (time component ignored).")
    date_column = "DATE_CREATED"
    metric_name = "KYC'd Clients"

# Initialize tour state
if "tour_step" not in st.session_state:
    st.session_state.tour_step = 0
if "tour_active" not in st.session_state:
    st.session_state.tour_active = False

# --- CSV Format Guide ---
with st.expander("📚 **CSV Format Guide & Instructions**", expanded=False):
    st.markdown("### Required CSV Fields")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1️⃣ `portal - ftd_time` (Required)")
        st.markdown("""
        - **Purpose**: Date when client became FTD
        - **Format**: DD/MM/YYYY (e.g., "25/08/2024")
        - **Used for**: FTD Dashboard
        - **Valid Range**: 2023-2026 (earlier dates treated as invalid)
        """)
        
        st.markdown("#### 2️⃣ `DATE_CREATED` or `date_created` (Required)")
        st.markdown("""
        - **Purpose**: Date when client completed KYC
        - **Format**: DD/MM/YYYY HH:MM:SS
        - **Example**: "25/08/2024 14:30:45"
        - **Used for**: KYC Dashboard
        - **Valid Range**: 2023-2026 (earlier dates treated as invalid)
        - **Note**: Time component is ignored, case-insensitive
        """)
        
        st.markdown("#### 3️⃣ `portal - source_marketing_campaign` (Required)")
        st.markdown("""
        - **Purpose**: Source/campaign that brought the client
        - **Format**: Text string (can be empty for organic)
        - **Examples**: IB-18050031, MKT-Campaign, etc.
        - **Empty/null**: Becomes "(Unknown)" Organic
        """)
    
    with col2:
        st.markdown("#### 4️⃣ `Record ID` (Required)")
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
        
        st.warning("""
        **⚠️ Important**: Both date columns MUST be present in your CSV file:
        - `portal - ftd_time` (for FTD)
        - `DATE_CREATED` or `date_created` (for KYC)
        
        Column names are case-insensitive. Both columns required even if using only one dashboard.
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
uploaded = st.file_uploader("Upload CSV (must include both date columns and source column)", type=["csv"])

def parse_dd_mm_yyyy_date(date_str, debug=False):
    """Force DD/MM/YYYY parsing - NO AMERICAN FORMAT"""
    try:
        # Remove any extra whitespace
        date_str = str(date_str).strip()
        
        # Handle NaN/None/empty values AND the string 'NaT'
        if date_str in ['nan', 'NaN', 'None', '', 'NaT', 'nat', 'NAT', '<NA>', 'null', 'NULL']:
            if debug:
                print(f"  Null/NaT value detected: '{date_str}'")
            return pd.NaT
            
        # Handle 1/1/1970 placeholder dates (means "no FTD yet")
        if date_str == '1/1/1970' or date_str == '01/01/1970' or date_str == '1/01/1970':
            if debug:
                print(f"  Skipping placeholder date (no FTD): {date_str}")
            return pd.NaT
            
        # Remove time component if present
        if ' ' in date_str:
            date_str = date_str.split(' ')[0]
        
        # Split by / or -
        if '/' in date_str:
            parts = date_str.split('/')
        elif '-' in date_str:
            parts = date_str.split('-')
        else:
            if debug:
                print(f"  No separator found in: {date_str}")
            return pd.NaT
            
        if len(parts) >= 3:
            day = int(parts[0])    # FIRST part is DAY
            month = int(parts[1])  # SECOND part is MONTH  
            year = int(parts[2])   # THIRD part is YEAR
            
            # Handle 2-digit years
            if year < 100:
                if year < 30:  # 00-29 -> 2000-2029
                    year = 2000 + year
                else:  # 30-99 -> 1930-1999 (but these will be filtered out)
                    year = 1900 + year
            
            # Basic validation
            if 1 <= day <= 31 and 1 <= month <= 12:
                # Don't filter by year here, let the main function handle it
                result = pd.Timestamp(year, month, day)
                if debug and year < 2020:
                    print(f"  Parsed but will filter: {date_str} -> {result}")
                return result
            else:
                if debug:
                    print(f"  Invalid day/month: day={day}, month={month} from {date_str}")
    except Exception as e:
        if debug:
            print(f"  Error parsing '{date_str}': {e}")
        pass
    return pd.NaT

@st.cache_data(show_spinner=False)
def load_df(file):
    # Read CSV with ALL columns as strings first to prevent pandas auto-parsing dates incorrectly
    df = pd.read_csv(file, dtype=str)
    original_count = len(df)
    
    # Create debug info to show in UI
    debug_info = []
    
    # Just show me the first 5 rows of the ENTIRE CSV as-is
    debug_info.append("📄 RAW CSV DATA - First 5 rows:")
    debug_info.append(df.head().to_string())
    
    # Show EXACT column names (check for extra spaces/characters)  
    debug_info.append(f"\n📋 EXACT column names: {[repr(col) for col in df.columns]}")
    
    # Show first 10 values from the FTD column exactly as they appear
    ftd_col = 'portal - ftd_time'
    if ftd_col in df.columns:
        debug_info.append(f"\n📅 First 10 values from '{ftd_col}':")
        for i in range(min(10, len(df))):
            val = df[ftd_col].iloc[i]
            debug_info.append(f"  Row {i+1}: {repr(val)}")
    else:
        debug_info.append(f"\n❌ Column '{ftd_col}' not found!")
        debug_info.append("Looking for columns containing 'ftd':")
        for col in df.columns:
            if 'ftd' in col.lower():
                debug_info.append(f"  Found: {repr(col)}")
                debug_info.append(f"    Sample values: {df[col].head(3).tolist()}")
    
    # Add summary of placeholder dates
    placeholder_count = 0
    if ftd_col in df.columns:
        placeholder_count = df[ftd_col].isin(['1/1/1970', '01/01/1970', '1/01/1970']).sum()
        debug_info.append(f"\n📊 FTD DATA SUMMARY:")
        debug_info.append(f"  Total records: {len(df)}")
        debug_info.append(f"  Placeholder dates (1/1/1970): {placeholder_count}")
        debug_info.append(f"  Potential FTD records: {len(df) - placeholder_count}")
    
    # Store debug info for display
    df.attrs['debug_info'] = '\n'.join(debug_info)
    df.attrs['placeholder_count'] = placeholder_count
    
    # Also print to console
    print('\n'.join(debug_info))
    
    # Expected columns - BOTH date columns must be present
    ftd_date_col = "portal - ftd_time"
    kyc_date_col = "DATE_CREATED"
    source_col = "portal - source_marketing_campaign"
    
    # Check for case-insensitive column matching
    def find_column_case_insensitive(df, col_name):
        """Find column name with case-insensitive matching"""
        for col in df.columns:
            if col.lower() == col_name.lower():
                return col
        return None
    
    # Find actual column names (handling case differences)
    actual_ftd_col = find_column_case_insensitive(df, ftd_date_col)
    actual_kyc_col = find_column_case_insensitive(df, kyc_date_col)
    actual_source_col = find_column_case_insensitive(df, source_col)
    
    # Check all required columns exist
    missing_cols = []
    if not actual_ftd_col:
        missing_cols.append(ftd_date_col)
    if not actual_kyc_col:
        missing_cols.append(kyc_date_col)
    if not actual_source_col:
        missing_cols.append(source_col)
    
    if missing_cols:
        raise ValueError(f"CSV is missing required columns: {missing_cols}. Found columns: {list(df.columns)}")
    
    # Use the actual column names found
    ftd_date_col = actual_ftd_col
    kyc_date_col = actual_kyc_col
    source_col = actual_source_col
    
    # Debug: Show actual raw date values
    print("🔍 RAW DATE DEBUGGING:")
    print("📌 NOTE: Reading all CSV columns as strings to prevent pandas auto-parsing")
    
    # EMERGENCY: Show ALL columns and sample values
    print("\n🚨 EMERGENCY DEBUG - ALL COLUMNS AND SAMPLE VALUES:")
    for col in df.columns[:20]:  # Show first 20 columns
        sample_vals = df[col].head(3).tolist()
        print(f"  Column '{col}': {sample_vals}")
    
    print(f"\n🎯 Looking for FTD column: '{ftd_date_col}'")
    print(f"🎯 Column exists in df: {ftd_date_col in df.columns}")
    
    if ftd_date_col in df.columns:
        print(f"\nFirst 10 raw values from '{ftd_date_col}' column:")
        for i in range(min(10, len(df))):
            raw_value = df[ftd_date_col].iloc[i]
            print(f"Row {i+1}: '{raw_value}' (type: {type(raw_value).__name__})")
    else:
        print(f"❌ ERROR: Column '{ftd_date_col}' NOT FOUND in DataFrame!")
        print(f"Available columns: {list(df.columns)}")
    
    print(f"\n📋 Total columns: {len(df.columns)}")
    print(f"📊 DataFrame shape: {df.shape}")
    
    # Parse FTD date column using EXPLICIT DD/MM/YYYY parser
    sample_dates = df[ftd_date_col].head(20).tolist()
    print(f"DEBUG: Sample raw FTD dates: {sample_dates[:10]}")
    print(f"DEBUG: Data types: {df[ftd_date_col].dtype}")
    
    # Check for unique date formats in the data
    unique_formats = df[ftd_date_col].astype(str).str.extract(r'(\d+)[/-](\d+)[/-](\d+)', expand=False).notna().all(axis=1).sum()
    print(f"DEBUG: Dates matching DD/MM/YYYY or DD-MM-YYYY pattern: {unique_formats}")
    
    # Debug parse first few dates to see what's happening
    print("DEBUG: Parsing first 5 dates with debug mode:")
    for i, date_str in enumerate(sample_dates[:5]):
        print(f"  Date {i+1}: '{date_str}' (type: {type(date_str).__name__}, repr: {repr(date_str)})")
        parse_dd_mm_yyyy_date(date_str, debug=True)
    
    # Apply the explicit parser to all FTD dates
    df[ftd_date_col] = df[ftd_date_col].apply(parse_dd_mm_yyyy_date)
    
    # Ensure the column is datetime type
    df[ftd_date_col] = pd.to_datetime(df[ftd_date_col])
    
    # Show parsing success rate BEFORE filtering
    valid_dates_before_filter = df[ftd_date_col].notna().sum()
    placeholder_dates = len(df) - valid_dates_before_filter
    print(f'📊 FTD Parsing Results:')
    print(f'  - Valid FTD dates parsed: {valid_dates_before_filter}')
    print(f'  - Placeholder/No FTD (1/1/1970): {placeholder_dates}')
    print(f'  - Total records: {len(df)}')
    
    # Mark dates before 2023 or after reasonable future as invalid
    min_valid_date = pd.Timestamp('2023-01-01')
    max_valid_date = pd.Timestamp('2026-12-31')  # Allow up to end of 2026
    
    ftd_before_2023 = (df[ftd_date_col] < min_valid_date).sum()
    ftd_future = (df[ftd_date_col] > max_valid_date).sum()
    
    df.loc[df[ftd_date_col] < min_valid_date, ftd_date_col] = pd.NaT
    df.loc[df[ftd_date_col] > max_valid_date, ftd_date_col] = pd.NaT
    
    invalid_ftd_dates = df[ftd_date_col].isna().sum()
    valid_dates_after_filter = df[ftd_date_col].notna().sum()
    print(f'✅ Final: {valid_dates_after_filter} valid FTD dates after filtering ({ftd_before_2023} before 2023, {ftd_future} after 2026)')
    
    # Parse KYC date column using EXPLICIT DD/MM/YYYY parser
    print(f"DEBUG: Sample raw KYC dates: {df[kyc_date_col].head(10).tolist()}")
    
    # Apply the explicit parser to all KYC dates
    df[kyc_date_col] = df[kyc_date_col].apply(parse_dd_mm_yyyy_date)
    
    # Ensure the column is datetime type
    df[kyc_date_col] = pd.to_datetime(df[kyc_date_col])
    
    # Show parsing success rate
    valid_kyc_dates = df[kyc_date_col].notna().sum()
    print(f'✅ Successfully parsed {valid_kyc_dates} out of {len(df)} KYC dates ({valid_kyc_dates/len(df)*100:.1f}%)')
    
    # Mark KYC dates before 2023 or too far in future as invalid too
    kyc_before_2023 = (df[kyc_date_col] < min_valid_date).sum()
    kyc_future = (df[kyc_date_col] > max_valid_date).sum()
    
    df.loc[df[kyc_date_col] < min_valid_date, kyc_date_col] = pd.NaT
    df.loc[df[kyc_date_col] > max_valid_date, kyc_date_col] = pd.NaT
    
    invalid_kyc_dates = df[kyc_date_col].isna().sum()
    
    # Fill missing sources
    df[source_col] = df[source_col].fillna("(Unknown)").astype(str).str.strip()
    
    # Create month columns for both dashboards
    df["ftd_month"] = df[ftd_date_col].dt.to_period("M").dt.to_timestamp()
    df["kyc_month"] = df[kyc_date_col].dt.to_period("M").dt.to_timestamp()
    
    # Store diagnostic info
    df.attrs['original_count'] = original_count
    df.attrs['invalid_ftd_dates'] = invalid_ftd_dates
    df.attrs['invalid_kyc_dates'] = invalid_kyc_dates
    df.attrs['ftd_before_2023'] = ftd_before_2023
    df.attrs['kyc_before_2023'] = kyc_before_2023
    df.attrs['ftd_future'] = ftd_future
    df.attrs['kyc_future'] = kyc_future
    df.attrs['final_count'] = len(df)
    
    # Store the actual column names found for later use
    df.attrs['ftd_date_col'] = ftd_date_col
    df.attrs['kyc_date_col'] = kyc_date_col
    df.attrs['source_col'] = source_col
    
    return df

if uploaded is not None:
    try:
        df = load_df(uploaded)
        
        # Show debug info in an expander RIGHT AFTER LOADING
        with st.expander("🔍 RAW CSV DEBUG INFO - CLICK HERE TO SEE YOUR DATA", expanded=True):
            if hasattr(df, 'attrs') and 'debug_info' in df.attrs:
                st.code(df.attrs['debug_info'], language='text')
            else:
                st.error("Debug info not available")
                
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
    # Get the actual column names from the dataframe attributes
    source_col = df.attrs.get('source_col', 'portal - source_marketing_campaign')
    
    # Select the appropriate date column and month column based on dashboard
    if dashboard_type == "FTD Dashboard":
        active_date_col = df.attrs.get('ftd_date_col', 'portal - ftd_time')
        active_month_col = "ftd_month"
        invalid_dates_key = 'invalid_ftd_dates'
    else:
        active_date_col = df.attrs.get('kyc_date_col', 'DATE_CREATED')
        active_month_col = "kyc_month"
        invalid_dates_key = 'invalid_kyc_dates'
    
    # Show loading diagnostics
    st.markdown(f"#### Data Loading Summary ({dashboard_type})")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", f"{df.attrs.get('original_count', len(df)):,}")
    
    with col2:
        placeholder_count = df.attrs.get('placeholder_count', 0)
        st.metric("No FTD Yet", f"{placeholder_count:,}",
                  "1/1/1970 placeholders",
                  delta_color="off")
    
    with col3:
        # Count valid records for this dashboard (non-null dates)
        valid_records = df[active_date_col].notna().sum()
        st.metric("With FTD", f"{valid_records:,}",
                  f"{valid_records/df.attrs.get('original_count', 1)*100:.1f}% conversion")
    
    with col4:
        retention = (valid_records / df.attrs.get('original_count', len(df)) * 100) if df.attrs.get('original_count', 1) > 0 else 100
        st.metric("Data Retention", f"{retention:.1f}%")
    
    if df.attrs.get(invalid_dates_key, 0) > 0:
        before_2023_key = 'ftd_before_2023' if dashboard_type == "FTD Dashboard" else 'kyc_before_2023'
        future_key = 'ftd_future' if dashboard_type == "FTD Dashboard" else 'kyc_future'
        before_2023 = df.attrs.get(before_2023_key, 0)
        future = df.attrs.get(future_key, 0)
        
        details = []
        if before_2023 > 0:
            details.append(f"{before_2023} before 2023")
        if future > 0:
            details.append(f"{future} too far in future")
            
        if details:
            st.warning(f"⚠️ **{df.attrs.get(invalid_dates_key, 0)} records have invalid dates** in '{active_date_col}' column, including {' and '.join(details)}.")
        else:
            st.warning(f"⚠️ **{df.attrs.get(invalid_dates_key, 0)} records have invalid dates** in '{active_date_col}' column. These dates could not be parsed.")
    
    st.markdown("#### Data Quality Metrics")
    col1, col2, col3 = st.columns(3)
    
    # Filter to only records with valid dates for the active dashboard
    valid_df = df[df[active_date_col].notna()].copy()
    
    with col1:
        if len(valid_df) > 0:
            st.metric("Date Range", f"{valid_df[active_month_col].min():%b %Y} - {valid_df[active_month_col].max():%b %Y}")
            # Show sample dates for verification
            sample_dates = valid_df[active_date_col].dropna().head(3)
            if len(sample_dates) > 0:
                st.caption("Sample parsed dates:")
                for d in sample_dates:
                    if dashboard_type == "KYC Dashboard":
                        st.caption(f"  • {d:%d/%m/%Y %H:%M:%S}")
                    else:
                        st.caption(f"  • {d:%d/%m/%Y}")
            else:
                st.caption("No valid dates found")
                # Show some raw date samples for debugging
                raw_samples = df[active_date_col].head(5)
                st.caption("Raw date samples from CSV:")
                for i, raw_date in enumerate(raw_samples):
                    st.caption(f"  • Row {i+1}: '{raw_date}'")
        else:
            st.metric("Date Range", "No valid dates")
            # Show raw date samples for debugging
            raw_samples = df[active_date_col].head(5)
            st.caption("Raw date samples from CSV:")
            for i, raw_date in enumerate(raw_samples):
                st.caption(f"  • Row {i+1}: '{raw_date}'")
    
    with col2:
        unknown_sources = (valid_df[source_col] == "(Unknown)").sum()
        st.metric("Unknown Sources", f"{unknown_sources:,}")
        if unknown_sources > 0:
            st.warning(f"⚠️ {unknown_sources} records with unknown source")
    
    with col3:
        st.metric("Unique Sources", f"{valid_df[source_col].nunique()}")
        # Check for data gaps
        if len(valid_df) > 0:
            expected_months = pd.period_range(valid_df[active_month_col].min(), valid_df[active_month_col].max(), freq='M')
            actual_months = valid_df[active_month_col].dt.to_period('M').unique()
            missing_months = len(expected_months) - len(actual_months)
            if missing_months > 0:
                st.warning(f"⚠️ {missing_months} months with no data")
    
    # Show monthly breakdown for verification
    st.markdown(f"#### Monthly Record Count (All Sources - {dashboard_type})")
    if len(valid_df) > 0:
        monthly_counts = valid_df.groupby(valid_df[active_month_col].dt.to_period('M'))['Record ID'].count().sort_index()
        monthly_df = pd.DataFrame({
            'Month': monthly_counts.index.strftime('%B %Y'),
            'All Sources': monthly_counts.values
        })
        
        # Add a note about filtering
        st.info("💡 **Note:** This table shows ALL records in your data. The chart below only shows records from your SELECTED sources. If you've selected fewer sources, the chart numbers will be lower.")
        
        st.dataframe(monthly_df, hide_index=True, width="stretch")
    else:
        st.warning("No valid data available for the selected dashboard. Please check the data quality metrics above.")

# --- Simple Tour Implementation ---
# Using Streamlit's native info boxes for reliability
tour_container = st.container()
with tour_container:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Quick Tour Guide", type="primary", use_container_width=True):
            st.session_state.show_tour_guide = not st.session_state.get('show_tour_guide', False)
    
    if st.session_state.get('show_tour_guide', False):
        st.markdown("---")
        st.markdown("## 🎯 Dashboard Tour Guide")
        
        tour_tab1, tour_tab2, tour_tab3, tour_tab4 = st.tabs(["📊 Data & Filters", "📈 Charts", "📋 Tables", "💾 Export"])
        
        with tour_tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.info("""
                **🎛️ Sidebar Filters (Left Panel)**
                
                • **Source Selection**: Search box + checkboxes for each source
                • **Quick Buttons**: Select All, Clear All, Top N
                • **Scrollable List**: 500px container with small fonts
                • **Date Range**: Individual month checkboxes
                • **Display Options**: Toggle total line, group sources
                """)
            with col2:
                st.info("""
                **📊 Data Quality (Top Expanders)**
                
                • **CSV Format Guide**: Required fields and examples
                • **Data Quality Report**: Invalid dates, date range, unknowns
                • **Monthly Breakdown**: Shows ALL records by month
                • **Sample Dates**: Verifies DD/MM/YYYY parsing
                """)
        
        with tour_tab2:
            st.success("""
            **📈 Main Chart Features**
            
            • **Interactive**: Hover to see exact values
            • **Chart Types**: Switch between Line and Stacked Bar
            • **Red Total Line**: Toggle on/off in Display Options
            • **Color Coding** (when grouped):
              - 🟢 Green = IB Sources
              - 🔵 Blue = Organic (Unknown)
              - 🟠 Orange = Marketing
            • **Legend**: Click items to highlight
            """)
        
        with tour_tab3:
            st.warning("""
            **📋 Data Tables & Metrics**
            
            • **Overview Metrics**: Total clients, averages, active sources
            • **Performance Metrics**: Latest/Best/Worst months, growth %
            • **Source Rankings**: Top/Bottom performers with trends
            • **Pivot Table**: Month × Source matrix with totals
            • **Note**: Tables show filtered data only!
            """)
        
        with tour_tab4:
            st.error("""
            **💾 Export Options**
            
            • **CSV**: Universal format for Excel/Sheets
            • **Excel**: Direct .xlsx with formatting
            • **JSON**: For developers and APIs
            • **Filtered Data**: Exports respect your current filters
            • **Debug Mode**: Check "Show debug info" for raw data
            """)
        
        if st.button("✅ Close Tour Guide", use_container_width=True):
            st.session_state.show_tour_guide = False
            st.rerun()
        
        st.markdown("---")

# --- Sidebar filters ---
# Get the actual source column name from the dataframe
source_col = df.attrs.get('source_col', 'portal - source_marketing_campaign')
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
    
    # Initialize session state if not exists - default to ALL sources selected
    if "selected_sources" not in st.session_state:
        st.session_state.selected_sources = all_sources.copy()  # Select all sources by default
    
    # Filter sources based on search
    filtered_sources = [s for s in all_sources if search_term.lower() in s.lower()]
    
    # Display count
    st.caption(f"Showing {len(filtered_sources)} of {len(all_sources)} sources | {len(st.session_state.selected_sources)} selected")
    
    # Scrollable container with checkboxes
    st.markdown("---")
    container = st.container(height=500)  # Fixed height for scrolling - increased further with smaller fonts
    
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
    
    # Get all available months based on dashboard type
    # Use the same variables defined at the top
    if dashboard_type == "FTD Dashboard":
        month_col = "ftd_month"
    else:
        month_col = "kyc_month"
    
    # Filter to valid records for this dashboard
    valid_df_sidebar = df[df[month_col].notna()].copy()
    
    if len(valid_df_sidebar) > 0:
        min_m, max_m = valid_df_sidebar[month_col].min(), valid_df_sidebar[month_col].max()
        all_months = pd.date_range(start=min_m, end=max_m, freq='MS').to_list()
    else:
        all_months = []
        st.warning(f"No valid dates found for {dashboard_type}. Please check your data.")
    
    # Initialize selected months in session state
    if "selected_months" not in st.session_state:
        # Default to all months selected
        st.session_state.selected_months = all_months
    
    # Quick select buttons
    st.caption("Quick select:")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("All", use_container_width=True):
            st.session_state.selected_months = all_months
            st.rerun()
    with col2:
        if st.button("None", use_container_width=True):
            st.session_state.selected_months = []
            st.rerun()
    with col3:
        if st.button("Last 6M", use_container_width=True):
            st.session_state.selected_months = all_months[-6:] if len(all_months) >= 6 else all_months
            st.rerun()
    with col4:
        if st.button("YTD", use_container_width=True):
            current_year = max_m.year
            st.session_state.selected_months = [m for m in all_months if m.year == current_year]
            st.rerun()
    
    # Display count
    st.caption(f"Selected {len(st.session_state.selected_months)} of {len(all_months)} months")
    
    # Scrollable container with month checkboxes
    st.markdown("---")
    month_container = st.container(height=200)  # Fixed height for scrolling
    
    with month_container:
        # Group months by year for better organization
        months_by_year = {}
        for month in all_months:
            year = month.year
            if year not in months_by_year:
                months_by_year[year] = []
            months_by_year[year].append(month)
        
        # Display checkboxes grouped by year
        for year in sorted(months_by_year.keys(), reverse=True):  # Most recent year first
            # Year header with select/deselect buttons
            year_col1, year_col2, year_col3 = st.columns([3, 1, 1])
            with year_col1:
                st.markdown(f"**📅 {year}**")
            with year_col2:
                if st.button("All", key=f"select_year_{year}", help=f"Select all months in {year}", use_container_width=True):
                    for month in months_by_year[year]:
                        if month not in st.session_state.selected_months:
                            st.session_state.selected_months.append(month)
                    st.rerun()
            with year_col3:
                if st.button("None", key=f"deselect_year_{year}", help=f"Deselect all months in {year}", use_container_width=True):
                    st.session_state.selected_months = [m for m in st.session_state.selected_months 
                                                       if m not in months_by_year[year]]
                    st.rerun()
            
            for month in reversed(months_by_year[year]):  # Most recent month first within year
                is_selected = month in st.session_state.selected_months
                month_label = month.strftime("%B")
                
                # Count of records in this month
                month_count = len(valid_df_sidebar[valid_df_sidebar[month_col] == month])
                
                new_state = st.checkbox(
                    f"{month_label} ({month_count:,} records)",
                    value=is_selected,
                    key=f"month_{month.strftime('%Y%m')}"
                )
                
                # Update session state
                if new_state and month not in st.session_state.selected_months:
                    st.session_state.selected_months.append(month)
                elif not new_state and month in st.session_state.selected_months:
                    st.session_state.selected_months.remove(month)
    
    # Use selected months for filtering
    selected_months = st.session_state.selected_months
    if selected_months:
        start = min(selected_months)
        end = max(selected_months)
    else:
        # If no months selected or no valid data, use dummy dates
        if len(valid_df_sidebar) > 0:
            start, end = min_m, max_m
        else:
            # No valid data at all, use current date as dummy
            start = end = pd.Timestamp.now()

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
# Use the correct month column based on dashboard type
if dashboard_type == "FTD Dashboard":
    filter_month_col = "ftd_month"
    filter_date_col = df.attrs.get('ftd_date_col', 'portal - ftd_time')
else:
    filter_month_col = "kyc_month"
    filter_date_col = df.attrs.get('kyc_date_col', 'DATE_CREATED')

# Filter by selected months (not just range)
if selected_months:
    mask_time = df[filter_month_col].isin(selected_months)
else:
    mask_time = pd.Series(False, index=df.index)  # No months selected = no data

# Also filter out records with invalid dates for this dashboard
mask_valid_dates = df[filter_date_col].notna()

mask_source = df[source_col].isin(selected_sources) if selected_sources else pd.Series(True, index=df.index)
dff = df.loc[mask_time & mask_valid_dates & mask_source].copy()

# Also get data for ALL sources in the selected months (for active sources calculation)
dff_all_sources = df.loc[mask_time & mask_valid_dates].copy()

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
if len(dff) == 0:
    # No data after filtering - create empty dataframe with expected structure
    months = sorted(selected_months) if selected_months else []
    if group_sources:
        # Create empty dataframe for grouped sources
        display_sources = []
    else:
        display_sources = selected_sources
    
    # Create empty counts dataframe
    counts = pd.DataFrame(columns=["ftd_month", source_col, "clients"])
    if len(months) > 0 and len(display_sources) > 0:
        # Create structure with zero clients
        full = pd.MultiIndex.from_product([months, display_sources], names=["ftd_month", source_col]).to_frame(index=False)
        full["clients"] = 0
        counts = full
elif group_sources:
    # Add source category column
    dff['source_category'] = dff[source_col].apply(categorize_source)
    
    # Group by category instead of individual source
    counts = (
        dff.groupby([filter_month_col, "source_category"])["Record ID"].size().reset_index(name="clients")
    )
    counts.rename(columns={"source_category": source_col, filter_month_col: "month"}, inplace=True)
    
    # Get unique categories from selected sources
    selected_categories = dff['source_category'].unique().tolist()
    
    # Use only selected months, not a continuous range
    months = sorted(selected_months) if selected_months else []
    # Ensure all (month, category) combos exist
    if len(months) > 0 and len(selected_categories) > 0:
        full = (
            pd.MultiIndex.from_product([months, selected_categories], names=["month", source_col])
            .to_frame(index=False)
        )
        counts = (
            full.merge(counts, on=["month", source_col], how="left")
            .fillna({"clients": 0})
        )
    # Rename back for consistency
    counts.rename(columns={"month": "ftd_month"}, inplace=True)
    
    # Update selected_sources to be categories for display purposes
    display_sources = selected_categories
else:
    # Original aggregation by individual source
    counts = (
        dff.groupby([filter_month_col, source_col])["Record ID"].size().reset_index(name="clients")
    )
    # Rename month column for consistency
    counts.rename(columns={filter_month_col: "month"}, inplace=True)
    
    # Use only selected months, not a continuous range
    months = sorted(selected_months) if selected_months else []
    # Ensure all (month, source) combos exist for proper stacking/lines
    if len(months) > 0 and len(selected_sources) > 0:
        full = (
            pd.MultiIndex.from_product([months, selected_sources], names=["month", source_col])
            .to_frame(index=False)
        )
        counts = (
            full.merge(counts, on=["month", source_col], how="left")
            .fillna({"clients": 0})
        )
    # Rename back for consistency with rest of code
    counts.rename(columns={"month": "ftd_month"}, inplace=True)
    display_sources = selected_sources

# KPI row
total_clients = safe_int_convert(counts["clients"].sum() if len(counts) > 0 else 0)
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

k1.metric(f"Total {metric_name}", f"{total_clients:,}",
          help=f"Total {metric_name.lower()} from SELECTED sources only")
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
    
    # Calculate metrics safely
    latest_month = monthly_totals.iloc[-1]["clients"] if len(monthly_totals) > 0 else 0
    prev_month = monthly_totals.iloc[-2]["clients"] if len(monthly_totals) > 1 else 0
    mom_change = ((latest_month - prev_month) / prev_month * 100) if prev_month > 0 else 0
    
    # Safe calculation of best/worst months
    if len(monthly_totals) > 0 and not monthly_totals["clients"].empty:
        best_month = monthly_totals.loc[monthly_totals["clients"].idxmax()]
        worst_month = monthly_totals.loc[monthly_totals["clients"].idxmin()]
    else:
        # Create dummy data for display
        dummy_date = pd.Timestamp.now()
        best_month = {"clients": 0, "ftd_month": dummy_date}
        worst_month = {"clients": 0, "ftd_month": dummy_date}
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Latest Month", 
        f"{safe_int_convert(latest_month)} clients",
        f"{mom_change:+.1f}%" if mom_change != 0 else "0%"
    )
    m2.metric(
        "Best Month", 
        f"{safe_int_convert(best_month['clients'])} clients",
        f"{best_month['ftd_month']:%b %Y}"
    )
    m3.metric(
        "Worst Month", 
        f"{safe_int_convert(worst_month['clients'])} clients",
        f"{worst_month['ftd_month']:%b %Y}"
    )
    avg_growth = monthly_totals['mom_growth'].mean() if len(monthly_totals) > 0 else 0
    m4.metric(
        "Avg Growth",
        f"{avg_growth:.1f}%" if not pd.isna(avg_growth) else "0.0%",
        "month-over-month"
    )

# Chart
import altair as alt

alt.data_transformers.disable_max_rows()

# Prepare data for chart
chart_data = counts.copy()

# Debug info
if st.checkbox("Show debug info", value=False, key="debug_info"):
    st.write(f"Number of rows in chart_data: {len(chart_data)}")
    st.write(f"Display sources: {display_sources}")
    st.write(f"Show total: {show_total}")
    if not chart_data.empty:
        st.write("Chart data preview:")
        st.dataframe(chart_data.head())

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
        # Use default color scale for individual sources without total
        if len(display_sources) > 0:
            color_scale = alt.Scale(
                domain=display_sources,
                range=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"][:len(display_sources)]
            )
        else:
            color_scale = None

chart_base = alt.Chart(chart_data).encode(
    x=alt.X("ftd_month:T", 
            axis=alt.Axis(title="Month", format="%b %Y"),
            scale=alt.Scale(padding=20)),
    y=alt.Y("clients:Q", 
            axis=alt.Axis(title="Clients"), 
            stack=None if chart_type == "Line" else "zero"),
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
    if show_total and ("📊 TOTAL" in chart_data[source_col].values):
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
if not chart_data.empty:
    st.altair_chart(chart.properties(height=380).interactive(), use_container_width=True)
else:
    st.info("No data to display. Please select at least one source from the sidebar.")

# Pivot table
st.markdown("### Table: counts by month")
if group_sources:
    st.caption("📊 Data grouped by category (IB / Organic / Marketing)")

if len(counts) > 0:
    pivot = counts.pivot_table(index="ftd_month", columns=source_col, values="clients", fill_value=0).sort_index()

    # Add total column if more than one source/category
    if len(display_sources) > 1:
        pivot["📊 TOTAL"] = pivot.sum(axis=1)
    
    # Format the index to show month names (only if index is datetime)
    if len(pivot) > 0 and hasattr(pivot.index, 'strftime'):
        pivot.index = pivot.index.strftime("%b %Y")

    st.dataframe(pivot, width="stretch")
else:
    # Create empty pivot for export functionality
    pivot = pd.DataFrame()
    st.info("No data available to display in the table. Please check your filters and data quality.")

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
        
        # Debug info
        print(f"DEBUG: source={source}, max_val={max_val} (type: {type(max_val)}), min_val={min_val} (type: {type(min_val)})")
        
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
            "Total Clients": safe_int_convert(total),
            "Avg/Month": f"{avg:.1f}" if not pd.isna(avg) else "0.0",
            "Best Month": safe_int_convert(max_val),
            "Worst Month": safe_int_convert(min_val),
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

if not pivot.empty:
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
                "period": f"{min(months):%Y-%m-%d} to {max(months):%Y-%m-%d}" if len(months) > 0 else "No data",
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
else:
    st.info("📥 **No data to export.** Please check your filters and data quality.")

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