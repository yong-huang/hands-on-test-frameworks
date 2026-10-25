*** Settings ***
Documentation     板斧二：DataDriver 插件——数据在外部 CSV，加一行数据不加代码
...               两个坑：DataDriver 要 Suite 级 Test Template，且模板关键字必须
...               定义在本文件的 Keywords 表（外部 resource 里的不算，实测 AttributeError）
Library           DataDriver    file=orders.csv    encoding=utf-8
Resource          resources/orders.resource
Test Template     下单并断言

*** Test Cases ***
CSV 驱动的下单
    No Operation    # 壳用例：真正的步骤由 Test Template + CSV 行提供

*** Keywords ***
下单并断言
    [Arguments]    ${customer}    ${product}    ${expected}=201
    ${payload}=    Create Dictionary    customer=${customer}    product=${product}
    ${resp}=    POST    ${BASE_URL}/api/orders    json=${payload}    expected_status=${expected}
    Should Be Equal As Strings    ${resp.status_code}    ${expected}
    IF    '${expected}' == '201'
        Should Not Be Empty    ${resp.json()["id"]}
    END
