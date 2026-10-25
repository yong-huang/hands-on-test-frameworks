*** Settings ***
Documentation     靶场业务关键字层：测试用例只说业务语言，定位与请求细节都住这里
Library           RequestsLibrary
Library           SeleniumLibrary

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Keywords ***
打开靶场首页
    [Documentation]    打开下单页并等待表单就绪（浏览器变量由调用方给）
    [Arguments]    ${browser}=headlesschrome
    Open Browser    ${BASE_URL}    ${browser}
    Wait Until Page Contains Element    id=submit-btn    timeout=10s

创建订单
    [Documentation]    调靶场创建订单接口，返回响应对象
    [Arguments]    ${customer}    ${product}    ${qty}=1
    ${payload}=    Create Dictionary    customer=${customer}    product=${product}    qty=${qty}
    ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}
    RETURN    ${resp}

查询订单
    [Documentation]    按订单号查询，返回响应对象
    [Arguments]    ${order_id}
    ${resp}=    GET    ${BASE_URL}/api/orders/${order_id}
    RETURN    ${resp}
