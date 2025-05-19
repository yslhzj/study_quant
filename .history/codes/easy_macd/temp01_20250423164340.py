# -*- coding: utf-8 -*-
# @Author : huanglei
# @File : 课程第十阶段：终章 - 理解 Analyzer 在参数优化中的角色.py

import datetime
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA
import pprint
from collections import OrderedDict

# --- 自定义 Observer (保持不变) ---
class MACDHistoObserver(bt.Observer):
    lines = ('histo',)
    plotinfo = dict(plot=True, subplot=True, plotname='MACD Histogram')
    def __init__(self): super().__init__(); self.lines.histo = self._owner.macd_histo.histo
    def next(self): pass

# --- 自定义 Analyzer (保持不变) ---
class GrossProfitFactorAnalyzer(bt.Analyzer):
    def __init__(self):
        super().__init__(); self.total_won_pnl = 0.0; self.total_lost_pnl = 0.0
        self.won_count = 0; self.lost_count = 0
    def notify_trade(self, trade):
        if trade.isclosed:
            pnl = trade.pnl
            if pnl > 0: self.total_won_pnl += pnl; self.won_count += 1
            elif pnl < 0: self.total_lost_pnl += pnl; self.lost_count += 1
    def stop(self):
        avg_won = self.total_won_pnl / self.won_count if self.won_count else 0.0
        avg_lost = self.total_lost_pnl / self.lost_count if self.lost_count else 0.0
        factor = abs(avg_won / avg_lost) if avg_lost else float('inf') if avg_won else 0.0
        self.rets = OrderedDict([('avg_won_pnl', avg_won), ('avg_lost_pnl', avg_lost), ('gross_profit_factor', factor)])

