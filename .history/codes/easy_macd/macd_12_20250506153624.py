# Python实用宝典
# 2020/04/20
# 转载请注明出处
import datetime
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA
from backtrader.observers import Trades  # 导入内置的Trades观察器


class TradeLinesObserver(bt.Observer):
    """绘制从交易开仓到平仓的连线"""

    lines = ('tradeline_plus', 'tradeline_minus')  # 定义两条线，一条表示盈利交易，一条表示亏损交易

    # 配置绘图参数 - 一定要设置在主图上显示
    plotinfo = dict(plot=True, subplot=True, plotname='TradeLinesObserver')

    plotlines = dict(
        tradeline_plus=dict(_name='Profit', ls='-', lw=2, color='lime'),
        tradeline_minus=dict(_name='Loss', ls='-', lw=2, color='red'),
    )

    def __init__(self):
        # 初始化设置
        self.trades = []
        self.trade_entry_bar = None
        self.trade_entry_price = None

    def next(self):
        # 重置线条值为NaN，确保只在需要连线的点处有值
        self.lines.tradeline_plus[0] = float('nan')
        self.lines.tradeline_minus[0] = float('nan')

        # 遍历刚刚关闭的交易，在当前bar的位置绘制连线
        for trade in self._owner._tradespending:
            if not trade.isclosed:
                continue

            # 获取交易相关数据
            strategy = self._owner

            # 尝试从策略中获取开仓信息
            if hasattr(strategy, 'trade_entry_bar') and hasattr(strategy, 'trade_entry_price'):
                entry_bar = strategy.trade_entry_bar
                entry_price = strategy.trade_entry_price

                # 当前bar是平仓bar
                exit_bar = len(self)
                exit_price = trade.price

                # 计算开仓点相对于当前bar的索引偏移
                bar_offset = exit_bar - entry_bar

                # 根据盈亏设置连线
                if trade.pnl > 0:
                    # 在平仓位置
                    self.lines.tradeline_plus[0] = exit_price
                    # 在开仓位置
                    if bar_offset > 0 and bar_offset < len(self.lines.tradeline_plus):
                        self.lines.tradeline_plus[-bar_offset] = entry_price
                else:
                    # 在平仓位置
                    self.lines.tradeline_minus[0] = exit_price
                    # 在开仓位置
                    if bar_offset > 0 and bar_offset < len(self.lines.tradeline_minus):
                        self.lines.tradeline_minus[-bar_offset] = entry_price


class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    @staticmethod
    def percent(today, yesterday):
        return float(today - yesterday) / today

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.volume = self.datas[0].volume

        self.order = None
        self.buyprice = None
        self.buycomm = None

        me1 = EMA(self.data, period=12)
        me2 = EMA(self.data, period=26)
        self.macd = me1 - me2
        self.signal = EMA(self.macd, period=9)

        bt.indicators.MACDHisto(self.data)

        # 记录开仓和平仓信息
        self.trade_entry_price = None
        self.trade_entry_bar = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.bar_executed_close = self.dataclose[0]

                # 记录开仓信息
                self.trade_entry_price = order.executed.price
                self.trade_entry_bar = len(self)
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    # Python 实用宝典
    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])
        if self.order:
            return

        if not self.position:
            condition1 = self.macd[-1] - self.signal[-1]
            condition2 = self.macd[0] - self.signal[0]
            if condition1 < 0 and condition2 > 0:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()

        else:
            condition = (
                self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
            if condition > 0.1 or condition < -0.1:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    cerebro.addstrategy(TestStrategy)

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '603186.csv')

    # 加载数据到模型中
    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(2010, 1, 1),
        todate=datetime.datetime(2020, 4, 12),
        dtformat='%Y%m%d',
        datetime=2,
        open=3,
        high=4,
        low=5,
        close=6,
        volume=10,
        reverse=True
    )
    cerebro.adddata(data)

    cerebro.broker.setcash(10000)

    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    cerebro.broker.setcommission(commission=0.005)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # 只使用交易连线观察器，避免重复的子图
    # cerebro.addobserver(Trades)
    cerebro.addobserver(TradeLinesObserver)

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot()
