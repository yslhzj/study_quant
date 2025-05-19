from __future__ import ( # 从 `__future__` 模块导入特性，以增强版本兼容性
                        # (就像给代码装上一个翻译器，让它在不同Python版本下表现一致)
    absolute_import, division, # 指定导入 `absolute_import` (绝对导入) 和 `division` (精确除法) 特性
                               # (让导入模块的行为更标准，除法运算更精确，例如1/2=0.5)
    print_function, unicode_literals # 指定导入 `print_function` (print函数) 和 `unicode_literals` (Unicode字符串字面量) 特性
                                     # (让打印变成函数调用，字符串统一使用Unicode编码，方便处理各种文字)
) # `__future__` 导入语句的括号结束
  # (特性列表指定完毕)
import backtrader as bt # 导入 `backtrader` 量化交易框架库，并将其别名为 `bt`
                        # (引入一个叫做 `backtrader` 的炒股程序工具箱，以后用 `bt` 这个小名来叫它)
import pandas as pd # 导入 `pandas` 数据分析库，并将其别名为 `pd`
                    # (引入一个叫做 `pandas` 的数据处理工具箱，以后用 `pd` 这个小名来叫它)
import datetime # 导入 `datetime` 模块，用于处理日期和时间相关的操作
                # (引入一个时间管理工具，可以用来表示和计算日期、时间)
import os # 导入 `os` 模块，提供与操作系统交互的功能，如文件路径操作
          # (引入一个能和你的电脑系统打交道的工具，比如找文件、看文件夹路径等)


