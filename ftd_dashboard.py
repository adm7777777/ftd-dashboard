#!/usr/bin/env python3
"""
FTD Dashboard - Fixed Version
Properly handles Excel serial number 25569 as NULL placeholder
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime
import io

# Page config
st.set_page_config(page_title="FTD Acquisition Dashboard", layout="wide")

# Password protection
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("## 🔒 Authentication Required")
        password = st.text_input("Enter password:", type="password")
        if st.button("Login"):
            if password == "OQ123":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return st.session_state.password_correct

if not check_password():
    st.stop()

st.title("FTD Acquisition Dashboard")
st.caption("Fixed Excel serial number handling - Serial 25569 (1970-01-01) = NULL placeholder")

# File uploader
uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx'])

def convert_excel_serial_to_date(serial_value):
    """
    Convert Excel serial number to proper date
    CRITICAL: 25569 = 1970-01-01 = NULL placeholder (not a real date)
    """
    if pd.isna(serial_value) or serial_value is None:
        return pd.NaT
    
    try:
        serial_num = float(serial_value)
        
        # CRITICAL: 25569 is Excel's representation of 1970-01-01 
        # This is used as a placeholder for "no FTD date" - treat as NULL
        if serial_num == 25569 or serial_num == 0:
            return pd.NaT
        
        # Only convert serials > 25569 (post-1970 dates)
        if serial_num > 25569:
            # Excel epoch: December 30, 1899
            date_val = pd.to_datetime(serial_num, origin='1899-12-30', unit='D')
            return date_val
        else:
            # Invalid/placeholder serial
            return pd.NaT
            
    except (ValueError, TypeError, OverflowError):
        return pd.NaT

@st.cache_data
def load_and_process_data(file):
    """Load Excel file and properly handle serial dates"""
    
    # Read Excel file without auto-converting dates
    df = pd.read_excel(file, keep_default_na=False, na_values=['', 'None', 'null'])
    
    st.write("### 🔍 Raw Data Analysis")
    st.write(f"**Total records loaded:** {len(df):,}")
    
    # Show raw FTD column data
    ftd_col = 'portal - ftd_time'
    if ftd_col in df.columns:
        raw_ftd = df[ftd_col].copy()
        
        # Analyze raw values
        st.write(f"**Raw FTD column type:** {raw_ftd.dtype}")
        st.write("**First 10 raw values:**")
        for i, val in enumerate(raw_ftd.head(10)):
            st.text(f"  Row {i+1}: {repr(val)} (type: {type(val).__name__})")
        
        # Count serial 25569 (placeholder)
        if raw_ftd.dtype in ['int64', 'float64', 'object']:
            try:
                numeric_vals = pd.to_numeric(raw_ftd, errors='coerce')
                placeholder_count = (numeric_vals == 25569).sum()
                valid_serial_count = (numeric_vals > 25569).sum()
                
                st.write(f"**Serial 25569 (NULL placeholder):** {placeholder_count:,}")
                st.write(f"**Valid serials (>25569):** {valid_serial_count:,}")
                
                # Show sample conversions
                if valid_serial_count > 0:
                    st.write("**Sample serial → date conversions:**")
                    valid_serials = numeric_vals[numeric_vals > 25569].head(5)
                    for serial in valid_serials:
                        if not pd.isna(serial):
                            date_val = convert_excel_serial_to_date(serial)
                            st.text(f"  Serial {int(serial)} → {date_val}")
            except Exception as e:
                st.error(f"Error analyzing serials: {e}")
        
        # Convert FTD dates
        st.write("**Converting FTD dates...**")
        df[ftd_col] = raw_ftd.apply(convert_excel_serial_to_date)
        
        # Post-conversion analysis
        valid_ftd_count = df[ftd_col].notna().sum()
        null_ftd_count = df[ftd_col].isna().sum()
        
        st.write(f"**✅ Valid FTD dates after conversion:** {valid_ftd_count:,}")
        st.write(f"**📝 NULL FTD dates (no deposit yet):** {null_ftd_count:,}")
        
        if valid_ftd_count > 0:
            date_range = f"{df[ftd_col].min():%Y-%m-%d} to {df[ftd_col].max():%Y-%m-%d}"
            st.write(f"**📅 FTD date range:** {date_range}")
    
    # Handle other required columns
    source_col = 'portal - source_marketing_campaign'
    kyc_col = 'DATE_CREATED'
    
    # Fill missing sources
    if source_col in df.columns:
        df[source_col] = df[source_col].fillna("(Unknown)")
        source_count = df[source_col].nunique()
        st.write(f"**📊 Unique sources:** {source_count:,}")
    
    # Process KYC dates
    if kyc_col in df.columns:
        df[kyc_col] = pd.to_datetime(df[kyc_col], errors='coerce', dayfirst=True)
        valid_kyc = df[kyc_col].notna().sum()
        st.write(f"**✅ Valid KYC dates:** {valid_kyc:,}")
    
    # Create month columns
    df['ftd_month'] = df[ftd_col].dt.to_period('M').dt.to_timestamp()
    df['kyc_month'] = df[kyc_col].dt.to_period('M').dt.to_timestamp()
    
    return df

if uploaded_file:
    try:
        df = load_and_process_data(uploaded_file)
        
        # Dashboard content
        st.markdown("---")
        st.markdown("## 📊 Dashboard")
        
        # Filter to records with valid FTD dates
        ftd_data = df[df['portal - ftd_time'].notna()].copy()
        
        if len(ftd_data) == 0:
            st.warning("No valid FTD dates found in the data.")
        else:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total FTD Clients", f"{len(ftd_data):,}")
            
            with col2:
                st.metric("Date Range", f"{ftd_data['portal - ftd_time'].min():%b %Y} - {ftd_data['portal - ftd_time'].max():%b %Y}")
            
            with col3:
                unique_sources = ftd_data['portal - source_marketing_campaign'].nunique()
                st.metric("Active Sources", f"{unique_sources:,}")
            
            with col4:
                months_span = ftd_data['ftd_month'].nunique()
                st.metric("Months Covered", f"{months_span}")
            
            # Monthly trend chart
            st.markdown("### 📈 Monthly FTD Trend")
            
            monthly_counts = ftd_data.groupby('ftd_month').size().reset_index(name='FTD_Count')
            monthly_counts['Month'] = monthly_counts['ftd_month'].dt.strftime('%b %Y')
            
            chart = alt.Chart(monthly_counts).mark_line(point=True).encode(
                x=alt.X('ftd_month:T', axis=alt.Axis(title='Month', format='%b %Y')),
                y=alt.Y('FTD_Count:Q', axis=alt.Axis(title='FTD Clients')),
                tooltip=['Month:N', 'FTD_Count:Q']
            ).properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
            
            # Top sources table
            st.markdown("### 🏆 Top Sources")
            
            source_counts = ftd_data.groupby('portal - source_marketing_campaign').size().reset_index(name='FTD_Count')
            source_counts = source_counts.sort_values('FTD_Count', ascending=False).head(10)
            
            st.dataframe(source_counts, hide_index=True, use_container_width=True)
            
            # Monthly breakdown table
            st.markdown("### 📋 Monthly Breakdown")
            
            monthly_table = ftd_data.groupby([
                ftd_data['ftd_month'].dt.strftime('%b %Y'),
                'portal - source_marketing_campaign'
            ]).size().reset_index(name='Count')
            
            pivot_table = monthly_table.pivot(
                index='portal - source_marketing_campaign',
                columns='ftd_month',
                values='Count'
            ).fillna(0).astype(int)
            
            st.dataframe(pivot_table, use_container_width=True)
            
            # Export data
            st.markdown("### 💾 Export Data")
            
            csv_data = ftd_data.to_csv(index=False)
            st.download_button(
                "📄 Download FTD Data (CSV)",
                data=csv_data,
                file_name=f"ftd_data_{datetime.now():%Y%m%d}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.exception(e)

else:
    st.info("👆 Please upload an Excel file to get started")
    
    st.markdown("### 📋 Expected Excel Format")
    st.markdown("""
    Your Excel file should contain these columns:
    - **portal - ftd_time**: FTD dates (Excel serial numbers)
    - **DATE_CREATED**: KYC dates 
    - **portal - source_marketing_campaign**: Source/campaign names
    - **Record ID**: Unique identifier for each client
    
    **Key Fix:** Serial number 25569 (1970-01-01) will be treated as NULL (no FTD), not as a real date.
    """)

# Footer
st.markdown("---")
st.caption("🔧 **Rebuilt Dashboard** - Fixed Excel serial 25569 = NULL handling")
