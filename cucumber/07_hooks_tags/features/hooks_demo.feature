# language: zh-CN
功能: 钩子与标签

  @smoke
  场景: 冒烟集（登录可见）
    假如 打开 pw-store 首页
    那么 登录表单可见

  场景: 时序探针（钩子标记进 timeline）
    假如 打开 pw-store 首页
    那么 Before 已执行且记录在 timeline

  @wip
  场景: 进行中的实验（用 not @wip 排除演示）
    假如 打开 pw-store 首页
    那么 登录表单可见
