*** Settings ***
Documentation     API 回归关键字库——请求/断言细节全住这里
Library           RequestsLibrary
Library           Collections
Library           OperatingSystem

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Keywords ***
校验靶场在线
    [Arguments]    ${base_url}
    ${r}=    GET    ${base_url}/api/health    expected_status=200
    Should Be Equal As Strings    ${r.json()["status"]}    ok

创建订单
    [Arguments]    ${customer}    ${product}    ${qty}=1
    ${payload}=    Create Dictionary    customer=${customer}    product=${product}    qty=${qty}
    ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=any
    RETURN    ${resp}

创建并返回ID
    [Arguments]    ${customer}
    ${resp}=    创建订单    ${customer}    机械键盘    1
    Should Be Equal As Strings    ${resp.status_code}    201
    RETURN    ${resp.json()["id"]}

查询订单
    [Arguments]    ${oid}    ${expected}
    ${r}=    GET    ${BASE_URL}/api/orders/${oid}    expected_status=${expected}
    RETURN    ${r}

支付订单
    [Arguments]    ${oid}    ${expected}
    ${r}=    POST    ${BASE_URL}/api/orders/${oid}/pay    expected_status=${expected}
    RETURN    ${r}

取消订单
    [Arguments]    ${oid}    ${expected}
    ${r}=    POST    ${BASE_URL}/api/orders/${oid}/cancel    expected_status=${expected}
    RETURN    ${r}

校验响应符合订单 Schema
    [Arguments]    ${resp}    ${schema_path}
    ${schema}=    Get File    ${schema_path}
    ${instance}=    Evaluate    $resp.json()
    Evaluate    jsonschema.validate($instance, json.loads($schema))    modules=jsonschema

校验响应不符合订单 Schema
    [Arguments]    ${instance}    ${schema_path}
    ${schema}=    Get File    ${schema_path}
    ${ok}=    Run Keyword And Return Status
    ...    Evaluate    jsonschema.validate($instance, json.loads($schema))    modules=jsonschema
    Should Not Be True    ${ok}

准备指定状态的订单
    [Arguments]    ${target_status}
    ${oid}=    创建并返回ID    矩阵员
    IF    '${target_status}' == 'paid'
        支付订单    ${oid}    200
    ELSE IF    '${target_status}' == 'cancelled'
        取消订单    ${oid}    200
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
    ELSE IF    '支付-已支付' in '${动作}'
        ${oid}=    准备指定状态的订单    paid
        ${r}=    POST    ${BASE_URL}/api/orders/${oid}/pay    expected_status=${期望码}
    ELSE
        Fail    未知矩阵格：${动作}
    END
    Should Be Equal As Strings    ${r.status_code}    ${期望码}
    Dictionary Should Contain Key    ${r.json()}    error
