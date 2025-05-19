# -*- coding: utf-8 -*-
# @Author : huanglei
# @File : 课程第九阶段：创建简单自定义 Analyzer - 计算特定指标.py

import datetime
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA
import pprint
from collections import OrderedDict # 导入 OrderedDict，让结果字典保持顺序

# --- 自定义 Observer (保持不变) ---
class MACDHistoObserver(bt.Observer):
    lines = ('histo',)
    plotinfo = dict(plot=True, subplot=True, plotname='MACD Histogram')
    def __init__(self):
        super().__init__()
        self.lines.histo = self._owner.macd_histo.histo
    def next(self): pass

# --- 自定义 Analyzer ---
# 计算基于毛利润的 平均盈利/平均亏损 比率
class GrossProfitFactorAnalyzer(bt.Analyzer):
    # 初始化方法
    def __init__(self):
        # 调用父类初始化
        super().__init__()
        # 初始化存储变量
        self.total_won_pnl = 0.0 # 总盈利 (毛利)
        self.total_lost_pnl = 0.0 # 总亏损 (毛利, 负数)
        self.won_count = 0 # 盈利次数
        self.lost_count = 0 # 亏损次数

    # 交易通知方法
    def notify_trade(self, trade):
        # 只处理已关闭的交易
        if trade.isclosed:
            # 获取毛利润 (trade.pnl)
            pnl = trade.pnl
            # 判断盈亏
            if pnl > 0:
                # 累加总盈利和次数
                self.total_won_pnl += pnl
                self.won_count += 1
            elif pnl < 0:
                # 累加总亏损和次数
                self.total_lost_pnl += pnl # pnl 本身是负数
                self.lost_count += 1
            # pnl == 0 的交易忽略

    # 回测结束时调用
    def stop(self):
        # 计算平均盈利
        avg_won_pnl = self.total_won_pnl / self.won_count if self.won_count > 0 else 0.0
        # 计算平均亏损
        avg_lost_pnl = self.total_lost_pnl / self.lost_count if self.lost_count > 0 else 0.0

        # 计算平均盈利/平均亏损绝对值 (处理除零)
        if avg_lost_pnl != 0.0:
            gross_profit_factor = abs(avg_won_pnl / avg_lost_pnl)
        elif avg_won_pnl > 0.0:
            gross_profit_factor = float('inf') # 有盈利无亏损，比率为无穷大
        else:
            gross_profit_factor = 0.0 # 无盈利无亏损

        # 将结果存储在 self.rets 字典中 (Analyzer 默认创建的)
        # 使用 OrderedDict 可以让结果按添加顺序排列
        self.rets = OrderedDict()
        self.rets['total_won_pnl'] = self.total_won_pnl
        self.rets['won_count'] = self.won_count
        self.rets['avg_won_pnl'] = avg_won_pnl
        self.rets['total_lost_pnl'] = self.total_lost_pnl
        self.rets['lost_count'] = self.lost_count
        self.rets['avg_lost_pnl'] = avg_lost_pnl
        self.rets['gross_profit_factor'] = gross_profit_factor

    # 返回分析结果的方法 (默认实现已返回 self.rets)
    # def get_analysis(self):
    #     return self.rets

# --- 策略定义 (保持不变) ---
class TestStrategy(bt.Strategy):
    params = (('maperiod', 15),)
    def log(self, txt, dt=None): dt = dt or self.datas[0].datetime.date(0)
    def __init__(self):
        self.dataclose = self.datas[0].close; self.order = None
        me1 = EMA(self.data, period=12); me2 = EMA(self.data, period=26)
        self.macd = me1 - me2; self.signal = EMA(self.macd, period=9)
        self.macd_histo = bt.indicators.MACDHisto(self.data); self.macd_histo.plotinfo.plot = False
        self.bar_executed_close = 0
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]: return
        if order.status in [order.Completed]:
            if order.isbuy(): self.bar_executed_close = self.dataclose[0]
        self.order = None
    def notify_trade(self, trade): pass
    def next(self):
        if self.order: return
        if not self.position:
            condition1 = self.macd[-1] - self.signal[-1]; condition2 = self.macd[0] - self.signal[0]
            if condition1 < 0 and condition2 > 0: self.order = self.buy()
        else:
            condition = (self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
            if condition > 0.1 or condition < -0.1: self.order = self.sell()

# --- 主程序入口 ---
if __name__ == '__main__':
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.addstrategy(TestStrategy)

    # --- 添加 Observers ---
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell, barplot=True)
    cerebro.addobserver(MACDHistoObserver)

    # --- 添加 Analyzers ---
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years, _name='timereturn_yearly')
    cerebro.addanalyzer(bt.analyzers.PyFolio, timeframe=bt.TimeFrame.Days, _name='pyfolio')
    # --- 添加自定义 Analyzer ---
    cerebro.addanalyzer(GrossProfitFactorAnalyzer, _name='grossprofitfactor')
    # -----------------------

    # --- 数据加载 (保持不变) ---
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '603186.csv')
    data = bt.feeds.GenericCSVData(
        dataname=datapath, fromdate=datetime.datetime(2010, 1, 1),
        todate=datetime.datetime(2020, 4, 12), dtformat='%Y%m%d',
        datetime=2, open=3, high=4, low=5, close=6, volume=10,
        timeframe=bt.TimeFrame.Days, reverse=True)
    cerebro.adddata(data)

    # --- 设置 (保持不变) ---
    cerebro.broker.setcash(10000.0)
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    cerebro.broker.setcommission(commission=0.005)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    results = cerebro.run()
    first_strategy = results[0]

    # --- 打印 Analyzer 结果 ---
    # ... (省略其他 Analyzer 打印) ...

    # --- 打印自定义 Analyzer 结果 ---
    print("-" * 30 + " Custom Gross Profit Factor Analyzer " + "-" * 30)
    try:
        gpf_analysis = first_strategy.analyzers.grossprofitfactor.get_analysis()
        pprint.pprint(gpf_analysis) # 使用 pprint 打印有序字典
        # print(f"Gross Profit Factor (Avg Won PnL / |Avg Lost PnL|): {gpf_analysis.get('gross_profit_factor', 'N/A'):.2f}")
    except AttributeError:
        print("GrossProfitFactorAnalyzer not found or analysis failed.")
    except Exception as e:
        print(f"Error getting custom analyzer result: {e}")
    # -----------------------------

    print("-" * 30 + " Final Portfolio Value " + "-" * 30)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # cerebro.plot(style='candlestick') # 可选绘制