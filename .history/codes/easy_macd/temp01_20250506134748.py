# -*- coding: utf-8 -*-
# @Author : huanglei
# @File : 课程第十二阶段：自定义 Observer 进阶 - 事件驱动的可视化.py

import datetime
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA
import pprint
from collections import OrderedDict, deque  # 导入 deque 用于存储交易信息
import math

# --- 自定义 Observer ---
# 响应交易关闭事件，在图上绘制从开仓点到平仓点的连线，并根据盈亏标记不同颜色


class TradeConnectObserver(bt.Observer):
    """子图中显示交易连线的观察器，清晰展示每笔交易的盈亏状况"""

    # 使用专用lines记录交易信息，定义为水平线便于在plot中取值
    lines = ('trade_profit', 'trade_loss')

    # 设置绘图信息
    plotinfo = dict(
        plot=True,
        subplot=True,  # 显示为子图
        plotname='Trade Results',
        plothlines=[0],  # 在0处绘制一条水平线
        plotymargin=0.5,  # 增加Y轴边距，使图表更清晰
        plotlinelabels=True,
    )

    # 设置线样式
    plotlines = dict(
        trade_profit=dict(_name='Profit', color='green',
                          marker='o', markersize=8, fillstyle='full',
                          ls='-', linewidth=1.5),
        trade_loss=dict(_name='Loss', color='red',
                        marker='o', markersize=8, fillstyle='full',
                        ls='-', linewidth=1.5),
    )

    def __init__(self):
        super().__init__()
        # 存储已处理的交易ID
        self.processed_trades = set()
        # 存储所有交易信息(完整信息)
        self.trades_info = []
        # 不要在这里初始化lines值 - 移除这两行
        # self.lines.trade_profit[0] = float('nan')
        # self.lines.trade_loss[0] = float('nan')

    def notify_trade(self, trade):
        """当交易关闭时，记录交易相关信息"""
        if trade.isclosed:
            # 避免重复处理
            if trade.ref in self.processed_trades:
                return

            self.processed_trades.add(trade.ref)

            # 从策略中获取交易信息
            strategy = self._owner

            # 获取开仓信息
            entry_bar = strategy.trade_entry_info.get(trade.ref, {}).get('bar')
            entry_price = strategy.trade_entry_info.get(
                trade.ref, {}).get('price')

            # 获取平仓信息
            exit_bar = strategy.trade_exit_info.get(trade.ref, {}).get('bar')
            exit_price = strategy.trade_exit_info.get(
                trade.ref, {}).get('price')

            # 确保数据完整
            if None in (entry_bar, entry_price, exit_bar, exit_price):
                return

            # 确定交易方向和盈亏状态
            is_long = True
            if len(trade.history) > 0:
                is_long = trade.history[0].status.size > 0

            # 使用实际盈亏值判断
            pnl = trade.pnlcomm
            is_win = pnl >= 0

            # 记录交易信息
            trade_info = {
                'trade_ref': trade.ref,
                'entry_bar': entry_bar,
                'entry_price': entry_price,
                'exit_bar': exit_bar,
                'exit_price': exit_price,
                'pnl': pnl,
                'is_win': is_win,
                'is_long': is_long
            }

            self.trades_info.append(trade_info)

            # 打印确认
            print(f"观察器记录 #{trade.ref}: {'多头' if is_long else '空头'}, "
                  f"{'盈利' if is_win else '亏损'}, 开仓={entry_price:.2f}@{entry_bar}, "
                  f"平仓={exit_price:.2f}@{exit_bar}, 盈亏={pnl:.2f}")

    def prenext(self):
        """在策略第一个数据处理前初始化线值为NaN"""
        self.lines.trade_profit[0] = float('nan')
        self.lines.trade_loss[0] = float('nan')

    def next(self):
        """初始化线数据为NaN，避免连接无关点"""
        self.lines.trade_profit[0] = float('nan')
        self.lines.trade_loss[0] = float('nan')

    def plot(self, ax, style='line'):
        """在子图中绘制交易连线和盈亏状况"""
        # 调用父类绘图方法，绘制基本内容
        super().plot(ax, style)

        # 如果没有交易记录，直接返回
        if not self.trades_info:
            return

        # 获取数据总长度
        obs_len = len(self)

        # 绘制每个交易的信息
        for trade in self.trades_info:
            # 计算坐标
            x1 = obs_len - trade['entry_bar'] - 1  # 开仓点
            x2 = obs_len - trade['exit_bar'] - 1   # 平仓点

            # 确保坐标在有效范围内
            if 0 <= x1 < obs_len and 0 <= x2 < obs_len:
                # 设置颜色
                color = 'green' if trade['is_win'] else 'red'

                # 绘制垂直线表示开仓点
                ax.axvline(x=x1, color=color, alpha=0.3, linestyle='--')

                # 绘制垂直线表示平仓点
                ax.axvline(x=x2, color=color, alpha=0.3, linestyle='--')

                # 确定Y轴位置 - 堆叠显示多个交易
                y_pos = trade['pnl']  # 使用实际盈亏值

                # 绘制开仓到平仓的水平连线
                ax.plot([x1, x2], [y_pos, y_pos],
                        color=color, linewidth=2, marker='o', alpha=0.8)

                # 添加盈亏标签
                pnl_text = f"+{trade['pnl']:.2f}" if trade['is_win'] else f"{trade['pnl']:.2f}"
                mid_x = (x1 + x2) / 2
                ax.text(mid_x, y_pos, pnl_text,
                        color=color, fontsize=9, fontweight='bold',
                        ha='center', va='bottom' if trade['is_win'] else 'top')

                # 在开仓点添加交易ID标签
                ax.text(x1, y_pos, f"#{trade['trade_ref']}",
                        color=color, fontsize=8, ha='right', va='center')

        # 设置Y轴标题和网格线
        ax.set_ylabel('Profit/Loss')
        ax.grid(True, alpha=0.3)

        # 调整Y轴范围，确保所有交易盈亏都可见
        pnl_values = [t['pnl'] for t in self.trades_info]
        if pnl_values:
            min_pnl = min(pnl_values)
            max_pnl = max(pnl_values)
            margin = (max_pnl - min_pnl) * 0.2 if max_pnl > min_pnl else 1.0
            ax.set_ylim(min_pnl - margin, max_pnl + margin)

