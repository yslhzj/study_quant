import backtrader as bt
import pandas as pd

# 1. 创建测试数据
data = bt.feeds.PandasData(
    dataname=pd.DataFrame({
        'close': [i%2 for i in range(100)],  # 0/1交替数据
        'open': [0.5]*100,
        'high': [1.2]*100,
        'low': [0.2]*100,
        'volume': [100]*100
    })
)

# 2. 创建回测引擎
cerebro = bt.Cerebro()
cerebro.adddata(data)

# 3. 添加简单策略
class TestStrategy(bt.Strategy):
    def next(self):
        pass  # 不做任何交易

cerebro.addstrategy(TestStrategy)

# 4. 全局绘图设置
cerebro.plot(
    numfigs=2,                      # 分成2个图
    iplot=False,                    # 禁用Jupyter内联
    style='candle',                 # K线类型
    plotbarup='#FF6B6B',            # 上涨K线玫红色
    plotbardown='#4ECDC4',          # 下跌K线蒂芙尼蓝
    title='自定义样式演示',         # 图表标题
    grid=True                       # 显示网格线
)