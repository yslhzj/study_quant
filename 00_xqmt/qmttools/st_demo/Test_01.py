from xtquant import xtdata
from datetime import datetime

# 定义日期时间格式
date_format = "%Y%m%d%H%M%S"

# 创建一个日期时间字符串
date_string = "20230101093000"

# 转换为时间戳
timestamp = xtdata.datetime_to_timetag(date_string, date_format)

print(f"时间戳: {timestamp} (类型: {type(timestamp)})")