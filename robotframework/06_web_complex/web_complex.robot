*** Settings ***
Documentation     项目 6：复杂页面三难——iframe / 多窗口 / 懒加载
Library           SeleniumLibrary
Library           Collections

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Test Cases ***
iframe 支付面板生成订单
    Open Browser    ${BASE_URL}    headlesschrome
    Wait Until Page Contains Element    id:pay-frame    timeout=10s
    Select Frame    id:pay-frame
    Click Button    id:gen-btn
    Wait Until Page Contains    面板订单号 ROB-    timeout=10s
    Element Should Contain    id:panel-order    ROB-
    Unselect Frame
    Element Should Be Visible    id:submit-btn    # 回主文档后主表单依然在
    [Teardown]    Close Browser

比价链接开新窗口往返
    Open Browser    ${BASE_URL}    headlesschrome
    Click Link    id:compare-link
    Switch Window    locator=NEW
    Wait Until Page Contains Element    id:cmp    timeout=10s
    Title Should Be    价格对照 - Robot 靶场
    Close Window
    Switch Window    main
    Title Should Be    Robot 靶场
    [Teardown]    Close Browser

懒加载推荐 30 件全载
    Open Browser    ${BASE_URL}    headlesschrome
    Wait Until Page Contains Element    class:rcard    timeout=10s
    FOR    ${i}    IN RANGE    10
        ${n}=    Execute Javascript    return document.querySelectorAll('.rcard').length;
        Exit For Loop If    ${n} >= 30
        Execute Javascript    window.scrollTo(0, document.body.scrollHeight);
        Wait Until Keyword Succeeds    3x    1s    Wait Until Page Contains Element    class:rcard
        Sleep    500ms
    END
    ${final}=    Execute Javascript    return document.querySelectorAll('.rcard').length;
    Should Be Equal As Numbers    ${final}    30
    Element Should Be Visible    id:rec-done
    [Teardown]    Close Browser
