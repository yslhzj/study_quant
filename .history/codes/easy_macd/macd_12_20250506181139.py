# Python实用宝典
# 2020/04/20
# 转载请注明出处
import datetime
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA
from backtrader.observers import Trades  # 导入内置的Trades观察器
import matplotlib.pyplot as plt


class TradeLinesObserver(bt.Observer):
    """在子图中绘制交易连线观察器"""

    lines = ('long_entry', 'long_exit', 'short_entry', 'short_exit')

    # 配置绘图参数 - 确保在子图中显示
    plotinfo = dict(
        plot=True,
        subplot=True,
        plotname='TradeLine',
        plotymargin=0.10,
        plotylim=(-2, 2)  # 设置Y轴范围为-2到2
    )

    # 配置绘图样式
    plotlines = dict(
        long_entry=dict(_name='Buy', marker='*', markersize=8, color='lime',
                        fillstyle='full', ls='', linewidth=1),
        long_exit=dict(_name='Sell', marker='v', markersize=8, color='red',
                       fillstyle='full', ls='-', linewidth=1),
        short_entry=dict(_name='Short', marker='o', markersize=8, color='blue',
                         fillstyle='full', ls='', linewidth=1),
        short_exit=dict(_name='Cover', marker='^', markersize=8, color='yellow',
                        fillstyle='full', ls='--', linewidth=1)
    )

    def __init__(self):
        # 初始化交易信息
        self.trades = []
        self.order_type = None

    def next(self):
        # 首先设置所有线条为NaN（不可见）
        for linefield in self.lines:
            linefield[0] = float('nan')

        # 检查是否有新的开仓或平仓
        for trade in self._owner._tradespending:
            if trade.isclosed:  # 交易已关闭
                # 判断交易盈亏，使用更可靠的trade.pnl属性
                if trade.pnl > 0:
                    self.lines.long_exit[0] = 1.1  # 盈利平仓标记（接近2.0但留有余量）
                else:
                    self.lines.short_exit[0] = -1.1  # 亏损平仓标记（接近-2.0但留有余量）
                continue

            # 如果是刚开仓的交易
            if trade.justopened:
                # 使用更安全的方式确定交易方向
                try:
                    # 尝试通过trade.history判断方向是否可行
                    if (hasattr(trade, 'history') and trade.history and
                            hasattr(trade.history[0], 'status') and
                            hasattr(trade.history[0].status, 'order') and
                            hasattr(trade.history[0].status.order, 'isbuy') and
                            trade.history[0].status.order.isbuy()):
                        self.lines.long_entry[0] = 1.1  # 多头入场标记（接近2.0但留有余量）
                    # 没有history或无法确定方向时，使用size判断
                    elif not hasattr(trade, 'history') or not trade.history:
                        if trade.size > 0:  # 正数size表示做多
                            # 多头入场标记（接近2.0但留有余量）
                            self.lines.long_entry[0] = 1.1
                        else:  # 负数size表示做空
                            # 空头入场标记（接近-2.0但留有余量）
                            self.lines.short_entry[0] = -1.1
                    else:
                        # 默认假设为多头入场
                        self.lines.long_entry[0] = 1.1  # 多头入场标记（接近2.0但留有余量）
                except (IndexError, AttributeError, KeyError) as e:
                    # 捕获任何可能的异常，使用size判断方向
                    if hasattr(trade, 'size'):
                        if trade.size > 0:
                            # 多头入场标记（接近2.0但留有余量）
                            self.lines.long_entry[0] = 1.1
                        else:
                            # 空头入场标记（接近-2.0但留有余量）
                            self.lines.short_entry[0] = -1.1
                    else:
                        # 最后的兜底方案：默认为多头入场
                        self.lines.long_entry[0] = 1.1  # 多头入场标记（接近2.0但留有余量）


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

        # 开启交易历史记录，确保观察器能访问交易历史
        self.set_tradehistory(True)

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
    cerebro = bt.Cerebro(stdstats=False)  # 关闭默认的broker和trades子图

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

    # 使用最直接的方法设置Y轴范围
    # 设置一个强制绘图样式
    plt.style.use('default')

    # 直接通过plot函数获取图表
    figs = cerebro.plot(style='candlestick')

    # 只有在图表成功创建时处理
    if figs and len(figs) > 0 and len(figs[0]) > 0:
        # 获取所有轴对象
        fig = figs[0][0]
        axes = fig.axes

        # 尝试找到TradeLine子图
        for ax in axes:
            if hasattr(ax, 'get_title') and 'TradeLine' in ax.get_title():
                # 设置Y轴范围
                ax.set_ylim(-2, 2)
                # 添加一个直观的网格
                ax.grid(True, linestyle='--', alpha=0.7)
                # 设置清晰的Y轴刻度
                ax.set_yticks([-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2])
                # 绘制参考线
                ax.axhline(y=2, color='green', linestyle='-', alpha=0.3)
                ax.axhline(y=-2, color='red', linestyle='-', alpha=0.3)

        # 强制刷新图形
        fig.tight_layout()
        plt.show()
