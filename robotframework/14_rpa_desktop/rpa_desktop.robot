*** Settings ***
Documentation     项目 14：RPA——桌面应用自动化（macOS 计算器键盘流 + 剪贴板跨应用搬运）
Library           CalcBridge.py

*** Test Cases ***
计算器五道四则运算（键盘驱动 + 显示读数断言）
    打开计算器
    ${cases}=    Evaluate    {"12*3=": "36", "45+8=": "53", "9*7=": "63", "81-19=": "62", "144/12=": "12"}
    ${exprs}=    Create List    12*3=    45+8=    9*7=    81-19=    144/12=
    FOR    ${expr}    IN    @{exprs}
        计算器按键序列    ${expr}
        Sleep    400ms    # 等结果层刷新
        ${got}=    读取计算器结果
        Should Be Equal As Strings    ${got}    ${cases}[${expr}]
        ...    msg=算式 ${expr} 屏显 ${got} ≠ 期望 ${cases}[${expr}]
        Log    ${expr} → ${got} ✅
    END

剪贴板跨应用搬运
    ${token}=    Evaluate    __import__("uuid").uuid4().hex[:12]
    剪贴板写入    ${token}
    ${readback}=    剪贴板读取
    Should Be Equal    ${readback}    ${token}    msg=剪贴板写入读回不一致
    Log    剪贴板往返一致：${token} ✅
