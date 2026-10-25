*** Settings ***
Documentation     项目 5：Web 表单与控件全集——多选/复选/radio/文件上传 + 汇总断言
Library           SeleniumLibrary
Library           OperatingSystem

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952

*** Test Cases ***
控件全集操作与汇总断言
    Open Browser    ${BASE_URL}    headlesschrome
    Wait Until Page Contains Element    id=customer    timeout=10s

    # 基础下单信息
    Input Text    id:customer    李雷
    Select From List By Value    id:product    无线鼠标

    # 多选下拉：加急 + 保价
    Select From List By Value    id:gifts    rush
    Select From List By Value    id:gifts    insure
    List Selection Should Be    id:gifts    rush    insure

    # 复选框：勾上并断言状态
    Select Checkbox    id:gift-wrap
    Checkbox Should Be Selected    id:gift-wrap

    # 单选组：选 EMS 并断言
    Select Radio Button    express    ems
    Radio Button Should Be Set To    express    ems

    # 文件上传：OperatingSystem 库造临时文件，Choose File 直接投递路径
    ${voucher}=    Set Variable    ${OUTPUT_DIR}/voucher-李雷.txt
    Create File    ${voucher}    订单凭证内容
    Choose File    id:voucher    ${voucher}

    Click Button    id:submit-btn
    Wait Until Page Contains    订单号    timeout=10s
    Wait Until Element Is Visible    id:summary    timeout=10s
    Element Should Contain    id:summary    rush+insure
    Element Should Contain    id:summary    贺卡=true
    Element Should Contain    id:summary    快递=ems
    Element Should Contain    id:summary    附件=voucher-李雷.txt
    Element Should Contain    id:order-id    ROB-
    [Teardown]    Close Browser
