"""干净对照：同样的业务动作，全部走安全写法——零误报的试金石。"""
import ast
import os
import sqlite3

from fastapi import FastAPI

app = FastAPI()
API_KEY = os.environ["APP_API_KEY"]  # 从环境读取，非字面量赋值


def query_user(user_id: str):
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))  # 参数化查询
    return cur.fetchone()


def safe_literal(expr: str):
    return ast.literal_eval(expr)  # 字面量求值，不执行任意代码


def load_secret():
    return os.environ.get("APP_SECRET", "")  # 兜底是空串，不是密钥
