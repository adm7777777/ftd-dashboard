# FTD Acquisition Dashboard

A Streamlit dashboard for tracking First Time Deposit (FTD) client acquisitions by month and source.

## Features

- 📊 Interactive charts (line and stacked bar)
- 🔍 Searchable source selection with scrollable list
- 📅 Quick date range selection (Last 3/6/12 months, YTD)
- 📈 Performance metrics and growth tracking
- 🏆 Source performance ranking
- 📋 Data quality report
- 💾 Multiple export formats (CSV, Excel, JSON)
- 🎯 Detailed hover tooltips

## Required Data Format

Your CSV must include these columns:
- `portal - ftd_time` - Date in DD/MM/YYYY format
- `portal - source_marketing_campaign` - Marketing source/campaign name

## Local Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the dashboard:
```bash
streamlit run ftd_dashboard.py
```

3. Upload your CSV file or place a `source.csv` file in the same directory

## Deployment

This app can be deployed to:
- **Streamlit Community Cloud** (recommended - free)
- **Heroku** 
- **Railway**
- **Google Cloud Run**
- **AWS EC2**

Note: This is a Streamlit app requiring Python runtime, so it cannot be deployed to static hosting services like Netlify.

## Live Demo

[Add your deployed URL here]
