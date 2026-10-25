"""bug03 · 时区（修复版）：显式换算到业务时区再比较。"""
from datetime import datetime
from zoneinfo import ZoneInfo

BEIJING = ZoneInfo("Asia/Shanghai")


def before_cutoff(utc_now: datetime) -> bool:
    """截单线为北京时间 23:00；判断给定 UTC 时刻是否还没到截单。"""
    local = utc_now.astimezone(BEIJING)
    cutoff = local.replace(hour=23, minute=0, second=0, microsecond=0)
    return local < cutoff
