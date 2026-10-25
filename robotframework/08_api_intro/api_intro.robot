*** Settings ***
Documentation     项目 8：RequestsLibrary 入门——靶场 4 接口全覆盖（正向 6 + 异常 4）
Library           RequestsLibrary
Library           Collections

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Test Cases ***
创建订单返回 201 与完整字段
    ${payload}=    Create Dictionary    customer=李雷    product=机械键盘    qty=2
    ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
    Should Be Equal As Strings    ${resp.status_code}    201
    Should Be Equal As Strings    ${resp.json()["customer"]}    李雷
    Should Not Be Empty    ${resp.json()["id"]}
    Should Be True    ${resp.json()["amount"]} > 0

查询订单返回创建态
    ${payload}=    Create Dictionary    customer=查询员    product=无线鼠标
    ${created}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
    ${oid}=    Set Variable    ${created.json()["id"]}
    ${resp}=    GET    ${BASE_URL}/api/orders/${oid}    expected_status=200
    Should Be Equal As Strings    ${resp.json()["status"]}    created

支付订单流转为 paid
    ${payload}=    Create Dictionary    customer=支付员    product=显示器灯
    ${created}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
    ${oid}=    Set Variable    ${created.json()["id"]}
    ${resp}=    POST    ${BASE_URL}/api/orders/${oid}/pay    expected_status=200
    Should Be Equal As Strings    ${resp.json()["status"]}    paid

取消订单流转为 cancelled
    ${payload}=    Create Dictionary    customer=取消员    product=机械键盘
    ${created}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
    ${oid}=    Set Variable    ${created.json()["id"]}
    ${resp}=    POST    ${BASE_URL}/api/orders/${oid}/cancel    expected_status=200
    Should Be Equal As Strings    ${resp.json()["status"]}    cancelled

异常组：缺字段 422 / 不存在 404 / 重复支付 409
    ${payload}=    Create Dictionary    product=机械键盘
    ${bad}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=422
    Should Be Equal As Strings    ${bad.status_code}    422
    ${resp}=    GET    ${BASE_URL}/api/orders/ROB-not-exist    expected_status=404
    Should Be Equal As Strings    ${resp.status_code}    404
    ${payload}=    Create Dictionary    customer=重复支付员    product=显示器灯
    ${c}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
    ${oid}=    Set Variable    ${c.json()["id"]}
    POST    ${BASE_URL}/api/orders/${oid}/pay    expected_status=200
    ${again}=    POST    ${BASE_URL}/api/orders/${oid}/pay    expected_status=409
    Should Be Equal As Strings    ${again.status_code}    409
