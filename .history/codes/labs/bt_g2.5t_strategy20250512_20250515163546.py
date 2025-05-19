        # 一、数据准备
        # (这个区块主要负责从原始数据文件加载数据，并进行清洗、转换和预处理，为后续的特征工程和策略分析准备好干净、规整的数据。)
        # 一.一、加载与初步处理数据
        # (这部分是数据准备的第一步，主要是把CSV文件里的数据读进来，把日期格式弄对，然后按天整理数据，并处理掉一些缺失的数据点。)
        data = pd.read_csv(self.csv_path)
        # 从指定的CSV文件路径 `self.csv_path` 加载数据到名为 `data` 的pandas DataFrame中。
        # (好比打开一个Excel表格，把里面的内容全部读到电脑内存里，存成一个叫`data`的表格，方便后面用程序处理。)
        data['date'] = pd.to_datetime(data['date'])
        # 将 `data` DataFrame 中的 'date' 列的数据类型转换为pandas的datetime对象。
        # (表格里“日期”那一列，本来可能只是普通的文字，比如"2023-01-15"，现在把它变成程序能认得的、可以进行日期计算的专门格式。)
        data.set_index('date', inplace=True)
        # 将 'date' 列设置为 `data` DataFrame 的索引，`inplace=True` 表示直接修改原始的 `data` DataFrame。
        # (把“日期”这一列变成整个表格的行标签，以后就可以直接用日期来找某一行的数据了。`inplace=True` 的意思是这个改动直接在原来的表格上生效，不用再赋值给新的表格变量。)
        data = data.resample('D').last()
        # 将 `data` DataFrame 按照每日（'D'）的频率进行重采样，并取每日内的最后一个有效观测值。
        # (如果一天内有多条数据记录，比如股票每分钟都有价格，这条命令会把数据变成一天只有一条记录，取的是当天最后出现的那个价格数据。)
        data.fillna(method='ffill', limit=5, inplace=True)
        # 使用前向填充（'ffill'）方法填充 `data` DataFrame 中的缺失值（NaN），最多连续填充5个缺失值，`inplace=True` 表示直接修改。
        # (如果有些天的数据缺失了，就用它前一天的有效数据来填补，但如果连续缺失超过5天，就不再往前找了。这个改动也直接在原来的表格上生效。)
        data.dropna(inplace=True)
        # 删除 `data` DataFrame 中所有包含任何缺失值（NaN）的行，`inplace=True` 表示直接修改。
        # (经过前面的填充后，如果还有行存在缺失数据，就把这些不完整的行整个删掉。这个改动也直接在原来的表格上生效。)

        # 一.二、特征工程
        # (这部分是在处理好的基础数据上，计算和衍生出一些用于后续策略判断的技术指标，比如均线、RSI、MACD等。)
        data['SMA20'] = data['close'].rolling(window=20).mean()
        # 计算收盘价（'close'列）的20日简单移动平均线（SMA），并将结果存储在名为 'SMA20' 的新列中。
        # (选取“收盘价”这一列数据，计算最近20天的平均价格，把这个平均价格序列存到新的一列，命名为'SMA20'。)
        data['SMA60'] = data['close'].rolling(window=60).mean()
        # 计算收盘价（'close'列）的60日简单移动平均线（SMA），并将结果存储在名为 'SMA60' 的新列中。
        # (选取“收盘价”这一列数据，计算最近60天的平均价格，把这个平均价格序列存到新的一列，命名为'SMA60'。)
        data['RSI'] = talib.RSI(data['close'], timeperiod=14)
        # 使用TA-Lib库的RSI函数计算基于收盘价（'close'列）的14日相对强弱指数（RSI），并将结果存储在名为 'RSI' 的新列中。
        # (用一个专门的技术分析库TA-Lib来计算RSI指标，这个指标反映了最近14天价格上涨和下跌的相对强度，结果存到新的一列，命名为'RSI'。)
        macd, macdsignal, macdhist = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        # 使用TA-Lib库的MACD函数计算移动平均收敛散度指标，参数包括收盘价（'close'列）、12日快速指数移动平均线、26日慢速指数移动平均线和9日信号线。函数返回MACD线、信号线和MACD柱。
        # (还是用TA-Lib库来计算MACD指标，它由三部分组成：MACD线（快线和慢线的差值）、信号线（MACD线的移动平均）和MACD柱（MACD线和信号线的差值）。这里设置的参数是常用的12天、26天和9天。)
        data['MACD'] = macd
        # 将计算得到的MACD线赋值给 `data` DataFrame 中名为 'MACD' 的新列。
        # (把上面算出来的MACD线（通常是DIF）存到表格里，新的一列叫'MACD'。)
        data['MACDsignal'] = macdsignal
        # 将计算得到的MACD信号线赋值给 `data` DataFrame 中名为 'MACDsignal' 的新列。
        # (把上面算出来的MACD信号线（通常是DEA或DEM）存到表格里，新的一列叫'MACDsignal'。)
        upperband, middleband, lowerband = talib.BBANDS(data['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        # 使用TA-Lib库的BBANDS函数计算布林带指标，参数包括收盘价（'close'列）、20日时间周期、上下轨分别为2倍标准差，移动平均类型为简单移动平均（matype=0）。函数返回上轨、中轨和下轨。
        # (用TA-Lib库计算布林带，它由三条线组成：中轨（一般是20日均线）、上轨（中轨+2倍标准差）和下轨（中轨-2倍标准差）。)
        data['UpperBand'] = upperband
        # 将计算得到的布林带上轨赋值给 `data` DataFrame 中名为 'UpperBand' 的新列。
        # (把上面算出来的布林带的上线存到表格里，新的一列叫'UpperBand'。)
        data['LowerBand'] = lowerband
        # 将计算得到的布林带下轨赋值给 `data` DataFrame 中名为 'LowerBand' 的新列。
        # (把上面算出来的布林带的下线存到表格里，新的一列叫'LowerBand'。)
        data.dropna(inplace=True)
        # 删除 `data` DataFrame 中因特征工程计算（如滚动窗口导致期初数据不足）而产生的任何包含缺失值（NaN）的行，`inplace=True` 表示直接修改。
        # (因为计算移动平均这类指标时，开始的几天数据量不够，会产生无效值（NaN），这里就把这些带有无效值的行删掉。这个改动也直接在原来的表格上生效。)

        # 二、策略逻辑定义
        # (这个区块基于前面计算出的技术指标，定义具体的买入和卖出信号规则。)
        data['signal'] = 0
        # 在 `data` DataFrame 中初始化名为 'signal' 的新列，并将其所有值设置为0，代表初始无交易信号或持有状态。
        # (新建一列叫做'signal'，里面先全部填上0。0通常表示“不操作”或者“继续持有当前仓位”。)
        data.loc[(data['SMA20'] > data['SMA60']) & (data['RSI'] < 70), 'signal'] = 1
        # 根据条件设置买入信号：当20日均线（SMA20）大于60日均线（SMA60） 并且 14日相对强弱指数（RSI）小于70时，将 'signal' 列的对应位置设为1（买入）。
        # (定一个买入的规矩：如果20天平均价格高过60天平均价格（金叉），并且RSI指标显示市场不是过热（小于70），那么就在'signal'列的对应日期标记为1，表示“买入”。)
        data.loc[(data['SMA20'] < data['SMA60']) | (data['RSI'] > 70), 'signal'] = -1
        # 根据条件设置卖出信号：当20日均线（SMA20）小于60日均线（SMA60） 或者 14日相对强弱指数（RSI）大于70时，将 'signal' 列的对应位置设为-1（卖出）。
        # (定一个卖出的规矩：如果20天平均价格低于60天平均价格（死叉），或者RSI指标显示市场可能过热（大于70），那么就在'signal'列的对应日期标记为-1，表示“卖出”。)

        # 三、回测与收益计算
        # (这个区块根据前面产生的交易信号，模拟实际交易过程，并计算策略的收益表现以及与基准（如一直持有）的对比。)
        data['returns'] = data['close'].pct_change()
        # 计算每日收盘价（'close'列）的百分比变化（即每日收益率），并将结果存储在名为 'returns' 的新列中。
        # (算一下如果一直持有这个资产，每天的涨跌幅是多少，结果存到新的一列，命名为'returns'。)
        data['strategy_returns'] = data['returns'] * data['signal'].shift(1)
        # 计算策略的每日收益率：将资产的每日收益率（'returns'）与前一日的交易信号（'signal'列的值向前移动一位 `.shift(1)`）相乘。
        # (根据我们定义的买卖信号来计算策略每天的收益。这里用`.shift(1)`是因为我们通常是根据前一天的信号来决定今天的操作，所以今天的收益是今天资产的涨跌幅乘以昨天给出的信号。)
        data.dropna(inplace=True)
        # 删除 `data` DataFrame 中因计算收益率（pct_change）或信号移位（shift）可能引入的包含缺失值（NaN）的行，`inplace=True` 表示直接修改。
        # (因为计算每日收益率时第一天没有前期数据，信号移位也会在第一行产生NaN，所以这里把这些带有无效值的行删掉。这个改动也直接在原来的表格上生效。)

        data['cumulative_returns'] = (1 + data['returns']).cumprod()
        # 计算资产的累积收益率：将每日收益率（'returns'）加1后进行累乘，并将结果存储在名为 'cumulative_returns' 的新列中。
        # (算一下如果从一开始就买入并一直持有这个资产，到每天结束时总共的累计收益是多少倍，结果存到新的一列，命名为'cumulative_returns'。)
        data['cumulative_strategy_returns'] = (1 + data['strategy_returns']).cumprod()
        # 计算策略的累积收益率：将策略的每日收益率（'strategy_returns'）加1后进行累乘，并将结果存储在名为 'cumulative_strategy_returns' 的新列中。
        # (算一下如果从一开始就按照我们定义的交易信号进行买卖，到每天结束时总共的累计收益是多少倍，结果存到新的一列，命名为'cumulative_strategy_returns'。)
