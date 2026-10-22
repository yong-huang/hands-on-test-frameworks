#!/usr/bin/env bash
# 共享 Appium 环境：安装 Appium server 与 XCUITest driver（幂等）
set -euo pipefail
cd "$(dirname "$0")"

export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"

if [ ! -d node_modules/appium ]; then
    echo "==> 安装 Appium 3.8.0"
    npm install --no-audit --no-fund
else
    echo "==> Appium 依赖已存在"
fi

if ! npx appium driver list --installed 2>&1 | grep -c xcuitest >/dev/null; then
    echo "==> 安装 XCUITest driver"
    npx appium driver install xcuitest
else
    echo "==> XCUITest driver 已存在"
fi

echo "==> 体检 XCUITest driver"
npx appium driver doctor xcuitest
