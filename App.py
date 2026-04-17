"""
╔══════════════════════════════════════════════╗
║   DATA ANALYSIS DASHBOARD  –  Streamlit App  ║
╚══════════════════════════════════════════════╝
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataPulse Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.stApp { background: #0D0F1A; }
section[data-testid="stSidebar"] { background: #0D0F1A !important; border-right: 1px solid #1E2436; }

.metric-card {
    background: linear-gradient(135deg, #141824 0%, #1A2035 100%);
    border: 1px solid #00F5C4222;
    border-left: 3px solid;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 6px 0;
}
.metric-card.green  { border-left-color: #00F5C4; }
.metric-card.purple { border-left-color: #7C6EFA; }
.metric-card.pink   { border-left-color: #FF6B8A; }
.metric-card.yellow { border-left-color: #FFB830; }

.metric-label { color: #64748B; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }
.metric-value { color: #E2E8F0; font-family: 'Space Mono', monospace; font-size: 26px; font-weight: 700; }
.metric-delta { font-size: 11px; margin-top: 4px; }
.metric-delta.up   { color: #00F5C4; }
.metric-delta.down { color: #FF6B8A; }

.section-title {
    color: #E2E8F0; font-family: 'Space Mono', monospace;
    font-size: 13px; letter-spacing: 2px; text-transform: uppercase;
    border-bottom: 1px solid #1E2436; padding-bottom: 8px; margin: 24px 0 14px;
}
[data-testid="stMetricValue"] { color: #00F5C4 !important; font-family: 'Space Mono', monospace; }
</style>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load():
    df = pd.read_csv('sales_data.csv', parse_dates=['Date'])
    return df

df = load()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Filters")
    cats     = st.multiselect("Category", df['Category'].unique(), default=list(df['Category'].unique()))
    regions  = st.multiselect("Region",   df['Region'].unique(),   default=list(df['Region'].unique()))
    quarters = st.multiselect("Quarter",  sorted(df['Quarter'].unique()), default=list(df['Quarter'].unique()))
    st.divider()
    st.markdown("### 📁 Upload CSV")
    up = st.file_uploader("Drop a CSV file", type='csv')
    if up:
        df = pd.read_csv(up, parse_dates=['Date'])
        st.success("Loaded your data ✓")

mask = (df['Category'].isin(cats)) & (df['Region'].isin(regions)) & (df['Quarter'].isin(quarters))
fd   = df[mask].copy()

COLORS = ['#00F5C4','#7C6EFA','#FF6B8A','#FFB830','#4CC9F0']
TMPL   = dict(layout=go.Layout(
    paper_bgcolor='#141824', plot_bgcolor='#141824',
    font=dict(color='#E2E8F0', family='Sora'),
    xaxis=dict(gridcolor='#1E2436', zeroline=False),
    yaxis=dict(gridcolor='#1E2436', zeroline=False),
    margin=dict(l=40, r=20, t=40, b=40),
))

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(90deg,#00F5C422,#7C6EFA11);
            border:1px solid #00F5C433;border-radius:16px;padding:20px 28px;margin-bottom:24px'>
  <span style='font-family:Space Mono,monospace;color:#00F5C4;font-size:22px;font-weight:700;
               letter-spacing:2px'>⚡ DataPulse</span>
  <span style='color:#64748B;font-size:14px;margin-left:16px'>Sales Analytics Platform</span>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
cards = [
    (c1, "green",  "TOTAL SALES",     f"${fd['Sales'].sum():,.0f}",  "↑ All Regions"),
    (c2, "purple", "TOTAL PROFIT",    f"${fd['Profit'].sum():,.0f}", "↑ Net Earned"),
    (c3, "pink",   "AVG RATING",      f"{fd['Rating'].mean():.2f} ★","Customer Score"),
    (c4, "yellow", "TRANSACTIONS",    f"{len(fd):,}",                "↑ Orders Recorded"),
]
for col, color, label, value, delta in cards:
    col.markdown(f"""
    <div class='metric-card {color}'>
      <div class='metric-label'>{label}</div>
      <div class='metric-value'>{value}</div>
      <div class='metric-delta up'>{delta}</div>
    </div>""", unsafe_allow_html=True)

# ── Sales Trend ────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📈 Revenue Trend</div>", unsafe_allow_html=True)
monthly = fd.groupby(fd['Date'].dt.to_period('M')).agg(Sales=('Sales','sum'), Profit=('Profit','sum')).reset_index()
monthly['Date'] = monthly['Date'].astype(str)

fig1 = go.Figure(template=TMPL)
fig1.add_trace(go.Scatter(x=monthly['Date'], y=monthly['Sales'], name='Sales',
    line=dict(color='#00F5C4',width=2.5), fill='tozeroy', fillcolor='#00F5C411', mode='lines+markers'))
fig1.add_trace(go.Scatter(x=monthly['Date'], y=monthly['Profit'], name='Profit',
    line=dict(color='#7C6EFA',width=2.5), fill='tozeroy', fillcolor='#7C6EFA11', mode='lines+markers'))
fig1.update_layout(title='Monthly Sales vs Profit', height=300, legend=dict(orientation='h'))
st.plotly_chart(fig1, use_container_width=True)

# ── Category & Region ──────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🛒 Category & Region Analysis</div>", unsafe_allow_html=True)
col_a, col_b = st.columns(2)

with col_a:
    cat_sales = fd.groupby('Category')['Sales'].sum().reset_index().sort_values('Sales')
    fig2 = px.bar(cat_sales, x='Sales', y='Category', orientation='h',
                  color='Category', color_discrete_sequence=COLORS, template=TMPL)
    fig2.update_layout(title='Sales by Category', height=300, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    reg = fd.groupby('Region')['Profit'].sum().reset_index()
    fig3 = px.pie(reg, values='Profit', names='Region',
                  color_discrete_sequence=COLORS, hole=0.55, template=TMPL)
    fig3.update_layout(title='Profit by Region', height=300)
    st.plotly_chart(fig3, use_container_width=True)

# ── Heatmap & Scatter ──────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🗺️ Deep Dive</div>", unsafe_allow_html=True)
col_c, col_d = st.columns(2)

with col_c:
    piv = fd.pivot_table(values='Sales', index='Region', columns='Category', aggfunc='sum')
    fig4 = px.imshow(piv, color_continuous_scale='Plasma', template=TMPL, text_auto='.0f')
    fig4.update_layout(title='Heatmap: Region × Category', height=320)
    st.plotly_chart(fig4, use_container_width=True)

with col_d:
    fig5 = px.scatter(fd, x='Sales', y='Profit', color='Category', size='Units',
                      color_discrete_sequence=COLORS, template=TMPL, opacity=0.7,
                      trendline='ols')
    fig5.update_layout(title='Sales vs Profit Scatter', height=320)
    st.plotly_chart(fig5, use_container_width=True)

# ── Quarterly grouped bars ─────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📅 Quarterly Performance</div>", unsafe_allow_html=True)
qdata = fd.groupby(['Quarter','Category'])['Sales'].sum().reset_index()
fig6 = px.bar(qdata, x='Quarter', y='Sales', color='Category',
              barmode='group', color_discrete_sequence=COLORS, template=TMPL)
fig6.update_layout(title='Quarterly Sales by Category', height=300)
st.plotly_chart(fig6, use_container_width=True)

# ── Distribution histograms ────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📊 Distributions</div>", unsafe_allow_html=True)
col_e, col_f, col_g = st.columns(3)
for col, field, color in zip([col_e, col_f, col_g],
                              ['Sales', 'Customer_Age', 'Rating'],
                              ['#00F5C4','#7C6EFA','#FF6B8A']):
    fig = px.histogram(fd, x=field, nbins=25, template=TMPL, color_discrete_sequence=[color])
    fig.update_layout(title=f'{field} Distribution', height=250, showlegend=False)
    col.plotly_chart(fig, use_container_width=True)

# ── EDA Summary table ─────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🔬 EDA Summary Statistics</div>", unsafe_allow_html=True)
num = fd.select_dtypes(include=np.number)
stats = num.describe().T.round(2)
stats['missing'] = fd.isnull().sum()
stats['skew']    = num.skew().round(3)
st.dataframe(stats.style.background_gradient(cmap='viridis', axis=0), use_container_width=True)

# ── Raw data ───────────────────────────────────────────────────────────────────
with st.expander("🗂️ Raw Data Table"):
    st.dataframe(fd.head(100), use_container_width=True)
    st.download_button("⬇️ Download Filtered CSV", fd.to_csv(index=False),
                       'filtered_data.csv', 'text/csv')

st.markdown("<br><div style='text-align:center;color:#1E2436;font-size:11px'>DataPulse Analytics v1.0</div>", unsafe_allow_html=True)