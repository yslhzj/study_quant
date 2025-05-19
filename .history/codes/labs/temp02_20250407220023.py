import backtrader as bt
# 导入 backtrader 库，并将其简写为 bt，方便后续调用。
# (就像给一个很长的名字取个小名，方便叫唤。)
import datetime
# 导入 datetime 库，用于处理日期和时间。
# (就像导入一个日历和时钟工具。)
import math
# 导入 math 库，用于进行数学计算，例如开方、取整等。
# (就像导入一个计算器。)

class AShareETFStrategy(bt.Strategy):
    # 定义一个名为 AShareETFStrategy 的策略类，它继承自 backtrader 的 Strategy 类。
    # (就像创建一个新的游戏角色，这个角色天生就具备一些基础的交易能力。)
    params = (
        # 定义策略的参数，这些参数可以在之后调整以优化策略表现。
        # (就像给游戏角色设定初始属性，比如力量、敏捷度，这些属性可以调整。)
        ('etf_type', 'trend'),
        # 定义ETF类型参数，'trend'表示趋势型，'range'表示震荡型。
        # (设定这个ETF适合玩"追涨杀跌"还是"高抛低吸"。)
        ('ema_medium_period', 60),
        # 定义中期指数移动平均线（EMA）的计算周期为60天。
        # (设定一个观察最近60天平均价格的指标。)
        ('ema_long_period', 120),
        # 定义长期指数移动平均线（EMA）的计算周期为120天。
        # (设定一个观察最近120天平均价格的指标，比上面的看得更长远。)
        ('adx_period', 14),
        # 定义平均动向指数（ADX）的计算周期为14天。
        # (设定一个观察最近14天趋势强弱的指标。)
        ('atr_period', 20),
        # 定义平均真实波幅（ATR）的计算周期为20天。
        # (设定一个观察最近20天价格波动幅度的指标。)
        ('bbands_period', 20),
        # 定义布林带（Bollinger Bands）的计算周期为20天。
        # (设定一个观察最近20天价格通道的指标。)
        ('bbands_devfactor', 2.0),
        # 定义布林带的标准差倍数为2.0。
        # (设定布林带通道的宽度，数值越大通道越宽。)
        ('rsi_period', 14),
        # 定义相对强弱指数（RSI）的计算周期为14天。
        # (设定一个观察最近14天买卖力量对比的指标。)
        ('rsi_oversold', 30),
        # 定义RSI指标的超卖阈值为30。
        # (设定一个标准，低于30就认为可能卖得太多，价格可能反弹。)
        ('trend_breakout_lookback', 60),
        # 定义趋势突破策略回顾期为60天，用于寻找近期高点。
        # (设定在趋势策略中，要看过去60天内的最高价。)
        ('trend_volume_avg_period', 20),
        # 定义趋势策略中计算平均成交量的周期为20天。
        # (设定在趋势策略中，要看过去20天的平均交易量。)
        ('trend_volume_ratio_min', 1.1),
        # 定义趋势突破时成交量需要达到的最小倍数（相对于平均成交量）。
        # (设定突破时，交易量至少要放大到平均值的1.1倍才算数。)
        ('trend_stop_loss_atr_mult', 2.5),
        # 定义趋势策略中止损计算使用的ATR倍数。
        # (设定在趋势交易中，亏损多少（用ATR衡量）就得认赔出局。)
        ('trend_take_profit_rratio', 2.0),
        # 定义趋势策略中的盈亏比目标。
        # (设定在趋势交易中，期望赚的钱至少是亏损风险的2倍。)
        ('range_stop_loss_buffer', 0.005),
        # 定义震荡策略中止损设置在K线最低点下方的缓冲比例。
        # (设定在震荡交易中，止损线比最低价再低一点点，留个缓冲空间。)
        ('max_risk_per_trade_trend', 0.01),
        # 定义趋势策略下单笔交易允许的最大风险占总资金的比例（1%）。
        # (设定每次趋势交易最多只允许亏掉总资金的1%。)
        ('max_risk_per_trade_range', 0.005),
        # 定义震荡策略下单笔交易允许的最大风险占总资金的比例（0.5%）。
        # (设定每次震荡交易最多只允许亏掉总资金的0.5%。)
        ('max_position_per_etf_percent', 0.30),
        # 定义单个ETF允许持有的最大仓位占总资金的比例（30%）。
        # (设定单个ETF最多只能买总资金的30%。)
        ('max_total_account_risk_percent', 0.06),
        # 定义整个账户允许承担的总风险上限比例（6%）（简化版，仅考虑当前ETF）。
        # (设定整个账户最多能承受总资金6%的潜在亏损。)
        ('drawdown_level1_threshold', 0.05),
        # 定义一级回撤阈值（5%），触发时可能降低风险。
        # (设定当账户亏损达到总资金的5%时，发出黄色警报，可能要小心点。)
        ('drawdown_level2_threshold', 0.10),
        # 定义二级回撤阈值（10%），触发时可能暂停交易。
        # (设定当账户亏损达到总资金的10%时，发出红色警报，可能要停止交易。)
    )

    def log(self, txt, dt=None):
        # 定义一个日志记录函数，用于在控制台输出策略执行信息。
        # (就像写日记，记录下策略在做什么。)
        dt = dt or self.datas[0].datetime.date(0)
        # 获取当前数据点的时间戳，如果没有提供dt参数，则使用当前K线的日期。
        # (确定这条日记是哪一天写的。)
        print(f'{dt.isoformat()} {txt}')
        # 格式化输出日期和日志文本。
        # (把日期和内容打印出来，格式是"YYYY-MM-DD 内容"。)

    def __init__(self):
        # 定义策略的初始化函数，在策略开始运行时执行一次。
        # (就像游戏角色出生时，需要先设定好装备和初始状态。)
        self.dataclose = self.datas[0].close
        # 获取第一个数据源（通常是主数据）的收盘价数据线。
        # (拿到每天收盘时的价格数据。)
        self.dataopen = self.datas[0].open
        # 获取第一个数据源的开盘价数据线。
        # (拿到每天开盘时的价格数据。)
        self.datahigh = self.datas[0].high
        # 获取第一个数据源的最高价数据线。
        # (拿到每天的最高价格数据。)
        self.datalow = self.datas[0].low
        # 获取第一个数据源的最低价数据线。
        # (拿到每天的最低价格数据。)
        self.datavolume = self.datas[0].volume
        # 获取第一个数据源的成交量数据线。
        # (拿到每天的交易量数据。)

        self.ema_medium = bt.indicators.EMA(
            self.dataclose, period=self.params.ema_medium_period)
        # 计算中期指数移动平均线（EMA）。
        # (计算一个反应近期（60天）价格趋势的平均线。)
        self.ema_long = bt.indicators.EMA(
            self.dataclose, period=self.params.ema_long_period)
        # 计算长期指数移动平均线（EMA）。
        # (计算一个反应更长期（120天）价格趋势的平均线。)
        self.adx = bt.indicators.ADX(
            self.datas[0], period=self.params.adx_period)
        # 计算平均动向指数（ADX），需要传入包含HLC（高、低、收）的数据。
        # (计算一个判断当前趋势是强还是弱的指标。)
        self.atr = bt.indicators.ATR(
            self.datas[0], period=self.params.atr_period)
        # 计算平均真实波幅（ATR）。
        # (计算一个衡量近期价格波动大小的指标。)
        self.bbands = bt.indicators.BollingerBands(self.dataclose,
                                                   period=self.params.bbands_period,
                                                   devfactor=self.params.bbands_devfactor)
        # 计算布林带指标，包含上轨、中轨、下轨。
        # (计算一个价格通道，价格通常在这个通道内波动。)
        self.rsi = bt.indicators.RSI(
            self.dataclose, period=self.params.rsi_period)
        # 计算相对强弱指数（RSI）。
        # (计算一个判断当前是买方力量强还是卖方力量强的指标。)
        self.highest_high = bt.indicators.Highest(
            self.datahigh, period=self.params.trend_breakout_lookback)
        # 计算过去N期内的最高价。
        # (找出最近一段时间（60天）里的最高价格是多少。)
        self.sma_volume = bt.indicators.SMA(
            self.datavolume, period=self.params.trend_volume_avg_period)
        # 计算简单移动平均成交量。
        # (计算最近一段时间（20天）的平均交易量。)

        self.order = None
        # 初始化订单状态变量，用于跟踪当前是否有挂单。
        # (记录当前有没有正在等待成交的买卖指令。)
        self.buy_price = None
        # 初始化买入价格变量，记录上次买入的价格。
        # (记录上次买入花了多少钱。)
        self.buy_comm = None
        # 初始化买入佣金变量，记录上次买入支付的佣金。
        # (记录上次买入交了多少手续费。)
        self.stop_loss_price = None
        # 初始化止损价格变量。
        # (记录如果价格跌到多少钱就必须卖出止损。)
        self.take_profit_price = None
        # 初始化止盈价格变量。
        # (记录如果价格涨到多少钱就应该卖出获利。)
        self.position_type = None
        # 初始化持仓类型变量，记录当前持仓是基于趋势策略还是震荡策略。
        # (记录这笔交易是按"追涨杀跌"逻辑买的，还是按"高抛低吸"逻辑买的。)

        self.high_water_mark = 0
        # 初始化账户净值的历史最高点（高水位标记）。
        # (记录账户里钱最多的时候是多少。)
        self.drawdown_level1_triggered = False
        # 初始化一级回撤警报触发状态。
        # (记录是否触发了"黄色警报"。)
        self.halt_trading = False
        # 初始化交易暂停状态。
        # (记录是否因为亏损太多而暂停了交易。)
        self.current_risk_multiplier = 1.0
        # 初始化当前风险乘数，用于根据回撤调整风险敞口。
        # (记录当前的风险系数，正常是1，触发警报后可能会调低。)

    def notify_order(self, order):
        # 定义订单通知函数，当订单状态发生变化时被调用。
        # (当买卖指令的状态更新时，比如提交了、成交了、取消了，这个函数就会被叫到。)
        if order.status in [order.Submitted, order.Accepted]:
            # 检查订单状态是否为已提交或已接受。
            # (如果指令只是刚发出去或者券商收到了，暂时不用管。)
            return
            # 如果是已提交或已接受状态，则不执行任何操作，直接返回。
            # (那就先等着，不用做啥。)

        if order.status in [order.Completed]:
            # 检查订单状态是否为已完成（成交）。
            # (如果指令已经成功执行了。)
            if order.isbuy():
                # 检查这是否是一个买入订单。
                # (如果是买入成功了。)
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}')
                # 记录买入执行的日志，包括价格、总成本和佣金。
                # (记一笔日记：买入成功！成交价、总花费、手续费分别是多少。)
                self.buy_price = order.executed.price
                # 更新买入价格。
                # (把这次买入的价格记下来。)
                self.buy_comm = order.executed.comm
                # 更新买入佣金。
                # (把这次买入的手续费记下来。)
            elif order.issell():
                # 检查这是否是一个卖出订单。
                # (如果是卖出成功了。)
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}')
                # 记录卖出执行的日志，包括价格、总价值和佣金。
                # (记一笔日记：卖出成功！成交价、总收入、手续费分别是多少。)
            self.bar_executed = len(self)
            # 记录订单执行发生在第几根K线。
            # (记下这笔交易是在第几天完成的。)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # 检查订单状态是否为已取消、保证金不足或被拒绝。
            # (如果指令被取消了，或者钱不够买/卖，或者被券商拒绝了。)
            self.log(
                f'Order Canceled/Margin/Rejected: Status {order.getstatusname()}')
            # 记录订单失败的日志。
            # (记一笔日记：指令失败了！原因是啥。)

        self.order = None
        # 重置订单状态变量，表示当前没有挂单。
        # (无论成功还是失败，这个指令处理完了，把"有挂单"的标记去掉。)

    def notify_trade(self, trade):
        # 定义交易通知函数，当一笔交易关闭（平仓）时被调用。
        # (当一笔完整的买卖（从买入到卖出）结束时，这个函数会被叫到。)
        if not trade.isclosed:
            # 检查交易是否已经关闭。
            # (如果这笔交易还没结束，比如只买了还没卖。)
            return
            # 如果交易未关闭，则不执行任何操作，直接返回。
            # (那就先等着，不用做啥。)
        self.log(
            f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')
        # 记录交易的毛利润（不含佣金）和净利润（含佣金）。
        # (记一笔日记：这笔买卖结束了！毛利润多少，扣掉手续费后净赚/亏多少。)

    def notify_cashvalue(self, cash, value):
        # 定义现金和价值通知函数，通常在每个交易日结束时调用。
        # (每天收盘后，这个函数会被叫到，告诉我们现在有多少现金，总资产值多少钱。)
        self.high_water_mark = max(self.high_water_mark, value)
        # 更新账户净值的历史最高点（高水位标记）。
        # (看看现在的总资产是不是比以前任何时候都多，如果是，就更新记录。)
        drawdown = (self.high_water_mark - value) / \
            self.high_water_mark if self.high_water_mark > 0 else 0
        # 计算当前的回撤比例（从最高点下跌了多少百分比）。
        # (算一下，现在的总资产比历史最高点少了百分之多少。)

        if drawdown > self.params.drawdown_level2_threshold:
            # 检查回撤是否超过了二级阈值（例如10%）。
            # (如果亏损超过了设定的"红线"（比如10%）。)
            if not self.halt_trading:
                # 检查当前是否已经处于暂停交易状态。
                # (如果之前还没暂停交易。)
                self.log(
                    f'!!! RED ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level2_threshold*100:.0f}%. HALTING TRADING !!!')
                # 记录红色警报日志，并宣布暂停交易。
                # (赶紧记日记：红色警报！亏损太多了！暂停交易！)
                self.halt_trading = True
                # 将交易暂停状态设置为True。
                # (把"暂停交易"的开关打开。)
        elif drawdown > self.params.drawdown_level1_threshold:
            # 检查回撤是否超过了一级阈值（例如5%）。
            # (如果亏损超过了设定的"黄线"（比如5%），但还没到红线。)
            if not self.drawdown_level1_triggered:
                # 检查一级警报是否已经被触发过。
                # (如果之前还没触发过黄色警报。)
                self.log(
                    f'-- YELLOW ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level1_threshold*100:.0f}%. Reducing risk.--')
                # 记录黄色警报日志，并提示降低风险。
                # (记日记：黄色警报！亏损有点多了！要降低风险了！)
                self.drawdown_level1_triggered = True
                # 将一级回撤警报触发状态设置为True。
                # (把"触发过黄色警报"的标记设为真。)
                self.current_risk_multiplier = 0.5
                # 将风险乘数减半（例如从1.0降到0.5）。
                # (把风险系数调低一半，下次买的时候少买点。)
        else:
            # 如果回撤没有超过一级阈值（回撤恢复）。
            # (如果亏损没那么多了，低于"黄线"了。)
            if self.halt_trading:
                # 检查之前是否暂停了交易。
                # (如果之前暂停过交易。)
                self.log('--- Trading Resumed ---')
                # 记录交易恢复的日志。
                # (记日记：交易恢复了！)
                self.halt_trading = False
                # 将交易暂停状态设置为False。
                # (把"暂停交易"的开关关掉。)
            if self.drawdown_level1_triggered:
                # 检查之前是否触发过一级警报。
                # (如果之前触发过黄色警报。)
                self.log('--- Risk Level Restored ---')
                # 记录风险水平恢复的日志。
                # (记日记：风险水平恢复正常了！)
                self.drawdown_level1_triggered = False
                # 将一级回撤警报触发状态设置为False。
                # (把"触发过黄色警报"的标记设为假。)
                self.current_risk_multiplier = 1.0

                # 将风险乘数恢复到默认值（例如1.0）。
                # (把风险系数调回正常值1。)

    def _calculate_trade_size(self, entry_price, stop_loss_price, risk_per_trade_percent):
        """Helper method to calculate the position size based on risk management rules."""
        # 定义一个辅助方法来计算仓位大小，基于风险管理规则。
        # (这是一个小工具，专门用来算这次该买多少股。)
        if stop_loss_price >= entry_price:
            # 如果止损价高于或等于入场价，无法计算风险。
            # (如果止损价比入场价还高，这买卖没法做，风险无限大或负数。)
            self.log(
                f"Stop loss price {stop_loss_price:.2f} is not below entry price {entry_price:.2f}. Cannot calculate size.")
            # 记录错误日志。
            # (记个日记：止损价比入场价高，算不了买多少。)
            return 0  # 返回0表示无法购买

        risk_per_share = entry_price - stop_loss_price
        # 计算每股的风险金额。
        # (算一下如果买在当前价，跌到止损价，每股会亏多少钱。)
        if risk_per_share <= 0:
            # 防止除以零或负数风险
            # (如果每股风险算出来是0或者负数，也不对。)
            self.log(
                f"Calculated risk per share is zero or negative ({risk_per_share:.2f}). Cannot calculate size.")
            # 记录错误日志。
            # (记个日记：每股风险是0或负数，算不了买多少。)
            return 0

        effective_risk_percent = risk_per_trade_percent * self.current_risk_multiplier
        # 计算有效的单笔交易风险比例（考虑风险乘数）。
        # (根据当前风险系数调整实际承担的风险比例。)
        cash = self.broker.get_cash()
        # 获取当前账户可用现金。
        # (看看现在有多少现金可以用。)
        equity = self.broker.get_value()
        # 获取当前账户总净值。
        # (看看现在账户里总共有多少钱（包括股票市值）。)
        risk_amount = equity * effective_risk_percent
        # 计算本次交易允许承担的最大风险金额。
        # (算出这次交易最多能亏多少钱。)

        size_raw = risk_amount / risk_per_share
        # 根据风险金额和每股风险计算理论仓位大小。
        # (用总风险金额除以每股亏损，算出理论上可以买多少股。)
        size = int(size_raw / 100) * 100  # A股最小交易单位为100股
        # 将仓位大小向下取整到100的倍数（A股最小交易单位）。
        # (因为A股一般最少买100股，所以把算出来的股数向下取整到100的倍数。)

        if size <= 0:
            # 如果计算出的股数小于等于0
            # (如果算出来买不了（小于100股），那就不买了。)
            self.log(
                f"Calculated size is zero or negative ({size}). Cannot place order.")
            # 记录日志。
            # (记个日记：算出来买不了，不买了。)
            return 0

        # --- 检查最大仓位限制和现金限制 ---
        # (再检查一下，买这么多会不会超标？钱够不够？)
        max_pos_value = equity * self.params.max_position_per_etf_percent
        # 计算单个ETF允许的最大持仓市值。
        # (算出这个ETF最多能买多少钱的。)
        current_price_for_calc = self.dataclose[0]  # 使用当前收盘价进行市值和现金检查
        # (用最新的收盘价来算算钱。)

        potential_trade_value = size * current_price_for_calc
        # 计算潜在交易的总市值。
        # (算算如果按计划买这么多股，总共值多少钱。)

        if potential_trade_value > max_pos_value:
            # 如果计算出的仓位市值超过了允许的最大值。
            # (如果算出来要买的金额超过了单个ETF的上限。)
            size = int(max_pos_value / current_price_for_calc / 100) * 100
            # 则将仓位大小调整为允许的最大值对应的股数。
            # (那就减少买入股数，只买到上限允许的金额。)
            self.log(
                f"Size adjusted due to max position limit. New size: {size}")
            # 记录调整日志。
            # (记个日记：买太多超标了，减少到 {size} 股。)

        # Recalculate value after adjustment
        potential_trade_value = size * current_price_for_calc
        # 重新计算调整后的潜在交易市值。
        # (重新算算调整后值多少钱。)
        if potential_trade_value > cash:
            # 检查计算出的仓位所需现金是否超过了可用现金。
            # (看看算出来要买的金额是不是比现在手里的现金还多。)
            size = int(cash / current_price_for_calc / 100) * 100
            # 如果现金不足，则将仓位大小调整为可用现金能买的最大股数。
            # (如果现金不够，那就再减少买入股数，只买现金够买的部分。)
            self.log(f"Size adjusted due to cash limit. New size: {size}")
            # 记录调整日志。
            # (记个日记：现金不够买那么多了，减少到 {size} 股。)

        return size  # 返回最终计算的、经过调整的仓位大小
        # (最终决定买 {size} 股！)

    def next(self):
        # 定义next函数，每个数据点（例如每个交易日）都会被调用一次。
        # (这是策略的核心，每天开盘后都要运行一遍，决定今天该干啥。)
        if self.order:
            # 检查当前是否有挂单。
            # (如果昨天下了指令还没成交。)
            return
            # 如果有挂单，则不执行任何操作，等待订单完成。
            # (那就先等着指令结果，今天啥也别干。)

        # --- 持仓管理逻辑: 现在由 Broker 通过括号订单处理，这部分可以移除 ---
        # if self.position:
        #     # 检查当前是否持有仓位。
        #     # (如果手里已经买了还没卖。)
        #     if self.datalow[0] <= self.stop_loss_price:
        #         # 检查当日最低价是否触及或跌破止损价。
        #         # (看看今天的最低价是不是已经跌到了止损线。)
        #         self.log(
        #             f'STOP LOSS HIT: Price {self.datalow[0]:.2f} <= Stop {self.stop_loss_price:.2f}')
        #         # 记录触及止损的日志。
        #         # (记日记：触及止损了！赶紧卖！)
        #         self.order = self.sell(size=self.position.size) # Creates a new order object
        #         # 创建卖出订单，卖出所有持仓。
        #         # (下指令，把手里的全卖掉。)
        #     elif self.take_profit_price is not None and self.datahigh[0] >= self.take_profit_price:
        #         # 检查当日最高价是否触及或超过止盈价。
        #         # (看看今天的最高价是不是已经涨到了止盈线。)
        #         self.log(
        #             f'TAKE PROFIT HIT: Price {self.datahigh[0]:.2f} >= Target {self.take_profit_price:.2f}')
        #         # 记录触及止盈的日志。
        #         # (记日记：达到止盈目标了！赶紧卖！)
        #         self.order = self.sell(size=self.position.size) # Creates a new order object
        #         # 创建卖出订单，卖出所有持仓。
        #         # (下指令，把手里的全卖掉。)
        #
        #     # After placing a sell order, reset self.order to None in notify_order,
        #     # but we should return here to avoid placing new buy orders in the same bar.
        #     # However, if self.order was already set by a previous bracket component, we should not overwrite it.
        #     # The bracket order handles exits, so this entire block is removed.
        #     return # Exit next() method if already in position to only manage exits (handled by bracket now)

        # --- 开仓逻辑 ---
        # (如果现在手里没货，才考虑要不要买。)

        if self.halt_trading:
            # 检查是否处于暂停交易状态。
            # (看看是不是因为之前亏太多暂停交易了。)
            return
            # 如果处于暂停交易状态，则不执行任何操作。
            # (如果是，那今天啥也别干。)

        # 只有在没有持仓时才考虑开仓
        if not self.position:
            market_state = 'UNCERTAIN_DO_NOT_TRADE'
            # 初始化市场状态为不确定，不交易。
            # (先假设今天市场情况不明朗，最好别交易。)
            is_trend_up = (self.dataclose[0] > self.ema_medium[0] > self.ema_long[0] and
                           self.ema_medium[0] > self.ema_medium[-1] and
                           self.ema_long[0] > self.ema_long[-1])
            # 判断是否处于上升趋势：当前收盘价>中期均线>长期均线，且两条均线都在向上。
            # (判断是不是牛市：短期均线在长期均线上方，而且两条线都在往上走。)
            is_range_confirmed = (not is_trend_up and
                                  # 放宽均线走平条件
                                  abs(self.ema_medium[0] / self.ema_medium[-1] - 1) < 0.003 and
                                  # 放宽均线走平条件
                                  abs(self.ema_long[0] / self.ema_long[-1] - 1) < 0.003 and
                                  self.adx.adx[0] < 20 and
                                  (self.bbands.top[0] - self.bbands.bot[0]) / self.dataclose[0] < 0.07)  # 新增：布林带相对宽度小于7%
            # 判断是否处于震荡市：不是上升趋势，均线近似走平（允许小幅波动），ADX值较低，且布林带宽度较窄。
            # (判断是不是震荡市：不是牛市，均线稍微有点动静没事，趋势强度弱，而且最近价格波动范围不大。)

            if is_trend_up:
                # 如果判断为上升趋势。
                # (如果是牛市。)
                market_state = 'TREND_UP'
                # 将市场状态设置为上升趋势。
                # (那就标记一下，现在是上升趋势。)
            elif is_range_confirmed and self.p.etf_type == 'range':
                # 如果判断为震荡市，并且该ETF被设定为适合震荡交易。
                # (如果是震荡市，而且这个ETF适合玩"高抛低吸"。)
                market_state = 'RANGE_CONFIRMED'
                # 将市场状态设置为确认震荡。
                # (那就标记一下，现在是震荡市。)

            entry_signal = False
            # 初始化入场信号为False。
            # (先假设今天没有买入信号。)
            risk_per_trade_percent = 0
            # 初始化单笔交易风险比例。
            # (先假设风险是0。)
            # Keep this to log the type of signal maybe? Or remove if not used.
            potential_position_type = None
            # 初始化潜在持仓类型。
            # (先假设不知道要按哪种策略买。)
            stop_loss_price_calc = None
            # 初始化计算出的止损价。
            # (先假设不知道止损价是多少。)
            take_profit_price_calc = None
            # 初始化计算出的止盈价。
            # (先假设不知道止盈价是多少。)
            # Assume entry at close for calculations, bracket order might use limit/market
            entry_price_calc = self.dataclose[0]
            # 假设以收盘价入场进行计算，括号订单可能使用限价或市价

            if market_state == 'TREND_UP' and self.p.etf_type == 'trend':
                # 如果市场处于上升趋势，并且该ETF适合趋势交易。
                # (如果是上升趋势，而且这个ETF适合"追涨杀跌"。)
                is_breakout = (self.dataclose[0] > self.highest_high[-1] and
                               self.datavolume[0] > self.sma_volume[0] * self.params.trend_volume_ratio_min)
                # 判断是否为突破信号：当前收盘价创近期新高，并且成交量放大。
                # (判断是不是突破了：价格创了最近60天新高，而且交易量比平时大。)
                is_pullback = (min(abs(self.datalow[0]/self.ema_medium[0]-1), abs(self.datalow[0]/self.ema_long[0]-1)) < 0.01 and
                               self.dataclose[0] > self.dataopen[0])
                # 判断是否为回调企稳信号：当日最低价接近均线，并且当日收阳线。
                # (判断是不是回调站稳了：价格跌到均线附近，但当天又涨回来了。)

                if is_breakout or is_pullback:
                    # 如果出现突破信号或回调企稳信号。
                    # (如果突破了或者回调站稳了。)
                    entry_signal = True
                    # 设置入场信号为True。
                    # (标记：可以买了！)
                    potential_position_type = 'trend'
                    # 设置潜在持仓类型为趋势。
                    # (标记：这是按趋势策略买的。)
                    risk_per_trade_percent = self.params.max_risk_per_trade_trend
                    # 设置单笔交易风险比例为趋势策略的设定值。
                    # (标记：这次交易最多亏总资金的1%。)
                    stop_loss_price_calc = entry_price_calc - \
                        self.params.trend_stop_loss_atr_mult * self.atr[0]
                    # 使用ATR计算止损价 (基于假定入场价计算)。
                    # (根据最近的平均波动幅度，算出止损价应该设在假定入场价下方多少。)

                    # 检查止损价是否有效
                    if stop_loss_price_calc < entry_price_calc:
                        risk_per_share = entry_price_calc - stop_loss_price_calc
                        # 计算每股的风险金额。
                        # (算一下如果买在当前价，跌到止损价，每股会亏多少钱。)
                        if risk_per_share > 0:
                            take_profit_price_calc = entry_price_calc + \
                                self.params.trend_take_profit_rratio * risk_per_share
                            # 根据盈亏比计算止盈价 (基于假定入场价计算)。
                            # (根据设定的盈亏比（比如2倍），算出止盈价应该设在假定入场价上方多少。)
                        else:
                            entry_signal = False  # Should not happen if stop_loss_price_calc < entry_price_calc
                    else:
                        entry_signal = False  # Stop loss is not below entry price
                        self.log(
                            f"Trend signal skipped: Stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}")
                        # 记录跳过信号的日志。
                        # (记日记：趋势信号跳过，因为止损价不在入场价下方。)

            elif market_state == 'RANGE_CONFIRMED' and self.p.etf_type == 'range':
                # 如果市场处于震荡市，并且该ETF适合震荡交易。
                # (如果是震荡市，而且这个ETF适合"高抛低吸"。)
                is_range_buy = (self.datalow[0] <= self.bbands.bot[0] and
                                self.dataclose[0] > self.bbands.bot[0] and
                                self.rsi[0] < self.params.rsi_oversold)
                # 判断是否为震荡买入信号：价格触及或下穿布林带下轨后收回，且RSI处于超卖区。
                # (判断是不是到底了：价格碰到或跌破布林带下轨，但当天收盘又涨回来了，并且RSI显示超卖。)

                if is_range_buy:
                    # 如果出现震荡买入信号。
                    # (如果满足上面的条件。)
                    entry_signal = True
                    # 设置入场信号为True。
                    # (标记：可以买了！)
                    potential_position_type = 'range'
                    # 设置潜在持仓类型为震荡。
                    # (标记：这是按震荡策略买的。)
                    risk_per_trade_percent = self.params.max_risk_per_trade_range
                    # 设置单笔交易风险比例为震荡策略的设定值。
                    # (标记：这次交易最多亏总资金的0.5%。)
                    stop_loss_price_calc = self.datalow[0] * \
                        (1 - self.params.range_stop_loss_buffer)
                    # 计算止损价：触发信号K线的最低价下方一定比例。
                    # (把止损价设在触发信号那天最低价再低一点点的位置。)
                    take_profit_price_calc = self.bbands.mid[0]
                    # 计算止盈价：布林带中轨。
                    # (把止盈目标设在布林带的中线位置。)

                    # 检查止损价是否有效
                    if stop_loss_price_calc >= entry_price_calc:
                        entry_signal = False  # Stop loss is not below entry price
                        self.log(
                            f"Range signal skipped: Stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}")
                        # 记录跳过信号的日志。
                        # (记日记：震荡信号跳过，因为止损价不在入场价下方。)

            if entry_signal and stop_loss_price_calc is not None and entry_price_calc > stop_loss_price_calc:
                # 如果有入场信号，且成功计算出有效的止损价。
                # (如果决定要买，而且算好了有效的止损价。)

                # 调用辅助方法计算仓位大小
                # (让小工具帮忙算算买多少股。)
                size = self._calculate_trade_size(
                    entry_price_calc, stop_loss_price_calc, risk_per_trade_percent)

                if size > 0:
                    # 如果最终计算出的仓位大小大于0。
                    # (如果算了一圈下来，确实还能买 > 0 股。)
                    self.log(
                        f'CREATE BRACKET BUY ORDER, Size: {size}, StopPrice: {stop_loss_price_calc:.2f}, LimitPrice: {take_profit_price_calc if take_profit_price_calc else "N/A"}, Market State: {market_state}, Signal Type: {potential_position_type}')
                    # 记录创建买入括号订单的日志。
                    # (记日记：准备买入（括号单）！买多少股，止损价，止盈价，当前市场状态，是按哪种策略买的。)

                    # 使用 buy_bracket 创建订单
                    # 注意: buy_bracket 默认的入场订单类型是 Limit，价格是 price 参数。
                    # 如果想用市价单入场，需要设置 exectype=bt.Order.Market，并且 price 参数会被忽略。
                    # 这里我们假设希望以接近当前收盘价的价格入场，使用限价单可能更可控，但也可能无法成交。
                    # 如果希望尽快入场，可以使用市价单。我们暂时使用限价单，价格设为当前收盘价。
                    # 如果止盈价未计算出 (例如在某些趋势条件下)，则不设置止盈单 (limitexec=None)。
                    limit_exec_type = bt.Order.Limit if take_profit_price_calc is not None else None

                    bracket_orders = self.buy_bracket(
                        size=size,
                        price=entry_price_calc,  # 主订单的价格 (Limit Order)
                        # 主订单类型 (Limit) - 或改为 Market 如果想立即成交
                        exectype=bt.Order.Limit,
                        # --- 止损参数 ---
                        stopprice=stop_loss_price_calc,  # 止损触发价格
                        stopexec=bt.Order.Stop,       # 止损单类型 (触发后市价卖出)
                        # --- 止盈参数 (可选) ---
                        limitprice=take_profit_price_calc,  # 止盈触发价格
                        limitexec=limit_exec_type         # 止盈单类型 (限价卖出)
                    )
                    # buy_bracket 返回一个包含三个订单的列表：[main_order, stop_order, limit_order]
                    # 我们需要将 self.order 设置为主订单，以便策略知道有挂单
                    if bracket_orders and bracket_orders[0]:
                        self.order = bracket_orders[0]
                    # 不需要再手动保存 stop_loss_price 和 take_profit_price
                    # 也不需要保存 position_type，因为出场由括号单管理

if __name__ == '__main__':
    # Python主程序入口，确保以下代码只在直接运行此脚本时执行。
    # (这是程序的起点，只有直接运行这个文件时，下面的代码才会执行。)
    cerebro = bt.Cerebro()
    # 创建Cerebro引擎实例，它是backtrader的核心控制器。
    # (创建交易回测的大脑。)

    datapath = 'your_etf_data.csv'
    # 设置ETF数据文件的路径（需要替换为实际路径）。
    # (告诉程序你的历史数据文件放在哪里，叫什么名字。)
    data = bt.feeds.GenericCSVData(
        # 使用GenericCSVData加载CSV格式的数据。
        # (告诉程序怎么读取你那个CSV文件。)
        dataname=datapath,
        # 指定数据文件名。
        # (就是上面那个文件名。)
        fromdate=datetime.datetime(2018, 1, 1),
        # 设置回测开始日期。
        # (从哪一天开始回测。)
        todate=datetime.datetime(2023, 12, 31),
        # 设置回测结束日期。
        # (到哪一天结束回测。)
        nullvalue=0.0,
        # 指定CSV中空值的表示方式。
        # (如果文件里有空格，就当它是0。)
        dtformat=('%Y-%m-%d'),
        # 指定CSV中日期的格式。
        # (告诉程序日期是"年-月-日"这种格式。)
        datetime=0,
        # 指定日期列在CSV中的索引（第0列）。
        # (日期在第一列。)
        open=1,
        # 指定开盘价列在CSV中的索引（第1列）。
        # (开盘价在第二列。)
        high=2,
        # 指定最高价列在CSV中的索引（第2列）。
        # (最高价在第三列。)
        low=3,
        # 指定最低价列在CSV中的索引（第3列）。
        # (最低价在第四列。)
        close=4,
        # 指定收盘价列在CSV中的索引（第4列）。
        # (收盘价在第五列。)
        volume=5,
        # 指定成交量列在CSV中的索引（第5列）。
        # (成交量在第六列。)
        openinterest=-1
        # 指定未平仓量列的索引（-1表示不需要）。
        # (我们不需要未平仓量这个数据。)
    )
    cerebro.adddata(data)
    # 将加载的数据添加到Cerebro引擎中。
    # (把数据喂给大脑。)

    cerebro.addstrategy(AShareETFStrategy, etf_type='trend')
    # 将我们定义的策略类添加到Cerebro引擎，并设置etf_type参数为'trend'。
    # (告诉大脑要用哪个策略，并且设定这个ETF主要按趋势策略来跑。)

    cerebro.broker.setcash(500000.0)
    # 设置回测的初始资金。
    # (设定开始时有多少本金，比如50万。)

    cerebro.broker.setcommission(commission=0.0003, stocklike=True)
    # 设置交易佣金，commission为佣金率，stocklike=True表示按股票方式计算。
    # (设定每次买卖要交多少手续费，比如万分之三。)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio',
                        timeframe=bt.TimeFrame.Days, compression=252)
    # 添加夏普比率分析器，用于评估风险调整后的收益（年化）。
    # (添加一个分析工具，算算收益和风险的比值怎么样。)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # 添加回撤分析器，用于计算最大回撤等指标。
    # (添加一个分析工具，算算最多亏了多少钱。)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    # 添加交易分析器，用于统计交易次数、胜率、盈亏等。
    # (添加一个分析工具，统计总共交易了多少次，赢了多少次，亏了多少次。)
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    # 添加系统质量数（SQN）分析器。
    # (添加一个分析工具，评估整个交易系统的好坏。)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    # 添加回报率分析器。
    # (添加一个分析工具，算算总收益率。)

    # --- 添加 Observers ---
    # (添加观察工具，让图表更好看、信息更全)
    cerebro.addobserver(bt.observers.Broker)  # 显示现金和组合价值
    # (在图下方显示账户钱和总资产的变化)
    cerebro.addobserver(bt.observers.Trades)  # 在图表上标记交易盈利/亏损区间
    # (在K线上标记每次买卖是赚了还是亏了)
    cerebro.addobserver(bt.observers.BuySell)  # 在图表上用箭头标记买卖点
    # (在K线上用红绿箭头标出具体买入和卖出的点位)
    cerebro.addobserver(bt.observers.DrawDown)  # 在图下方绘制回撤曲线
    # (在图下方单独画出账户亏损比例的变化曲线)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 打印初始投资组合价值。
    # (在开始回测前，打印一下初始有多少钱。)
    results = cerebro.run()
    # 运行回测。
    # (开始跑回测！)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 打印最终投资组合价值。
    # (回测结束后，打印一下最后还剩多少钱。)

    strat = results[0]
    # 获取回测结果中的策略实例。
    # (拿到跑完的策略结果。)
    print('\n--- Analyzers Results ---')
    # 打印分析器结果的标题。
    # (准备打印分析报告。)
    print(
        f"Sharpe Ratio: {strat.analyzers.sharpe_ratio.get_analysis()['sharperatio']:.3f}")
    # 打印年化夏普比率。
    # (打印夏普比率是多少。)
    print(
        f"Max Drawdown: {strat.analyzers.drawdown.get_analysis()['max']['drawdown']:.2f}%")
    # 打印最大回撤百分比。
    # (打印最大亏损比例是多少。)
    print(f"SQN: {strat.analyzers.sqn.get_analysis()['sqn']:.2f}")
    # 打印系统质量数（SQN）。
    # (打印SQN值是多少。)

    trade_analysis = strat.analyzers.trade_analyzer.get_analysis()
    # 获取交易分析器的结果。
    # (拿到详细的交易统计数据。)
    if trade_analysis:
        # 如果交易分析结果存在。
        # (如果确实有交易发生。)
        print("\n--- Trade Analysis ---")
        # 打印交易分析的标题。
        # (准备打印交易统计。)
        print(f"Total Closed Trades: {trade_analysis.total.closed}")
        # 打印总平仓交易次数。
        # (打印总共完成了多少笔买卖。)
        print(f"Total Net Profit: {trade_analysis.pnl.net.total:.2f}")
        # 打印总净利润。
        # (打印总共赚了/亏了多少钱。)
        print(f"Won Trades: {trade_analysis.won.total}")
        # 打印盈利交易次数。
        # (打印赚钱的交易有多少次。)
        print(f"Lost Trades: {trade_analysis.lost.total}")
        # 打印亏损交易次数。
        # (打印亏钱的交易有多少次。)
        print(
            f"Win Rate: {trade_analysis.won.total / trade_analysis.total.closed * 100:.2f}%" if trade_analysis.total.closed else "N/A")
        # 打印胜率。
        # (打印赚钱交易次数占总次数的百分比。)
        print(
            f"Average Winning Trade: {trade_analysis.won.pnl.average:.2f}" if trade_analysis.won.total else "N/A")
        # 打印平均盈利金额。
        # (打印平均每次赚钱的交易赚了多少。)
        print(
            f"Average Losing Trade: {trade_analysis.lost.pnl.average:.2f}" if trade_analysis.lost.total else "N/A")
        # 打印平均亏损金额。
        # (打印平均每次亏钱的交易亏了多少。)
        print(
            f"Profit Factor: {abs(trade_analysis.won.pnl.total / trade_analysis.lost.pnl.total):.2f}" if trade_analysis.lost.pnl.total != 0 else "Infinite")
        # 打印盈利因子（总盈利/总亏损）。
        # (打印总盈利是总亏损的多少倍。)

    cerebro.plot(style='candlestick', barup='red', bardown='green')
    # 绘制回测结果图表，使用K线图样式，并设置红涨绿跌。
    # (把回测结果画成图表，用K线图显示，并且是国内习惯的红涨绿跌。)
