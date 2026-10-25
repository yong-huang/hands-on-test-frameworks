*** Settings ***
Documentation     下单业务关键字（两板斧共用）
Library           RequestsLibrary
Library           Collections

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Keywords ***
下单并断言
    [Documentation]    创建订单并断言状态码（expected 支持 201 正向 / 422 负向）
    [Arguments]    ${customer}    ${product}    ${expected}=201
    ${payload}=    Create Dictionary    customer=${customer}    product=${product}
    ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=${expected}
    Should Be Equal As Strings    ${resp.status_code}    ${expected}
    IF    '${expected}' == '201'
        Should Not Be Empty    ${resp.json()["id"]}
    ELSE
        Dictionary Should Contain Key    ${resp.json()}    error
    END
