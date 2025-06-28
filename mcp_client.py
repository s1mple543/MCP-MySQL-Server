import asyncio
from typing import Dict, Any, Optional
from mcp_server import get_mcp_server

class MCPClient:
    """MCP客户端，提供与MCP服务器通信的接口"""
    
    def __init__(self):
        self.server = get_mcp_server()
    
    async def get_schema(self, schema_type: str = "text", table_names=None) -> Dict[str, Any]:
        """获取数据库结构，支持表名过滤"""
        request = {
            "type": "schema",
            "schema_type": schema_type
        }
        if table_names is not None:
            request["table_names"] = table_names
        return await self.server.handle_request(request)
    
    async def query(self, nl_query: str, user_info: str = "cli_user", session_id: Optional[str] = None) -> Dict[str, Any]:
        """处理自然语言查询"""
        request = {
            "type": "query",
            "query": nl_query,
            "user_info": user_info,
            "session_id": session_id
        }
        return await self.server.handle_request(request)
    
    def get_logs_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        return self.server.get_logs_stats()
    
    def get_recent_logs(self, limit: int = 10) -> Dict[str, Any]:
        """获取最近的查询日志"""
        logs = self.server.get_recent_logs(limit)
        return {
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        }
    
    def get_error_logs(self, limit: int = 10) -> Dict[str, Any]:
        """获取错误日志"""
        errors = self.server.get_error_logs(limit)
        return {
            "success": True,
            "data": {
                "errors": errors,
                "count": len(errors)
            }
        }

# 同步包装器，用于非异步环境
class MCPClientSync:
    """同步MCP客户端"""
    
    def __init__(self):
        self.client = MCPClient()
    
    def get_schema(self, schema_type: str = "text", table_names=None) -> Dict[str, Any]:
        """获取数据库结构（同步版本），支持表名过滤"""
        return asyncio.run(self.client.get_schema(schema_type, table_names))
    
    def query(self, nl_query: str, user_info: str = "cli_user", session_id: Optional[str] = None) -> Dict[str, Any]:
        """处理自然语言查询（同步版本）"""
        return asyncio.run(self.client.query(nl_query, user_info, session_id))
    
    def get_logs_stats(self) -> Dict[str, Any]:
        """获取日志统计信息（同步版本）"""
        return self.client.get_logs_stats()
    
    def get_recent_logs(self, limit: int = 10) -> Dict[str, Any]:
        """获取最近的查询日志（同步版本）"""
        return self.client.get_recent_logs(limit)
    
    def get_error_logs(self, limit: int = 10) -> Dict[str, Any]:
        """获取错误日志（同步版本）"""
        return self.client.get_error_logs(limit) 