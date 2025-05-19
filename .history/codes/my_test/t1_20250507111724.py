
import backtrader as bt

class St(bt.Strategy):
    params = (
        ('printout', True),  # 开启打印
        ('stake', 1000),     # 每次交易1000股
        ('fast', 5),         # 快速均线周期
        ('slow', 20),       # 慢速均线周期
    )

    def __init__(self):
        # 定义均线指标
        self.fast_ma = bt.indicators.SMA(period=self.p.fast)
        self.slow_ma = bt.indicators.SMA(period=self.p.slow)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        # 数据打印（同前文）
        if self.p.printout:
            txtfields = [
                '%04d' % len(self),
                self.data.datetime.datetime(0).isoformat(),
                '%.2f' % self.data0.open[0],
                '%.2f' % self.data0.high[0],
                '%.2f' % self.data0.low[0],
                '%.2f' % self.data0.close[0],
                '%.2f' % self.data0.volume[0],
                '%.2f' % self.data0.openinterest[0]
            ]
            print(','.join(txtfields))

        # 交易逻辑
        if self.position:
            if self.crossover < 0:
                self.close()
        else:
            if self.crossover > 0:
                self.buy(size=self.p.stake)

# 初始化引擎
cerebro = bt.Cerebro()
data = bt.feeds.GenericCSVData(
    dataname='test.csv',
    dtformat=('%Y-%m-%d'),
    datetime=0, open=1, high=2, low=3, close=4,
    volume=5, openinterest=6
)
cerebro.adddata(data)
cerebro.addstrategy(St)
cerebro.run()
cerebro.plot()