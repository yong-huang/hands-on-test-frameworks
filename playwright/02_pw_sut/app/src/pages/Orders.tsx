// Orders.tsx — 订单区：列表 + 创建 + （admin）删除 + WS 实时状态演进
import { useEffect, useState } from 'react';
import { api, type Order, type Role } from '../api';
import { t, type Lang } from '../i18n';
import { LiveBadge, useWebSocket } from '../App';

const STATUS_KEY = { created: 'created', paid: 'paid', shipped: 'shipped' } as const;

const PAGE_SIZE = 20;   // lab 17：客户端分页，大列表 UI 模式的被测能力

export function OrdersPage({ lang, role }: { lang: Lang; role: Role }) {
    const [orders, setOrders] = useState<Order[]>([]);
    const [title, setTitle] = useState('');
    const [error, setError] = useState('');
    const [page, setPage] = useState(0);
    const tr = (key: Parameters<typeof t>[1]) => t(lang, key);

    // WS 消息驱动重取：订单状态演进由服务端定时器广播（created→paid→shipped）
    const connected = useWebSocket((msg) => {
        if (msg.type === 'order-status' || msg.type === 'order-created' || msg.type === 'order-deleted') {
            api.listOrders().then((r) => setOrders(r.orders)).catch(() => {});
        }
    });

    useEffect(() => {
        api.listOrders().then((r) => setOrders(r.orders)).catch((e) => setError(String(e)));
    }, []);

    const pageCount = Math.max(1, Math.ceil(orders.length / PAGE_SIZE));
    const safePage = Math.min(page, pageCount - 1);
    const visible = orders.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);

    async function create(e: React.FormEvent) {
        e.preventDefault();
        setError('');
        if (!title.trim()) return;
        try { await api.createOrder(title.trim()); setTitle(''); }
        catch (err) { setError(err instanceof Error ? err.message : 'failed'); }
    }

    async function remove(id: string) {
        setError('');
        try { await api.deleteOrder(id); setOrders((prev) => prev.filter((o) => o.id !== id)); }
        catch (err) { setError(err instanceof Error ? err.message : 'failed'); }
    }

    return (
        <section data-testid="orders-page" aria-labelledby="orders-h">
            <h2 id="orders-h">{tr('ordersTitle')}</h2>
            <LiveBadge connected={connected} label={connected ? tr('liveConnected') : tr('liveOff')} />

            <form data-testid="order-form" onSubmit={create}>
                <label>{tr('orderTitle')}
                    <input data-testid="order-title" value={title}
                        onChange={(e) => setTitle(e.target.value)} />
                </label>
                <button data-testid="order-add" type="submit">{tr('addBtn')}</button>
            </form>
            {error && <p role="alert" data-testid="orders-error">{error}</p>}

            <div data-testid="pager" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button data-testid="page-prev" disabled={safePage === 0}
                    onClick={() => setPage(safePage - 1)}>‹</button>
                <span data-testid="page-indicator">
                    {safePage + 1} / {pageCount}（共 {orders.length} 条）
                </span>
                <button data-testid="page-next" disabled={safePage >= pageCount - 1}
                    onClick={() => setPage(safePage + 1)}>›</button>
            </div>

            <ul data-testid="order-list">
                {visible.map((o) => (
                    <li key={o.id} data-testid="order-item" data-order-id={o.id} data-status={o.status}>
                        <span className="title">{o.title}</span>
                        <span className="status">{tr(STATUS_KEY[o.status])}</span>
                        {role === 'admin' && (
                            <button data-testid="order-del" aria-label={`${tr('delBtn')} ${o.title}`}
                                onClick={() => remove(o.id)}>
                                {tr('delBtn')}
                            </button>
                        )}
                    </li>
                ))}
            </ul>
        </section>
    );
}
