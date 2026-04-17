import pandas as pd
import numpy as np

np.random.seed(42)
n = 500

categories = ['Electronics', 'Clothing', 'Food', 'Sports', 'Books']
regions = ['North', 'South', 'East', 'West', 'Central']
months = pd.date_range('2023-01-01', periods=12, freq='MS')

data = {
    'Date': np.random.choice(pd.date_range('2023-01-01', '2023-12-31'), n),
    'Category': np.random.choice(categories, n, p=[0.3, 0.2, 0.25, 0.15, 0.1]),
    'Region': np.random.choice(regions, n),
    'Sales': np.abs(np.random.normal(5000, 2000, n)).round(2),
    'Profit': np.abs(np.random.normal(1200, 600, n)).round(2),
    'Units': np.random.randint(1, 200, n),
    'Customer_Age': np.random.randint(18, 70, n),
    'Rating': np.round(np.random.uniform(1, 5, n), 1),
    'Returns': np.random.choice([0, 1], n, p=[0.85, 0.15]),
}

df = pd.DataFrame(data)
df['Month'] = df['Date'].dt.month_name()
df['Quarter'] = df['Date'].dt.quarter
df['Profit_Margin'] = (df['Profit'] / df['Sales'] * 100).round(2)
df.to_csv('sales_data.csv', index=False)
print(f"✅ Dataset generated: {len(df)} rows × {len(df.columns)} columns")
print(df.head())