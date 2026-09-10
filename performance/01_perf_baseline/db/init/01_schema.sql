-- perf-shop 库表：结构刻意"裸奔"——该有的索引先不给，
-- 留给项目 6 用 EXPLAIN ANALYZE 亲手补
CREATE TABLE products (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE stock (
    product_id INT NOT NULL,
    qty        INT NOT NULL DEFAULT 0
    -- 没有索引：项目 6 的 Seq Scan 教学素材
);

CREATE TABLE orders (
    id         SERIAL PRIMARY KEY,
    user_id    INT NOT NULL,
    product_id INT NOT NULL,
    qty        INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    -- 没有索引：高频写入 + 项目 6 的素材
);

-- 种子数据：200 个商品 + 各 1000 件库存
INSERT INTO products (name, price)
SELECT
    'product-' || g,
    round((random() * 500 + 5)::numeric, 2)
FROM generate_series(1, 200) AS g;

INSERT INTO stock (product_id, qty)
SELECT g, 1000 FROM generate_series(1, 200) AS g;

-- lab 04 修复版依赖：预计算推荐打分表
CREATE TABLE IF NOT EXISTS recommend_scores (
    product_id INT PRIMARY KEY,
    score      INT NOT NULL DEFAULT 0
);
