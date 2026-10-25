*** Settings ***
Documentation     项目 4：SeleniumLibrary 入门——下单主流程 + 慢元素显式等待 + HEADLESS 切换
Library           SeleniumLibrary

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Test Cases ***
下单主流程（id 前缀定位 + Wait Until 显式等待）
    Open Browser    ${BASE_URL}    ${BROWSER}
    Wait Until Page Contains Element    id=customer    timeout=10s
    Input Text    id:customer    李雷
    Select From List By Value    id:product    无线鼠标
    Click Button    id:submit-btn
    Wait Until Page Contains    订单号    timeout=10s
    Element Should Contain    id:order-id    ROB-
    [Teardown]    Close Browser

慢元素用 Wait Until（不用 sleep）
    Open Browser    ${BASE_URL}    ${BROWSER}
    Wait Until Element Is Visible    id:slow-banner    timeout=10s    error=慢元素 10s 内未现身
    Element Should Be Visible    id:slow-banner
    [Teardown]    Close Browser
