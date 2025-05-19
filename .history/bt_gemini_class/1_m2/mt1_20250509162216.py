# module_5_script.py
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# 功能: 从 `__future__` 模块导入特性，确保代码在不同 Python 版本间的兼容性。
# (大白话: 就像给你的代码装上一个“万能翻译器”，让它在老版本和新版本的Python上都能跑得顺畅。)
import backtrader as bt
# 功能: 导入 `backtrader` 库，并将其简写为 `bt`，方便后续调用。
# (大白话: 引入一个叫 `backtrader` 的“工具箱”，以后用 `bt` 这个小名就能找到它里面的工具。)
import pandas as pd
# 功能: 导入 `pandas` 库，并将其简写为 `pd`，用于数据处理。
# (大白话: 引入一个叫 `pandas` 的“数据表格处理专家”，以后用 `pd` 这个小名就能让它帮忙整理数据。)
import datetime
# 功能: 导入 `datetime` 模块，用于处理日期和时间。
# (大白话: 引入一个“时间管理员”模块，专门处理日期和时间相关的事情。)
import os
# 功能: 导入 `os` 模块，用于与操作系统交互，例如文件路径操作。
# (大白话: 引入一个“系统助手”模块，可以帮你找到文件在哪里，或者创建文件夹之类的。)


class SmaCrossStrategy(bt.Strategy):
# 功能: 定义一个名为 `SmaCrossStrategy` 的类，它继承自 `backtrader.Strategy` 类，表示这是一个交易策略。
# (大白话: 我们正在创建一个“交易机器人”的设计图，这个机器人叫做 `SmaCrossStrategy`，它会按照 `backtrader` 框架的规矩来行动。)
    params = (
# 功能: 开始定义策略的参数。
# (大白话: 给我们的“交易机器人”设置一些可以调整的“旋钮”。)
        ('fast_ma_period', 2),
# 功能: 定义一个名为 `fast_ma_period` 的参数，默认值为 `2`，代表快速移动平均线的周期。
# (大白话: 设置一个“快线旋钮”，默认值是2，用来计算短期平均价格。)
        ('slow_ma_period', 3),
# 功能: 定义一个名为 `slow_ma_period` 的参数，默认值为 `3`，代表慢速移动平均线的周期。
# (大白话: 设置一个“慢线旋钮”，默认值是3，用来计算稍长期一点的平均价格。)
    )

    def log(self, txt, dt=None):
# 功能: 定义一个名为 `log` 的方法，用于记录日志信息，包含日期和自定义文本。
# (大白话: 给机器人设计一个“小本本记录员”，它会把重要的事情和发生时间记下来。)
        dt = dt or self.datas[0].datetime.date(0)
# 功能: 如果未提供日期 `dt`，则使用当前数据点的日期。
# (大白话: 如果记录员没拿到具体的日期，就用当前交易日的日期。)
        print(f'{dt.isoformat()}, {txt}')
# 功能: 打印格式化的日志信息，包括ISO格式的日期和传入的文本。
# (大白话: 把日期和事情内容，按照“年-月-日, 事情描述”的格式打印出来，方便查看。)

    def __init__(self):
# 功能: 定义策略的构造函数（初始化方法），在策略实例创建时执行。
# (大白话: 这是“交易机器人”的“出厂设置”环节，机器人一造出来就会先做这些准备工作。)
        self.dataclose = self.datas[0].close
# 功能: 获取第一个数据源（通常是股票数据）的收盘价序列，并赋值给 `self.dataclose`。
# (大白话: 机器人拿到股价数据后，把每天的“收盘价”这条线单独存起来，方便以后看。)
        self.order = None
# 功能: 初始化 `self.order` 变量为 `None`，用于跟踪当前活动的订单。
# (大白话: 机器人一开始手上没有“交易指令单”，所以先设为空。)
        self.buyprice = None
# 功能: 初始化 `self.buyprice` 变量为 `None`，用于记录买入价格。
# (大白话: 机器人还没买过东西，所以“买入价格”先记为空。)
        self.buycomm = None
