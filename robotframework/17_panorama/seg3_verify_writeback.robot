*** Settings ***
Documentation     段三：API 终态复核（全部 paid）+ 结果写回 Excel 新工作表
Library           RequestsLibrary
Library           Collections
Library           OperatingSystem
Library           RPA.Excel.Files

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952
${IDS_IN}         ${CURDIR}/reports/order_ids.json
${XLSX_IN}        ${CURDIR}/reports/orders_input.xlsx
${XLSX_OUT}       ${CURDIR}/reports/orders_result.xlsx

*** Test Cases ***
段三：终态复核与结果回写
    ${ids}=    Evaluate    json.load(open(r'''${IDS_IN}'''))    modules=json
    # ① API 复核：8 笔全部 paid
    ${summary}=    Create List
    FOR    ${oid}    IN    @{ids}
        ${r}=    GET    ${BASE_URL}/api/orders/${oid}    expected_status=200
        Should Be Equal As Strings    ${r.json()["status"]}    paid
        Append To List    ${summary}    Create Dictionary    order_id=${oid}    result=已支付    amount=${r.json()["amount"]}
    END
    # ② 结果写回 Excel（人工可复核）
    Open Workbook    ${XLSX_IN}
    Create Worksheet    结果    content=${summary}    header=True
    Save Workbook    ${XLSX_OUT}
    Close Workbook
    File Should Exist    ${XLSX_OUT}
    Log    结果表已写回：${XLSX_OUT}（${ids.__len__()} 笔）
