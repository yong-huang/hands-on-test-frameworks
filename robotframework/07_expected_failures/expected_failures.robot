*** Settings ***
Documentation     项目 7：期望失败与失败留证——负向用例「按预期红」+ Teardown 截图
Library           RequestsLibrary
Library           SeleniumLibrary
Library           Collections
Suite Setup       Log    靶场由 07_expected_failures.sh apply 拉起

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Test Cases ***
负向一：空客户下单被 422 拒绝
    ${payload}=    Create Dictionary    product=机械键盘
    ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=422
    Should Be Equal As Strings    ${resp.status_code}    422
    Dictionary Should Contain Key    ${resp.json()}    error

负向二：UI 空表单提交不出订单
    Open Browser    ${BASE_URL}    headlesschrome
    Wait Until Page Contains Element    id:submit-btn    timeout=10s
    Click Button    id:submit-btn    # 客户为空，服务端 422，页面不会出现订单号
    Sleep    500ms    # 给 fetch 留返回窗口
    ${order_text}=    Get Text    id:order-id
    Should Contain    ${order_text}    下单失败    # 空客户被服务端 422 拒绝，页面给出失败提示
    Should Not Contain    ${order_text}    ROB-
    [Teardown]    Close Browser

负向三：缺失元素按预期报错（Run Keyword And Expect Error）
    Open Browser    ${BASE_URL}    headlesschrome
    Run Keyword And Expect Error    *with locator 'id:no-such-thing' not found*    Element Text Should Be    id:no-such-thing    x
    [Teardown]    Close Browser

负向四：TRY/EXCEPT/FINALLY——FINALLY 必达
    ${finally_ran}=    Set Variable    ${FALSE}
    TRY
        Fail    预期失败：演示 FINALLY
    EXCEPT    AS    ${err}
        Log    已捕获：${err}
    FINALLY
        ${finally_ran}=    Set Variable    ${TRUE}
    END
    Should Be True    ${finally_ran}
    Should Contain    ${err}    预期失败

留证演示：故意失败触发 Teardown 截图
    Open Browser    ${BASE_URL}    headlesschrome
    Wait Until Page Contains Element    id:customer    timeout=10s
    # ❌ 注入的失败：断言一个不存在的元素，让 Teardown 截图有活干
    Element Should Contain    id:customer    这行文字永远不存在
    [Teardown]    Run Keywords    Capture Page Screenshot    AND    Close Browser
