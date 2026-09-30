# 14 · 文件上传下载：字节级完整性与拖拽注入

> 文件功能测到"列表里有条目"就算完，等于没测。本实验把闭环走满：
> 多文件上传全部可见、下载落盘后与源字节做 sha256 全量比对、
> DataTransfer 构造拖拽注入、5MB 大文件的时限验证——四条用例一条红线。

## Background

文件功能的常见测试形态是"上传后看见文件名"——但名字可见不代表字节没坏：
编码转换、截断、多 part 边界处理错误，都可能让"看得见"的文件打不开。
完整性必须到字节级：上传前后内容指纹（sha256，文件内容的哈希摘要）
完全一致才算通过。

拖拽上传是另一个盲区：`setInputFiles` 只覆盖 `<input type=file>` 路径，
拖拽走的是 drop 事件与 DataTransfer（拖拽时携带数据的浏览器对象），
入口完全不同。

真实用户两条路都会走，测试也得两条路都到。

## What

pw-store 的上传走 raw body：前端把文件字节直接 PUT 给服务端（免 multipart
表单编码），服务端落盘并记录 sha256；下载是带 `?token=` 的锚点链接，
浏览器原生处理保存。测试要验证的是这条链路的每一环。

可以把文件闭环想成快递：两种寄件方式（表单上传/拖拽）都到同一个分拣中心，
入库时称重贴指纹（sha256 落库），取件凭凭证（token 链接），
收件人开箱验货（下载后比对指纹）。

但和快递不同，字节链路里没有"运输破损"的借口——差一个字节就是缺陷。

![文件闭环：两种注入、一次落盘、指纹比对](images/files.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/14_pw_files/images/files.html)
> （或本地打开 [`images/files.html`](images/files.html)）。
> 外圈虚线是验证闭环：saveAs 落盘后与源字节全量比对，指纹在列表页有前缀展示。

## When to Use

| 断言层级 | 做法 | 强度 |
|:---|:---|:---|
| 列表可见（名字出现） | `filter({ hasText })` 计数 | 最弱，仅证明流程通了 |
| 指纹前缀展示一致 | 列表文案含服务端返回的 sha256 前 12 位 | 中，证明记录正确 |
| 落盘字节全量比对 | download.saveAs 后 sha256 对比源 buffer | 最强，字节级闭环 |

判断口径：**文件类断言至少做到指纹比对**。可见性断言适合当流程的前置等待，
不应当作文件功能的终点。

## Quick Start

```bash
cd playwright/14_pw_files
./files.sh          # apply 体检 → observe 四条用例 + 服务端落盘核对 → clean
```

observe ① 四条用例全绿（多文件 / sha256 完整性 / 拖拽 / 5MB 大文件）：

```
  ✓  1 多文件上传：一次传 3 个，列表全部可见
  ✓  2 下载完整性：UI 下载的字节与源文件 sha256 一致
  ✓  3 拖拽上传：DataTransfer 构造 drop 事件
  ✓  4 大文件：5MB 上传在超时窗口内完成
  4 passed (1.6s)
```

observe ② 是服务端视角的核对——`.uploads/` 里能看到本轮上传的实物文件。
验收方式：四条全绿；下载用例的断言包含三重验证
（下载字节 == 源 buffer、列表指纹前缀 == 下载内容的指纹前缀）；
拖拽用例在开发者工具里禁用 input 元素后依然通过（证明走的是 drop 通道）。

## How It Works

**两种注入通道，语义等价。** `setInputFiles` 操作 `<input type=file>` 元素；
拖拽注入分两步——先在浏览器里构造带 File 的 DataTransfer，
再 `dispatchEvent('drop', { dataTransfer })` 派发到目标区域。

两条路最终都把 File 对象交给同一段上传代码，服务端行为应完全一致——
这正是"等价性"要用测试钉住的原因。

**下载的三步骨架。** `waitForEvent('download')` 先挂监听 → 点击下载链接 →
`download.saveAs(路径)` 落盘。

之后是纯 Node 的事：读回字节、`node:crypto` 算 sha256、与内存里的源 buffer 比对。
挂监听必须先于点击——与 lab 05 的 waitForResponse 是同一个"先等后动"模式。

**下载鉴权走查询参数。** 本实验实测踩过一个坑：锚点下载是浏览器导航请求，
带不了 fetch 层的 Authorization 头，服务端 401 导致 `saveAs: canceled`。

解法是业界标准形态——下载链接附加 `?token=` 查询参数，
服务端鉴权同时接受头与查询参数。pw-store 的 token 是可逆 base64，
前端拼链接零成本；生产系统的等价物是短期签名 URL。

**大文件的断言是"时限内完成"而不是"能完成"。** 5MB 上传在本地毫秒级，
断言真正防的是回归：同步阻塞、或无谓的 base64 转换（体积膨胀 33%），
都会让 15 秒窗口先红。

性能类断言给的都是相对阈值，上线前按真实网络环境重新标定。

## Pitfalls & Q&A

**Q：为什么本实验的用例会受界面语言影响？**
第一版断言写死了"上传成功"文案——跑起来发现是"Uploaded"：Playwright 默认
locale 是 en-US，而 lab 11 给 pw-store 加了语言跟随逻辑（靶场能力反哺测试）。

解法是 config 里固定 `locale: 'zh-CN'`。教训：凡断言文案，先问环境变量——
语言、时区、主题都可能让同一行代码渲染出不同文本。

**Q：`setInputFiles` 能设任意路径吗？**
能，且不经过真实文件选择器对话框——Playwright 直接把 Buffer 或路径注入元素。

本实验全部用 `Buffer.from` 内存造文件：测试自包含（不依赖 fixture 文件入库）、
内容可控（sha256 随手可算）。需要真实二进制（图片/PDF）的场景才落临时目录。

**Q：下载测试为什么不需要清理下载目录？**
`download.saveAs` 的目标路径完全由测试指定（本实验用 mkdtemp 临时目录，
afterEach 删除）。浏览器默认的"下载文件夹"不参与——Playwright 的下载
事件是程序化的，这正是它比手工测试干净的地方。

**Q：拖拽注入的 `dispatchEvent` 和真实拖拽有差别吗？**
有边界：dispatchEvent 直接派发合成事件，绕过了浏览器的拖拽手势状态机
（dragenter 序列、命中测试）。

它验证的是"应用对 drop 事件的响应逻辑"；拖拽手势本身的可用性
属于真机手测范围。对文件拖拽这个场景，drop 响应逻辑就是全部业务，
合成事件足够。

**Q：服务端的 `.uploads/` 为什么也要清？**
测试产物有两个家：测试机的 test-results 与 SUT 侧的 .uploads。

只清前者会让靶场目录无限膨胀，还可能让"列表可见"断言被历史数据污染
（文件列表跨用例累积，lab 02 讲过）。clean 双清是本系列的约定。
