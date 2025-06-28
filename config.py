DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "050701",
    "database": "college"
}

TONGYI_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
TONGYI_API_KEY = "sk-b1423fb8e0af4be0be479e90e46471c1"

# 敏感字段配置
SENSITIVE_FIELDS = [
    'password',      # 密码
    'salary',        # 薪资
    'credit_card',   # 信用卡
    'ssn',          # 社会安全号
    'phone',        # 电话
    'email',        # 邮箱
    'address',      # 地址
    'id_card',      # 身份证
    'bank_account', # 银行账户
    'social_security', # 社保号
    'passport',     # 护照
    'driver_license', # 驾照
    'medical_record', # 医疗记录
    'tax_id',       # 税号
    'secret_key',   # 密钥
    'api_key',      # API密钥
    'token',        # 令牌
    'private_key',  # 私钥
    'encrypted',    # 加密字段
    'hash'          # 哈希字段
] 