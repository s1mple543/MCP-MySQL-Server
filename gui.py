import streamlit as st
import json
import uuid
from mcp_client import MCPClientSync

def main():
    st.set_page_config(
        page_title="智能数据库查询系统",
        page_icon="",
        layout="wide"
    )
    
    st.title("智能数据库查询系统")
    st.markdown("支持自然语言转SQL")
    
    # 初始化客户端和会话ID
    if 'client' not in st.session_state:
        st.session_state.client = MCPClientSync()
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # 侧边栏
    with st.sidebar:
        st.header("系统信息")
        
        # 新增：数据库结构查看
        st.subheader("查看数据库结构")
        table_input = st.text_input("输入表名（多个用逗号分隔，留空查看全部）", "")
        if st.button("获取结构"):
            table_names = None
            if table_input.strip():
                table_names = [t.strip() for t in table_input.split(",") if t.strip()]
                if len(table_names) == 1:
                    table_names = table_names[0]
            schema_result = st.session_state.client.get_schema(schema_type="text", table_names=table_names)
            if schema_result["success"]:
                st.success("数据库结构：")
                st.text(schema_result["data"]["schema"])
            else:
                st.error(f"获取数据库结构失败: {schema_result['error']}")
        
        # 日志统计
        if st.button("查看日志统计"):
            stats = st.session_state.client.get_logs_stats()
            if stats:
                st.success("日志统计")
                st.write(f"总查询数: {stats['total_queries']}")
                st.write(f"成功查询: {stats['successful_queries']}")
                st.write(f"失败查询: {stats['failed_queries']}")
                st.write(f"成功率: {stats['success_rate']}%")
                st.write(f"总语句数: {stats['total_statements']}")
        
        # 最近查询
        if st.button("最近查询"):
            logs_response = st.session_state.client.get_recent_logs(5)
            if logs_response["success"]:
                logs = logs_response["data"]["logs"]
                st.success(f"最近 {len(logs)} 次查询")
                for log in logs:
                    with st.expander(f"{log['timestamp']} - {log['nl_query'][:30]}..."):
                        st.write(f"**查询:** {log['nl_query']}")
                        st.code(log['generated_sql'])
                        st.write(f"执行时间: {log['execution_time']:.3f}秒")
                        st.write(f"状态: {'成功' if log['success'] else '失败'}")
        
        # 错误日志
        if st.button("错误日志"):
            errors_response = st.session_state.client.get_error_logs(5)
            if errors_response["success"]:
                errors = errors_response["data"]["errors"]
                st.error(f"最近 {len(errors)} 个错误")
                for error in errors:
                    with st.expander(f"{error['timestamp']} - {error['nl_query'][:30]}..."):
                        st.write(f"**查询:** {error['nl_query']}")
                        st.code(error['generated_sql'])
                        st.error(f"错误: {error['error_message']}")
    
    # 主界面
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("自然语言查询")
        nl_query = st.text_area(
            "请输入您的查询需求",
            placeholder="例如：查询所有学生的姓名和成绩",
            height=100
        )
        
        if st.button("执行查询", type="primary"):
            if nl_query.strip():
                with st.spinner("正在处理查询..."):
                    result = st.session_state.client.query(nl_query, "gui_user", st.session_state.session_id)
                
                if result["success"]:
                    data = result["data"]
                    st.success("查询处理成功")
                    
                    # 显示查询信息
                    with st.expander("查询详情", expanded=True):
                        st.write(f"**原始查询:** {data['original_query']}")
                        st.code(data['generated_sql'], language="sql")
                        st.write(f"**执行时间:** {data['execution_time']:.3f}秒")
                    
                    # 处理查询结果
                    query_result = data['result']
                    
                    if isinstance(query_result, dict):
                        if query_result["type"] == "error":
                            st.error(f"错误: {query_result['message']}")
                        
                        elif query_result["type"] == "multiple":
                            # 多语句执行结果
                            st.info(f"多语句执行结果")
                            st.write(f"总语句数: {query_result['total_statements']}")
                            st.write(f"成功语句: {query_result['successful_statements']}")
                            st.write(f"失败语句: {query_result['failed_statements']}")
                            st.write(f"总影响行数: {query_result['total_affected_rows']}")
                            
                            # 显示每个语句的结果
                            for stmt_result in query_result['results']:
                                with st.expander(f"语句 {stmt_result['statement_index']}: {stmt_result['sql'][:50]}...", expanded=True):
                                    if stmt_result["type"] == "error":
                                        st.error(f"执行失败: {stmt_result['message']}")
                                    elif stmt_result["type"] in ["select", "show", "describe"]:
                                        if stmt_result["data"]:
                                            st.success(f"返回 {stmt_result['row_count']} 行数据")
                                            st.write(f"**列名:** {', '.join(stmt_result['columns'])}")
                                            
                                            # 直接显示数据表格
                                            st.dataframe(
                                                stmt_result["data"],
                                                column_config={str(i): col for i, col in enumerate(stmt_result["columns"])},
                                                use_container_width=True
                                            )
                                        else:
                                            st.info("无返回数据")
                                    elif stmt_result["type"] == "modify":
                                        st.success(f"{stmt_result['message']}")
                                        st.write(f"影响行数: {stmt_result['affected_rows']}")
                        
                        elif query_result["type"] in ["select", "show", "describe"]:
                            if query_result["data"]:
                                st.success(f"查询成功，返回 {query_result['row_count']} 行数据")
                                st.write(f"**列名:** {', '.join(query_result['columns'])}")
                                
                                # 直接显示数据表格
                                st.dataframe(
                                    query_result["data"],
                                    column_config={str(i): col for i, col in enumerate(query_result["columns"])},
                                    use_container_width=True
                                )
                            else:
                                st.info("查询完成，无返回数据")
                        
                        elif query_result["type"] == "modify":
                            st.success(f"{query_result['message']}")
                            st.write(f"操作类型: {query_result['sql_type']}")
                            st.write(f"影响行数: {query_result['affected_rows']}")
                    
                    else:
                        st.write(query_result)
                else:
                    st.error(f"查询处理失败: {result['error']}")
            else:
                st.warning("请输入查询内容")
    
    with col2:
        st.subheader("使用说明")
        st.markdown("""
        **功能特性:**
        - 自然语言转SQL
        - 多语句执行
        - 查询日志记录
        - 数据库结构查看
        - 对话上下文支持
        
        **查询示例:**
        - 查询所有学生信息
        - 显示成绩大于80分的学生
        - 统计每个班级的平均分
        
        **对话上下文:**
        - 系统会记住您的查询历史
        - 支持连续查询和上下文理解
        - 提升复杂查询的准确性
        """)

if __name__ == "__main__":
    main()