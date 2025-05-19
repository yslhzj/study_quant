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

    # 配置绘图参数
    plotinfo = dict(plot=True, subplot=Tra)  # 绘制在主图上

    plotlines = dict(
        tradeline_plus=dict(_name='Profit', ls='-', lw=1.5, color='lime'),
        tradeline_minus=dict(_name='Loss', ls='-', lw=1.5, color='red'),
    )

    def __init__(self):
        self.trades = []  # 存储交易信息
        self.trade_open_price = None  # 开仓价格
        self.trade_close_price = None  # 平仓价格

    def next(self):
        # 在next中清空之前的值
        self.lines.tradeline_plus[0] = float('nan')  # 使用nan表示不绘制点
        self.lines.tradeline_minus[0] = float('nan')  # 使用nan表示不绘制点

        # 检查是否有已关闭的交易需要绘制连线
        for trade in self.trades:
            close_idx = trade['close_idx']
            if close_idx == len(self) - 1:  # 如果当前bar是交易的平仓点
                # 获取开仓和平仓信息
                open_idx = trade['open_idx']
                open_price = trade['open_price']
                close_price = trade['close_price']
                pnl = trade['pnl']

                # 在当前点(平仓点)设置对应交易线的值
                if pnl > 0:
                    self.lines.tradeline_plus[0] = close_price
                    # 回溯到开仓点设置值
                    self.lines.tradeline_plus[-close_idx+open_idx] = open_price
                else:
                    self.lines.tradeline_minus[0] = close_price
                    # 回溯到开仓点设置值
                    self.lines.tradeline_minus[-close_idx +
                                               open_idx] = open_price

    def notify_trade(self, trade):
        """交易关闭时记录交易信息"""
        if not trade.isclosed:
            return

        # 获取交易开仓和平仓信息
        data = trade.data

        # 尝试从策略中获取开仓信息
        strategy = self._owner
        if hasattr(strategy, 'trade_entry_bar') and hasattr(strategy, 'trade_entry_price'):
            open_bar = strategy.trade_entry_bar
            open_price = strategy.trade_entry_price
        else:
            # 如果策略中没有记录开仓信息，使用交易自带的信息
            open_bar = trade.baropen
            open_price = trade.price  # 注意：这里可能不精确，是平均成本而非开仓价

        close_bar = len(self)  # 当前bar是平仓bar
        close_price = trade.price
        pnl = trade.pnl

        # 存储交易信息
        self.trades.append({
            'open_idx': open_bar,
            'open_price': open_price,
            'close_idx': close_bar,
            'close_price': close_price,
            'pnl': pnl
        })


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
