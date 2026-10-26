*** Settings ***
Documentation     段二：Web 页面逐笔查询并支付（读段一订单清单 JSON）
Library           RequestsLibrary
Library           Collections
Library           OperatingSystem
Library           SeleniumLibrary

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952
${IDS_IN}         ${CURDIR}/reports/order_ids.json

*** Test Cases ***
段二：Web 逐笔查询并支付
    ${ids}=    Evaluate    json.load(open(r'''${IDS_IN}'''))    modules=json
    Length Should Be    ${ids}    8
    Open Browser    ${BASE_URL}/orders.html    headlesschrome
    Wait Until Page Contains Element    id:oid    timeout=10s
    FOR    ${oid}    IN    @{ids}
        Input Text    id:oid    ${oid}
        Click Button    id:query-btn
        Wait Until Page Contains    ${oid}    timeout=10s
        Element Should Contain    id:detail    created
        Click Button    id:pay-btn
        Wait Until Page Contains    "status": "paid"    timeout=10s
    END
    [Teardown]    Close Browser