# --- 策略定义 (添加一个可优化参数) ---
class TestStrategy(bt.Strategy):
    # 添加 EMA 周期作为可优化参数
    params = (
        ('fast_ema', 12), # 快速EMA周期
        ('slow_ema', 26), # 慢速EMA周期
        ('signal_ema', 9), # 信号线EMA周期
    )
    def log(self, txt, dt=None): dt = dt or self.datas[0].datetime.date(0)
    def __init__(self):
        self.dataclose = self.datas[0].close; self.order = None
        # 使用 params 中的值来计算指标
        me1 = EMA(self.data, period=self.p.fast_ema)
        me2 = EMA(self.data, period=self.p.slow_ema)
        self.macd = me1 - me2
        self.signal = EMA(self.macd, period=self.p.signal_ema)
        self.macd_histo = self.macd - self.signal # 直接计算 Histo
        self.macd_histo.plotinfo.plot = False # 禁用默认绘制
        self.bar_executed_close = 0

        # 打印当前使用的参数 (在优化时会看到不同组合)
        print(f"Strategy Init - Params: fast={self.p.fast_ema}, slow={self.p.slow_ema}, signal={self.p.signal_ema}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]: return
        if order.status in [order.Completed]:
            if order.isbuy(): self.bar_executed_close = self.dataclose[0]
        self.order = None
    def notify_trade(self, trade): pass
    def next(self):
        if self.order: return
        if not self.position:
            condition1 = self.macd_histo[-1]; condition2 = self.macd_histo[0]
            if condition1 < 0 and condition2 > 0: self.order = self.buy()
        else:
            condition = (self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
            if condition > 0.1 or condition < -0.1: self.order = self.sell()

# --- 主程序入口 ---
if __name__ == '__main__':
    # --- 重点说明：优化场景 ---
    # 在实际优化中，我们会使用 cerebro.optstrategy 来代替 addstrategy
    # 例如:
    # cerebro.optstrategy(
    #     TestStrategy,
    #     fast_ema=range(10, 15), # 测试 fast_ema 从 10 到 14
    #     slow_ema=[25, 26]       # 测试 slow_ema 为 25 和 26
    #     # signal_ema 保持默认值 9
    # )
    # 这会运行 (14-10+1) * 2 = 10次回测

    # --- 本示例仍使用 addstrategy 进行单次回测，但解释优化概念 ---
    cerebro = bt.Cerebro(stdstats=False, optreturn=True) # 设置 optreturn=True (优化时常用)
    cerebro.addstrategy(TestStrategy, fast_ema=12, slow_ema=26, signal_ema=9) # 单次运行参数

    # --- 添加 Observers (保持不变) ---
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell, barplot=True)
    cerebro.addobserver(MACDHistoObserver)

    # --- 添加用于评估优化的核心 Analyzers ---
    # 在优化中，通常关注几个关键指标
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days, compression=1, factor=252, annualize=True, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    # 自定义 Analyzer 也可以用于优化评估
    cerebro.addanalyzer(GrossProfitFactorAnalyzer, _name='grossprofitfactor')
    # TimeReturn 和 PyFolio 在单次优化运行结果中不太常用，但在选出最优参数后进行详细分析时有用
    # cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years, _name='timereturn_yearly')
    # cerebro.addanalyzer(bt.analyzers.PyFolio, timeframe=bt.TimeFrame.Days, _name='pyfolio')

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

    # --- 运行回测 ---
    # 对于单次运行，results 是 [OptReturn] 对象列表 (如果 optreturn=True)
    # 或 [Strategy] 对象列表 (如果 optreturn=False)
    # 对于优化运行 (optstrategy)，results 是多个 OptReturn/Strategy 对象的列表的列表
    results = cerebro.run()

    # --- 分析结果 (以单次运行为例，演示如何从 OptReturn 提取) ---
    if results:
        # 因为是单次运行，取第一个结果
        # 如果是优化，你需要遍历 results 列表中的每个子列表（每个子列表代表一组参数的结果）
        run_result = results[0] # 对于单次运行，是 results[0]
                               # 对于优化，可能是 results[0][0], results[1][0]...

        print("-" * 30 + " Accessing Results (optreturn=True) " + "-" * 30)

        # run_result 是一个 OptReturn 对象 (或 Strategy 对象，如果 optreturn=False)
        # 它包含 params 和 analyzers

        # 访问参数
        print("Parameters used:", run_result.params) # OptReturn 有 params 属性

        # 访问 Analyzers
        print("\n--- Key Analyzer Metrics ---")
        try:
            # TradeAnalyzer
            ta = run_result.analyzers.tradeanalyzer.get_analysis()
            print(f"  Net Profit: {ta.pnl.net.total:.2f}")
        except AttributeError: print("  TradeAnalyzer result not found.")

        try:
            # SharpeRatio
            sr = run_result.analyzers.sharpe.get_analysis()
            print(f"  Sharpe Ratio: {sr.get('sharperatio', 'N/A')}")
        except AttributeError: print("  SharpeRatio result not found.")

        try:
            # DrawDown
            dd = run_result.analyzers.drawdown.get_analysis()
            print(f"  Max Drawdown: {dd.max.drawdown:.2f}%")
        except AttributeError: print("  DrawDown result not found.")

        try:
            # SQN
            sq = run_result.analyzers.sqn.get_analysis()
            print(f"  SQN: {sq.get('sqn', 'N/A')}")
        except AttributeError: print("  SQN result not found.")

        try:
            # Custom Analyzer
            gpf = run_result.analyzers.grossprofitfactor.get_analysis()
            print(f"  Gross Profit Factor: {gpf.get('gross_profit_factor', 'N/A'):.2f}")
        except AttributeError: print("  GrossProfitFactor result not found.")

        # --- 优化场景说明 ---
        print("\n--- Optimization Context ---")
        print("In a real optimization, you would collect these metrics for each parameter combination.")
        print("Then, you could sort or filter based on a chosen metric (e.g., highest Sharpe Ratio,")
        print("highest Net Profit with Drawdown below a threshold) to find the 'best' parameters.")
        print("The 'optreturn=True' setting makes this process efficient by only returning params and analyzers.")
        print("If 'optreturn=False', 'run_result' would be the full Strategy object,")
        print("allowing deeper inspection but consuming more memory during optimization.")

    else:
        print("Cerebro run returned no results.")


    # 最终价值需要从 cerebro 获取，而不是 result 对象
    print("-" * 30 + " Final Portfolio Value " + "-" * 30)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 在优化场景下，通常不绘制图表，除非是针对选出的最优参数进行单独回测时
    # cerebro.plot(style='candlestick')