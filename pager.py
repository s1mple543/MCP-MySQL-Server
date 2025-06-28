import math
from typing import List, Dict, Any, Optional

class QueryPager:
    """查询结果分页管理器"""
    
    def __init__(self, data: List, page_size: int = 10, columns: Optional[List[str]] = None):
        self.data = data
        self.page_size = page_size
        self.columns = columns or []
        self.current_page = 0
        self.total_pages = math.ceil(len(data) / page_size) if data else 0
        self.total_rows = len(data)
    
    def get_current_page_data(self) -> List:
        """获取当前页数据"""
        if not self.data:
            return []
        
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.data))
        return self.data[start_idx:end_idx]
    
    def next_page(self) -> bool:
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            return True
        return False
    
    def prev_page(self) -> bool:
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            return True
        return False
    
    def go_to_page(self, page_num: int) -> bool:
        """跳转到指定页"""
        if 0 <= page_num < self.total_pages:
            self.current_page = page_num
            return True
        return False
    
    def get_page_info(self) -> Dict[str, Any]:
        """获取页面信息"""
        current_data = self.get_current_page_data()
        return {
            "current_page": self.current_page + 1,
            "total_pages": self.total_pages,
            "total_rows": self.total_rows,
            "page_size": self.page_size,
            "current_rows": len(current_data),
            "has_next": self.current_page < self.total_pages - 1,
            "has_prev": self.current_page > 0,
            "start_row": self.current_page * self.page_size + 1,
            "end_row": min((self.current_page + 1) * self.page_size, self.total_rows)
        }
    
    def format_page_display(self, show_columns: bool = True) -> str:
        """格式化页面显示"""
        if not self.data:
            return "无数据"
        
        page_info = self.get_page_info()
        current_data = self.get_current_page_data()
        
        # 构建显示内容
        lines = []
        
        # 页面信息
        lines.append(f"第 {page_info['current_page']}/{page_info['total_pages']} 页")
        lines.append(f"显示第 {page_info['start_row']}-{page_info['end_row']} 行，共 {page_info['total_rows']} 行")
        
        # 列名
        if show_columns and self.columns:
            lines.append(f"列名: {', '.join(self.columns)}")
        
        lines.append("-" * 60)
        
        # 数据行
        for i, row in enumerate(current_data, 1):
            lines.append(f"{page_info['start_row'] + i - 1:3d}. {row}")
        
        lines.append("-" * 60)
        
        # 只有当数据超过一页时才显示导航信息
        if self.total_pages > 1:
            nav_info = []
            if page_info['has_prev']:
                nav_info.append("输入 'prev' 上一页")
            if page_info['has_next']:
                nav_info.append("输入 'next' 下一页")
            nav_info.append("输入 'first' 第一页")
            nav_info.append("输入 'last' 最后一页")
            nav_info.append("输入 'page 数字' 跳转到指定页")
            nav_info.append("输入 'auto' 自动分页显示")
            nav_info.append("输入 'exit' 退出分页")
            
            lines.append("导航: " + " | ".join(nav_info))
        
        return "\n".join(lines)
    
    def auto_paginate(self, delay: float = 1.0) -> None:
        """自动分页显示"""
        import time
        
        print(f"自动分页显示，每页 {self.page_size} 行，延迟 {delay} 秒")
        
        for page in range(self.total_pages):
            self.current_page = page
            print(f"\n{self.format_page_display()}")
            
            if page < self.total_pages - 1:
                print(f"{delay}秒后显示下一页...")
                time.sleep(delay)
        
        print("自动分页完成")

class PagerManager:
    """分页管理器"""
    
    def __init__(self):
        self.current_pager = None
    
    def create_pager(self, data: List, page_size: int = 10, columns: Optional[List[str]] = None) -> QueryPager:
        """创建分页器"""
        self.current_pager = QueryPager(data, page_size, columns)
        return self.current_pager
    
    def handle_pager_command(self, command: str) -> bool:
        """处理分页命令"""
        if not self.current_pager:
            return False
        
        command = command.lower().strip()
        
        if command == "next":
            if self.current_pager.next_page():
                print(self.current_pager.format_page_display())
                return True
            else:
                print("已经是最后一页")
                return True
        
        elif command == "prev":
            if self.current_pager.prev_page():
                print(self.current_pager.format_page_display())
                return True
            else:
                print("已经是第一页")
                return True
        
        elif command == "first":
            if self.current_pager.go_to_page(0):
                print(self.current_pager.format_page_display())
                return True
        
        elif command == "last":
            if self.current_pager.go_to_page(self.current_pager.total_pages - 1):
                print(self.current_pager.format_page_display())
                return True
        
        elif command.startswith("page "):
            try:
                page_num = int(command.split()[1]) - 1  # 用户输入从1开始
                if self.current_pager.go_to_page(page_num):
                    print(self.current_pager.format_page_display())
                    return True
                else:
                    print(f"页码超出范围 (1-{self.current_pager.total_pages})")
                    return True
            except (ValueError, IndexError):
                print("无效的页码格式，请使用 'page 数字'")
                return True
        
        elif command == "auto":
            self.current_pager.auto_paginate()
            return True
        
        elif command == "exit":
            print("退出分页模式")
            return False
        
        else:
            print("未知命令，请输入 'next', 'prev', 'first', 'last', 'page 数字', 'auto' 或 'exit'")
            return True
        
        return True
    
    def interactive_paging(self, data: List, page_size: int = 10, columns: Optional[List[str]] = None) -> None:
        """交互式分页"""
        if not data:
            print("无数据需要分页")
            return
        
        pager = self.create_pager(data, page_size, columns)
        
        # 如果数据量小于等于页面大小，直接显示
        if len(data) <= page_size:
            print(pager.format_page_display())
            return
        
        # 显示第一页
        print(pager.format_page_display())
        
        # 交互式分页
        while True:
            command = input("\n分页命令: ").strip()
            if not self.handle_pager_command(command):
                break

# 全局分页管理器实例
pager_manager = PagerManager()

def get_pager_manager() -> PagerManager:
    """获取分页管理器"""
    return pager_manager 