*** Settings ***
Documentation     项目 1 首个套件：打开靶场断言标题 + 调接口断言 200
Library           SeleniumLibrary
Library           RequestsLibrary
Suite Setup       Log    靶场由 01_shop_first_suite.sh 的 apply 步拉起（sh 先行，robot 只管跑）

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952
${BROWSER}        headlesschrome

*** Test Cases ***
Web 页面标题应正确
    Open Browser    ${BASE_URL}    ${BROWSER}
    Wait Until Page Contains Element    id=submit-btn    timeout=10s
    Title Should Be    Robot 靶场
    [Teardown]    Close Browser

健康检查接口应返回 200
    ${resp}=    GET    ${BASE_URL}/api/health
    Should Be Equal As Strings    ${resp.status_code}    200
    Should Be Equal As Strings    ${resp.json()["status"]}    ok
