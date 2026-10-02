# language: zh-CN
功能: 登录矩阵
  不同凭据组合的登录行为各有确定结果

  场景大纲: 以 <用户名>/<密码> 登录应 <预期结果>
    假如 打开 pw-store 首页
    当 以用户名 <用户名> 密码 <密码> 登录
    那么 登录 <预期结果> 且欢迎语或错误提示包含 <关键文案>

    例子:
      | 用户名   | 密码          | 预期结果 | 关键文案               |
      | admin    | admin123      | 成功     | admin                  |
      | customer | customer123   | 成功     | customer               |
      | admin    | wrong-pass    | 失败     | 用户名或密码错误       |
      | nobody   | whatever      | 失败     | 用户名或密码错误       |
