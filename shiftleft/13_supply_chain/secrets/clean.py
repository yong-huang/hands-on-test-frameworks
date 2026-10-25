"""干净对照：凭据全部来自环境变量，代码里没有任何字面量钥匙。"""
import os

import boto3


def connect_dev():
    return boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )
