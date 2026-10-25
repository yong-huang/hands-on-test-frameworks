*** Settings ***
Documentation     板斧二：外部 CSV 数据文件 + FOR 循环驱动——加一行数据不加代码。
...               注：DataDriver 插件 1.11.2 与 Robot Framework 7.5 不兼容（官方 README 的
...               极简样例实测同样报 Unassigned required argument，见 README 踩坑），故用
...               「CSV + Evaluate 读表 + FOR 逐行跑模板关键字」实现同等目标。
Resource          resources/orders.resource
Library           Collections

*** Variables ***
${CSV_PATH}       ${CURDIR}/orders.csv

*** Test Cases ***
CSV 驱动的下单（读外部 CSV 逐行执行）
    ${rows}=    Evaluate    list(csv.DictReader(open(r'''${CSV_PATH}''', encoding="utf-8")))    modules=csv
    Length Should Be    ${rows}    4
    FOR    ${row}    IN    @{rows}
        Log    执行组：${row}[customer] / ${row}[product] / 期望 ${row}[expected]
        下单并断言    ${row}[customer]    ${row}[product]    ${row}[expected]
    END
