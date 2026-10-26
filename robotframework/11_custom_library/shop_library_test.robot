*** Settings ***
Documentation     项目 11：自定义 Python 关键字库 ShopLibrary——造轮子与用轮子
Library           ShopLibrary.py
Library           Collections

*** Test Cases ***
生成订单号前缀唯一且带环境段
    ${p1}=    生成订单号前缀    test
    ${p2}=    生成订单号前缀    test
    Should Start With    ${p1}    test-
    Should Not Be Equal    ${p1}    ${p2}    # 唯一性：两次生成必不同

金额校验：合法通过 / 非法红
    ${v}=    校验金额    19.90
    Should Be Equal As Numbers    ${v}    19.90
    ${ok}=    Run Keyword And Return Status    校验金额    abc
    Should Not Be True    ${ok}    # 非数字应红
    ${ok}=    Run Keyword And Return Status    校验金额    -3.00
    Should Not Be True    ${ok}    # 非正数应红
    ${ok}=    Run Keyword And Return Status    校验金额    1.999
    Should Not Be True    ${ok}    # 超两位小数应红

测试数据工厂带唯一毫秒后缀
    ${d1}=    生成测试数据    李雷    北京市海淀区
    ${d2}=    生成测试数据    李雷    北京市海淀区
    Should Not Be Equal    ${d1}[customer]    ${d2}[customer]
    Should Contain    ${d1}[customer]    李雷-

签名计算与一致性断言
    ${payload}=    Create Dictionary    customer=李雷    amount=19.90
    ${sig}=    计算签名    ${payload}    my-secret
    Should Contain    ${sig}    ${EMPTY}    # 形如 hex 串
    断言签名一致    ${payload}    my-secret    ${sig}
    ${ok}=    Run Keyword And Return Status    断言签名一致    ${payload}    wrong-secret    ${sig}
    Should Not Be True    ${ok}    # 密钥错误应红
