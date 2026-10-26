*** Settings ***
Documentation     Web 关键字库（业务语言层）——定位与等待细节全部住这里
Library           SeleniumLibrary
Library           Collections

*** Keywords ***
打开靶场下单页
    [Arguments]    ${base_url}
    ${opts}=    Set Variable    add_argument("--no-sandbox");add_argument("--disable-dev-shm-usage")
    Open Browser    ${base_url}    headlesschrome    options=${opts}
    Wait Until Page Contains Element    id:customer    timeout=10s

下单
    [Arguments]    ${customer}    ${product}
    Input Text    id:customer    ${customer}
    Select From List By Value    id:product    ${product}
    Click Button    id:submit-btn
    Wait Until Page Contains    订单号    timeout=10s
    Sleep    300ms    # 等 fetch 回填订单号到页面

订单号应出现
    [Arguments]    ${prefix}
    Element Should Contain    id:order-id    ${prefix}

失败时留截图
    [Documentation]    用例 Teardown：失败时截图到 reports/（通过时 no-op）
    Run Keyword If Test Failed    Capture Page Screenshot
