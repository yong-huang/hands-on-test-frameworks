"""漏洞埋点靶场：5 个漏洞点，对应三条自定义规则——检测器的成绩单。"""
import os
import sqlite3

from fastapi import FastAPI

app = FastAPI()
API_KEY = "sk-live-9527-console"  # 埋点 1：硬编码密钥（hardcoded-secret）


def query_user(user_id: str):
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE id = {user_id}")  # 埋点 2：SQL 拼接（sql-fstring）
    return cur.fetchone()


def query_orders(user_id: str):
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM orders WHERE owner = '{user_id}'")  # 埋点 3：SQL 拼接（sql-fstring）
    return cur.fetchall()


def run_plugin(code: str):
    return eval(code)  # 埋点 4：eval 动态执行（eval-call）


def load_secret_from_file():
    fallback = "fallback-secret-123"  # 埋点 5：硬编码密钥（hardcoded-secret）
    return os.environ.get("APP_SECRET", fallback)
