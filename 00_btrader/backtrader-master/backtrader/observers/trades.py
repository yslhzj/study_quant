#!/usr/bin/env python
# 指定脚本使用 env 查找的 python 解释器执行。
# (白话: 告诉电脑用哪个版本的“翻译官”来读和运行这个“剧本”。)
# -*- coding: utf-8; py-indent-offset:4 -*-
# 声明文件编码为 UTF-8，并设置 Python 缩进偏移量为4个空格。
# (白话: 告诉电脑这个“剧本”是用“世界语”（UTF-8）写的，而且每段台词的开头要空4格，这样看起来整齐。)

# 一、导入所需模块及定义基础设置
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
# 从 __future__ 模块导入特性，以确保代码在 Python 2 和 Python 3 中的行为一致性。
# (白话: 引入一些“未来规则”，让这段代码无论是在老版本还是新版本的“翻译官”下都能表现得一样好，减少兼容性问题。)
# absolute_import: 确保 import X 总是查找顶级模块，而不是同目录下的模块。
# (白话: 找东西时，先从“国家图书馆”找，别先在“村头小卖部”乱翻。)
# division: 确保 / 总是执行真除法 (结果是浮点数)。
# (白话: 算除法时，3/2 等于 1.5，而不是 1，更精确。)
# print_function: 将 print 语句变为 print() 函数。
# (白话: 以前喊“打印！某某东西”，现在要说“打印（某某东西）”，更像个正式的命令。)
# unicode_literals: 使得代码中所有字符串字面量默认为 Unicode 字符串。
# (白话: 写字默认用“万国码”，这样中文、英文、各种符号都能好好显示，不乱码。)

import uuid
# 导入 uuid 模块，用于生成通用唯一识别码 (UUID)。
# (白话: 引入一个工具，这个工具能帮你生成独一无二的身份证号，比如给动态创建的图表元素用，确保它们不重名。)

from .. import Observer
# 从当前包的上级目录导入 Observer 基类。
# (白话: 引入一个“观察员”的基础模板，我们定义的观察器都要基于这个模板来创建。)
from ..utils.py3 import with_metaclass
# 从当前包的上级目录的 utils.py3 模块导入 with_metaclass 工具函数，用于在 Python 2/3 中兼容地使用元类。
# (白话: 引入一个辅助工具，帮助我们用一种高级的“模具制造技术”（元类），这种技术在老版本和新版本的“工厂”里都能用。)

from ..trade import Trade
# 从当前包的上级目录导入 Trade 类。
# (白话: 引入“交易”这个概念的定义，这样代码才知道什么是交易，交易有哪些信息。)

