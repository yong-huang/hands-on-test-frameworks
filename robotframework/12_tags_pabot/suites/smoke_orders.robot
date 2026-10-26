*** Settings ***
Documentation     smoke 套件：快速冒烟（API 路径，不驱动浏览器）
Force Tags        smoke    api
Library           RequestsLibrary

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Test Cases ***
健康检查
    ${resp}=    GET    ${BASE_URL}/api/health    expected_status=200
    Should Be Equal As Strings    ${resp.json()["status"]}    ok

下单冒烟
    ${p}=    Create Dictionary    customer=冒烟员    product=机械键盘
    ${r}=    POST    ${BASE_URL}/api/orders    json=${p}    expected_status=201
    Should Start With    ${r.json()["id"]}    ROB-
