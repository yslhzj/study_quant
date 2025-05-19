import datetime
# 导入datetime模块，用于处理日期和时间
# (就像导入一个工具箱，里面有处理日期和时间的工具)
import os.path
# 导入os.path模块，用于处理文件路径
# (就像导入一个工具箱，里面有处理文件地址的工具)
import sys
# 导入sys模块，用于访问与Python解释器交互的变量和函数
# (就像导入一个工具箱，可以让你和Python程序本身进行交流)
import backtrader as bt
# 导入backtrader库，并将其别名设置为bt，这是一个用于量化交易回测的库
# (就像导入一个专门用来模拟股票买卖的软件库，并给它取个小名叫bt)
from backtrader.indicators import EMA
# 从backtrader库的indicators模块中导入EMA（指数移动平均线）指标
# (就像从bt这个软件库里，拿出一个叫EMA的计算工具，这个工具可以算一种特殊的平均价格)


class TestStrategy(bt.Strategy):
# 定义一个名为TestStrategy的类，它继承自backtrader库中的Strategy类，用于编写交易策略
# (就像创建一个新的游戏角色，这个角色是基于bt库里预设的"策略"模板来创建的，我们可以在里面设定买卖规则)
    params = (
        # 定义策略的参数，这里设置了一个名为maperiod的参数，默认值为15
        # (就像给游戏角色设置初始属性，比如力量值设为15)
        ('maperiod', 15),
        # 设置maperiod参数的值为15
        # (把角色的力量值具体设定为15)
    )

    def log(self, txt, dt=None):
        return
    # 定义一个名为log的方法（函数），用于记录策略执行过程中的信息
    # (就像给游戏角色一个日记本，可以随时记录发生的事情)
        ''' Logging function fot this strategy'''
        # 这个是函数文档字符串，简单说明了这个函数是用来记录日志的
        # (这是日记本的封面，写着"日志记录本")
        dt = dt or self.datas[0].datetime.date(0)
        # 获取当前数据点的时间，如果没有提供dt参数，则使用当前K线数据的日期
        # (记录事情时，如果没特别指定日期，就用今天的日期)
        print('%s, %s' % (dt.isoformat(), txt))
        # 打印格式化的日志信息，包含日期和传入的文本内容
        # (在日记本上写下日期和发生的事情，比如"2023-10-27，今天天气不错")
        # (在日记本上写下日期和发生的事情，比如“2023-10-27，今天天气不错”)

    @staticmethod
    # 这是一个装饰器，表示下面的percent方法是一个静态方法，不需要实例就可以调用
    # (就像一个通用工具，不需要特定角色也能使用)
    def percent(today, yesterday):
    # 定义一个静态方法percent，用于计算两个数值之间的百分比变化
    # (定义一个计算涨跌幅的公式)
        return float(today - yesterday) / today
        # 返回计算结果，即(今日值 - 昨日值) / 今日值
        # (用公式算出今天的价格相对于昨天的价格变化了多少百分比)

    def __init__(self):
    # 定义类的初始化方法，当创建TestStrategy对象时会自动执行
    # (就像角色诞生时，需要进行一些初始设定)
        self.dataclose = self.datas[0].close
        # 获取第一个数据源（通常是股票数据）的收盘价数据线
        # (拿到每天股票收盘时的价格记录)
        self.volume = self.datas[0].volume
        # 获取第一个数据源的成交量数据线
        # (拿到每天股票交易了多少股的记录)

        self.order = None
        # 初始化订单变量为None，表示当前没有挂单
        # (一开始手上没有任何买入或卖出的指令单)
        self.buyprice = None
        # 初始化买入价格变量为None
        # (还没买入，所以不知道买入价格是多少)
        self.buycomm = None
        # 初始化买入手续费变量为None
        # (还没买入，所以不知道手续费是多少)

        me1 = EMA(self.data, period=12)
        # 计算12周期的指数移动平均线（EMA）
        # (用EMA工具计算最近12天的平均价格，得到一条线，叫me1)
        me2 = EMA(self.data, period=26)
        # 计算26周期的指数移动平均线（EMA）
        # (用EMA工具计算最近26天的平均价格，得到另一条线，叫me2)
        self.macd = me1 - me2
        # 计算MACD指标的快线（DIF），即短期EMA减去长期EMA
        # (用me1线减去me2线，得到一条新的线，叫MACD快线，表示短期和长期平均价格的差距)
        self.signal = EMA(self.macd, period=9)
        # 计算MACD指标的慢线（DEA或Signal），即MACD快线的9周期EMA
        # (再用EMA工具计算MACD快线最近9天的平均值，得到又一条线，叫MACD慢线)

        bt.indicators.MACDHisto(self.data)
        # 计算并添加MACD柱状图（MACD Histogram）指标，它等于MACD快线减去MACD慢线
        # (计算快线和慢线之间的差距，画成柱子图，方便看两条线的距离)

    def notify_order(self, order):
    # 定义订单通知方法，当订单状态发生变化时会被调用
    # (就像一个订单状态更新的提醒器，比如下单了、成交了、取消了都会通知你)
        if order.status in [order.Submitted, order.Accepted]:
        # 如果订单状态是已提交（Submitted）或已接受（Accepted），则不执行任何操作，直接返回
        # (如果订单只是刚提交或者交易所刚收到，暂时不用管，等等看结果)
            return
            # 结束当前函数的执行
            # (好的，知道了，先不处理)
        if order.status in [order.Completed]:
        # 如果订单状态是已完成（Completed），表示订单已成交
        # (如果订单成功买入或卖出了)
            if order.isbuy():
            # 判断这个已完成的订单是不是买入订单
            # (看看是买入成功了，还是卖出成功了？如果是买入...)
                self.log(
                # 调用log方法记录买入执行信息
                # (在日记本上记下：买入成功！)
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    # 记录买入的成交价格、总花费和手续费
                    # (写清楚买入的价格是多少，一共花了多少钱，手续费是多少)
                    (order.executed.price,
                     # 获取订单执行后的成交价格
                     # (这是成交的价格)
                     order.executed.value,
                     # 获取订单执行后的总价值（成交价格 * 数量）
                     # (这是成交的总金额)
                     order.executed.comm))
                     # 获取订单执行后的手续费
                     # (这是付给券商的手续费)

                self.buyprice = order.executed.price
                # 将成交价格保存到buyprice变量中
                # (记住这次买入的价格)
                self.buycomm = order.executed.comm
                # 将手续费保存到buycomm变量中
                # (记住这次买入花了多少手续费)
                self.bar_executed_close = self.dataclose[0]
                # 记录下订单成交时那根K线的收盘价
                # (记住成交那天股票收盘时的价格)
            else:
            # 如果不是买入订单，那就是卖出订单
            # (如果不是买入成功，那就是卖出成功了...)
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                # 调用log方法记录卖出执行信息
                # (在日记本上记下：卖出成功！)
                         (order.executed.price,
                          # 获取订单执行后的成交价格
                          # (这是卖出的价格)
                          order.executed.value,
                          # 获取订单执行后的总价值（成交价格 * 数量），对于卖出来说是收入
                          # (这是卖出得到的总金额)
                          order.executed.comm))
                          # 获取订单执行后的手续费
                          # (这是卖出时付的手续费)
            self.bar_executed = len(self)
            # 记录订单执行时是第几根K线（从回测开始算）
            # (记住这次交易发生在整个模拟过程中的第几天)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
        # 如果订单状态是已取消（Canceled）、保证金不足（Margin）或被拒绝（Rejected）
        # (如果订单被取消了，或者钱不够买/卖，或者被交易所拒绝了)
            self.log('Order Canceled/Margin/Rejected')
            # 调用log方法记录订单失败信息
            # (在日记本上记下：订单出问题了，没成功！)

        self.order = None
        # 重置订单变量为None，表示当前没有挂单了（无论成功、失败还是取消）
        # (处理完这个订单通知后，把手上的指令单清空，表示现在没有正在等待处理的指令了)

    def notify_trade(self, trade):
    # 定义交易通知方法，当一笔完整的交易（买入后卖出）关闭时会被调用
    # (就像一个交易结果总结器，每次完成一买一卖后，告诉你这笔交易是赚是赔)
        if not trade.isclosed:
        # 如果这笔交易还没有关闭（即还没有卖出持有的仓位）
        # (如果这笔交易还没结束，比如只买了还没卖)
            return
            # 则不执行任何操作，直接返回
            # (那就先不管，等卖出之后再说)

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
        # 调用log方法记录交易的盈利情况
        # (在日记本上记下这笔交易的最终结果)
                 (trade.pnl,
                  # 获取交易的毛利润（不考虑手续费）
                  # (这是不算手续费赚了或亏了多少钱)
                  trade.pnlcomm))
                  # 获取交易的净利润（考虑手续费）
                  # (这是扣掉手续费后，真正赚了或亏了多少钱)

    def next(self):
    # 定义next方法，这是策略的核心，每个K线数据点都会调用一次这个方法
    # (就像游戏里的每一回合，角色都需要根据当前情况决定下一步行动)
        self.log('Close, %.2f' % self.dataclose[0])
        # 调用log方法记录当前K线的收盘价
        # (在日记本上记下今天的收盘价)
        if self.order:
        # 检查当前是否有正在处理的订单
        # (先看看手上有没有还没处理完的买入或卖出指令单)
            return
            # 如果有，则不执行任何新的操作，等待订单完成或失败
            # (如果有，就先不行动，等指令处理完了再说)

        if not self.position:
        # 检查当前是否持有仓位（即是否持有股票）
        # (看看现在手上有没有股票)
            condition1 = self.macd[-1] - self.signal[-1]
            # 计算上一根K线的MACD快线值减去慢线值
            # (看看昨天快线和慢线的差距是多少)
            condition2 = self.macd[0] - self.signal[0]
            # 计算当前K线的MACD快线值减去慢线值
            # (看看今天快线和慢线的差距是多少)
            if condition1 < 0 and condition2 > 0:
            # 如果上一根K线的快线在慢线下方（负值），而当前K线的快线在慢线上方（正值），形成金叉
            # (如果昨天快线还在慢线下面，今天快线跑到慢线上面去了，这就是“金叉”信号)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # 调用log方法记录准备创建买入订单
                # (在日记本上记下：准备买入！当前价格是XX)
                self.order = self.buy()
                # 执行买入操作，并将返回的订单对象赋值给self.order
                # (下达买入指令，并把这个指令单拿在手上)

        else:
        # 如果当前持有仓位（即手上有股票）
        # (如果现在手上有股票了)
            condition = (self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
            # 计算当前收盘价相对于买入时那根K线收盘价的涨跌幅（注意这里分母是当前收盘价，可能不是标准计算方式）
            # (算一下现在的价格相比于我买入那天的收盘价，涨了或跌了多少百分比 - 这个算法有点怪，通常是用买入价做分母)
            if condition > 0.1 or condition < -0.1:
            # 如果涨幅超过10%或者跌幅超过10% （基于上述特殊计算方式）
            # (如果算出来的结果大于10%或者小于-10%，也就是波动比较大了)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                # 调用log方法记录准备创建卖出订单
                # (在日记本上记下：准备卖出！当前价格是XX)
                self.order = self.sell()
                # 执行卖出操作，并将返回的订单对象赋值给self.order
                # (下达卖出指令，并把这个指令单拿在手上)


if __name__ == '__main__':
# 这是一个Python的标准写法，表示当这个脚本文件被直接运行时，才执行下面的代码块
# (这是程序的入口，只有当你直接运行这个文件时，下面的代码才会跑起来，如果被其他文件导入，则不执行)
    cerebro = bt.Cerebro()
    # 创建Cerebro引擎实例，Cerebro是大脑的意思，是backtrader的核心控制器
    # (创建了一个名叫cerebro的“大脑”或者说“指挥官”，用来管理整个回测过程)

    cerebro.addstrategy(TestStrategy)
    # 将我们上面定义的TestStrategy策略添加到Cerebro引擎中
    # (告诉“大脑”我们要使用刚才设计的那个TestStrategy游戏角色（策略）)

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    # 获取当前脚本文件所在的目录路径
    # (找到这个程序文件放在电脑的哪个文件夹里)
    datapath = os.path.join(modpath, '603186.csv')
    # 构建数据文件的完整路径，假设数据文件'603186.csv'和脚本在同一个目录下
    # (在程序文件所在的文件夹里，找到名叫'603186.csv'的股票数据文件)

    data = bt.feeds.GenericCSVData(
    # 创建一个通用CSV数据加载器实例，用于从CSV文件加载数据
    # (准备一个工具来读取CSV格式的股票数据)
        dataname=datapath,
        # 指定数据文件的路径
        # (告诉工具数据文件在哪里)
        fromdate=datetime.datetime(2010, 1, 1),
        # 设置回测开始日期
        # (告诉工具从2010年1月1日开始读取数据)
        todate=datetime.datetime(2020, 4, 12),
        # 设置回测结束日期
        # (告诉工具读到2020年4月12日结束)
        dtformat='%Y%m%d',
        # 指定CSV文件中日期的格式（年年年年月月日日）
        # (告诉工具CSV里的日期是像“20231027”这样的格式)
        datetime=2,
        # 指定日期时间列在CSV文件中的索引位置（从0开始计数，第3列）
        # (告诉工具日期在哪一列，这里是第3列)
        open=3,
        # 指定开盘价列的索引位置（第4列）
        # (告诉工具开盘价在哪一列，这里是第4列)
        high=4,
        # 指定最高价列的索引位置（第5列）
        # (告诉工具最高价在哪一列，这里是第5列)
        low=5,
        # 指定最低价列的索引位置（第6列）
        # (告诉工具最低价在哪一列，这里是第6列)
        close=6,
        # 指定收盘价列的索引位置（第7列）
        # (告诉工具收盘价在哪一列，这里是第7列)
        volume=10,
        # 指定成交量列的索引位置（第11列）
        # (告诉工具成交量在哪一列，这里是第11列)
        reverse=True
        # 指定数据是否需要反转，如果CSV数据是按时间倒序排列的，则设为True
        # (如果CSV文件里的数据是最新的在前面，旧的在后面，就告诉工具需要反过来读)
    )
    cerebro.adddata(data)
    # 将加载好的数据添加到Cerebro引擎中
    # (把读取到的股票数据交给“大脑”)

    cerebro.broker.setcash(10000)
    # 设置初始账户资金为10000
    # (告诉“大脑”开始模拟时有多少本金，这里是10000块)

    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    # 添加一个固定数量的sizer，表示每次交易买卖100股
    # (告诉“大脑”每次买卖股票时，固定买卖100股)

    cerebro.broker.setcommission(commission=0.005)
    # 设置交易手续费率为0.005（即0.5%）
    # (告诉“大脑”每次买卖股票需要支付0.5%的手续费)

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    # 添加交易分析器，用于分析每笔交易的详细情况
    # (给“大脑”安装一个“交易分析插件”，用来统计每次买卖的具体盈亏等信息)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    # 添加夏普比率分析器，用于衡量策略的风险调整后收益
    # (给“大脑”安装一个“夏普比率插件”，用来评估策略赚钱的效率和风险)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # 添加最大回撤分析器，用于衡量策略可能出现的最大资金损失比例
    # (给“大脑”安装一个“最大回撤插件”，用来评估策略可能遇到的最糟糕的亏损情况)
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    # 添加系统质量数（SQN）分析器，用于评估策略的整体质量
    # (给“大脑”安装一个“SQN插件”，用来给整个策略的表现打分)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 打印回测开始时的总资产价值
    # (在模拟开始前，看看我们有多少钱)

    results = cerebro.run()
    # 运行Cerebro引擎，执行回测
    # (告诉“大脑”：开始模拟交易！)
    first_strategy = results[0]
    # 获取回测结果中的第一个策略实例（因为我们只添加了一个策略）
    # (模拟结束后，“大脑”会返回结果，我们拿到那个执行了策略的角色实例)

    trade_analysis = first_strategy.analyzers.tradeanalyzer.get_analysis()
    # 从策略实例中获取交易分析器的分析结果
    # (让角色的“交易分析插件”把分析报告拿出来)
    print("------ TradeAnalyzer Analysis ------")
    # 打印分隔符和标题
    # (打印一个标题，告诉下面是交易分析结果)
    print(f"Total Closed Trades: {trade_analysis.total.closed}")
    # 打印总共完成的交易次数
    # (报告里说：一共完成了多少笔买卖)
    print(f"Total Net Profit: {trade_analysis.pnl.net.total:.2f}")
    # 打印总净利润（扣除手续费后）
    # (报告里说：最后总共赚了或亏了多少钱)
    print(f"Winning Trades: {trade_analysis.won.total}")
    # 打印盈利的交易次数
    # (报告里说：有多少笔交易是赚钱的)
    print(f"Losing Trades: {trade_analysis.lost.total}")
    # 打印亏损的交易次数
    # (报告里说：有多少笔交易是亏钱的)

    sharpe_ratio = first_strategy.analyzers.sharpe.get_analysis()
    # 从策略实例中获取夏普比率分析器的分析结果
    # (让角色的“夏普比率插件”把分析报告拿出来)
    print("------ SharpeRatio Analysis ------")
    # 打印分隔符和标题
    # (打印一个标题，告诉下面是夏普比率分析结果)
    print(f"Sharpe Ratio: {sharpe_ratio.get('sharperatio', 'N/A')}")
    # 打印夏普比率，如果结果中没有'sharperatio'键，则打印'N/A'
    # (报告里说：策略的夏普比率是多少，如果算不出来就显示N/A)

    drawdown = first_strategy.analyzers.drawdown.get_analysis()
    # 从策略实例中获取最大回撤分析器的分析结果
    # (让角色的“最大回撤插件”把分析报告拿出来)
    print("------ DrawDown Analysis ------")
    # 打印分隔符和标题
    # (打印一个标题，告诉下面是最大回撤分析结果)
    print(f"Max Drawdown: {drawdown.max.drawdown:.2f}%")
    # 打印最大回撤百分比
    # (报告里说：策略过程中最多亏损了本金的百分之多少)
    print(f"Max Drawdown Money: {drawdown.max.moneydown:.2f}")
    # 打印最大回撤金额
    # (报告里说：策略过程中最多亏损了多少钱)

    sqn = first_strategy.analyzers.sqn.get_analysis()
    # 从策略实例中获取SQN分析器的分析结果
    # (让角色的“SQN插件”把分析报告拿出来)
    print("------ SQN Analysis ------")
    # 打印分隔符和标题
    # (打印一个标题，告诉下面是SQN分析结果)
    print(f"SQN: {sqn.get('sqn', 'N/A')}")
    # 打印SQN值，如果结果中没有'sqn'键，则打印'N/A'
    # (报告里说：策略的SQN分数是多少，如果算不出来就显示N/A)

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 打印回测结束时的总资产价值
    # (在模拟结束后，看看我们最终还剩多少钱)
