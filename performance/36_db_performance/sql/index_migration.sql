-- 索引迁移（项目 6 的"修复"）：EXECUTE 前后各做一次 EXPLAIN 留证
-- 注意用 CONCURRENTLY 不锁写；本实验量级下普通 CREATE INDEX 亦可
CREATE INDEX IF NOT EXISTS idx_stock_product_id ON stock (product_id);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders (product_id);
ANALYZE stock;
ANALYZE orders;