# --- 策略定义 (修改以记录交易信息) ---


class TestStrategy(bt.Strategy):
    # 定义策略参数：移动平均线周期 (未使用)、快线 EMA 周期、慢线 EMA 周期、信号线 EMA 周期
    params = (('maperiod', 15), ('fast_ema', 12),
              ('slow_ema', 26), ('signal_ema', 9),)

    # 定义日志记录函数 (当前代码中未使用)
    def log(self, txt, dt=None): dt = dt or self.datas[0].datetime.date(0)

    # 初始化方法，在策略被创建时执行一次
    def __init__(self):
        # 获取第一个数据源 (self.datas[0]) 的收盘价时间序列
        self.dataclose = self.datas[0].close
        # 初始化订单对象变量，用于跟踪当前活动的订单
        self.order = None
        # --- 计算 MACD 指标 ---
        # 计算快线 EMA (指数移动平均)
        me1 = EMA(self.data, period=self.p.fast_ema)
        # 计算慢线 EMA
        me2 = EMA(self.data, period=self.p.slow_ema)
        # 计算 MACD 线 (快线 - 慢线)，结果是一个 Lines 对象
        self.macd = me1 - me2
        # 计算信号线 (MACD 线的 EMA)
        self.signal = EMA(self.macd, period=self.p.signal_ema)
        # 计算 MACD 柱状图 (MACD 线 - 信号线)
        self.macd_histo = self.macd - self.signal
        # 初始化一个变量 (似乎在当前逻辑中未使用，可考虑移除)
        self.bar_executed_close = 0

        # --- 新增：用于存储交易开平仓信息的字典 ---
        # 这是策略与 Observer 沟通的关键
        # 键是 trade.ref (交易的唯一引用标识)，值是一个字典，包含 'bar' 和 'price'
        # 存储开仓信息 {trade.ref: {'bar': bar_index, 'price': entry_price}}
        self.trade_entry_info = {}
        # 存储平仓信息 {trade.ref: {'bar': bar_index, 'price': exit_price}}
        self.trade_exit_info = {}
        # --------------------------------------

        # 添加交易逻辑 - 简单的MACD策略
        # 当MACD柱状图由负变正，买入
        # 当MACD柱状图由正变负，卖出
        self.last_histo = 0.0  # 记录上一个MACD柱状值

    # 订单状态通知方法，当订单状态变化时 Backtrader 调用
    def notify_order(self, order):
        # 如果订单状态是"已提交"或"已接受"，说明还在处理中，暂时忽略
        if order.status in [order.Submitted, order.Accepted]:
            return

        # 如果订单已完成
        if order.status in [order.Completed]:
            # 获取执行价格和执行时间
            price = order.executed.price
            dt = self.data.datetime.date()

            # 如果是买入订单，记录买入信息
            if order.isbuy():
                self.log(
                    f'买入执行 价格: {price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')
            # 如果是卖出订单，记录卖出信息
            else:
                self.log(
                    f'卖出执行 价格: {price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')

        # 如果订单被取消、边距不足或拒绝
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单被取消/边距不足/拒绝')

        # 无论如何，重置订单变量
        self.order = None

    # 交易状态通知方法，当交易状态变化时 Backtrader 调用
    def notify_trade(self, trade):
        # --- 在交易首次打开时 (justopened) 记录开仓信息 ---
        if trade.justopened:
            # 确保trade.history不为空后再访问元素
            if len(trade.history) > 0:
                # trade.history 列表记录了与此交易相关的事件
                # history[0] 通常是开仓事件
                # .event.order 获取该事件关联的订单对象
                entry_order = trade.history[0].event.order
                # 使用 trade.ref (交易的唯一引用) 作为键，存储开仓信息
                self.trade_entry_info[trade.ref] = {
                    # 记录开仓时的 K 线索引 (baropen 是 trade 对象的属性)
                    'bar': trade.baropen,
                    # 记录开仓订单的实际执行价格 (从订单对象的 executed 属性获取)
                    'price': entry_order.executed.price
                }
                # 打印日志，方便调试
                self.log(
                    f"Trade {trade.ref} opened: Bar={trade.baropen}, Price={entry_order.executed.price}")
            else:
                # 如果没有历史记录，使用当前价格作为开仓价格
                self.trade_entry_info[trade.ref] = {
                    'bar': trade.baropen,
                    'price': self.data.close[0]  # 使用当前收盘价作为近似
                }
                self.log(
                    f"Trade {trade.ref} opened: Bar={trade.baropen}, Price(approx)={self.data.close[0]}")

        # --- 在交易关闭时 (isclosed) 记录平仓信息 ---
        if trade.isclosed:
            # 确保trade.history不为空后再访问元素
            if len(trade.history) > 0:
                # history[-1] 通常是最后一个事件，即平仓事件
                exit_order = trade.history[-1].event.order
                # 使用 trade.ref 作为键，存储平仓信息
                self.trade_exit_info[trade.ref] = {
                    # 记录平仓时的 K 线索引 (barclose 是 trade 对象的属性)
                    'bar': trade.barclose,
                    # 记录平仓订单的实际执行价格
                    'price': exit_order.executed.price
                }
                # 打印日志，方便调试
                self.log(
                    f"Trade {trade.ref} closed: Bar={trade.barclose}, Price={exit_order.executed.price}, PnL={trade.pnlcomm}")
            else:
                # 如果没有历史记录，使用当前价格作为平仓价格
                self.trade_exit_info[trade.ref] = {
                    'bar': trade.barclose,
                    'price': self.data.close[0]  # 使用当前收盘价作为近似
                }
                self.log(
                    f"Trade {trade.ref} closed: Bar={trade.barclose}, Price(approx)={self.data.close[0]}, PnL={trade.pnlcomm}")

    def next(self):
        # 如果有挂起的订单，不执行新的交易
        if self.order:
            return

        # 获取当前MACD柱状图值
        current_histo = self.macd_histo[0]

        # 判断MACD柱状图的变化
        if self.last_histo <= 0 and current_histo > 0:
            # MACD柱状图由负转正，买入信号
            self.order = self.buy()
        elif self.last_histo >= 0 and current_histo < 0:
            # MACD柱状图由正转负，卖出信号
            self.order = self.sell()

        # 更新上一个MACD柱状图值
        self.last_histo = current_histo

