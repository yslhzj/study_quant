def analyze_optimization_results(results):
    # 定义一个函数，用于分析优化结果
    # (这个函数是用来分析跑完策略优化后得到的一堆结果的)

    print("\n{:*^50}")
    # 打印一行由50个星号组成的分割线，用于视觉分隔
    # (在屏幕上打一行星星，好看一点，方便区分不同的输出内容)
    pprint.pprint(results)
    # 使用pprint模块的pprint函数格式化打印优化结果列表
    # (把优化跑出来的原始结果，用一种比较好看的方式打印出来瞅瞅)

    print("\n{:*^50}")
    # 再次打印一行由50个星号组成的分割线
    # (又打一行星星，跟上面的对应)
    """
    分析优化结果，计算归一化得分并找到最优参数。
    Analyzes optimization results, calculates normalized scores, and finds the best parameters.

    Args:
        results (list): cerebro.run() 返回的优化结果列表。 (List of optimization results returned by cerebro.run().)

    Returns:
        tuple: 包含最佳策略实例和所有结果得分的元组。 (Tuple containing the best strategy instance and scores for all results.)
               如果无法处理，则返回 (None, [])。 (Returns (None, []) if results cannot be processed.)
    """
    if not results:
        # 检查优化结果列表是否为空
        # (看看是不是啥结果都没有)
        print("\n{:!^50}".format(' 错误 '))
        # 打印错误提示信息的标题，使用感叹号填充居中
        # (如果没结果，就打个大大的“错误”标题)
        print("没有策略成功运行。请检查数据加载是否有误或参数范围是否有效。")
        # 打印具体的错误信息
        # (告诉用户可能是数据没加载对，或者参数设置有问题，导致一个策略都没跑成功)
        print('!' * 50)
        # 打印一行由50个感叹号组成的分割线
        # (再打一行感叹号，强调一下错误)
        return None, []
        # 如果结果为空，则返回 None 和一个空列表
        # (既然没结果，就返回个空的东西，表示没法分析)

    processed_results = []
    # 初始化一个空列表，用于存储处理后的结果
    # (准备一个空篮子，待会儿把整理好的每个策略的结果放进去)
    print("\n--- 开始提取分析结果 ---")
    # 打印信息，提示开始提取分析结果
    # (告诉用户，现在要开始从原始结果里把有用的信息挑出来了)

    run_count = 0
    # 初始化运行计数器为0
    # (记一下总共跑了多少个参数组合)
    successful_runs = 0
    # 初始化成功提取结果的运行计数器为0
    # (记一下有多少个参数组合是成功提取出分析数据的)
    for strat_list in results:
        # 遍历优化结果列表中的每一个策略运行结果列表
        # (优化的时候，每个参数组合跑完会生成一个小列表，我们一个个来看这些小列表)
        run_count += 1
        # 运行计数器加1
        # (每看一个，总数就加一)
        if not strat_list:
            # 检查当前策略运行结果列表是否为空
            # (看看这个参数组合跑完有没有结果，有时候可能会是空的)
            continue
            # 如果为空，则跳过当前循环，处理下一个结果
            # (要是空的，就不处理了，直接看下一个)

        strategy_instance = strat_list[0]
        # 获取策略实例，通常是列表中的第一个元素
        # (每个小列表里第一个东西就是策略本身的一些信息)
        params = strategy_instance.params
        # 获取策略实例的参数
        # (从策略信息里拿到这次跑的参数是啥)
        analyzers = strategy_instance.analyzers
        # 获取策略实例的分析器
        # (从策略信息里拿到分析器，里面有夏普率、收益这些数据)

        params_str_parts = []
        # 初始化一个空列表，用于存储参数键值对字符串
        # (准备一个空列表，用来放“参数名=参数值”这样的字符串)

        optimized_param_names = [
            'etf_type', 'ema_medium_period', 'ema_long_period',
            'bbands_period', 'bbands_devfactor', 'trend_stop_loss_atr_mult',
            'range_stop_loss_buffer',
            'risk_per_trade_trend',
            'risk_per_trade_range'
        ]
        # 定义一个列表，包含所有参与优化的参数名称
        # (列出我们这次优化都调整了哪些参数，比如ETF类型、均线周期、布林带参数等等)
        for p_name in optimized_param_names:
            # 遍历预定义的优化参数名称列表
            # (一个个地看这些我们关心的参数)
            if hasattr(params, p_name):
                # 检查当前参数对象是否具有名为 p_name 的属性
                # (看看这个策略跑的时候，有没有用到这个参数)
                params_str_parts.append(f"{p_name}={getattr(params, p_name)}")
                # 如果存在该属性，则将其键值对格式化后添加到列表中
                # (有的话，就把它和它的值拼成“参数名=值”的样子，加到列表里)
            else:
                # 如果参数对象没有名为 p_name 的属性
                # (要是没这个参数)
                params_str_parts.append(f"{p_name}=MISSING")
                # 则添加一个表示该参数缺失的字符串
                # (就记一个“参数名=MISSING”，表示这个参数没找到)
        params_str = ", ".join(params_str_parts)
        # 使用逗号和空格将列表中的所有参数字符串连接成一个单一的字符串
        # (把列表里所有的“参数名=值”用逗号隔开，拼成一个长字符串，方便看)

        try:
            # 开始一个 try 块，用于捕获提取分析结果时可能发生的错误
            # (尝试一下提取数据，因为有时候可能会出错)

            sharpe_analysis = analyzers.sharpe_ratio.get_analysis()
            # 从分析器中获取夏普比率的分析结果
            # (从分析器里拿出夏普比率相关的数据)
            returns_analysis = analyzers.returns.get_analysis()
            # 从分析器中获取收益率的分析结果
            # (从分析器里拿出总收益相关的数据)
            drawdown_analysis = analyzers.drawdown.get_analysis()
            # 从分析器中获取最大回撤的分析结果
            # (从分析器里拿出最大亏损（回撤）相关的数据)

            valid_analysis = True
            # 初始化分析结果有效性标志为 True
            # (先假设分析结果是好的)

            if not sharpe_analysis or 'sharperatio' not in sharpe_analysis:
                # 检查夏普比率分析结果是否为空或不包含 'sharperatio' 键
                # (看看夏普比率的数据是不是空的，或者里面没有我们要的 'sharperatio' 这个值)
                valid_analysis = False
                # 如果条件为真，则将有效性标志设为 False
                # (如果是，那这个分析结果就不算好)
            if not returns_analysis or 'rtot' not in returns_analysis:
                # 检查收益率分析结果是否为空或不包含 'rtot' 键
                # (看看总收益的数据是不是空的，或者里面没有我们要的 'rtot' 这个值)
                valid_analysis = False
                # 如果条件为真，则将有效性标志设为 False
                # (如果是，那这个分析结果也不算好)
            if not drawdown_analysis or 'max' not in drawdown_analysis or 'drawdown' not in drawdown_analysis.get('max', {}):
                # 检查回撤分析结果是否为空，或不包含 'max' 键，或 'max' 字典中不包含 'drawdown' 键
                # (看看最大回撤的数据是不是空的，或者里面没有 'max'，或者 'max' 里面没有 'drawdown' 这个值)
                valid_analysis = False
                # 如果条件为真，则将有效性标志设为 False
                # (如果是，那这个分析结果还是不算好)

            if not valid_analysis:
                # 如果分析结果被标记为无效
                # (如果前面检查发现分析结果有问题)

                continue
                # 则跳过当前参数组的处理，继续下一个循环
                # (那这个参数组合就不分析了，直接看下一个)

            sharpe = sharpe_analysis.get('sharperatio')
            # 从夏普比率分析结果中获取 'sharperatio' 的值
            # (拿到夏普比率的值)

            if sharpe is None:
                # 如果获取到的夏普比率为 None
                # (万一夏普比率没取到，是个 None)
                sharpe = 0.0
                # 则将其设置为 0.0
                # (就当它是0吧)

            total_return = returns_analysis.get('rtot', 0.0)
            # 从收益率分析结果中获取 'rtot' 的值，如果不存在则默认为 0.0
            # (拿到总收益率，要是没有就当是0)

            max_drawdown = drawdown_analysis.get(
                'max', {}).get('drawdown', 0.0) / 100.0
            # 从回撤分析结果中获取 'max'字典下的 'drawdown' 值，如果不存在则默认为0.0，然后除以100转换为小数
            # (拿到最大回撤值，它原来是百分比的数字，比如20代表20%，我们把它变成0.2这样的小数)

            current_params_dict = {}
            # 初始化一个空字典，用于存储当前参数组的参数键值对
            # (准备一个字典，把当前这组参数存起来)

            for p_name in optimized_param_names:
                # 遍历预定义的优化参数名称列表
                # (再看一遍我们关心的那些参数名)
                if hasattr(params, p_name):
                    # 检查当前参数对象是否具有名为 p_name 的属性
                    # (看看这个策略跑的时候，有没有用到这个参数)
                    current_params_dict[p_name] = getattr(params, p_name)
                    # 如果存在，则将参数名作为键，参数值作为值，存入字典
                    # (有的话，就存到字典里，比如 'ema_period': 20)
                else:
                    # 如果参数对象没有名为 p_name 的属性
                    # (要是没这个参数)
                    current_params_dict[p_name] = 'MISSING_IN_PARAMS_OBJ'
                    # 则将参数名作为键，值为 'MISSING_IN_PARAMS_OBJ' 存入字典
                    # (就在字典里记一下这个参数缺失了)

            processed_results.append({
                'instance': strategy_instance,
                'params_dict': current_params_dict,
                'sharpe': sharpe,
                'return': total_return,
                'drawdown': max_drawdown
            })
            # 将当前参数组的分析结果(策略实例、参数字典、夏普比率、总回报、最大回撤)打包成字典并添加到 processed_results 列表中
            # (把这个策略实例、它的参数、算出来的夏普、收益、回撤都打包成一个字典，放到我们之前准备的篮子里)
            successful_runs += 1
            # 成功处理的运行次数加1
            # (成功处理完一个，计数加一)

        except AttributeError as e:
            # 捕获属性错误（AttributeError），通常发生在尝试访问不存在的属性时
            # (如果在尝试拿分析器数据的时候，发现某个东西没有，比如 analyzers.sharpe_ratio 根本不存在)

            pass
            # 捕获错误后不执行任何操作，直接跳过
            # (出错了就出错了吧，不影响处理下一个，这里就先不管它)

        except Exception as e:
            # 捕获所有其他类型的异常
            # (如果发生了其他类型的错误)

            import traceback
            # 导入 traceback 模块，用于打印详细的错误堆栈信息
            # (引入一个工具，能帮我们看错误出在哪儿)

            pass
            # 捕获错误后不执行任何操作，直接跳过
            # (同样，出错了也先不管，继续处理其他的)

    print(f"--- 完成提取分析。总运行次数: {run_count}, 成功提取结果: {successful_runs} ---")
    # 打印提取分析完成的信息，包括总运行次数和成功提取结果的次数
    # (告诉用户，数据都看完了，总共看了多少个参数组合，成功整理了多少个)

    if not processed_results:
        # 检查处理后的结果列表是否为空
        # (如果忙活了半天，一个有用的结果都没整理出来)
        print("\n错误：未能成功提取任何有效的分析结果。无法进行评分。")
        # 打印错误信息
        # (就告诉用户，没拿到有效数据，没法打分了)
        return None, []
        # 返回 None 和一个空列表
        # (返回空东西，表示分析失败)

    all_sharpes = [r['sharpe'] for r in processed_results]
    # 使用列表推导式从 processed_results 列表中提取所有结果的夏普比率
    # (把所有整理好的结果里的夏普比率都拿出来，放一个列表里)

    all_returns = [r['return'] for r in processed_results]
    # 使用列表推导式从 processed_results 列表中提取所有结果的总收益率
    # (把所有整理好的结果里的总收益率都拿出来，放一个列表里)

    all_drawdowns = [r['drawdown'] for r in processed_results]
    # 使用列表推导式从 processed_results 列表中提取所有结果的最大回撤
    # (把所有整理好的结果里的最大回撤都拿出来，放一个列表里)

    min_sharpe = min(all_sharpes) if all_sharpes else 0.0
    # 计算所有夏普比率中的最小值，如果列表为空则默认为 0.0
    # (找出所有夏普比率里最小的那个，要是列表是空的，就当最小是0)

    max_sharpe = max(all_sharpes) if all_sharpes else 0.0
    # 计算所有夏普比率中的最大值，如果列表为空则默认为 0.0
    # (找出所有夏普比率里最大的那个，要是列表是空的，就当最大是0)

    min_return = min(all_returns) if all_returns else 0.0
    # 计算所有总收益率中的最小值，如果列表为空则默认为 0.0
    # (找出所有总收益率里最小的那个，要是列表是空的，就当最小是0)

    max_return = max(all_returns) if all_returns else 0.0
    # 计算所有总收益率中的最大值，如果列表为空则默认为 0.0
    # (找出所有总收益率里最大的那个，要是列表是空的，就当最大是0)

    min_drawdown = min(all_drawdowns) if all_drawdowns else 0.0
    # 计算所有最大回撤中的最小值，如果列表为空则默认为 0.0
    # (找出所有最大回撤里最小的那个，要是列表是空的，就当最小是0)

    max_drawdown_val = max(all_drawdowns) if all_drawdowns else 0.0
    # 计算所有最大回撤中的最大值，如果列表为空则默认为 0.0 (变量名用 max_drawdown_val 避免与内置函数 max 冲突)
    # (找出所有最大回撤里最大的那个，要是列表是空的，就当最大是0)

    best_score = float('-inf')
    # 初始化最佳得分为负无穷大
    # (先假设最好的分数是负无穷，这样随便一个分数都比它大，方便后面比较更新)

    best_result_data = None
    # 初始化最佳结果数据为 None
    # (先假设还没有找到最好的结果)

    scored_results = []
    # 初始化一个空列表，用于存储带得分的策略结果
    # (准备一个空列表，用来放所有计算过得分的策略结果)

    print("\n--- 开始计算归一化得分 ---")
    # 打印信息，提示开始计算归一化得分
    # (告诉用户，现在要开始给每个策略结果打分了，打分前会先做个标准化处理)

    print(f"Min/Max - Sharpe: ({min_sharpe:.4f}, {max_sharpe:.4f}), Return: ({min_return:.4f}, {max_return:.4f}), Drawdown: ({min_drawdown:.4f}, {max_drawdown_val:.4f})")
    # 打印各指标（夏普、收益、回撤）的最小值和最大值，格式化为4位小数
    # (把刚才算出来的夏普、收益、回撤的最大最小值都打印出来看看，心里有个数)

    for result_data in processed_results:
        # 遍历所有已处理的策略结果数据
        # (一个个地看我们之前整理好的那些策略结果)

        sharpe = result_data['sharpe']
        # 从当前结果数据中获取夏普比率
        # (拿出这个结果的夏普比率)

        ret = result_data['return']
        # 从当前结果数据中获取总收益率
        # (拿出这个结果的总收益率)

        dd = result_data['drawdown']
        # 从当前结果数据中获取最大回撤
        # (拿出这个结果的最大回撤)

        sharpe_range = max_sharpe - min_sharpe
        # 计算夏普比率的最大值与最小值之差（即范围）
        # (算一下所有夏普比率的最大值和最小值的差距有多大)

        return_range = max_return - min_return
        # 计算总收益率的最大值与最小值之差（即范围）
        # (算一下所有总收益率的最大值和最小值的差距有多大)

        drawdown_range = max_drawdown_val - min_drawdown
        # 计算最大回撤的最大值与最小值之差（即范围）
        # (算一下所有最大回撤的最大值和最小值的差距有多大)

        sharpe_norm = (sharpe - min_sharpe) / \
            sharpe_range if sharpe_range > 1e-9 else 0.0
        # 归一化夏普比率：(当前值 - 最小值) / 范围。如果范围过小（接近0），则归一化值为0
        # (把当前的夏普比率，按照它在所有夏普比率里的位置，换算成一个0到1之间的数。如果所有夏普都差不多一样，就直接给0)

        return_norm = (ret - min_return) / \
            return_range if return_range > 1e-9 else 0.0
        # 归一化总收益率：(当前值 - 最小值) / 范围。如果范围过小，则归一化值为0
        # (同样的方法，把总收益率也换算成0到1之间的数)

        drawdown_norm = (dd - min_drawdown) / \
            drawdown_range if drawdown_range > 1e-9 else 0.0
        # 归一化最大回撤：(当前值 - 最小值) / 范围。如果范围过小，则归一化值为0
        # (最大回撤也一样，换算成0到1之间的数)

        score = 0.6 * sharpe_norm + 0.1 * return_norm - 0.3 * drawdown_norm
        # 计算综合得分：夏普比率权重0.6，收益率权重0.1，回撤权重-0.3 (回撤是负向指标)
        # (给这个策略打个总分：标准化的夏普比率占60%，标准化的收益率占10%，标准化的回撤扣30%的分，因为回撤越小越好)

        result_data['score'] = score
        # 将计算出的综合得分添加到当前结果数据字典中
        # (把算出来的总分，存到这个策略结果里)

        scored_results.append(result_data)
        # 将带有得分的当前结果数据添加到 scored_results 列表中
        # (把这个包含了参数、各项指标和总分的策略结果，加到打分结果列表里)

        if score > best_score:
            # 如果当前计算的得分高于已知的最佳得分
            # (如果这个策略的总分比我们目前见过的最高分还要高)

            best_score = score
            # 更新最佳得分为当前得分
            # (那这个分数就是新的最高分)

            best_result_data = result_data
            # 更新最佳结果数据为当前的策略结果数据
            # (这个策略就是目前最好的策略)

    print(f"--- 完成 {len(scored_results)} 组得分计算 ---")
    # 打印得分计算完成的信息，并显示总共计算了多少组结果的得分
    # (告诉用户，所有策略都打完分了，总共打了多少个)

    return best_result_data, scored_results
    # 返回最佳结果数据和所有带得分的结果列表
    # (把找到的最好策略的结果，以及所有策略的打分结果，都返回出去)
