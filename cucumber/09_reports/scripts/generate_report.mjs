// generate_report.mjs — 从 cucumber.json 渲染活文档 HTML 报告
// multiple-cucumber-html-reporter 兼容 cucumber 13 的 json 格式（本 lab 实测探活通过）
import reporter from 'multiple-cucumber-html-reporter';
import { readFileSync } from 'node:fs';

const data = JSON.parse(readFileSync('reports/cucumber.json', 'utf-8'));
const [first] = data;

reporter.generate({
    jsonDir: 'reports',
    reportPath: 'reports/html',
    displayReportTime: true,
    hideMetadata: false,
    metadata: {
        browser: { name: first?.metadata?.browser?.name ?? 'chromium', version: '—' },
        device: 'local',
        platform: { name: process.platform, version: 'macOS' },
    },
    customData: {
        title: '运行信息',
        data: [
            { label: '项目', value: 'pw-store BDD 活文档（lab 09）' },
            { label: '生成时间', value: new Date().toISOString() },
        ],
    },
});
