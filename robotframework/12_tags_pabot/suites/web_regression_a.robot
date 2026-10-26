*** Settings ***
Documentation     regression/web 套件 A：下单页主流程
Force Tags        regression    web
Library           SeleniumLibrary

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Test Cases ***
下单页主流程 A1
    Open Browser    ${BASE_URL}    headlesschrome
    Wait Until Page Contains Element    id:submit-btn    timeout=10s
    Input Text    id:customer    回归A-1
    Select From List By Value    id:product    无线鼠标
    Click Button    id:submit-btn
    Wait Until Page Contains    订单号    timeout=10s
    [Teardown]    Close Browser

下单页主流程 A2
    Open Browser    ${BASE_URL}    headlesschrome
    Wait Until Page Contains Element    id:submit-btn    timeout=10s
    Input Text    id:customer    回归A-2
    Select From List By Value    id:product    显示器灯
    Click Button    id:submit-btn
    Wait Until Page Contains    订单号    timeout=10s
    [Teardown]    Close Browser

下单页主流程 A3
    Open Browser    ${BASE_URL}    headlesschrome
    Wait Until Page Contains Element    id:submit-btn    timeout=10s
    Input Text    id:customer    回归A-3
    Select From List By Value    id:product    机械键盘
    Click Button    id:submit-btn
    Wait Until Page Contains    订单号    timeout=10s
    [Teardown]    Close Browser
