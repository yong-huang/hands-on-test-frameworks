"""密钥泄漏靶场：三段假钥匙（公开示例形态，非真实凭据）。

注意（实测）：gitleaks 8.30 默认规则对裸 AKIA AccessKeyId 不告警（规则集
变化），因此靶场的报红由下面两条组成——secret 赋值行命中 generic-api-key、
ghp_ 令牌命中 github-pat。AKIA 行保留，用于说明「默认规则也有盲区」。
"""
import boto3


def connect_dev():
    # 埋点 1：AWS secret 赋值行 → gitleaks generic-api-key 命中
    return boto3.client(
        "s3",
        aws_access_key_id="AKIAVQ2WDKN3RM7PLQ8Z",
        aws_secret_access_key="Zk9pQ3wR7tY5uI1oP0aS9dF8gH2jK4l6MzX8cV2b",
    )


def connect_staging():
    # 埋点 2：GitHub PAT 形态 → gitleaks github-pat 命中
    api_key = "ghp_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7RS"
    return {"Authorization": f"Bearer {api_key}"}
