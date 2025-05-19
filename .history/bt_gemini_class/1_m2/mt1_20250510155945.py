from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# 导入 `__future__` 模块的特性，确保代码在不同 Python 版本间的兼容性。(就像给代码装上翻译器，让它在老版本Python也能听懂新指令)
import backtrader as bt
# 导入 `backtrader` 库并将其别名为 `bt`。(引入一个叫 `backtrader` 的工具箱，并给它取个小名叫 `bt`)
import pandas as pd
# 导入 `pandas` 库并将其别名为 `pd`。(引入一个叫 `pandas` 的数据处理工具箱，并给它取个小名叫 `pd`)
import datetime
# 导入 `datetime` 模块，用于处理日期和时间。(引入一个时间管理工具)
import os
# 导入 `os` 模块，用于与操作系统交互，如文件路径操作。(引入一个能和电脑系统打交道的工具)
import matplotlib
# 导入matplotlib用于图表显示设置
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# 设置matplotlib不使用科学计数法显示
matplotlib.rcParams['axes.formatter.useoffset'] = False
matplotlib.rcParams['axes.formatter.limits'] = (-10000, 10000)

# 自定义数字格式化函数


def format_number(x, pos):
    return f'{x:.0f}'

# 自定义Backtrader绘图函数


def custom_plot(cerebro, **kwargs):
    figs = cerebro.plot(**kwargs)
    if not figs:
        return

    # 对所有图表应用自定义格式
    for fig in figs:
        for ax in fig[0].get_axes():
            # 设置Y轴格式化器，防止科学计数法
            formatter = FuncFormatter(format_number)
            ax.yaxis.set_major_formatter(formatter)

    # 显示图表
    plt.show()


