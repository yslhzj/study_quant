

import backtrader as bt

class DemoStrategy(bt.Strategy):
    def __init__(self):
        self.sma = bt.indicators.SMA(self.data, period=10)
        self.pct = bt.indicators.PctChange(self.data.close, period=1)
        
        # 1. 均线和主K线画在一起
        self.sma.plotinfo.subplot = False  # 不单独开小窗
        self.sma.plotinfo.plotmaster = self.data  # 跟随主K线画
        
        # 2. 涨跌幅单独开小窗，y轴只看自己
        self.pct.plotinfo.subplot = True  # 单独开小窗
        self.pct.plotinfo.plotylimited = True  # y轴只看自己

# 后面是标准回测流程
cerebro = bt.Cerebro()
data = bt.feeds.GenericCSVData(
    dataname='test.csv',
    dtformat=('%Y-%m-%d'),
    datetime=0, open=1, high=2, low=3, close=4,
    volume=5, openinterest=6
)
cerebro.adddata(data)
cerebro.addstrategy(DemoStrategy)
cerebro.run()
cerebro.plot()