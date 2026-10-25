*** Settings ***
Library           Collections

*** Test Cases ***
精确全消息
    TRY
        boom
    EXCEPT    boom-b happened
        Log    caught exact
    END
    Log    T1 survived

前缀模式
    TRY
        boom
    EXCEPT    boom-b*
        Log    caught prefix
    END
    Log    T2 survived

type glob 显式
    TRY
        boom
    EXCEPT    type=glob    *boom*
        Log    caught typeglob
    END
    Log    T3 survived
*** Keywords ***
boom
    Fail    boom-b happened
