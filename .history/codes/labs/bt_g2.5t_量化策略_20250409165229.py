import datetime
import math
import os
import pandas as pd
import backtrader as bt
# 确保下面的导入路径是正确的，根据你的项目结构调整
from codes.labs.bt_g2.5t_量化策略 import AShareETFStrategy


def load_data_feeds(cerebro, data_files, column_mapping, openinterest_col, fromdate, todate):
    """
    加载并处理数据文件，将其添加到Cerebro实例中。

    Args:
        cerebro: Backtrader Cerebro 引擎实例。
        data_files: 包含数据文件路径的列表。
        column_mapping: Excel列名到Backtrader标准列名的映射字典。
        openinterest_col: 持仓量列的索引 (-1 表示没有)。
        fromdate: 回测起始日期 (datetime对象)。
        todate: 回测结束日期 (datetime对象)。

    Returns:
        成功加载的数据文件数量，如果加载失败则返回 None。
    """
    print("<font color='blue'>开始加载数据...</font>")
    # 打印提示信息，表示开始加载数据。 (打印一句话，提示用户：开始加载数据了。)
    loaded_data_count = 0  # 计数器，用于记录成功加载的数据数量
    # 初始化一个计数器，记录成功加载了多少个数据文件。 (初始化一个计数器，用来数成功加载了几个文件。)

    for file_path in data_files:
        # 遍历数据文件路径列表。 (循环处理每个数据文件。)
        try:
            # 尝试执行以下代码，捕获可能发生的异常。 (尝试做下面的事情，如果出错了就跳到except那里。)
            if not os.path.exists(file_path):
                print(f"<font color='red'>错误: 文件未找到 {file_path}</font>")
                continue  # 跳过不存在的文件

            print(f"正在加载: {file_path}")
            # 打印正在加载的文件路径。 (打印一下当前正在处理哪个文件。)
            dataframe = pd.read_excel(file_path)
            # 使用pandas读取Excel文件到DataFrame。 (用pandas读取Excel文件，把数据放到一个表格里。)

            dataframe.rename(columns=column_mapping, inplace=True)
            # 重命名DataFrame的列名，使其符合Backtrader标准。 (按照我们定义的字典，把表格的列名改成Backtrader认识的名字。)

            if 'datetime' not in dataframe.columns:
                print(
                    f"<font color='red'>错误: 文件 {file_path} 缺少 'datetime' 列。</font>")
                continue  # 跳过缺少日期列的文件

            # --- 时间列处理 ---
            try:
                # 尝试将'datetime'列转换为datetime对象，并处理可能的格式错误
                # Using errors='coerce' will turn unparseable dates into NaT (Not a Time)
                dataframe['datetime'] = pd.to_datetime(
                    dataframe['datetime'], errors='coerce')
                # 删除包含无效日期的行
                original_rows = len(dataframe)
                dataframe.dropna(subset=['datetime'], inplace=True)
                if len(dataframe) < original_rows:
                    print(
                        f"<font color='orange'>警告: 文件 {file_path} 中移除了 {original_rows - len(dataframe)} 行无效日期数据。</font>")
            except Exception as e:
                # 捕获日期时间转换异常。 (如果日期时间转换出错了。)
                print(
                    f"<font color='red'>错误: 无法解析 {file_path} 中的日期时间列。错误: {e}</font>")
                # 打印错误信息，提示日期时间列解析失败，并显示错误信息。 (打印错误信息，告诉用户日期时间格式有问题，请检查。)
                continue  # 跳过当前文件
                # 跳过当前文件，继续处理下一个文件。 (跳过这个文件，不处理了，继续处理下一个。)

            # --- 数据过滤 ---
            dataframe = dataframe[(dataframe['datetime'] >= fromdate) & (
                dataframe['datetime'] <= todate)]
            # 根据提供的起始和结束日期过滤数据。 (只保留在指定日期范围内的数据。)

            if dataframe.empty:
                print(
                    f"<font color='orange'>警告: 文件 {file_path} 在日期范围 {fromdate.date()} 到 {todate.date()} 内没有数据。</font>")
                continue  # 如果过滤后数据为空，则跳过

            # --- Backtrader 数据 Feed 创建 ---
            # 确保所有必需的列都存在
            required_cols = ['datetime', 'open',
                             'high', 'low', 'close', 'volume']
            missing_cols = [
                col for col in required_cols if col not in dataframe.columns]
            if missing_cols:
                print(
                    f"<font color='red'>错误: 文件 {file_path} 缺少必需的列: {', '.join(missing_cols)}</font>")
                continue

            data_feed = bt.feeds.PandasData(
                dataname=dataframe,
                datetime='datetime',  # 指定日期时间列
                # 指定 OHLCV 列
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=None if openinterest_col == -
                    1 else dataframe.columns[openinterest_col],  # 如果有持仓量列则指定
                # 时间范围已在DataFrame层面过滤，这里再次指定确保一致性
                fromdate=fromdate,
                todate=todate
            )
            # 使用Pandas DataFrame创建一个Backtrader数据源对象。 (把我们处理好的表格数据，变成Backtrader能认得的数据格式。)

            # 从文件名提取数据名称 (例如 '510050_d' -> '510050')
            data_name = os.path.splitext(os.path.basename(file_path))[
                0].split('_')[0]
            # 提取文件名作为数据在Backtrader中的标识名称。 (给这个数据起个名字，方便后面区分。)

            cerebro.adddata(data_feed, name=data_name)
            # 将创建的数据源添加到Cerebro引擎中。 (把这个数据添加到交易大脑里。)
            loaded_data_count += 1
            # 成功加载计数器加一。 (加载成功一个，计数器就加1。)
            print(
                f"<font color='green'>成功加载数据: {file_path}, 数据名称: {data_name}</font>")
            # 打印成功加载的信息。 (告诉用户这个文件加载好了。)

        except FileNotFoundError:
            # 捕获文件未找到异常。 (如果文件路径不对，找不到文件。)
            print(f"<font color='red'>错误: 文件未找到 {file_path}</font>")
            # 打印文件未找到的错误信息。 (告诉用户找不到这个文件。)
        except Exception as e:
            # 捕获其他所有在加载过程中可能发生的异常。 (如果加载过程中出了其他问题。)
            print(f"<font color='red'>加载数据 {file_path} 时出错: {e}</font>")
            # 打印加载数据时发生的通用错误信息。 (告诉用户加载这个文件的时候出错了，并显示具体错误。)

    if loaded_data_count == 0:
        # 检查是否成功加载了任何数据文件。 (检查是不是一个文件都没加载成功。)
        print("<font color='red'>错误：未能成功加载任何数据文件。</font>")
        # 如果没有加载任何文件，打印错误信息。 (如果一个都没加载成功，就报错。)
        return None  # 返回 None 表示加载失败
        # 返回 None，表示数据加载环节失败了。 (告诉程序，数据没准备好，后面别运行了。)

    print(f"<font color='blue'>数据加载完成，共加载 {loaded_data_count} 个文件。</font>")
    # 打印数据加载完成的信息和成功加载的文件数量。 (告诉用户数据都加载完了，一共加载了多少个。)
    return loaded_data_count  # 返回加载成功的数量
    # 返回成功加载的文件数量。 (告诉程序成功加载了几个文件。)


