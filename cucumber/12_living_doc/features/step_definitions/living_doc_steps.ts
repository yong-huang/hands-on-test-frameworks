// living_doc_steps.ts — 活文档演示步骤：docstring 消费 + pending 语义
import { Given, Then, When } from '@cucumber/cucumber';
import { DocPage } from '../../pages/doc_page.ts';

interface ReturnRequest {
    商品: string;
    购买天数: number;
    是否使用: string;
}

/** 极简退货规则引擎（演示"场景即规格"的判定逻辑） */
function evaluate(req: ReturnRequest): { approved: boolean; reason?: string } {
    if (req.购买天数 > 30) return { approved: false, reason: '超过退货期限' };
    return { approved: true };
}

Given('管理员已登录', async function (this: any) {
    const { DocPage } = await import('../../pages/doc_page.ts');
    const doc = new DocPage(this.page);
    await doc.goto();
});

When('提交如下退货申请', async function (this: any, docstring: string) {
    // docstring（三引号块）原样进入步骤——多行业务数据的标准通道
    this.capturedDoc = docstring;
    const req: Partial<ReturnRequest> = {};
    for (const line of docstring.split('\n')) {
        const [k, v] = line.split(':').map((s) => s.trim());
        if (k && v) (req as Record<string, string>)[k] = v;
    }
    req.购买天数 = Number(req.购买天数);
    this.lastResult = evaluate(req as ReturnRequest);
});

Then('退货申请应被受理', async function (this: any) {
    if (!this.lastResult?.approved) throw new Error(`应受理，实际: ${JSON.stringify(this.lastResult)}`);
});

Then('退货申请应被拒绝且原因是 {string}', async function (this: any, reason: string) {
    if (this.lastResult?.approved) throw new Error('应被拒绝');
    if (this.lastResult?.reason !== reason) {
        throw new Error(`原因不符: 期望 ${reason}，实际 ${this.lastResult?.reason}`);
    }
});

// 该规则尚未实现——步骤返回 pending 字符串，cucumber 标记为 pending（黄）
When('提交已拆封电子产品的退货申请', async function (this: any) {
    return 'pending';
});

Then('申请应转为换新流程', async function (this: any) {
    return 'pending';
});
