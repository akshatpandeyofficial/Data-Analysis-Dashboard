import io
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# -------------------- PAGE SETUP --------------------
st.set_page_config(
    page_title="Indian Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
)

# -------------------- STOCK MASTER --------------------
NSE_SYMBOLS = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "ITC": "ITC.NS",
    "Larsen & Toubro": "LT.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Axis Bank": "AXISBANK.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Wipro": "WIPRO.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "Titan Company": "TITAN.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "NTPC": "NTPC.NS",
    "Power Grid": "POWERGRID.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Nestle India": "NESTLEIND.NS",
    "Bajaj Auto": "BAJAJ-AUTO.NS",
    "IndusInd Bank": "INDUSINDBK.NS",
    "Tech Mahindra": "TECHM.NS",
    "JSW Steel": "JSWSTEEL.NS",
    "Mahindra & Mahindra": "M&M.NS",
}

SECTOR_MAP = {
    "RELIANCE.NS": "Energy",
    "TCS.NS": "IT",
    "INFY.NS": "IT",
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "SBIN.NS": "Banking",
    "ITC.NS": "FMCG",
    "LT.NS": "Infrastructure",
    "HINDUNILVR.NS": "FMCG",
    "BHARTIARTL.NS": "Telecom",
    "AXISBANK.NS": "Banking",
    "MARUTI.NS": "Automobile",
    "BAJFINANCE.NS": "Financial Services",
    "KOTAKBANK.NS": "Banking",
    "HCLTECH.NS": "IT",
    "WIPRO.NS": "IT",
    "ASIANPAINT.NS": "FMCG",
    "TITAN.NS": "Consumer",
    "SUNPHARMA.NS": "Pharma",
    "NTPC.NS": "Power",
    "POWERGRID.NS": "Power",
    "ULTRACEMCO.NS": "Cement",
    "TATAMOTORS.NS": "Automobile",
    "ADANIENT.NS": "Conglomerate",
    "NESTLEIND.NS": "FMCG",
    "BAJAJ-AUTO.NS": "Automobile",
    "INDUSINDBK.NS": "Banking",
    "TECHM.NS": "IT",
    "JSWSTEEL.NS": "Metals",
    "M&M.NS": "Automobile",
}

PERIOD_OPTIONS = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "3 Years": "3y",
    "5 Years": "5y",
}