def run_strategy(run_optimization=False):
    """
    运行回测或参数优化。

    Args:
        run_optimization (bool): 如果为 True，则运行参数优化；否则运行单次回测。
    """
    # --- Cerebro 初始化 ---
    # optreturn=False 保留策略实例以便访问分析器，这对于优化后分析至关重要
    # stdstats 根据 run_optimization 联动，优化时关闭以提高速度，单测时打开以绘图
    cerebro = bt.Cerebro(stdstats=not run_optimization, optreturn=False)
    # 创建Cerebro引擎实例。 (创建一个交易回测的大脑。)
    # stdstats=False/True: 是否自动添加标准观察器（如资金曲线、交易记录）。 (要不要显示默认的统计图表。)
    # optreturn=False: 优化后返回完整的策略实例列表，而不是简化版，方便访问分析器。 (优化跑完后，把每次运行的详细情况都记下来。)

    # --- 数据加载 ---
    # 定义数据文件路径列表。 (定义一个列表，里面放着我们要分析的ETF数据文件的路径。)
    data_files = [r'D:\\BT2025\\datas\\510050_d.xlsx',
                  r'D:\\BT2025\\datas\\510300_d.xlsx', r'D:\\BT2025\\datas\\159949_d.xlsx']
    # 定义Excel列名到Backtrader标准列名的映射字典。 (定义一个字典，告诉程序Excel里的列名对应Backtrader的标准名字。)
    column_mapping = {'date': 'datetime', 'open': 'open',
                      'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'}
    # 指定持仓量列索引为-1，表示数据中没有持仓量列。 (我们的数据里没有"持仓量"这一列。)
    openinterest_col = -1
    # 设置回测的起始日期。 (设置回测从哪天开始。)
    fromdate = datetime.datetime(2015, 1, 1)
    # 设置回测的结束日期。 (设置回测到哪天结束。)
    todate = datetime.datetime(2024, 4, 30)

    # 调用封装好的数据加载函数
    # 调用我们之前定义的 load_data_feeds 函数来加载数据。 (让刚才准备好的"数据加载工具箱"开始工作。)
    loaded_count = load_data_feeds(
        cerebro, data_files, column_mapping, openinterest_col, fromdate, todate)
    if loaded_count is None:
        # 如果数据加载失败（返回 None），则打印错误信息并退出函数。 (如果数据加载失败了，就提示一下，然后不继续往下跑了。)
        print("<font color='red'>因数据加载失败，策略无法运行。</font>")
        return  # 退出函数

    # --- Broker 设置 ---
    # 设置初始资金。 (设置开始回测时有多少本金。)
    startcash = 100000.0
    # 将初始资金告知 Cerebro 的 Broker。 (告诉交易大脑，我们有多少本金。)
    cerebro.broker.setcash(startcash)
    # 设置交易佣金和杠杆。 (设置每次买卖需要付多少手续费，以及是否有杠杆。)
    # commission: 佣金率 (例如 0.0005 表示 0.05%)
    # leverage: 杠杆倍数 (1.0 表示无杠杆)
    cerebro.broker.setcommission(commission=0.0005, leverage=1.0)  # 示例佣金设置

    # --- 添加策略或进行优化 ---
    if run_optimization:
        # 如果 run_optimization 标志为 True，则执行参数优化。 (如果我们要进行"装备测试"。)
        print("<font color='blue'>开始运行参数优化...</font>")
        # 打印开始优化的提示信息。 (告诉用户：开始优化参数了。)

        # 定义优化参数的范围
        # 定义快速EMA周期的测试范围 (例如: 10, 15, 20, 25, 30)。 (快速均线我们要试试 10天、15天...一直到30天。)
        fast_ema_range = range(10, 31, 5)
        # 定义慢速EMA周期的测试范围 (例如: 20, 30, 40, 50, 60)。 (慢速均线我们要试试 20天、30天...一直到60天。)
        slow_ema_range = range(20, 61, 10)
        # 定义布林带周期的测试范围 (例如: 15, 20, 25, 30, 35)。 (布林带我们要试试用 15天、20天...一直到35天的数据来算。)
        boll_period_range = range(15, 36, 5)
        # 定义布林带标准差倍数的测试范围 (例如: 1.5, 1.8, 2.0, 2.2, 2.5)。 (布林带的宽度我们要试试 1.5倍、1.8倍...一直到2.5倍标准差。)
        boll_devfactor_range = [1.5, 1.8, 2.0, 2.2, 2.5]  # 使用列表处理浮点数步长

        # 使用 optstrategy 添加策略以进行优化
        # 调用 cerebro.optstrategy 来添加策略并指定要优化的参数。 (告诉交易大脑，我们要用这个策略来测试这些参数组合。)
        stratruns = cerebro.optstrategy(
            AShareETFStrategy,  # 要优化的策略类 (指定我们要测试的策略。)
            # --- 优化的参数 ---
            fast_ema_period=fast_ema_range,          # 快速EMA周期范围 (快速均线的测试范围。)
            slow_ema_period=slow_ema_range,          # 慢速EMA周期范围 (慢速均线的测试范围。)
            boll_period=boll_period_range,            # 布林带周期范围 (布林带周期的测试范围。)
            # 布林带标准差倍数范围 (布林带宽度的测试范围。)
            boll_devfactor=boll_devfactor_range,
            # --- 保持不变的参数 (必须包装在元组或列表中) ---
            # 注意：即使参数值是单个值，也要放在元组或列表中，例如 (14,) 或 [True]
            # ATR周期保持14不变。 (ATR指标的周期固定用14。)
            atr_period=(14,),
            # 单笔交易风险比例保持2%不变。 (每次交易最多亏损本金的2%。)
            risk_per_trade_percent=(0.02,),
            # 目标利润ATR倍数保持2.0不变。 (目标赚取2倍ATR的利润。)
            target_profit_atr_multiplier=(2.0,),
            # 追踪止损ATR倍数保持1.5不变。 (价格回撤1.5倍ATR就止损。)
            trailing_stop_atr_multiplier=(1.5,),
            enable_trailing_stop=(True,),               # 启用追踪止损。 (开启追踪止损功能。)
            enable_target_profit=(True,),               # 启用目标利润。 (开启目标利润功能。)
            # 交易暂停阈值保持-5%不变。 (如果亏损超过5%，暂停交易。)
            trade_halt_threshold_percent=(-0.05,),
            enable_trade_halt=(True,),                  # 启用交易暂停功能。 (开启交易暂停功能。)
            # 移动平均过滤器周期保持20不变。 (用20日均线做过滤。)
            ma_filter_period=(20,),
            # 启用移动平均过滤器。 (开启均线过滤功能。)
            enable_ma_filter=(True,),
            # 成交量过滤器倍数保持1.5不变。 (要求成交量是平均成交量的1.5倍以上。)
            volume_filter_multiplier=(1.5,),
            # 启用成交量过滤器。 (开启成交量过滤功能。)
            enable_volume_filter=(True,),
            # 特定交易暂停日期列表保持为空。 (没有指定特别需要暂停交易的日期。)
            specific_trade_halt_dates=([],),
            # 最小交易间隔天数保持2天不变。 (两次交易之间至少间隔2天。)
            min_trade_interval_days=(2,)
        )
    else:
        # 如果 run_optimization 标志为 False，则执行单次回测。 (如果只是进行一次"实战演练"。)
        print("<font color='blue'>开始运行单次回测...</font>")
        # 打印开始单次回测的提示信息。 (告诉用户：开始跑一次回测了。)

        # 使用 addstrategy 添加策略进行单次运行
        # 调用 cerebro.addstrategy 添加策略，并传入一组固定的参数。 (告诉交易大脑，用这套固定的参数跑一次策略。)
        cerebro.addstrategy(
            AShareETFStrategy,  # 要运行的策略类 (指定要运行的策略。)
            # --- 用于单次回测的固定参数 ---
            fast_ema_period=20,  # 快速EMA周期设为20。 (快速均线用20天。)
            slow_ema_period=50,  # 慢速EMA周期设为50。 (慢速均线用50天。)
            boll_period=20,     # 布林带周期设为20。 (布林带用20天。)
            boll_devfactor=2.0,  # 布林带标准差倍数设为2.0。 (布林带宽度用2.0倍标准差。)
            atr_period=14,      # ATR周期设为14。 (ATR指标周期用14。)
            risk_per_trade_percent=0.02,  # 单笔交易风险比例设为2%。 (每次交易最多亏2%。)
            target_profit_atr_multiplier=2.0,  # 目标利润ATR倍数设为2.0。 (目标赚2倍ATR。)
            trailing_stop_atr_multiplier=1.5,  # 追踪止损ATR倍数设为1.5。 (回撤1.5倍ATR就跑。)
            enable_trailing_stop=True,  # 启用追踪止损。 (开启追踪止损。)
            enable_target_profit=True,  # 启用目标利润。 (开启目标利润。)
            trade_halt_threshold_percent=-0.05,  # 交易暂停阈值设为-5%。 (亏超过5%就暂停。)
            enable_trade_halt=True,  # 启用交易暂停。 (开启暂停交易功能。)
            ma_filter_period=20,    # 移动平均过滤器周期设为20。 (用20日均线过滤。)
            enable_ma_filter=True,  # 启用移动平均过滤器。 (开启均线过滤。)
            volume_filter_multiplier=1.5,  # 成交量过滤器倍数设为1.5。 (成交量要超过平均的1.5倍。)
            enable_volume_filter=True,   # 启用成交量过滤器。 (开启成交量过滤。)
            specific_trade_halt_dates=[],  # 特定交易暂停日期列表为空。 (没有特殊暂停交易日。)
            min_trade_interval_days=2   # 最小交易间隔天数设为2。 (两次交易至少隔2天。)
        )

    # --- 添加分析器 (优化和单测都需要) ---
    # 添加 SharpeRatio 分析器，计算夏普比率。 (添加一个分析器，用来算夏普比率。)
    # _name: 分析器的名称，方便后续引用。 (给这个分析器起个名字叫 'sharpe'。)
    # timeframe: 计算的时间周期 (日线)。 (基于每天的数据计算。)
    # compression: 时间压缩单位 (1表示不压缩)。 (用的是原始的日线数据。)
    # factor: 年化因子 (一年大约252个交易日)。 (一年按252天算，用来把日收益率年化。)
    # annualize: 是否进行年化。 (把结果转换成年化夏普比率。)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe',
                        timeframe=bt.TimeFrame.Days, compression=1, factor=252, annualize=True)
    # 添加 Returns 分析器，计算回报率。 (添加一个分析器，用来算回报率。)
    # _name: 分析器名称 'returns'。 (给它起个名字叫 'returns'。)
    # timeframe: 日线周期。 (基于每天的数据算。)
    # compression: 不压缩。 (用原始日线。)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns',
                        timeframe=bt.TimeFrame.Days, compression=1)
    # 添加 DrawDown 分析器，计算最大回撤。 (添加一个分析器，用来算最大亏了多少。)
    # _name: 分析器名称 'drawdown'。 (给它起个名字叫 'drawdown'。)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # 添加 TradeAnalyzer 分析器，分析交易详情。 (添加一个分析器，用来分析具体的交易情况。)
    # _name: 分析器名称 'tradeanalyzer'。 (给它起个名字叫 'tradeanalyzer'。)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')

    # --- 运行 Cerebro ---
    print("<font color='blue'>运行Cerebro引擎...</font>")
    # 打印开始运行引擎的提示。 (告诉用户：大脑开始运转了。)
    # 执行回测或优化。maxcpus=1 表示使用单个CPU核心，便于调试。 (让大脑开始跑回测或者优化，这里先用一个CPU跑。)
    results = cerebro.run(maxcpus=1)
    print("<font color='blue'>Cerebro运行完成。</font>")
    # 打印运行完成的提示。 (告诉用户：大脑跑完了。)

    # --- 结果处理 ---
    if run_optimization:
        # 如果是优化模式，处理优化结果。 (如果是"装备测试"模式，处理测试结果。)
        print("\n<font color='blue'>--- 参数优化结果分析 ---</font>")
        # 打印优化结果分析的标题。 (打印一个标题，下面是优化结果分析。)

        if not results:
            # 检查优化是否产生了结果。 (检查优化有没有跑出结果。)
            print("<font color='red'>错误：优化运行未能产生任何结果。</font>")
            # 如果没有结果，打印错误信息。 (如果没跑出结果，就报错。)
            return  # 退出函数

        # 初始化用于存储有效结果和各项指标的列表。 (准备一些空列表，用来放有效的测试结果和各项指标数据。)
        valid_results = []
        all_sharpes = []
        all_returns = []
        all_drawdowns = []

        print(f"优化产生了 {len(results)} 组结果，开始处理...")
        # 打印优化产生的总结果数量。 (告诉用户一共跑了多少次测试。)

        # 遍历优化运行产生的所有结果 (stratruns)
        # results 是一个列表的列表，外层列表代表不同的参数组合，内层列表包含该参数组合下所有数据源对应的策略实例
        # 因为我们 optreturn=False，所以内层列表包含完整的策略实例
        for i, run_strategies in enumerate(results):
            # run_strategies 是一个包含单个参数组合下所有策略实例的列表 (通常对应不同的数据源)
            # 我们只需要从第一个策略实例中获取参数和分析器结果，因为参数对于同一次运行是相同的
            if not run_strategies:
                print(f"<font color='orange'>警告: 第 {i+1} 组结果为空，跳过。</font>")
                continue  # 跳过空的结果组

            strategy_instance = run_strategies[0]  # 获取第一个策略实例

            # 过滤掉不符合条件的参数组合 (例如 fast_ema >= slow_ema)
            # 从策略实例中获取参数。 (拿到这次测试用的参数。)
            params = strategy_instance.params
            if params.fast_ema_period >= params.slow_ema_period:
                # 如果快速EMA周期大于等于慢速EMA周期，则跳过这个无效组合。 (如果快线比慢线还慢或者一样，这组合没意义，跳过。)
                # print(f"跳过无效参数组合: fast_ema={params.fast_ema_period}, slow_ema={params.slow_ema_period}")
                continue  # 跳过当前循环

            try:
                # 尝试从策略实例的分析器中获取结果。 (尝试从策略的分析器里拿出计算结果。)
                # .analyzers 是策略实例的属性，后面跟分析器的 _name
                # .get_analysis() 获取分析结果字典
                sharpe_analyzer = strategy_instance.analyzers.sharpe.get_analysis()
                return_analyzer = strategy_instance.analyzers.returns.get_analysis()
                drawdown_analyzer = strategy_instance.analyzers.drawdown.get_analysis()

                # 提取关键指标，处理分析器可能未产生结果 (None) 或缺少键的情况
                # 从夏普分析结果中获取 'sharperatio'，如果不存在或为None，默认为 0.0。 (拿出夏普比率，如果没有就当是0。)
                sharpe = sharpe_analyzer.get(
                    'sharperatio', 0.0) if sharpe_analyzer else 0.0
                # 从回报率分析结果中获取 'rtot' (总复合回报率)，如果不存在或为None，默认为 0.0。 (拿出总回报率，没有就当是0。)
                total_return = return_analyzer.get(
                    'rtot', 0.0) if return_analyzer else 0.0
                # 从回撤分析结果中获取 'max' 下的 'drawdown' (最大回撤百分比)，如果不存在或为None，默认为 0.0。 (拿出最大回撤，没有就当是0。)
                max_drawdown = drawdown_analyzer.get('max', {}).get(
                    'drawdown', 0.0) if drawdown_analyzer else 0.0

                # 进一步处理 NaN (Not a Number) 值，确保用于计算的都是有效数值
                # 检查 sharpe 是否为 None 或 NaN，如果是则设为 0.0。 (如果夏普比率是无效数字，也当成0。)
                sharpe = sharpe if sharpe is not None and not math.isnan(
                    sharpe) else 0.0
                # 检查 total_return 是否为 None 或 NaN，如果是则设为 0.0。 (如果总回报是无效数字，也当成0。)
                total_return = total_return if total_return is not None and not math.isnan(
                    total_return) else 0.0
                # 检查 max_drawdown 是否为 None 或 NaN，如果是则设为 0.0。最大回撤通常是正百分比。 (如果最大回撤是无效数字，也当成0。)
                max_drawdown = max_drawdown if max_drawdown is not None and not math.isnan(
                    max_drawdown) else 0.0

                # 将有效结果及其指标存入列表
                # 把这次测试的参数、夏普比率、回报率（转为百分比）、最大回撤（已经是百分比）存起来。 (把这次测试的结果整理好放进 valid_results 列表。)
                valid_results.append({
                    'params': params,  # 参数对象
                    'sharpe': sharpe,  # 夏普比率 (原始值)
                    'return': total_return * 100,  # 总回报率 (转换为百分比)
                    'drawdown': max_drawdown  # 最大回撤 (已经是百分比)
                })
                # 将各项指标也分别存入各自的列表，用于后续计算最大最小值。 (把夏普、回报、回撤分别存到对应的列表里，方便后面找最大最小值。)
                all_sharpes.append(sharpe)
                all_returns.append(total_return * 100)
                all_drawdowns.append(max_drawdown)

            except AttributeError as e:
                # 捕获访问分析器属性时可能发生的错误 (例如分析器未成功初始化)。 (如果访问分析器出错了。)
                print(
                    f"<font color='orange'>警告: 处理第 {i+1} 组结果时跳过，无法访问分析器结果: {e}</font>")
                # 打印警告信息。 (提示一下这组结果处理不了。)
            except KeyError as e:
                # 捕获访问分析结果字典中不存在的键时发生的错误。 (如果分析结果里没有我们要的那个指标名字。)
                print(
                    f"<font color='orange'>警告: 处理第 {i+1} 组结果时跳过，分析器结果中缺少键: {e}</font>")
                # 打印警告信息。 (提示一下这组结果缺东西。)
            except Exception as e:
                # 捕获其他未预料到的错误。 (如果发生了其他奇怪的错误。)
                print(
                    f"<font color='orange'>警告: 处理第 {i+1} 组结果时发生未知错误: {e}</font>")
                # 打印通用错误警告。 (提示一下发生了未知错误。)

        if not valid_results:
            # 再次检查是否有有效的优化结果可供评分。 (检查处理完后还有没有有效的测试结果。)
            print("<font color='red'>错误：没有找到有效的优化结果进行评分。</font>")
            # 如果没有，打印错误信息并退出。 (如果没有，就报错退出。)
            return

        print(f"有效结果数量: {len(valid_results)}")
        # 打印有效结果的数量。 (告诉用户有多少个有效的测试结果。)

        # --- 指标归一化 ---
        # 计算所有有效结果中各项指标的最大值和最小值。 (找出所有测试结果里，夏普、回报、回撤的最大值和最小值。)
        min_sharpe, max_sharpe = min(all_sharpes), max(all_sharpes)
        min_return, max_return = min(all_returns), max(all_returns)
        min_drawdown, max_drawdown = min(
            all_drawdowns), max(all_drawdowns)  # 回撤是越小越好

        # 计算指标的范围 (最大值 - 最小值)，用于归一化分母。 (算出每个指标的最大波动范围。)
        # 处理最大值等于最小值的情况，避免除以零，此时范围设为 1.0。 (如果所有结果的某个指标都一样，范围就设成1，防止计算出错。)
        sharpe_range = max_sharpe - min_sharpe if max_sharpe > min_sharpe else 1.0
        return_range = max_return - min_return if max_return > min_return else 1.0
        drawdown_range = max_drawdown - min_drawdown if max_drawdown > min_drawdown else 1.0

        # --- 计算得分 ---
        scored_results = []  # 初始化用于存储带得分结果的列表。 (准备一个空列表放计算好得分的结果。)
        for res in valid_results:
            # 遍历每个有效结果。 (处理每一个有效的测试结果。)
            # --- 归一化计算 ---
            # 计算夏普比率的归一化值: (当前值 - 最小值) / 范围。 (计算夏普比率的归一化得分。)
            sharpe_norm = (res['sharpe'] - min_sharpe) / \
                sharpe_range if sharpe_range != 0 else 0.0
            # 计算回报率的归一化值: (当前值 - 最小值) / 范围。 (计算回报率的归一化得分。)
            return_norm = (res['return'] - min_return) / \
                return_range if return_range != 0 else 0.0
            # 计算原始回撤的归一化值: (当前值 - 最小值) / 范围。这个值越大表示回撤越大(越差)。 (计算原始回撤的归一化值。)
            drawdown_raw_norm = (
                res['drawdown'] - min_drawdown) / drawdown_range if drawdown_range != 0 else 0.0

            # --- 评分公式 ---
            # 应用用户指定的评分公式。 (根据公式计算综合得分。)
            # Score = w1 * Sharpe_norm + w2 * Return_norm - w3 * Drawdown_raw_norm
            score = 0.5 * sharpe_norm + 0.3 * return_norm - 0.2 * drawdown_raw_norm

            # 将计算出的得分添加到结果字典中。 (把算好的得分存到这个结果里。)
            res['score'] = score
            # 将带得分的结果添加到 scored_results 列表中。 (把这个带得分的结果加到最终列表里。)
            scored_results.append(res)

        # --- 结果排序与展示 ---
        # 根据得分 (score) 对结果进行降序排序，得分最高的排在最前面。 (把所有结果按照得分从高到低排个序。)
        best_results = sorted(
            scored_results, key=lambda x: x['score'], reverse=True)

        print("\n<font color='green'>--- 最佳参数组合 ---</font>")
        # 打印最佳参数组合的标题。 (打印一个标题，下面是最好的那组参数。)
        if best_results:
            # 如果找到了最佳结果。 (如果排序后有结果。)
            top_res = best_results[0]  # 获取得分最高的结果。 (拿出排第一的那个结果。)
            # 打印最高分。
            print(f"<font color='green'>最佳得分: {top_res['score']:.4f}</font>")
            print(f"参数:")  # 打印参数标题。
            # 打印最佳快线周期。
            print(f"  fast_ema_period: {top_res['params'].fast_ema_period}")
            # 打印最佳慢线周期。
            print(f"  slow_ema_period: {top_res['params'].slow_ema_period}")
            # 打印最佳布林带周期。
            print(f"  boll_period: {top_res['params'].boll_period}")
            # 打印最佳布林带宽度。
            print(f"  boll_devfactor: {top_res['params'].boll_devfactor:.2f}")
            print(f"指标:")  # 打印指标标题。
            # 打印各项指标的原始值和归一化值。 (打印这个最佳组合对应的夏普、回报、回撤的原始值和归一化得分。)
            print(
                f"  夏普比率 (Sharpe): {top_res['sharpe']:.4f} (归一化: {((top_res['sharpe'] - min_sharpe) / sharpe_range if sharpe_range != 0 else 0.0):.4f})")
            print(
                f"  总回报率 (Return): {top_res['return']:.2f}% (归一化: {((top_res['return'] - min_return) / return_range if return_range != 0 else 0.0):.4f})")
            print(
                f"  最大回撤 (Drawdown): {top_res['drawdown']:.2f}% (归一化: {((top_res['drawdown'] - min_drawdown) / drawdown_range if drawdown_range != 0 else 0.0):.4f})")

            # 打印排名前5的结果，方便比较。 (把排名前5的结果也打印出来看看。)
            print("\n<font color='blue'>--- 排名前 5 的参数组合 ---</font>")
            for i, res in enumerate(best_results[:5]):
                # 遍历排名前5的结果。 (循环处理前5名。)
                # 打印排名、得分和主要指标。
                print(
                    f"排名 {i+1}: 得分={res['score']:.4f}, Sharpe={res['sharpe']:.4f}, Return={res['return']:.2f}%, Drawdown={res['drawdown']:.2f}%")
                # 打印对应的参数。
                print(
                    f"   参数: fast_ema={res['params'].fast_ema_period}, slow_ema={res['params'].slow_ema_period}, boll_p={res['params'].boll_period}, boll_dev={res['params'].boll_devfactor:.2f}")

        else:
            # 如果排序后列表为空 (虽然前面有检查，但作为保险)。 (如果排完序发现一个结果都没有。)
            print("<font color='red'>未能找到有效的最佳参数组合。</font>")
            # 打印找不到最佳组合的错误信息。 (就报错说找不到最好的。)

    elif results and not run_optimization:  # 处理单次回测的结果
        # 如果是单次回测模式并且有结果。 (如果是"实战演练"模式并且跑出了结果。)
        print("\n<font color='blue'>--- 单次回测结果 ---</font>")
        # 打印单次回测结果的标题。 (打印一个标题，下面是这次回测的结果。)
        # results 是 [ [strategy] ] 结构，获取唯一的策略实例。 (拿出这次运行的策略实例。)
        strat = results[0][0]
        try:
            # 尝试从策略实例的分析器中获取各项指标。 (尝试从策略的分析器里拿出结果。)
            # .get('key', 'default') 用于安全地获取字典值，如果键不存在则返回默认值 'N/A' 或 0.0。
            sharpe = strat.analyzers.sharpe.get_analysis().get(
                'sharperatio', 'N/A')  # 获取夏普比率。
            returns = strat.analyzers.returns.get_analysis().get('rtot', 0.0) * \
                100  # 获取总回报率并转为百分比。
            drawdown = strat.analyzers.drawdown.get_analysis().get(
                'max', {}).get('drawdown', 'N/A')  # 获取最大回撤百分比。
            trade_analysis = strat.analyzers.tradeanalyzer.get_analysis()  # 获取交易分析结果。

            # 打印关键的回测摘要信息。 (打印最重要的几个回测结果。)
            print(f"最终组合价值: {cerebro.broker.getvalue():.2f}")  # 打印结束时的总资产。
            print(f"总回报率: {returns:.2f}%")  # 打印总回报率。
            # 打印夏普比率 (如果是数字才格式化)。
            print(f"夏普比率: {sharpe if isinstance(sharpe, float) else 'N/A'}")
            print(f"最大回撤: {drawdown:.2f}%" if isinstance(
                drawdown, float) else 'N/A')  # 打印最大回撤 (如果是数字才格式化)。

            if trade_analysis:
                # 如果交易分析有结果，则打印详细的交易统计。 (如果交易分析有结果，就打印详细的交易统计数据。)
                print("\n交易分析:")
                # 打印总交易次数。
                print(
                    f"  总交易次数: {trade_analysis.get('total', {}).get('total', 0)}")
                # 打印赚钱的次数。
                print(
                    f"  盈利交易次数: {trade_analysis.get('won', {}).get('total', 0)}")
                # 打印亏钱的次数。
                print(
                    f"  亏损交易次数: {trade_analysis.get('lost', {}).get('total', 0)}")
                total_trades = trade_analysis.get(
                    'total', {}).get('total', 0)  # 获取总次数，用于计算胜率。
                won_trades = trade_analysis.get(
                    'won', {}).get('total', 0)  # 获取盈利次数。
                # 计算并打印胜率。
                print(
                    f"  胜率: {won_trades / total_trades * 100:.2f}%" if total_trades > 0 else "N/A")
                avg_won = trade_analysis.get('won', {}).get(
                    'pnl', {}).get('average', 0.0)  # 获取平均每次盈利金额。
                avg_lost = trade_analysis.get('lost', {}).get(
                    'pnl', {}).get('average', 0.0)  # 获取平均每次亏损金额。
                print(f"  平均盈利: {avg_won:.2f}" if won_trades >
                      0 else "N/A")  # 打印平均盈利。
                print(f"  平均亏损: {avg_lost:.2f}" if trade_analysis.get(
                    'lost', {}).get('total', 0) > 0 else "N/A")  # 打印平均亏损。
                # 计算并打印盈亏比 (平均盈利 / 平均亏损的绝对值)。
                print(
                    f"  盈亏比: {abs(avg_won / avg_lost):.2f}" if avg_lost != 0 else "N/A")

            # --- 绘图 (仅在单次回测时进行) ---
            print("\n<font color='blue'>生成回测图表...</font>")
            # 打印生成图表的提示。 (告诉用户：开始画图了。)
            # 调用 cerebro.plot() 来绘制包含资金曲线、交易标记等的图表。 (让大脑把回测结果画出来。)
            # style='candlestick': 使用K线图样式。 (用K线图。)
            # barup='red': 上涨K线用红色。 (涨的时候是红K线。)
            # bardown='green': 下跌K线用绿色。 (跌的时候是绿K线。)
            cerebro.plot(style='candlestick', barup='red', bardown='green')

        except AttributeError as e:
            # 捕获访问分析器属性时可能发生的错误。 (如果访问分析器出错了。)
            print(f"<font color='red'>错误: 分析单次回测结果时发生错误: {e}</font>")
            # 打印错误信息。 (提示一下分析结果出错了。)
        except Exception as e:
            # 捕获处理单次回测结果时发生的其他未知错误。 (如果处理结果时发生了其他奇怪的错误。)
            print(f"<font color='red'>错误： 处理单次回测结果时发生未知错误: {e}</font>")
            # 打印通用错误信息。 (提示一下发生了未知错误。)


