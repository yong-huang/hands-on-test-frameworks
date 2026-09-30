// components.tsx — lab 07 被测组件：pw-store 订单区的三个纯展示组件
// 刻意不含网络与全局状态：props 进、事件出——组件测试的理想对象
import { useState } from 'react';
import type { Order } from '../../02_pw_sut/app/src/api';

export function StatusBadge({ status }: { status: Order['status'] }) {
    const label = { created: '已创建', paid: '已支付', shipped: '已发货' }[status];
    return <span className={`badge ${status}`} data-testid="status-badge">{label}</span>;
}

export function OrderCard({ order, onDelete }: {
    order: Order;
    onDelete?: (id: string) => void;
}) {
    return (
        <div className="card" data-testid="order-card">
            <span className="title">{order.title}</span>
            <StatusBadge status={order.status} />
            {onDelete && (
                <button data-testid="card-delete" onClick={() => onDelete(order.id)}>删除</button>
            )}
        </div>
    );
}

export function OrderForm({ onCreate }: { onCreate: (title: string) => void }) {
    const [title, setTitle] = useState('');

    function submit(e: React.FormEvent) {
        e.preventDefault();
        const trimmed = title.trim();
        if (!trimmed) return;
        onCreate(trimmed);
        setTitle('');
    }

    return (
        <form data-testid="order-form" onSubmit={submit}>
            <input data-testid="form-input" value={title} placeholder="商品标题"
                onChange={(e) => setTitle(e.target.value)} />
            <button data-testid="form-submit" type="submit">创建订单</button>
        </form>
    );
}

// 带插槽（children）的卡片容器：演示对 children 的挂载与透传断言
export function CardShell({ header, children }: {
    header: string;
    children?: React.ReactNode;
}) {
    return (
        <section data-testid="card-shell" className="card">
            <strong>{header}</strong>
            {children}
        </section>
    );
}
