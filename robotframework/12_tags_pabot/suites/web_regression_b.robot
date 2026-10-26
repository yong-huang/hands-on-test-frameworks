*** Settings ***
Documentation     regression/web 套件 B：查询页冒烟 + 弹性注入失败（--rerunfailed 演示）
Force Tags        regression    web
Library           SeleniumLibrary
Library           OperatingSystem

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Test Cases ***
查询页可打开
    Open Browser    ${BASE_URL}/orders.html    headlesschrome
    Wait Until Page Contains Element    id:oid    timeout=10s
    Element Should Be Visible    id:query-btn
    [Teardown]    Close Browser

弹性注入失败（环境变量 INJECT=1 时红，用于重跑合并演示）
    ${inject}=    Get Environment Variable    INJECT    0
    IF    '${inject}' == '1'
        Fail    注入失败：用于 --rerunfailed + rebot 合并演示
    END
    Log    未注入，正常通过
