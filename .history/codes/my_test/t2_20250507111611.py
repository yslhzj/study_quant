# 生成测试数据（保存为test.csv）
import pandas as pd
import numpy as np

dates = pd.date_range('2020-01-01', periods=100)
data = pd.DataFrame({
    'open': np.cumsum(np.random.randn(100)) + 100,
    'high': np.cumsum(np.random.randn(100)) + 101,
    'low': np.cumsum(np.random.randn(100)) + 99,
    'close': np.cumsum(np.random.randn(100)) + 100,
    'volume': np.random.randint(10000, 50000, 100),
    'openinterest': np.zeros(100)
}, index=dates)
data.to_csv('test.csv')
