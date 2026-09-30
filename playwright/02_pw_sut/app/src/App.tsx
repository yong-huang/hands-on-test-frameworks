// App.tsx — pw-store 主应用：登录 → 四个功能区 Tab
// 布局刻意朴素：靶场的职责是给测试提供稳定靶点，不是视觉 showcase
import { useEffect, useState } from 'react';
import { api, loadAuth, saveAuth, type Auth } from './api';
import { t, type Lang } from './i18n';
import { OrdersPage } from './pages/Orders';
import { UploadPage } from './pages/Upload';
import { SlowPage } from './pages/Slow';
import { EmbedPage } from './pages/Embed';

type Tab = 'orders' | 'upload' | 'slow' | 'embed';

export function App() {
    // 初始语言跟随浏览器 locale（lab 11 的 locale 仿真靶点）
    const [lang, setLang] = useState<Lang>(() =>
        (navigator.language || 'zh-CN').toLowerCase().startsWith('en') ? 'en' : 'zh');
    const [auth, setAuth] = useState<Auth | null>(() => loadAuth());
    const [tab, setTab] = useState<Tab>('orders');

    const tr = (key: Parameters<typeof t>[1]) => t(lang, key);

    function handleLogin(username: string, password: string) {
        return api.login(username, password).then((a) => {
            saveAuth(a);
            setAuth(a);
        });
    }

    function handleLogout() {
        saveAuth(null);
        setAuth(null);
    }

    if (!auth) return <LoginPage lang={lang} onLogin={handleLogin} />;

    return (
        <div className="app">
            <header data-testid="app-header">
                <h1>{tr('appName')}</h1>
                <span data-testid="welcome" aria-live="polite">
                    {tr('welcome')}，{auth.username}（{auth.role === 'admin' ? tr('adminBadge') : tr('customerBadge')}）
                </span>
                <button data-testid="lang-toggle" onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}>
                    {lang === 'zh' ? 'English' : '中文'}
                </button>
                <button data-testid="logout" onClick={handleLogout}>{tr('logout')}</button>
            </header>

            <nav role="tablist" aria-label="功能区">
                {(['orders', 'upload', 'slow', 'embed'] as Tab[]).map((key) => (
                    <button key={key} role="tab" aria-selected={tab === key}
                        data-testid={`tab-${key}`} onClick={() => setTab(key)}>
                        {tr(key === 'orders' ? 'tabOrders' : key === 'upload' ? 'tabUpload'
                            : key === 'slow' ? 'tabSlow' : 'tabEmbed')}
                    </button>
                ))}
            </nav>

            <main>
                {tab === 'orders' && <OrdersPage lang={lang} role={auth.role} />}
                {tab === 'upload' && <UploadPage lang={lang} />}
                {tab === 'slow' && <SlowPage lang={lang} />}
                {tab === 'embed' && <EmbedPage lang={lang} />}
            </main>
        </div>
    );
}

function LoginPage({ lang, onLogin }: {
    lang: Lang;
    onLogin: (u: string, p: string) => Promise<void>;
}) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const tr = (key: Parameters<typeof t>[1]) => t(lang, key);

    async function submit(e: React.FormEvent) {
        e.preventDefault();
        setError('');
        try { await onLogin(username, password); }
        catch (err) { setError(err instanceof Error ? err.message : tr('loginError')); }
    }

    return (
        <form data-testid="login-form" onSubmit={submit} className="login">
            <h1>{tr('loginTitle')}</h1>
            <label>{tr('username')}
                <input data-testid="login-user" value={username}
                    onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
            </label>
            <label>{tr('password')}
                <input data-testid="login-pass" type="password" value={password}
                    onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
            </label>
            <button data-testid="login-btn" type="submit">{tr('loginBtn')}</button>
            {error && <p role="alert" data-testid="login-error">{error}</p>}
            <p className="hint">admin / admin123 · customer / customer123</p>
        </form>
    );
}

// 实时连接状态徽标：WS 断连时全局可见（lab 45 的断连恢复用例断言它）
export function LiveBadge({ connected, label }: { connected: boolean; label: string }) {
    return (
        <span data-testid="live-badge" className={connected ? 'live on' : 'live off'} role="status">
            {label}
        </span>
    );
}

// 首次挂载时的 WS 预热连接，保证 /ws 通道在订单页外也可用
export function useWebSocket(onMessage: (msg: any) => void) {
    const [connected, setConnected] = useState(false);
    useEffect(() => {
        let ws: WebSocket | null = null;
        let closed = false;
        let timer: number | undefined;

        function connect() {
            const proto = location.protocol === 'https:' ? 'wss' : 'ws';
            ws = new WebSocket(`${proto}://${location.host}/ws`);
            ws.onopen = () => setConnected(true);
            ws.onmessage = (e) => { try { onMessage(JSON.parse(e.data)); } catch { /* 非 JSON 忽略 */ } };
            ws.onclose = () => {
                setConnected(false);
                if (!closed) timer = window.setTimeout(connect, 1000);  // 断线 1s 重连
            };
        }
        connect();
        return () => { closed = true; if (timer) clearTimeout(timer); ws?.close(); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    return connected;
}
