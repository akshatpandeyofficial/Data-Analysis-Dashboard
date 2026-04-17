import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
import os

# ── Palette ────────────────────────────────────────────────────────────────────
PALETTE = {
    'bg':      '#0D0F1A',
    'card':    '#141824',
    'accent1': '#00F5C4',
    'accent2': '#7C6EFA',
    'accent3': '#FF6B8A',
    'accent4': '#FFB830',
    'accent5': '#4CC9F0',
    'text':    '#E2E8F0',
    'muted':   '#64748B',
}
COLORS = [PALETTE['accent1'], PALETTE['accent2'], PALETTE['accent3'],
          PALETTE['accent4'], PALETTE['accent5']]

def style_axes(ax, title=''):
    ax.set_facecolor(PALETTE['card'])
    ax.spines[:].set_color(PALETTE['muted'] + '44')
    ax.tick_params(colors=PALETTE['text'], labelsize=9)
    ax.xaxis.label.set_color(PALETTE['muted'])
    ax.yaxis.label.set_color(PALETTE['muted'])
    if title:
        ax.set_title(title, color=PALETTE['text'], fontsize=11, fontweight='bold', pad=10)

# ── Load & Summarize ────────────────────────────────────────────────────────────
def load_data(path='sales_data.csv'):
    df = pd.read_csv(path, parse_dates=['Date'])
    return df

def summary_stats(df):
    numeric = df.select_dtypes(include=np.number)
    stats = numeric.describe().T
    stats['missing'] = df.isnull().sum()
    stats['skew']    = numeric.skew()
    return stats

# ── Chart generators ───────────────────────────────────────────────────────────
def plot_sales_trend(df, out='charts/sales_trend.png'):
    os.makedirs('charts', exist_ok=True)
    monthly = df.groupby(df['Date'].dt.to_period('M')).agg(
        Sales=('Sales','sum'), Profit=('Profit','sum')).reset_index()
    monthly['Date'] = monthly['Date'].astype(str)

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(PALETTE['bg'])
    ax.set_facecolor(PALETTE['card'])

    ax.fill_between(monthly['Date'], monthly['Sales'],
                    alpha=0.15, color=PALETTE['accent1'])
    ax.plot(monthly['Date'], monthly['Sales'],
            color=PALETTE['accent1'], lw=2.5, marker='o', ms=5, label='Sales')
    ax.fill_between(monthly['Date'], monthly['Profit'],
                    alpha=0.12, color=PALETTE['accent2'])
    ax.plot(monthly['Date'], monthly['Profit'],
            color=PALETTE['accent2'], lw=2.5, marker='s', ms=5, label='Profit')

    ax.set_xticks(range(len(monthly['Date'])))
    ax.set_xticklabels(monthly['Date'], rotation=35, ha='right', fontsize=8)
    style_axes(ax, '📈 Monthly Sales & Profit Trend')
    ax.legend(facecolor=PALETTE['bg'], labelcolor=PALETTE['text'], fontsize=9)
    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()
    return out

