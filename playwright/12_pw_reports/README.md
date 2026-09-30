# 12 · 报告与产物体系：让失败自己携带全部证据

> "本地跑挂了但我这边是绿的"这类扯皮，靠的是标准化产物。本实验给 pw-store 套件
> 配三路 reporter（HTML / JUnit / list）与全量产物（trace + 截图 + 视频），
> 用一条人为失败用例当标本，逐项验证产物的存在性与合法性（JUnit 过 xmllint 校验）。

## Background

一条失败的用例需要回答四个问题：哪条红了、失败瞬间页面什么样、操作轨迹是什么、
给 CI 平台看的数据在哪。没有产物体系时，这些靠口头描述与截图粘贴；
有了产物体系，失败用例自带全部证据，任何人在任何机器上都能还原现场。

reporter（报告器）是把执行结果转成特定格式的插件。Playwright 的多 reporter
设计让"给人看的"与"给机器吃的"并行产出：HTML 报告供本地排障，
JUnit XML（持续集成平台通用的测试结果格式）供流水线聚合展示，互不干扰。

## What

本实验的 config 声明三路 reporter 与三类产物：`html`（可视化报告）、
`junit`（写 report.xml）、`list`（终端实时）；`use` 里开 `video: 'on'`、
`screenshot: 'on'`、`trace: 'on'`——标本用例失败时三者齐挂。

可以把产物体系想成航班的黑匣子与登机牌：执行结束同时产出黑匣子
（trace/视频，供事故调查）、登机牌数据（JUnit，供机场大屏聚合）和
广播（list，实时通知）。但和航班不同，这些产物在本地一键生成，
不需要任何基础设施——CI 集成只是把同一批文件搬到 artifact 存储（lab 18）。

![报告与产物体系：一次执行，四路产出](images/reports.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/12_pw_reports/images/reports.html)
> （或本地打开 [`images/reports.html`](images/reports.html)）。
> 四条扇出边分别通向四类消费者：人（HTML）、机器（JUnit）、归档（产物目录）、当下（终端）。

## When to Use

| 消费场景 | 产物 | 打开方式 |
|:---|:---|:---|
| 本地排障（失败后立刻看） | HTML 报告 | `npx playwright show-report` |
| CI 平台展示用例数/失败数 | JUnit report.xml | 平台自动解析聚合 |
| 事后深度还原（跨机器） | trace.zip | `npx playwright show-trace <path>` |
| 向不在场的人演示失败过程 | video.webm | 任意播放器 |
| 开发循环的高频反馈 | list 终端输出 | 跑批即见 |

判断口径：**产物越全，磁盘与速度的税越重**。日常档位
（video off / screenshot retain-on-failure / trace retain-on-failure）
与排查档位（全开，lab 08 模式）按需切换，不要常年全开。

## Quick Start

```bash
cd playwright/12_pw_reports
./reports.sh          # apply 体检 → observe 跑批 + 五类产物验证 → clean
```

observe ① 跑 3 条用例（2 绿 + 1 条人为失败标本，脚本显式容忍红）：

```
✓  1 [chromium] › 订单区正常（绿用例，产物齐但用不上） (399ms)
✗  3 [chromium] › 人为失败标本：断言一个不存在的元素
  2 passed, 1 failed
```

observe ②③ 是两条硬验收线——JUnit 用 xmllint 验合法性，标本用例验三产物齐挂：

```
>>> report.xml 结构合法 ✓
>>> trace   ✓ …/人为失败标本…/trace.zip
>>> 截图    ✓ …/人为失败标本…/test-failed-1.png
>>> 视频    ✓ …/人为失败标本…/video.webm
```

验收方式：`xmllint --noout report.xml` 零输出（合法）；标本用例目录下
trace/截图/视频三个文件齐备；`npx playwright show-report` 打开 HTML 报告，
失败条目下能直接回放 trace 与视频。

## How It Works

**多 reporter 是并列产出而非切换。** config 的 reporter 数组里每项独立生效：
一次执行同时写 HTML 报告目录、生成 report.xml、向终端逐条打印。

注意一个本实验实测踩过的坑：命令行 `--reporter=line` 会**整体覆盖** config 的
reporter 数组——加了它，junit 静默消失（report.xml 根本不生成）。
要用终端 list 就写进 config 数组，不要用 CLI 覆盖。

**产物的挂载粒度是"用例"。** trace/截图/视频挂在用例自己的目录
（`test-results/<用例名>-chromium/`）。

HTML 报告里点开失败条目，三产物内嵌展示——trace 逐帧回放，
视频整段播放，截图是失败瞬间的静态帧。
分工：trace 给排障，视频给演示，截图给快照。

**JUnit 是 CI 的通用货币。** report.xml 的 tests/failures 属性是各 CI 平台
（GitHub Actions/Jenkins/GitLab）解析测试结果的标准入口。

本实验用 `xmllint --noout` 验证 XML 合法性——产物"生成了"和"生成对了"
是两回事，机器消费的产物必须有格式校验。

**outputDir 路径要显式钉死。** Playwright 的输出路径解析受 package.json 位置
影响，不显式指定时产物会落到意料之外的上层目录。

本实验全部用 `outputDir: fileURLToPath(new URL('./test-results', import.meta.url))`
钉在实验目录内，clean 才能删干净
（实测踩过：产物散落上层导致 clean 无效）。

## Pitfalls & Q&A

**Q：video: 'on' 什么时候算过度？**
除排查窗口外都算过度。视频编码是执行期持续成本，套件越大越明显。
默认档位用 `video: 'retain-on-failure'`（失败才保留，成功即删），
和 trace 的 retain-on-failure 语义对齐。本实验为凑齐标本产物才全程开。

**Q：JUnit 报告在 CI 里显示的用例名为什么带文件路径前缀？**
junit reporter 把 classname 设为 spec 文件相对路径、name 设为用例标题，
平台按二者聚合。这是标准行为；重名用例会在此处撞车。

团队规范一般是"标题内含足够上下文"——本系列用中文业务描述，
如"人为失败标本：断言一个不存在的元素"。

**Q：HTML 报告能发布给别人看吗？**
可以。`playwright-report/` 是自包含静态目录（zip 后丢任何静态服务器），
`npx playwright show-report --host` 还能起本地服务。

注意报告内嵌 trace 与视频，体积可观——对外分享前清理无关执行，
或只上传 CI 的 artifact 留档。

**Q：为什么 list reporter 还要留在 config 里？**
它是开发循环的最低延迟反馈：跑一条看一条，不用等报告生成。

三路 reporter 各服务一个时间尺度——list 服务"此刻"，
HTML 服务"这一轮"，JUnit 服务"这段历史"。
砍掉任何一路，对应场景就退化成翻文件。

**Q：产物目录会不会被下次执行撑爆？**
Playwright 默认清空 outputDir 再写（每次执行都是全新产物集）。
要保留历史就得主动搬走——CI 的 artifact 上传就是这件事。

本系列的 clean 脚本负责把 test-results / playwright-report / report.xml
一次删净，仓库不留执行痕迹。
