# FTD Dashboard - Developer Handover

## Project Overview
Create a Streamlit dashboard to analyze First Time Deposit (FTD) data from HubSpot CRM exports. The dashboard should show monthly FTD acquisition trends by marketing source/campaign.

## Core Requirements

### Data Source
- **Input**: Excel files exported from HubSpot CRM
- **Expected format**: ~4,500 total records
- **Expected FTD count**: ~590 clients with actual deposits
- **Expected placeholder count**: ~3,941 clients with no deposit yet

### Key Columns Required
```
- Record ID: Unique client identifier
- portal - ftd_time: FTD date (CRITICAL - see data issues below)
- DATE_CREATED: KYC/registration date
- portal - source_marketing_campaign: Marketing source/campaign
- portal - country: Client country (optional)
- portal - made_a_deposit_: "Yes"/"No"/NULL flag for deposits
```

### Dashboard Features Needed
1. **Monthly FTD trend chart** (line/bar charts)
2. **Source filtering** (checkboxes with search)
3. **Date range filtering** (month selection)
4. **Key metrics**: Total FTDs, avg/month, active sources
5. **Source performance ranking**
6. **Export functionality** (CSV, Excel, JSON)
7. **Country filtering** (if country data available)

## CRITICAL DATA ISSUE - The Core Problem

### The Excel Date Problem
The `portal - ftd_time` column in the Excel file has a fundamental issue:

**Expected Data:**
- ~590 records: Real FTD dates (2023-2025 range)
- ~3,941 records: NULL/empty (no FTD yet)

**Actual Data in Excel:**
- ~590 records: Real FTD dates 
- ~3,941 records: **1970-01-01 placeholder dates**

### Root Cause
Excel is storing "no FTD" as **serial number 25569** which equals **1970-01-01**. This is NOT a real date - it's a placeholder for NULL.

**Critical Rule**: Any date with year 1970 = NULL (no FTD yet)

## Failed Attempts & Issues

### Issue #1: Excel Serial Number Handling
- **Problem**: Excel stores dates as serial numbers
- **Serial 25569** = 1970-01-01 = NULL placeholder
- **Serial >25569** = Real dates (e.g., 45919 = 2025-09-19)
- **Failed Fix**: Pandas auto-converts serials before we can detect them

### Issue #2: Pandas Auto-Conversion
- **Problem**: `pd.read_excel()` automatically converts dates
- **Result**: 1970 serials become Timestamp('1970-01-01') objects
- **Failed Fix**: Reading with `dtype=str` breaks other logic

### Issue #3: Column Name Issues
- **Problem**: Column names have quotes: `"'portal - ftd_time'"`
- **Result**: String matching fails
- **Partial Fix**: Dynamic column detection added but still problematic

### Issue #4: Date Parsing Logic
- **Problem**: Multiple parsing approaches conflict
- **Attempts**: Serial conversion, string parsing, deposit flag fallback
- **Result**: Either 0 FTDs shown or 4,516 FTDs (wrong count)

### Issue #5: Caching Issues
- **Problem**: Streamlit caches broken data processing
- **Result**: Changes don't take effect without manual cache clearing
- **Workaround**: Cache clear buttons added but unreliable

## Current State
- **Dashboard loads** but shows incorrect data
- **Detection works**: Correctly identifies 3,941 placeholders and 590 potential FTDs
- **Filtering fails**: Still shows 0 or 4,516 FTDs instead of 590
- **UI intact**: All dashboard features work except core data

## Recommended Solution for New Developer

### Approach 1: Clean Excel Import
```python
# Read Excel without date conversion
df = pd.read_excel(file, dtype={'portal - ftd_time': str})

# Handle the serial number issue
def convert_ftd_date(val):
    if pd.isna(val) or val == '':
        return pd.NaT
    
    # Try to convert to number (serial)
    try:
        serial = float(val)
        if serial == 25569:  # 1970-01-01 = NULL
            return pd.NaT
        if serial > 25569:  # Valid date
            return pd.to_datetime(serial, origin='1899-12-30', unit='D')
    except:
        pass
    
    # Try string parsing
    if '1970' in str(val):
        return pd.NaT
    
    return pd.to_datetime(val, errors='coerce', dayfirst=True)
```

### Approach 2: Use Deposit Flag as Ground Truth
```python
# Ignore dates entirely, use deposit flag
if 'portal - made_a_deposit_' in df.columns:
    # Only count records where made_a_deposit_ == 'Yes'
    ftd_clients = df[df['portal - made_a_deposit_'] == 'Yes']
    # Use DATE_CREATED as FTD date for these clients
```

### Approach 3: Raw Data Analysis First
```python
# Before any processing, examine raw Excel data
raw_df = pd.read_excel(file, dtype=str, nrows=100)
print("Raw FTD values:", raw_df['portal - ftd_time'].value_counts())

# Identify the pattern, then build parser accordingly
```

## Test Data Expectations
When working correctly, the dashboard should show:
- **Total FTD Clients**: 590 (not 0, not 4,516)
- **Date Range**: May 2023 - Sep 2025
- **Monthly data**: Distributed across multiple months
- **Sources**: 88 unique sources with varying FTD counts

## Files to Replace/Rebuild
- `ftd_dashboard.py` - Main dashboard (completely rebuild)
- Keep: `requirements.txt`, `README.md`, other docs

## Current Codebase Status: BROKEN
The current `ftd_dashboard.py` has multiple failed fix attempts layered on top of each other. **Recommend starting fresh** rather than trying to fix the existing code.

## Repository
- GitHub: https://github.com/adm7777777/ftd-dashboard.git
- Deploy: Streamlit Cloud (auto-deploys from main branch)
- Password: "OQ123" (hardcoded in app)

---

**Bottom Line**: The core issue is Excel serial number 25569 (1970-01-01) being treated as a real date instead of NULL. Fix this, and the dashboard will work correctly.
