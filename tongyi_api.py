import requests
from config import TONGYI_API_URL, TONGYI_API_KEY

# 全局对话上下文存储
conversation_context = {
    "previous_queries": [],
    "table_schema": "",
    "current_session": None
}

def nl2sql(nl_query, db_schema="", session_id=None):
    """
    将自然语言转换为SQL，支持对话上下文优化
    :param nl_query: 自然语言查询
    :param db_schema: 数据库结构信息
    :param session_id: 会话ID，用于维护上下文
    :return: 生成的SQL语句
    """
    global conversation_context
    
    # 更新会话上下文
    if session_id:
        if conversation_context["current_session"] != session_id:
            # 新会话，重置上下文
            conversation_context = {
                "previous_queries": [],
                "table_schema": db_schema,
                "current_session": session_id
            }
        else:
            # 同一会话，保持上下文
            if db_schema and not conversation_context["table_schema"]:
                conversation_context["table_schema"] = db_schema
    
    headers = {
        "Authorization": f"Bearer {TONGYI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建示例对（Few-shot Learning）
    examples = """
【示例对话1】
用户：查询所有学生的姓名和年龄
SQL：SELECT name, age FROM student;

用户：其中成绩大于80分的
SQL：SELECT name, age FROM student WHERE score > 80;

用户：按年龄降序排列
SQL：SELECT name, age FROM student WHERE score > 80 ORDER BY age DESC;

【示例对话2】
用户：显示所有表
SQL：SHOW TABLES;

用户：查看学生表的结构
SQL：DESCRIBE student;

用户：查询学生表中的前5条记录
SQL：SELECT * FROM student LIMIT 5;

【示例对话3】
用户：统计每个班级的学生人数
SQL：SELECT class_id, COUNT(*) as student_count FROM student GROUP BY class_id;

用户：只显示人数大于10的班级
SQL：SELECT class_id, COUNT(*) as student_count FROM student GROUP BY class_id HAVING COUNT(*) > 10;

用户：按人数降序排列
SQL：SELECT class_id, COUNT(*) as student_count FROM student GROUP BY class_id HAVING COUNT(*) > 10 ORDER BY student_count DESC;

【示例对话4】
用户：查询成绩最高的学生
SQL：SELECT * FROM student ORDER BY score DESC LIMIT 1;

用户：查询成绩前10名的学生
SQL：SELECT * FROM student ORDER BY score DESC LIMIT 10;

用户：查询平均成绩
SQL：SELECT AVG(score) as average_score FROM student;

【示例对话5】
用户：查询姓张的学生
SQL：SELECT * FROM student WHERE name LIKE '张%';

用户：查询名字包含"明"的学生
SQL：SELECT * FROM student WHERE name LIKE '%明%';

用户：查询年龄在18到25岁之间的学生
SQL：SELECT * FROM student WHERE age BETWEEN 18 AND 25;
"""
    
    # 构建上下文信息
    context_info = ""
    if conversation_context["previous_queries"]:
        context_info = "\n【对话上下文】\n"
        for i, (query, sql) in enumerate(conversation_context["previous_queries"][-3:], 1):
            context_info += f"第{i}次查询：{query}\n生成SQL：{sql}\n"
        context_info += "\n"
    
    # 优化后的Prompt模板
    if db_schema:
        prompt = f"""
你是一个资深MySQL数据库专家，请根据下方数据库结构和自然语言需求，生成**高质量、准确、可直接执行**的MySQL SQL语句。

【数据库结构】
{db_schema}

{examples}

{context_info}

【生成要求】
1. 只返回**MySQL标准SQL语句**，不要任何解释说明。
2. SQL必须严格匹配表名、字段名、字段类型，注意主键、外键、唯一约束等。
3. 字段类型要与表结构一致，避免类型错误。
4. 查询条件、排序、分组等要与自然语言需求完全对应。
5. 如需多语句，**每条SQL用分号分隔**，不要换行。
6. 不要生成DROP/DELETE/UPDATE/INSERT等修改或删除数据的语句。
7. 如需统计、聚合、分组、连接等操作，优先用标准SQL写法。
8. 查询结果字段顺序与自然语言描述一致。
9. 不要生成任何注释、解释、markdown、自然语言，只输出SQL。
10. 若自然语言有歧义，优先选择最常见的业务场景。
11. **注意上下文连续性**：如果当前查询是对之前查询的补充或修改，请基于上下文生成合适的SQL。

【自然语言需求】
{nl_query}

【输出格式】
只输出SQL语句，不要任何解释、注释、markdown。
"""
    else:
        prompt = f"""
你是一个资深MySQL数据库专家，请将下方自然语言需求转换为**高质量、准确、可直接执行**的MySQL SQL语句。

{examples}

{context_info}

【生成要求】
1. 只返回**MySQL标准SQL语句**，不要任何解释说明。
2. SQL必须严格匹配表名、字段名、字段类型。
3. 查询条件、排序、分组等要与自然语言需求完全对应。
4. 如需多语句，**每条SQL用分号分隔**，不要换行。
5. 不要生成DROP/DELETE/UPDATE/INSERT等修改或删除数据的语句。
6. 不要生成任何注释、解释、markdown、自然语言，只输出SQL。
7. **注意上下文连续性**：如果当前查询是对之前查询的补充或修改，请基于上下文生成合适的SQL。

【自然语言需求】
{nl_query}

【输出格式】
只输出SQL语句，不要任何解释、注释、markdown。
"""
    
    data = {
        "model": "qwen-turbo",
        "input": {"prompt": prompt}
    }
    
    try:
        response = requests.post(TONGYI_API_URL, headers=headers, json=data)
        response.raise_for_status()  # 检查HTTP错误
        result = response.json()
        
        if "output" in result and "text" in result["output"]:
            sql = result["output"]["text"].strip()
            # 清理可能的markdown格式
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.endswith("```"):
                sql = sql[:-3]
            
            sql = sql.strip()
            
            # 更新对话上下文
            if session_id:
                conversation_context["previous_queries"].append((nl_query, sql))
                # 保持最近5次对话
                if len(conversation_context["previous_queries"]) > 5:
                    conversation_context["previous_queries"] = conversation_context["previous_queries"][-5:]
            
            return sql
        else:
            return f"API响应格式错误: {result}"
            
    except requests.exceptions.RequestException as e:
        return f"网络请求失败: {e}"
    except Exception as e:
        return f"通义API调用失败: {e}"

def clear_conversation_context(session_id=None):
    """清除对话上下文"""
    global conversation_context
    if session_id is None or conversation_context["current_session"] == session_id:
        conversation_context = {
            "previous_queries": [],
            "table_schema": "",
            "current_session": None
        } 