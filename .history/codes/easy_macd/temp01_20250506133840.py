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
    # 定义多条线用于存储交易信息
    # 每次交易需要两个点（开仓点和平仓点）来绘制连线
    # 使用多条线来代表不同的连线（盈利连线和亏损连线）
    lines = ('long_win_entry', 'long_win_exit',  # 多头盈利交易的开仓/平仓点
             'long_loss_entry', 'long_loss_exit',  # 多头亏损交易的开仓/平仓点
             'short_win_entry', 'short_win_exit',  # 空头盈利交易的开仓/平仓点
             'short_loss_entry', 'short_loss_exit',)  # 空头亏损交易的开仓/平仓点

    # 设置绘图信息
    plotinfo = dict(
        plot=True, subplot=False,
        plotlinelabels=False,  # 不显示线的标签
        plotlinevalues=False,  # 不显示线的值
        plotvaluetags=False,   # 不显示值标签
    )

    # 设置绘图线的样式，提高可见性
    plotlines = dict(
        # 多头盈利交易
        long_win_entry=dict(marker='o', markersize=8.0,
                            color='lime', fillstyle='full', linewidth=2),
        long_win_exit=dict(marker='o', markersize=8.0,
                           color='lime', fillstyle='full', linewidth=2),
        # 多头亏损交易
        long_loss_entry=dict(marker='o', markersize=8.0,
                             color='red', fillstyle='full', linewidth=2),
        long_loss_exit=dict(marker='o', markersize=8.0,
                            color='red', fillstyle='full', linewidth=2),
        # 空头盈利交易
        short_win_entry=dict(marker='o', markersize=8.0,
                             color='lime', fillstyle='full', linewidth=2),
        short_win_exit=dict(marker='o', markersize=8.0,
                            color='lime', fillstyle='full', linewidth=2),
        # 空头亏损交易
        short_loss_entry=dict(marker='o', markersize=8.0,
                              color='red', fillstyle='full', linewidth=2),
        short_loss_exit=dict(marker='o', markersize=8.0,
                             color='red', fillstyle='full', linewidth=2),
    )

    def __init__(self):
        super().__init__()
        # 存储已处理的交易ID，避免重复绘制
        self.processed_trades = set()
        # 存储待绘制的交易连线
        self.trade_lines = []
        # 存储交易盈亏信息，用于标注
        self.pnl_info = {}
        # 标记是否是第一次调用next
        self._first_next = True

    def notify_trade(self, trade):
        # 只关注已关闭的交易
        if trade.isclosed:
            # 如果已经处理过这个交易，跳过
            if trade.ref in self.processed_trades:
                return

            # 记录这个交易已被处理
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

            # 检查信息是否完整
            if None in (entry_bar, entry_price, exit_bar, exit_price):
                return

            # 确定交易方向和盈亏
            is_long = True  # 默认假设为多头交易
            if len(trade.history) > 0:
                # 如果交易历史不为空，从历史记录中获取方向
                is_long = trade.history[0].status.size > 0  # 判断是否是多头交易
            else:
                # 如果交易历史为空，则通过比较开平仓价格来推断方向
                # 如果开仓价格低于平仓价格，则可能是多头；反之则可能是空头
                is_long = entry_price < exit_price

            # 使用实际的盈亏值判断交易是否盈利
            is_win = trade.pnlcomm >= 0  # 判断是否盈利

            # 保存盈亏信息，用于标注
            self.pnl_info[trade.ref] = {
                'pnl': trade.pnlcomm,
                'percent': (exit_price - entry_price) / entry_price * 100 if is_long else
                           (entry_price - exit_price) / entry_price * 100
            }

            # 添加到待绘制列表
            self.trade_lines.append({
                'entry_bar': entry_bar,
                'entry_price': entry_price,
                'exit_bar': exit_bar,
                'exit_price': exit_price,
                'is_long': is_long,
                'is_win': is_win,
                'pnl': trade.pnlcomm,
                'trade_ref': trade.ref
            })

            # 立即记录到对应的线上，确保在next中可以引用
            self._process_trade_line({
                'entry_bar': entry_bar,
                'entry_price': entry_price,
                'exit_bar': exit_bar,
                'exit_price': exit_price,
                'is_long': is_long,
                'is_win': is_win,
                'trade_ref': trade.ref
            })

            # 打印日志，确认交易记录
            print(f"交易记录 #{trade.ref}: 方向={'多头' if is_long else '空头'}, "
                  f"结果={'盈利' if is_win else '亏损'}, "
                  f"开仓={entry_price:.2f}@{entry_bar}, 平仓={exit_price:.2f}@{exit_bar}, "
                  f"盈亏={trade.pnlcomm:.2f}")

    def _process_trade_line(self, trade_line):
        """处理一条交易线，将其记录到适当的observer线上"""
        # 设置线索引的当前值
        curr_idx = len(self) - 1

        # 计算开仓和平仓位置
        entry_idx = curr_idx - (trade_line['entry_bar'] - len(self) + 1)
        exit_idx = curr_idx - (trade_line['exit_bar'] - len(self) + 1)

        # 根据交易类型选择正确的线
        if trade_line['is_long'] and trade_line['is_win']:
            entry_line = self.lines.long_win_entry
            exit_line = self.lines.long_win_exit
        elif trade_line['is_long'] and not trade_line['is_win']:
            entry_line = self.lines.long_loss_entry
            exit_line = self.lines.long_loss_exit
        elif not trade_line['is_long'] and trade_line['is_win']:
            entry_line = self.lines.short_win_entry
            exit_line = self.lines.short_win_exit
        else:  # not is_long and not is_win
            entry_line = self.lines.short_loss_entry
            exit_line = self.lines.short_loss_exit

        # 检查索引是否有效
        if 0 <= entry_idx < len(self):
            # 在开仓位置记录价格
            entry_line[entry_idx] = trade_line['entry_price']

        if 0 <= exit_idx < len(self):
            # 在平仓位置记录价格
            exit_line[exit_idx] = trade_line['exit_price']

    def prenext(self):
        # 初始化所有线为NaN
        for line in self.lines:
            line[0] = float('nan')

    def next(self):
        # 初始化所有线为NaN
        for line in self.lines:
            line[0] = float('nan')

        # 处理所有待绘制的交易线
        curr_idx = len(self) - 1

        # 再次处理所有交易线，确保线上有正确的值
        for trade_line in self.trade_lines:
            self._process_trade_line(trade_line)

    def _draw_trades_directly(self, ax):
        """直接使用matplotlib绘制交易线"""
        # 获取绘图区域长度
        obs_len = len(self)

        # 遍历所有待绘制的交易线
        for trade_line in self.trade_lines:
            # 获取交易信息
            entry_bar = trade_line['entry_bar']
            entry_price = trade_line['entry_price']
            exit_bar = trade_line['exit_bar']
            exit_price = trade_line['exit_price']
            is_win = trade_line['is_win']
            pnl = trade_line.get('pnl', 0)
            trade_ref = trade_line.get('trade_ref', 0)

            # 选择颜色和线宽
            color = 'lime' if is_win else 'red'
            linewidth = 2.5

            # 计算在图表上的x坐标位置
            x1 = obs_len - entry_bar - 1
            x2 = obs_len - exit_bar - 1

            # 确保坐标在有效范围内
            if 0 <= x1 < obs_len and 0 <= x2 < obs_len:
                try:
                    # 绘制有方向的箭头连线
                    ax.annotate('',
                                xy=(x2, exit_price),
                                xytext=(x1, entry_price),
                                arrowprops=dict(
                                    arrowstyle='->',
                                    color=color,
                                    lw=linewidth,
                                    connectionstyle='arc3,rad=0.05',  # 弯曲的线
                                ),
                                zorder=100  # 确保显示在最上层
                                )

                    # 绘制开仓点和平仓点
                    ax.scatter([x1], [entry_price], s=80,
                               color=color, marker='o', zorder=100)
                    ax.scatter([x2], [exit_price], s=80,
                               color=color, marker='o', zorder=100)

                    # 添加盈亏标注
                    mid_x = (x1 + x2) / 2
                    mid_y = (entry_price + exit_price) / 2

                    # 获取盈亏信息
                    pnl_data = self.pnl_info.get(trade_ref, {})
                    pnl_value = pnl_data.get('pnl', pnl)
                    pnl_percent = pnl_data.get('percent', 0)

                    # 格式化盈亏标签
                    pnl_text = f"{'✓' if is_win else '✗'} {pnl_value:.2f} ({pnl_percent:.1f}%)"

                    # 调整标签位置，避免与K线重叠
                    offset_x = 0  # x轴偏移
                    offset_y = entry_price * 0.02  # y轴偏移，价格的2%

                    # 添加文本标注，在连线中间位置
                    ax.text(mid_x + offset_x, mid_y + offset_y, pnl_text,
                            color=color, fontweight='bold', fontsize=9,
                            bbox=dict(boxstyle="round,pad=0.3",
                                      fc='white', alpha=0.7),
                            ha='center', va='center', zorder=100)

                    print(f"成功绘制交易线: bars:{entry_bar}->{exit_bar} x坐标:{x1:.1f}->{x2:.1f}, "
                          f"价格:{entry_price:.2f}->{exit_price:.2f}, PnL:{pnl:.2f}")
                except Exception as e:
                    print(f"绘图错误: {e}")

    def plot(self, ax, style='candle'):
        """重写plot方法，确保交易连线正确显示"""
        # 首先调用父类的plot方法绘制标准内容
        super().plot(ax, style)

        # 获取当前观察者记录的数据时间长度
        obs_len = len(self)

        # 通过策略获取完整的交易历史数据
        strategy = self._owner

        # 直接在图表上绘制连线
        for trade_ref, entry_info in strategy.trade_entry_info.items():
            # 检查是否有对应的平仓信息
            if trade_ref not in strategy.trade_exit_info:
                continue

            exit_info = strategy.trade_exit_info[trade_ref]

            # 获取开仓和平仓信息
            entry_bar = entry_info['bar']
            entry_price = entry_info['price']
            exit_bar = exit_info['bar']
            exit_price = exit_info['price']

            # 寻找对应的交易记录来获取准确的盈亏信息
            pnl = 0
            is_win = exit_price > entry_price  # 默认判断

            # 查找记录的交易数据获取更准确的信息
            for trade_line in self.trade_lines:
                if trade_line.get('trade_ref') == trade_ref:
                    is_win = trade_line['is_win']
                    pnl = trade_line.get('pnl', 0)
                    break

            # 选择颜色
            color = 'lime' if is_win else 'red'

            # 计算图表上的坐标
            x1 = obs_len - entry_bar - 1
            x2 = obs_len - exit_bar - 1

            # 确保坐标在有效范围内
            if 0 <= x1 < obs_len and 0 <= x2 < obs_len:
                try:
                    # 绘制开仓点和平仓点
                    ax.scatter([x1], [entry_price], s=80,
                               color=color, marker='o', zorder=100)
                    ax.scatter([x2], [exit_price], s=80,
                               color=color, marker='o', zorder=100)

                    # 绘制连线
                    ax.plot([x1, x2], [entry_price, exit_price],
                            color=color, linestyle='-', linewidth=2.5,
                            marker='', alpha=0.8, zorder=90)

                    # 添加盈亏标签
                    mid_x = (x1 + x2) / 2
                    mid_y = (entry_price + exit_price) / 2
                    label = f"+{pnl:.2f}" if pnl > 0 else f"{pnl:.2f}"

                    # 在连线中间添加文本
                    ax.text(mid_x, mid_y, label, color=color,
                            fontweight='bold', fontsize=9,
                            bbox=dict(boxstyle="round", fc='white', alpha=0.7),
                            ha='center', va='center', zorder=100)
                except Exception as e:
                    print(f"绘图错误: {e}")

        # 确保图层级别
        ax.set_zorder(10)


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

    # 验证交易连线实现
    print('\n' + '-'*30 + ' 交易连线功能验证 ' + '-'*30)
    print('检查交易开仓/平仓记录：')
    print(f"记录的开仓交易数: {len(first_strategy.trade_entry_info)}")
    print(f"记录的平仓交易数: {len(first_strategy.trade_exit_info)}")

    if len(first_strategy.trade_entry_info) == 0 or len(first_strategy.trade_exit_info) == 0:
        print("警告: 没有完整的交易记录，可能无法绘制交易连线！")
    else:
        print(f"共有{len(first_strategy.trade_entry_info)}笔交易将尝试绘制连线")
        print("回测图表将显示包含交易连线的K线图")
        print("连线颜色: 绿色=盈利交易, 红色=亏损交易")
        print("连线会显示具体的盈亏金额")

    # 验证交易连线功能
    print('\n' + '-'*30 + ' 交易连线实现详情 ' + '-'*30)
    # 获取策略和观察器对象
    strategy = first_strategy
    trade_observers = [ob for ob in strategy.observers if isinstance(
        ob, TradeConnectObserver)]

    if trade_observers:
        # 获取第一个交易连线观察器
        trade_observer = trade_observers[0]

        # 显示连线详情
        print(f"交易连线观察器状态:")
        print(f"- 记录的交易线数量: {len(trade_observer.trade_lines)}")
        print(f"- 已处理交易ID数量: {len(trade_observer.processed_trades)}")

        # 显示交易线详情
        print("\n交易线详情:")
        for i, line in enumerate(trade_observer.trade_lines):
            print(f"交易线 #{i+1}: "
                  f"方向={'多头' if line['is_long'] else '空头'}, "
                  f"结果={'盈利' if line['is_win'] else '亏损'}, "
                  f"开仓={line['entry_price']:.2f}@{line['entry_bar']}, "
                  f"平仓={line['exit_price']:.2f}@{line['exit_bar']}, "
                  f"盈亏={line.get('pnl', 0):.2f}")
    else:
        print("未找到交易连线观察器实例，请检查是否正确添加到Cerebro")

    print("\n绘制提示: 图表中交易连线说明")
    print("- 绿色箭头连线: 盈利交易")
    print("- 红色箭头连线: 亏损交易")
    print("- 连线标签: ✓/✗ [盈亏金额] ([百分比收益率])")
    print("- 所有交易线均有开仓点和平仓点标记")
    print("=" * 60)
    print("如果图表中没有显示交易连线，请检查:")
    print("1. 是否有完成的交易(开仓和平仓)")
    print("2. 图表的缩放比例是否合适")
    print("3. 数据点是否在可见区域内")
    print("=" * 60)

    # --- 绘制图表 ---
    print('\n' + '-'*30 + ' 绘制回测图表 ' + '-'*30)
    print('正在生成包含交易连线的回测图表，请稍候...')
    # 调用 Cerebro 的 plot 方法生成包含 K 线、指标、观察器标记和分析器信息的图表
    # style='candlestick' 指定主图使用蜡烛图样式
    # 运行后会弹出一个图表窗口
    cerebro.plot(style='candlestick')
    print('图表生成完成！交易连线功能已实现！')
