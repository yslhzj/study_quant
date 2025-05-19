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
# 响应交易关闭事件，在图上标记开仓和平仓点


class TradeEventObserver(bt.Observer):
    # 定义三条线，分别用于标记开仓点、盈利平仓点和亏损平仓点
    # 这些 'lines' 对象本质上是时间序列，我们会在特定时间点给它们赋值，其他时间点为 NaN
    lines = ('trade_entry', 'trade_exit_win',
             'trade_exit_loss',)
    # 设置绘图信息：
    # plot=True 表示这个 Observer 要画图
    # subplot=False 表示画在主图（价格 K 线所在图）上
    # plotlinelabels=True 表示显示每条线的名字标签 (比如 'trade_entry')
    plotinfo = dict(
        plot=True, subplot=False,
        plotlinelabels=True,
    )

    # 分别设置三条线的绘图样式
    plotlines = dict(
        # 开仓标记：marker='^' 使用向上三角符号
        # markersize=8.0 设置符号大小
        # color='blue' 设置颜色为蓝色
        # fillstyle='full' 表示填充符号
        # ls='' 表示不画连接线，只画标记点
        trade_entry=dict(marker='^', markersize=8.0, color='blue',
                         fillstyle='full', ls=''),
        # 盈利平仓标记：marker='o' 使用圆形符号，颜色为绿色
        trade_exit_win=dict(marker='o', markersize=8.0,
                            color='green', fillstyle='full', ls=''),
        # 亏损平仓标记：marker='v' 使用向下三角符号，颜色为红色
        trade_exit_loss=dict(marker='v', markersize=8.0,
                             color='red', fillstyle='full', ls=''),
    )

    # 初始化方法
    def __init__(self):
        # 调用父类 bt.Observer 的初始化方法
        super().__init__()
        # 初始化时，将当前 K 线 (索引 0) 的所有标记线的值设置为 NaN (Not a Number)
        # NaN 在绘图中表示该点不绘制
        self.lines.trade_entry[0] = math.nan
        self.lines.trade_exit_win[0] = math.nan
        self.lines.trade_exit_loss[0] = math.nan

    # 核心方法：当有交易事件通知时被 Backtrader 调用
    # trade 参数是包含了该笔交易信息的对象
    def notify_trade(self, trade):
        # 检查这笔交易 (trade) 是否已经关闭 (isclosed)
        if trade.isclosed:
            # --- 获取交易信息 ---
            # self._owner 指向拥有这个 Observer 的对象，也就是我们的策略 TestStrategy 实例
            # 我们需要从策略实例中预存的字典里获取开平仓信息
            # 使用 .get(trade.ref, {}) 安全地获取字典，如果 trade.ref 不存在则返回空字典 {}
            # 再用 .get('bar') 或 .get('price') 获取具体值，不存在则返回 None

            # 获取开仓时的 K 线索引 (第几根 K 线，从 0 开始)
            entry_bar = self._owner.trade_entry_info.get(
                trade.ref, {}).get('bar')
            # 获取开仓时的执行价格
            entry_price = self._owner.trade_entry_info.get(
                trade.ref, {}).get('price')
            # 获取平仓时的 K 线索引
            exit_bar = self._owner.trade_exit_info.get(
                trade.ref, {}).get('bar')
            # 获取平仓时的执行价格
            exit_price = self._owner.trade_exit_info.get(
                trade.ref, {}).get('price')
            # 获取这笔交易的净盈亏 (Profit and Loss, 扣除佣金后的)
            pnl = trade.pnlcomm

            # --- 标记开仓点 ---
            # 检查是否成功获取到了开仓的 bar 索引和价格
            if entry_bar is not None and entry_price is not None:
                # 获取当前 Observer 正在处理的 K 线的索引 (即最新的 K 线索引)
                current_bar_index = len(self) - 1
                # 确保开仓 bar 索引是有效的 (小于等于当前索引)
                if entry_bar <= current_bar_index:
                    # 计算当前 K 线索引与开仓 K 线索引之间的差值 (偏移量)
                    # 这个偏移量告诉我们开仓事件发生在多少根 K 线之前
                    idx_offset = current_bar_index - entry_bar
                    # 在 lines 对象中使用负索引可以访问历史数据
                    # -idx_offset 就定位到了发生开仓的那根 K 线
                    # 将开仓价格赋值给 trade_entry 线的对应历史位置
                    self.lines.trade_entry[-idx_offset] = entry_price
                    # 【重要】清除同一根历史 K 线上的其他标记，防止标记重叠显示
                    # 因为一根 K 线理论上只应该有一个开仓或平仓事件标记
                    self.lines.trade_exit_win[-idx_offset] = math.nan
                    self.lines.trade_exit_loss[-idx_offset] = math.nan

            # --- 标记平仓点 ---
            # 检查是否成功获取到了平仓的 bar 索引和价格
            if exit_bar is not None and exit_price is not None:
                # 在当前 K 线 (索引 0) 标记平仓价格
                # 根据盈亏 pnl 判断使用哪个标记线
                if pnl >= 0:
                    # 如果盈利或盈亏为 0，使用 trade_exit_win 线标记
                    self.lines.trade_exit_win[0] = exit_price
                    # 清除同一 K 线上的亏损标记
                    self.lines.trade_exit_loss[0] = math.nan
                else:
                    # 如果亏损，使用 trade_exit_loss 线标记
                    self.lines.trade_exit_loss[0] = exit_price
                    # 清除同一 K 线上的盈利标记
                    self.lines.trade_exit_win[0] = math.nan

    # 每个 K 线周期结束时 Backtrader 会调用 next 方法
    def next(self):
        # 重置当前 K 线 (索引 0) 的所有标记为 NaN
        # 这是非常重要的步骤！因为标记是事件驱动的，只应出现在事件发生的 K 线上。
        # 如果不在这里重置，上一个 K 线的标记值会“延续”到当前 K 线，导致错误的连续标记。
        self.lines.trade_entry[0] = math.nan
        self.lines.trade_exit_win[0] = math.nan
        self.lines.trade_exit_loss[0] = math.nan


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
        # 【修复】删除下面这行导致 AttributeError 的代码
        # 'LinesOperation' object has no attribute 'plotinfo'
        # self.macd_histo.plotinfo.plot = False
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

    # 订单状态通知方法，当订单状态变化时 Backtrader 调用
    def notify_order(self, order):
        # 如果订单状态是“已提交”或“已接受”，说明还在处理中，暂时忽略
        if order.status in [order.Submitted, order.Accepted]:
            return

        # --- 原本在订单完成时记录信息的逻辑已移至 notify_trade ---
        # 因为 notify_trade 能更方便地关联交易 (trade) 和订单 (order)
        # if order.status == order.Completed:
        #     ... (原始逻辑注释掉或移除) ...

        # 如果订单处理完毕 (无论完成、取消、拒绝等)，重置 self.order 变量
        # 表示当前没有需要跟踪的活动订单了 (这个策略似乎只跟踪一个订单)
        self.order = None

    # 交易状态通知方法，当交易状态变化时 Backtrader 调用
    def notify_trade(self, trade):
        # --- 在交易首次打开时 (justopened) 记录开仓信息 ---
        if trade.justopened:
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
            # 打印日志，方便调试 (可选)
            # print(f"Trade {trade.ref} opened: Bar={trade.baropen}, Price={entry_order.executed.price}")

        # --- 在交易关闭时 (isclosed) 记录平仓信息 ---
        if trade.isclosed:
            # history[-1] 通常是最后一个事件，即平仓事件
            exit_order = trade.history[-1].event.order
            # 使用 trade.ref 作为键，存储平仓信息
            self.trade_exit_info[trade.ref] = {
                # 记录平仓时的 K 线索引 (barclose 是 trade 对象的属性)
                'bar': trade.barclose,
                # 记录平仓订单的实际执行价格
                'price': exit_order.executed.price
            }
            # 打印日志，方便调试 (可选)
            # print(f"Trade {trade.ref} closed: Bar={trade.barclose}, Price={exit_order.executed.price}, PnL={trade.pnlcomm}")

            # 可选：清理 trade_entry_info 中已关闭交易的条目以节省内存
            # 但由于 Observer 可能在之后还需要读取，所以在这个例子中暂时保留
            # if trade.ref in self.trade_entry_info:
            #     pass # 或者 del self.trade_entry_info[trade.ref]

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
    def notify_trade(self, t):
        # 检查交易是否已关闭
        if t.isclosed:
            # 获取交易的净盈亏
            p = t.pnl
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
    # 将我们自己编写的 TradeEventObserver 添加到 Cerebro
    # 这个 Observer 会在主图上标记开仓和平仓点
    cerebro.addobserver(TradeEventObserver)
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
    # 运行回测！Cerebro 会处理数据、执行策略、计算指标和分析器
    results = cerebro.run()
    # results 是一个包含策略实例的列表，我们只有一个策略，所以取第一个
    first_strategy = results[0]

    # --- 打印 Analyzer 分析结果 ---
    # 这里可以添加代码来获取并打印各个 Analyzer 的分析结果
    # 例如:
    # print("Sharpe Ratio:", first_strategy.analyzers.sharpe.get_analysis())
    # print("Max Drawdown:", first_strategy.analyzers.drawdown.get_analysis())
    # print("SQN:", first_strategy.analyzers.sqn.get_analysis())
    # print("Gross Profit Factor:", first_strategy.analyzers.grossprofitfactor.get_analysis())
    # print("Trade Analysis:", first_strategy.analyzers.tradeanalyzer.get_analysis())
    # (为简洁起见，具体打印代码省略)

    # 打印回测结束后的最终投资组合价值
    print("-" * 30 + " Final Portfolio Value " + "-" * 30)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # --- 绘制图表 ---
    # 调用 Cerebro 的 plot 方法生成包含 K 线、指标、观察器标记和分析器信息的图表
    # style='candlestick' 指定主图使用蜡烛图样式
    # 运行后会弹出一个图表窗口
    cerebro.plot(style='candlestick')
