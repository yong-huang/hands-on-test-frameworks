# language: zh-CN
功能: 文件上传（业务域: 上传）

  场景: 上传文件后可见
    假如 管理员已登录
    当 上传文件 "final-attachment.txt" 内容为 "final suite payload"
    那么 上传列表中存在 "final-attachment.txt"
