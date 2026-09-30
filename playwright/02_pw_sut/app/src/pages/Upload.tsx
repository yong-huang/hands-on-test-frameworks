// Upload.tsx — 上传区：多文件上传 + 文件列表 + 下载链接（lab 14 的主靶点）
import { useEffect, useRef, useState } from 'react';
import { api, loadAuth, type StoredFile } from '../api';
import { t, type Lang } from '../i18n';

export function UploadPage({ lang }: { lang: Lang }) {
    const [files, setFiles] = useState<StoredFile[]>([]);
    const [busy, setBusy] = useState(false);
    const [done, setDone] = useState(false);
    const [dragging, setDragging] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const tr = (key: Parameters<typeof t>[1]) => t(lang, key);

    function refresh() {
        api.listFiles().then((r) => setFiles(r.files)).catch(() => {});
    }
    useEffect(refresh, []);

    async function uploadAll(picked: File[]) {
        if (!picked.length) return;
        setBusy(true);
        setDone(false);
        try {
            for (const f of picked) await api.upload(f);   // 逐个上传：测试断言"3 个文件全可见"
            setDone(true);
            refresh();
        } finally {
            setBusy(false);
            if (inputRef.current) inputRef.current.value = '';
        }
    }

    async function handleFiles(e: React.ChangeEvent<HTMLInputElement>) {
        await uploadAll(Array.from(e.target.files ?? []));
    }

    // 拖拽上传：drop 事件的 DataTransfer.files 与 input 选择等价处理
    async function handleDrop(e: React.DragEvent) {
        e.preventDefault();
        setDragging(false);
        await uploadAll(Array.from(e.dataTransfer.files ?? []));
    }

    return (
        <section data-testid="upload-page" aria-labelledby="upload-h"
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            style={dragging ? { outline: '2px dashed #1f6feb' } : undefined}>
            <h2 id="upload-h">{tr('uploadTitle')}</h2>

            <label data-testid="upload-choose" className="file-label">
                {busy ? tr('uploading') : tr('chooseFile')}
                <input ref={inputRef} data-testid="upload-input" type="file" multiple
                    style={{ display: 'none' }} onChange={handleFiles} disabled={busy} />
            </label>
            {done && <span role="status" data-testid="upload-done">{tr('uploadDone')}</span>}

            <h3>{tr('fileList')}</h3>
            <ul data-testid="file-list">
                {files.map((f) => (
                    <li key={f.name} data-testid="file-item">
                        <span className="fname">{f.name}</span>
                        <span className="fmeta">{f.size} B · sha256:{f.sha256.slice(0, 12)}…</span>
                        <a data-testid="file-download"
                            href={`/api/files/${f.name}?token=${loadAuth()?.token ?? ''}`}
                            download={f.name}>{tr('download')}</a>
                    </li>
                ))}
            </ul>
        </section>
    );
}
