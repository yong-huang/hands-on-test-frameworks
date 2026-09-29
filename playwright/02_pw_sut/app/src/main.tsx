// main.tsx — 应用入口 + Shadow DOM 自定义元素 <pw-badge>（lab 03 穿透定位靶点）
import { createRoot } from 'react-dom/client';
import { App } from './App';
import './styles.css';

// 自定义元素：open shadow root 内一个点赞按钮。
// 点击时向外交发 composed CustomEvent（穿透 shadow 边界冒泡到主文档），
// React 侧监听它更新主文档计数——这正是"shadow 内操作 → 主文档断言"的教材场景。
class PwBadge extends HTMLElement {
    private count = 0;

    connectedCallback() {
        const label = this.getAttribute('label') ?? 'badge';
        const shadow = this.attachShadow({ mode: 'open' });
        shadow.innerHTML = `
            <style>
                button { padding: 4px 10px; border-radius: 6px; border: 1px solid #888; cursor: pointer; }
            </style>
            <button type="button" data-testid="shadow-btn">${label} <span data-testid="shadow-count">0</span></button>
        `;
        const btn = shadow.querySelector('button')!;
        btn.addEventListener('click', () => {
            this.count += 1;
            shadow.querySelector('[data-testid="shadow-count"]')!.textContent = String(this.count);
            this.dispatchEvent(new CustomEvent('badge-click', {
                detail: { count: this.count },
                bubbles: true,
                composed: true,
            }));
        });
    }
}

if (!customElements.get('pw-badge')) {
    customElements.define('pw-badge', PwBadge);
}

createRoot(document.getElementById('root')!).render(<App />);
