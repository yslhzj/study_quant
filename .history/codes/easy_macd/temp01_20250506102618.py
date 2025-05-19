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
import pandas as pd
import numpy as np
import time

# --- 自定义 Observer (保持不变) ---

class MACDHistoObserver(bt.Observer):
    lines = ('histo',)
    plotinfo = dict(plot=True, subplot=True, plotname='MACD Histogram')

    def __init__(self):
        super().__init__()
        # 直接使用macd_histo，不需要访问.histo属性
        self.lines.histo = self._owner.macd_histo

    def next(self): pass

# --- 自定义 Analyzer (保持不变) ---

class GrossProfitFactorAnalyzer(bt.Analyzer):
    def __init__(self):
        super().__init__()
        self.total_won_pnl = 0.0
        self.total_lost_pnl = 0.0
        self.won_count = 0
        self.lost_count = 0

    def notify_trade(self, trade):
        if trade.isclosed:
            pnl = trade.pnl
            if pnl > 0:
                self.total_won_pnl += pnl
                self.won_count += 1
            elif pnl < 0:
                self.total_lost_pnl += pnl
                self.lost_count += 1

    def stop(self):
        avg_won = self.total_won_pnl / self.won_count if self.won_count else 0.0
        avg_lost = self.total_lost_pnl / self.lost_count if self.lost_count else 0.0
        factor = abs(
            avg_won / avg_lost) if avg_lost else float('inf') if avg_won else 0.0
        self.rets = OrderedDict(
            [('avg_won_pnl', avg_won), ('avg_lost_pnl', avg_lost), ('gross_profit_factor', factor)])

# --- 策略定义 (添加一个可优化参数) ---

class TestStrategy(bt.Strategy):
    # 添加 EMA 周期作为可优化参数
    params = (
        ('fast_ema', 12),  # 快速EMA周期
        ('slow_ema', 26),  # 慢速EMA周期
        ('signal_ema', 9),  # 信号线EMA周期
    )
    def log(self, txt, dt=None): dt = dt or self.datas[0].datetime.date(0)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        # 使用 params 中的值来计算指标
        me1 = EMA(self.data, period=self.p.fast_ema)
        me2 = EMA(self.data, period=self.p.slow_ema)
        self.macd = me1 - me2
        self.signal = EMA(self.macd, period=self.p.signal_ema)
        self.macd_histo = self.macd - self.signal  # 直接计算 Histo
        self.bar_executed_close = 0

        # 打印当前使用的参数 (在优化时会看到不同组合)
        # print(f"Strategy Init - Params: fast={self.p.fast_ema}, slow={self.p.slow_ema}, signal={self.p.signal_ema}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.bar_executed_close = self.dataclose[0]
        self.order = None

    def notify_trade(self, trade): pass

    def next(self):
        if self.order:
            return
        if not self.position:
            condition1 = self.macd_histo[-1]
            condition2 = self.macd_histo[0]
            if condition1 < 0 and condition2 > 0:
                self.order = self.buy()
        else:
            condition = (
                self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
            if condition > 0.1 or condition < -0.1:
                self.order = self.sell()

# --- 主程序入口 ---
if __name__ == '__main__':
    # --- 优化参数范围设置 ---
    fast_range = range(8, 16)     # 测试 fast_ema 从 8 到 15
    slow_range = range(20, 31, 2)  # 测试 slow_ema 从 20 到 30，步长为2
    signal_range = range(7, 12)   # 测试 signal_ema 从 7 到 11

    # 输出参数优化范围信息
    print("="*50)
    print("参数优化范围:")
    print(f"fast_ema: {list(fast_range)} (共{len(fast_range)}个值)")
    print(f"slow_ema: {list(slow_range)} (共{len(slow_range)}个值)")
    print(f"signal_ema: {list(signal_range)} (共{len(signal_range)}个值)")
    print(f"总共组合数: {len(fast_range) * len(slow_range) * len(signal_range)}")
    print("="*50)

    # --- 改用 optstrategy 进行参数优化 ---
    # 设置 optreturn=True, maxcpus=1使优化过程更易于观察
    cerebro = bt.Cerebro(stdstats=False, optreturn=True, maxcpus=1)

    # 使用optstrategy进行参数优化
    cerebro.optstrategy(
        TestStrategy,
        fast_ema=fast_range,
        slow_ema=slow_range,
        signal_ema=signal_range
    )

    # --- 添加 Observers (保持不变) ---
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell, barplot=True)
    cerebro.addobserver(MACDHistoObserver)

    # --- 添加用于评估优化的核心 Analyzers ---
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days,
                        compression=1, factor=252, annualize=True, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(GrossProfitFactorAnalyzer, _name='grossprofitfactor')

    # --- 数据加载 (保持不变) ---
