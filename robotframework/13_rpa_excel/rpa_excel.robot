*** Settings ***
Documentation     项目 13：RPA——Excel 驱动批量下单（读单→逐行下单→结果写回→非法行不中断）
Library           RPA.Excel.Files
Library           RPA.Tables
Library           Collections
Library           OperatingSystem
Library           RequestsLibrary

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952
${XLSX_IN}        ${OUTPUT_DIR}/orders_input.xlsx
${XLSX_OUT}       ${OUTPUT_DIR}/orders_result.xlsx

*** Test Cases ***
Excel 驱动批量下单（10 行含 2 非法，结果写回）
    # ① xlsx 输入由 sh 用 openpyxl 从 CSV 预制（RPA 环节直接操作真 xlsx）
    File Should Exist    ${XLSX_IN}
    Open Workbook    ${XLSX_IN}
    ${rows}=    Read Worksheet As Table    header=True
    Close Workbook
    Length Should Be    ${rows}    10

    # ② 逐行下单：非法行被捕获、不中断批处理；结果收集
    ${results}=    Create List
    FOR    ${row}    IN    @{rows}
        ${r}=    Create Dictionary
        ...    name=${row}[name]    customer=${row}[customer]    product=${row}[product]
        ${status}    ${msg}=    Run Keyword And Ignore Error
        ...    下单一行    ${row}[customer]    ${row}[product]    ${row}[qty]
        IF    '${status}' == 'PASS'
            Set To Dictionary    ${r}    result=通过    order_id=${msg}
        ELSE
            Set To Dictionary    ${r}    result=失败    order_id=${msg}
        END
        Append To List    ${results}    ${r}
    END

    # ③ 汇总断言：8 成功 2 失败（订单05 无客户、订单08 空行），非法行确实没有中断
    ${ok}=    Evaluate    sum(1 for r in $results if r["result"] == "通过")
    ${bad}=    Evaluate    sum(1 for r in $results if r["result"] == "失败")
    Should Be Equal As Numbers    ${ok}    8
    Should Be Equal As Numbers    ${bad}    2
    Log    汇总：${ok} 成功 / ${bad} 失败

    # ④ 结果写回 xlsx（新工作表，人工可复核；Save Workbook 另存为输出文件）
    Open Workbook    ${XLSX_IN}
    Create Worksheet    结果    content=${results}    header=True
    Save Workbook    ${XLSX_OUT}
    Close Workbook
    File Should Exist    ${XLSX_OUT}
    Log    结果表已写回：${XLSX_OUT}

*** Keywords ***
下单一行
    [Arguments]    ${customer}    ${product}    ${qty}
    Should Not Be Empty    ${customer}    客户为空
    Should Not Be Empty    ${product}    商品为空
    ${payload}=    Create Dictionary    customer=${customer}    product=${product}    qty=${qty}
    ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=201
    RETURN    ${resp.json()["id"]}