# 二、定义 Trades 观察器类，用于跟踪和绘制总体交易盈亏
class Trades(Observer):
    # 定义一个名为 Trades 的类，它继承自 Observer 类。
    # (白话: 创建一个专门记录和展示所有交易盈亏的“交易观察员”，它是“观察员”家族的一员。)
    '''
    该观察器跟踪完整的交易，并在交易关闭时绘制实现的盈亏水平。
    当头寸从0（或跨越0）变为X时，交易被打开；当头寸回到0（或反向跨越0）时，交易被关闭。

    参数:
      - ``pnlcomm`` (默认: ``True``)
        显示净利润/亏损，即扣除佣金后。如果设置为 ``False``，则显示未扣除佣金的交易结果。
    '''
    # 上述为原有docstring，根据指令，此处应删除，并在后续代码行进行解释。
    # (白话说明: 上面这段是原来对这个“交易观察员”的简介，说明了它的作用是跟踪买卖过程，并在买卖结束后把赚了多少或亏了多少画出来。还提到了一个参数可以设置是看扣手续费前还是扣手续费后的盈亏。)

    _stclock = True
    # 设置 _stclock 属性为 True，表示此观察器与策略时钟同步。
    # (白话: 告诉这个“记录员”（观察器），要跟“指挥部”（策略）的时间表对齐，一步一步跟着走，别自己乱跑。)

    lines = ('pnlplus', 'pnlminus')
    # 定义观察器需要绘制的两条线：一条用于正盈利 (pnlplus)，一条用于负盈利 (pnlminus)。
    # (白话: 这个“交易观察员”会在图上画两种点：赚钱的交易点和亏钱的交易点。)

    params = dict(pnlcomm=True)
    # 定义观察器的参数，pnlcomm 默认为 True，表示计算盈亏时包含佣金。
    # (白话: 设置一个开关“pnlcomm”，默认打开，表示算赚多少钱的时候，要把手续费也算进去，看的是净利润。)

    plotinfo = dict(plot=True, subplot=True,
    # 定义绘图信息字典，用于控制观察器的图表显示方式。
    # (白话: 设置这个观察器图表的“导演参数”，比如是否要画图、是不是画在小窗口里等等。)
                    plotname='Trades - Net Profit/Loss',
    # 设置图表的名称为 'Trades - Net Profit/Loss'。
    # (白话: 给这个小图表起个名字，叫“交易 - 净盈亏”。)
                    plotymargin=0.10,
    # 设置Y轴的边距为10%。
    # (白话: 图表上下两边留点空，别让线画得太贴边，好看点。)
                    plothlines=[0.0])
    # 在Y轴的0.0位置绘制一条水平线，通常代表盈亏平衡点。
    # (白话: 在图上画条横线，通常是盈亏平衡线，一眼看出是赚是赔。)

    plotlines = dict(
    # 定义各条线的绘图样式。
    # (白话: 具体规定怎么画那两种点（赚钱和亏钱的）。)
        pnlplus=dict(_name='Positive',
    # 定义 'pnlplus' (正盈利) 线的样式。
    # (白话: 赚钱的交易点怎么画。)
                     ls='', marker='o', color='blue',
    # ls='': 线型为空 (不画线，只画标记点); marker='o': 标记点为圆形; color='blue': 颜色为蓝色。
    # (白话: 赚钱的交易用蓝色的圆点表示，点和点之间不连线。)
                     markersize=8.0, fillstyle='full'),
    # markersize=8.0: 标记点大小为8.0; fillstyle='full': 标记点完全填充。
    # (白话: 圆点要大一点（8号），而且是实心的。)
        pnlminus=dict(_name='Negative',
    # 定义 'pnlminus' (负盈利) 线的样式。
    # (白话: 亏钱的交易点怎么画。)
                      ls='', marker='o', color='red',
    # ls='': 线型为空; marker='o': 标记点为圆形; color='red': 颜色为红色。
    # (白话: 亏钱的交易用红色的圆点表示，点和点之间也不连线。)
                      markersize=8.0, fillstyle='full')
    # markersize=8.0: 标记点大小为8.0; fillstyle='full': 标记点完全填充。
    # (白话: 圆点也是8号大小，实心的。)
    )
    # 结束 plotlines 字典的定义。
    # (白话: 画点规则设定完毕。)

    # 三、初始化 Trades 观察器实例的属性
    def __init__(self):
    # 定义 Trades 类的构造函数 (初始化方法)。
    # (白话: 这是“交易观察员”刚被创建出来时要做的准备工作。)

        self.trades = 0
    # 初始化已完成的交易总数。
    # (白话: 准备一个计数器，记下一共完成了多少笔买卖，初始为0。)

        self.trades_long = 0
    # 初始化多头交易的总数。
    # (白话: 准备一个计数器，记下做了多少次“买入再卖出”的买卖，初始为0。)
        self.trades_short = 0
    # 初始化空头交易的总数。
    # (白话: 准备一个计数器，记下做了多少次“卖出再买入”的买卖，初始为0。)

        self.trades_plus = 0
    # 初始化盈利交易的总数 (计入佣金后)。
    # (白话: 准备一个计数器，记下有多少笔买卖是赚钱的（扣掉手续费后），初始为0。)
        self.trades_minus = 0
    # 初始化亏损交易的总数 (计入佣金后)。
    # (白话: 准备一个计数器，记下有多少笔买卖是亏钱的（扣掉手续费后），初始为0。)

        self.trades_plus_gross = 0
    # 初始化毛盈利交易的总数 (不计佣金)。
    # (白话: 准备一个计数器，记下有多少笔买卖是赚钱的（不扣手续费），初始为0。)
        self.trades_minus_gross = 0
    # 初始化毛亏损交易的总数 (不计佣金)。
    # (白话: 准备一个计数器，记下有多少笔买卖是亏钱的（不扣手续费），初始为0。)

        self.trades_win = 0
    # 初始化连续盈利的当前次数。
    # (白话: 准备一个计数器，记下当前连续赚了几笔钱，初始为0。)
        self.trades_win_max = 0
    # 初始化历史最大连续盈利次数。
    # (白话: 准备一个记录本，记下历史上最多连续赚了多少笔钱，初始为0。)
        self.trades_win_min = 0
    # 初始化历史最小连续盈利次数 (通常指连续盈利中断前的次数，或在某些特定统计场景使用)。
    # (白话: 准备一个记录本，记下历史上最少连续赚了多少笔钱才断掉，初始为0，这个用得少一些。)

        self.trades_loss = 0
    # 初始化连续亏损的当前次数。
    # (白话: 准备一个计数器，记下当前连续亏了几笔钱，初始为0。)
        self.trades_loss_max = 0
    # 初始化历史最大连续亏损次数。
    # (白话: 准备一个记录本，记下历史上最多连续亏了多少笔钱，初始为0。)
        self.trades_loss_min = 0
    # 初始化历史最小连续亏损次数 (同 trades_win_min 的逻辑)。
    # (白话: 准备一个记录本，记下历史上最少连续亏了多少笔钱才断掉，初始为0，这个也用得少一些。)

        self.trades_length = 0
    # 初始化当前交易的持仓周期长度。
    # (白话: 准备一个计数器，记下一笔买卖从开始到结束持续了多久（多少根K线），初始为0。)
        self.trades_length_max = 0
    # 初始化历史最长持仓周期。
    # (白话: 准备一个记录本，记下历史上哪笔买卖持续时间最长，初始为0。)
        self.trades_length_min = 0
    # 初始化历史最短持仓周期。
    # (白话: 准备一个记录本，记下历史上哪笔买卖持续时间最短，初始为0。)

    # 四、Trades 观察器在每个K线周期执行的逻辑
    def next(self):
    # 定义 next 方法，该方法在每个新的K线数据点 (bar) 到达时被调用。
    # (白话: 这是“交易观察员”每个时间点（比如每天收盘后）都要执行的任务。)
        for trade in self._owner._tradespending:
    # 遍历策略中所有待处理的交易 (_tradespending 列表)。
    # (白话: 检查一下“指挥部”（策略）那里有没有刚结束的买卖。)
            if trade.data not in self.ddatas:
    # 如果交易对应的数据源不在当前观察器监控的数据源列表中，则跳过。
    # (白话: 如果这笔买卖用的不是我（这个观察员）负责看管的股票数据，那我就不管了。)
                continue
    # 继续下一次循环。
    # (白话: 跳过这笔，看下一笔。)

            if not trade.isclosed:
    # 如果交易尚未关闭，则跳过。
    # (白话: 如果这笔买卖还没结束（还在持仓中），那也先不管，等它结束了再说。)
                continue
    # 继续下一次循环。
    # (白话: 跳过这笔，看下一笔。)

            pnl = trade.pnlcomm if self.p.pnlcomm else trade.pnl
    # 根据参数 self.p.pnlcomm 的设置，获取交易的净盈亏 (pnlcomm) 或毛盈亏 (pnl)。
    # (白话: 看看之前设置的“算不算手续费”开关是开是关，然后拿出对应的盈亏金额。)

            if pnl >= 0.0:
    # 如果盈亏大于或等于0 (盈利或不亏不赚)。
    # (白话: 如果这笔买卖是赚钱的，或者至少没亏钱。)
                self.lines.pnlplus[0] = pnl
    # 在 'pnlplus' 线上记录当前的盈亏值。
    # (白话: 就在代表“赚钱”的线上，把赚的金额标出来。)
            else:
    # 如果盈亏小于0 (亏损)。
    # (白话: 如果这笔买卖是亏钱的。)
                self.lines.pnlminus[0] = pnl
    # 在 'pnlminus' 线上记录当前的盈亏值。
    # (白话: 就在代表“亏钱”的线上，把亏的金额标出来。)