# -------------------- HELPERS --------------------
def format_pct(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"

def format_inr(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"₹{value:,.2f}"

def market_status_ist():
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    weekday = now_ist.weekday()
    current_minutes = now_ist.hour * 60 + now_ist.minute
    open_minutes = 9 * 60 + 15
    close_minutes = 15 * 60 + 30

    is_open = weekday < 5 and open_minutes <= current_minutes <= close_minutes
    status = "Market Open" if is_open else "Market Closed"
    return status, now_ist

@st.cache_data(show_spinner=False, ttl=600)
def load_historical_data(symbols, period):
    frames = []

    for symbol in symbols:
        df = yf.download(
            symbol,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df.empty:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        df = df.reset_index()

        if "Date" not in df.columns:
            df = df.rename(columns={df.columns[0]: "Date"})

        keep_cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in df.columns]
        df = df[keep_cols].copy()

        df["Symbol"] = symbol
        df["Company"] = next((k for k, v in NSE_SYMBOLS.items() if v == symbol), symbol)
        df["Sector"] = SECTOR_MAP.get(symbol, "Other")
        frames.append(df)

    if not frames:
        return pd.DataFrame(), pd.DataFrame()

    data = pd.concat(frames, ignore_index=True)
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.sort_values(["Symbol", "Date"]).reset_index(drop=True)

    data["Daily Return %"] = data.groupby("Symbol")["Close"].pct_change() * 100
    data["SMA 20"] = data.groupby("Symbol")["Close"].transform(lambda s: s.rolling(20).mean())
    data["SMA 50"] = data.groupby("Symbol")["Close"].transform(lambda s: s.rolling(50).mean())
    data["Month"] = data["Date"].dt.to_period("M").dt.to_timestamp()

    monthly_close = (
        data.groupby(["Company", "Month"], as_index=False)["Close"]
        .last()
        .sort_values(["Company", "Month"])
    )
    monthly_close["Monthly Return %"] = monthly_close.groupby("Company")["Close"].pct_change() * 100

    return data, monthly_close

@st.cache_data(show_spinner=False, ttl=60)
def load_live_snapshot(symbols):
    rows = []

    for symbol in symbols:
        company = next((k for k, v in NSE_SYMBOLS.items() if v == symbol), symbol)
        sector = SECTOR_MAP.get(symbol, "Other")

        try:
            ticker = yf.Ticker(symbol)

            intraday = ticker.history(period="2d", interval="1m", auto_adjust=False)
            daily = ticker.history(period="5d", interval="1d", auto_adjust=False)

            if intraday.empty and daily.empty:
                continue

            if not intraday.empty:
                last_price = float(intraday["Close"].dropna().iloc[-1])
                last_time = intraday.index[-1]
            else:
                last_price = float(daily["Close"].dropna().iloc[-1])
                last_time = daily.index[-1]

            if len(daily.dropna(subset=["Close"])) >= 2:
                prev_close = float(daily["Close"].dropna().iloc[-2])
            else:
                prev_close = np.nan

            change = last_price - prev_close if pd.notna(prev_close) else np.nan
            change_pct = ((last_price / prev_close) - 1) * 100 if pd.notna(prev_close) and prev_close != 0 else np.nan

            rows.append(
                {
                    "Company": company,
                    "Symbol": symbol,
                    "Sector": sector,
                    "Live Price": last_price,
                    "Prev Close": prev_close,
                    "Change": change,
                    "Change %": change_pct,
                    "Last Updated": pd.to_datetime(last_time),
                }
            )
        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    live_df = pd.DataFrame(rows).sort_values("Change %", ascending=False).reset_index(drop=True)
    return live_df

@st.cache_data(show_spinner=False, ttl=20)
def load_live_intraday(symbol):
    try:
        ticker = yf.Ticker(symbol)
        live_df = ticker.history(period="1d", interval="1m", auto_adjust=False)

        if live_df.empty:
            return pd.DataFrame()

        live_df = live_df.reset_index()

        if "Datetime" not in live_df.columns:
            live_df = live_df.rename(columns={live_df.columns[0]: "Datetime"})

        live_df["Datetime"] = pd.to_datetime(live_df["Datetime"])
        return live_df

    except Exception:
        return pd.DataFrame()

def build_summary(stock_df: pd.DataFrame, monthly_df: pd.DataFrame):
    stock_df = stock_df.dropna(subset=["Close"]).copy()
    if stock_df.empty:
        return None

    latest_close = float(stock_df["Close"].iloc[-1])
    first_close = float(stock_df["Close"].iloc[0])
    period_return = ((latest_close / first_close) - 1) * 100 if first_close else np.nan

    latest_daily_return = float(stock_df["Daily Return %"].iloc[-1]) if stock_df["Daily Return %"].notna().any() else np.nan
    high_price = float(stock_df["High"].max()) if "High" in stock_df.columns else np.nan
    low_price = float(stock_df["Low"].min()) if "Low" in stock_df.columns else np.nan
    avg_volume = float(stock_df["Volume"].mean()) if "Volume" in stock_df.columns else np.nan

    latest_monthly_return = np.nan
    monthly_df = monthly_df.dropna(subset=["Monthly Return %"])
    if not monthly_df.empty:
        latest_monthly_return = float(monthly_df["Monthly Return %"].iloc[-1])

    return {
        "latest_close": latest_close,
        "period_return": period_return,
        "latest_daily_return": latest_daily_return,
        "latest_monthly_return": latest_monthly_return,
        "high": high_price,
        "low": low_price,
        "avg_volume": avg_volume,
    }

def generate_insights(stock_df: pd.DataFrame, company_name: str):
    insights = []
    clean = stock_df.dropna(subset=["Close"]).copy()

    if clean.empty:
        return ["No data available for this stock in the selected range."]

    latest = clean.iloc[-1]
    first = clean.iloc[0]
    period_return = ((latest["Close"] / first["Close"]) - 1) * 100 if first["Close"] else np.nan
    insights.append(f"{company_name} moved {period_return:.2f}% in the selected period.")

    if pd.notna(latest.get("SMA 20")) and pd.notna(latest.get("SMA 50")):
        if latest["SMA 20"] > latest["SMA 50"]:
            insights.append("Short-term trend is stronger because SMA 20 is above SMA 50.")
        else:
            insights.append("Short-term trend is softer because SMA 20 is below SMA 50.")

    if clean["Daily Return %"].notna().sum() > 5:
        best_day = clean.loc[clean["Daily Return %"].idxmax()]
        worst_day = clean.loc[clean["Daily Return %"].idxmin()]
        insights.append(
            f"Best day: {best_day['Date'].date()} ({best_day['Daily Return %']:.2f}%). "
            f"Worst day: {worst_day['Date'].date()} ({worst_day['Daily Return %']:.2f}%)."
        )

    positive_ratio = (clean["Daily Return %"] > 0).mean() * 100
    insights.append(f"It closed positive on {positive_ratio:.1f}% of trading sessions.")

    return insights[:4]

# -------------------- TITLE --------------------
market_text, now_ist = market_status_ist()

st.title("📈 Indian Stock Market Dashboard")
st.caption(" Dashboard for Indian stocks with live fluctuation and separate multiple-stock comparison.")

top_a, top_b, top_c = st.columns([1.7, 1.2, 1.1])

with top_a:
    selected_company = st.selectbox(
        "Select one Indian stock for full analysis",
        options=list(NSE_SYMBOLS.keys()),
        index=0,
    )

with top_b:
    selected_period_label = st.selectbox(
        "Analysis range",
        options=list(PERIOD_OPTIONS.keys()),
        index=3,
    )
    selected_period = PERIOD_OPTIONS[selected_period_label]

with top_c:
    show_sma = st.checkbox("Show SMA 20 / SMA 50", value=True)
    st.markdown(
        f"""
        <div style="padding:10px 14px;border-radius:14px;background:#0f172a;color:white;margin-top:8px;">
            <div style="font-size:14px;font-weight:600;">{market_text}</div>
            <div style="font-size:12px;opacity:0.8;">IST: {now_ist.strftime('%d %b %Y, %I:%M %p')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### Compare Multiple Stocks")
comparison_names = st.multiselect(
    "Select stocks for comparison charts",
    options=list(NSE_SYMBOLS.keys()),
    default=[selected_company, "TCS", "Infosys"] if selected_company not in ["TCS", "Infosys"] else [selected_company, "Reliance Industries", "HDFC Bank"],
    max_selections=8,
)

if selected_company not in comparison_names:
    comparison_names = [selected_company] + comparison_names

comparison_names = list(dict.fromkeys(comparison_names))

# -------------------- AUTO REFRESH --------------------
refresh_count = st_autorefresh(interval=20000, key="live_refresh")

all_selected_names = comparison_names
symbols = [NSE_SYMBOLS[name] for name in all_selected_names]

with st.spinner("Fetching Indian market data..."):
    historical_data, monthly_data = load_historical_data(tuple(symbols), selected_period)
    live_data = load_live_snapshot(tuple(symbols))

if historical_data.empty:
    st.error("No data found for the selected stocks.")
    st.stop()

selected_symbol = NSE_SYMBOLS[selected_company]
stock_df = historical_data[historical_data["Symbol"] == selected_symbol].copy()
stock_monthly_df = monthly_data[monthly_data["Company"] == selected_company].copy()
summary = build_summary(stock_df, stock_monthly_df)

# -------------------- LIVE WATCHLIST --------------------
st.subheader("Live / Current Price Watchlist")

if live_data.empty:
    st.info("Live/current snapshot could not be loaded right now. Historical analysis is still available below.")
else:
    live_cols = st.columns(min(4, len(live_data)))

    for idx, (_, row) in enumerate(live_data.head(4).iterrows()):
        with live_cols[idx % len(live_cols)]:
            delta_text = f"{row['Change']:.2f} ({row['Change %']:.2f}%)" if pd.notna(row["Change %"]) else "N/A"
            st.metric(
                label=row["Company"],
                value=format_inr(row["Live Price"]),
                delta=delta_text,
            )
            st.caption(f"{row['Sector']} • {row['Symbol']}")

    with st.expander("View full live/current price table", expanded=False):
        live_view = live_data.copy()
        live_view["Live Price"] = live_view["Live Price"].map(lambda x: round(x, 2))
        live_view["Prev Close"] = live_view["Prev Close"].map(lambda x: round(x, 2) if pd.notna(x) else np.nan)
        live_view["Change"] = live_view["Change"].map(lambda x: round(x, 2) if pd.notna(x) else np.nan)
        live_view["Change %"] = live_view["Change %"].map(lambda x: round(x, 2) if pd.notna(x) else np.nan)
        live_view["Last Updated"] = live_view["Last Updated"].dt.strftime("%d-%m-%Y %I:%M %p")
        st.dataframe(live_view, use_container_width=True, hide_index=True)

# -------------------- LIVE FLUCTUATION FOR SELECTED STOCK --------------------
st.subheader(f"Live Fluctuation: {selected_company}")

live_intraday_df = load_live_intraday(selected_symbol)

if live_intraday_df.empty:
    st.info("Live intraday data is not available right now.")
else:
    latest_live = float(live_intraday_df["Close"].iloc[-1])
    open_live = float(live_intraday_df["Open"].iloc[0])
    high_live = float(live_intraday_df["High"].max())
    low_live = float(live_intraday_df["Low"].min())
    live_change = latest_live - open_live
    live_change_pct = ((latest_live / open_live) - 1) * 100 if open_live != 0 else np.nan

    l1, l2, l3, l4 = st.columns(4)
    l1.metric("Live Price", format_inr(latest_live), f"{live_change:.2f} ({live_change_pct:.2f}%)")
    l2.metric("Day Open", format_inr(open_live))
    l3.metric("Day High", format_inr(high_live))
    l4.metric("Day Low", format_inr(low_live))

    fig_live = go.Figure()
    fig_live.add_trace(
        go.Scatter(
            x=live_intraday_df["Datetime"],
            y=live_intraday_df["Close"],
            mode="lines",
            name="Live Price",
            line=dict(width=3),
        )
    )

    fig_live.update_layout(
        title=f"{selected_company} Live Price Movement",
        xaxis_title="Time",
        yaxis_title="Price (₹)",
        height=420,
    )
    st.plotly_chart(fig_live, use_container_width=True)

    last_point = live_intraday_df["Datetime"].iloc[-1]
    st.caption(f"Auto-refresh active every 20 seconds • latest data point: {last_point}")

# -------------------- SINGLE STOCK DETAILED ANALYSIS --------------------
st.subheader(f"Detailed Analysis: {selected_company}")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Latest Close", format_inr(summary["latest_close"]))
m2.metric("Range Return", format_pct(summary["period_return"]))
m3.metric("Latest Daily Return", format_pct(summary["latest_daily_return"]))
m4.metric("Latest Monthly Return", format_pct(summary["latest_monthly_return"]))
m5.metric("Average Volume", f"{summary['avg_volume']:,.0f}" if pd.notna(summary["avg_volume"]) else "N/A")

info1, info2 = st.columns(2)
with info1:
    st.info(f"Selected range low: {format_inr(summary['low'])}")
with info2:
    st.info(f"Selected range high: {format_inr(summary['high'])}")

chart_left, chart_right = st.columns([2.1, 1])

with chart_left:
    fig_price = go.Figure()
    fig_price.add_trace(
        go.Scatter(
            x=stock_df["Date"],
            y=stock_df["Close"],
            mode="lines",
            name="Close Price",
            line=dict(width=3),
        )
    )

    if show_sma:
        fig_price.add_trace(
            go.Scatter(
                x=stock_df["Date"],
                y=stock_df["SMA 20"],
                mode="lines",
                name="SMA 20",
            )
        )
        fig_price.add_trace(
            go.Scatter(
                x=stock_df["Date"],
                y=stock_df["SMA 50"],
                mode="lines",
                name="SMA 50",
            )
        )

    fig_price.update_layout(
        title=f"{selected_company} Historical Price Trend",
        xaxis_title="Trading Date",
        yaxis_title="Price (₹)",
        height=430,
        legend_title="Series",
    )
    st.plotly_chart(fig_price, use_container_width=True)

with chart_right:
    st.markdown("### Quick Insights")
    for i, insight in enumerate(generate_insights(stock_df, selected_company), start=1):
        st.markdown(f"**{i}.** {insight}")

# -------------------- DAILY + MONTHLY RETURNS --------------------
ret_left, ret_right = st.columns(2)

with ret_left:
    daily_returns_df = stock_df.dropna(subset=["Daily Return %"]).copy()
    fig_daily = px.line(
        daily_returns_df,
        x="Date",
        y="Daily Return %",
        title=f"{selected_company} Daily Return %",
    )
    fig_daily.update_layout(height=380, yaxis_title="Daily Return %")
    st.plotly_chart(fig_daily, use_container_width=True)

with ret_right:
    fig_monthly = px.bar(
        stock_monthly_df.dropna(subset=["Monthly Return %"]),
        x="Month",
        y="Monthly Return %",
        title=f"{selected_company} Monthly Return %",
    )
    fig_monthly.update_layout(height=380, yaxis_title="Monthly Return %")
    st.plotly_chart(fig_monthly, use_container_width=True)

# -------------------- MULTI-STOCK COMPARISON --------------------
st.subheader("Multiple Stock Comparison")

comparison_df = historical_data[historical_data["Company"].isin(comparison_names)][["Date", "Company", "Sector", "Close", "Daily Return %", "Volume"]].copy()
comparison_df["Normalized Close"] = comparison_df.groupby("Company")["Close"].transform(lambda s: (s / s.iloc[0]) * 100)

compare_left, compare_right = st.columns(2)

with compare_left:
    fig_compare = px.line(
        comparison_df,
        x="Date",
        y="Normalized Close",
        color="Company",
        title="Price Comparison (Base = 100)",
    )
    fig_compare.update_layout(height=420, yaxis_title="Normalized Price")
    st.plotly_chart(fig_compare, use_container_width=True)

with compare_right:
    latest_daily = (
        comparison_df.dropna(subset=["Daily Return %"])
        .sort_values("Date")
        .groupby("Company", as_index=False)
        .tail(1)
        .sort_values("Daily Return %", ascending=False)
    )

    fig_daily_compare = px.bar(
        latest_daily,
        x="Company",
        y="Daily Return %",
        color="Company",
        title="Latest Daily Return Comparison",
    )
    fig_daily_compare.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig_daily_compare, use_container_width=True)

# -------------------- MONTHLY COMPARISON + HEATMAP --------------------
bottom_left, bottom_right = st.columns(2)

with bottom_left:
    latest_monthly = (
        monthly_data[monthly_data["Company"].isin(comparison_names)]
        .dropna(subset=["Monthly Return %"])
        .sort_values("Month")
        .groupby("Company", as_index=False)
        .tail(1)
        .sort_values("Monthly Return %", ascending=False)
    )

    fig_month_comp = px.bar(
        latest_monthly,
        x="Company",
        y="Monthly Return %",
        color="Company",
        title="Latest Monthly Return Comparison",
    )
    fig_month_comp.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig_month_comp, use_container_width=True)

with bottom_right:
    heat_df = (
        monthly_data[monthly_data["Company"].isin(comparison_names)]
        .pivot_table(index="Company", columns="Month", values="Monthly Return %")
    )

    if heat_df.empty:
        st.info("Not enough monthly data for heatmap.")
    else:
        fig_heat = px.imshow(
            heat_df,
            text_auto=".1f",
            aspect="auto",
            title="Monthly Return Heatmap (%)",
        )
        fig_heat.update_layout(height=420)
        st.plotly_chart(fig_heat, use_container_width=True)

# -------------------- STOCK RANKING --------------------
st.subheader("Stock Ranking in Selected Range")

ranking = (
    historical_data[historical_data["Company"].isin(comparison_names)]
    .groupby("Company", as_index=False)
    .agg(Start_Close=("Close", "first"), End_Close=("Close", "last"))
)
ranking["Return %"] = ((ranking["End_Close"] / ranking["Start_Close"]) - 1) * 100
ranking = ranking.sort_values("Return %", ascending=False)

fig_rank = px.bar(
    ranking,
    x="Company",
    y="Return %",
    color="Company",
    title="Overall Return Ranking",
)
fig_rank.update_layout(height=420, showlegend=False)
st.plotly_chart(fig_rank, use_container_width=True)

# -------------------- RAW DATA + DOWNLOAD --------------------
st.subheader("Filtered Data Table")

view_cols = [
    "Date", "Company", "Sector", "Open", "High", "Low", "Close", "Volume",
    "Daily Return %", "SMA 20", "SMA 50"
]
st.dataframe(historical_data[view_cols], use_container_width=True, hide_index=True)

csv_buffer = io.StringIO()
historical_data[view_cols].to_csv(csv_buffer, index=False)

st.download_button(
    label="Download Data as CSV",
    data=csv_buffer.getvalue(),
    file_name="indian_stock_dashboard.csv",
    mime="text/csv",
)

st.markdown("---")
st.markdown(
    "Built with **Streamlit + Pandas + NumPy + Plotly + yfinance**. "
    "This version supports live fluctuation, one-stock detailed analysis, and a separate multi-stock comparison bar."
)