603186
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

    # --- 运行优化回测 ---
    print("\n" + "=" * 15 + " 开始参数优化过程 " + "=" * 15)
    print("正在运行参数优化，这可能需要一些时间...")
    print("优化引擎将尝试每种参数组合，评估其性能指标")
    print("="*50)

    start_time = time.time()
    results = cerebro.run()
    end_time = time.time()

    elapsed_time = end_time - start_time
    print(f"参数优化完成! 耗时: {elapsed_time:.2f}秒")
    print(f"共测试了 {len(results)} 组参数")
    print("="*50)

    # --- 收集优化结果 ---
    print("\n" + "=" * 15 + " 收集和处理优化结果 " + "=" * 15)
    # 创建一个列表来存储所有结果
    result_list = []
    valid_count = 0

    # 遍历所有优化结果
    for i, result in enumerate(results):
        params = result[0].params  # 获取参数

        # 间隔显示处理进度
        if i % 40 == 0 or i == len(results) - 1:
            print(
                f"正在处理优化结果: {i+1}/{len(results)} ({(i+1)/len(results)*100:.1f}%)")

        # 从analyizers中提取指标
        try:
            ta = result[0].analyzers.tradeanalyzer.get_analysis()
            net_profit = ta.pnl.net.total if hasattr(
                ta, 'pnl') and hasattr(ta.pnl, 'net') else 0
            trades = ta.total.closed if hasattr(ta, 'total') else 0
        except (AttributeError, KeyError):
            net_profit = 0
            trades = 0

        try:
            sr = result[0].analyzers.sharpe.get_analysis()
            sharpe = sr.get('sharperatio', 0)
        except (AttributeError, KeyError):
            sharpe = 0

        try:
            dd = result[0].analyzers.drawdown.get_analysis()
            max_drawdown = dd.max.drawdown
        except (AttributeError, KeyError):
            max_drawdown = 100  # 如果无法获取，则假设最坏情况

        try:
            sqn_val = result[0].analyzers.sqn.get_analysis().sqn
        except (AttributeError, KeyError):
            sqn_val = 0

        try:
            gpf = result[0].analyzers.grossprofitfactor.get_analysis()
            profit_factor = gpf.get('gross_profit_factor', 0)
        except (AttributeError, KeyError):
            profit_factor = 0

        # 将结果存储到列表中
        result_list.append({
            'fast_ema': params.fast_ema,
            'slow_ema': params.slow_ema,
            'signal_ema': params.signal_ema,
            'net_profit': net_profit,
            'max_drawdown': max_drawdown,
            'sharpe': sharpe,
            'sqn': sqn_val,
            'profit_factor': profit_factor,
            'trades': trades
        })

        # 记录有效交易的数量
        if trades > 0:
            valid_count += 1

    print(
        f"处理完成! 有效参数组合数: {valid_count}/{len(results)} ({valid_count/len(results)*100:.1f}%)")
    print("="*50)

    # 转换为DataFrame以便于分析
    results_df = pd.DataFrame(result_list)

    # 至少要有交易才能判断策略好坏
    results_df = results_df[results_df['trades'] > 0]

    if len(results_df) > 0:
        # 输出原始数据统计信息
        print("\n" + "=" * 15 + " 优化结果统计 " + "=" * 15)
        print("各指标的统计描述:")
        print(results_df[['net_profit', 'max_drawdown', 'sharpe',
              'sqn', 'profit_factor', 'trades']].describe())
        print("="*50)

        # 不同参数组合的分布统计
        fast_counts = results_df['fast_ema'].value_counts().sort_index()
        slow_counts = results_df['slow_ema'].value_counts().sort_index()
        signal_counts = results_df['signal_ema'].value_counts().sort_index()

        print("\n参数分布情况 (有效组合中各参数值的出现次数):")
        print("fast_ema分布:")
        for fast, count in fast_counts.items():
            print(
                f"  - fast_ema={fast}: {count}次 ({count/len(results_df)*100:.1f}%)")

        print("\nslow_ema分布:")
        for slow, count in slow_counts.items():
            print(
                f"  - slow_ema={slow}: {count}次 ({count/len(results_df)*100:.1f}%)")

        print("\nsignal_ema分布:")
        for signal, count in signal_counts.items():
            print(
                f"  - signal_ema={signal}: {count}次 ({count/len(results_df)*100:.1f}%)")

        print("\n" + "=" * 15 + " 开始评分计算 " + "=" * 15)
        # 计算综合得分：高收益、低回撤、高夏普、高SQN、高盈亏比
        # 将各指标归一化
        print("1. 对各指标进行归一化处理")
        results_df['norm_profit'] = (results_df['net_profit'] - results_df['net_profit'].min()) / \
            (results_df['net_profit'].max() -
             results_df['net_profit'].min() + 1e-10)

        # 对于回撤，较低值更好，所以反转归一化
        if results_df['max_drawdown'].max() > results_df['max_drawdown'].min():
            results_df['norm_drawdown'] = 1 - (results_df['max_drawdown'] - results_df['max_drawdown'].min()) / \
                (results_df['max_drawdown'].max() -
                 results_df['max_drawdown'].min())
        else:
            results_df['norm_drawdown'] = 1.0

        results_df['norm_sharpe'] = (results_df['sharpe'] - results_df['sharpe'].min()) / \
            (results_df['sharpe'].max() - results_df['sharpe'].min() + 1e-10)

        results_df['norm_sqn'] = (results_df['sqn'] - results_df['sqn'].min()) / \
            (results_df['sqn'].max() - results_df['sqn'].min() + 1e-10)

        results_df['norm_pf'] = (results_df['profit_factor'] - results_df['profit_factor'].min()) / \
            (results_df['profit_factor'].max() -
             results_df['profit_factor'].min() + 1e-10)

        # 计算综合得分，收益和回撤是最重要的因素
        print("2. 根据指定权重计算综合得分:")
        print("   - 收益权重: 35%")
        print("   - 回撤权重: 35%")
        print("   - 夏普比率权重: 10%")
        print("   - SQN权重: 10%")
        print("   - 盈亏比权重: 10%")

        results_df['score'] = (
            results_df['norm_profit'] * 0.35 +  # 收益权重35%
            results_df['norm_drawdown'] * 0.35 +  # 回撤权重35%
            results_df['norm_sharpe'] * 0.1 +    # 夏普比率权重10%
            results_df['norm_sqn'] * 0.1 +       # SQN权重10%
            results_df['norm_pf'] * 0.1          # 盈亏比权重10%
        )

        # 按综合得分排序
        print("3. 按综合得分排序结果")
        results_df = results_df.sort_values('score', ascending=False)
        print("="*50)

        # 打印前10个最佳参数组合
        print("\n----- 最佳参数组合（按综合得分排序） -----")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        top_10 = results_df[['fast_ema', 'slow_ema', 'signal_ema', 'net_profit',
                             'max_drawdown', 'sharpe', 'sqn', 'profit_factor', 'trades', 'score']].head(10)
        print(top_10)

        # 找出收益最高的参数
        best_profit = results_df.loc[results_df['net_profit'].idxmax()]
        print("\n----- 收益最高的参数组合 -----")
        print(
            f"fast_ema: {best_profit['fast_ema']}, slow_ema: {best_profit['slow_ema']}, signal_ema: {best_profit['signal_ema']}")
        print(
            f"净收益: {best_profit['net_profit']:.2f}, 最大回撤: {best_profit['max_drawdown']:.2f}%, 夏普比率: {best_profit['sharpe']:.2f}")
        print(
            f"综合得分: {best_profit['score']:.4f}, 排名: {results_df['score'].rank(ascending=False)[best_profit.name]}/{len(results_df)}")

        # 找出回撤最小的参数
        best_drawdown = results_df.loc[results_df['max_drawdown'].idxmin()]
        print("\n----- 回撤最小的参数组合 -----")
        print(
            f"fast_ema: {best_drawdown['fast_ema']}, slow_ema: {best_drawdown['slow_ema']}, signal_ema: {best_drawdown['signal_ema']}")
        print(
            f"净收益: {best_drawdown['net_profit']:.2f}, 最大回撤: {best_drawdown['max_drawdown']:.2f}%, 夏普比率: {best_drawdown['sharpe']:.2f}")
        print(
            f"综合得分: {best_drawdown['score']:.4f}, 排名: {results_df['score'].rank(ascending=False)[best_drawdown.name]}/{len(results_df)}")

        # 找出综合得分最高的参数
        best_overall = results_df.iloc[0]
        print("\n----- 综合得分最高的参数组合 -----")
        print(
            f"fast_ema: {best_overall['fast_ema']}, slow_ema: {best_overall['slow_ema']}, signal_ema: {best_overall['signal_ema']}")
        print(
            f"净收益: {best_overall['net_profit']:.2f}, 最大回撤: {best_overall['max_drawdown']:.2f}%, 夏普比率: {best_overall['sharpe']:.2f}")
        print(
            f"SQN: {best_overall['sqn']:.2f}, 盈亏比: {best_overall['profit_factor']:.2f}, 交易次数: {int(best_overall['trades'])}")
        print(f"综合得分: {best_overall['score']:.4f} (最高分)")

        # 使用最优参数再次运行单次回测并绘制图表
        print("\n" + "=" * 15 + " 使用最优参数进行验证回测 " + "=" * 15)
        cerebro_best = bt.Cerebro(stdstats=False)
        cerebro_best.addstrategy(TestStrategy,
                                 fast_ema=int(best_overall['fast_ema']),
                                 slow_ema=int(best_overall['slow_ema']),
                                 signal_ema=int(best_overall['signal_ema']))

        # 添加观察器
        cerebro_best.addobserver(bt.observers.Broker)
        cerebro_best.addobserver(bt.observers.Trades)
        cerebro_best.addobserver(bt.observers.BuySell, barplot=True)
        cerebro_best.addobserver(MACDHistoObserver)

        # 添加分析器
        cerebro_best.addanalyzer(
            bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
        cerebro_best.addanalyzer(
            bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days, _name='sharpe')
        cerebro_best.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

        # 添加相同的数据
        cerebro_best.adddata(data)

        # 设置相同的现金和手续费
        cerebro_best.broker.setcash(10000.0)
        cerebro_best.addsizer(bt.sizers.FixedSize, stake=100)
        cerebro_best.broker.setcommission(commission=0.005)

        print(
            f"使用最优参数运行单次回测: fast_ema={int(best_overall['fast_ema'])}, slow_ema={int(best_overall['slow_ema'])}, signal_ema={int(best_overall['signal_ema'])}")
        print("开始验证回测...")
        best_result = cerebro_best.run()

        # 提取验证回测结果
        try:
            ta_val = best_result[0].analyzers.tradeanalyzer.get_analysis()
            total_trades = ta_val.total.closed if hasattr(
                ta_val, 'total') else 0
            win_trades = ta_val.won.total if hasattr(ta_val, 'won') else 0
            loss_trades = ta_val.lost.total if hasattr(ta_val, 'lost') else 0
            win_rate = win_trades / total_trades * 100 if total_trades else 0

            dd_val = best_result[0].analyzers.drawdown.get_analysis()
            max_dd = dd_val.max.drawdown if hasattr(dd_val, 'max') else 0

            print("\n验证回测结果:")
            print(f"总交易次数: {total_trades}")
            print(
                f"获利交易: {win_trades}, 亏损交易: {loss_trades}, 胜率: {win_rate:.2f}%")
            print(f"最大回撤: {max_dd:.2f}%")
        except:
            print("无法获取详细的验证回测结果")

        final_value = cerebro_best.broker.getvalue()
        initial_value = 10000.0
        total_return = (final_value - initial_value) / initial_value * 100

        print(f"初始资金: {initial_value:.2f}")
        print(f"最终资产: {final_value:.2f}")
        print(f"总收益率: {total_return:.2f}%")
        print("="*50)

        # 绘制图表
        print("\n正在生成回测图表...")
        cerebro_best.plot(style='candlestick')
    else:
        print("没有找到有效的交易结果，请调整参数范围再试。")
