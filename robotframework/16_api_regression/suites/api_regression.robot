*** Settings ***
Documentation     🏁 API 回归套件：≥20 条用例（正向/异常/Schema/状态机全流转），复用 ShopLibrary
Force Tags        regression    api
Library           RequestsLibrary
Library           Collections
Library           OperatingSystem
Library           ShopLibrary.py    # 项目 11 的关键字库（造数据/金额校验/签名）
Resource          resources/api_keywords.resource
Suite Setup       校验靶场在线    ${BASE_URL}

*** Variables ***
${BASE_URL}       http://127.0.0.1:8952
${SCHEMA_PATH}    ${CURDIR}${/}..${/}..${/}09_api_schema${/}order.schema.json

*** Test Cases ***
正01 创建订单返回 201 全字段
    ${prefix}=    生成订单号前缀    reg
    ${d}=    生成测试数据    正01    回归地址
    ${resp}=    创建订单    ${d}[customer]    机械键盘    1
    Should Be Equal As Strings    ${resp.status_code}    201
    Should Start With    ${resp.json()["id"]}    ROB-
    Should Be Equal As Strings    ${resp.json()["status"]}    created

正02 金额等于单价×数量（ShopLibrary 校验）
    ${resp}=    创建订单    正02实验员    机械键盘    3
    ${amount}=    校验金额    ${resp.json()["amount"]}
    Should Be Equal As Numbers    ${amount}    59.7    # 19.9 × 3

正03 查询订单回读一致
    ${resp}=    创建订单    正03实验员    无线鼠标    1
    ${oid}=    Set Variable    ${resp.json()["id"]}
    ${q}=    查询订单    ${oid}    200
    Should Be Equal    ${q.json()["customer"]}    ${resp.json()["customer"]}

正04 支付流转 paid
    ${oid}=    创建并返回ID    正04实验员
    ${r}=    支付订单    ${oid}    200
    Should Be Equal As Strings    ${r.json()["status"]}    paid

正05 取消流转 cancelled
    ${oid}=    创建并返回ID    正05实验员
    ${r}=    取消订单    ${oid}    200
    Should Be Equal As Strings    ${r.json()["status"]}    cancelled

正06 中文客户名全链路
    ${d}=    生成测试数据    中文组⚡    東京都渋谷区
    ${resp}=    创建订单    ${d}[customer]    显示器灯    1
    Should Contain    ${resp.json()["customer"]}    中文组⚡

正07 特殊字符客户名
    ${resp}=    创建订单    <QA> & "引号"    机械键盘    1
    Should Be Equal As Strings    ${resp.status_code}    201

异01 缺客户 422 点名 error
    负向一格    创建-缺客户    ${None}    422

异02 缺商品 422
    负向一格    创建-缺商品    ${None}    422

异03 空字典 422
    负向一格    创建-空字典    ${None}    422

异04 查询不存在 404
    负向一格    查询-不存在    ROB-deadbeef    404

异05 查询畸形 ID 404
    负向一格    查询-畸形ID    not-an-order    404

异06 支付不存在 404
    负向一格    支付-不存在    ROB-deadbeef    404

异07 取消不存在 404
    负向一格    取消-不存在    ROB-deadbeef    404

异08 已支付再支付 409
    负向一格    支付-已支付    ${None}    409

异09 已支付再取消 409
    负向一格    取消-已支付    ${None}    409

异10 已取消再支付 409
    负向一格    支付-已取消    ${None}    409

Schema01 创建响应过订单 Schema
    ${resp}=    创建订单    Schema组    机械键盘    1
    校验响应符合订单 Schema    ${resp}    ${SCHEMA_PATH}

Schema02 非法实例被 Schema 识破
    ${bad}=    Create Dictionary    foo=1
    校验响应不符合订单 Schema    ${bad}    ${SCHEMA_PATH}

机01 状态机全流转：创建→支付→(再支付409)→(取消409)
    ${oid}=    创建并返回ID    状态机组
    支付订单    ${oid}    200
    ${again}=    支付订单    ${oid}    409
    ${cancel}=    取消订单    ${oid}    409
    ${final}=    查询订单    ${oid}    200
    Should Be Equal As Strings    ${final.json()["status"]}    paid

机02 状态机全流转：创建→取消→(再取消409)
    ${oid}=    创建并返回ID    状态机组2
    取消订单    ${oid}    200
    ${again}=    取消订单    ${oid}    409
    ${final}=    查询订单    ${oid}    200
    Should Be Equal As Strings    ${final.json()["status"]}    cancelled
