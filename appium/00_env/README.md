# 00 · 共享环境：Appium Server 与 XCUITest Driver

> 整个 iOS 系列共用这一份环境：Appium 3.8.0 当调度层，
> XCUITest 12.19.1 当执行层。把它放在项目内而不是全局，
> 是为了让每个实验都能用同一条命令复现，不被机器上的旧版本干扰。

## Background

Appium 的环境由两半组成：server 和 driver。server 只负责接 HTTP、
解析 capabilities、把命令路由给 driver；真正和 iOS 打交道的是
XCUITest driver。

全局 `npm i -g appium` 看起来省事，但版本会随机器漂移。今天用 3.8，
明天另一个项目升到 4.x，旧实验的结论就不可复现了。

项目内安装把 server 锁在 `package.json`，driver 锁在 setup 脚本；
谁 clone 仓库，谁就得到同一套组合。

## What

本模块只做三件事：安装 Appium 3.8.0、安装 XCUITest 12.19.1、
运行 `appium driver doctor xcuitest` 体检。

`setup.sh` 是幂等的：已安装的依赖不重装，缺 driver 才补装。
`package.json` 另外提供 `npm run server` 和 `npm run doctor` 两个入口。

体检的期望结果是 **0 required fixes**。可选的 `applesimutils`
缺失只影响权限类命令，不影响首会话。

## When to Use

在这些时刻运行本模块：

- 第一次 clone 仓库，准备开始 `01_ios_session`。
- Xcode 或 iOS simulator runtime 升级之后。
- Appium 报 driver 不兼容、WDA 编译失败，需要重建环境时。
- 想确认 4723 端口和 driver 状态，但还不想跑完整用例。

不适用：Android 实验需要另装 `uiautomator2` driver；
本模块只覆盖 iOS 的 XCUITest 链路。

## Quick Start

```bash
cd appium/00_env
./setup.sh              # 安装 server + driver，然后 doctor
npm run server          # 前台启动，端口 4723，base path /wd/hub
npm run doctor          # 单独复查
```

setup 的关键输出：

```
✔ Installing 'xcuitest'
ℹ Driver xcuitest@12.19.1 successfully installed
info Doctor ### Diagnostic completed, 0 required fixes needed, 1 optional fix possible. ###
```

server 启动后另开终端验证：

```bash
curl -s http://127.0.0.1:4723/wd/hub/status
# {"value":{"ready":true,"message":"The server is ready to accept new connections",...}}
```

## How It Works

**server 装在 `node_modules`，不装全局。** `npm install` 按
`package.json` 把 Appium 3.8.0 放进本目录；脚本用
`node_modules/.bin/appium` 调用，不依赖 PATH 上碰巧存在的版本。

**driver 装在 Appium home，不在 `node_modules`。** `appium driver install
xcuitest` 下载 driver 到用户级目录（通常是 `~/.appium`），
server 启动时按已安装列表加载。所以换项目目录不影响 driver。

**doctor 是环境的地图，不是装饰。** 它逐项检查 Xcode 路径、
Command Line Tools、ffmpeg、Simulator SDK 和可选工具；
哪一项缺失，报错会直接指向修复动作。

**脚本的检查读的是 stderr。** `appium driver list --installed` 把列表写到
stderr，不是 stdout；脚本用 `2>&1` 合并后再判断，否则会误判为未安装。

## Pitfalls & Q&A

**Q：doctor 说 Xcode 没问题，WDA 还是编译失败？**
doctor 看的是 `DEVELOPER_DIR` 或 `xcode-select` 的结果，
但你的 shell 可能把它指到了 Command Line Tools。

先跑 `xcode-select -p`，必要时 `export DEVELOPER_DIR`。

**Q：`applesimutils` 必须装吗？**
不必须。它只服务 `mobile: setPermission` 这类权限操作；
首会话、定位、登录都不用它。需要时再
`brew tap wix/brew && brew install applesimutils`。

**Q：升级 Xcode 后 driver 要不要重装？**
先试 `appium driver update xcuitest`；如果 WDA 仍编译失败，
删掉 driver 重装。Xcode 大版本升级后，旧 WDA 缓存经常不兼容。

**Q：4723 端口被占用怎么办？**
`lsof -i :4723` 找到进程；如果是旧实验留下的 Appium，
用对应脚本的 `clean` 或 `kill` 关掉。不要同时起两个 server，
客户端会连到先监听的那个。

**Q：为什么不直接把 Appium 写成全局命令？**
全局版本会被其他项目改写，实验之间互相污染。
项目内安装 + `npm run` 才能保证"同一份代码，同一套环境"。
