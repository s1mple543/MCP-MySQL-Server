import pymysql
from config import DB_CONFIG, SENSITIVE_FIELDS

class DBManager:
    def __init__(self):
        self.conn = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        self.cursor = self.conn.cursor()

    def get_database_schema(self):
        """获取数据库结构信息"""
        try:
            # 获取所有表名
            self.cursor.execute("SHOW TABLES")
            tables = self.cursor.fetchall()
            
            schema_info = []
            for table in tables:
                table_name = table[0]
                
                # 获取表结构
                self.cursor.execute(f"DESCRIBE {table_name}")
                columns = self.cursor.fetchall()
                
                # 获取表的创建语句
                self.cursor.execute(f"SHOW CREATE TABLE {table_name}")
                create_result = self.cursor.fetchone()
                create_statement = create_result[1] if create_result else ""
                
                table_info = {
                    "table_name": table_name,
                    "columns": [{"field": col[0], "type": col[1], "null": col[2], "key": col[3], "default": col[4]} for col in columns],
                    "create_statement": create_statement
                }
                schema_info.append(table_info)
            
            return schema_info
        except Exception as e:
            return f"获取数据库结构失败: {e}"

    def get_schema_text(self):
        """获取格式化的数据库结构文本，用于AI模型理解"""
        schema_info = self.get_database_schema()
        if isinstance(schema_info, str):  # 如果返回的是错误信息
            return schema_info
        
        schema_text = "数据库结构：\n"
        for table in schema_info:
            schema_text += f"\n表名：{table['table_name']}\n"
            schema_text += "字段信息：\n"
            for col in table['columns']:
                schema_text += f"  - {col['field']} ({col['type']})"
                if col['key'] == 'PRI':
                    schema_text += " [主键]"
                if col['null'] == 'NO':
                    schema_text += " [非空]"
                schema_text += "\n"
            schema_text += f"建表语句：{table['create_statement']}\n"
        
        return schema_text

    def execute_sql(self, sql):
        try:
            # 清理SQL语句
            sql = sql.strip()
            
            # 检查SQL类型，只允许查询语句
            sql_lower = sql.lower()
            allowed_keywords = ['select', 'show', 'describe', 'desc', 'explain']
            
            # 检查是否以允许的关键字开头
            is_allowed = any(sql_lower.startswith(keyword) for keyword in allowed_keywords)
            
            if not is_allowed:
                return {
                    "type": "error",
                    "message": f"安全限制：只允许执行查询语句（SELECT、SHOW、DESCRIBE等），当前语句类型不允许执行",
                    "sql": sql,
                    "sql_type": "restricted"
                }
            
            # 检查敏感字段访问
            sql_words = sql_lower.split()
            
            # 检查是否包含敏感字段
            sensitive_field_found = None
            for field in SENSITIVE_FIELDS:
                # 检查字段名是否在SQL中（考虑表名.字段名的形式）
                if field in sql_words or f".{field}" in sql_lower or f" {field} " in sql_lower:
                    sensitive_field_found = field
                    break
            
            if sensitive_field_found:
                return {
                    "type": "error",
                    "message": f"安全限制：禁止访问敏感字段 '{sensitive_field_found}'，该字段包含敏感信息",
                    "sql": sql,
                    "sql_type": "sensitive_field"
                }
            
            # 检查SELECT * 是否可能包含敏感字段
            if 'select' in sql_words and '*' in sql_words:
                # 对于SELECT * 查询，需要检查表结构
                table_check_result = self._check_table_sensitive_fields(sql_lower)
                if table_check_result:
                    return table_check_result
            
            # 分割多个SQL语句
            statements = [stmt.strip() + ';' for stmt in sql.split(';') if stmt.strip()]
            
            if len(statements) == 1:
                # 单个语句执行
                return self._execute_single_sql(statements[0])
            else:
                # 多个语句执行
                return self._execute_multiple_sql(statements)
                
        except Exception as e:
            return {
                "type": "error",
                "message": f"SQL执行出错: {e}",
                "sql": sql
            }
    
    def _check_table_sensitive_fields(self, sql_lower):
        """检查表是否包含敏感字段"""
        try:
            # 提取表名（简化处理）
            if 'from' in sql_lower:
                from_index = sql_lower.find('from')
                after_from = sql_lower[from_index:].split()
                if len(after_from) > 1:
                    table_name = after_from[1].strip(';').strip()
                    
                    # 获取表结构
                    self.cursor.execute(f"DESCRIBE {table_name}")
                    columns = self.cursor.fetchall()
                    
                    # 检查字段名
                    for col in columns:
                        field_name = col[0].lower()
                        for sensitive_field in SENSITIVE_FIELDS:
                            if sensitive_field in field_name:
                                return {
                                    "type": "error",
                                    "message": f"安全限制：表 '{table_name}' 包含敏感字段 '{col[0]}'，禁止访问",
                                    "sql": sql_lower,
                                    "sql_type": "sensitive_table"
                                }
        except Exception:
            # 如果检查失败，允许执行（避免过度限制）
            pass
        return None
    
    def _execute_single_sql(self, sql):
        """执行单个SQL语句"""
        try:
            self.cursor.execute(sql)
            sql_lower = sql.strip().lower()
            
            if sql_lower.startswith("select"):
                # SELECT查询：返回数据
                results = self.cursor.fetchall()
                # 获取列名
                column_names = [desc[0] for desc in self.cursor.description]
                return {
                    "type": "select",
                    "data": results,
                    "columns": column_names,
                    "row_count": len(results)
                }
            elif sql_lower.startswith("show"):
                # SHOW语句：返回表结构等信息
                results = self.cursor.fetchall()
                column_names = [desc[0] for desc in self.cursor.description]
                return {
                    "type": "show",
                    "data": results,
                    "columns": column_names,
                    "row_count": len(results)
                }
            elif sql_lower.startswith("describe") or sql_lower.startswith("desc"):
                # DESCRIBE语句：返回表结构
                results = self.cursor.fetchall()
                column_names = [desc[0] for desc in self.cursor.description]
                return {
                    "type": "describe",
                    "data": results,
                    "columns": column_names,
                    "row_count": len(results)
                }
            elif sql_lower.startswith("explain"):
                # EXPLAIN语句：返回执行计划
                results = self.cursor.fetchall()
                column_names = [desc[0] for desc in self.cursor.description]
                return {
                    "type": "explain",
                    "data": results,
                    "columns": column_names,
                    "row_count": len(results)
                }
            else:
                # 其他查询语句（已通过安全检查）
                results = self.cursor.fetchall()
                column_names = [desc[0] for desc in self.cursor.description]
                return {
                    "type": "query",
                    "data": results,
                    "columns": column_names,
                    "row_count": len(results)
                }
                
        except Exception as e:
            return {
                "type": "error",
                "message": f"SQL执行出错: {e}",
                "sql": sql
            }
    
    def _execute_multiple_sql(self, statements):
        """执行多个SQL语句"""
        try:
            results = []
            total_affected_rows = 0
            
            for i, sql in enumerate(statements):
                try:
                    # 检查SQL类型，只允许查询语句
                    sql_lower = sql.strip().lower()
                    allowed_keywords = ['select', 'show', 'describe', 'desc', 'explain']
                    
                    # 检查是否以允许的关键字开头
                    is_allowed = any(sql_lower.startswith(keyword) for keyword in allowed_keywords)
                    
                    if not is_allowed:
                        results.append({
                            "statement_index": i + 1,
                            "sql": sql,
                            "type": "error",
                            "message": f"安全限制：只允许执行查询语句（SELECT、SHOW、DESCRIBE等），当前语句类型不允许执行"
                        })
                        continue
                    
                    # 检查敏感字段访问
                    sql_words = sql_lower.split()
                    
                    # 检查是否包含敏感字段
                    sensitive_field_found = None
                    for field in SENSITIVE_FIELDS:
                        # 检查字段名是否在SQL中（考虑表名.字段名的形式）
                        if field in sql_words or f".{field}" in sql_lower or f" {field} " in sql_lower:
                            sensitive_field_found = field
                            break
                    
                    if sensitive_field_found:
                        results.append({
                            "statement_index": i + 1,
                            "sql": sql,
                            "type": "error",
                            "message": f"安全限制：禁止访问敏感字段 '{sensitive_field_found}'，该字段包含敏感信息"
                        })
                        continue
                    
                    # 检查SELECT * 是否可能包含敏感字段
                    if 'select' in sql_words and '*' in sql_words:
                        table_check_result = self._check_table_sensitive_fields(sql_lower)
                        if table_check_result:
                            results.append({
                                "statement_index": i + 1,
                                "sql": sql,
                                "type": "error",
                                "message": table_check_result["message"]
                            })
                            continue
                    
                    self.cursor.execute(sql)
                    
                    if sql_lower.startswith("select"):
                        # SELECT查询
                        query_results = self.cursor.fetchall()
                        column_names = [desc[0] for desc in self.cursor.description]
                        results.append({
                            "statement_index": i + 1,
                            "sql": sql,
                            "type": "select",
                            "data": query_results,
                            "columns": column_names,
                            "row_count": len(query_results)
                        })
                    elif sql_lower.startswith("show"):
                        # SHOW语句
                        query_results = self.cursor.fetchall()
                        column_names = [desc[0] for desc in self.cursor.description]
                        results.append({
                            "statement_index": i + 1,
                            "sql": sql,
                            "type": "show",
                            "data": query_results,
                            "columns": column_names,
                            "row_count": len(query_results)
                        })
                    elif sql_lower.startswith("describe") or sql_lower.startswith("desc"):
                        # DESCRIBE语句
                        query_results = self.cursor.fetchall()
                        column_names = [desc[0] for desc in self.cursor.description]
                        results.append({
                            "statement_index": i + 1,
                            "sql": sql,
                            "type": "describe",
                            "data": query_results,
                            "columns": column_names,
                            "row_count": len(query_results)
                        })
                    elif sql_lower.startswith("explain"):
                        # EXPLAIN语句
                        query_results = self.cursor.fetchall()
                        column_names = [desc[0] for desc in self.cursor.description]
                        results.append({
                            "statement_index": i + 1,
                            "sql": sql,
                            "type": "explain",
                            "data": query_results,
                            "columns": column_names,
                            "row_count": len(query_results)
                        })
                        
                except Exception as e:
                    results.append({
                        "statement_index": i + 1,
                        "sql": sql,
                        "type": "error",
                        "message": f"语句执行失败: {e}"
                    })
            
            return {
                "type": "multiple",
                "total_statements": len(statements),
                "successful_statements": len([r for r in results if r["type"] != "error"]),
                "failed_statements": len([r for r in results if r["type"] == "error"]),
                "total_affected_rows": total_affected_rows,
                "results": results
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"多语句执行失败: {e}",
                "sql": "; ".join(statements)
            }

    def close(self):
        self.cursor.close()
        self.conn.close()

    def get_tables_schema(self, table_names):
        """获取指定表的结构信息，table_names为列表或单个表名"""
        if isinstance(table_names, str):
            table_names = [table_names]
        try:
            schema_info = []
            for table_name in table_names:
                # 获取表结构
                self.cursor.execute(f"DESCRIBE {table_name}")
                columns = self.cursor.fetchall()
                # 获取表的创建语句
                self.cursor.execute(f"SHOW CREATE TABLE {table_name}")
                create_result = self.cursor.fetchone()
                create_statement = create_result[1] if create_result else ""
                table_info = {
                    "table_name": table_name,
                    "columns": [{"field": col[0], "type": col[1], "null": col[2], "key": col[3], "default": col[4]} for col in columns],
                    "create_statement": create_statement
                }
                schema_info.append(table_info)
            return schema_info
        except Exception as e:
            return f"获取指定表结构失败: {e}"

    def get_tables_schema_text(self, table_names):
        """获取指定表的结构文本"""
        schema_info = self.get_tables_schema(table_names)
        if isinstance(schema_info, str):
            return schema_info
        schema_text = "数据库结构：\n"
        for table in schema_info:
            schema_text += f"\n表名：{table['table_name']}\n"
            schema_text += "字段信息：\n"
            for col in table['columns']:
                schema_text += f"  - {col['field']} ({col['type']})"
                if col['key'] == 'PRI':
                    schema_text += " [主键]"
                if col['null'] == 'NO':
                    schema_text += " [非空]"
                schema_text += "\n"
            schema_text += f"建表语句：{table['create_statement']}\n"
        return schema_text 