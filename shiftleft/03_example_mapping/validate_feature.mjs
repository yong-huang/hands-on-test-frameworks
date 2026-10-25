// validate_feature.mjs —— 用官方 @cucumber/gherkin 解析器校验生成的 feature 文件。
// 复用 cucumber/ 线共享的 node_modules（cucumber 13 的依赖 gherkin 42），按相对路径
// 直接 import，不在本实验里另装依赖。退出码：解析零错误 → 0；有错 → 1 并打印明细。
// 注：gherkin 42 的 AST 里场景与场景大纲都用 children[].scenario（keyword 区分）。
import { AstBuilder, GherkinClassicTokenMatcher, Parser } from
    '../../cucumber/node_modules/@cucumber/gherkin/dist/index.js';
import { readFileSync } from 'node:fs';

const file = process.argv[2];
if (!file) {
    console.error('用法: node validate_feature.mjs <feature 文件>');
    process.exit(2);
}
const source = readFileSync(file, 'utf8');
const parser = new Parser(new AstBuilder(() => 'id'), new GherkinClassicTokenMatcher());
try {
    const ast = parser.parse(source);
    const feature = ast.feature;
    let nScen = 0;
    let nExa = 0;
    for (const c of feature.children) {
        if (!c.scenario) continue;
        nScen += 1;
        nExa += (c.scenario.examples ?? [])
            .reduce((n, e) => n + e.tableBody.length, 0);
    }
    console.log(`✅ gherkin 解析零错误：功能「${feature.name}」，${nScen} 个场景（含大纲），${nExa} 条例子`);
    process.exit(0);
} catch (e) {
    const errs = e.errors ?? [{ message: String(e) }];
    console.error(`❌ gherkin 解析失败（${errs.length} 处）：`);
    for (const x of errs) console.error('  ' + x.message.split('\n')[0]);
    process.exit(1);
}
