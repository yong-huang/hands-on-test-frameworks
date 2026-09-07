# 24 · Selenium 进阶：POM + ActionChains + 本地 Grid 并行

> Selenium 的工程化三件套：页面对象稳住结构、ActionChains 覆盖鼠标语义、
> Docker Grid 把并行做真。本篇全部实测：本地套件全绿，Grid ×2 并行加速 1.8x。

## 1. 为什么需要它

- 拖拽/悬停是常见交互，ActionChains 用原生鼠标事件驱动；
- Grid 让"多浏览器并行"从口号变成一条 docker-compose。

## 2. 总览：从单机到 Grid 的拓扑

<!-- 图: images/selenium_grid.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/24_selenium_advanced/images/selenium_grid.html)
> （或本地打开 [`images/selenium_grid.html`](images/selenium_grid.html)）。

pytest-xdist 双进程 → Grid(:4444, maxSession=2) → 两个容器内 Chrome →
访问宿主机 SUT（host.docker.internal）。

## 3. 快速开始

```bash
./selenium_grid.sh    # 本地执行 → 起 Grid → 串行 vs ×2 并行对比 → 清理
```

实测数据：Grid 串行 12.2s → 双会话并行 6.8s（加速比 1.8x，7 条用例含 4×1.5s 工作量）。

## 4. 核心概念

### 4.1 Selenium 版 POM

`pages/order_page.py` 与 lab 18 的 IndexPage 同语义：选择器集中在类里，
动作方法说业务语言。对照阅读能看出两代框架 POM 的差异只在驱动层 API。

### 4.2 ActionChains：原生鼠标事件

`click_and_hold(src).move_to_element(dst).release()` 完成拖拽。
**坑**：HTML5 的 DnD API 不吃合成的鼠标事件——本实验的自定义页面用
mousemove/mouseup 监听实现拖放语义，ActionChains 才能驱动。
（真 HTML5 拖拽要用 JS 注入 dispatchEvent。）

### 4.3 JS 执行器

`execute_script("arguments[0].scrollIntoView(...)", el)`——协议做不到的事
直接执行 JS；也是读取页面状态（title、变量）的万能后门。

### 4.4 Grid 两个经典坑（本实验真实踩过）

1. **容器内 127.0.0.1 是容器自己**：Chrome 在容器里，访问宿主机 SUT 必须
   `host.docker.internal`。
2. **data: URL 的 `#` 是 fragment 分隔符**：内联 HTML 里的十六进制颜色会把
   页面截断——必须 `urllib.parse.quote` 编码。

### 4.5 并行收益的度量

套件太快时启动开销吃掉全部收益（第一版实测串行 1.8s 并行 1.9s）——
加入 4×1.5s 的工作量用例后 1.8x 加速才显形。**度量的前提是负载真实**。

## 5. 关键命令

```bash
docker compose -f docker-compose.grid.yml up -d     # Grid :4444
SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub pytest -n 2
```

```python
webdriver.Remote(command_executor=URL, options=opts)   # 切到 Grid
ActionChains(d).click_and_hold(a).move_to_element(b).release().perform()
```

## 6. 文件结构

```
24_selenium_advanced/
├── README.md
├── selenium_grid.sh               # SUT + Grid 生命周期 + 对比
├── docker-compose.grid.yml        # standalone-chrome（SE_NODE_MAX_SESSIONS=2）
├── configs/pytest.ini
├── pages/order_page.py            # Selenium 版 POM
├── tests/
│   ├── conftest.py                # driver fixture（本地/远程自动切换）
│   ├── test_grid_local.py         # POM + ActionChains + JS 执行器
│   └── test_workload.py           # 4×1.5s 工作量用例（并行度量素材）
└── images/
```

## 7. 面试要点

- **Q: Grid 并行度怎么定？** maxSession 与机器核/内存匹配；每个 Chrome 吃
  0.5-1GB，shm_size 要给足（2g 起）。
- **Q: HTML5 拖拽怎么测？** ActionChains 驱动不了 DnD API——用 JS 注入事件，
  或让被测页面同时响应鼠标事件（本实验做法）。
- **Q: Selenium 套件的失败取证怎么做？** 自建钩子：pytest hookimpl 里
  driver.get_screenshot_as_file——框架不管，工程补位。

## 8. 总结

三大框架全部工程化。下一篇 [25_comparison](../25_comparison/README.md)：
同一 SUT 同语义用例矩阵，用数据给三国杀收口。
