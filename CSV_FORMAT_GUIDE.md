# FTD Dashboard - CSV Format Guide

## Overview
This guide explains the required CSV format for the FTD Acquisition Dashboard. The dashboard analyzes First Time Depositor (FTD) data by source and time period.

## Required Fields

Your CSV file **MUST** contain these three columns with exact names (including spaces):

### 1. `portal - ftd_time`
- **Purpose**: The date when the client became an FTD
- **Format**: DD/MM/YYYY (e.g., "25/08/2024", "01/12/2024")
- **Required**: Yes
- **Notes**: 
  - Must be a valid date in DD/MM/YYYY format
  - Invalid dates will be dropped from analysis
  - This is the primary date field for all time-based analysis

### 2. `portal - source_marketing_campaign`
- **Purpose**: Identifies the source/campaign that brought the client
- **Format**: Text string
- **Required**: Yes
- **Examples**:
  - "Google_Campaign_Q1_2024"
  - "IB_Partner_John"
  - "Facebook_Ads_Summer"
  - "" (empty/null for organic traffic)
- **Notes**:
  - Empty values will be labeled as "(Unknown)" and treated as Organic
  - Used for grouping and filtering in the dashboard

### 3. `Record ID`
- **Purpose**: Unique identifier for each client/record
- **Format**: Any unique value (number or text)
- **Required**: Yes
- **Examples**: "1001", "CL_2024_001", "ABC123"
- **Notes**: Used for counting unique clients

## Source Grouping Logic

When the "Group Sources by Type" option is enabled, sources are automatically categorized:

- **🏦 IB Sources**: Any source containing "IB" in the name (case-insensitive)
- **🌱 Organic**: Sources that are empty, null, or "(Unknown)"
- **📢 Marketing**: All other sources (campaigns, ads, etc.)

## Example CSV Structure

```csv
Record ID,portal - ftd_time,portal - source_marketing_campaign,Other_Field_1,Other_Field_2
1001,15/01/2024,Google_Campaign_Q1,optional_data,optional_data
1002,16/01/2024,IB_Partner_John,optional_data,optional_data
1003,17/01/2024,,optional_data,optional_data
1004,18/02/2024,Facebook_Ads_2024,optional_data,optional_data
1005,19/02/2024,IB_Sarah_Team,optional_data,optional_data
```

## Important Notes

### ✅ Column Names Must Match Exactly
- Correct: `portal - ftd_time` (with spaces)
- Wrong: `portal-ftd_time` (without spaces)
- Wrong: `Portal - FTD_Time` (different capitalization)

### ✅ Date Format
- The system expects DD/MM/YYYY format
- Dates in other formats (MM/DD/YYYY, YYYY-MM-DD) may be misinterpreted
- Invalid dates will be dropped and reported in the Data Quality Report

### ✅ Each Row = One Client
- Each row represents one unique FTD client
- The dashboard counts unique records per month per source
- Duplicate Record IDs may cause incorrect counts

### ✅ Optional Fields
- Your CSV can contain additional columns
- Extra columns will be ignored but won't cause errors
- Only the three required fields are used for analysis

## Common Issues & Solutions

### Issue: "CSV is missing required columns"
**Solution**: Ensure your column names match exactly as shown above, including spaces and capitalization.

### Issue: Dates not parsing correctly
**Solution**: 
- Use DD/MM/YYYY format (e.g., 25/12/2024)
- Check the Data Quality Report to see how many dates were dropped
- Review sample parsed dates shown in the report

### Issue: Sources showing as "(Unknown)"
**Explanation**: This happens when the source field is empty or null. These are treated as Organic traffic.

### Issue: No data showing in chart
**Check**:
1. Date range filter - ensure it covers your data period
2. Source selection - ensure sources are selected in the sidebar
3. Data Quality Report - check for parsing issues

## Dashboard Features

### Filtering Options
- **Date Range**: Filter by specific time periods
- **Source Selection**: Choose specific sources to analyze
- **Group by Type**: Aggregate sources into IB/Organic/Marketing categories

### Available Charts
- Line charts for trend analysis
- Stacked bar charts for composition analysis
- Total line overlay option
- Monthly data tables

### Export Options
- CSV export of filtered data
- Excel export with multiple sheets
- JSON export for programmatic use

## Sample Template

A sample CSV template is available for download directly from the dashboard. Look for the "📥 Download Sample CSV Template" button in the CSV Format Guide section.

## Support

If you encounter issues:
1. Check the Data Quality Report for specific errors
2. Verify your CSV format matches this guide
3. Ensure dates are in DD/MM/YYYY format
4. Confirm column names match exactly

---

*Last Updated: September 2025*
*Dashboard Version: 1.0*