def plot_category_breakdown(df, out='charts/category.png'):
    os.makedirs('charts', exist_ok=True)
    cat = df.groupby('Category')['Sales'].sum().sort_values(ascending=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor(PALETTE['bg'])

    bars = ax1.barh(cat.index, cat.values,
                    color=COLORS[:len(cat)], edgecolor='none', height=0.6)
    for bar, val in zip(bars, cat.values):
        ax1.text(val * 0.98, bar.get_y() + bar.get_height()/2,
                 f'${val:,.0f}', va='center', ha='right',
                 color=PALETTE['bg'], fontsize=8, fontweight='bold')
    style_axes(ax1, '🛒 Sales by Category')

    profit_cat = df.groupby('Category')['Profit'].sum()
    wedges, texts, autotexts = ax2.pie(
        profit_cat.values, labels=profit_cat.index,
        colors=COLORS[:len(profit_cat)],
        autopct='%1.1f%%', startangle=140,
        wedgeprops=dict(edgecolor=PALETTE['bg'], linewidth=2))
    for t in texts:   t.set_color(PALETTE['text']); t.set_fontsize(9)
    for a in autotexts: a.set_color(PALETTE['bg']); a.set_fontsize(8); a.set_fontweight('bold')
    ax2.set_facecolor(PALETTE['card'])
    ax2.set_title('💰 Profit Share', color=PALETTE['text'], fontsize=11, fontweight='bold')

    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()
    return out

def plot_region_heatmap(df, out='charts/heatmap.png'):
    os.makedirs('charts', exist_ok=True)
    pivot = df.pivot_table(values='Sales', index='Region',
                           columns='Category', aggfunc='sum')

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(PALETTE['bg'])
    ax.set_facecolor(PALETTE['card'])

    sns.heatmap(pivot, ax=ax, cmap='plasma', annot=True, fmt='.0f',
                linewidths=0.5, linecolor=PALETTE['bg'],
                annot_kws={'size': 8, 'color': 'white'},
                cbar_kws={'shrink': 0.8})

    ax.set_title('🗺️ Sales Heatmap: Region × Category',
                 color=PALETTE['text'], fontsize=11, fontweight='bold', pad=12)
    ax.tick_params(colors=PALETTE['text'], labelsize=9)
    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()
    return out

def plot_distributions(df, out='charts/distributions.png'):
    os.makedirs('charts', exist_ok=True)
    cols = ['Sales', 'Profit', 'Customer_Age', 'Rating']

    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    fig.patch.set_facecolor(PALETTE['bg'])
    axes = axes.flatten()

    for i, (col, ax) in enumerate(zip(cols, axes)):
        ax.set_facecolor(PALETTE['card'])
        data = df[col].dropna()
        ax.hist(data, bins=25, color=COLORS[i], alpha=0.8, edgecolor='none')
        ax.axvline(data.mean(), color='white', lw=1.5, ls='--', alpha=0.7)
        style_axes(ax, f'📊 {col} Distribution')
        ax.text(0.97, 0.92, f'μ={data.mean():.1f}', transform=ax.transAxes,
                ha='right', color=PALETTE['text'], fontsize=8)

    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()
    return out

def plot_scatter_profit(df, out='charts/scatter.png'):
    os.makedirs('charts', exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(PALETTE['bg'])
    ax.set_facecolor(PALETTE['card'])

    cats = df['Category'].unique()
    for i, cat in enumerate(cats):
        sub = df[df['Category'] == cat]
        ax.scatter(sub['Sales'], sub['Profit'],
                   c=COLORS[i % len(COLORS)], alpha=0.55,
                   s=40, label=cat, edgecolors='none')

    m, b = np.polyfit(df['Sales'], df['Profit'], 1)
    xr = np.linspace(df['Sales'].min(), df['Sales'].max(), 100)
    ax.plot(xr, m*xr+b, color='white', lw=1.5, ls='--', alpha=0.5, label='Trend')

    style_axes(ax, '🔵 Sales vs Profit Scatter')
    ax.legend(facecolor=PALETTE['bg'], labelcolor=PALETTE['text'], fontsize=8,
              ncol=3, loc='upper left')
    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()
    return out

def plot_quarterly(df, out='charts/quarterly.png'):
    os.makedirs('charts', exist_ok=True)
    q = df.groupby(['Quarter', 'Category'])['Sales'].sum().unstack()

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(PALETTE['bg'])
    ax.set_facecolor(PALETTE['card'])

    x = np.arange(4)
    w = 0.15
    for i, col in enumerate(q.columns):
        ax.bar(x + i*w, q[col], w, color=COLORS[i], label=col,
               edgecolor='none', alpha=0.9)

    ax.set_xticks(x + w*2)
    ax.set_xticklabels([f'Q{i+1}' for i in range(4)])
    style_axes(ax, '📅 Quarterly Sales by Category')
    ax.legend(facecolor=PALETTE['bg'], labelcolor=PALETTE['text'], fontsize=8)
    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()
    return out

# ── Run all ───────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    df = load_data()
    print("📊 EDA Summary:\n", summary_stats(df).to_string())
    for fn in [plot_sales_trend, plot_category_breakdown, plot_region_heatmap,
               plot_distributions, plot_scatter_profit, plot_quarterly]:
        p = fn(df)
        print(f'✅ Saved: {p}')