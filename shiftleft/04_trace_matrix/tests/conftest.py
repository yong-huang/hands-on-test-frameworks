"""本目录回归测试的环境钩子。

关键顺序：SUT_DB 环境变量必须在 import labs/11 的 main 之前设置——
main.py 在 import 时就把 DB_PATH 冻结（os.environ.get 的求值时机），
设晚了会写进 labs/11 的共享 orders.db。这就是「共有资产只读」的实现方式：
测试打的是同一份应用代码，落到本实验目录下的临时库。
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABS_APP = ROOT.parent.parent / "labs/11_sut_app/app"
TMP_DB = ROOT / ".orders_tmp.db"

os.environ["SUT_DB"] = str(TMP_DB)
sys.path.insert(0, str(LABS_APP))
