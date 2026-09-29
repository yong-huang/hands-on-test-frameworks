// ts_stack.spec.ts — lab 31 主用例：TS 原生栈的四件事
//   ① 定位与断言的基本形  ② 异步渲染的自动等待  ③ web-first 断言  ④ 自定义 fixture
// 对比对象是实验 16-20 的 pytest-playwright：同样的等待语义，但配置与
// 复用机制从"插件参数"变成了"config + 代码级 fixture"。
import { test, expect } from '@playwright/test';

// ---- ① 基本形：role 定位 + web-first 断言 ----
// getByRole 依赖无障碍树（accessible name），是本系列默认的定位首选。
test('页面标题与三个功能区可见', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveTitle(/TS 栈演示页/);
    await expect(page.getByRole('heading', { name: '① 异步列表' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '② 订阅表单' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '③ 动态时钟' })).toBeVisible();
});

// ---- ② 自动等待：点击后接口 800ms 才返回，断言自动等列表渲染完 ----
// 注意没有任何 sleep：expect 的重试语义覆盖了"接口慢"这个不确定性。
test('异步列表：点击加载后无需 sleep 直达结果', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: '加载商品列表' }).click();

    // 列表从空到 3 条 —— toHaveCount 持续轮询 DOM，直到条件成立
    const items = page.getByRole('listitem');
    await expect(items).toHaveCount(3);
    await expect(items.first()).toHaveText('机械键盘');
});

// ---- ③ web-first 断言 vs 立即查询 ----
// 立即查询（page.textContent()）拿到的是"此刻"的值，接口没返回就断言失败；
// web-first（expect(...).toHaveText）拿到的是"最终会成立"的承诺。
test('订阅表单：提交后等待确认号出现', async ({ page }) => {
    await page.goto('/');

    await page.getByLabel('邮箱').fill('learner@example.com');
    await page.getByRole('button', { name: '订阅' }).click();

    // 接口 300ms 后才写 role=status 区 —— web-first 断言自动等它
    await expect(page.getByRole('status')).toContainText('订阅成功');
});

// ---- ④ 自定义 fixture 初识：test.extend 注入"每条用例都好用的东西" ----
// 这里造一个确定性的测试用户。pytest 里等价物是 conftest.py 的 @pytest.fixture；
// TS 栈里 fixture 是代码级函数，带类型推导，还能声明初始化/清理时机（lab 39 深讲）。
type TestUser = { name: string; email: string };

const testWithUser = test.extend<{ user: TestUser }>({
    user: async ({}, use) => {
        const user: TestUser = { name: '学员甲', email: 'learner-31@example.com' };
        await use(user); // 用例体执行期间 user 可用；use 之后可以做清理
    },
});

testWithUser('自定义 fixture：注入的 user 直接可用且带类型', async ({ page, user }) => {
    await page.goto('/');

    // user.name 有类型提示；拼写错误在 tsc --noEmit 阶段就报错，而不是运行时
    await page.getByLabel('邮箱').fill(user.email);
    await page.getByRole('button', { name: '订阅' }).click();

    await expect(page.getByRole('status')).toContainText(`确认号 SUB-${user.email.length}`);
});

// ---- ⑤ 动态内容：时钟每秒都变，用正则断言"形状"而不是"值" ----
test('动态时钟始终是 时:分:秒 形状', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('#clock')).toHaveText(/^\d{2}:\d{2}:\d{2}$/);
});