class SmaCrossStrategy(bt.Strategy):
    # 定义一个名为 `SmaCrossStrategy` 的策略类，它继承自 `bt.Strategy`。(创建一个交易策略的蓝图，这个蓝图基于 `backtrader` 提供的标准策略模板)
    params = (
        # 定义策略的参数字典。(给策略设置一些可以调整的选项开关)
        ('fast_ma_period', 2),
        # 定义快线移动平均线的周期为2。(设置短期均线的计算天数是2天)
        ('slow_ma_period', 3),
        # 定义慢线移动平均线的周期为3。(设置长期均线的计算天数是3天)
    )
    # 参数定义结束。(选项开关设置完毕)

    def log(self, txt, dt=None):
        # 定义一个日志记录方法 `log`。(创建一个专门用来打日志的工具函数)
        dt = dt or self.datas[0].datetime.date(0)
        # 获取当前数据点的日期，如果未提供 `dt` 参数，则使用第一个数据源的当前日期。(如果没指定日志时间，就用当前交易日的日期)
        print(f'{dt.isoformat()}, {txt}')
        # 打印格式化的日志信息，包含日期和文本内容。(把日期和日志内容一起打印出来，方便查看)

    def __init__(self):
        # 策略类的构造函数，在策略实例化时执行初始化操作。(策略对象一创建，这里面的代码就会自动运行，做些准备工作)
        self.dataclose = self.datas[0].close
        # 获取第一个数据源的收盘价数据序列。(拿到每天的收盘价数据，方便后面用)
        self.order = None
        # 初始化订单跟踪变量为 `None`，表示当前没有待处理订单。(一开始没有挂单，所以标记一下)
        self.buyprice = None
        # 初始化买入价格变量为 `None`。(记录买入价格的地方，先空着)
        self.buycomm = None
        # 初始化买入佣金变量为 `None`。(记录买入佣金的地方，先空着)

        self.sma_fast = bt.indicators.SimpleMovingAverage(
            # 创建快速移动平均线指标。(计算短期均线)
            self.datas[0], period=self.params.fast_ma_period
            # 基于第一个数据源的收盘价和 `fast_ma_period` 参数计算。(用的是收盘价和前面设置的短期均线天数)
        )
        # 快速移动平均线指标创建完成。
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            # 创建慢速移动平均线指标。(计算长期均线)
            self.datas[0], period=self.params.slow_ma_period
            # 基于第一个数据源的收盘价和 `slow_ma_period` 参数计算。(用的是收盘价和前面设置的长期均线天数)
        )
        # 慢速移动平均线指标创建完成。

        self.sma_crossover = bt.indicators.CrossOver(
            # 创建移动平均线交叉指标。(专门看短期均线和长期均线有没有交叉的工具)
            self.sma_fast, self.sma_slow
            # 基于已创建的快速和慢速移动平均线。(告诉它要比较的是哪两条均线)
        )
        # 交叉指标创建完成。
        print("--- SMA Crossover Strategy Initialized ---")
        # 打印策略初始化完成的提示信息。(告诉我们策略已经准备好了)
        print(
            # 打印快慢均线的周期参数。(把设置的均线天数打印出来确认一下)
            f"Fast MA Period: {self.p.fast_ma_period}, Slow MA Period: {self.p.slow_ma_period}")
        # 格式化并打印快慢均线的周期。(具体打印出短期均线是几天，长期均线是几天)

    def notify_order(self, order):
        # 定义订单通知方法，当订单状态发生变化时被调用。(当下的单子有新进展了，比如成交了、取消了，这个函数就会被叫起来)
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            # 如果订单状态是已提交或已接受，则不作处理直接返回。(如果单子只是刚提交或者交易所刚收到，暂时不用管)
            return
            # 结束当前方法的执行。(那就先不处理，等等看后续状态)
        if order.status in [bt.Order.Completed]:
            # 如果订单状态是已完成。(如果单子已经成交了)
            if order.isbuy():
                # 如果是买入订单。(如果这个成交的单子是买单)
                self.log(
                    # 记录买入执行的日志。(打个日志说买入成功了)
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                # 日志内容包括成交价格、总花费和佣金。(日志里写清楚买入价格、花了多少钱、手续费多少)
                self.buyprice = order.executed.price
                # 记录买入价格。(把成交价格存起来)
                self.buycomm = order.executed.comm
                # 记录买入佣金。(把手续费存起来)
            elif order.issell():
                # 如果是卖出订单（通常是平仓）。(如果这个成交的单子是卖单，一般就是把之前买的卖掉)
                self.log(
                    # 记录卖出执行的日志。(打个日志说卖出成功了)
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                # 日志内容包括成交价格、总价值和佣金。(日志里写清楚卖出价格、卖了多少钱、手续费多少)
        elif order.status in [bt.Order.Canceled, bt.Order.Rejected]:
            # 如果订单状态是已取消、保证金不足或被拒绝。(如果单子被取消了，或者钱不够，或者交易所不让过)
            self.log(f'Order Canceled/Margin/Rejected: Status {order.status}')
            # 记录订单取消/保证金不足/被拒绝的日志及状态。(打个日志说单子黄了，并说明具体原因)
        self.order = None
        # 重置订单跟踪变量为 `None`，表示当前订单处理完毕。(不管成交还是没成交，这个单子的事情处理完了，把订单标记清空，准备下一个单子)

    def notify_trade(self, trade):
        # 定义交易通知方法，当一笔交易（买入和卖出匹配）完成时被调用。(当一次完整的买卖操作结束了，这个函数就会被叫起来)
        if not trade.isclosed:
            # 如果交易尚未关闭（即仍在持仓中），则不作处理直接返回。(如果这笔交易还没完结，比如只买了还没卖，那就先不管)
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
                # 必须保存到self.order​，否则无法管理订单状态。
                self.order = self.buy(size=5000)
        else:  # 持有仓位
            # 卖出（平仓）信号：快线下穿慢线 (sma_crossover < 0)
            if self.sma_crossover < 0:
                # 修正: 添加[0]索引
                self.log(
                    f'SELL CREATE (Close Position), Close: {self.dataclose[0]:.2f}')
                self.order = self.close()


if __name__ == '__main__':
    # 设置使用自定义绘图类
    cerebro = bt.Cerebro(plot=False)  # 禁用内置绘图
    cerebro.broker.setcash(500000.0)
    cerebro.broker.setcommission(commission=0.01)  # 设置0.1%的佣金

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

    # 设置绘图选项，防止使用科学计数法
    plt_style = {
        'style': 'candlestick',
        'barup': 'red',
        'bardown': 'green',
        'tickformat': '%.0f',  # 整数格式
        'volume': True,
        'legendindloc': 'best',
        'format_string': '%.0f'  # 整数格式
    }

    # 使用自定义绘图类
    custom_plot(cerebro, **plt_style)
