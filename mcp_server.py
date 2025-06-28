import json
import asyncio
import time
from typing import Dict, Any, List, Optional
from db_manager import DBManager
from tongyi_api import nl2sql
from logger import get_query_logger
from config import DB_CONFIG, TONGYI_API_KEY

class MCPServer:
    """MCP服务器，提供统一的数据库和AI服务接口"""
    
    def __init__(self):
        self.db_manager = DBManager()
        self.api_key = TONGYI_API_KEY
        self.logger = get_query_logger()
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        try:
            request_type = request.get("type")
            
            if request_type == "schema":
                return await self.get_schema(request)
            elif request_type == "query":
                return await self.process_query(request)
            else:
                return {
                    "success": False,
                    "error": f"未知的请求类型: {request_type}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"MCP服务错误: {str(e)}"
            }
    
    async def get_schema(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """获取数据库结构，支持按表名过滤"""
        try:
            schema_type = request.get("schema_type", "text")
            table_names = request.get("table_names")
            if table_names:
                # 支持单个表名或表名列表
                if schema_type == "text":
                    schema = self.db_manager.get_tables_schema_text(table_names)
                else:
                    schema = self.db_manager.get_tables_schema(table_names)
            else:
                if schema_type == "text":
                    schema = self.db_manager.get_schema_text()
                else:
                    schema = self.db_manager.get_database_schema()
            return {
                "success": True,
                "data": {
                    "schema": schema,
                    "type": schema_type
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"获取数据库结构失败: {str(e)}"
            }
    
    async def process_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理自然语言查询"""
        start_time = time.time()
        
        try:
            nl_query = request.get("query", "")
            user_info = request.get("user_info", "unknown")
            session_id = request.get("session_id", None)  # 新增会话ID支持
            
            if not nl_query:
                return {
                    "success": False,
                    "error": "查询内容不能为空"
                }
            
            # 1. 获取数据库结构
            schema_response = await self.get_schema({"schema_type": "text"})
            if not schema_response["success"]:
                return {
                    "success": False,
                    "error": f"获取数据库结构失败: {schema_response['error']}"
                }
            
            db_schema = schema_response["data"]["schema"]
            
            # 2. 自然语言转SQL（支持会话上下文）
            sql = nl2sql(nl_query, db_schema, session_id)
            
            # 3. 执行SQL
            result = self.db_manager.execute_sql(sql)
            
            # 4. 计算执行时间
            execution_time = time.time() - start_time
            
            # 5. 记录日志
            self.logger.log_query(
                nl_query=nl_query,
                generated_sql=sql,
                result=result,
                execution_time=execution_time,
                user_info=user_info
            )
            
            return {
                "success": True,
                "data": {
                    "original_query": nl_query,
                    "generated_sql": sql,
                    "result": result,
                    "execution_time": execution_time
                }
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 记录错误日志
            self.logger.log_query(
                nl_query=nl_query if 'nl_query' in locals() else "",
                generated_sql=sql if 'sql' in locals() else "",
                result={"type": "error", "message": str(e)},
                execution_time=execution_time,
                user_info=user_info if 'user_info' in locals() else "unknown"
            )
            
            return {
                "success": False,
                "error": f"查询处理失败: {str(e)}"
            }
    
    def get_logs_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        return self.logger.get_stats()
    
    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的查询日志"""
        return self.logger.get_recent_queries(limit)
    
    def get_error_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取错误日志"""
        return self.logger.get_error_logs(limit)
    
    def close(self):
        """关闭MCP服务"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()

# 全局MCP服务实例
mcp_server = MCPServer()

def get_mcp_server() -> MCPServer:
    """获取MCP服务实例"""
    return mcp_server 