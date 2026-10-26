"""calc_bridge.py — macOS 计算器桌面自动化的关键字库（osascript/System Events 桥）。

环境链说明：RPA.Desktop 的图像定位对分辨率敏感、RPA.Windows 以 Windows 为主——
macOS 上最稳的桌面通道是 System Events 的辅助功能 API（键盘事件 + UI 树读值），
本库把它桥成 Robot 关键字。前置：终端/宿主需有「辅助功能」权限。
"""
import subprocess
import time

from robot.api.deco import keyword


def _osa(script: str) -> str:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError(f"AppleScript 失败：{r.stderr.strip()[:200]}")
    return r.stdout.strip()


DISPLAY_RESULT = ('tell application "System Events" to tell process "Calculator" '
                  "to get value of static text 1 of scroll area 2 of group 1 of group 1 "
                  "of splitter group 1 of group 1 of window 1")


class CalcBridge:

    @keyword("打开计算器")
    def open_calculator(self) -> None:
        """前台激活 macOS 计算器（读数与键盘事件都要求前台）。"""
        _osa('tell application "Calculator" to activate')
        time.sleep(0.8)

    @keyword("计算器按键序列")
    def calc_keys(self, expr: str) -> None:
        """向计算器发送一段键击序列（数字/运算符/回车用字符串表示）。"""
        _osa(
            'tell application "System Events"\n'
            f'  keystroke "{expr}"\n'
            "end tell"
        )

    @keyword("按步骤计算")
    def calc_stepwise(self, steps: list) -> None:
        """按步骤发送键击（列表每项一步，步间 300ms），供分步断言使用。"""
        for s in steps:
            _osa(
                'tell application "System Events"\n'
                f'  keystroke "{s}"\n'
                "end tell"
            )
            time.sleep(0.3)

    @keyword("读取计算器结果")
    def read_result(self) -> str:
        """读取计算器显示屏的结果层（返回去掉全角空格的字符串）。"""
        raw = _osa(DISPLAY_RESULT)
        return raw.replace("\u200e", "").strip()

    @keyword("剪贴板写入")
    def clipboard_set(self, text: str) -> None:
        """把文本写入剪贴板（RPA.Clipboard 的 osascript 等价实现）。"""
        _osa(f'set the clipboard to "{text}"')

    @keyword("剪贴板读取")
    def clipboard_get(self) -> str:
        """读取剪贴板文本。"""
        return _osa("the clipboard")
