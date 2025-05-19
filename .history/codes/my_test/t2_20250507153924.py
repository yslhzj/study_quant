import backtrader as bt
import pandas as pd

# 生成测试数据（带时间戳）
data = pd.DataFrame({
    'open': [i for i in range(100)],
    'high': [i+1 for i in range(100)],
    'low': [i-1 for i in range(100)],
    'close': [i+0.5 for i in range(100)],
    'volume': [100]*100
}, index=pd.date_range('2024-01-01', periods=100))

# 创建策略
class FillStrategy(bt.Strategy):
    def __init__(self):
        # 添加SMA指标
        self.sma = bt.indicators.SMA(period=15)
        
        # 配置填充规则：
        # 1. 收盘价上穿SMA时黄色填充
        # 2. 收盘价下穿SMA时紫色填充
        self.plotlines = dict(
            close=dict(
                _fill_gt('sma', ('yellow', 0.3)),
                _fill_lt('sma', ('purple', 0.3))
            )
        )

# 回测引擎设置
cerebro = bt.Cerebro()
cerebro.adddata(bt.feeds.PandasData(dataname=data))
cerebro.addstrategy(FillStrategy)
cerebro.run()
cerebro.plot(style='candle')