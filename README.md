# 基于MCP服务的智能SQL查询系统

##  系统架构

```
用户界面 (CLI/GUI) → MCP客户端 → MCP服务器 → 通义API → 数据库
```

### 核心组件

1. **MCP服务器** (`mcp_server.py`)
   - 统一管理数据库访问
   - 集成通义大模型API
   - 提供标准化服务接口

2. **MCP客户端** (`mcp_client.py`)
   - 与MCP服务器通信
   - 支持同步和异步调用
   - 完整的查询流程处理

3. **数据库管理器** (`db_manager.py`)
   - 数据库连接管理
   - 自动获取数据库结构
   - 智能SQL执行

4. **通义API集成** (`tongyi_api.py`)
   - 自然语言转SQL
   - 错误处理和重试机制

## 功能特性

### 已实现功能
- **自然语言转SQL**: 支持中文自然语言查询
- **智能数据库结构获取**: 自动分析表结构和关系
- **多类型查询支持**: SELECT、SHOW、DESCRIBE
- **双交互模式**: CLI命令行 + Streamlit可视化界面
- **MCP服务架构**: 统一的服务管理和错误处理
- **长结果分页**: 支持长查询结果的分页显示和导航

## 安装和配置
**项目在python=3.12.2上可运行，推荐python>3.12**
### 1. 下载源代码
```bash
git clone https://github.com/s1mple543/MCP-MySQL-Server.git
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置数据库和API
编辑 `config.py`:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "your_database"
}

TONGYI_API_KEY = "your_tongyi_api_key"
```

## 使用方法

### 方式1: CLI命令行模式
```bash
python cli.py
```

### 方式2: Streamlit可视化界面
```bash
streamlit run gui.py
```


##  查询示例

### 数据查询
- "查询所有学生信息"
- "显示成绩大于80分的学生"
- "统计每个班级的学生人数"

### 表结构查询
- "显示所有表"
- "查看学生表的结构"
- "显示表的字段信息"

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库配置
   - 确认数据库服务运行状态
   - 验证用户名和密码

2. **通义API调用失败**
   - 检查API密钥配置
   - 确认网络连接
   - 查看API配额限制

## 日志功能

系统提供完整的查询日志记录，**CLI和GUI的日志统一存放在 `logs` 文件夹下**：

### 日志文件结构
```
logs/
├── query_log.jsonl      # 查询日志（JSONL格式）
├── error_log.jsonl      # 错误日志（JSONL格式）
└── stats.json          # 统计信息（JSON格式）
```

### 日志内容
- **查询统计**: 总查询数、成功率、执行时间统计
- **最近查询**: 查看最近的查询记录
- **错误日志**: 查看失败的查询和错误信息
- **详细记录**: 包含自然语言查询、生成SQL、执行时间、结果状态

### 日志统一性
- **路径统一**: 无论是启动CLI或GUI，日志都存放在 `logs` 文件夹下
- **格式统一**: CLI和GUI使用相同的日志格式和存储方式
- **统计统一**: 所有查询统计信息统一管理 

## 安全限制

系统实现了严格的安全限制，**只允许执行查询语句**：

### 允许的SQL类型
- `SELECT` - 数据查询
- `SHOW` - 显示数据库信息
- `DESCRIBE` / `DESC` - 查看表结构
- `EXPLAIN` - 查看执行计划

### 禁止的SQL类型
- `INSERT` - 数据插入
- `UPDATE` - 数据更新
- `DELETE` - 数据删除
- `DROP` - 删除表/数据库
- `CREATE` - 创建表/数据库
- `ALTER` - 修改表结构
- 其他修改数据的语句

### 敏感字段访问控制

系统禁止访问包含敏感信息的字段：

#### 禁止访问的敏感字段
- `password` - 密码
- `salary` - 薪资
- `credit_card` - 信用卡
- `phone` - 电话
- `email` - 邮箱
- `address` - 地址
- `id_card` - 身份证
- `bank_account` - 银行账户
- `social_security` - 社保号
- `passport` - 护照
- `driver_license` - 驾照
- `medical_record` - 医疗记录
- `tax_id` - 税号
- `secret_key` - 密钥
- `api_key` - API密钥
- `token` - 令牌
- `private_key` - 私钥
- `encrypted` - 加密字段
- `hash` - 哈希字段

#### 检查机制
- **直接字段检查**: 检查SQL语句中是否直接包含敏感字段名
- **表结构检查**: 对于 `SELECT *` 查询，检查表结构是否包含敏感字段
- **多语句支持**: 在多语句执行中，每个语句都会进行敏感字段检查
- **配置化管理**: 敏感字段列表在 `config.py` 中配置，便于维护

### 安全机制
- **SQL解析**: 系统会解析每个SQL语句的开头关键字
- **类型检查**: 只允许以查询关键字开头的语句执行
- **敏感字段检查**: 检查是否访问敏感字段
- **错误提示**: 对于不允许的语句，会返回明确的安全限制错误信息
- **多语句支持**: 在多语句执行中，每个语句都会进行安全检查

### 错误示例
```
安全限制：只允许执行查询语句（SELECT、SHOW、DESCRIBE等），当前语句类型不允许执行
安全限制：禁止访问敏感字段 'password'，该字段包含敏感信息
安全限制：表 'users' 包含敏感字段 'password'，禁止访问
``` 