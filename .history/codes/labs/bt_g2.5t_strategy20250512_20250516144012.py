# codes/labs/bt_g2.5t_strategy20250512.py
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import backtrader as bt
import pandas as pd
import numpy as np
import itertools
from tabulate import tabulate # 确保已安装：pip install tabulate


# 自定义分析器，用于参数优化时返回更多指标
class OptAShareETFStrategyReturn(bt.analyzers.OptReturn):
    # analyzers.OptReturn本身就设计为在优化时收集每个参数组合的策略表现。
    # 我们这里继承它，主要是为了演示可以如何自定义或扩展。
    # 在本例中，我们其实可以直接用OptReturn，然后在策略的stop方法中把想要的指标放入self.analyzers.optreturn.rets中。
    # 但为了更清晰地展示如何添加自定义分析指标，我们创建一个子类。
    # 注意：实际上，如果只是添加几个数值指标，更推荐的做法是在策略的stop方法中直接操作 self.analyzers.optreturn.rets
    # 这里我们为了演示获取自定义的交易类型计数，稍微调整一下get_analysis

    def get_analysis(self):
        # 基础分析结果已经由父类收集在 self.rets 中
        # self.rets 在优化过程中，每个策略实例的stop方法被调用后，
        # 会收集该策略实例 self.analyzers.optreturn.rets 的内容。
        # 如果策略直接将 'trend_trade_count' 和 'range_trade_count' 放入了 self.analyzers.optreturn.rets，
        # 那么这里理论上不需要额外操作，它们应该已经存在于 self.rets 中了。
        # 但为了确保，我们假设策略将这些值存储在了一个特定的地方，例如 strategy.trade_type_counts
        
        # 在实际优化运行时，self.strategy 是当前参数组合下运行的策略实例
        # 而 self.rets 是一个列表，每个元素对应一个参数组合的运行结果(通常是一个字典)
        # 我们需要确保在策略的stop方法中，已经将这些自定义的值加入到分析器的rets中
        
        # 对于参数优化，get_analysis 通常在所有参数组合运行完毕后，由Cerebro的run方法内部调用以汇总结果。
        # 此时，self.rets 包含了所有参数组合的结果。
        # 如果我们需要在每个参数组合运行结束时就获取特定值，那应该在策略的stop方法中处理。

        # 这里我们假设，在策略的stop方法中，已经将 trend_trade_count 和 range_trade_count 
        # 添加到了 self.analyzers.optreturn.rets (或者我们自定义的分析器的rets)。
        # 父类的 get_analysis 会处理这些。
        # 因此，我们主要关注的是确保这些值被正确地收集。

        # 修正：在优化结束时，OptReturn (或其子类) 的 get_analysis 返回的是一个列表的列表，
        # 每个内部列表代表一个参数组合的运行结果，包含参数值和分析器返回的指标。
        # 我们这里想要的是在分析器内部处理，确保它能拿到策略计算出的额外信息。
        # 策略的 stop 方法是关键。

        # 我们在策略的 stop 方法中，会把 trend_trade_count 和 range_trade_count 
        # 放入 self.analyzers.opt_ashare_etf_strategy_return.rets
        # （其中 opt_ashare_etf_strategy_return 是我们给这个分析器实例起的名字）
        
        # 父类的 get_analysis 会处理好这部分，所以我们这里不需要特别做什么。
        # 这里的 get_analysis 是在单个策略运行结束时被调用，以返回其分析结果。
        # 对于OptReturn及其子类，它的主要逻辑是在Cerebro层面汇总所有策略实例的结果。
        
        # 让我们简化一下，假设策略的stop方法已经把所有需要的值都放进了
        # self.analyzers.opt_ashare_etf_strategy_return.rets 字典中。
        # 那么父类的 get_analysis 就能正确处理。

        # 如果我们需要在OptReturn的子类中 *添加* 额外的计算逻辑（基于策略运行结束时的状态），
        # 可以在这里进行，但通常收集数据点是在策略的stop方法中。

        # 假设在策略的 stop 方法中，已经将 trend_trade_count 和 range_trade_count
        # 添加到了 self.rets (这是 OptReturn 内部用于存储单个策略运行结果的字典)
        # 那么父类的 get_analysis 就能正常工作。

        # 为了演示，我们假设策略将这些值存储在其自身的一个属性中，
        # 并且我们在策略的stop方法中将它们传递给了这个分析器。
        
        # 正确的做法是在策略的 stop 方法中，将自定义的统计结果放入 self.analyzers.myanalyzer.rets 字典中。
        # 例如:
        # def stop(self):
        #     self.analyzers.myanalyzer.rets['trend_trades'] = self.trend_trade_count
        #     self.analyzers.myanalyzer.rets['range_trades'] = self.range_trade_count
        #     # 其他分析指标...

        # 然后，OptAShareETFStrategyReturn 的 get_analysis 方法（继承自OptReturn）
        # 会在每个策略实例结束时被调用，并返回这个 rets 字典。
        # Cerebro 随后会收集所有这些字典。

        # 所以，这个 get_analysis 方法本身不需要做太多事情，
        # 除非我们要在这里基于 self.strategy 的最终状态进行一些额外的计算。
        # 但我们已经决定在策略的 stop 中进行计算和存储。

        # 因此，这个自定义类的主要目的是确保分析器被正确添加和命名，
        # 并且策略知道将结果存储到哪里。
        # 父类 OptReturn 的 get_analysis 已经足够。
        
        # 返回的是一个字典，包含了该策略实例的分析结果
        return self.rets 


