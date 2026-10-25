*** Settings ***
Documentation     项目 2：关键字宇宙与变量体系——业务语言测试层 + FOR/IF 组合
Resource          resources/shop.resource
Library           Collections

*** Variables ***
${GREETING}       这是标量变量
@{PRODUCTS}       机械键盘    无线鼠标    显示器灯
&{DEFAULTS}       qty=2    channel=web

*** Test Cases ***
业务语言下单（关键字下沉验证）
    [Documentation]    用例层只剩业务语言：打开/创建/查询，细节全在 resource
    打开靶场首页
    ${resp}=    创建订单    李雷    ${PRODUCTS}[0]
    Should Be Equal As Strings    ${resp.status_code}    201
    ${order_id}=    Set Variable    ${resp.json()["id"]}
    ${query}=    查询订单    ${order_id}
    Should Be Equal As Strings    ${query.json()["status"]}    created
    [Teardown]    Close Browser

FOR 与 IF 组合演示
    [Documentation]    批量下单两件商品（跳过第三件），验证返回 2 个订单号
    @{created}=    Create List
    FOR    ${p}    IN    @{PRODUCTS}
        IF    '${p}' != '显示器灯'
            ${r}=    创建订单    批量下单员    ${p}    ${DEFAULTS}[qty]
            Append To List    ${created}    ${r.json()["id"]}
        ELSE
            Log    跳过：${p}
        END
    END
    Length Should Be    ${created}    2
