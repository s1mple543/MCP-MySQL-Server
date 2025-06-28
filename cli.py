from mcp_client import MCPClientSync
from pager import get_pager_manager
import uuid

def main():
    client = MCPClientSync()
    pager_manager = get_pager_manager()
    session_id = str(uuid.uuid4())  # 为CLI会话生成唯一ID
    
    print("欢迎使用自然语言SQL查询系统")
    print("输入 'logs' 查看日志统计，输入 'recent' 查看最近查询，输入 'errors' 查看错误日志")
    print("输入 'schema' 或 'schema 表名1,表名2' 查看数据库结构")
    print("长查询结果支持分页显示，输入 'next', 'prev', 'auto' 等命令导航")
    print("支持对话上下文，系统会记住您的查询历史")
    
    while True:
        nl_query = input("\n请输入您的指令（输入exit退出）：")
        if nl_query.lower() == "exit":
            break
        elif nl_query.lower().startswith("schema"):
            # schema命令，支持过滤表名
            parts = nl_query.strip().split()
            table_names = None
            if len(parts) > 1:
                # 支持多个表名用逗号分隔
                table_names = [t.strip() for t in parts[1].split(",") if t.strip()]
                if len(table_names) == 1:
                    table_names = table_names[0]
            schema_result = client.get_schema(schema_type="text", table_names=table_names)
            if schema_result["success"]:
                print("\n 数据库结构：")
                print(schema_result["data"]["schema"])
            else:
                print(f"获取数据库结构失败: {schema_result['error']}")
            continue
        elif nl_query.lower() == "logs":
            # 显示日志统计
            stats = client.get_logs_stats()
            print("\n日志统计信息:")
            print(f"   总查询数: {stats['total_queries']}")
            print(f"   成功查询: {stats['successful_queries']}")
            print(f"   失败查询: {stats['failed_queries']}")
            print(f"   成功率: {stats['success_rate']}%")
            print(f"   总语句数: {stats['total_statements']}")
            print(f"   开始时间: {stats['start_time']}")
            print(f"   最后查询: {stats['last_query_time']}")
            continue
        elif nl_query.lower() == "recent":
            # 显示最近查询
            logs_response = client.get_recent_logs(10)
            if logs_response["success"]:
                logs = logs_response["data"]["logs"]
                print(f"\n最近 {len(logs)} 次查询:")
                for i, log in enumerate(logs, 1):
                    print(f"\n{i}. 时间: {log['timestamp']}")
                    print(f"   查询: {log['nl_query']}")
                    print(f"   SQL: {log['generated_sql']}")
                    print(f"   执行时间: {log['execution_time']:.3f}秒")
                    print(f"   状态: {'成功' if log['success'] else '失败'}")
                    if not log['success']:
                        print(f"   错误: {log['error_message']}")
            continue
        elif nl_query.lower() == "errors":
            # 显示错误日志
            errors_response = client.get_error_logs(10)
            if errors_response["success"]:
                errors = errors_response["data"]["errors"]
                print(f"\n最近 {len(errors)} 个错误:")
                for i, error in enumerate(errors, 1):
                    print(f"\n{i}. 时间: {error['timestamp']}")
                    print(f"   查询: {error['nl_query']}")
                    print(f"   SQL: {error['generated_sql']}")
                    print(f"   错误: {error['error_message']}")
            continue
        
        print("正在处理查询...")
        result = client.query(nl_query, "cli_user", session_id)
        
        if result["success"]:
            data = result["data"]
            print("查询处理成功")
            print(f"原始查询: {data['original_query']}")
            print(f"生成SQL: {data['generated_sql']}")
            print(f"执行时间: {data['execution_time']:.3f}秒")
            
            # 处理查询结果
            query_result = data['result']
            
            if isinstance(query_result, dict):
                if query_result["type"] == "error":
                    print(f"错误: {query_result['message']}")
                
                elif query_result["type"] == "multiple":
                    # 多语句执行结果
                    print("多语句执行结果")
                    print(f"总语句数: {query_result['total_statements']}")
                    print(f"成功语句: {query_result['successful_statements']}")
                    print(f"失败语句: {query_result['failed_statements']}")
                    print(f"总影响行数: {query_result['total_affected_rows']}")
                    
                    # 显示每个语句的结果
                    for stmt_result in query_result['results']:
                        print(f"\n语句 {stmt_result['statement_index']}: {stmt_result['sql']}")
                        if stmt_result["type"] == "error":
                            print(f"执行失败: {stmt_result['message']}")
                        elif stmt_result["type"] in ["select", "show", "describe"]:
                            if stmt_result["data"]:
                                print(f"返回 {stmt_result['row_count']} 行数据")
                                print(f"列名: {', '.join(stmt_result['columns'])}")
                                
                                # 分页显示数据
                                pager_manager.interactive_paging(
                                    data=stmt_result["data"],
                                    columns=stmt_result["columns"],
                                    page_size=10
                                )
                            else:
                                print("无返回数据")
                        elif stmt_result["type"] == "modify":
                            print(f"{stmt_result['message']}")
                            print(f"影响行数: {stmt_result['affected_rows']}")
                
                elif query_result["type"] in ["select", "show", "describe"]:
                    if query_result["data"]:
                        print(f"查询成功，返回 {query_result['row_count']} 行数据")
                        print(f"列名: {', '.join(query_result['columns'])}")
                        
                        # 分页显示数据
                        pager_manager.interactive_paging(
                            data=query_result["data"],
                            columns=query_result["columns"],
                            page_size=10
                        )
                    else:
                        print("查询完成，无返回数据")
                
                elif query_result["type"] == "modify":
                    print(f"{query_result['message']}")
                    print(f"操作类型: {query_result['sql_type']}")
                    print(f"影响行数: {query_result['affected_rows']}")
            
            else:
                print(query_result)
        else:
            print(f"查询处理失败: {result['error']}")

if __name__ == "__main__":
    main() 