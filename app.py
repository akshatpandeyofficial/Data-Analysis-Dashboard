import io
from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Indian Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
)

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
}


def format_pct(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


@st.cache_data(show_spinner=False)
def load_data(symbols, start_date, end_date):
    frames = []
    for symbol in symbols:
        df = yf.download(
            symbol,
            start=start_date,
            end=end_date + timedelta(days=1),
            auto_adjust=False,
            progress=False
        )
        if df.empty:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        df = df.reset_index()
        if "Date" not in df.columns:
            df = df.rename(columns={df.columns[0]: "Date"})

        keep_cols = [c for c in ["Date","Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in df.columns]
        df = df[keep_cols].copy()
        df["Symbol"] = symbol
        df["Company"] = next((k for k, v in NSE_SYMBOLS.items() if v == symbol), symbol)
        df["Sector"] = SECTOR_MAP.get(symbol, "Other")
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    data = pd.concat(frames, ignore_index=True)
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.sort_values(["Symbol", "Date"]).reset_index(drop=True)

    data["Daily Return %"] = data.groupby("Symbol")["Close"].pct_change() * 100
    data["SMA 20"] = data.groupby("Symbol")["Close"].transform(lambda s: s.rolling(20).mean())
    data["SMA 50"] = data.groupby("Symbol")["Close"].transform(lambda s: s.rolling(50).mean())
    data["Volatility 20D %"] = data.groupby("Symbol")["Daily Return %"].transform(
        lambda s: s.rolling(20).std() * np.sqrt(252)
    )
    data["Volume MA 20"] = data.groupby("Symbol")["Volume"].transform(lambda s: s.rolling(20).mean())
    data["Volume Ratio"] = data["Volume"] / data["Volume MA 20"]
    data["Month"] = data["Date"].dt.to_period("M").dt.to_timestamp()

    return data


def compute_summary(stock_df: pd.DataFrame):
    stock_df = stock_df.dropna(subset=["Close"]).copy()
    if stock_df.empty:
        return None

    latest_close = float(stock_df["Close"].iloc[-1])
    first_close = float(stock_df["Close"].iloc[0])
    period_return = ((latest_close / first_close) - 1) * 100 if first_close else np.nan
    avg_volume = float(stock_df["Volume"].mean()) if "Volume" in stock_df.columns else np.nan
    volatility = float(stock_df["Daily Return %"].std() * np.sqrt(252)) if stock_df["Daily Return %"].notna().any() else np.nan
    high_52 = float(stock_df["High"].max()) if "High" in stock_df.columns else np.nan
    low_52 = float(stock_df["Low"].min()) if "Low" in stock_df.columns else np.nan

    return {
        "latest_close": latest_close,
        "period_return": period_return,
        "avg_volume": avg_volume,
        "volatility": volatility,
        "high": high_52,
        "low": low_52,
    }


def generate_insights(stock_df: pd.DataFrame, company_name: str):
    insights = []
    clean = stock_df.dropna(subset=["Close"]).copy()
    if clean.empty:
        return ["No data available for the selected range."]

    latest = clean.iloc[-1]
    first = clean.iloc[0]
    period_return = ((latest["Close"] / first["Close"]) - 1) * 100 if first["Close"] else np.nan
    insights.append(f"{company_name} moved {period_return:.2f}% across the selected period.")

    if pd.notna(latest.get("SMA 20")) and pd.notna(latest.get("SMA 50")):
        if latest["SMA 20"] > latest["SMA 50"]:
            insights.append("Short-term momentum is stronger than the medium-term trend because SMA 20 is above SMA 50.")
        else:
            insights.append("Short-term momentum is weaker than the medium-term trend because SMA 20 is below SMA 50.")

    if clean["Daily Return %"].notna().sum() > 5:
        best_day = clean.loc[clean["Daily Return %"].idxmax()]
        worst_day = clean.loc[clean["Daily Return %"].idxmin()]
        insights.append(
            f"Best single trading day: {best_day['Date'].date()} ({best_day['Daily Return %']:.2f}%). "
            f"Worst single trading day: {worst_day['Date'].date()} ({worst_day['Daily Return %']:.2f}%)."
        )

    positive_ratio = (clean["Daily Return %"] > 0).mean() * 100
    insights.append(f"The stock closed positive on {positive_ratio:.1f}% of trading sessions in this range.")

    rolling_vol = clean["Volatility 20D %"].dropna()
    if not rolling_vol.empty:
        insights.append(
            f"20-day annualized volatility recently stood near {rolling_vol.iloc[-1]:.2f}%, "
            f"compared with an average of {rolling_vol.mean():.2f}% over the selected range."
        )

    return insights[:5]


def get_volume_spikes(stock_df: pd.DataFrame, threshold: float):
    spikes = stock_df.copy()
    spikes = spikes.dropna(subset=["Volume Ratio", "Daily Return %"])
    spikes = spikes[spikes["Volume Ratio"] >= threshold].copy()
    spikes = spikes.sort_values("Date", ascending=False)
    return spikes


st.title("📈 Indian Stock Market Data Analysis Dashboard")
st.caption("A full deployable Streamlit project built around live public stock-market data from Yahoo Finance.")

with st.sidebar:
    st.header("Controls")
    selected_names = st.multiselect(
        "Pick 1–5 Indian stocks",
        options=list(NSE_SYMBOLS.keys()),
        default=["Reliance Industries", "TCS", "Infosys"],
        max_selections=5,
    )

    end_date = st.date_input("End date", value=date.today())
    start_date = st.date_input("Start date", value=date.today() - timedelta(days=365))

    if start_date >= end_date:
        st.error("Start date must be before end date.")
        st.stop()

    benchmark = st.selectbox("Benchmark for comparison", ["^NSEI", "^BSESN"], index=0)

    st.markdown("---")
    st.subheader("New Feature")
    volume_spike_threshold = st.slider(
        "Volume spike threshold (x times 20-day avg)",
        min_value=1.0,
        max_value=5.0,
        value=2.0,
        step=0.1
    )

    st.markdown("---")
    st.markdown("**Tip:** use 2–5 stocks to unlock the comparison and correlation views.")

symbols = [NSE_SYMBOLS[name] for name in selected_names]

with st.spinner("Fetching live market data..."):
    data = load_data(tuple(symbols), start_date, end_date)
    benchmark_df = yf.download(
        benchmark,
        start=start_date,
        end=end_date + timedelta(days=1),
        auto_adjust=False,
        progress=False
    )
    if isinstance(benchmark_df.columns, pd.MultiIndex):
        benchmark_df.columns = [c[0] for c in benchmark_df.columns]
    if not benchmark_df.empty:
        benchmark_df = benchmark_df.reset_index()[["Date", "Close"]]
        benchmark_df["Date"] = pd.to_datetime(benchmark_df["Date"])

if data.empty:
    st.warning("No data could be loaded. Try another stock or a different date range.")
    st.stop()

selected_company = st.selectbox("Detailed analysis for", options=selected_names, index=0)
selected_symbol = NSE_SYMBOLS[selected_company]
stock_df = data[data["Symbol"] == selected_symbol].copy()
summary = compute_summary(stock_df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Close", f"₹{summary['latest_close']:.2f}")
col2.metric("Period Return", format_pct(summary["period_return"]))
col3.metric("Avg Volume", f"{summary['avg_volume']:,.0f}")
col4.metric("Annualized Volatility", format_pct(summary["volatility"]))

col5, col6 = st.columns(2)
with col5:
    st.info(f"52-week range in selected period: ₹{summary['low']:.2f} to ₹{summary['high']:.2f}")
with col6:
    st.success(f"Rows loaded: {len(data):,} | Stocks compared: {data['Symbol'].nunique()}")

left, right = st.columns([2, 1])

with left:
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["Close"], mode="lines", name="Close"))
    fig_price.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["SMA 20"], mode="lines", name="SMA 20"))
    fig_price.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["SMA 50"], mode="lines", name="SMA 50"))
    fig_price.update_layout(
        title=f"{selected_company} Price Trend",
        xaxis_title="Date",
        yaxis_title="Price (₹)",
        height=430
    )
    st.plotly_chart(fig_price, use_container_width=True)