# --- 自定义 Analyzer (保持不变) ---
# 用于计算毛利因子 (Gross Profit Factor) 的分析器


class GrossProfitFactorAnalyzer(bt.Analyzer):
    # 初始化方法
    def __init__(self):
        # 调用父类 bt.Analyzer 的初始化方法
        super().__init__()
        # 初始化总盈利 (Total Profit)
        self.tpnl = 0.0
        # 初始化总亏损 (Total Loss) - 注意这里存的是负数之和
        self.tlnl = 0.0
        # 初始化盈利交易次数 (Winning Count)
        self.wc = 0
        # 初始化亏损交易次数 (Losing Count)
        self.lc = 0

    # 交易通知方法，在交易关闭时被调用
    def notify_trade(self, trade):
        # 检查交易是否已关闭
        if trade.isclosed:
            # 获取交易的净盈亏
            p = trade.pnl
            # 如果盈亏 p 大于 0，则累加到总盈利 tpnl，盈利次数 wc 加 1
            (self.tpnl, self.wc) = (self.tpnl + p,
                                    self.wc + 1) if p > 0 else (self.tpnl, self.wc)
            # 如果盈亏 p 小于 0，则累加到总亏损 tlnl (累加负数)，亏损次数 lc 加 1
            (self.tlnl, self.lc) = (self.tlnl + p,
                                    self.lc + 1) if p < 0 else (self.tlnl, self.lc)

    # 回测结束时调用 stop 方法，用于计算最终结果
    def stop(self):
        # 计算平均每次盈利金额 (Average Win)
        # 如果盈利次数 wc 不为 0，则用总盈利除以次数，否则为 0.0
        aw = self.tpnl / self.wc if self.wc else 0.0
        # 计算平均每次亏损金额 (Average Loss) - 注意 al 会是负数或 0
        # 如果亏损次数 lc 不为 0，则用总亏损除以次数，否则为 0.0
        al = self.tlnl / self.lc if self.lc else 0.0
        # 计算毛利因子 (Gross Profit Factor, GPF)
        # GPF = 总盈利 / abs(总亏损) = 平均盈利 / abs(平均亏损)
        # 需要处理分母 al 为 0 的情况
        # 如果 al 不为 0，则计算 abs(aw / al)
        # 如果 al 为 0:
        #   如果 aw 也为 0 (没有盈利也没有亏损)，则 GPF 为 0.0
        #   如果 aw 不为 0 (只有盈利没有亏损)，则 GPF 为无穷大 (float('inf'))
        f = abs(aw / al) if al else float('inf') if aw else 0.0
        # 将计算结果存储在 self.rets 这个有序字典中，方便外部访问
        self.rets = OrderedDict([('aw', aw), ('al', al), ('gpf', f)])