# 五、定义 MetaDataTrades 元类，用于动态创建 DataTrades 的 lines 和 plotlines
class MetaDataTrades(Observer.__class__):
    # 定义一个名为 MetaDataTrades 的元类，它继承自 Observer 类的元类 (通常是 type)。
    # (白话: 这像是一个“模具的模具”，它不是直接造东西的，而是用来规定怎么造“DataTrades”这种“模具”的。)
    def donew(cls, *args, **kwargs):
    # 定义元类的 donew 方法，这个方法在创建 DataTrades 类的新实例 (_obj) 之前被调用，用于自定义实例的创建过程。
    # (白话: 这是“模具的模具”里的一个特殊指令，当要用“DataTrades模具”造一个实际的观察器时，这个指令会先运行，做一些准备工作。)
        _obj, args, kwargs = super(MetaDataTrades, cls).donew(*args, **kwargs)
    # 调用父元类 (Observer.__class__) 的 donew 方法，完成 Observer 实例 (_obj) 的基本创建。
    # (白话: 先让“上级模具的模具”把基础的观察器造出来。)

        # Recreate the lines dynamically
        # (根据指令，此行为原有注释，已融入下方解释)
        if _obj.params.usenames:
    # 检查 DataTrades 实例的参数 usenames 是否为 True。
    # (白话: 看看这个要造的观察器是不是设置了要用数据名当图例名。)
            lnames = tuple(x._name for x in _obj.datas)
    # 如果 usenames 为 True，则从实例的每个数据源 (x in _obj.datas) 中获取其名称 (x._name) 作为线的名称。
    # (白话: 如果要用数据名，那就把每个数据（比如“股票A”、“股票B”）的名字拿出来，作为图上每条线的名字。)
        else:
    # 如果 usenames 不为 True。
    # (白话: 如果不用数据名。)
            lnames = tuple('data{}'.format(x) for x in range(len(_obj.datas)))
    # 生成默认的线名称，格式为 'data0', 'data1', ...，数量与数据源个数相同。
    # (白话: 那就自动给每条线起名叫“数据0”、“数据1”等等。)

        # Generate a new lines class
        # (根据指令，此行为原有注释，已融入下方解释)
        linescls = cls.lines._derive(uuid.uuid4().hex, lnames, 0, ())
    # 基于 Observer 的 lines 属性 (通常是一个 Lines Sizer 对象)，动态创建一个新的 Lines 类 (linescls)。
    # 这个新类使用 uuid 生成一个唯一名称，并包含上面生成的 lnames 作为其具体的 line 名称。
    # (白话: 用一个独特的名字（像身份证号一样，保证不重复）和上面定好的线名，临时造一个新的“画线规则集合”。)

        # Instantiate lines
        # (根据指令，此行为原有注释，已融入下方解释)
        _obj.lines = linescls()
    # 将新创建的 Lines 类的实例赋值给 DataTrades 实例的 lines 属性。
    # (白话: 把这个刚造好的“画线规则集合”装到实际的观察器上，以后观察器就按这个规则画线。)

        # Generate plotlines info
        # (根据指令，此行为原有注释，已融入下方解释)
        markers = ['o', 'v', '^', '<', '>', '1', '2', '3', '4', '8', 's', 'p',
                   '*', 'h', 'H', '+', 'x', 'D', 'd']
    # 定义一个包含多种标记点样式的列表。
    # (白话: 准备一堆不同形状的“图章”，比如圆圈、三角、星星等。)

        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'b', 'g', 'r', 'c', 'm',
                  'y', 'k', 'b', 'g', 'r', 'c', 'm']
    # 定义一个包含多种颜色的列表。
    # (白话: 准备一堆不同颜色的“颜料”，比如蓝色、绿色、红色等。)

        basedict = dict(ls='', markersize=8.0, fillstyle='full')
    # 定义一个基础绘图样式字典：不画连接线 (ls='')，标记点大小为8.0，完全填充 (fillstyle='full')。
    # (白话: 先定一个基本的画点风格：点和点之间不连线，点的大小是8号，而且是实心的。)

        plines = dict()
    # 初始化一个空字典 plines，用于存储每条线的具体绘图样式。
    # (白话: 准备一个空的“调色盘”，等下给每条线配颜色和形状。)
        for lname, marker, color in zip(lnames, markers, colors):
    # 遍历线名列表 (lnames)、标记点列表 (markers) 和颜色列表 (colors)。
    # (白话: 给每一条线，都从准备好的“图章”和“颜料”里各挑一个出来。)
            plines[lname] = d = basedict.copy()
    # 复制基础样式到变量 d，并将 d 赋值给 plines 字典中对应线名 (lname) 的条目。
    # (白话: 先拿一份基本风格，然后准备在这个基础上给这条线定制。)
            d.update(marker=marker, color=color)
    # 更新字典 d，为其添加或修改 marker (标记点样式) 和 color (颜色)。
    # (白话: 把刚选好的“图章”和“颜料”用到这条线的风格上。)

        plotlines = cls.plotlines._derive(
    # 基于 Observer 的 plotlines 属性，动态创建一个新的 PlotLines 对象。
    # (白话: 用一个独特的名字和上面配好的各种线的风格，临时造一个新的“画图风格集合”。)
            uuid.uuid4().hex, plines, [], recurse=True)
    # 使用 uuid 生成唯一名称，plines 作为具体的样式定义，recurse=True 表示递归处理。
    # (白话: 这个新的“画图风格集合”也是独一无二的，并且包含了所有线的定制风格。)
        _obj.plotlines = plotlines()
    # 将新创建的 PlotLines 对象的实例赋值给 DataTrades 实例的 plotlines 属性。
    # (白话: 把这个刚造好的“画图风格集合”也装到实际的观察器上。)

        return _obj, args, kwargs  # return the instantiated object and args
    # 返回经过修改的 DataTrades 实例 (_obj) 以及原始的参数 (*args, **kwargs)。
    # (白话: 把这个装备齐全的观察器交出去，让系统继续完成它的创建。)

