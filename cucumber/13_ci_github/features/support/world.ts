// features/support/world.ts — CI 冒烟集 World（轻量：仅 API 冒烟，无浏览器）
import {
    Before, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import type { Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9114';
setDefaultTimeout(15_000);
const TOKEN = Buffer.from('admin:admin').toString('base64');

export class CIWorld extends World {
    page: Page | null = null;   // API 冒烟不需要浏览器 page，字段保留兼容

    /** API 健康探活 */
    async healthy(): Promise<boolean> {
        try {
            const res = await fetch(`${BASE_URL}/api/health`);
            return res.status === 200;
        } catch { return false; }
    }

    async apiCreate(title: string): Promise<number> {
        const res = await fetch(`${BASE_URL}/api/orders`, {
            method: 'POST',
            headers: { 'content-type': 'application/json', authorization: `Bearer ${TOKEN}` },
            body: JSON.stringify({ title }),
        });
        return res.status;
    }

    async orderCount(): Promise<number> {
        const res = await fetch(`${BASE_URL}/api/orders`, {
            headers: { authorization: `Bearer ${TOKEN}` },
        });
        return ((await res.json()) as { orders: unknown[] }).orders.length;
    }
}

Before(async function (this: CIWorld) {
    await fetch(`${BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { authorization: `Bearer ${TOKEN}` },
    });
});

setWorldConstructor(CIWorld);