# --- 主程序入口 ---
# 当直接运行这个 Python 文件时，以下代码会被执行
if __name__ == '__main__':
    # --- Cerebro 引擎设置 ---
    # 创建 Cerebro 核心引擎实例，stdstats=False 表示不使用 Backtrader 内置的标准统计输出
    cerebro = bt.Cerebro(stdstats=False)
    # 将我们定义的策略类添加到 Cerebro 引擎中
    cerebro.addstrategy(TestStrategy)

    # --- 添加 Observers ---
    # 添加 Broker 观察器，用于在图表中显示账户价值和现金的变化
    cerebro.addobserver(bt.observers.Broker)
    # 添加 Trades 观察器，用于在副图中显示每笔交易的持仓周期和盈亏条
    cerebro.addobserver(bt.observers.Trades)
    # 添加 BuySell 观察器，用于在主图的 K 线上用箭头标记买入和卖出点
    # barplot=True 让标记正好画在 K 线上方或下方，而不是价格线上
    cerebro.addobserver(bt.observers.BuySell, barplot=True)
    # --- 添加新的自定义事件驱动 Observer ---
    # 将我们自己编写的 TradeConnectObserver 添加到 Cerebro
    # 这个 Observer 会在主图上绘制交易连线
    cerebro.addobserver(TradeConnectObserver)
    # ---------------------------------

    # --- 添加 Analyzers ---
    # 添加交易分析器，用于统计详细的交易指标
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    # 添加夏普比率分析器，按日计算 (timeframe=Days, compression=1)，年化因子设为 252
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days,
                        compression=1, factor=252, annualize=True, _name='sharpe')
    # 添加最大回撤分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # 添加 SQN (System Quality Number) 分析器
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    # 添加我们自定义的毛利因子分析器
    cerebro.addanalyzer(GrossProfitFactorAnalyzer, _name='grossprofitfactor')

    # --- 数据加载 ---
    # 获取当前脚本文件所在的目录的绝对路径
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    # 构建 CSV 数据文件的完整路径 (假设 CSV 文件在同目录下的 '603186.csv')
    datapath = os.path.join(modpath, '603186.csv')
    # 使用 Backtrader 内置的 GenericCSVData 类来加载 CSV 文件
    data = bt.feeds.GenericCSVData(
        # 数据文件路径
        dataname=datapath,
        # 数据开始日期
        fromdate=datetime.datetime(2010, 1, 1),
        # 数据结束日期
        todate=datetime.datetime(2020, 4, 12),
        # CSV 文件中的日期时间格式
        dtformat='%Y%m%d',
        # 指定 CSV 文件中各列对应的 OHLCV 数据 (列索引从 0 开始)
        datetime=2,  # 日期时间在第 3 列
        open=3,      # 开盘价在第 4 列
        high=4,      # 最高价在第 5 列
        low=5,       # 最低价在第 6 列
        close=6,     # 收盘价在第 7 列
        volume=10,    # 成交量在第 11 列
        # 设置数据的时间周期为日线
        timeframe=bt.TimeFrame.Days,
        # 如果 CSV 文件中的数据是按时间倒序排列的 (最新的在前面)，则需要设置 reverse=True
        reverse=True)
    # 将加载好的数据添加到 Cerebro 引擎
    cerebro.adddata(data)

    # --- 回测设置 ---
    # 设置初始账户资金
    cerebro.broker.setcash(10000.0)
    # 添加一个 Sizer，用于决定每次交易买卖多少股
    # FixedSize 表示每次交易固定数量，stake=100 表示每次买卖 100 股
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    # 设置交易佣金，commission=0.005 表示佣金率为 0.5% (双边收取)
    cerebro.broker.setcommission(commission=0.005)

    # --- 运行与结果输出 ---
    # 打印回测开始前的初始投资组合价值
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    print('\n' + '-'*30 + ' 运行回测 ' + '-'*30)
    print('正在运行回测策略，将执行交易并记录开仓/平仓信息...')
    print('自定义Observer将捕获交易事件并绘制交易连线...')

    # 运行回测！Cerebro 会处理数据、执行策略、计算指标和分析器
    results = cerebro.run()
    # results 是一个包含策略实例的列表，我们只有一个策略，所以取第一个
    first_strategy = results[0]

    print('\n' + '-'*30 + ' 回测完成 ' + '-'*30)

    # --- 打印 Analyzer 分析结果 ---
    # 打印夏普比率
    print(
        f"夏普比率: {first_strategy.analyzers.sharpe.get_analysis()['sharperatio']:.3f}")
    # 打印最大回撤
    drawdown = first_strategy.analyzers.drawdown.get_analysis()
    print(f"最大回撤: {drawdown.max.drawdown:.2f}%")
    # 打印SQN
    sqn = first_strategy.analyzers.sqn.get_analysis()
    print(f"SQN: {sqn.sqn:.3f}")
    # 打印交易统计
    trade_analyzer = first_strategy.analyzers.tradeanalyzer.get_analysis()
    print(f"总交易次数: {trade_analyzer.total.closed}")
    print(f"盈利交易: {trade_analyzer.won.total} 亏损交易: {trade_analyzer.lost.total}")

    # 打印回测结束后的最终投资组合价值
    print("-" * 30 + " Final Portfolio Value " + "-" * 30)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # 替换为简化的提示信息
    print("\n连线功能说明: 图表上可以看到交易开仓点和平仓点之间的连线")
    print("- 绿色连线: 盈利交易")
    print("- 红色连线: 亏损交易")
    print("- 连线中间的数字: 交易盈亏金额")

    # --- 绘制图表 ---
    print('\n' + '-'*30 + ' 绘制回测图表 ' + '-'*30)
    print('正在生成包含交易连线的回测图表，请稍候...')
    # 调用 Cerebro 的 plot 方法生成包含 K 线、指标、观察器标记和分析器信息的图表
    # style='candlestick' 指定主图使用蜡烛图样式
    # 运行后会弹出一个图表窗口
    cerebro.plot(style='candlestick')
    print('图表生成完成！交易连线功能已实现！')
