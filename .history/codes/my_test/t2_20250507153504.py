import backtrader as bt
import pandas as pd

# 生成测试数据
data = pd.DataFrame({
    'close': [i for i in range(1, 101)],
    'open': [i-0.5 for i in range(1, 101)],
    'high': [i+0.3 for i in range(1, 101)],
    'low': [i-0.3 for i in range(1, 101)]
})

# 自定义MACD样式
class ColorMACD(bt.indicators.MACDHisto):
    plotlines = {
        'histo': {
            '_method': 'bar',
            'color': 'purple',
            '_name': '能量柱'  # 修改图例名称
        }
    }

# 创建回测引擎
cerebro = bt.Cerebro()
feed = bt.feeds.PandasData(dataname=data)
cerebro.adddata(feed)
cerebro.addindicator(ColorMACD)

# 运行并绘图
cerebro.run()
cerebro.plot(style='candle')  # 显示K线+MACD组合图