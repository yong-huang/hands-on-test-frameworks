-- shorturl 库表：5000 条种子短链是线性扫描缺陷的"燃料"
\c shorturl

CREATE TABLE links (
    code       TEXT PRIMARY KEY,
    url        TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO links (code, url)
SELECT
    's' || lpad(g::text, 5, '0'),
    'https://example.com/long/target/' || g
FROM generate_series(1, 5000) AS g
ON CONFLICT (code) DO NOTHING;

-- init 脚本以 POSTGRES_USER(shop) 身份执行，把表交给 shorturl 角色
ALTER TABLE links OWNER TO shorturl;

