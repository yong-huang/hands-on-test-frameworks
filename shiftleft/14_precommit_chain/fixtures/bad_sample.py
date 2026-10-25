"""违禁样本：含 GitHub PAT 形态的假密钥——专供「坏提交被真实阻断」演示。

（令牌为公开示例形态，非真实凭据；实测可命中 gitleaks 默认规则 github-pat。）
"""


def connect_staging():
    api_key = "ghp_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7RS"
    return {"Authorization": f"Bearer {api_key}"}