class AShareETFStrategy(bt.Strategy):
    """
    A股ETF增强策略（演示版本）
    核心逻辑：
    1. 基于EMA均线判断趋势方向。
    2. 基于布林带判断波动区间。
    3. 结合市场状态（趋势/盘整）和预设的ETF类型（趋势型/区间型）进行交易决策。
    4. 动态风险管理：基于ATR计算止损，根据账户价值和回撤调整仓位。
    """
    params = (
        ('ema_short_period', 20),
        ('ema_medium_period', 40),
        ('ema_long_period', 60),
        ('bbands_period', 20),
        ('bbands_devfactor', 2.0),
        ('atr_period', 14),
        ('trend_stop_loss_atr_multiplier', 2.0), # 趋势跟踪止损ATR倍数
        ('range_stop_loss_buffer', 0.005), # 区间交易止损缓冲 (百分比)
        ('trend_risk_percentage', 0.01), # 趋势交易单笔风险占总资金百分比
        ('range_risk_percentage', 0.005), # 区间交易单笔风险占总资金百分比
        ('printlog', True), # 是否打印日志
        # ('etf_type', 'trend'), # 策略针对的ETF类型: 'trend' 或 'range'，在多数据时，这个参数意义不大，除非针对特定数据
        ('initial_cash_per_etf', 100000), # 假设每个ETF的初始模拟资金，用于Sizer计算（如果Sizer依赖）
        ('max_drawdown_limit_1', 0.05), # 第一级最大回撤限制
        ('max_drawdown_action_1_reduce_risk', 0.5), # 触发一级回撤后，风险参数降低比例
        ('max_drawdown_limit_2', 0.10), # 第二级最大回撤限制
        ('max_drawdown_action_2_halt_trading_days', 20), # 触发二级回撤后，暂停交易天数
        ('sma_filter_period', 200), # 用于过滤市场整体趋势的SMA周期
        ('rsi_period', 14), # RSI周期，用于辅助判断超买超卖
        ('rsi_overbought', 70), # RSI超买阈值
        ('rsi_oversold', 30), # RSI超卖阈值
        ('adx_period', 14), # ADX周期，用于判断趋势强度
        ('adx_threshold', 25), # ADX趋势强度阈值
    )

    def __init__(self):
        self.inds = {} # 存储每个数据源的指标
        self.orders = {} # 存储每个数据源的活动订单
        self.buy_prices = {} # 存储每个数据源的买入价格
        self.position_types = {} # 存储每个数据源的持仓类型 ('trend_long', 'range_long', 'range_short')
        self.pending_trade_info = {} # 存储每个数据源待Sizer处理的交易信息

        # 风险管理相关
        self.highest_equity = self.broker.getvalue() # 账户历史最高价值
        self.current_drawdown = 0.0 # 当前回撤
        self.halt_trading_until = None # 暂停交易截止日期
        self.risk_reduction_factor = 1.0 # 风险降低因子，初始为1.0

        # 为参数优化时统计不同类型的交易次数
        self.trend_trade_count = 0
        self.range_trade_count = 0


        for i, d in enumerate(self.datas):
            d_name = d._name # 获取数据源的名称

            self.inds[d_name] = {} # 为当前数据源创建一个指标字典

            # EMA均线
            self.inds[d_name]['ema_short'] = bt.indicators.ExponentialMovingAverage(d.close, period=self.p.ema_short_period)
            self.inds[d_name]['ema_medium'] = bt.indicators.ExponentialMovingAverage(d.close, period=self.p.ema_medium_period)
            self.inds[d_name]['ema_long'] = bt.indicators.ExponentialMovingAverage(d.close, period=self.p.ema_long_period)

            # 布林带
            self.inds[d_name]['bbands'] = bt.indicators.BollingerBands(d.close, period=self.p.bbands_period, devfactor=self.p.bbands_devfactor)
            
            # ATR 用于止损
            self.inds[d_name]['atr'] = bt.indicators.AverageTrueRange(d, period=self.p.atr_period)

            # SMA 用于大趋势过滤
            self.inds[d_name]['sma_filter'] = bt.indicators.SimpleMovingAverage(d.close, period=self.p.sma_filter_period)
            
            # RSI 用于辅助判断超买超卖
            self.inds[d_name]['rsi'] = bt.indicators.RelativeStrengthIndex(d.close, period=self.p.rsi_period)

            # ADX 用于判断趋势强度
            self.inds[d_name]['adx'] = bt.indicators.AverageDirectionalMovementIndex(d, period=self.p.adx_period)


            self.orders[d_name] = None # 初始化订单状态
            self.buy_prices[d_name] = None # 初始化买入价格
            self.position_types[d_name] = None # 初始化持仓类型

        self.log(f"策略参数: EMA短周期={self.p.ema_short_period}, EMA中周期={self.p.ema_medium_period}, EMA长周期={self.p.ema_long_period}, "
                 f"布林带周期={self.p.bbands_period}, 布林带标准差={self.p.bbands_devfactor}, ATR周期={self.p.atr_period}, "
                 f"趋势止损ATR倍数={self.p.trend_stop_loss_atr_multiplier}, 区间止损缓冲={self.p.range_stop_loss_buffer}, "
                #  f"ETF类型='{self.p.etf_type}', "
                 f"趋势风险={self.p.trend_risk_percentage*100:.2f}%, 区间风险={self.p.range_risk_percentage*100:.2f}%, "
                 f"SMA过滤周期={self.p.sma_filter_period}, RSI周期={self.p.rsi_period}, ADX周期={self.p.adx_period}, ADX阈值={self.p.adx_threshold}")


    def log(self, txt, dt=None, doprint=False):
        if self.p.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            time_str = self.datas[0].datetime.time(0).strftime("%H:%M:%S") if len(self.datas[0]) else "N/A"
            print(f'{dt.isoformat()} {time_str} - {txt}')

    def notify_order(self, order):
        d_name = order.data._name # 获取订单对应的数据源名称

        if order.status in [order.Submitted, order.Accepted]:
            self.log(f'订单已提交/已接受: {order.getordername()} Ref:{order.ref}, Size:{order.size:.0f}, Price:{order.price:.2f}, For {d_name}')
            self.orders[d_name] = order # 更新活动订单
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: Ref:{order.ref}, {order.executed.size:.0f} 股, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}, For {d_name}')
                self.buy_prices[d_name] = order.executed.price # 记录买入价格
                # self.position_types[d_name] 已在下单前设置
            elif order.issell():
                self.log(f'卖出执行: Ref:{order.ref}, {order.executed.size:.0f} 股, 价格: {order.executed.price:.2f}, 收入: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}, For {d_name}')
                # 在卖出完成后，如果需要，可以重置 buy_price 和 position_type，但这通常在 notify_trade 中处理更合适
            
            self.orders[d_name] = None # 清除已完成的订单

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            self.log(f'订单取消/保证金/拒绝/过期: {order.getordername()} Ref:{order.ref}, Status: {order.getstatusname()}, For {d_name}')
            # 如果是开仓订单失败，需要重置 pending_trade_info
            if d_name in self.pending_trade_info and self.pending_trade_info[d_name].get('order_ref') == order.ref:
                self.log(f"开仓订单 {order.ref} 失败，清除 {d_name} 的 pending_trade_info")
                del self.pending_trade_info[d_name]

            self.orders[d_name] = None # 清除订单

    def notify_trade(self, trade):
        d_name = trade.data._name # 获取交易对应的数据源名称

        if not trade.isclosed:
            # 只有当交易记录被创建时（即开仓时），这个if分支才会被执行一次。
            # 后续的交易更新（如价格变动导致盈亏变化）不会再次进入此分支。
            self.log(f'开仓交易: Ref:{trade.ref}, 品种:{d_name}, 数量:{trade.size:.0f}, 开仓价:{trade.price:.2f}, 当前状态:{trade.status_names[trade.status]}')
            return

        # 当交易关闭时 (trade.isclosed is True)
        self.log(f'平仓交易: Ref:{trade.ref}, 品种:{d_name}, 毛利:{trade.pnl:.2f}, 净利:{trade.pnlcomm:.2f}, 持仓类型:{self.position_types.get(d_name, "N/A")}')
        
        # 根据平仓时的持仓类型，增加相应的交易计数
        position_type_closed = self.position_types.get(d_name)
        if position_type_closed:
            if 'trend' in position_type_closed:
                self.trend_trade_count += 1
                self.log(f"趋势交易计数增加: {self.trend_trade_count} (来自 {d_name})")
            elif 'range' in position_type_closed:
                self.range_trade_count += 1
                self.log(f"区间交易计数增加: {self.range_trade_count} (来自 {d_name})")


        # 重置该数据源的状态
        if self.position_types.get(d_name) is not None:
            self.position_types[d_name] = None
            self.log(f"已重置 {d_name} 的持仓类型 (position_type)")
        if self.buy_prices.get(d_name) is not None: # 确保key存在
            self.buy_prices[d_name] = None
            self.log(f"已重置 {d_name} 的买入价格 (buy_price)")
        
        # 确保 pending_trade_info 中的信息也被清理，如果它是导致这次交易的
        # 通常 pending_trade_info 在下单成功后就应该被 sizer 或策略本身清理
        # 但为了保险，可以检查一下
        if d_name in self.pending_trade_info:
            # 这个检查可能不完全准确，因为 trade.ref 和 pending_trade_info.order_ref 可能不直接对应
            # 更好的做法是在下单成功后由sizer或策略清理pending_trade_info
            self.log(f"交易关闭，检查并考虑清理 {d_name} 的 pending_trade_info (如果相关)")
            # del self.pending_trade_info[d_name] # 谨慎使用，确保逻辑正确

    def notify_cashvalue(self, cash, value):
        """当账户现金或总价值发生变化时调用"""
        self.log(f'现金 {cash:.2f}, 总价值 {value:.2f}')
        
        # 更新最高权益和当前回撤
        if value > self.highest_equity:
            self.highest_equity = value
        self.current_drawdown = (self.highest_equity - value) / self.highest_equity if self.highest_equity > 0 else 0
        
        self.log(f'当前账户最高权益: {self.highest_equity:.2f}, 当前回撤: {self.current_drawdown*100:.2f}%')

        # 检查是否触发回撤控制
        if self.current_drawdown >= self.p.max_drawdown_limit_2:
            if self.halt_trading_until is None or self.datas[0].datetime.date(0) > self.halt_trading_until:
                self.halt_trading_until = self.datas[0].datetime.date(0) + datetime.timedelta(days=self.p.max_drawdown_action_2_halt_trading_days)
                self.risk_reduction_factor = 0.0 # 暂停交易期间，风险因子设为0
                self.log(f'触发二级回撤限制 ({self.p.max_drawdown_limit_2*100:.2f}%), 暂停所有交易至 {self.halt_trading_until.isoformat()}', doprint=True)
        elif self.current_drawdown >= self.p.max_drawdown_limit_1:
            if self.risk_reduction_factor == 1.0: # 确保只在首次触发时降低
                 self.risk_reduction_factor = 1.0 - self.p.max_drawdown_action_1_reduce_risk
                 self.log(f'触发一级回撤限制 ({self.p.max_drawdown_limit_1*100:.2f}%), 风险参数降低至 {self.risk_reduction_factor*100:.0f}%', doprint=True)
        else:
            # 如果回撤恢复到一级限制以下，且之前降低过风险，可以考虑恢复 (可选逻辑)
            if self.risk_reduction_factor < 1.0 and self.current_drawdown < self.p.max_drawdown_limit_1 * 0.8: # 恢复到一级回撤的80%以下
                self.log(f'回撤改善，风险参数恢复至100%', doprint=True)
                self.risk_reduction_factor = 1.0
            # 如果暂停交易到期，也恢复风险因子（如果回撤已改善）
            if self.halt_trading_until and self.datas[0].datetime.date(0) > self.halt_trading_until:
                self.log(f'暂停交易期结束，检查是否可以恢复交易', doprint=True)
                self.halt_trading_until = None
                if self.current_drawdown < self.p.max_drawdown_limit_2 : # 确保回撤已经不在二级暂停区
                    self.risk_reduction_factor = 1.0 # 假设恢复到100%，或基于当前回撤决定
                    if self.current_drawdown >= self.p.max_drawdown_limit_1:
                        self.risk_reduction_factor = 1.0 - self.p.max_drawdown_action_1_reduce_risk


    def next(self):
        current_date = self.datas[0].datetime.date(0)
        # 检查是否处于暂停交易期
        if self.halt_trading_until and current_date <= self.halt_trading_until:
            if current_date == self.halt_trading_until: # 最后一天打印日志
                 self.log(f'处于暂停交易期 (至 {self.halt_trading_until.isoformat()})，本日不进行任何操作。')
            return

        for i, d in enumerate(self.datas):
            d_name = d._name
            pos = self.getposition(d)
            
            # 获取当前数据源的活动订单。如果存在，则不进行新的操作。
            if self.orders.get(d_name):
                self.log(f"数据源 {d_name} 存在活动订单 {self.orders[d_name].ref}，跳过此次 next")
                continue
            
            # 指标获取
            close = d.close[0]
            ema_short = self.inds[d_name]['ema_short'][0]
            ema_medium = self.inds[d_name]['ema_medium'][0]
            ema_long = self.inds[d_name]['ema_long'][0]
            bb_top = self.inds[d_name]['bbands'].lines.top[0]
            bb_mid = self.inds[d_name]['bbands'].lines.mid[0]
            bb_bot = self.inds[d_name]['bbands'].lines.bot[0]
            atr_val = self.inds[d_name]['atr'][0]
            sma_filter = self.inds[d_name]['sma_filter'][0]
            rsi = self.inds[d_name]['rsi'][0]
            adx = self.inds[d_name]['adx'].lines.adx[0]


            # 确定当前市场状态 (针对当前数据 d)
            market_state = 'UNCERTAIN_DO_NOT_TRADE' # 默认为不交易状态
            
            # 趋势判断 (基于均线排列和ADX强度)
            is_uptrend_ema = ema_short > ema_medium > ema_long
            is_downtrend_ema = ema_short < ema_medium < ema_long
            is_adx_strong_trend = adx > self.p.adx_threshold

            # 区间判断 (基于价格在布林带内的位置，以及ADX不指示强趋势)
            is_price_near_bb_bot = close < bb_bot * (1 + 0.01) # 价格接近下轨 (1%以内)
            is_price_near_bb_top = close > bb_top * (1 - 0.01) # 价格接近上轨 (1%以内)
            is_adx_weak_trend_or_range = adx < self.p.adx_threshold * 0.8 # ADX指示弱趋势或盘整


            # 状态决策逻辑
            if is_uptrend_ema and is_adx_strong_trend and close > sma_filter:
                market_state = 'TREND_UP'
            elif is_downtrend_ema and is_adx_strong_trend and close < sma_filter:
                market_state = 'TREND_DOWN'
            elif is_adx_weak_trend_or_range: # 如果ADX指示非强趋势，则考虑区间
                # 可以在这里加入更精细的区间确认逻辑，例如价格在布林带中轨附近震荡一段时间
                # 或者波动率指标(如ATR/布林带宽)处于较低水平
                # 为了简化，我们暂时认为ADX弱就可能是区间
                if is_price_near_bb_bot:
                    market_state = 'RANGE_LOW_POTENTIAL_BUY'
                elif is_price_near_bb_top:
                    market_state = 'RANGE_HIGH_POTENTIAL_SELL'
                else:
                    market_state = 'RANGE_CONFIRMED_NEUTRAL' # 在区间中部，等待机会
            else: # 其他情况，比如均线纠缠但ADX又不够弱，或者ADX强但均线不配合
                market_state = 'UNCERTAIN_TRANSITIONING'


            self.log(f"数据 {d_name}: Close={close:.2f}, MarketState={market_state}, ADX={adx:.2f}, RSI={rsi:.2f}, PosSize={pos.size}")


            # 交易决策逻辑
            potential_position_type = None # 'trend_long', 'range_long', 'range_short'
            entry_price = None
            risk_per_share = None # 对于趋势是ATR，对于区间是到止损线的距离
            amount_to_risk_for_trade = None # 本次交易愿意承担的总风险金额

            # 清仓逻辑 (通用，应优先于开仓)
            if pos.size > 0: # 当前持有多头仓位
                current_pos_type = self.position_types.get(d_name)
                stop_loss_price = -1

                if current_pos_type == 'trend_long':
                    stop_loss_price = self.buy_prices.get(d_name, close) - self.p.trend_stop_loss_atr_multiplier * atr_val
                    if close < stop_loss_price:
                        self.log(f'趋势多头止损: {d_name} 平仓. Close={close:.2f} < SL={stop_loss_price:.2f}')
                        self.close(data=d, exectype=bt.Order.Market) # 市价平仓
                        self.orders[d_name] = "placeholder_sell_trend_sl" # 标记有卖单，避免重复下单
                        continue
                    # 趋势跟踪也可以有止盈逻辑，例如均线反转或RSI超买后回落
                    if market_state == 'TREND_DOWN' or (is_downtrend_ema and rsi < 50): # 趋势反转信号
                        self.log(f'趋势多头止盈/反转信号: {d_name} 平仓. MarketState={market_state}')
                        self.close(data=d, exectype=bt.Order.Market)
                        self.orders[d_name] = "placeholder_sell_trend_tp"
                        continue

                elif current_pos_type == 'range_long':
                    stop_loss_price = self.buy_prices.get(d_name, bb_bot) * (1 - self.p.range_stop_loss_buffer) # 基于买入价或下轨
                    take_profit_price = bb_top # 区间上轨止盈
                    if close < stop_loss_price:
                        self.log(f'区间多头止损: {d_name} 平仓. Close={close:.2f} < SL={stop_loss_price:.2f}')
                        self.close(data=d, exectype=bt.Order.Market)
                        self.orders[d_name] = "placeholder_sell_range_sl"
                        continue
                    if close > take_profit_price:
                        self.log(f'区间多头止盈: {d_name} 平仓. Close={close:.2f} > TP={take_profit_price:.2f}')
                        self.close(data=d, exectype=bt.Order.Market)
                        self.orders[d_name] = "placeholder_sell_range_tp"
                        continue
                    # 如果市场状态变为趋势，区间单也应考虑平仓
                    if market_state == 'TREND_UP' or market_state == 'TREND_DOWN':
                         self.log(f'市场转为趋势 ({market_state}), 区间多头 {d_name} 平仓.')
                         self.close(data=d, exectype=bt.Order.Market)
                         self.orders[d_name] = "placeholder_sell_range_market_change"
                         continue
            
            # 简化版：暂不考虑做空
            # if pos.size < 0: # 当前持有空头仓位 (仅当策略支持做空时)
            #     current_pos_type = self.position_types.get(d_name)
            #     # 类似的止损止盈逻辑 for range_short or trend_short


            # 开仓逻辑 (仅当没有持仓时)
            if pos.size == 0:
                # 趋势做多逻辑
                # if market_state == 'TREND_UP' and self.p.etf_type == 'trend': # 假设这个参数用于选择策略类型
                if market_state == 'TREND_UP': # 简化：只要市场是上升趋势就考虑趋势做多
                    # 附加条件：例如回调到短期均线附近，或RSI未超买
                    if close > ema_short and rsi < self.p.rsi_overbought - 10: # 价格在短期均线上方，且RSI未严重超买
                        potential_position_type = 'trend_long'
                        entry_price = close # 假设市价入场，或限价单使用当前价格作为参考
                        risk_per_share = self.p.trend_stop_loss_atr_multiplier * atr_val
                        amount_to_risk_for_trade = self.broker.getvalue() * self.p.trend_risk_percentage * self.risk_reduction_factor
                        self.log(f"准备趋势做多 {d_name}: MarketState={market_state}, Close={close:.2f}, EntryRef={entry_price:.2f}, Risk/Share={risk_per_share:.2f}, TotalRiskAllowed={amount_to_risk_for_trade:.2f}")

                # 区间交易逻辑
                # elif market_state == 'RANGE_LOW_POTENTIAL_BUY' and self.p.etf_type == 'range':
                elif market_state == 'RANGE_LOW_POTENTIAL_BUY': # 简化：市场处于区间底部就考虑区间做多
                     # 附加条件：例如RSI超卖，或价格突破下轨后迅速拉回
                    if rsi < self.p.rsi_oversold + 10 : # RSI接近或处于超卖区
                        potential_position_type = 'range_long'
                        entry_price = close # 或 bb_bot
                        # risk_per_share 的计算要小心，止损位是 entry_price * (1 - buffer) 或 bb_bot * (1-buffer)
                        # 假设止损在买入价下方一定百分比
                        range_sl_price = entry_price * (1 - self.p.range_stop_loss_buffer)
                        risk_per_share = entry_price - range_sl_price
                        amount_to_risk_for_trade = self.broker.getvalue() * self.p.range_risk_percentage * self.risk_reduction_factor
                        self.log(f"准备区间做多 {d_name}: MarketState={market_state}, Close={close:.2f}, EntryRef={entry_price:.2f}, Risk/Share={risk_per_share:.2f}, TotalRiskAllowed={amount_to_risk_for_trade:.2f}, RangeSLPrice={range_sl_price:.2f}")

                # 可以在这里加入做空逻辑 (range_short, trend_short)，如果策略需要

                # 如果确定了潜在交易类型，则准备下单
                if potential_position_type and entry_price and risk_per_share and amount_to_risk_for_trade:
                    if risk_per_share <= 1e-9: # 避免除以零或过小的数
                        self.log(f"警告: {d_name} 的 risk_per_share过小 ({risk_per_share:.4f})，无法计算仓位，跳过此次开仓。")
                        continue
                    if amount_to_risk_for_trade <= 1e-9:
                        self.log(f"警告: {d_name} 的 amount_to_risk_for_trade过小 ({amount_to_risk_for_trade:.4f})，无法计算仓位，跳过此次开仓。")
                        continue

                    self.log(f"为 {d_name} 准备交易信息: Type={potential_position_type}, Entry={entry_price:.2f}, Risk/Share={risk_per_share:.2f}, AmountToRisk={amount_to_risk_for_trade:.2f}")
                    self.pending_trade_info[d_name] = {
                        'entry_price': entry_price, # 理论入场价（Sizer可能用于计算价值）
                        'risk_per_share': risk_per_share, # 每股最大可接受亏损
                        'amount_to_risk': amount_to_risk_for_trade, # 本次交易总风险敞口
                        'order_type': 'buy' # 'buy' or 'sell'
                    }
                    
                    # 调用 Sizer 获取理论仓位大小
                    # 注意：Backtrader的Sizer在buy/sell调用时自动运行。
                    # 我们这里是“预计算”或“准备信息给Sizer”。
                    # 实际的 buy 调用会触发 Sizer。
                    # 假设我们用市价单，Sizer会根据当前可用现金和设置的参数决定最终股数。
                    
                    # 更新策略状态，准备买入
                    self.position_types[d_name] = potential_position_type # 重要：在下单前设置
                    # buy_price 会在 notify_order 中订单执行后设置
                    
                    # 执行买入操作，Sizer 会在这里起作用
                    # self.buy(data=d, exectype=bt.Order.Market) # 使用市价单
                    # 为了让Sizer能用上我们算好的 entry_price (如果Sizer的设计需要它)
                    # 我们可以考虑限价单，或者Sizer内部逻辑能获取这些信息
                    # 假设我们的Sizer的_getsizing能通过 self.strategy.pending_trade_info 获取这些
                    
                    # 使用市价单触发Sizer
                    buy_order = self.buy(data=d, exectype=bt.Order.Market)
                    if buy_order:
                        self.orders[d_name] = buy_order # 存储活动订单
                        # 将订单ref关联到pending_trade_info，以便订单失败时清理
                        self.pending_trade_info[d_name]['order_ref'] = buy_order.ref 
                        self.log(f"已为 {d_name} 发出 {potential_position_type} 买入市价单, Ref: {buy_order.ref}. Sizer将决定具体股数。")
                    else:
                        # 买单未能创建（例如现金不足，Sizer返回0等）
                        self.log(f"为 {d_name} 创建 {potential_position_type} 买入市价单失败。可能是Sizer返回0或其他原因。")
                        self.position_types[d_name] = None # 重置，因为没有成功下单
                        if d_name in self.pending_trade_info: # 清理未成功的交易信息
                            del self.pending_trade_info[d_name]
                    continue # 处理完一个数据源的开仓就到下一个数据源或下一个bar

    def stop(self):
        self.log('策略结束. 最终组合价值: %.2f' % self.broker.getvalue(), doprint=True)
        self.log(f'总趋势交易次数: {self.trend_trade_count}', doprint=True)
        self.log(f'总区间交易次数: {self.range_trade_count}', doprint=True)

        # 将自定义统计信息放入分析器的结果中
        # 假设我们添加的OptAShareETFStrategyReturn分析器实例名为'opt_ashare_etf_strategy_return'
        # 在Cerebro中添加分析器时，我们会这样： cerebro.addanalyzer(OptAShareETFStrategyReturn, _name='opt_ashare_etf_strategy_return')
        # 那么这里就可以通过 self.analyzers.opt_ashare_etf_strategy_return.rets 来访问
        
        # 对于参数优化，OptReturn (或其子类) 会自动收集 self.analyzers.[analyzer_name].rets
        # 所以我们只需要确保这些值被放进去。
        # OptReturn 的 rets 是一个字典，我们可以在这里添加键值对。

        # 检查分析器是否存在，以避免在非优化运行时出错
        if hasattr(self.analyzers, 'opt_ashare_etf_strategy_return'):
            self.analyzers.opt_ashare_etf_strategy_return.rets['trend_trade_count'] = self.trend_trade_count
            self.analyzers.opt_ashare_etf_strategy_return.rets['range_trade_count'] = self.range_trade_count
            self.log("已将趋势和区间交易次数添加到优化分析结果中。", doprint=True)
        
        # 如果直接使用 OptReturn，并且实例名为 optreturn (默认)
        if hasattr(self.analyzers, 'optreturn'):
            if 'trend_trade_count' not in self.analyzers.optreturn.rets: # 避免覆盖
                 self.analyzers.optreturn.rets['trend_trade_count'] = self.trend_trade_count
            if 'range_trade_count' not in self.analyzers.optreturn.rets:
                 self.analyzers.optreturn.rets['range_trade_count'] = self.range_trade_count
            self.log("已将趋势和区间交易次数添加到默认 OptReturn 分析结果中 (如果存在且未被占用)。", doprint=True)


