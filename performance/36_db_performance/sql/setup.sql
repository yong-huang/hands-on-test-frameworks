-- 项目 6 观测基建：扩展与慢查询阈值（幂等，可反复执行）
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 超过 50ms 的语句记入日志（docker logs 可查）
ALTER SYSTEM SET log_min_duration_statement = '50ms';
SELECT pg_reload_conf();

-- 清空排行榜，从本轮压测重新累计
SELECT pg_stat_statements_reset();
