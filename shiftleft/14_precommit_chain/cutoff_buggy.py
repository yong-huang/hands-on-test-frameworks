"""bug03 · 时区（缺陷版）：拿 UTC 的小时数当北京时间的小时数比——naive 时区思维。"""
from datetime import datetime


def before_cutoff(utc_now: datetime) -> bool:
    """截单线为北京时间 23:00；判断给定 UTC 时刻是否还没到截单。"""
    return utc_now.hour < 23  # 缺陷：UTC 15:30 实为北京 23:30，早过了截单
