# Python实用宝典
# 2020/04/20
# 转载请注明出处
import datetime,pprint
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA


class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
    )

    def log(self, txt, dt=None):
        return
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
        me1.plotinfo.plot = False 
        me2 = EMA(self.data, period=26)
        me2.plotinfo.plot = False 
        self.macd = me1 - me2
        self.signal = EMA(self.macd, period=9)
        self.signal.plotinfo.plot = False 

        macd_histo = bt.indicators.MACDHisto(self.data)
        macd_histo.plotinfo.plot = False  # 设置不显示在图表中

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
            condition = (self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
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
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    # 添加年回报率分析器
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years, _name='timereturn_yearly')
    # 添加月回报率分析器 (可选)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Months, _name='timereturn_monthly')
    # cerebro.addobserver(bt.observers.BuySell)  # 买卖点标记
    # cerebro.addobserver(bt.observers.Value)    # 资产价值曲线
    # cerebro.addobserver(bt.observers.Trades)   # 交易详情

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    results = cerebro.run()
    first_strategy = results[0]  # 获取第一个策略实例

    # 打印 TradeAnalyzer 结果
    trade_analysis = first_strategy.analyzers.tradeanalyzer.get_analysis()
    print("------ TradeAnalyzer Analysis ------")
    print(f"Total Closed Trades: {trade_analysis.total.closed}")
    print(f"Total Net Profit: {trade_analysis.pnl.net.total:.2f}")
    print(f"Winning Trades: {trade_analysis.won.total}")
    print(f"Losing Trades: {trade_analysis.lost.total}")

    # 打印 SharpeRatio 结果
    sharpe_ratio = first_strategy.analyzers.sharpe.get_analysis()
    print("------ SharpeRatio Analysis ------")
    print(f"Sharpe Ratio: {sharpe_ratio.get('sharperatio', 'N/A')}")

    # 打印 DrawDown 结果
    drawdown = first_strategy.analyzers.drawdown.get_analysis()
    print("------ DrawDown Analysis ------")
    print(f"Max Drawdown: {drawdown.max.drawdown:.2f}%")
    print(f"Max Drawdown Money: {drawdown.max.moneydown:.2f}")

    # 打印 SQN 结果
    sqn = first_strategy.analyzers.sqn.get_analysis()
    print("------ SQN Analysis ------")
    print(f"SQN: {sqn.get('sqn', 'N/A')}")
    #(可选) 打印月回报率结果
    print("-" * 30 + " Monthly TimeReturn Analysis " + "-" * 30)
    try:
        timereturn_monthly_analysis = first_strategy.analyzers.timereturn_monthly.get_analysis()
        pprint.pprint(timereturn_monthly_analysis)
    except Exception as e:
        print(f"Monthly TimeReturn: Not available ({e})")
    

    # 打印最终价值
    print("-" * 30 + " Final Portfolio Value " + "-" * 30)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 绘制图表
    cerebro.plot()