// Slow.tsx — 慢加载区：按钮触发 1.2s 慢接口，期间显示 loading（等待训练靶点）
import { useState } from 'react';
import { api, type SlowRow } from '../api';
import { t, type Lang } from '../i18n';

export function SlowPage({ lang }: { lang: Lang }) {
    const [rows, setRows] = useState<SlowRow[] | null>(null);
    const [loading, setLoading] = useState(false);
    const tr = (key: Parameters<typeof t>[1]) => t(lang, key);

    async function load() {
        setLoading(true);
        setRows(null);
        try { setRows((await api.slowData()).rows); }
        finally { setLoading(false); }
    }

    return (
        <section data-testid="slow-page" aria-labelledby="slow-h">
            <h2 id="slow-h">{tr('slowTitle')}</h2>
            <button data-testid="slow-load" onClick={load} disabled={loading}>
                {tr('slowLoadBtn')}
            </button>
            {loading && <p role="status" data-testid="slow-loading">{tr('loading')}</p>}

            {rows && (
                <table data-testid="slow-table">
                    <thead>
                        <tr><th>{tr('colSku')}</th><th>{tr('colName')}</th><th>{tr('colStock')}</th></tr>
                    </thead>
                    <tbody>
                        {rows.map((r) => (
                            <tr key={r.sku} data-testid="slow-row">
                                <td>{r.sku}</td><td>{r.name}</td>
                                <td>{r.stock > 0 ? String(r.stock) : tr('outOfStock')}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </section>
    );
}