# 自定义Sizer
class AShareETFSizer(bt.Sizer):
    params = (
        ('initial_cash_per_etf_default', 100000), # 如果策略没提供，则使用此默认值
        ('max_etf_percentage_of_equity', 0.3), # 单个ETF最大持仓市值占总权益的百分比
        ('min_size', 100), # 最小交易单位（A股通常是100股）
        ('portfolio_target_etf_count', 3), # 投资组合中期望的目标ETF数量 (用于调整单个ETF的风险分配)
        ('printlog', True),
    )

    def __init__(self):
        if self.p.printlog:
            print(f"AShareETFSizer initialized with: max_etf_percentage_of_equity={self.p.max_etf_percentage_of_equity*100:.2f}%, "
                  f"min_size={self.p.min_size}, portfolio_target_etf_count={self.p.portfolio_target_etf_count}")

    def _getsizing(self, comminfo, cash, data, isbuy):
        d_name = data._name
        if self.p.printlog:
            print(f"\n--- Sizer _getsizing for {d_name} ---")
            print(f"  Date: {data.datetime.date(0)}")
            print(f"  IsBuy: {isbuy}, Cash: {cash:.2f}, Position: {self.broker.getposition(data).size}")

        if not isbuy:
            # 如果是卖出操作，通常返回0，因为卖出数量由 self.close() 或 self.sell() 调用时指定
            # 或者如果Sizer要控制部分平仓，则需要不同逻辑
            if self.p.printlog: print(f"  Action: Not a buy order. Returning 0 shares (sell all).")
            return 0 # 表示卖出当前持仓的全部 (如果 self.close() 被调用)

        if self.broker.getposition(data).size != 0:
            if self.p.printlog: print(f"  Action: Already have a position in {d_name}. Returning 0 shares.")
            return 0 # 已有持仓，不再买入 (简单策略，避免加仓)


        # 从策略获取为本次交易计算的特定风险参数
        # 这些信息应该在策略的 next 方法中，在调用 buy() 之前，准备好并存储在策略实例中
        # 例如: self.strategy.pending_trade_info[d_name]
        
        if not hasattr(self.strategy, 'pending_trade_info') or d_name not in self.strategy.pending_trade_info:
            if self.p.printlog: print(f"  Error: No pending_trade_info found in strategy for {d_name}. Returning 0 shares.")
            return 0
        
        trade_info = self.strategy.pending_trade_info[d_name]
        
        entry_price_ref = trade_info.get('entry_price') # 策略提供的参考入场价
        risk_per_share = trade_info.get('risk_per_share') # 策略计算的每股风险
        amount_to_risk_for_this_trade = trade_info.get('amount_to_risk') # 策略决定的本次交易总风险金额

        if self.p.printlog:
            print(f"  Strategy's trade_info for {d_name}: EntryPriceRef={entry_price_ref}, RiskPerShare={risk_per_share}, AmountToRiskThisTrade={amount_to_risk_for_this_trade}")

        if not all([entry_price_ref, risk_per_share, amount_to_risk_for_this_trade]):
            if self.p.printlog: print(f"  Error: Incomplete trade_info from strategy for {d_name}. Returning 0 shares.")
            if d_name in self.strategy.pending_trade_info: del self.strategy.pending_trade_info[d_name] # 清理无效信息
            return 0

        if risk_per_share <= 1e-9: # 避免除以零或极小数
            if self.p.printlog: print(f"  Error: risk_per_share is too small ({risk_per_share:.4f}) for {d_name}. Returning 0 shares.")
            if d_name in self.strategy.pending_trade_info: del self.strategy.pending_trade_info[d_name]
            return 0
        
        if amount_to_risk_for_this_trade <= 1e-9:
             if self.p.printlog: print(f"  Error: amount_to_risk_for_this_trade is too small ({amount_to_risk_for_this_trade:.4f}) for {d_name}. Returning 0 shares.")
             if d_name in self.strategy.pending_trade_info: del self.strategy.pending_trade_info[d_name]
             return 0


        # 1. 基于策略提供的风险参数计算理想股数
        size_based_on_risk = int(amount_to_risk_for_this_trade / risk_per_share)
        if self.p.printlog: print(f"  Size calculation based on risk: AmountToRisk({amount_to_risk_for_this_trade:.2f}) / RiskPerShare({risk_per_share:.2f}) = {size_based_on_risk:.0f} shares (raw)")
        
        # 调整到最小交易单位的倍数 (例如100股)
        size_adj_for_min_unit = int(size_based_on_risk / self.p.min_size) * self.p.min_size
        if self.p.printlog: print(f"  Size adjusted to min_unit ({self.p.min_size}): {size_adj_for_min_unit:.0f} shares")

        if size_adj_for_min_unit <= 0:
            if self.p.printlog: print(f"  Calculated size after risk and min_unit adjustment is <=0 for {d_name}. Returning 0 shares.")
            if d_name in self.strategy.pending_trade_info: del self.strategy.pending_trade_info[d_name]
            return 0
        
        size = size_adj_for_min_unit


        # 2. 应用Sizer本身的全局限制
        current_equity = self.broker.getvalue() # 当前账户总权益
        
        # 限制1: 单个ETF持仓市值不能超过总权益的一定百分比
        max_pos_value_for_etf = current_equity * self.p.max_etf_percentage_of_equity
        
        # 使用策略提供的参考入场价，如果无效，则使用当前市场价
        price_for_value_calc = entry_price_ref
        if not price_for_value_calc or price_for_value_calc <= 1e-9 :
            price_for_value_calc = data.close[0] # Fallback to current close if entry_price_ref is bad
            if self.p.printlog: print(f"  Warning: Invalid entry_price_ref from strategy, using current close {price_for_value_calc:.2f} for value calculation.")

        if price_for_value_calc <= 1e-9: # 如果价格还是无效
            if self.p.printlog: print(f"  Error: Price for value calculation is invalid ({price_for_value_calc:.2f}) for {d_name}. Returning 0 shares.")
            if d_name in self.strategy.pending_trade_info: del self.strategy.pending_trade_info[d_name]
            return 0

        size_limited_by_max_etf_pos = int(max_pos_value_for_etf / price_for_value_calc)
        size_limited_by_max_etf_pos = int(size_limited_by_max_etf_pos / self.p.min_size) * self.p.min_size # 调整到100的倍数
        
        if self.p.printlog:
            print(f"  Max position value for one ETF: CurrentEquity({current_equity:.2f}) * MaxPerc({self.p.max_etf_percentage_of_equity:.2f}) = {max_pos_value_for_etf:.2f}")
            print(f"  Size limited by max ETF percentage: MaxValue({max_pos_value_for_etf:.2f}) / Price({price_for_value_calc:.2f}) = {size_limited_by_max_etf_pos:.0f} shares")

        if size > size_limited_by_max_etf_pos:
            if self.p.printlog: print(f"  Size ({size:.0f}) exceeds max ETF percentage limit ({size_limited_by_max_etf_pos:.0f}). Reducing size.")
            size = size_limited_by_max_etf_pos


        # 限制2: 购买所需现金不能超过可用现金 (乘以一个安全边际，例如95%)
        required_cash = size * price_for_value_calc # 使用参考价估算所需现金
        # comminfo.getvaluesize(size, price_for_value_calc) 可以获取更精确的包含手续费的价值
        # 为了简化，我们直接用 size * price
        
        available_cash_for_trade = cash * 0.98 # 保留一点余地
        if self.p.printlog: print(f"  Required cash for {size:.0f} shares at {price_for_value_calc:.2f} = {required_cash:.2f}. Available cash for trade (98% of total cash {cash:.2f}) = {available_cash_for_trade:.2f}")

        if required_cash > available_cash_for_trade:
            new_size_due_to_cash = int(available_cash_for_trade / price_for_value_calc)
            new_size_due_to_cash = int(new_size_due_to_cash / self.p.min_size) * self.p.min_size
            if self.p.printlog: print(f"  Required cash exceeds available. Reducing size from {size:.0f} to {new_size_due_to_cash:.0f} based on available cash.")
            size = new_size_due_to_cash

        if size < self.p.min_size: # 如果最终计算出来的股数小于最小交易单位
            if self.p.printlog: print(f"  Final size ({size:.0f}) is less than min_size ({self.p.min_size}). Returning 0 shares.")
            if d_name in self.strategy.pending_trade_info: del self.strategy.pending_trade_info[d_name] # 清理
            return 0
        
        if self.p.printlog: print(f"  Final calculated size for {d_name}: {size:.0f} shares.")
        print(f"--- End Sizer _getsizing for {d_name} ---\n")

        # 清理本次交易的pending_trade_info，因为它已经被Sizer处理了
        # 这个清理应该在订单成功创建后进行，或者在这里标记为已处理
        # 但更稳妥的是在 order notification 中根据订单状态清理
        # 这里我们假设，如果返回非0，则pending_trade_info的信息被认为已使用
        # 策略的notify_order会在订单失败时清理它。
        # 如果订单成功，sizer返回股数，策略的notify_trade在交易关闭时清理更合适。
        # 暂时不在sizer中主动删除 pending_trade_info，除非计算出的size为0。

        # if size > 0 and d_name in self.strategy.pending_trade_info:
        #     del self.strategy.pending_trade_info[d_name] # 如果sizer决定了股数，就认为这个信息用掉了

        return size


