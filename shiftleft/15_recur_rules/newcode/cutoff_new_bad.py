"""拦截目标：写法全新的同类缺陷——now() 裸奔无时区（bug03 再世）。"""
from datetime import datetime


def is_promo_alive(deadline_hour: int) -> bool:
    return datetime.now().hour < deadline_hour  # 同类缺陷：naive now