# 功能: 初始化 `self.buycomm` 变量为 `None`，用于记录买入时的手续费。
# (大白话: 机器人还没买过东西，所以“买入手续费”也先记为空。)

        self.sma_fast = bt.indicators.SimpleMovingAverage(
# 功能: 创建一个简单移动平均线（SMA）指标实例，作为快速移动平均线。
# (大白话: 机器人开始计算“短期平均价格线”。)
            self.datas[0], period=self.params.fast_ma_period
# 功能: 指定该SMA指标作用于第一个数据源，并使用策略参数 `fast_ma_period` 作为其计算周期。
# (大白话: 告诉机器人用我们之前设置的“快线旋钮”的周期（比如2天）来计算这个短期平均价格。)
        )
        self.sma_slow = bt.indicators.SimpleMovingAverage(
# 功能: 创建另一个简单移动平均线（SMA）指标实例，作为慢速移动平均线。
# (大白话: 机器人再计算一个“稍长期平均价格线”。)
            self.datas[0], period=self.params.slow_ma_period
# 功能: 指定该SMA指标作用于第一个数据源，并使用策略参数 `slow_ma_period` 作为其计算周期。
# (大白话: 告诉机器人用我们之前设置的“慢线旋钮”的周期（比如3天）来计算这个稍长期平均价格。)
        )

        self.sma_crossover = bt.indicators.CrossOver(
# 功能: 创建一个交叉（CrossOver）指标实例，用于检测两条线的交叉情况。
# (大白话: 机器人现在要看这两条平均价格线有没有“相交”。)
            self.sma_fast, self.sma_slow
# 功能: 指定该交叉指标监测 `self.sma_fast`（快线）和 `self.sma_slow`（慢线）的交叉。
# (大白话: 告诉机器人，关注的是“短期平均价格线”和“稍长期平均价格线”的相交情况。)
        )
        print("--- SMA Crossover Strategy Initialized ---")
# 功能: 打印一条信息，表示SMA交叉策略已初始化完成。
# (大白话: 告诉我们，这个“均线交叉交易机器人”已经准备好了！)
        print(
# 功能: 打印策略参数的具体值。
# (大白话: 把机器人当前使用的“快线旋钮”和“慢线旋钮”的数值告诉我们。)
            f"Fast MA Period: {self.p.fast_ma_period}, Slow MA Period: {self.p.slow_ma_period}")
# 功能: 格式化并打印快速移动平均线周期和慢速移动平均线周期。
# (大白话: 具体显示出快线周期是多少，慢线周期是多少。)

    def notify_order(self, order):
# 功能: 定义 `notify_order` 方法，当订单状态发生变化时，系统会自动调用此方法。
# (大白话: 这是机器人的“订单状态播报员”，每当交易指令单的状态有更新（比如下单了、成交了、取消了），它就会被叫出来报告。)
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
# 功能: 检查订单状态是否为“已提交”或“已接受”。
# (大白话: 如果指令单只是“刚刚发出去”或者“交易所说收到了”，机器人暂时不做任何事。)
            return
# 功能: 如果是上述状态，则直接返回，不执行后续逻辑。
# (大白话: 那就先等等，不用往下处理了。)
        if order.status in [bt.Order.Completed]:
# 功能: 检查订单状态是否为“已完成”（即已成交）。
# (大白话: 如果指令单“已经成功交易了”。)
            if order.isbuy():