# --- 数据加载和处理 ---
def load_stock_data(file_path, stock_name):
    df = pd.read_csv(file_path)
    df['datetime'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    df.set_index('datetime', inplace=True)
    df.rename(columns={
        'open_price': 'open',
        'high_price': 'high',
        'low_price': 'low',
        'close_price': 'close',
        'volume_td': 'volume', # 成交量(万股)
        'amount_td': 'turnover' # 成交额(万元)
    }, inplace=True)
    df['openinterest'] = 0 # Backtrader需要这个字段，对于股票设为0
    
    # 选择需要的列，并确保顺序符合Backtrader要求
    df = df[['open', 'high', 'low', 'close', 'volume', 'openinterest', 'turnover']]
    # df = df.astype(float) # 确保数据类型正确
    return bt.feeds.PandasData(dataname=df, name=stock_name)


# --- 打印优化结果 ---
def print_optimization_results(results):
    """
    打印参数优化的结果。
    results 是一个列表，每个元素是一个 StrategyAnalyzer 实例列表。
    每个 StrategyAnalyzer 对应一个参数组合的运行。
    StrategyAnalyzer.params 是参数字典。
    StrategyAnalyzer.analyzers[0].rets 是该参数组合下的分析结果字典。
    """
    print("\n===================== 参数优化结果 =====================")
    res_dicts = []
    for res_set in results: # results是列表的列表，每个内部列表是单个cerebro.run()的结果
        for res in res_set: # res是单个参数组合的运行结果 (OptReturn的实例)
            params_dict = res.params._asdict() # 获取参数
            
            # 获取分析结果，假设第一个分析器是 OptAShareETFStrategyReturn (或包含所有我们需要数据的分析器)
            # 并且它返回一个包含 'sharpe_ratio', 'total_return', 'max_drawdown', 'score' 的字典
            # 以及我们新加的 'trend_trade_count', 'range_trade_count'
            analysis_dict = {}
            if hasattr(res.analyzers[0], 'rets') and res.analyzers[0].rets: # 确保rets存在且不为空
                analysis_dict = res.analyzers[0].rets 
            
            row = {}
            row.update(params_dict) # 合并参数
            
            # 添加核心分析指标
            row['夏普比率'] = analysis_dict.get('sharpe_ratio', float('nan'))
            row['总收益率'] = analysis_dict.get('total_return', float('nan')) * 100 # 转为百分比
            row['最大回撤'] = analysis_dict.get('max_drawdown', float('nan')) * 100 # 转为百分比
            row['得分'] = analysis_dict.get('score', float('nan')) # 'score'是我们在 OptAShareETFStrategyReturn 中计算的

            # 添加交易类型计数
            row['趋势交易次数'] = analysis_dict.get('trend_trade_count', 0)
            row['区间交易次数'] = analysis_dict.get('range_trade_count', 0)

            res_dicts.append(row)

    if not res_dicts:
        print("没有找到优化结果。")
        return

    # 将结果转换为DataFrame方便排序和显示
    df_results = pd.DataFrame(res_dicts)
    
    # 根据“得分”降序排序
    df_sorted = df_results.sort_values(by='得分', ascending=False)
    
    # 选择要显示的列，并调整顺序
    # 动态获取所有参数名作为列
    param_names = list(results[0][0].params._asdict().keys())
    display_columns = param_names + ['夏普比率', '总收益率', '最大回撤', '趋势交易次数', '区间交易次数', '得分']
    
    # 确保所有列都存在于df_sorted中，如果某个参数组合没有某个指标（例如全亏返回NaN），fillna处理
    for col in display_columns:
        if col not in df_sorted.columns:
            df_sorted[col] = float('nan') 
            
    df_display = df_sorted[display_columns].copy() # 使用 .copy() 避免 SettingWithCopyWarning

    # 格式化浮点数列
    float_format_cols = ['夏普比率', '总收益率', '最大回撤', '得分']
    for col_name in float_format_cols:
        if col_name in df_display.columns:
             # 检查是否为数值类型，以避免对非数值类型（如对象类型列中的NaN字符串）使用.map
            if pd.api.types.is_numeric_dtype(df_display[col_name]):
                df_display.loc[:, col_name] = df_display[col_name].map(lambda x: f'{x:.4f}' if pd.notnull(x) else 'N/A')
            else:
                # 如果已经是字符串或者包含非数值，尝试转换为数值，失败则保持原样或标记为N/A
                try:
                    df_display.loc[:, col_name] = pd.to_numeric(df_display[col_name], errors='coerce').map(lambda x: f'{x:.4f}' if pd.notnull(x) else 'N/A')
                except Exception:
                    df_display.loc[:, col_name] = 'N/A'


    print(tabulate(df_display.head(15), headers='keys', tablefmt='grid', showindex=False))

    if not df_display.empty:
        best_params_series = df_display.iloc[0]
        print("\n===================== 最优参数组合 =====================")
        for param_name, value in best_params_series.items():
            readable_name = param_name.replace('_', ' ').title() # 将参数名变得更易读
            # 特殊处理百分比参数的显示
            if param_name in ['trend_risk_percentage', 'range_risk_percentage', 'max_drawdown_limit_1', 'max_drawdown_limit_2', 'range_stop_loss_buffer']:
                # 假设参数值是小数形式 (如 0.01 代表 1%)
                # 在优化时，参数本身应该是数值。这里的 best_params_series 可能已经是格式化后的字符串。
                # 我们需要从原始的 df_sorted 中获取数值进行转换。
                original_value = df_sorted.iloc[0][param_name]
                if pd.notnull(original_value) and isinstance(original_value, (float, int)):
                    print(f"{readable_name: <30}: {original_value*100:.2f}% (原始值: {original_value})")
                else:
                    print(f"{readable_name: <30}: {value}") # 如果不是预期的数值，直接打印
            elif param_name in ['总收益率', '最大回撤']: # 这些已经是格式化后的字符串，带百分号
                 print(f"{readable_name: <30}: {value}")
            else:
                print(f"{readable_name: <30}: {value}")
        return df_sorted.iloc[0].to_dict() # 返回最优参数字典
    return None


if __name__ == '__main__':
    cerebro = bt.Cerebro(optreturn=False) # optreturn=False 因为我们用了 optstrategy

    # --- 数据准备 ---
    data_files = {
        "510050_d": r"D:\dev\code\BT2026\datas\daily\510050_ashare_etf_daily_qfq.csv",
        "510300_d": r"D:\dev\code\BT2026\datas\daily\510300_ashare_etf_daily_qfq.csv",
        "510500_d": r"D:\dev\code\BT2026\datas\daily\510500_ashare_etf_daily_qfq.csv",
        # "159915_d": r"D:\dev\code\BT2026\datas\daily\159915_ashare_etf_daily_qfq.csv"
    }
    
    # 定义回测时间范围
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2024, 1, 1)

    for name, path in data_files.items():
        data_feed = load_stock_data(path, name)
        cerebro.adddata(data_feed, name=name) # 为每个数据源指定名称
        print(f"已加载数据: {name} from {path}")

    # --- 策略和Sizer ---
    # cerebro.addstrategy(AShareETFStrategy, printlog=False) # 单次运行时打开printlog
    # cerebro.addsizer(AShareETFSizer, printlog=False) # 单次运行时打开printlog

    # --- 优化设置 ---
    # 参数空间定义
    opt_params = {
        'ema_short_period': range(10, 31, 10), # 10, 20, 30
        'ema_medium_period': range(40, 61, 10), # 40, 50, 60
        'ema_long_period': range(80, 121, 20), # 80, 100, 120
        'bbands_period': range(15, 26, 5), # 15, 20, 25
        'bbands_devfactor': [1.8, 2.0, 2.2],
        'atr_period': [10, 14, 20],
        'trend_stop_loss_atr_multiplier': [1.5, 2.0, 2.5],
        'range_stop_loss_buffer': [0.005, 0.008, 0.01],
        'trend_risk_percentage': [0.01, 0.015], # 1%, 1.5%
        'range_risk_percentage': [0.005, 0.008], # 0.5%, 0.8%
        # 'etf_type': ['trend', 'range'], # 这个参数对于多数据源动态判断市场状态的策略意义不大，除非特定设计
        'adx_threshold': [20, 25, 30],
        'printlog': [False] # 优化时关闭日志以提高速度
    }
    cerebro.optstrategy(AShareETFStrategy, **opt_params)
    cerebro.addsizer(AShareETFSizer, printlog=False)


    # --- 账户和手续费 ---
    cerebro.broker.setcash(300000.0) # 总初始资金
    cerebro.broker.setcommission(commission=0.0003, margin=None, mult=1.0) # 设置手续费

    # --- 分析器 ---
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio', timeframe=bt.TimeFrame.Days, compression=1, factor=252, annualize=True)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='total_return', timeframe=bt.TimeFrame.NoTimeFrame) # 总收益用NoTimeFrame
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='max_drawdown')
    
    # 添加我们自定义的（或直接用OptReturn的）分析器来收集优化结果
    # OptReturn 会自动收集所有其他分析器的结果，并与参数结合。
    # 如果我们用了 optstrategy, Cerebro会自动处理OptReturn。
    # 我们需要确保 OptAShareETFStrategyReturn (如果用它) 或者策略的 stop 方法能正确填充结果。
    # 我们在策略的stop中直接填充了 self.analyzers.opt_ashare_etf_strategy_return.rets
    # cerebro.addanalyzer(OptAShareETFStrategyReturn, _name='opt_ashare_etf_strategy_return')
    # 或者，如果直接用Backtrader内置的OptReturn (由optstrategy隐式添加)，
    # 那么策略的stop方法应该写入 self.analyzers.optreturn.rets
    
    # 为了确保我们的自定义计数器被收集，我们还是显式添加我们修改过的分析器
    # 关键是：这个分析器的 _name 必须和策略 stop 方法中引用的名称一致。
    # cerebro.run() 在优化模式下，会为每个参数组合创建一个 Cerebro 实例的副本，
    # 并在其上运行策略。每个副本中的策略实例会访问其自身的 analyzers 集合。
    # OptReturn (由 cerebro.optstrategy 内部管理) 会收集每个策略实例的 self.analyzers.myanalyzername.rets。

    # 由于 optstrategy 会自动添加一个 OptReturn 分析器 (通常名为 'optreturn')
    # 并且策略的 stop 方法中已经有逻辑尝试写入 self.analyzers.optreturn.rets
    # 和 self.analyzers.opt_ashare_etf_strategy_return.rets
    # 我们只需要确保其中一个能被 OptReturn 机制捕获。
    # Backtrader 的 optstrategy 默认会寻找名为 'optreturn' 的 OptReturn 分析器实例。
    # 如果我们不显式添加，它会自己创建一个。
    # 如果我们显式添加一个 OptReturn 或其子类的实例，需要确保 optstrategy 能识别它。
    # 最简单的方式是依赖 optstrategy 自动创建的 'optreturn'，并在策略的 stop 方法中
    # 将自定义结果写入 self.analyzers.optreturn.rets。

    # 为了让 print_optimization_results 函数中的 res.analyzers[0].rets 正确工作，
    # 我们需要确保第一个分析器（或包含所有所需数据的那个）是我们想要的。
    # 当使用 optstrategy 时，它生成的 OptReturn 实例会聚合其他分析器的结果。
    # 所以，我们只要确保 Sharpe, Returns, DrawDown 被添加，
    # 并且策略的 stop 方法将 trend/range counts 添加到某个可被 OptReturn 访问的 rets 字典中。

    # 为了与 print_optimization_results 的假设 (res.analyzers[0].rets) 兼容，
    # 并且考虑到 optstrategy 的工作方式，我们让 OptReturn 成为主要的收集者。
    # 我们不需要显式添加 OptAShareETFStrategyReturn，
    # 只要策略的 stop 方法能把 trend_trade_count 和 range_trade_count
    # 放到一个能被 OptReturn 收集的地方即可。
    # 在策略的 stop 方法中，我们有：
    # if hasattr(self.analyzers, 'optreturn'):
    #     self.analyzers.optreturn.rets['trend_trade_count'] = self.trend_trade_count
    #     self.analyzers.optreturn.rets['range_trade_count'] = self.range_trade_count

    # 这样，当 optstrategy 运行时，它创建的 OptReturn 实例 (名为 'optreturn')
    # 会在其 rets 字典中包含 'sharpe_ratio', 'total_return', 'max_drawdown' (来自其他分析器)
    # 以及我们手动添加的 'trend_trade_count' 和 'range_trade_count'。
    # print_optimization_results 就能通过 res.analyzers.optreturn.rets (或者 res.analyzers[0].rets 如果optreturn是第一个) 来获取。
    # 通常，optstrategy 添加的 OptReturn 实例是 analyzers 列表中的第一个。

    # --- 运行优化 ---
    print("开始参数优化...")
    # cerebro.optreaders(False) # 优化时不读取数据，除非数据依赖于参数
    # cerebro.optdatas(False) # 优化时不重新加载数据
    
    # 运行优化。maxcpus=None 会尝试使用所有可用核心，可以设置为1进行单核调试。
    optimized_runs = cerebro.run(maxcpus=1) #  maxcpus=None for all cores, 1 for single core (easier debugging)
    print("参数优化完成.")

    # --- 打印结果 ---
    best_params_dict = print_optimization_results(optimized_runs)

    if best_params_dict:
        print("\n===================== 使用最优参数进行回测 =====================")
        # 从最优参数字典中移除分析器返回的指标，只保留策略参数
        final_run_params = {k: v for k, v in best_params_dict.items() if k in opt_params or k == 'printlog'}
        final_run_params['printlog'] = True # 在最终回测时打开日志

        cerebro_final = bt.Cerebro()
        for name, path in data_files.items():
            data_feed = load_stock_data(path, name)
            cerebro_final.adddata(data_feed, name=name)

        cerebro_final.addstrategy(AShareETFStrategy, **final_run_params)
        cerebro_final.addsizer(AShareETFSizer, printlog=True) # Sizer日志也打开

        cerebro_final.broker.setcash(300000.0)
        cerebro_final.broker.setcommission(commission=0.0003)
        
        # 为最终回测添加分析器
        cerebro_final.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio', timeframe=bt.TimeFrame.Days, compression=1, factor=252, annualize=True)
        cerebro_final.addanalyzer(bt.analyzers.Returns, _name='total_return', timeframe=bt.TimeFrame.NoTimeFrame)
        cerebro_final.addanalyzer(bt.analyzers.DrawDown, _name='max_drawdown')
        cerebro_final.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer') # 交易分析
        cerebro_final.addanalyzer(bt.analyzers.SQN, _name='sqn') # 系统质量评分
        cerebro_final.addanalyzer(bt.analyzers.Transactions, _name='transactions') # 交易记录

        results_final_run = cerebro_final.run()
        strat_final = results_final_run[0] # 获取策略实例

        print(f"\n最优参数最终回测结果:")
        print(f"  夏普比率: {strat_final.analyzers.sharpe_ratio.get_analysis()['sharperatio']:.4f}")
        print(f"  总收益率: {strat_final.analyzers.total_return.get_analysis()['rtot']*100:.2f}%")
        print(f"  最大回撤: {strat_final.analyzers.max_drawdown.get_analysis()['max']['drawdown']*100:.2f}%")
        print(f"  SQN: {strat_final.analyzers.sqn.get_analysis()['sqn']:.4f}")
        
        trade_analysis = strat_final.analyzers.trade_analyzer.get_analysis()
        print(f"  总交易次数: {trade_analysis.total.total if trade_analysis.total else 0}")
        print(f"  盈利交易次数: {trade_analysis.won.total if trade_analysis.won else 0}")
        print(f"  亏损交易次数: {trade_analysis.lost.total if trade_analysis.lost else 0}")
        print(f"  胜率: {(trade_analysis.won.total / trade_analysis.total.total * 100) if (trade_analysis.total and trade_analysis.total.total > 0) else 0:.2f}%")
        print(f"  平均盈利: {trade_analysis.won.pnl.average if (trade_analysis.won and trade_analysis.won.pnl) else 0:.2f}")
        print(f"  平均亏损: {trade_analysis.lost.pnl.average if (trade_analysis.lost and trade_analysis.lost.pnl) else 0:.2f}")
        print(f"  盈亏比: {abs(trade_analysis.won.pnl.average / trade_analysis.lost.pnl.average) if (trade_analysis.won and trade_analysis.lost and trade_analysis.lost.pnl.average != 0) else 'N/A'}")
        
        print(f"  本次运行趋势交易次数: {strat_final.trend_trade_count}")
        print(f"  本次运行区间交易次数: {strat_final.range_trade_count}")

        # cerebro_final.plot(style='candlestick', barup='red', bardown='green')
        # cerebro_final.plot(iplot=True, style='candlestick', barup='red', bardown='green')

    else:
        print("未能从优化中找到最优参数。")

    print("--- 主程序结束 ---")
