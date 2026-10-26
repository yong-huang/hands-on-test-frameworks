*** Settings ***
Documentation     段一：Excel 读单 → API 批量建单 → 订单清单落盘 JSON（供段二/段三使用）
Library           RPA.Excel.Files
Library           RPA.Tables
Library           RequestsLibrary
Library           Collections
Library           OperatingSystem

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952
${XLSX_IN}        ${CURDIR}/reports/orders_input.xlsx
${IDS_OUT}        ${CURDIR}/reports/order_ids.json

*** Test Cases ***
段一：Excel 读单并 API 批量建单（非法行捕获）
    Open Workbook    ${XLSX_IN}
    ${rows}=    Read Worksheet As Table    header=True
    Close Workbook
    Length Should Be    ${rows}    10

    ${ids}=    Create List
    FOR    ${row}    IN    @{rows}
        ${status}    ${msg}=    Run Keyword And Ignore Error
        ...    建单一行    ${row}[customer]    ${row}[product]    ${row}[qty]
        IF    '${status}' == 'PASS'
            Append To List    ${ids}    ${msg}
        ELSE
            Log    非法行跳过（${row}[name]）：${msg}    level=WARN
        END
    END
    Length Should Be    ${ids}    8    # 10 行 - 2 非法 = 8 笔
    Evaluate    json.dump($ids, open(r'''${IDS_OUT}''', "w"))    modules=json
    Log    订单清单已落盘：${IDS_OUT}

*** Keywords ***
建单一行
    [Arguments]    ${customer}    ${product}    ${qty}
    Should Not Be Empty    ${customer}    客户为空
    Should Not Be Empty    ${product}    商品为空
    ${payload}=    Create Dictionary    customer=${customer}    product=${product}    qty=${qty}
    ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
    RETURN    ${resp.json()["id"]}