# 功能: 如果是买入订单。
# (大白话: 如果这是一张“买入”的指令单。)
                self.log(
# 功能: 记录买入执行的日志。
# (大白话: 机器人就在它的小本本上记下这次买入的详细情况。)
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
# 功能: 格式化并记录买入价格、总花费和手续费。
# (大白话: 记录内容是：“买入成功！成交价格是XX，总共花了XX钱，手续费是XX。”)
                self.buyprice = order.executed.price
# 功能: 将成交价格保存到 `self.buyprice`。
# (大白话: 把这次买入的成交价格存起来，方便以后算账。)
                self.buycomm = order.executed.comm
# 功能: 将成交手续费保存到 `self.buycomm`。
# (大白话: 把这次买入的手续费也存起来。)
            elif order.issell():
# 功能: 如果是卖出订单（通常是平仓）。
# (大白话: 如果这是一张“卖出”的指令单。)
                self.log(
# 功能: 记录卖出执行的日志。
# (大白话: 机器人就在它的小本本上记下这次卖出的详细情况。)
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
# 功能: 格式化并记录卖出价格、总收入和手续费。
# (大白话: 记录内容是：“卖出成功！成交价格是XX，总共得到XX钱，手续费是XX。”)
        elif order.status in [bt.Order.Canceled, bt.Order.Rejected]:
# 功能: 检查订单状态是否为“已取消”、“保证金不足”或“已拒绝”。
# (大白话: 如果指令单被“取消了”，或者因为“钱不够”或者其他原因被“拒绝了”。)
            self.log(f'Order Canceled/Margin/Rejected: Status {order.status}')
# 功能: 记录订单被取消/拒绝的日志及具体状态。
# (大白话: 机器人就记录下来：“指令单出问题了，状态是XX（比如已取消）。”)
        self.order = None
# 功能: 重置 `self.order` 为 `None`，表示当前没有待处理的订单。
# (大白话: 不管指令单是成功了还是失败了，处理完之后，机器人手上的“当前指令单”就清空了，准备接收下一个。)

    def notify_trade(self, trade):
# 功能: 定义 `notify_trade` 方法，当一笔交易（买入和对应的卖出构成一笔完整交易）完成时，系统会自动调用此方法。
# (大白话: 这是机器人的“交易总结员”，每当一次完整的“买卖回合”结束后，它就会被叫出来总结这次交易赚了还是亏了。)
        if not trade.isclosed:
# 功能: 检查交易是否已经关闭（即已经平仓）。
# (大白话: 如果这个“买卖回合”还没结束（比如只买了还没卖）。)
            return
        self.log(
            f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def next(self):
        # 记录收盘价和均线值（可选，用于调试）
        # self.log(f'Close: {self.dataclose[0]:.2f}, FastMA: {self.sma_fast[0]:.2f}, SlowMA: {self.sma_slow[0]:.2f}, CrossOver: {self.sma_crossover[0]}')

        # 检查是否有待处理订单
        if self.order:
            return

        # 检查是否持有仓位
        if not self.position:
            # 买入信号：快线上穿慢线 (sma_crossover > 0)
            if self.sma_crossover > 0:
                # 修正: 添加[0]索引
                self.log(f'BUY CREATE, Close: {self.dataclose[0]:.2f}')
                self.order = self.buy()  # 必须保存到self.order​，否则无法管理订单状态。
        else:  # 持有仓位
            # 卖出（平仓）信号：快线下穿慢线 (sma_crossover < 0)
            if self.sma_crossover < 0:
                # 修正: 添加[0]索引
                self.log(
                    f'SELL CREATE (Close Position), Close: {self.dataclose[0]:.2f}')
                self.order = self.close()


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(500000.0)
    cerebro.broker.setcommission(commission=0.001)  # 设置0.1%的佣金

    # --- 加载数据 ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'sample_data_a_share.csv')
    df = pd.read_csv(data_path, parse_dates=True, index_col='Date')
    data_feed = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2023, 1, 1),
        todate=datetime.datetime(2023, 12, 31)  # 使用全年数据
    )
    cerebro.adddata(data_feed, name='SampleStock')

    cerebro.addstrategy(SmaCrossStrategy)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    cerebro.run()
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    cerebro.plot(style='candlestick')
    # 可选: 绘制结果图表 (需要安装 matplotlib: pip install matplotlib)
    # print("Plotting results...")
    # cerebro.plot(style='candlestick')