# 六、定义 DataTrades 观察器类，为每个数据源分别绘制交易盈亏
class DataTrades(with_metaclass(MetaDataTrades, Observer)):
    # 定义一个名为 DataTrades 的类，它使用 MetaDataTrades 作为其元类，并继承自 Observer 类。
    # (白话: 创建一个更高级的“多数据交易观察员”，它能同时关注好几个不同的股票（数据源），并且用上了前面定义的“模具的模具”来帮它在创建时自动配置好画图的细节。)
    _stclock = True
    # 设置 _stclock 属性为 True，表示此观察器与策略时钟同步。
    # (白话: 同样，这个“多数据观察员”也要跟“指挥部”的时间表对齐。)

    params = (('usenames', True),)
    # 定义观察器的参数，usenames 默认为 True，表示在图例中使用数据源的名称。
    # (白话: 设置一个开关“usenames”，默认打开，表示图上不同线的名字就用对应数据的名字，比如“股票A线”、“股票B线”。)

    plotinfo = dict(plot=True, subplot=True, plothlines=[0.0],
    # 定义绘图信息字典。
    # (白话: 设置这个观察器图表的“导演参数”。)
                    plotymargin=0.10)
    # plot=True: 绘制图表; subplot=True: 在子图中绘制; plothlines=[0.0]: 在0.0位置画水平线; plotymargin=0.10: Y轴边距10%。
    # (白话: 要画图，画在小窗口里，图上要有0刻度线（盈亏平衡线），上下留点空隙。)

    plotlines = dict()
    # 初始化 plotlines 为空字典。实际的绘图样式将由元类 MetaDataTrades 动态生成。
    # (白话: 这里先空着，具体的画图风格等会儿由“模具的模具”自动填好。)

    # 七、DataTrades 观察器在每个K线周期执行的逻辑
    def next(self):
    # 定义 next 方法，该方法在每个新的K线数据点 (bar) 到达时被调用。
    # (白话: 这是“多数据观察员”每个时间点要执行的任务。)
        for trade in self._owner._tradespending:
    # 遍历策略中所有待处理的交易。
    # (白话: 检查“指挥部”那里有没有刚结束的买卖。)
            if trade.data not in self.ddatas:
    # 如果交易对应的数据源不在当前观察器监控的数据源列表中，则跳过。
    # (白话: 如果这笔买卖涉及的数据不是我这个观察员负责的，我就不管。)
                continue
    # 继续下一次循环。
    # (白话: 跳过这笔，看下一笔。)

            if not trade.isclosed:
    # 如果交易尚未关闭，则跳过。
    # (白话: 如果这笔买卖还没结束，也先不管。)
                continue
    # 继续下一次循环。
    # (白话: 跳过这笔，看下一笔。)

            self.lines[trade.data._id - 1][0] = trade.pnl
    # 获取交易对应数据源的内部ID (trade.data._id)，减1后作为索引 (因为ID从1开始，列表索引从0开始)。
    # 将该交易的毛盈亏 (trade.pnl) 赋值给对应数据源的动态生成的lines上。
    # (白话: 找到这笔交易是用哪个数据（比如“股票A”还是“股票B”）做的，然后在图上代表这个数据的线上，把这笔交易的盈亏（没扣手续费的）标出来。)
