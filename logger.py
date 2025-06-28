import os
import json
import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

class QueryLogger:
    """查询日志记录器"""
    
    def __init__(self, log_dir: Optional[str] = None):
        # 如果没有指定日志目录，使用项目根目录下的logs文件夹
        if log_dir is None:
            # 获取当前文件所在目录（SQL-Lab6）
            current_dir = Path(__file__).parent
            log_dir = str(current_dir / "logs")
        else:
            log_dir = str(log_dir)
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建不同类型的日志文件
        self.query_log_file = self.log_dir / "query_log.jsonl"
        self.error_log_file = self.log_dir / "error_log.jsonl"
        self.stats_file = self.log_dir / "stats.json"
        
        # 初始化统计信息
        self._init_stats()
    
    def _init_stats(self):
        """初始化统计信息"""
        if not self.stats_file.exists():
            stats = {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "total_statements": 0,
                "start_time": datetime.datetime.now().isoformat(),
                "last_query_time": None
            }
            self._save_stats(stats)
    
    def _load_stats(self) -> Dict[str, Any]:
        """加载统计信息"""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "total_statements": 0,
                "start_time": datetime.datetime.now().isoformat(),
                "last_query_time": None
            }
    
    def _save_stats(self, stats: Dict[str, Any]):
        """保存统计信息"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def log_query(self, nl_query: str, generated_sql: str, result: Dict[str, Any], 
                  execution_time: float = 0.0, user_info: str = "unknown"):
        """记录查询日志"""
        timestamp = datetime.datetime.now()
        
        # 构建日志条目
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "nl_query": nl_query,
            "generated_sql": generated_sql,
            "execution_time": execution_time,
            "user_info": user_info,
            "result_type": result.get("type", "unknown"),
            "success": result.get("type") != "error",
            "error_message": result.get("message") if result.get("type") == "error" else None
        }
        
        # 添加多语句执行的详细信息
        if result.get("type") == "multiple":
            log_entry.update({
                "total_statements": result.get("total_statements", 0),
                "successful_statements": result.get("successful_statements", 0),
                "failed_statements": result.get("failed_statements", 0),
                "total_affected_rows": result.get("total_affected_rows", 0)
            })
        elif result.get("type") in ["select", "show", "describe"]:
            log_entry.update({
                "row_count": result.get("row_count", 0),
                "column_count": len(result.get("columns", []))
            })
        elif result.get("type") == "modify":
            log_entry.update({
                "affected_rows": result.get("affected_rows", 0),
                "sql_type": result.get("sql_type", "unknown")
            })
        
        # 写入日志文件
        with open(self.query_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        # 更新统计信息
        self._update_stats(log_entry)
        
        # 如果是错误，也记录到错误日志
        if not log_entry["success"]:
            self._log_error(log_entry)
    
    def _log_error(self, log_entry: Dict[str, Any]):
        """记录错误日志"""
        error_entry = {
            "timestamp": log_entry["timestamp"],
            "nl_query": log_entry["nl_query"],
            "generated_sql": log_entry["generated_sql"],
            "error_message": log_entry["error_message"],
            "execution_time": log_entry["execution_time"]
        }
        
        with open(self.error_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + '\n')
    
    def _update_stats(self, log_entry: Dict[str, Any]):
        """更新统计信息"""
        stats = self._load_stats()
        
        stats["total_queries"] += 1
        stats["last_query_time"] = log_entry["timestamp"]
        
        if log_entry["success"]:
            stats["successful_queries"] += 1
        else:
            stats["failed_queries"] += 1
        
        # 统计语句数
        if log_entry.get("result_type") == "multiple":
            stats["total_statements"] += log_entry.get("total_statements", 0)
        else:
            stats["total_statements"] += 1
        
        self._save_stats(stats)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._load_stats()
        
        # 计算成功率
        if stats["total_queries"] > 0:
            stats["success_rate"] = round(stats["successful_queries"] / stats["total_queries"] * 100, 2)
        else:
            stats["success_rate"] = 0
        
        return stats
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的查询记录"""
        queries = []
        
        if self.query_log_file.exists():
            with open(self.query_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        queries.append(json.loads(line.strip()))
                    except:
                        continue
        
        return queries[::-1]  # 返回最新的在前
    
    def get_error_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取错误日志"""
        errors = []
        
        if self.error_log_file.exists():
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        errors.append(json.loads(line.strip()))
                    except:
                        continue
        
        return errors[::-1]  # 返回最新的在前
    
    def clear_logs(self):
        """清空所有日志"""
        if self.query_log_file.exists():
            self.query_log_file.unlink()
        if self.error_log_file.exists():
            self.error_log_file.unlink()
        self._init_stats()

# 全局日志记录器实例
query_logger = QueryLogger()

def get_query_logger() -> QueryLogger:
    """获取查询日志记录器"""
    return query_logger 