with right:
    st.subheader("5 quick insights")
    for idx, insight in enumerate(generate_insights(stock_df, selected_company), start=1):
        st.markdown(f"**{idx}.** {insight}")

col_a, col_b = st.columns(2)

with col_a:
    hist_df = stock_df.dropna(subset=["Daily Return %"])
    fig_hist = px.histogram(hist_df, x="Daily Return %", nbins=40, title="Daily Returns Distribution")
    fig_hist.update_layout(height=380)
    st.plotly_chart(fig_hist, use_container_width=True)

with col_b:
    monthly = stock_df.groupby("Month", as_index=False).agg({"Close": "last"})
    monthly["Monthly Return %"] = monthly["Close"].pct_change() * 100
    fig_monthly = px.bar(monthly, x="Month", y="Monthly Return %", title="Monthly Return %")
    fig_monthly.update_layout(height=380)
    st.plotly_chart(fig_monthly, use_container_width=True)

st.subheader("Compare multiple stocks")
comparison = data[["Date", "Company", "Close", "Daily Return %", "Volume"]].copy()
comparison["Normalized Close"] = comparison.groupby("Company")["Close"].transform(lambda s: s / s.iloc[0] * 100)

fig_compare = px.line(
    comparison,
    x="Date",
    y="Normalized Close",
    color="Company",
    title="Normalized Performance (Base = 100)"
)

