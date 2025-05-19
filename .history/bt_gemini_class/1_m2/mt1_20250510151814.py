from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# Imports features from the __future__ module for Python version compatibility. (就像给代码装上翻译器，让它在老版本Python也能听懂新指令)
import backtrader as bt
# Imports the backtrader library and aliases it as bt. (引入一个叫 backtrader 的工具箱，并给它取个小名叫 bt)
import pandas as pd
# Imports the pandas library and aliases it as pd. (引入一个叫 pandas 的数据处理工具箱，并给它取个小名叫 pd)
import datetime
# Imports the datetime module for handling dates and times. (引入一个时间管理工具)
import os
# Imports the os module for interacting with the operating system, like file path operations. (引入一个能和电脑系统打交道的工具)


class SmaCrossStrategy(bt.Strategy):
    # Defines a strategy class named SmaCrossStrategy, inheriting from bt.Strategy. (创建一个交易策略的蓝图，这个蓝图基于 backtrader 提供的标准策略模板)
    params = (
        # Defines the strategy's parameters dictionary. (给策略设置一些可以调整的选项开关)
        ('fast_ma_period', 2),
        # Defines the period for the fast moving average as 2. (设置短期均线的计算天数是2天)
        ('slow_ma_period', 3),
        # Defines the period for the slow moving average as 3. (设置长期均线的计算天数是3天)
    )
    # End of parameter definition. (选项开关设置完毕)

    def log(self, txt, dt=None):
        # Defines a logging method named log. (创建一个专门用来打日志的工具函数)
        dt = dt or self.datas[0].datetime.date(0)
        # Gets the date of the current data point, using the first data source's current date if dt is not provided. (如果没指定日志时间，就用当前交易日的日期)
        print(f'{dt.isoformat()}, {txt}')
        # Prints the formatted log message, including date and text content. (把日期和日志内容一起打印出来，方便查看)

    def __init__(self):
        # The constructor for the strategy class, executed when the strategy is instantiated. (策略对象一创建，这里面的代码就会自动运行，做些准备工作)
        self.dataclose = self.datas[0].close
        # Gets the closing price data series from the first data source. (拿到每天的收盘价数据，方便后面用)
        self.order = None
        # Initializes the order tracking variable to None, indicating no pending order. (一开始没有挂单，所以标记一下)
        self.buyprice = None
        # Initializes the buy price variable to None. (记录买入价格的地方，先空着)
        self.buycomm = None
        # Initializes the buy commission variable to None. (记录买入佣金的地方，先空着)

        self.sma_fast = bt.indicators.SimpleMovingAverage(
            # Creates the fast moving average indicator. (计算短期均线)
            self.datas[0], period=self.params.fast_ma_period
            # Calculates based on the first data source's closing price and the fast_ma_period parameter. (用的是收盘价和前面设置的短期均线天数)
        )
        # Fast moving average indicator creation completed.
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            # Creates the slow moving average indicator. (计算长期均线)
            self.datas[0], period=self.params.slow_ma_period
            # Calculates based on the first data source's closing price and the slow_ma_period parameter. (用的是收盘价和前面设置的长期均线天数)
        )
        # Slow moving average indicator creation completed.

        self.sma_crossover = bt.indicators.CrossOver(
            # Creates the moving average crossover indicator. (专门看短期均线和长期均线有没有交叉的工具)
            self.sma_fast, self.sma_slow
            # Based on the created fast and slow moving averages. (告诉它要比较的是哪两条均线)
        )
        # Crossover indicator creation completed.
        print("--- SMA Crossover Strategy Initialized ---")
        # Prints a message indicating that the strategy initialization is complete. (告诉我们策略已经准备好了)
        print(
            # Prints the fast and slow moving average period parameters. (把设置的均线天数打印出来确认一下)
            f"Fast MA Period: {self.p.fast_ma_period}, Slow MA Period: {self.p.slow_ma_period}")
        # Formats and prints the periods of the fast and slow moving averages. (具体打印出短期均线是几天，长期均线是几天)

    def notify_order(self, order):
        # Defines the order notification method, called when an order's status changes. (当下的单子有新进展了，比如成交了、取消了，这个函数就会被叫起来)
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            # If the order status is Submitted or Accepted, return without further processing. (如果单子只是刚提交或者交易所刚收到，暂时不用管)
            return
            # Ends the execution of the current method. (那就先不处理，等等看后续状态)
        if order.status in [bt.Order.Completed]:
            # If the order status is Completed. (如果单子已经成交了)
            if order.isbuy():
                # If it is a buy order. (如果这个成交的单子是买单)
                self.log(
                    # Logs the buy execution details. (打个日志说买入成功了)
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                # Log content includes execution price, total cost, and commission. (日志里写清楚买入价格、花了多少钱、手续费多少)
                self.buyprice = order.executed.price
                # Records the buy price. (把成交价格存起来)
                self.buycomm = order.executed.comm
                # Records the buy commission. (把手续费存起来)
            elif order.issell():
                # If it is a sell order (usually closing a position). (如果这个成交的单子是卖单，一般就是把之前买的卖掉)
                self.log(
                    # Logs the sell execution details. (打个日志说卖出成功了)
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                # Log content includes execution price, total value, and commission. (日志里写清楚卖出价格、卖了多少钱、手续费多少)
        elif order.status in [bt.Order.Canceled, bt.Order.Rejected]:
            # If the order status is Canceled, Margin, or Rejected. (如果单子被取消了，或者钱不够，或者交易所不让过)
            self.log(f'Order Canceled/Margin/Rejected: Status {order.status}')
            # Logs the cancellation/margin/rejection status. (打个日志说单子黄了，并说明具体原因)
        self.order = None
        # Resets the order tracking variable to None, indicating the current order is processed. (不管成交还是没成交，这个单子的事情处理完了，把订单标记清空，准备下一个单子)

    def notify_trade(self, trade):
        # Defines the trade notification method, called when a trade (buy and sell match) is completed. (当一次完整的买卖操作结束了，这个函数就会被叫起来)
        if not trade.isclosed:
        # If the trade is not yet closed (i.e., still holding a position), return without further processing. (如果这笔交易还没完结，比如只买了还没卖，那就先不管)
            return
        self.log(
            f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')
        # Logs the profit/loss details for the completed trade. (记录这笔交易的总盈亏和净盈亏)

    def next(self):
        # This method is called for each data point (usually each bar/day). (每天都会调用这个函数来决定是否交易)
        # Optional: Log close price and MA values for debugging. (可选：打印收盘价和均线值，方便调试)
        # self.log(f'Close: {self.dataclose[0]:.2f}, FastMA: {self.sma_fast[0]:.2f}, SlowMA: {self.sma_slow[0]:.2f}, CrossOver: {self.sma_crossover[0]}')

        # Checks if there is a pending order. (检查是不是有单子还在处理中)
        if self.order:
            # If there is a pending order, do nothing and return. (如果有单子没处理完，就等，今天不操作了)
            return

        # Checks if a position is currently held. (检查是不是手里有股票)
        if not self.position:
            # Buy signal: Fast MA crosses above Slow MA (sma_crossover > 0). (买入信号：短期均线穿过长期均线向上)
            if self.sma_crossover > 0:
                # Correction: Add [0] index to access current value. (修正：加上[0]来获取当前值)
                self.log(f'BUY CREATE, Close: {self.dataclose[0]:.2f}')
                # Logs the buy creation signal with the current closing price. (打个日志说准备买入了，并记录当前收盘价)
                self.order = self.buy()
                # Places a buy order and stores the order object in self.order to track its status. (下买单，并把这个单子存起来，方便后面知道它有没有成交)
        else:  # Holding a position. (手里有股票)
            # Sell (Close Position) signal: Fast MA crosses below Slow MA (sma_crossover < 0). (卖出信号：短期均线穿过长期均线向下)
            if self.sma_crossover < 0:
                # Correction: Add [0] index to access current value. (修正：加上[0]来获取当前值)
                self.log(
                    f'SELL CREATE (Close Position), Close: {self.dataclose[0]:.2f}')
                # Logs the sell creation signal with the current closing price. (打个日志说准备卖出了，并记录当前收盘价)
                self.order = self.close()
                # Places a sell order to close the current position and stores the order object. (下卖单，把手里的股票卖掉，并把这个单子存起来)


if __name__ == '__main__':
    # This block is executed only when the script is run directly. (只有直接运行这个文件时，下面的代码才会执行)
    cerebro = bt.Cerebro()
    # Creates an instance of Cerebro, the main engine of backtrader. (创建一个 backtrader 的大脑，所有东西都靠它来协调)
    cerebro.broker.setcash(500000.0)
    # Sets the initial cash amount in the broker. (给账户里放50万块钱)
    cerebro.broker.setcommission(commission=0.001)
    # Sets the commission rate to 0.1%. (设置交易手续费是千分之一)

    # --- Load Data --- (--- 加载数据 ---)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Gets the directory path of the current script file. (获取当前文件所在的文件夹路径)
    data_path = os.path.join(script_dir, 'sample_data_a_share.csv')
    # Constructs the full path to the data file. (拼接出数据文件的完整路径)
    df = pd.read_csv(data_path, parse_dates=True, index_col='Date')
    # Reads the CSV data file into a pandas DataFrame, parsing 'Date' as dates and setting it as the index. (用 pandas 读取数据文件，把日期列变成日期格式，并设为索引)
    data_feed = bt.feeds.PandasData(
        # Creates a data feed object from the pandas DataFrame. (把 pandas 读进来的数据转换成 backtrader 能用的格式)
        dataname=df,
        # Specifies the pandas DataFrame as the data source. (告诉 backtrader 用哪个数据)
        fromdate=datetime.datetime(2023, 1, 1),
        # Sets the start date for the data feed. (设置数据从哪天开始用)
        todate=datetime.datetime(2023, 12, 31)
        # Sets the end date for the data feed. (设置数据到哪天结束)
    )
    # Data feed creation completed.
    cerebro.adddata(data_feed, name='SampleStock')
    # Adds the created data feed to the Cerebro engine, naming it 'SampleStock'. (把准备好的数据喂给 backtrader 的大脑)

    cerebro.addstrategy(SmaCrossStrategy)
    # Adds the SmaCrossStrategy to the Cerebro engine. (把我们写的交易策略加到 backtrader 的大脑里)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    # Prints the initial portfolio value before running the backtest. (打印出开始回测前账户里有多少钱)
    cerebro.run()
    # Runs the backtest simulation. (开始运行回测)
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    # Prints the final portfolio value after the backtest is complete. (打印出回测结束后账户里还剩多少钱)
    cerebro.plot(style='candlestick')
    # Plots the backtest results using a candlestick style. (绘制回测结果图表，用K线图样式)
    # Optional: Plot results (requires matplotlib: pip install matplotlib). (可选：绘制结果图表 (需要安装 matplotlib: pip install matplotlib))
    # print("Plotting results...") (打印提示信息说正在绘制图表)
    # cerebro.plot(style='candlestick') (绘制回测结果图表)