if __name__ == '__main__':
    # --- 配置 ---
    # 设置为 True 进行参数优化, 设置为 False 进行单次回测并绘图
    # 在这里切换模式：True 代表进行"装备测试"（优化），False 代表进行"实战演练"（单测）。 (在这里改一下就能切换模式。)
    PERFORM_OPTIMIZATION = True  # <-- !!! 在这里切换运行模式 !!!

    # --- 运行 ---
    # 确保导入了所有需要的模块。 (检查一下是不是所有需要的工具都加载了。)

    # 调用核心运行函数，并传入选择的模式。 (让 run_strategy 函数根据我们选的模式开始工作。)
    run_strategy(run_optimization=PERFORM_OPTIMIZATION)

    # --- 记忆口诀 ---
    print("\n--- 学习小口诀 ---")
    print("<font color='purple'>数据加载封装好 (load_data_feeds)，</font>")
    print("<font color='purple'>策略运行有门道 (run_strategy)。</font>")
    print("<font color='purple'>优化开关巧联动 (run_optimization -> stdstats)，</font>")
    print("<font color='purple'>参数范围细细调 (optstrategy)。</font>")
    print("<font color='purple'>分析器算指标忙 (Sharpe, Return, Drawdown)，</font>")
    print("<font color='purple'>评分排序选最强 (Score -> Sort)。</font>")
    print("<font color='purple'>单测绘图细观察 (addstrategy -> plot)，</font>")
    print("<font color='purple'>最小修改记心上！</font>")
