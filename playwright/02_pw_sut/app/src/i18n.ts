// i18n.ts — 手写双语文案字典（不引 i18next：靶场保持依赖最小）
// locale 切换由 App 状态驱动，t() 按 key 取词。缺 key 时回退中文——文案矩阵用例（lab 46）会断言中英一致。
export type Lang = 'zh' | 'en';

const DICT = {
    zh: {
        appName: 'pw-store',
        username: '用户名', password: '密码', loginBtn: '登录', logout: '退出',
        loginTitle: '登录 pw-store', loginError: '用户名或密码错误',
        tabOrders: '订单', tabUpload: '上传', tabSlow: '慢加载', tabEmbed: '嵌入区',
        welcome: '欢迎', adminBadge: '管理员', customerBadge: '顾客',
        orderTitle: '商品标题', addBtn: '创建订单', ordersTitle: '订单列表',
        delBtn: '删除', adminOnly: '仅管理员',
        created: '已创建', paid: '已支付', shipped: '已发货',
        uploadTitle: '文件上传与下载', chooseFile: '选择文件', fileList: '已上传文件',
        download: '下载', uploading: '上传中…', uploadDone: '上传成功',
        slowTitle: '慢加载组件', slowLoadBtn: '加载库存数据', loading: '加载中…',
        colSku: 'SKU', colName: '名称', colStock: '库存',
        outOfStock: '缺货',
        embedTitle: 'iframe 与 Shadow DOM', liveConnected: '实时通道已连接', liveOff: '实时通道已断开',
    },
    en: {
        appName: 'pw-store',
        username: 'Username', password: 'Password', loginBtn: 'Sign in', logout: 'Sign out',
        loginTitle: 'Sign in to pw-store', loginError: 'Wrong username or password',
        tabOrders: 'Orders', tabUpload: 'Upload', tabSlow: 'Slow Load', tabEmbed: 'Embed',
        welcome: 'Welcome', adminBadge: 'Admin', customerBadge: 'Customer',
        orderTitle: 'Product title', addBtn: 'Create order', ordersTitle: 'Order list',
        delBtn: 'Delete', adminOnly: 'Admin only',
        created: 'Created', paid: 'Paid', shipped: 'Shipped',
        uploadTitle: 'File upload & download', chooseFile: 'Choose files', fileList: 'Uploaded files',
        download: 'Download', uploading: 'Uploading…', uploadDone: 'Uploaded',
        slowTitle: 'Slow component', slowLoadBtn: 'Load stock data', loading: 'Loading…',
        colSku: 'SKU', colName: 'Name', colStock: 'Stock',
        outOfStock: 'Out of stock',
        embedTitle: 'iframe & Shadow DOM', liveConnected: 'Live channel connected', liveOff: 'Live channel offline',
    },
} as const;

export type DictKey = keyof typeof DICT.zh;

export function t(lang: Lang, key: DictKey): string {
    return DICT[lang][key];
}
