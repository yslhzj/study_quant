# module_4_script.py
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import backtrader as bt
import pandas as pd
import datetime
import os

# --- 策略定义 ---


class BuyAndHold_N_Bars(bt.Strategy):
    params = (
        ('buy_after_bars', 5),  # 在第几个Bar之后买入
        ('hold_bars', 10),      # 持有多少个Bar后卖出
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None  # 跟踪待处理订单
        self.buyprice = None
        self.buycomm = None
        self.bar_executed_buy = 0  # 记录买入订单执行时的Bar计数
        self.bar_counter = 0  # 简单的Bar计数器

    def notify_order(self, order):
        if order.status in [ bt.Order.Canceled, bt.Order.Rejected]:
            # 订单已提交或已被经纪商接受 - 无需操作
            return

        # 检查订单是否已完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                # 记录买入完成时的Bar计数 (len(self) 返回当前已处理的Bar数量)
                self.bar_executed_buy = len(self)
            elif order.issell():  # 卖出订单完成
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            # self.bar_executed = len(self) # 可选：记录卖出完成时的Bar计数

        elif order.status in [bt.Order.Canceled, bt.Order.Rejected]:
            self.log(
                f'Order Canceled/Margin/Rejected: Status {order.Status[order.status]}')

        # 订单处理完毕（完成或失败），重置 self.order
        self.order = None

    def notify_trade(self, trade):
        # 当一笔交易关闭时调用
        if not trade.isclosed:
            return
        self.log(
            f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def next(self):
        self.log(f'Close: {self.close:.2f}')  # 使用 self.close 引用
        self.bar_counter += 1

        # 如果有待处理订单，则不执行任何操作
        if self.order:
            return

        # 检查是否持有仓位
        if not self.position:
            # 买入条件：达到指定Bar数后
            # 注意: bar_counter 从1开始计数, len(self) 也从1开始
            # 如果想在第5个Bar *之后* (即第6个Bar开始时) 买入，用 >= buy_after_bars + 1
            # 如果想在第5个Bar *结束时* 下单 (第6个Bar开盘成交)，用 >= buy_after_bars
            if len(self) >= self.p.buy_after_bars:
                self.log(f'BUY CREATE, {self.close:.2f}')
                # 跟踪创建的订单
                self.order = self.buy()
        else:
            # 卖出条件：持仓达到指定Bar数后
            # len(self) 是当前Bar的序号 (从1开始)
            # bar_executed_buy 是买入完成时的Bar序号
            if len(self) >= (self.bar_executed_buy + self.p.hold_bars):
                self.log(f'SELL CREATE (Close Position), {self.close:.2f}')
                # 跟踪创建的订单
                self.order = self.close()  # 使用 close() 平掉多头仓位


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(500000.0)
    # 添加佣金设置
    cerebro.broker.setcommission(commission=0.001)  # 示例: 千分之一佣金

    # --- 加载数据 ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'sample_data_a_share.csv')
    df = pd.read_csv(data_path, parse_dates=True, index_col='Date')
    data_feed = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2023, 1, 1),
        todate=datetime.datetime(2023, 1, 31)  # 使用一个月的数据以便观察
    )
    cerebro.adddata(data_feed, name='SampleStock')

    cerebro.addstrategy(BuyAndHold_N_Bars)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    cerebro.run()
    # 最终价值在策略的 stop() 方法中打印 (如果实现了 stop 方法)
    # 这里我们在主程序结束时打印
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
