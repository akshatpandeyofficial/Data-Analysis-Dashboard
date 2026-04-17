import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ─────────────────────────────────────
st.set_page_config(
    page_title="DataPulse Analytics",
    page_icon="📊",
    layout="wide"
)

# ── Load data ───────────────────────────────────────
@st.cache_data
def load():
    return pd.read_csv('sales_data.csv', parse_dates=['Date'])

df = load()

# ── Sidebar ─────────────────────────────────────────
with st.sidebar:
    st.title("Filters")
    cats = st.multiselect("Category", df['Category'].unique(), default=list(df['Category'].unique()))
    regions = st.multiselect("Region", df['Region'].unique(), default=list(df['Region'].unique()))
    quarters = st.multiselect("Quarter", df['Quarter'].unique(), default=list(df['Quarter'].unique()))

mask = (df['Category'].isin(cats)) & (df['Region'].isin(regions)) & (df['Quarter'].isin(quarters))
fd = df[mask]

# ── Theme Layout ────────────────────────────────────
BASE_LAYOUT = dict(
    paper_bgcolor='#141824',
    plot_bgcolor='#141824',
    font=dict(color='#E2E8F0'),
    margin=dict(l=40, r=20, t=40, b=40)
)

COLORS = ['#00F5C4','#7C6EFA','#FF6B8A','#FFB830','#4CC9F0']

# ── KPIs ────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Sales", f"${fd['Sales'].sum():,.0f}")
c2.metric("Total Profit", f"${fd['Profit'].sum():,.0f}")
c3.metric("Avg Rating", f"{fd['Rating'].mean():.2f}")
c4.metric("Transactions", len(fd))

# ── Trend Chart ─────────────────────────────────────
st.subheader("📈 Sales vs Profit Trend")

monthly = fd.groupby(fd['Date'].dt.to_period('M')).agg(
    Sales=('Sales','sum'),
    Profit=('Profit','sum')
).reset_index()

monthly['Date'] = monthly['Date'].astype(str)

fig1 = go.Figure()
fig1.update_layout(**BASE_LAYOUT)

fig1.add_trace(go.Scatter(
    x=monthly['Date'],
    y=monthly['Sales'],
    name='Sales',
    line=dict(color='#00F5C4'),
    fill='tozeroy',
    fillcolor='rgba(0,245,196,0.1)'
))

fig1.add_trace(go.Scatter(
    x=monthly['Date'],
    y=monthly['Profit'],
    name='Profit',
    line=dict(color='#7C6EFA'),
    fill='tozeroy',
    fillcolor='rgba(124,110,250,0.1)'
))

st.plotly_chart(fig1, use_container_width=True)

# ── Category Chart ──────────────────────────────────
st.subheader("🛒 Sales by Category")

cat = fd.groupby('Category')['Sales'].sum().reset_index()

fig2 = px.bar(cat, x='Sales', y='Category', color='Category',
              color_discrete_sequence=COLORS)

fig2.update_layout(**BASE_LAYOUT)
st.plotly_chart(fig2, use_container_width=True)

# ── Region Pie ──────────────────────────────────────
st.subheader("🌍 Profit by Region")

reg = fd.groupby('Region')['Profit'].sum().reset_index()

fig3 = px.pie(reg, values='Profit', names='Region', hole=0.5,
              color_discrete_sequence=COLORS)

fig3.update_layout(**BASE_LAYOUT)
st.plotly_chart(fig3, use_container_width=True)

# ── Scatter ─────────────────────────────────────────
st.subheader("📊 Sales vs Profit")

fig4 = px.scatter(fd, x='Sales', y='Profit', color='Category',
                  size='Units', color_discrete_sequence=COLORS)

fig4.update_layout(**BASE_LAYOUT)
st.plotly_chart(fig4, use_container_width=True)

# ── Heatmap ─────────────────────────────────────────
st.subheader("🗺️ Heatmap")

pivot = fd.pivot_table(values='Sales', index='Region', columns='Category', aggfunc='sum')

fig5 = px.imshow(pivot, text_auto=True)

fig5.update_layout(**BASE_LAYOUT)
st.plotly_chart(fig5, use_container_width=True)

# ── Histogram ───────────────────────────────────────
st.subheader("📊 Distribution")

fig6 = px.histogram(fd, x='Sales', nbins=20)
fig6.update_layout(**BASE_LAYOUT)
st.plotly_chart(fig6, use_container_width=True)

# ── EDA Table ───────────────────────────────────────
st.subheader("📋 Summary")

num = fd.select_dtypes(include=np.number)
stats = num.describe().T
stats['missing'] = num.isnull().sum()
stats['skew'] = num.skew()

st.dataframe(stats)

# ── Raw Data ────────────────────────────────────────
st.subheader("Raw Data")
st.dataframe(fd.head(50))