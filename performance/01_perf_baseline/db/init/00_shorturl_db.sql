-- 官方 postgres 镜像只会建 POSTGRES_USER + POSTGRES_DB（shop），
-- shorturl 服务单独建用户建库；建完由 02_shorturl.sql 的 \c 切过去灌种子
CREATE USER shorturl WITH PASSWORD 'shorturl';
CREATE DATABASE shorturl OWNER shorturl;
