// extract_features.mjs — 从 cucumber.json 抽取业务功能清单（活文档的文本形态）
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';

const data = JSON.parse(readFileSync('reports/cucumber.json', 'utf-8'));
const STATUS = { passed: '✅ 通过', failed: '❌ 失败', pending: '🟡 规划中' };

let md = '# pw-store 功能清单（活文档）\n\n';
md += '> 由 cucumber.json 自动生成——场景即功能，状态即实现进度\n\n';

for (const feature of data) {
    md += `## ${feature.keyword}: ${feature.name}\n\n`;
    if (feature.description) md += `${feature.description}\n\n`;
    for (const el of feature.elements ?? []) {
        const status = el.steps.every((s) => s.result?.status === 'passed')
            ? 'passed'
            : el.steps.some((s) => s.result?.status === 'pending') ? 'pending' : 'failed';
        md += `- ${STATUS[status] ?? status}｜${el.name}\n`;
    }
    md += '\n';
}

mkdirSync('reports', { recursive: true });
writeFileSync('reports/features.md', md);
console.log('>>> 功能清单已生成: reports/features.md');