class SmaCrossStrategy(bt.Strategy): # 定义一个名为 `SmaCrossStrategy` 的策略类，该类继承自 `bt.Strategy`
                                     # (创建一个我们自己的交易策略，这个策略是基于 `backtrader` 工具箱里的标准策略模板来改造的)
    params = ( # 定义策略参数的元组，这些参数可以在策略实例化时进行配置
               # (给我们的策略设置一些可以调整的选项开关，方便以后改变策略行为)
        ('fast_ma_period', 2), # 定义快线移动平均线的周期参数，默认值为2
                               # (设置一个叫“快均线周期”的选项，默认是2天，表示短期均线用2天的数据计算)
        ('slow_ma_period', 3), # 定义慢线移动平均线的周期参数，默认值为3
                               # (设置一个叫“慢均线周期”的选项，默认是3天，表示长期均线用3天的数据计算)
    ) # 参数元组定义结束
      # (选项开关设置完毕)

    def log(self, txt, dt=None): # 定义一个名为 `log` 的方法，用于记录日志信息
                                 # (创建一个专门用来打日志的工具函数，方便我们看策略运行过程中的情况)
        dt = dt or self.datas[0].datetime.date(0) # 获取当前K线的日期，如果未传入 `dt` 参数，则使用第一个数据源的当前日期
                                                  # (如果调用这个打日志工具时没指定时间，就用当前交易发生的日期)
        print(f'{dt.isoformat()}, {txt}') # 打印ISO格式的日期和传入的文本信息 `txt`
                                          # (把日期和要记录的信息一起打印到屏幕上，格式是“年-月-日, 信息内容”)

    def __init__(self): # 定义策略类的构造函数，在策略对象创建时自动执行初始化操作
                        # (当我们的策略一被创建出来，这里面的代码就会自动运行，做一些准备工作)
        self.dataclose = self.datas[0].close # 获取第一个数据源的收盘价数据序列，并赋值给 `self.dataclose`
                                             # (拿到我们交易的那个股票每天的收盘价数据，存起来方便后面用)
        self.order = None # 初始化 `self.order` 变量为 `None`，用于跟踪当前活动的订单
                          # (一开始我们还没有下单，所以用 `None` 标记一下，表示当前没有正在处理的单子)
        self.buyprice = None # 初始化 `self.buyprice` 变量为 `None`，用于记录买入价格
                             # (先准备一个空位，等买入股票了就把买入价格记在这里)
        self.buycomm = None # 初始化 `self.buycomm` 变量为 `None`，用于记录买入佣金
                            # (也准备一个空位，等买入股票了就把付的手续费记在这里)

        self.sma_fast = bt.indicators.SimpleMovingAverage( # 创建快速简单移动平均线指标实例
                                                          # (开始计算一个短期均线，比如5日均线)
            self.datas[0], period=self.params.fast_ma_period # 指定数据源为第一个数据序列，周期使用参数 `fast_ma_period`
                                                              # (告诉均线计算器用哪个股票的数据（就是我们前面拿到的收盘价），以及用几天的数据算平均值（比如之前设置的2天）)
        ) # 快速简单移动平均线指标 `sma_fast` 创建完成
          # (短期均线算好了，存在 `self.sma_fast` 里)
        self.sma_slow = bt.indicators.SimpleMovingAverage( # 创建慢速简单移动平均线指标实例
                                                          # (再计算一个长期均线，比如10日均线)
            self.datas[0], period=self.params.slow_ma_period # 指定数据源为第一个数据序列，周期使用参数 `slow_ma_period`
                                                              # (同样告诉均线计算器用哪个股票的数据，以及用几天的数据算平均值（比如之前设置的3天）)
        ) # 慢速简单移动平均线指标 `sma_slow` 创建完成
          # (长期均线也算好了，存在 `self.sma_slow` 里)

        self.sma_crossover = bt.indicators.CrossOver( # 创建均线交叉指标实例
                                                      # (创建一个专门看短期均线和长期均线有没有交叉的工具)
            self.sma_fast, self.sma_slow # 指定要比较的两条均线为 `self.sma_fast` 和 `self.sma_slow`
                                         # (告诉这个交叉工具，要盯住我们刚才算好的那两条短期和长期均线)
        ) # 均线交叉指标 `sma_crossover` 创建完成
          # (交叉工具也准备好了，存在 `self.sma_crossover` 里)
        print("--- SMA Crossover Strategy Initialized ---") # 打印策略初始化完成的提示信息
                                                           # (在屏幕上告诉我们：均线交叉策略已经准备就绪啦！)
        print( # 调用内置的 `print` 函数，用于输出信息到控制台
               # (准备在屏幕上显示一些文字)
            f"Fast MA Period: {self.p.fast_ma_period}, Slow MA Period: {self.p.slow_ma_period}") # 格式化并打印包含快慢均线周期的字符串，同时结束 `print` 函数调用
                                                                                                # (把设置的快均线是几天，慢均线是几天，这些信息打印出来确认一下)

    def notify_order(self, order): # 定义订单通知方法，当订单状态发生变化时由 `Cerebro` 引擎自动调用
                                   # (当下的单子有新进展了，比如成交了、取消了，`backtrader` 就会自动叫这个函数来处理)
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]: # 检查订单状态是否为已提交或已接受
                                                                    # (如果单子只是刚提交或者交易所刚收到，还没最终结果)
            return # 如果是已提交或已接受状态，则不执行后续操作，直接返回
                   # (那就先不用管，等等看后续状态变化)
        if order.status in [bt.Order.Completed]: # 检查订单状态是否为已完成（即已成交）
                                                 # (如果单子已经成交了)
            if order.isbuy(): # 检查已完成的订单是否为买入订单
                              # (如果这个成交的单子是买单)
                self.log( # 调用 `self.log` 方法记录日志
                          # (准备打个日志，记下这件事)
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}') # 格式化并记录买入执行的详细信息，同时结束 `self.log` 方法调用
                                                                                                                                        # (日志内容是：买入成功，成交价多少，花了多少钱，手续费多少。这条日志记完了)
                self.buyprice = order.executed.price # 将实际成交价格记录到 `self.buyprice`
                                                     # (把真正买入的价格记下来)
                self.buycomm = order.executed.comm # 将实际支付的佣金记录到 `self.buycomm`
                                                   # (把付的手续费也记下来)
            elif order.issell(): # 检查已完成的订单是否为卖出订单
                                 # (如果这个成交的单子是卖单，一般就是把之前买的股票卖掉)
                self.log( # 调用 `self.log` 方法记录日志
                          # (准备打个日志，记下这件事)
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}') # 格式化并记录卖出执行的详细信息，同时结束 `self.log` 方法调用
                                                                                                                                          # (日志内容是：卖出成功，成交价多少，卖了多少钱，手续费多少。这条日志记完了)
        elif order.status in [bt.Order.Canceled, bt.Order.Margin, bt.Order.Rejected]: # 检查订单状态是否为已取消、保证金不足或被拒绝
                                                                                      # (如果单子被取消了，或者钱不够买/卖（保证金不足），或者被交易所拒绝了)
            self.log(f'Order Canceled/Margin/Rejected: Status {order.status}') # 记录订单取消/保证金不足/被拒绝的日志及具体状态码
                                                                               # (打个日志说：这个单子黄了，具体原因是啥（状态码会显示原因）)
        self.order = None # 重置 `self.order` 变量为 `None`，表示当前订单处理完毕，没有活动的订单
                          # (不管成交还是没成交，这个单子的事情处理完了，把订单标记清空，准备处理下一个单子)

    def notify_trade(self, trade): # 定义交易通知方法，当一笔完整的交易（买入和对应的卖出）完成时由 `Cerebro` 引擎自动调用
                                   # (当一次完整的买卖操作（比如先买后卖）结束了，`backtrader` 就会自动叫这个函数)
        if not trade.isclosed: # 检查交易是否尚未关闭（即，如果只是买入但尚未卖出，则交易未关闭）
                               # (如果这笔交易还没完结，比如只买了还没卖，或者只卖空了还没买回来)
            return # 如果交易未关闭，则不执行后续操作，直接返回
                   # (那就先不管，等整个买卖流程走完了再说)
        self.log( # 调用 `self.log` 方法记录日志
                  # (准备打个日志，记下这件事)
            f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}') # 格式化并记录该笔交易的盈利信息（毛利润 `trade.pnl` 和净利润 `trade.pnlcomm`），同时结束 `self.log` 方法调用
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
