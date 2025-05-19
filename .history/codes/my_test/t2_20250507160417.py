import backtrader as bt
import pandas as pd
import numpy as np

# 生成测试数据（正弦波模拟价格波动）
dates = pd.date_range('2024-01-01', periods=100)
data = pd.DataFrame({
    'close': np.sin(np.linspace(0, 10, 100)) * 50 + 100
}, index=dates)

# 自定义随机指标（突出显示设置）
class MyStochastic(bt.indicators.Stochastic):
    plotlines = dict(
        percK=dict(_name='%K快线', color='red', linewidth=2),    # 红色粗实线
        percD=dict(_name='%D慢线', color='blue', linestyle='--') # 蓝色虚线
    )

# 创建策略
class Strategy(bt.Strategy):
    def __init__(self):
        self.stoch = MyStochastic()  # 使用自定义样式的随机指标

# 运行回测
cerebro = bt.Cerebro()
cerebro.adddata(bt.feeds.PandasData(dataname=data))
cerebro.addstrategy(Strategy)
cerebro.run()
cerebro.plot(style='candle')