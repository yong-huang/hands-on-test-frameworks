*** Settings ***
Documentation     项目 9：JSON Schema 校验 + 3×3 负向矩阵（模板关键字驱动，逐格断言错误码与 error 字段）
Library           RequestsLibrary
Library           Collections
Library           OperatingSystem

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952
${SCHEMA_PATH}    ${CURDIR}/order.schema.json

*** Test Cases ***
正向创建订单响应过 Schema
    ${payload}=    Create Dictionary    customer=Schema校验员    product=机械键盘
    ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
    校验响应符合订单 Schema    ${resp}

Schema 反向演示：非法实例必须被识破
    ${bad}=    Create Dictionary    foo=1
    校验响应不符合订单 Schema    ${bad}

负向矩阵 3×3（模板关键字驱动）
    [Template]    负向一格
    # 动作            标识/输入           期望码
    创建-缺客户       ${None}             422
    创建-缺商品       ${None}             422
    创建-空字典       ${None}             422
    查询-不存在       ROB-deadbeef        404
    查询-畸形ID       not-an-order        404
    支付-不存在       ROB-deadbeef        404
    取消-不存在       ROB-deadbeef        404
    取消-已支付       PAID                409
    支付-已取消       CANCELLED           409

*** Keywords ***
校验响应符合订单 Schema
    [Arguments]    ${resp}
    ${schema}=    Get File    ${SCHEMA_PATH}
    ${instance}=    Evaluate    $resp.json()
    Evaluate    jsonschema.validate($instance, json.loads($schema))    modules=jsonschema

校验响应不符合订单 Schema
    [Arguments]    ${instance}
    ${schema}=    Get File    ${SCHEMA_PATH}
    ${ok}=    Run Keyword And Return Status
    ...    Evaluate    jsonschema.validate($instance, json.loads($schema))    modules=jsonschema
    Should Not Be True    ${ok}

准备指定状态的订单
    [Arguments]    ${target_status}
    ${payload}=    Create Dictionary    customer=矩阵员    product=机械键盘
    ${c}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
    ${oid}=    Set Variable    ${c.json()["id"]}
    IF    '${target_status}' == 'paid'
        POST    ${BASE_URL}/api/orders/${oid}/pay    expected_status=200
    ELSE IF    '${target_status}' == 'cancelled'
        POST    ${BASE_URL}/api/orders/${oid}/cancel    expected_status=200
    END
    RETURN    ${oid}

负向一格
    [Arguments]    ${动作}    ${标识}    ${期望码}
    IF    '${动作}' == '创建-缺客户'
        ${p}=    Create Dictionary    product=机械键盘
        ${r}=    POST    ${BASE_URL}/api/orders    json=${p}    expected_status=${期望码}
    ELSE IF    '${动作}' == '创建-缺商品'
        ${p}=    Create Dictionary    customer=某人
        ${r}=    POST    ${BASE_URL}/api/orders    json=${p}    expected_status=${期望码}
    ELSE IF    '${动作}' == '创建-空字典'
        ${p}=    Create Dictionary
        ${r}=    POST    ${BASE_URL}/api/orders    json=${p}    expected_status=${期望码}
    ELSE IF    '查询' in '${动作}'
        ${r}=    GET    ${BASE_URL}/api/orders/${标识}    expected_status=${期望码}
    ELSE IF    '支付-不存在' in '${动作}' or '取消-不存在' in '${动作}'
        ${r}=    POST    ${BASE_URL}/api/orders/${标识}/${动作[:2]}    expected_status=${期望码}
    ELSE IF    '取消-已支付' in '${动作}'
        ${oid}=    准备指定状态的订单    paid
        ${r}=    POST    ${BASE_URL}/api/orders/${oid}/cancel    expected_status=${期望码}
    ELSE IF    '支付-已取消' in '${动作}'
        ${oid}=    准备指定状态的订单    cancelled
        ${r}=    POST    ${BASE_URL}/api/orders/${oid}/pay    expected_status=${期望码}
    ELSE
        Fail    未知矩阵格：${动作}
    END
    Should Be Equal As Strings    ${r.status_code}    ${期望码}
    Dictionary Should Contain Key    ${r.json()}    error
    Log    格 [${动作}] 断言通过：${期望码} + error 字段
