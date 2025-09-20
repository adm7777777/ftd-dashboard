# FTD Dashboard - Unresolved Issues Log

## Critical Issue: Wrong FTD Count
**Status**: UNRESOLVED
**Expected**: 590 FTD clients
**Actual**: Shows 0 or 4,516
**Root Cause**: Excel serial number 25569 (1970-01-01) not properly handled as NULL

## Issue #1: Excel Date Import
**Problem**: Excel stores "no FTD" as serial 25569 (1970-01-01)
**Impact**: 3,941 placeholder dates treated as real dates
**Attempts**: 
- Read as strings → broke other logic
- Serial number conversion → pandas auto-converts first
- Manual date parsing → inconsistent results
**Status**: FAILED

## Issue #2: Pandas Auto-Conversion
**Problem**: `pd.read_excel()` converts serials to dates before our code sees them
**Impact**: Can't detect original serial numbers
**Attempts**:
- `keep_default_na=False` → didn't help
- `dtype=str` → broke downstream processing
- Multiple read approaches → inconsistent
**Status**: FAILED

## Issue #3: Column Name Parsing
**Problem**: Column names have nested quotes: `"'portal - ftd_time'"`
**Impact**: String matching fails
**Attempts**:
- Strip quotes → partial fix
- Dynamic column detection → still issues
- Case-insensitive matching → works but inconsistent
**Status**: PARTIALLY FIXED

## Issue #4: Date Detection vs Filtering
**Problem**: Detection works (finds 3,941 + 590) but filtering fails
**Impact**: Dashboard shows wrong counts
**Evidence**: 
- Debug shows correct detection
- UI shows wrong metrics
- Data processing pipeline broken somewhere
**Attempts**:
- Multiple parsing functions
- Deposit flag fallback
- Emergency year filtering
**Status**: FAILED

## Issue #5: Streamlit Caching
**Problem**: Changes don't take effect due to caching
**Impact**: Hard to test fixes
**Attempts**:
- Cache clear buttons
- `@st.cache_data` modifications
- Manual cache clearing
**Status**: WORKAROUND ONLY

## Issue #6: Multiple Fix Attempts
**Problem**: Layered multiple failed approaches
**Impact**: Code became unmaintainable
**Result**: 
- Complex, conflicting logic
- Hard to debug
- Unreliable behavior
**Status**: CODEBASE CORRUPTED

## Data Quality Evidence
**From working detection logic**:
```
Total records: 4,531
Placeholder dates (1970-01-01): 3,941
Potential FTD records: 590
```

**From UI (wrong)**:
```
Total FTD Clients: 0
With FTD: 4,516
No FTD Yet: 3,941
```

## Console Debug Output (Last Known)
```
📊 Processing FTD dates from 'portal - ftd_time':
  Column dtype: datetime64[ns]
  Non-null values: 4516
  First 10 raw values:
    Row 1: Timestamp('2025-09-19 00:00:00') (type: Timestamp, year: 2025)
    Row 2: NaT (type: NaTType)
    [... more NaT values ...]
```

**Analysis**: Shows 4,516 non-null values when should be 590. The 1970 dates are being kept as valid timestamps.

## Failed Code Patterns
1. **Serial Number Detection**: `if serial == 25569` → Never triggered
2. **Year Filtering**: `if val.year == 1970` → 1970 dates already converted
3. **Deposit Flag**: Column name issues prevented proper filtering
4. **Emergency Fixes**: Added complexity without solving root cause

## Recommended Next Steps
1. **Start fresh** - don't try to fix existing code
2. **Focus on Excel import** - solve the 25569 serial issue first
3. **Test with minimal code** - verify date parsing before building UI
4. **Use deposit flag** as ground truth if date parsing fails
5. **Single approach** - don't layer multiple fixes

## Test Files Available
- Sample Excel file with 4,531 records
- Known good data structure
- Clear expected outcomes for validation

## Environment
- Python 3.13
- Streamlit (latest)
- Pandas (latest)
- Deployed on Streamlit Cloud
- Auto-deploys from GitHub main branch

---

**Summary**: The core Excel import issue was never properly resolved. All subsequent fixes were band-aids that created more complexity without solving the fundamental problem.
