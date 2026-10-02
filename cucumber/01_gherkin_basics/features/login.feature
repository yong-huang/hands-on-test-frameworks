# language: zh-CN
功能: pw-store 登录
  作为 pw-store 的用户
  我希望用账号密码登录
  以便管理我的订单

  场景: 正确的凭据登录成功
    假如 打开 pw-store 首页
    当 以用户名 "admin" 密码 "admin123" 登录
    那么 页面显示 "欢迎，admin"

  场景: 错误的密码登录失败
    假如 打开 pw-store 首页
    当 以用户名 "admin" 密码 "wrong-password" 登录
    那么 页面显示错误提示 "用户名或密码错误"

  场景: 未登录访客只能看到登录表单
    假如 打开 pw-store 首页
    那么 页面显示登录表单
