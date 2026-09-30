// files.spec.ts — lab 14：文件上传下载四件事
//   多文件上传 · 下载 sha256 完整性 · 拖拽上传 · 5MB 大文件
import { createHash } from 'node:crypto';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test, expect } from '@playwright/test';

const API = 'http://127.0.0.1:9014';
const sha256 = (buf: Buffer) => createHash('sha256').update(buf).digest('hex');

// 测试工作台：每个用例独立的临时目录 + 登录态
function makeFile(name: string, content: string | Buffer): { name: string; mimeType: string; buffer: Buffer } {
    const buffer = Buffer.isBuffer(content) ? content : Buffer.from(content, 'utf-8');
    return { name, mimeType: 'application/octet-stream', buffer };
}

async function login(page: import('@playwright/test').Page) {
    const res = await fetch(`${API}/api/login`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' }),
    });
    const { token } = (await res.json()) as { token: string };
    await page.addInitScript((tk) => {
        localStorage.setItem('pw-store-auth',
            JSON.stringify({ token: tk, role: 'admin', username: 'admin' }));
    }, token);
}

test.describe(() => {
    let dir: string;
    test.beforeEach(async ({ page }) => {
        dir = mkdtempSync(join(tmpdir(), 'pw14-'));
        await login(page);
        await page.goto('/');
        await page.getByTestId('tab-upload').click();
    });
    test.afterEach(() => rmSync(dir, { recursive: true, force: true }));

    test('多文件上传：一次传 3 个，列表全部可见', async ({ page }) => {
        const files = [
            makeFile('lab14-a.txt', 'alpha content'),
            makeFile('lab14-b.txt', 'beta content'),
            makeFile('lab14-c.txt', 'gamma content'),
        ];
        await page.getByTestId('upload-input').setInputFiles(files);

        for (const f of files) {
            await expect(page.getByTestId('file-item').filter({ hasText: f.name }))
                .toHaveCount(1);
        }
        await expect(page.getByTestId('upload-done')).toContainText('上传成功');
    });

    test('下载完整性：UI 下载的字节与源文件 sha256 一致', async ({ page }) => {
        const src = makeFile('lab14-dl.bin', 'downloadable payload '.repeat(100));
        await page.getByTestId('upload-input').setInputFiles([src]);
        const row = page.getByTestId('file-item').filter({ hasText: 'lab14-dl.bin' });
        await expect(row).toHaveCount(1);

        // 服务端公布的 sha256（上传响应里记录的指纹）
        const listedSha = await row.locator('.fmeta').textContent();
        expect(listedSha).toBeTruthy();

        // UI 触发下载并落盘
        const [download] = await Promise.all([
            page.waitForEvent('download'),
            row.getByTestId('file-download').click(),
        ]);
        const localPath = join(dir, download.suggestedFilename());
        await download.saveAs(localPath);

        // 完整性双验证：与源 buffer 一致，且与列表页展示的指纹前缀一致
        const downloaded = readFileSync(localPath);
        expect(sha256(downloaded)).toBe(sha256(src.buffer));
        expect(listedSha).toContain(sha256(downloaded).slice(0, 12));
    });

    test('拖拽上传：DataTransfer 构造 drop 事件', async ({ page }) => {
        const payload = 'dragged content';
        // 在浏览器里构造带 File 的 DataTransfer，再向上传区派发 drop 事件
        const dataTransfer = await page.evaluateHandle((content) => {
            const dt = new DataTransfer();
            dt.items.add(new File([content], 'lab14-dragged.txt', { type: 'text/plain' }));
            return dt;
        }, payload);

        await page.getByTestId('upload-page').dispatchEvent('drop', { dataTransfer });

        const row = page.getByTestId('file-item').filter({ hasText: 'lab14-dragged.txt' });
        await expect(row).toHaveCount(1);

        // 内容一致性：下载回来与拖入的字节相同
        const [download] = await Promise.all([
            page.waitForEvent('download'),
            row.getByTestId('file-download').click(),
        ]);
        const p = join(dir, 'dragged.bin');
        await download.saveAs(p);
        expect(readFileSync(p).toString('utf-8')).toBe(payload);
    });

    test('大文件：5MB 上传在超时窗口内完成', async ({ page }) => {
        const big = Buffer.alloc(5 * 1024 * 1024, 97); // 5MB 'a'
        const started = Date.now();
        await page.getByTestId('upload-input').setInputFiles([makeFile('lab14-big.bin', big)]);
        await expect(page.getByTestId('file-item').filter({ hasText: 'lab14-big.bin' }))
            .toHaveCount(1, { timeout: 15_000 });
        expect(Date.now() - started).toBeLessThan(15_000);
    });
});
