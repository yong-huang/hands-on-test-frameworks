// api.ts — 前端 API 封装：统一带 token、统一错误处理
export type Role = 'admin' | 'customer';

const AUTH_KEY = 'pw-store-auth';

export type Auth = { token: string; role: Role; username: string };

export function loadAuth(): Auth | null {
    try {
        const raw = localStorage.getItem(AUTH_KEY);
        return raw ? (JSON.parse(raw) as Auth) : null;
    } catch { return null; }
}

export function saveAuth(auth: Auth | null) {
    if (auth) localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
    else localStorage.removeItem(AUTH_KEY);
}

export class ApiError extends Error {
    constructor(public status: number, message: string) { super(message); }
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
    const authState = loadAuth();
    const headers = new Headers(opts.headers);
    if (authState) headers.set('authorization', `Bearer ${authState.token}`);
    if (opts.body && !(opts.body instanceof Blob)) headers.set('content-type', 'application/json');
    const res = await fetch(path, { ...opts, headers });
    if (!res.ok) {
        const body = await res.json().catch(() => ({ error: res.statusText }));
        throw new ApiError(res.status, body.error || res.statusText);
    }
    return res.json() as Promise<T>;
}

export const api = {
    login: (username: string, password: string) =>
        request<Auth>('/api/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
    listOrders: () => request<{ orders: Order[] }>('/api/orders'),
    createOrder: (title: string) =>
        request<{ order: Order }>('/api/orders', { method: 'POST', body: JSON.stringify({ title }) }),
    deleteOrder: (id: string) => request<{ ok: true }>(`/api/orders/${id}`, { method: 'DELETE' }),
    upload: (file: File) =>
        request<{ name: string; size: number; sha256: string }>(
            `/api/upload?name=${encodeURIComponent(file.name)}`,
            { method: 'PUT', body: file }),
    listFiles: () => request<{ files: StoredFile[] }>('/api/files'),
    slowData: () => request<{ rows: SlowRow[] }>('/api/slow-data'),
};

export type Order = { id: string; title: string; status: 'created' | 'paid' | 'shipped'; owner: string };
export type StoredFile = { name: string; size: number; sha256: string };
export type SlowRow = { sku: string; name: string; stock: number };
