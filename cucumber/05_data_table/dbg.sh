#!/usr/bin/env bash
cd "$(dirname "$0")"
lsof -ti :9105 2>/dev/null | xargs kill 2>/dev/null || true
PORT=9105 node ../../playwright/02_pw_sut/server.mjs > /dev/null 2>&1 &
for i in $(seq 1 40); do curl -sf -m 2 http://127.0.0.1:9105/api/health >/dev/null 2>&1 && break; sleep 0.25; done
npx cucumber-js features/batch.feature 2>&1 | grep -B 2 -A 6 'Error' | head -14
kill %1 2>/dev/null
