*** Settings ***
Documentation     🏁 Web 回归套件：关键字库化分层 + 失败自动截图 + act 本地 CI
Force Tags        regression    web
Resource          resources/web_keywords.resource
Suite Teardown    Run Keyword And Ignore Error    Close All Browsers

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Test Cases ***
下单主流程（业务关键字）
    打开靶场下单页    ${BASE_URL}
    下单    李雷-regression    无线鼠标
    订单号应出现    ROB-
    [Teardown]    失败时留截图

下单主流程（第二条，验证会话独立性）
    打开靶场下单页    ${BASE_URL}
    下单    Alice-regression    机械键盘
    订单号应出现    ROB-
    [Teardown]    失败时留截图

慢元素显式等待（回归防线）
    打开靶场下单页    ${BASE_URL}
    Wait Until Element Is Visible    id:slow-banner    timeout=10s
    Element Should Be Visible    id:slow-banner
    [Teardown]    失败时留截图
