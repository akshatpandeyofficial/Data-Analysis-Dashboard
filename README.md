# Indian Stock Market Data Analysis Dashboard

**Streamlit data analysis dashboard** 

This version uses **live Indian stock-market data** from Yahoo Finance for popular NSE-listed companies, so the dashboard stays useful even after deployment.

## What this project shows

- Data collection from a public source
- Cleaning and transforming time-series data with Pandas
- KPI cards and interactive filters
- Moving averages, returns, volatility, and correlation analysis
- A ready-to-deploy Streamlit dashboard
- Auto-generated insights that you can explain in your viva / README

## Tech stack

- Python
- Pandas
- NumPy
- Plotly
- Streamlit
- yfinance

## Features

- Select 1–5 Indian stocks
- Choose any date range
- See latest close, period return, average volume, and volatility
- Analyze one stock in detail
- Compare normalized performance across multiple stocks
- View daily return distribution
- View monthly returns
- View return correlation heatmap
- Export filtered data as CSV
- Get 5 quick insights automatically

## Project structure

```text

├── app.py
├── README.md
└── .streamlit/
    └── config.toml
```

### 1. Problem statement
I built a data analysis dashboard for Indian stock-market data. The goal is to study price movement, risk, and performance of major Indian companies using live public data.

### 2. Dataset
The dashboard uses public stock data from Yahoo Finance for major NSE-listed companies such as Reliance, TCS, Infosys, HDFC Bank, and SBI.

### 3. Data preparation
I fetched the data, cleaned date columns, calculated daily returns, moving averages, monthly returns, and rolling volatility using Pandas.

### 4. Dashboard views
The dashboard includes KPI cards, price trend charts, return distribution, monthly performance, normalized comparison, and correlation heatmap.

### 5. Insights
The app automatically creates five insights based on the selected stock and date range, such as total return, strongest and weakest day, positive-day ratio, and volatility trend.

### 6. Learning outcome
This project demonstrates EDA, dashboard design, and business-style communication of data.

## Example points you can say in viva

- Daily return tells how much the stock changed from one trading day to the next.
- Moving average helps smooth short-term noise.
- Volatility shows the risk or instability in price movement.
- Correlation helps compare whether two stocks move similarly.
- Normalized performance makes different stock prices comparable on the same scale.

## Resume-friendly project description

Built a deployable Streamlit dashboard for Indian stock-market analysis using Pandas, NumPy, Plotly, and yfinance. Implemented KPI cards, moving averages, return analysis, volatility tracking, stock comparison, correlation heatmaps, and CSV export with interactive filters.

## Future improvements

- Add candlestick charts
- Add sector-wise grouping
- Add portfolio tracker
- Add news sentiment analysis
- Add downloadable PDF report