if not benchmark_df.empty:
    benchmark_base = benchmark_df["Close"].iloc[0]
    benchmark_df["Normalized Close"] = benchmark_df["Close"] / benchmark_base * 100
    benchmark_name = "NIFTY 50" if benchmark == "^NSEI" else "SENSEX"
    fig_compare.add_trace(
        go.Scatter(
            x=benchmark_df["Date"],
            y=benchmark_df["Normalized Close"],
            mode="lines",
            name=benchmark_name,
        )
    )

fig_compare.update_layout(height=430)
st.plotly_chart(fig_compare, use_container_width=True)

heat_left, heat_right = st.columns(2)

with heat_left:
    corr_source = comparison.pivot_table(index="Date", columns="Company", values="Daily Return %")
    if corr_source.shape[1] >= 2:
        corr = corr_source.corr().round(2)
        fig_corr = px.imshow(corr, text_auto=True, aspect="auto", title="Return Correlation Heatmap")
        fig_corr.update_layout(height=400)
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Select at least 2 stocks to view correlation.")

with heat_right:
    sector_perf = comparison.groupby("Company", as_index=False).agg({"Close": ["first", "last"]})
    sector_perf.columns = ["Company", "Start", "End"]
    sector_perf["Return %"] = ((sector_perf["End"] / sector_perf["Start"]) - 1) * 100
    fig_sector = px.bar(
        sector_perf.sort_values("Return %", ascending=False),
        x="Company",
        y="Return %",
        title="Stock Returns Ranking"
    )
    fig_sector.update_layout(height=400)
    st.plotly_chart(fig_sector, use_container_width=True)

# NEW FEATURE SECTION
st.subheader("🚀 New Feature: Volume Spike Detector")

spike_df = get_volume_spikes(stock_df, volume_spike_threshold)

vol_left, vol_right = st.columns([2, 1])

with vol_left:
    fig_volume = go.Figure()
    fig_volume.add_trace(go.Bar(x=stock_df["Date"], y=stock_df["Volume"], name="Daily Volume"))
    fig_volume.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["Volume MA 20"], mode="lines", name="20-Day Avg Volume"))

    if not spike_df.empty:
        fig_volume.add_trace(
            go.Scatter(
                x=spike_df["Date"],
                y=spike_df["Volume"],
                mode="markers",
                name="Spike Days",
                marker=dict(size=10, symbol="diamond")
            )
        )

    fig_volume.update_layout(
        title=f"{selected_company} Volume Activity",
        xaxis_title="Date",
        yaxis_title="Volume",
        height=420
    )
    st.plotly_chart(fig_volume, use_container_width=True)

with vol_right:
    st.markdown(f"**Spike Rule:** Volume ≥ {volume_spike_threshold:.1f} × 20-day average")
    st.metric("Spike Days Found", len(spike_df))

    if not spike_df.empty:
        latest_spike = spike_df.iloc[0]
        st.success(
            f"Latest spike: {latest_spike['Date'].date()} | "
            f"Volume Ratio: {latest_spike['Volume Ratio']:.2f}x"
        )
    else:
        st.info("No spike days found for this threshold.")

if not spike_df.empty:
    st.dataframe(
        spike_df[["Date", "Close", "Volume", "Volume MA 20", "Volume Ratio", "Daily Return %"]]
        .rename(columns={
            "Close": "Close Price",
            "Volume MA 20": "20D Avg Volume",
            "Volume Ratio": "Volume Ratio",
            "Daily Return %": "Daily Return %"
        }),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Try lowering the spike threshold from the sidebar to detect more unusual volume days.")

st.subheader("Raw data and export")
view_cols = [
    "Date", "Company", "Sector", "Open", "High", "Low", "Close", "Volume",
    "Daily Return %", "SMA 20", "SMA 50", "Volatility 20D %", "Volume MA 20", "Volume Ratio"
]
st.dataframe(data[view_cols], use_container_width=True, hide_index=True)

csv_buffer = io.StringIO()
data[view_cols].to_csv(csv_buffer, index=False)

st.download_button(
    label="Download filtered data as CSV",
    data=csv_buffer.getvalue(),
    file_name="indian_stock_dashboard_export.csv",
    mime="text/csv",
)

st.markdown("---")
st.markdown(
    "Built with **Streamlit + Pandas + NumPy + Plotly + yfinance**. "
    "This project is ready for Streamlit Community Cloud, Render, or local deployment."
)