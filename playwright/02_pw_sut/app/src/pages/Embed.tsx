// Embed.tsx — 嵌入区：iframe（帧穿透靶点）+ Shadow DOM 组件（穿透定位靶点）
import { useEffect, useRef, useState } from 'react';
import { t, type Lang } from '../i18n';

export function EmbedPage({ lang }: { lang: Lang }) {
    const [badgeCount, setBadgeCount] = useState(0);
    const badgeRef = useRef<HTMLElement>(null);
    const tr = (key: Parameters<typeof t>[1]) => t(lang, key);

    // React 不认识自定义事件，用 ref 手工挂监听：
    // shadow 内点击 → composed 事件冒泡到主文档 → 主文档计数更新
    useEffect(() => {
        const el = badgeRef.current;
        if (!el) return;
        const onClick = (e: Event) => setBadgeCount((e as CustomEvent).detail.count);
        el.addEventListener('badge-click', onClick);
        return () => el.removeEventListener('badge-click', onClick);
    }, []);

    return (
        <section data-testid="embed-page" aria-labelledby="embed-h">
            <h2 id="embed-h">{tr('embedTitle')}</h2>

            {/* iframe：测试需用 frameLocator 穿透（lab 03 靶点） */}
            <iframe data-testid="embed-iframe" src="/embedded.html" title="iframe 内部面板" />

            {/* Shadow DOM：自定义元素挂 open shadow root，lab 03 演示选择器穿透 */}
            <div className="badge-zone">
                <pw-badge ref={badgeRef} data-testid="shadow-host" label="Shadow 内部点赞" />
                <span data-testid="badge-count">{badgeCount}</span>
            </div>
        </section>
    );
}

// JSX 认识 <pw-badge> 标签所需的类型扩充
declare global {
    // eslint-disable-next-line @typescript-eslint/no-namespace
    namespace JSX { interface IntrinsicElements { 'pw-badge': any; } }
}
