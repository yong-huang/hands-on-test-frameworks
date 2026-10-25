*** Settings ***
Documentation     板斧一：[Template] 模板关键字——数据写在用例表里
Resource          resources/orders.resource
Library           Collections

*** Test Cases ***
模板下单（含负向组）
    [Template]    下单并断言
    # customer        product      expected
    李雷              机械键盘      201
    Alice ⚡          无线鼠标      201
    佐藤太郎          显示器灯      201
    ${EMPTY}          机械键盘      422
    Klaus Müller      ${EMPTY}      422
