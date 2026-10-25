*** Settings ***
Documentation     项目 10：API 造数 → Web 页面逐笔验证支付 → API 复核流转 → 清理零残留
Library           RequestsLibrary
Library           Collections
Library           SeleniumLibrary
Suite Teardown    清理全部造数订单

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952
@{ORDER_IDS}      ${EMPTY}    ${EMPTY}    ${EMPTY}    # Suite 级：3 笔造数订单号（Teardown 清理用）

*** Test Cases ***
API 批量创建 3 笔订单
    ${ids}=    Create List
    FOR    ${i}    IN RANGE    3
        ${payload}=    Create Dictionary    customer=混合场景员-${i}    product=机械键盘
        ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
        Append To List    ${ids}    ${resp.json()["id"]}
    END
    Set Suite Variable    @{ORDER_IDS}    @{ids}
    Length Should Be    ${ORDER_IDS}    3

Web 页面逐笔查询并支付
    Open Browser    ${BASE_URL}/orders.html    headlesschrome
    Wait Until Page Contains Element    id:oid    timeout=10s
    FOR    ${oid}    IN    @{ORDER_IDS}
        Input Text    id:oid    ${oid}
        Click Button    id:query-btn
        Wait Until Page Contains    ${oid}    timeout=10s    # 等本轮唯一订单号（公前缀会被旧内容假命中）
        Element Should Contain    id:detail    created
        Click Button    id:pay-btn
        Wait Until Page Contains    "status": "paid"    timeout=10s
        Element Should Contain    id:detail    "status": "paid"
    END
    [Teardown]    Close Browser

API 复核三笔全部 paid
    FOR    ${oid}    IN    @{ORDER_IDS}
        ${resp}=    GET    ${BASE_URL}/api/orders/${oid}    expected_status=200
        Should Be Equal As Strings    ${resp.json()["status"]}    paid
    END

*** Keywords ***
清理全部造数订单
    [Documentation]    造数收尾：created 状态的取消掉，任何订单不得以 created 残留
    FOR    ${oid}    IN    @{ORDER_IDS}
        ${resp}=    GET    ${BASE_URL}/api/orders/${oid}    expected_status=any
        IF    '${resp.json()["status"]}' == 'created'
            POST    ${BASE_URL}/api/orders/${oid}/cancel    expected_status=any
        END
        ${after}=    GET    ${BASE_URL}/api/orders/${oid}    expected_status=200
        Should Not Be Equal As Strings    ${after.json()["status"]}    created
    END
